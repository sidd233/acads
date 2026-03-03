# ----------------------------------------
# RED Simulation - Fully Working Version
# ----------------------------------------

set ns [new Simulator]

# Trace file
set tracefile [open out_red.tr w]
$ns trace-all $tracefile

# Queue output file
set qfile [open queue_red.tr w]

# Create Nodes
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

# Access links (100Mbps, 25ms) — match Figure-1
$ns duplex-link $S0 $R1 100Mb 25ms DropTail
$ns duplex-link $S1 $R1 100Mb 25ms DropTail
$ns duplex-link $S2 $R1 100Mb 25ms DropTail
$ns duplex-link $S3 $R1 100Mb 25ms DropTail

# Bottleneck (10Mbps, 100ms) — match Figure-1
$ns duplex-link $R1 $R2 10Mb 100ms RED
$ns queue-limit $R1 $R2 1000

# Output links (100Mbps, 25ms)
$ns duplex-link $R2 $D0 100Mb 25ms DropTail
$ns duplex-link $R2 $D1 100Mb 25ms DropTail
$ns duplex-link $R2 $D2 100Mb 25ms DropTail
$ns duplex-link $R2 $D3 100Mb 25ms DropTail

# RED parameters (adjusted for larger queue)
Queue/RED set minthresh_ 50
Queue/RED set maxthresh_ 150
Queue/RED set q_weight_ 0.002
Queue/RED set linterm_ 10
Queue/RED set gentle_ true
Queue/RED set max_p_ 0.1

# ----------------------------------------
# Access the queue directly (IMPORTANT)
# ----------------------------------------

set link [$ns link $R1 $R2]
set queue [$link queue]

# Record queue size every 0.01 sec
proc record {} {
    global ns queue qfile
    set time [$ns now]
    set qsize [$queue set curq_]
    puts $qfile "$time $qsize"
    $ns at [expr $time + 0.01] "record"
}

$ns at 0.0 "record"

# ----------------------------------------
# Create TCP Connections
# ----------------------------------------

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

# Stop simulation
$ns at 10.0 "finish"

proc finish {} {
    global ns tracefile qfile
    $ns flush-trace
    close $tracefile
    close $qfile
    exit 0
}

$ns run