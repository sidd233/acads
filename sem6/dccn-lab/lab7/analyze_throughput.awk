BEGIN {
    window    = 0.5     # time window width (seconds)
    bytes     = 0
    t_start   = 0
    print "# time_mid(s)  throughput(Mbps)"
}

{
    event = $1
    time  = $2 + 0
    to    = $4 + 0
    ptype = $5
    size  = $6 + 0

    # Only 'r' (receive) events at destination nodes for TCP data
    if (event == "r" && ptype == "tcp" && to >= 6 && to <= 9) {

        # Have we crossed into the next window?
        while (time >= t_start + window) {
            mid        = t_start + window / 2.0
            throughput = (bytes * 8.0) / (window * 1e6)   # Mbps
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
