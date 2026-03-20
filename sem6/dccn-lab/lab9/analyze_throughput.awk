# analyze_throughput.awk
# Usage: awk -f analyze_throughput.awk <trace_file>
#
# Computes TCP throughput (Mbps) in 1-second windows.
# TCP sink is node 3 (0-indexed) – "r" events, ptype "tcp", fid 1.

BEGIN {
    window  = 1.0
    bytes   = 0
    t_start = 1.0      # TCP starts at 1 s
    print "# time_mid(s)  throughput(Mbps)"
}

{
    event = $1
    time  = $2 + 0
    to    = $4 + 0
    ptype = $5
    size  = $6 + 0
    fid   = $8 + 0

    # Receive events at TCP sink (node index 3), TCP data, flow 1
    if (event == "r" && ptype == "tcp" && to == 3 && fid == 1) {

        # Flush completed windows
        while (time >= t_start + window) {
            mid        = t_start + window / 2.0
            throughput = (bytes * 8.0) / (window * 1e6)
            printf "%.4f  %.6f\n", mid, throughput
            bytes   = 0
            t_start = t_start + window
        }

        bytes += size
    }
}

END {
    if (bytes > 0) {
        mid        = t_start + window / 2.0
        throughput = (bytes * 8.0) / (window * 1e6)
        printf "%.4f  %.6f\n", mid, throughput
    }
}
