#!/bin/bash

echo "🔧 Compiling..."
g++ bic_vs_reno.cpp -o sim

echo "🚀 Running simulation..."
./sim

echo "📊 Generating plot..."

gnuplot <<EOF
set terminal png size 1000,600
set output "comparison.png"

set title "TCP Reno vs BIC Congestion Control"
set xlabel "Time (RTT steps)"
set ylabel "Congestion Window (cwnd)"
set grid

plot "output.dat" using 1:2 with lines lw 2 title "TCP Reno", \
     "output.dat" using 1:3 with lines lw 2 title "TCP BIC"
EOF

echo "✅ Done! Output file: comparison.png"