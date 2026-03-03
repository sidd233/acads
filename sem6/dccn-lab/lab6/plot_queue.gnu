set terminal png size 800,600
set output "comp.png"

set title "Instantaneous Queue Size: RED vs Adaptive RED"
set xlabel "Time (sec)"
set ylabel "Queue Size (packets)"
set grid

plot "queue_red.tr" using 1:2 with lines title "RED", \
     "queue_ared.tr" using 1:2 with lines title "Adaptive RED"

pause -1