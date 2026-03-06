set -e   # stop on first error

echo "======================================================"
echo "  DCCN Lab 7 - AQM Performance Comparison"
echo "======================================================"

# Simulations
for QT in DropTail RED ARED; do
    echo ""
    echo "[1] Running NS2 simulation: $QT ..."
    ns sim.tcl "$QT"
done

# Throughput analysis
echo ""
echo "[2] Analysing throughput ..."
for QT in DropTail RED ARED; do
    awk -f analyze_throughput.awk "${QT}.tr" > "${QT}_tput.dat"
    echo "    Wrote ${QT}_tput.dat"
done

# Delay analysis
echo ""
echo "[3] Analysing end-to-end delay ..."
for QT in DropTail RED ARED; do
    awk -f analyze_delay.awk "${QT}.tr" > "${QT}_delay.dat"
    echo "    Wrote ${QT}_delay.dat"
done

# gnuplot
echo ""
echo "[4] Generating plots with gnuplot ..."
gnuplot plot.gp

echo ""
echo "======================================================"
echo "  Done!  Output files:"
echo "    queue_size.png   throughput.png   delay.png"
echo "======================================================"
