set terminal pngcairo size 1000,650 enhanced font 'Arial,13'
set grid lw 1 lc rgb "#cccccc"
set border lw 1.5

# Colour settings
set style line 1 lt 1 lw 2.5 lc rgb "#e74c3c"   # Drop-tail – red
set style line 2 lt 2 lw 2.5 lc rgb "#2980b9"   # RED       – blue
set style line 3 lt 3 lw 2.5 lc rgb "#27ae60"   # ARED      – green

set key top right box lw 1 spacing 1.3

# Average Queue Size
set output "queue_size.png"
set title  "Average Queue Size at Bottleneck Link (R1→R2)" font 'Arial,14'
set xlabel "Time (s)"
set ylabel "Queue Length (packets)"
set xrange [0:20]
set yrange [0:110]

plot \
  "DropTail_qsize.tr" using 1:2 with lines ls 1 title "Drop-tail", \
  "RED_qsize.tr"      using 1:2 with lines ls 2 title "RED",        \
  "ARED_qsize.tr"     using 1:2 with lines ls 3 title "Adaptive RED"

# Throughput
set output "throughput.png"
set title  "Aggregate Throughput at Destinations" font 'Arial,14'
set xlabel "Time (s)"
set ylabel "Throughput (Mbps)"
set xrange [0:20]
set yrange [0:*]

plot \
  "DropTail_tput.dat" using 1:2 with lines ls 1 title "Drop-tail", \
  "RED_tput.dat"      using 1:2 with lines ls 2 title "RED",        \
  "ARED_tput.dat"     using 1:2 with lines ls 3 title "Adaptive RED"

# End-to-End Delay
set output "delay.png"
set title  "Average End-to-End Delay" font 'Arial,14'
set xlabel "Time (s)"
set ylabel "Delay (ms)"
set xrange [0:20]
set yrange [0:*]

plot \
  "DropTail_delay.dat" using 1:2 with lines ls 1 title "Drop-tail", \
  "RED_delay.dat"      using 1:2 with lines ls 2 title "RED",        \
  "ARED_delay.dat"     using 1:2 with lines ls 3 title "Adaptive RED"

print "Plots written: queue_size.png  throughput.png  delay.png"
