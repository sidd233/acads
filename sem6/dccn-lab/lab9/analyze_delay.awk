# analyze_delay.awk
# Usage: awk -f analyze_delay.awk <trace_file>
#
# Computes average TCP end-to-end delay (ms) in 1-second windows.
# Records first enqueue (+) at TCP source (node 0) and
# matches to receive (r) at TCP sink (node 3), keyed on pkt-uid ($12).

BEGIN {
    window      = 1.0
    total_delay = 0
    count       = 0
    t_start     = 1.0
    print "# time_mid(s)  avg_delay(ms)"
}

{
    event = $1
    time  = $2 + 0
    from  = $3 + 0
    to    = $4 + 0
    ptype = $5
    fid   = $8 + 0
    uid   = $12

    # Record first send (+) at TCP source, flow 1
    if (event == "+" && ptype == "tcp" && from == 0 && fid == 1) {
        if (!(uid in send_time))
            send_time[uid] = time
    }

    # Match receive at TCP sink, flow 1
    if (event == "r" && ptype == "tcp" && to == 3 && fid == 1) {
        if (uid in send_time) {
            delay_s = time - send_time[uid]
            delete send_time[uid]

            # Flush completed windows
            while (time >= t_start + window) {
                mid = t_start + window / 2.0
                if (count > 0)
                    printf "%.4f  %.6f\n", mid, (total_delay / count) * 1000.0
                else
                    printf "%.4f  0.000000\n", mid
                total_delay = 0
                count       = 0
                t_start     = t_start + window
            }

            total_delay += delay_s
            count++
        }
    }
}

END {
    if (count > 0) {
        mid = t_start + window / 2.0
        printf "%.4f  %.6f\n", mid, (total_delay / count) * 1000.0
    }
    for (u in send_time) delete send_time[u]
}
