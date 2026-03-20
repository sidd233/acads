#!/usr/bin/env bash
set -e

echo "=== Running TCP Tahoe simulation ==="
ns tahoe.tcl

echo "=== Running TCP Reno simulation ==="
ns reno.tcl

echo "=== Computing throughput ==="
awk -f analyze_throughput.awk tahoe.tr > tahoe_tput.dat
awk -f analyze_throughput.awk reno.tr  > reno_tput.dat

echo "=== Computing end-to-end delay ==="
awk -f analyze_delay.awk tahoe.tr > tahoe_delay.dat
awk -f analyze_delay.awk reno.tr  > reno_delay.dat

echo "=== Plotting graphs ==="
gnuplot plot.gp

echo ""
echo "Done. Output files:"
echo "  throughput.png   – Throughput comparison (Tahoe vs Reno)"
echo "  delay.png        – Delay comparison      (Tahoe vs Reno)"
echo ""

# ── Summary table ────────────────────────────────────────────────────────────
echo "=== Summary Table ==="
printf "%-12s  %-20s  %-20s\n" "Algorithm" "Avg Throughput (Mbps)" "Avg Delay (ms)"
printf "%-12s  %-20s  %-20s\n" "---------" "---------------------" "--------------"

for algo in tahoe reno; do
    tput_avg=$(awk 'NR>1 {sum+=$2; n++} END {if(n>0) printf "%.4f", sum/n}' ${algo}_tput.dat)
    delay_avg=$(awk 'NR>1 {sum+=$2; n++} END {if(n>0) printf "%.4f", sum/n}' ${algo}_delay.dat)
    printf "%-12s  %-20s  %-20s\n" "TCP ${algo^}" "$tput_avg" "$delay_avg"
done
