# tahoe.tcl  –  TCP Tahoe vs UDP comparison (Lab 9)
# 6 nodes: n0=Node1(TCP-src), n1=Node2(router-L), n2=Node3(router-R),
#           n3=Node4(TCP-sink), n4=Node5(UDP-src), n5=Node6(UDP-sink)

set ns [new Simulator]

# ── Trace files ──────────────────────────────────────────────────────────────
set tf [open tahoe.tr w]
$ns trace-all $tf

set nf [open tahoe.nam w]
$ns namtrace-all $nf

# ── Flow colours (NAM) ───────────────────────────────────────────────────────
$ns color 1 Blue    ;# TCP flow
$ns color 2 Red     ;# UDP flow

# ── Nodes ────────────────────────────────────────────────────────────────────
set n0 [$ns node]   ;# Node 1 – TCP source
set n1 [$ns node]   ;# Node 2 – left  router
set n2 [$ns node]   ;# Node 3 – right router
set n3 [$ns node]   ;# Node 4 – TCP sink
set n4 [$ns node]   ;# Node 5 – UDP source
set n5 [$ns node]   ;# Node 6 – UDP sink

# ── Links ────────────────────────────────────────────────────────────────────
# Source / destination access links  →  300 Mbps, 20 ms
$ns duplex-link $n0 $n1  800Mb 20ms DropTail
$ns duplex-link $n2 $n3  800Mb 20ms DropTail
$ns duplex-link $n4 $n1  800Mb 20ms DropTail
$ns duplex-link $n2 $n5  800Mb 20ms DropTail

# Bottleneck link  →  1 Mbps, 10 ms  (bandwidth spec in assignment unclear;
#                                      1 Mb forces visible congestion)
$ns duplex-link $n1 $n2  1Mb  10ms DropTail

# ── NAM layout ───────────────────────────────────────────────────────────────
$ns duplex-link-op $n0 $n1 orient right-down
$ns duplex-link-op $n4 $n1 orient right-up
$ns duplex-link-op $n1 $n2 orient right
$ns duplex-link-op $n2 $n3 orient right-down
$ns duplex-link-op $n2 $n5 orient right-up

# ── TCP Tahoe  (Node 1 → Node 4) ────────────────────────────────────────────
set tcp  [new Agent/TCP]         ;# Tahoe is the default Agent/TCP
$tcp  set packetSize_ 1000
$tcp  set fid_        1
$ns attach-agent $n0 $tcp

set sink [new Agent/TCPSink]
$ns attach-agent $n3 $sink
$ns connect $tcp $sink

set ftp [new Application/FTP]
$ftp attach-agent $tcp

# ── UDP  (Node 5 → Node 6) ───────────────────────────────────────────────────
set udp  [new Agent/UDP]
$udp  set fid_ 2
$ns attach-agent $n4 $udp

set null [new Agent/Null]
$ns attach-agent $n5 $null
$ns connect $udp $null

set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set packetSize_ 512
$cbr set rate_       800Kb

# ── Schedule ─────────────────────────────────────────────────────────────────
$ns at  1.0   "$ftp start"
$ns at 15.0   "$cbr start"
$ns at 100.0  "$ftp stop"
$ns at 100.0  "$cbr stop"
$ns at 100.5  "finish"

proc finish {} {
    global ns tf nf
    $ns flush-trace
    close $tf
    close $nf
    puts "Tahoe simulation complete – trace written to tahoe.tr"
    exec nam tahoe.nam &
    exit 0
}

$ns run
