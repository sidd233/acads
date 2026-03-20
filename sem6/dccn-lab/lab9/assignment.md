# National Institute of Technology, Rourkela

## DCCN Lab (CS3072)

### 6th Semester – 2026 Spring Semester

---

## Evaluation Scheme

* **Day to Day Evaluation:** 50 Marks
* **Viva:** 20 Marks
* **Quiz:** 30 Marks

---

## Instructions for the Lab

1. If a student is absent on the day of evaluation, they will be awarded **ZERO** for that evaluation.
2. Turn off your systems before leaving the lab.
3. Do not use mobile phones during lab hours.

---

## Lab 9

### Objective

**Performance Comparison of TCP Algorithms Tahoe/Reno: Throughput and Delay**

---

## Experiment

Write a **Tcl script** that forms a network consisting of **6 nodes**, numbered from **1 to 6**.

### Network Configuration

* Each **source and destination**:

  * Bandwidth: **300 Mbps**
  * Delay: **20 ms**

* **Bottleneck link**:

  * Bandwidth: **500 sec** *(as specified in assignment)*
  * Delay: **10 ms**

* **Queue discipline**:

  * DropTail

* Define **different colors** for different data flows.

---

### Traffic Setup

* Send:

  * **TCP packet** from **Node 1 → Node 4**
  * **UDP packet** from **Node 5 → Node 6**

* Transmission timing:

  * TCP starts at **1 sec**
  * UDP starts at **15 sec**
  * End simulation at **100 sec**

* Run **NAM** to visualize results.

* Assume:

  * **TCP Tahoe / TCP Reno** connection between source and sink

---

## Performance Metrics

Using an **AWK script**, compute and analyze:

### 1. Throughput

* Plot graph: **Tahoe vs Reno**

### 2. End-to-End Delay

* Plot graph: **Tahoe vs Reno**

---

## Output Requirements

* Graphs:

  * Throughput comparison
  * Delay comparison

* Tabular representation of results
