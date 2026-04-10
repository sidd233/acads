# Performance Comparison of TCP Reno and TCP BIC Congestion Control Algorithms

## 1. Introduction

Transmission Control Protocol (TCP) is a core protocol of the Internet that ensures reliable data transmission between hosts. A critical component of TCP is **congestion control**, which regulates the rate of data transmission to avoid network congestion.

Over time, several congestion control algorithms have been developed. Among them:

* **TCP Reno** – a classical and widely used algorithm based on Additive Increase Multiplicative Decrease (AIMD)
* **TCP BIC (Binary Increase Congestion Control)** – a more advanced algorithm designed for high-speed and long-distance networks

This report presents a **comparative analysis of TCP Reno and TCP BIC** based on simulated congestion window (cwnd) behavior.

---

## 2. Objective

The objective of this experiment is to:

* Simulate and compare the behavior of TCP Reno and TCP BIC
* Analyze their performance in terms of:

  * Congestion window growth
  * Response to packet loss
  * Bandwidth utilization
* Demonstrate why BIC performs better in modern high-bandwidth networks

---

## 3. Methodology

### 3.1 Simulation Approach

Instead of using full-scale network simulation tools, a **custom C++ simulation** was developed to model the core behavior of congestion control algorithms.

The simulation:

* Runs over discrete time steps (representing RTTs)
* Introduces **random packet loss**
* Tracks the **congestion window (cwnd)** evolution over time

---

### 3.2 TCP Reno Model

TCP Reno follows the **AIMD strategy**:

* **Increase Phase**:

  * cwnd increases linearly:

    ```
    cwnd += 1 / cwnd
    ```

* **Loss Event**:

  * cwnd is reduced by half:

    ```
    cwnd = cwnd / 2
    ```

This results in a **sawtooth pattern** of growth and reduction.

---

### 3.3 TCP BIC Model

TCP BIC uses a **binary search-based approach**:

* Maintains:

  * `Wmax` → last maximum window before loss
  * `Wmin` → reduced window after loss

* Growth strategy:

  * Performs binary search between `Wmin` and `Wmax`
  * Uses aggressive probing when near the target

* Loss handling:

  * Reduces cwnd multiplicatively
  * Updates search bounds

This allows BIC to:

* Recover faster after loss
* Utilize bandwidth more efficiently

---

### 3.4 Data Collection

The simulation outputs:

* Time step
* TCP Reno cwnd
* TCP BIC cwnd

These values are stored in a file (`output.dat`) and plotted using **Gnuplot**.

---

## 4. Implementation

### 4.1 Tools Used

* **C++** – for simulation logic
* **Gnuplot** – for visualization
* **Shell Script** – to automate compilation, execution, and plotting

---

### 4.2 Workflow

1. Compile C++ program
2. Run simulation
3. Generate data file
4. Plot graph using Gnuplot
5. Export graph as PNG

---

## 5. Results

The generated graph (`comparison.png`) shows the variation of congestion window over time for both algorithms.

### Key Observations:

* **TCP Reno**:

  * Gradual linear growth
  * Sharp drops on packet loss
  * Slower recovery

* **TCP BIC**:

  * Faster growth after loss
  * More aggressive probing
  * Higher average cwnd

---

## 6. Analysis

### 6.1 Throughput

Since throughput is proportional to cwnd:

* BIC achieves **higher throughput**
* Reno underutilizes available bandwidth in high-speed networks

---

### 6.2 Loss Recovery

* Reno:

  * Slow recovery due to linear increase
* BIC:

  * Faster recovery due to binary search mechanism

---

### 6.3 Efficiency

* Reno is suitable for:

  * Low bandwidth networks
  * Simpler environments

* BIC is better for:

  * High bandwidth-delay product networks
  * Modern internet infrastructure

---

## 7. Advantages of TCP BIC

* Faster convergence to optimal bandwidth
* Better utilization of network resources
* Reduced time to recover from congestion
* Scalable for high-speed networks

---

## 8. Limitations

* BIC can be more aggressive, which may:

  * Affect fairness in mixed environments
* Simplified simulation does not include:

  * Real queueing delays
  * RTT variation
  * Multi-flow fairness

---

## 9. Conclusion

This study demonstrates that:

* TCP Reno provides stable but conservative congestion control
* TCP BIC significantly improves performance in terms of:

  * Faster recovery
  * Higher throughput
  * Better bandwidth utilization

Therefore, TCP BIC is more suitable for modern high-speed networks, while TCP Reno remains useful for simpler scenarios.

---

## 10. Future Work

* Extend simulation to include:

  * Multiple flows
  * Variable RTT
  * Queueing effects
* Compare with:

  * TCP Cubic
  * TCP Vegas
* Implement full network simulation (e.g., NS2/NS3)

---

## 11. References

1. Stevens, W. R. – *TCP/IP Illustrated*
2. Xu, L., Harfoush, K., Rhee, I. – *Binary Increase Congestion Control (BIC)*
3. RFC 5681 – TCP Congestion Control
4. NS2 Documentation

---
