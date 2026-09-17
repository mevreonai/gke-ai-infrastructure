# ReduceScatter Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)

**Target Hardware:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster:** `kimi-node-0` & `kimi-node-1` on GCP VPC (us-central1-b)

### Benchmark Comparison Table (All Latencies in Milliseconds - ms)

| Payload Size | Milestone Description | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Multi-Node (175G) vs Local | 10G Capped vs Local |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16 KiB** | Batch-1 Token Decode | **0.018 ms** | **0.132 ms** | 0.137 ms | 0.154 ms | 0.168 ms | **0.135 ms** | 7.49x | 7.66x |
| **32 KiB** | 32 KiB | **0.037 ms** | **0.137 ms** | 0.141 ms | 0.153 ms | 0.155 ms | **0.139 ms** | 3.70x | 3.76x |
| **64 KiB** | 64 KiB | **0.019 ms** | **0.14 ms** | 0.144 ms | 0.154 ms | 0.17 ms | **0.141 ms** | 7.18x | 7.27x |
| **128 KiB** | Small Activation | **0.029 ms** | **0.197 ms** | 0.176 ms | 0.219 ms | 0.235 ms | **0.217 ms** | 6.72x | 7.40x |
| **256 KiB** | 256 KiB | **0.05 ms** | **0.229 ms** | 0.188 ms | 0.218 ms | 0.252 ms | **0.424 ms** | 4.62x | 8.54x |
| **512 KiB** | 512 KiB | **0.09 ms** | **0.254 ms** | 0.21 ms | 0.281 ms | 0.428 ms | **0.824 ms** | 2.81x | 9.12x |
| **1 MiB** | 1 MiB Tensor | **0.075 ms** | **0.281 ms** | 0.236 ms | 0.287 ms | 0.448 ms | **0.826 ms** | 3.74x | 11.01x |
| **2 MiB** | 2 MiB | **0.124 ms** | **0.443 ms** | 0.47 ms | 0.503 ms | 0.833 ms | **1.647 ms** | 3.56x | 13.24x |
| **4 MiB** | 4 MiB | **0.187 ms** | **0.709 ms** | 0.57 ms | 0.71 ms | 1.645 ms | **3.293 ms** | 3.79x | 17.62x |
| **8 MiB** | 8 MiB | **0.349 ms** | **1.082 ms** | 1.21 ms | 1.318 ms | 3.287 ms | **6.583 ms** | 3.10x | 18.86x |
| **16 MiB** | 16 MiB Activation | **0.637 ms** | **1.633 ms** | 1.906 ms | 2.631 ms | 6.58 ms | **13.179 ms** | 2.57x | 20.70x |
| **32 MiB** | 32 MiB | **1.251 ms** | **2.807 ms** | 3.166 ms | 5.26 ms | 13.152 ms | **26.326 ms** | 2.24x | 21.05x |
| **64 MiB** | 64 MiB Chunk | **2.465 ms** | **4.715 ms** | 5.669 ms | 10.511 ms | 26.31 ms | **52.632 ms** | 1.91x | 21.35x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.845 ms** | **9.122 ms** | 11.403 ms | 21.06 ms | 52.682 ms | **105.4 ms** | 1.88x | 21.76x |
| **256 MiB** | Large Prefill (256 MiB) | **9.444 ms** | **17.936 ms** | 22.922 ms | 42.152 ms | 105.442 ms | **211.091 ms** | 1.90x | 22.35x |

### Algorithmic Bandwidth Comparison (GB/s)

| Payload Size | TP-8 Local Baseline | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 MiB** | **13.98 GB/s** | **3.73 GB/s** | 4.44 GB/s | 3.66 GB/s | 2.34 GB/s | **1.27 GB/s** |
| **2 MiB** | **16.86 GB/s** | **4.73 GB/s** | 4.46 GB/s | 4.17 GB/s | 2.52 GB/s | **1.27 GB/s** |
| **4 MiB** | **22.44 GB/s** | **5.92 GB/s** | 7.36 GB/s | 5.91 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **8 MiB** | **24.03 GB/s** | **7.75 GB/s** | 6.93 GB/s | 6.37 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **16 MiB** | **26.35 GB/s** | **10.27 GB/s** | 8.8 GB/s | 6.38 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **32 MiB** | **26.83 GB/s** | **11.95 GB/s** | 10.6 GB/s | 6.38 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **64 MiB** | **27.23 GB/s** | **14.23 GB/s** | 11.84 GB/s | 6.38 GB/s | 2.55 GB/s | **1.28 GB/s** |
| **128 MiB** | **27.7 GB/s** | **14.71 GB/s** | 11.77 GB/s | 6.37 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **256 MiB** | **28.43 GB/s** | **14.97 GB/s** | 11.71 GB/s | 6.37 GB/s | 2.55 GB/s | **1.27 GB/s** |

### Key Takeaways
1. **Decode vs Prefill**: Local TP-8 is optimal for small decode payloads ($\le 128$ KiB) avoiding TCP latency hops, while TP-16 scales memory capacity for prefill.
2. **Network Throttling**: Throttling from 175G to 10G dramatically impacts multi-node latency (by ~7x to 23x for large tensors), demonstrating that network bandwidth is the primary bottleneck for distributed communication.
