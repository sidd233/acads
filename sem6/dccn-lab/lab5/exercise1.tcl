# Create Simulator
set ns [new Simulator]

# Define colors
$ns color 1 Blue
$ns color 2 Red
$ns color 3 Green

# Open NAM trace
set nf [open out.nam w]
$ns namtrace-all $nf

# Finish procedure
proc finish {} {
    global ns nf
    $ns flush-trace
    close $nf
    exec nam out.nam &
    exit 0
}

# Create nodes
set n0 [$ns node]   ;# TCP sender 1
set n1 [$ns node]   ;# Router
set n2 [$ns node]   ;# TCP sender 2
set n3 [$ns node]   ;# Receiver
set n4 [$ns node]   ;# UDP sender

# Create links
$ns duplex-link $n0 $n1 1Mb 10ms DropTail
$ns duplex-link $n2 $n1 1Mb 10ms DropTail
$ns duplex-link $n4 $n1 1Mb 10ms DropTail
$ns duplex-link $n1 $n3 1Mb 10ms DropTail

# Set orientations (for clean NAM view)
$ns duplex-link-op $n0 $n1 orient right-down
$ns duplex-link-op $n2 $n1 orient right-up
$ns duplex-link-op $n4 $n1 orient left-down
$ns duplex-link-op $n1 $n3 orient right
$ns duplex-link-op $n1 $n3 queuePos 0.5

# ---------------- TCP Flow 1 ----------------
set tcp0 [new Agent/TCP]
$tcp0 set class_ 1
$ns attach-agent $n0 $tcp0

set sink0 [new Agent/TCPSink]
$ns attach-agent $n3 $sink0
$ns connect $tcp0 $sink0

set ftp0 [new Application/FTP]
$ftp0 attach-agent $tcp0

# ---------------- TCP Flow 2 ----------------
set tcp1 [new Agent/TCP]
$tcp1 set class_ 2
$ns attach-agent $n2 $tcp1

set sink1 [new Agent/TCPSink]
$ns attach-agent $n3 $sink1
$ns connect $tcp1 $sink1

set ftp1 [new Application/FTP]
$ftp1 attach-agent $tcp1

# ---------------- UDP Flow ----------------
set udp0 [new Agent/UDP]
$udp0 set class_ 3
$ns attach-agent $n4 $udp0

set null0 [new Agent/Null]
$ns attach-agent $n3 $null0
$ns connect $udp0 $null0

set cbr0 [new Application/Traffic/CBR]
$cbr0 set packetSize_ 500
$cbr0 set interval_ 0.005
$cbr0 attach-agent $udp0

# Schedule traffic
$ns at 0.5 "$ftp0 start"
$ns at 1.0 "$ftp1 start"
$ns at 1.5 "$cbr0 start"

$ns at 4.0 "$cbr0 stop"
$ns at 4.5 "$ftp1 stop"
$ns at 5.0 "$ftp0 stop"

# End simulation
$ns at 6.0 "finish"

# Run
$ns run
