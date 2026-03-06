BEGIN {
    window      = 0.5
    total_delay = 0
    count       = 0
    t_start     = 0
    print "# time_mid(s)  avg_delay(ms)"
}

{
    event = $1
    time  = $2 + 0
    from  = $3 + 0
    to    = $4 + 0
    ptype = $5
    uid   = $12

    # Record first enqueue (+) at source nodes (0,1,2,3), TCP data only
    if (event == "+" && ptype == "tcp" && from >= 0 && from <= 3) {
        if (!(uid in send_time)) {
            send_time[uid] = time
        }
    }

    # Match receive at destination nodes (6,7,8,9)
    if (event == "r" && ptype == "tcp" && to >= 6 && to <= 9) {
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

    # Free memory
    for (u in send_time) delete send_time[u]
}
