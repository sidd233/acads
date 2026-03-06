if {$argc < 1} {
    puts "Usage: ns sim.tcl <DropTail|RED|ARED>"
    exit 1
}

set qtype    [lindex $argv 0]
set sim_time 20.0
set pkt_size 1000

# Validate
if {$qtype != "DropTail" && $qtype != "RED" && $qtype != "ARED"} {
    puts "Error: queue type must be DropTail, RED, or ARED"
    exit 1
}

puts "Starting simulation: $qtype  (duration=${sim_time}s)"

# Simulator
set ns [new Simulator]

set tracefile [open "${qtype}.tr" w]
$ns trace-all $tracefile

# Nodes
set s(0) [$ns node]
set s(1) [$ns node]
set s(2) [$ns node]
set s(3) [$ns node]
set r1   [$ns node]
set r2   [$ns node]
set d(0) [$ns node]
set d(1) [$ns node]
set d(2) [$ns node]
set d(3) [$ns node]

# Links

# Si → R1  (100 Mbps, 25 ms, DropTail – not the bottleneck)
for {set i 0} {$i < 4} {incr i} {
    $ns duplex-link $s($i) $r1 100Mb 25ms DropTail
    $ns queue-limit $s($i) $r1 50
    $ns queue-limit $r1 $s($i) 50
}

# R1 ↔ R2  (10 Mbps, 100 ms – BOTTLENECK with chosen AQM)
if {$qtype == "DropTail"} {
    $ns duplex-link $r1 $r2 10Mb 100ms DropTail
} else {
    # Both RED and ARED use NS2's RED queue class
    $ns duplex-link $r1 $r2 10Mb 100ms RED
}
$ns queue-limit $r1 $r2 100
$ns queue-limit $r2 $r1 100

# R2 → Di  (100 Mbps, 25 ms, DropTail)
for {set i 0} {$i < 4} {incr i} {
    $ns duplex-link $r2 $d($i) 100Mb 25ms DropTail
    $ns queue-limit $r2 $d($i) 50
    $ns queue-limit $d($i) $r2 50
}

# RED / ARED Parameters
if {$qtype == "RED" || $qtype == "ARED"} {
    set redq [[$ns link $r1 $r2] queue]

    # Common RED parameters (queue-limit = 100 pkts)
    $redq set thresh_          20      ;# min threshold (packets)
    $redq set maxthresh_       60      ;# max threshold (packets)
    $redq set q_weight_        0.002   ;# queue weight for EWMA
    $redq set linterm_         10      ;# max drop probability = 1/linterm
    $redq set wait_            true
    $redq set setbit_          false
    $redq set drop_tail_       true
    $redq set queue_in_bytes_  false
    $redq set ns1_compat_      false

    if {$qtype == "ARED"} {
        # Adaptive RED: dynamically adjusts max_p
        $redq set adaptive_    1
        $redq set cautious_    1
        $redq set alpha_       0.01    ;# rate of increase for max_p
        $redq set beta_        0.9     ;# rate of decrease for max_p
        $redq set interval_    0.5     ;# update interval (s)
        $redq set targetdelay_ 0.005   ;# target queuing delay (s)
        $redq set top_         0.5     ;# upper bound for max_p
        $redq set bottom_      0.01    ;# lower bound for max_p
    }
}

# Queue-Size Monitor (sampled every 0.1 s)
set qmon [$ns monitor-queue $r1 $r2 ""]
set qf   [open "${qtype}_qsize.tr" w]
puts $qf "# time  queue_length_pkts"

proc record_queue {} {
    global ns qmon qf sim_time
    set now [$ns now]
    if {$now < $sim_time} {
        # pkts_ = instantaneous packet count in queue
        set qlen [$qmon set pkts_]
        if {$qlen < 0} { set qlen 0 }
        puts $qf "$now $qlen"
        $ns at [expr {$now + 0.1}] "record_queue"
    }
}
$ns at 0.0 "record_queue"

# TCP Flows (NewReno FTP)
for {set i 0} {$i < 4} {incr i} {
    # Sender
    set tcp($i) [new Agent/TCP/Newreno]
    $tcp($i) set packetSize_ $pkt_size
    $tcp($i) set window_     400
    $tcp($i) set maxcwnd_    400
    $ns attach-agent $s($i) $tcp($i)

    # Receiver
    set sink($i) [new Agent/TCPSink]
    $ns attach-agent $d($i) $sink($i)

    $ns connect $tcp($i) $sink($i)

    # Greedy FTP source
    set ftp($i) [new Application/FTP]
    $ftp($i) attach-agent $tcp($i)

    # Stagger starts slightly to avoid synchronisation
    $ns at [expr {0.5 + $i * 0.2}] "$ftp($i) start"
    $ns at [expr {$sim_time - 0.5}]  "$ftp($i) stop"
}

# Finish
proc finish {} {
    global ns tracefile qf qtype
    $ns flush-trace
    close $tracefile
    close $qf
    puts "Simulation $qtype complete."
    exit 0
}

$ns at $sim_time "finish"
$ns run
