/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/netanim-module.h"
#include <fstream>

// Network Topology
//
//   10.1.1.0/24            10.1.2.0/24
//  n0 (Source) ----------- n1 (Router) ----------- n2 (Sink)
//    p2p: 10Mbps, 4ms        p2p: 10Mbps, 4ms
//

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("Assignment4SingleVariantScript");

static void
CwndTracer (Ptr<OutputStreamWrapper> stream, uint32_t oldCwnd, uint32_t newCwnd)
{
  *stream->GetStream () << Simulator::Now ().GetSeconds () << "\t" << newCwnd << std::endl;
}

void
ConnectSocketTraces (std::string cwndFileName)
{
  AsciiTraceHelper asciiTraceHelper;
  Ptr<OutputStreamWrapper> stream = asciiTraceHelper.CreateFileStream (cwndFileName);
  Config::ConnectWithoutContext ("/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow",
                                 MakeBoundCallback (&CwndTracer, stream));
}

int
main (int argc, char *argv[])
{
  uint32_t payloadSize = 1024;
  double simTime = 20.0;
  bool tracing = true;

  CommandLine cmd (__FILE__);
  cmd.AddValue ("payloadSize", "Payload Size in Bytes", payloadSize);
  cmd.AddValue ("simTime", "Simulation Time in Seconds", simTime);
  cmd.AddValue ("tracing", "Enable PCAP and ASCII tracing", tracing);
  cmd.Parse (argc, argv);

  // Configure single TCP Variant (TCP NewReno) and Segment Size
  Config::SetDefault ("ns3::TcpSocket::SegmentSize", UintegerValue (payloadSize));
  Config::SetDefault ("ns3::TcpL4Protocol::SocketType", TypeIdValue (TcpNewReno::GetTypeId ()));

  // Node Creation: n0 (Source), n1 (Router), n2 (Sink)
  NodeContainer nodes;
  nodes.Create (3);

  NodeContainer n0n1 = NodeContainer (nodes.Get (0), nodes.Get (1));
  NodeContainer n1n2 = NodeContainer (nodes.Get (1), nodes.Get (2));

  // Point-to-Point Channel Configuration: 10 Mbps DataRate, 4 ms Delay
  PointToPointHelper pointToPoint;
  pointToPoint.SetDeviceAttribute ("DataRate", StringValue ("10Mbps"));
  pointToPoint.SetChannelAttribute ("Delay", StringValue ("4ms"));
  pointToPoint.SetQueue ("ns3::DropTailQueue", "MaxSize", StringValue ("10p"));

  NetDeviceContainer dev01 = pointToPoint.Install (n0n1);
  NetDeviceContainer dev12 = pointToPoint.Install (n1n2);

  // Install Internet Stack
  InternetStackHelper stack;
  stack.Install (nodes);

  // IPv4 Address Assignment
  Ipv4AddressHelper address;
  address.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer ip01 = address.Assign (dev01);

  address.SetBase ("10.1.2.0", "255.255.255.0");
  Ipv4InterfaceContainer ip12 = address.Assign (dev12);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

  // Install TCP Receiver (Sink) on n2
  uint16_t port = 9000;
  PacketSinkHelper sinkHelper ("ns3::TcpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), port));
  ApplicationContainer sinkApp = sinkHelper.Install (nodes.Get (2));
  sinkApp.Start (Seconds (0.0));
  sinkApp.Stop (Seconds (simTime));

  // Install TCP Sender (Source) on n0
  BulkSendHelper sourceHelper ("ns3::TcpSocketFactory", InetSocketAddress (ip12.GetAddress (1), port));
  sourceHelper.SetAttribute ("MaxBytes", UintegerValue (0));
  ApplicationContainer sourceApp = sourceHelper.Install (nodes.Get (0));
  sourceApp.Start (Seconds (1.0));
  sourceApp.Stop (Seconds (simTime));

  // Congestion Window Tracing
  std::string cwndFileName = "cwnd-TcpNewReno.dat";
  Simulator::Schedule (Seconds (1.01), &ConnectSocketTraces, cwndFileName);

  // Install FlowMonitor for Performance Analysis
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll ();

  // NetAnim Interface Configuration
  AnimationInterface anim ("Assn_4.xml");
  anim.SetConstantPosition (nodes.Get (0), 10.0, 30.0);
  anim.SetConstantPosition (nodes.Get (1), 30.0, 30.0);
  anim.SetConstantPosition (nodes.Get (2), 50.0, 30.0);

  // ASCII and PCAP Tracing
  if (tracing)
    {
      AsciiTraceHelper ascii;
      pointToPoint.EnableAsciiAll (ascii.CreateFileStream ("Assn_4.tr"));
      pointToPoint.EnablePcapAll ("Assn_4");
    }

  // Run Simulation
  Simulator::Stop (Seconds (simTime));
  Simulator::Run ();

  // Output Statistics
  monitor->CheckForLostPackets ();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier> (flowmon.GetClassifier ());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();

  for (auto iter = stats.begin (); iter != stats.end (); ++iter)
    {
      Ipv4FlowProbeTag ptag;
      FlowCharacteristics t = classifier->FindFlow (iter->first);
      if (t.sourceAddress == "10.1.1.1")
        {
          double duration = iter->second.timeLastRxPacket.GetSeconds () - iter->second.timeFirstRxPacket.GetSeconds ();
          double throughput = (iter->second.rxBytes * 8.0) / (duration * 1e6);

          std::cout << "\n================ RESULT ANALYSIS ================" << std::endl;
          std::cout << "TCP Variant    : TCP NewReno" << std::endl;
          std::cout << "Payload Size   : " << payloadSize << " bytes" << std::endl;
          std::cout << "Simulation Time: " << simTime << " s" << std::endl;
          std::cout << "Tx Packets     : " << iter->second.txPackets << std::endl;
          std::cout << "Rx Packets     : " << iter->second.rxPackets << std::endl;
          std::cout << "Packet Drops   : " << iter->second.lostPackets << std::endl;
          std::cout << "Throughput     : " << throughput << " Mbps" << std::endl;
          std::cout << "=================================================\n" << std::endl;
        }
    }

  Simulator::Destroy ();
  return 0;
}
