# AllToAll Distributed Characterization (TP16, TP8, TP4 vs Local)
**Target Hardware:** 2 Nodes × 8x NVIDIA RTX PRO 6000 Ada (16 GPUs Multi-Node)  
**Methodology:** Live NCCL `alltoall_perf` sweeps across 5 network bandwidth tiers (10G - 175G) and local intra-node baselines.  
**Evidence Level:** `MEASURED-GCP-HW` (100% Real Empirical VM Telemetry).

---

## 1. Executive Summary & All-to-All Fabric Stress Analysis
1. **All-to-All Cross-Traffic Congestion:**
   - In TP16 AllToAll, every GPU sends a separate slice to all 15 other GPUs ($16 \times 15 = 240$ simultaneous traffic flows, 128 of which cross the physical network interface).
   - At 10G network cap, inter-node queueing explodes: 256 MiB AllToAll latency climbs to **1242.26 ms (1.24 seconds)**, compared to **11.01 ms** on single-node TP8 (**112.8x penalty!**).
2. **NUMA / Socket-Local TP4 Baseline:**
   - TP4 local AllToAll achieves **0.016 ms (16 µs)** latency floor and up to **24.5 GB/s** algorithmic bandwidth.
   - Multi-node TP4 (2 GPUs per node) incurs ~0.25 ms floor due to network sync.

---

## 2. Empirical Benchmark Table (TP16 vs Local TP8 Baseline)
| Buffer Size | Payload Label | TP8 Local (ms) | TP16 175G Native (ms) | TP16 100G (ms) | TP16 50G (ms) | TP16 20G (ms) | TP16 10G (ms) | 10G vs Local TP8 Penalty |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 16384 | **16.0 KiB** | 0.0134 ms | 0.3327 ms | 0.8749 ms | 0.8645 ms | 0.9054 ms | **0.8392 ms** | **62.63x** |
| 32768 | **32.0 KiB** | 0.0834 ms | 0.6008 ms | 0.8868 ms | 1.4048 ms | 0.9161 ms | **1.0641 ms** | **12.76x** |
| 65536 | **64.0 KiB** | 0.0272 ms | 0.3342 ms | 1.1982 ms | 1.0143 ms | 1.0259 ms | **0.9352 ms** | **34.38x** |
| 131072 | **128.0 KiB** | 0.0462 ms | 0.3741 ms | 1.0417 ms | 1.0430 ms | 1.0520 ms | **1.0438 ms** | **22.59x** |
| 262144 | **256.0 KiB** | 0.0296 ms | 0.5893 ms | 1.5292 ms | 1.0989 ms | 1.1007 ms | **1.1478 ms** | **38.78x** |
| 524288 | **512.0 KiB** | 0.0448 ms | 0.5120 ms | 1.1943 ms | 1.2013 ms | 1.2426 ms | **2.5427 ms** | **56.76x** |
| 1048576 | **1.0 MiB** | 0.0758 ms | 0.9222 ms | 2.2831 ms | 2.7147 ms | 2.4735 ms | **6.3200 ms** | **83.38x** |
| 2097152 | **2.0 MiB** | 0.1353 ms | 2.2468 ms | 3.5090 ms | 2.9256 ms | 5.5052 ms | **13.0088 ms** | **96.15x** |
| 4194304 | **4.0 MiB** | 0.2477 ms | 2.6194 ms | 4.9816 ms | 4.9599 ms | 12.4573 ms | **46.0173 ms** | **185.78x** |
| 8388608 | **8.0 MiB** | 0.4625 ms | 4.7197 ms | 8.9384 ms | 8.6030 ms | 40.1670 ms | **88.4205 ms** | **191.18x** |
| 16777216 | **16.0 MiB** | 0.8534 ms | 8.6100 ms | 13.9181 ms | 21.3211 ms | 48.7139 ms | **109.8760 ms** | **128.75x** |
| 33554432 | **32.0 MiB** | 1.6938 ms | 15.1691 ms | 27.4917 ms | 36.7205 ms | 109.2960 ms | **213.6560 ms** | **126.14x** |
| 67108864 | **64.0 MiB** | 3.3158 ms | 28.0007 ms | 54.1517 ms | 83.9586 ms | 191.7610 ms | **374.2220 ms** | **112.86x** |
| 134217728 | **128.0 MiB** | 5.7845 ms | 86.3775 ms | 103.3780 ms | 151.6900 ms | 305.1700 ms | **693.1160 ms** | **119.82x** |
| 268435456 | **256.0 MiB** | 11.0108 ms | 137.3620 ms | 194.9930 ms | 225.0090 ms | 596.6860 ms | **1242.2600 ms** | **112.82x** |
