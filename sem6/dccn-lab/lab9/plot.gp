set terminal pngcairo size 1000,650 enhanced font 'Arial,13'
set grid lw 1 lc rgb "#cccccc"
set border lw 1.5

set style line 1 lt 1 lw 2.5 lc rgb "#e74c3c"   # Tahoe – red
set style line 2 lt 2 lw 2.5 lc rgb "#2980b9"   # Reno  – blue

set key top right box lw 1 spacing 1.3

# ── Throughput ───────────────────────────────────────────────────────────────
set output "throughput.png"
set title  "TCP Throughput: Tahoe vs Reno" font 'Arial,14'
set xlabel "Time (s)"
set ylabel "Throughput (Mbps)"
set xrange [0:100]
set yrange [0:*]

plot \
  "tahoe_tput.dat" using 1:2 with lines ls 1 title "TCP Tahoe", \
  "reno_tput.dat"  using 1:2 with lines ls 2 title "TCP Reno"

# ── End-to-End Delay ─────────────────────────────────────────────────────────
set output "delay.png"
set title  "TCP End-to-End Delay: Tahoe vs Reno" font 'Arial,14'
set xlabel "Time (s)"
set ylabel "Average Delay (ms)"
set xrange [0:100]
set yrange [0:*]

plot \
  "tahoe_delay.dat" using 1:2 with lines ls 1 title "TCP Tahoe", \
  "reno_delay.dat"  using 1:2 with lines ls 2 title "TCP Reno"

print "Plots written: throughput.png  delay.png"
