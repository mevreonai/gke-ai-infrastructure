# Master Distributed Collective Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)

**Hardware Platform:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster Infrastructure:** `kimi-node-0` (10.128.0.39) & `kimi-node-1` (10.128.0.40) on GCP VPC
**Collectives Covered:** AllReduce, AllGather, ReduceScatter
**Network Configurations:** 175G Native (173.6 Gbps), 100G, 50G, 20G, 10G Egress Caps

## 1. 256 MiB Large Prefill Summary Across All Collectives

| Collective | Metric | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **AllReduce** | Latency (ms) | **18.006 ms** | **45.886 ms** | 50.035 ms | 84.373 ms | 210.896 ms | **421.903 ms** | **2.55x** | **23.43x** |
| | AlgBW (GB/s) | **14.91 GB/s** | **5.85 GB/s** | 5.36 GB/s | 3.18 GB/s | 1.27 GB/s | **0.64 GB/s** | - | - |
| **AllGather** | Latency (ms) | **9.85 ms** | **30.537 ms** | 32.207 ms | 43.084 ms | 106.068 ms | **211.073 ms** | **3.10x** | **21.43x** |
| | AlgBW (GB/s) | **27.25 GB/s** | **8.79 GB/s** | 8.33 GB/s | 6.23 GB/s | 2.53 GB/s | **1.27 GB/s** | - | - |
| **ReduceScatter** | Latency (ms) | **9.934 ms** | **30.598 ms** | 34.59 ms | 42.904 ms | 106.482 ms | **211.135 ms** | **3.08x** | **21.25x** |
| | AlgBW (GB/s) | **27.02 GB/s** | **8.77 GB/s** | 7.76 GB/s | 6.26 GB/s | 2.52 GB/s | **1.27 GB/s** | - | - |

## 2. Mathematical Consistency Validation
According to distributed ring collective theory:
$$\text{Latency}_{\text{AllReduce}} \approx \text{Latency}_{\text{ReduceScatter}} + \text{Latency}_{\text{AllGather}}$$

Comparing the empirical measurements at 256 MiB on 10G Capped network:
- **ReduceScatter (10G)**: 211.14 ms
- **AllGather (10G)**: 211.07 ms
- **Sum**: 422.21 ms
- **Measured AllReduce (10G)**: **421.90 ms** (0.07% error - near mathematical perfection)

All CSV files have been exported to the `results/` directory for direct distribution.
