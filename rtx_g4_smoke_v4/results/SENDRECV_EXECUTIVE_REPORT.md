# 2-Node P2P Send/Recv vs Intra-Node Baseline Characterization
**Target Hardware:** 2 Nodes × 8x NVIDIA RTX PRO 6000 Ada (Blackwell Generation Server Nodes)  
**Methodology:** Live NCCL `sendrecv_perf` benchmarks across all payload sizes (8 KiB to 256 MiB).  
**Evidence Level:** `MEASURED-GCP-HW` (100% Real Empirical VM Telemetry).

---

## 1. Executive Summary & Key Architectural Findings
1. **Decode Latency Floor (α-bound):**
   - Intra-NUMA (same socket): **0.0091 ms (9.1 µs)**.
   - Cross-NUMA (inter-socket UPI): **0.0092 ms (9.2 µs)**.
   - 2-Node P2P (175G Native TCP): **0.0801 ms (80.1 µs)**.
   - *Key Takeaway:* 2-Node network hop incurs an ~8.8x latency penalty over local PCIe on small decode tokens due to Linux network stack traversal.
2. **Prefill Throughput & Bandwidth (β-bound):**
   - At 256 MiB payload, 2-node P2P over 175G native fabric reaches **2.75 GB/s (97.54 ms)**.
   - Throttling to 10G caps bandwidth at **1.19 GB/s (~9.52 Gbps, saturating 10G link)**, pushing latency to **225.36 ms (31.4x slowdown over local PCIe)**.

---

## 2. Empirical Benchmark Table (All Units in Milliseconds - ms)
| Buffer Size | Payload Label | Local Intra-NUMA (ms) | Local Cross-NUMA (ms) | 2-Node 175G Native (ms) | 2-Node 100G (ms) | 2-Node 50G (ms) | 2-Node 20G (ms) | 2-Node 10G (ms) | 10G vs Local Intra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 16384 | **16.0 KiB** | 0.0091 ms | 0.0092 ms | 0.0801 ms | 0.0783 ms | 0.0817 ms | 0.0967 ms | **0.1109 ms** | **12.19x** |
| 32768 | **32.0 KiB** | 0.0092 ms | 0.0115 ms | 0.1105 ms | 0.0888 ms | 0.1681 ms | 0.1268 ms | **0.1366 ms** | **14.85x** |
| 65536 | **64.0 KiB** | 0.0112 ms | 0.0128 ms | 0.1361 ms | 0.1557 ms | 0.1232 ms | 0.1322 ms | **0.1164 ms** | **10.39x** |
| 131072 | **128.0 KiB** | 0.0134 ms | 0.0152 ms | 0.1944 ms | 3.0297 ms | 0.2092 ms | 0.1896 ms | **0.1969 ms** | **14.69x** |
| 262144 | **256.0 KiB** | 0.0181 ms | 0.0221 ms | 0.2792 ms | 0.2863 ms | 0.2428 ms | 0.2643 ms | **0.2618 ms** | **14.46x** |
| 524288 | **512.0 KiB** | 0.0247 ms | 0.0356 ms | 0.4217 ms | 0.4175 ms | 0.3811 ms | 0.4498 ms | **0.4383 ms** | **17.74x** |
| 1048576 | **1.0 MiB** | 0.0393 ms | 0.0625 ms | 0.6315 ms | 0.9820 ms | 0.5316 ms | 0.5886 ms | **0.8884 ms** | **22.61x** |
| 2097152 | **2.0 MiB** | 0.0670 ms | 0.1162 ms | 1.5240 ms | 1.5490 ms | 1.0146 ms | 0.9986 ms | **1.9137 ms** | **28.56x** |
| 4194304 | **4.0 MiB** | 0.1211 ms | 0.2224 ms | 1.9447 ms | 2.0052 ms | 2.7329 ms | 1.7670 ms | **3.6665 ms** | **30.28x** |
| 8388608 | **8.0 MiB** | 0.2394 ms | 0.2384 ms | 2.9174 ms | 2.9870 ms | 2.8662 ms | 3.5216 ms | **7.0664 ms** | **29.52x** |
| 16777216 | **16.0 MiB** | 0.4588 ms | 0.4574 ms | 5.3436 ms | 5.6649 ms | 6.5830 ms | 7.1948 ms | **14.1652 ms** | **30.87x** |
| 33554432 | **32.0 MiB** | 0.8996 ms | 0.8951 ms | 15.3203 ms | 11.8002 ms | 13.1559 ms | 15.2430 ms | **28.2360 ms** | **31.39x** |
| 67108864 | **64.0 MiB** | 1.8029 ms | 1.7955 ms | 22.8137 ms | 20.9585 ms | 20.3424 ms | 30.4593 ms | **56.5672 ms** | **31.38x** |
| 134217728 | **128.0 MiB** | 3.6033 ms | 3.5844 ms | 52.2815 ms | 48.8725 ms | 50.1481 ms | 60.7517 ms | **112.7250 ms** | **31.28x** |
| 268435456 | **256.0 MiB** | 7.1798 ms | 7.1432 ms | 97.5356 ms | 102.4840 ms | 106.6850 ms | 116.6710 ms | **225.3560 ms** | **31.39x** |
