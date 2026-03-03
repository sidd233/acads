# DropTail AQM Simulation

set ns [new Simulator]

set tf [open out.tr w]
$ns trace-all $tf

set qf [open queue_droptail.tr w]

# Create nodes
set S0 [$ns node]
set S1 [$ns node]
set S2 [$ns node]
set S3 [$ns node]

set R1 [$ns node]
set R2 [$ns node]

set D0 [$ns node]
set D1 [$ns node]
set D2 [$ns node]
set D3 [$ns node]

# Links
$ns duplex-link $S0 $R1 10Mb 10ms DropTail
$ns duplex-link $S1 $R1 10Mb 10ms DropTail
$ns duplex-link $S2 $R1 10Mb 10ms DropTail
$ns duplex-link $S3 $R1 10Mb 10ms DropTail

# Bottleneck
$ns duplex-link $R1 $R2 1Mb 20ms DropTail
$ns queue-limit $R1 $R2 50

$ns duplex-link $R2 $D0 10Mb 10ms DropTail
$ns duplex-link $R2 $D1 10Mb 10ms DropTail
$ns duplex-link $R2 $D2 10Mb 10ms DropTail
$ns duplex-link $R2 $D3 10Mb 10ms DropTail

# Queue monitoring
set qmon [$ns monitor-queue $R1 $R2 $qf]

# TCP Connections
for {set i 0} {$i < 4} {incr i} {
    set tcp($i) [new Agent/TCP]
    set sink($i) [new Agent/TCPSink]
}

$ns attach-agent $S0 $tcp(0)
$ns attach-agent $D0 $sink(0)
$ns connect $tcp(0) $sink(0)

$ns attach-agent $S1 $tcp(1)
$ns attach-agent $D1 $sink(1)
$ns connect $tcp(1) $sink(1)

$ns attach-agent $S2 $tcp(2)
$ns attach-agent $D2 $sink(2)
$ns connect $tcp(2) $sink(2)

$ns attach-agent $S3 $tcp(3)
$ns attach-agent $D3 $sink(3)
$ns connect $tcp(3) $sink(3)

# FTP Applications
for {set i 0} {$i < 4} {incr i} {
    set ftp($i) [new Application/FTP]
    $ftp($i) attach-agent $tcp($i)
    $ns at 1.0 "$ftp($i) start"
}

$ns at 10.0 "finish"

proc finish {} {
    global ns tf qf
    $ns flush-trace
    close $tf
    close $qf
    exec nam out.nam &
    exit 0
}

$ns run