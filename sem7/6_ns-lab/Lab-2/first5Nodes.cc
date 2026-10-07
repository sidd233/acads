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
#include "ns3/netanim-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("FirstScriptExample");

int
main (int argc, char *argv[])
{
  bool tracing=true;
  CommandLine cmd;
  cmd.Parse (argc, argv);
  cmd.AddValue("tracing","Enable pcap tracing",tracing);
  
  Time::SetResolution (Time::NS);
  LogComponentEnable ("UdpEchoClientApplication", LOG_LEVEL_INFO);
  LogComponentEnable ("UdpEchoServerApplication", LOG_LEVEL_INFO);

  NodeContainer nodes;
  nodes.Create (5);

  PointToPointHelper pointToPoint;
  pointToPoint.SetDeviceAttribute ("DataRate", StringValue ("5Mbps"));
  pointToPoint.SetChannelAttribute ("Delay", StringValue ("2ms"));

  NetDeviceContainer devices;
  devices = pointToPoint.Install (nodes.Get(0),nodes.Get(1));
  NetDeviceContainer devices1;
  devices1 = pointToPoint.Install (nodes.Get(2),nodes.Get(1));
  NetDeviceContainer devices2;
  devices2 = pointToPoint.Install (nodes.Get(3),nodes.Get(1));
  NetDeviceContainer devices3;
  devices3 = pointToPoint.Install (nodes.Get(4),nodes.Get(1));
  

  InternetStackHelper stack;
  stack.Install (nodes);

  Ipv4AddressHelper address;
  address.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4AddressHelper address1;
  address1.SetBase ("10.1.2.0", "255.255.255.0");
  Ipv4AddressHelper address2;
  address2.SetBase ("10.1.3.0", "255.255.255.0");
  Ipv4AddressHelper address3;
  address3.SetBase ("10.1.4.0", "255.255.255.0");

  Ipv4InterfaceContainer interfaces = address.Assign (devices);
  Ipv4InterfaceContainer interfaces1 = address1.Assign (devices1);
  Ipv4InterfaceContainer interfaces2 = address2.Assign (devices2);
  Ipv4InterfaceContainer interfaces3 = address3.Assign (devices3);

  UdpEchoServerHelper echoServer (90);
  UdpEchoServerHelper echoServer1 (91);
  UdpEchoServerHelper echoServer2 (92);
  UdpEchoServerHelper echoServer3 (93);

  ApplicationContainer serverApps = echoServer.Install (nodes.Get (1));
  serverApps.Start (Seconds (1.0));
  serverApps.Stop (Seconds (20.0));

  UdpEchoClientHelper echoClient (interfaces.GetAddress (1), 90);
  echoClient.SetAttribute ("MaxPackets", UintegerValue (1));
  echoClient.SetAttribute ("Interval", TimeValue (Seconds (1.0)));
  echoClient.SetAttribute ("PacketSize", UintegerValue (1024));
  
  UdpEchoClientHelper echoClient1 (interfaces1.GetAddress (1), 91);
  echoClient1.SetAttribute ("MaxPackets", UintegerValue (1));
  echoClient1.SetAttribute ("Interval", TimeValue (Seconds (1.0)));
  echoClient1.SetAttribute ("PacketSize", UintegerValue (1024));
  
  UdpEchoClientHelper echoClient2 (interfaces2.GetAddress (1), 92);
  echoClient2.SetAttribute ("MaxPackets", UintegerValue (1));
  echoClient2.SetAttribute ("Interval", TimeValue (Seconds (1.0)));
  echoClient2.SetAttribute ("PacketSize", UintegerValue (1024));
  
  UdpEchoClientHelper echoClient3 (interfaces3.GetAddress (1), 93);
  echoClient3.SetAttribute ("MaxPackets", UintegerValue (1));
  echoClient3.SetAttribute ("Interval", TimeValue (Seconds (1.0)));
  echoClient3.SetAttribute ("PacketSize", UintegerValue (1024));

  ApplicationContainer clientApps = echoClient.Install (nodes.Get (0));
  clientApps.Start (Seconds (2.0));
  clientApps.Stop (Seconds (10.0));
  
  ApplicationContainer clientApps1 = echoClient1.Install (nodes.Get (2));
  clientApps1.Start (Seconds (7.0));
  clientApps1.Stop (Seconds (10.0));
  
  ApplicationContainer clientApps2 = echoClient2.Install (nodes.Get (3));
  clientApps2.Start (Seconds (10.0));
  clientApps2.Stop (Seconds (15.0));
  
  ApplicationContainer clientApps3 = echoClient3.Install (nodes.Get (4));
  clientApps3.Start (Seconds (13.0));
  clientApps3.Stop (Seconds (20.0));
  
  
  AnimationInterface anim("five.xml");
  anim.SetConstantPosition(nodes.Get(0),10.0,20.0);
  anim.SetConstantPosition(nodes.Get(1),20.0,30.0);
  anim.SetConstantPosition(nodes.Get(2),40.0,5.0);
  anim.SetConstantPosition(nodes.Get(3),10.0,40.0);
  anim.SetConstantPosition(nodes.Get(4),40.0,40.0);
  
  AsciiTraceHelper ascii;
  pointToPoint.EnableAsciiAll(ascii.CreateFileStream("five.tr"));
  
  if(tracing==true){
    pointToPoint.EnablePcapAll("five"); 
  }
  

  Simulator::Run ();
  Simulator::Destroy ();
  return 0;
}
