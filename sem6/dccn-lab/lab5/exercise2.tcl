# Create Simulator
set ns [new Simulator]

# Define color
$ns color 1 Blue

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

# Create 7 nodes
set n0 [$ns node]
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

# Create ring links
$ns duplex-link $n0 $n1 1Mb 10ms DropTail
$ns duplex-link $n1 $n2 1Mb 10ms DropTail
$ns duplex-link $n2 $n3 1Mb 10ms DropTail
$ns duplex-link $n3 $n4 1Mb 10ms DropTail
$ns duplex-link $n4 $n5 1Mb 10ms DropTail
$ns duplex-link $n5 $n6 1Mb 10ms DropTail
$ns duplex-link $n6 $n0 1Mb 10ms DropTail   ;# closes the cycle

# Orient links for clean NAM layout
$ns duplex-link-op $n0 $n1 orient right
$ns duplex-link-op $n1 $n2 orient right
$ns duplex-link-op $n2 $n3 orient down
$ns duplex-link-op $n3 $n4 orient left
$ns duplex-link-op $n4 $n5 orient left
$ns duplex-link-op $n5 $n6 orient up
$ns duplex-link-op $n6 $n0 orient right

# TCP Agent at n0
set tcp0 [new Agent/TCP]
$tcp0 set class_ 1
$ns attach-agent $n0 $tcp0

# TCP Sink at n3
set sink0 [new Agent/TCPSink]
$ns attach-agent $n3 $sink0

# Connect
$ns connect $tcp0 $sink0

# FTP Application
set ftp0 [new Application/FTP]
$ftp0 attach-agent $tcp0

# Start/Stop
$ns at 0.5 "$ftp0 start"
$ns at 4.5 "$ftp0 stop"

# Finish
$ns at 5.0 "finish"

# Run
$ns run
