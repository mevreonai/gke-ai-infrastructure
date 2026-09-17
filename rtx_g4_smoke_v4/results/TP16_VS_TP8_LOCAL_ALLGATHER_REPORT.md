# AllGather Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)

**Target Hardware:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster:** `kimi-node-0` & `kimi-node-1` on GCP VPC (us-central1-b)

### Benchmark Comparison Table (All Latencies in Milliseconds - ms)

| Payload Size | Milestone Description | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Multi-Node (175G) vs Local | 10G Capped vs Local |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16 KiB** | Batch-1 Token Decode | **0.016 ms** | **0.132 ms** | 0.134 ms | 0.182 ms | 0.138 ms | **0.145 ms** | 7.99x | 8.80x |
| **32 KiB** | 32 KiB | **0.019 ms** | **0.136 ms** | 0.139 ms | 0.207 ms | 0.152 ms | **0.149 ms** | 7.21x | 7.91x |
| **64 KiB** | 64 KiB | **0.02 ms** | **0.148 ms** | 0.141 ms | 0.183 ms | 0.149 ms | **0.151 ms** | 7.54x | 7.72x |
| **128 KiB** | Small Activation | **0.031 ms** | **0.195 ms** | 0.192 ms | 0.187 ms | 0.224 ms | **0.258 ms** | 6.36x | 8.45x |
| **256 KiB** | 256 KiB | **0.047 ms** | **0.213 ms** | 0.202 ms | 0.208 ms | 0.249 ms | **0.427 ms** | 4.51x | 9.02x |
| **512 KiB** | 512 KiB | **0.083 ms** | **0.228 ms** | 0.246 ms | 0.243 ms | 0.429 ms | **0.825 ms** | 2.74x | 9.90x |
| **1 MiB** | 1 MiB Tensor | **0.075 ms** | **0.282 ms** | 0.263 ms | 0.293 ms | 0.43 ms | **0.825 ms** | 3.74x | 10.94x |
| **2 MiB** | 2 MiB | **0.118 ms** | **0.484 ms** | 0.494 ms | 0.458 ms | 0.831 ms | **1.65 ms** | 4.11x | 14.03x |
| **4 MiB** | 4 MiB | **0.181 ms** | **0.598 ms** | 0.565 ms | 0.736 ms | 1.645 ms | **3.288 ms** | 3.31x | 18.18x |
| **8 MiB** | 8 MiB | **0.334 ms** | **0.94 ms** | 1.077 ms | 1.336 ms | 3.288 ms | **6.592 ms** | 2.82x | 19.77x |
| **16 MiB** | 16 MiB Activation | **0.634 ms** | **1.498 ms** | 1.941 ms | 2.636 ms | 6.61 ms | **13.158 ms** | 2.36x | 20.74x |
| **32 MiB** | 32 MiB | **1.24 ms** | **2.601 ms** | 3.798 ms | 5.262 ms | 13.211 ms | **26.307 ms** | 2.10x | 21.22x |
| **64 MiB** | 64 MiB Chunk | **2.461 ms** | **4.833 ms** | 7.656 ms | 10.51 ms | 26.322 ms | **52.633 ms** | 1.96x | 21.39x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.896 ms** | **9.462 ms** | 14.928 ms | 21.057 ms | 52.713 ms | **105.436 ms** | 1.93x | 21.54x |
| **256 MiB** | Large Prefill (256 MiB) | **9.743 ms** | **19.026 ms** | 29.54 ms | 42.152 ms | 105.464 ms | **211.042 ms** | 1.95x | 21.66x |

### Algorithmic Bandwidth Comparison (GB/s)

| Payload Size | TP-8 Local Baseline | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 MiB** | **13.9 GB/s** | **3.72 GB/s** | 3.98 GB/s | 3.58 GB/s | 2.44 GB/s | **1.27 GB/s** |
| **2 MiB** | **17.83 GB/s** | **4.33 GB/s** | 4.24 GB/s | 4.57 GB/s | 2.52 GB/s | **1.27 GB/s** |
| **4 MiB** | **23.19 GB/s** | **7.02 GB/s** | 7.42 GB/s | 5.7 GB/s | 2.55 GB/s | **1.28 GB/s** |
| **8 MiB** | **25.15 GB/s** | **8.92 GB/s** | 7.79 GB/s | 6.28 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **16 MiB** | **26.45 GB/s** | **11.2 GB/s** | 8.65 GB/s | 6.37 GB/s | 2.54 GB/s | **1.27 GB/s** |
| **32 MiB** | **27.07 GB/s** | **12.9 GB/s** | 8.84 GB/s | 6.38 GB/s | 2.54 GB/s | **1.28 GB/s** |
| **64 MiB** | **27.27 GB/s** | **13.88 GB/s** | 8.77 GB/s | 6.39 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **128 MiB** | **27.42 GB/s** | **14.19 GB/s** | 8.99 GB/s | 6.37 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **256 MiB** | **27.55 GB/s** | **14.11 GB/s** | 9.09 GB/s | 6.37 GB/s | 2.55 GB/s | **1.27 GB/s** |

### Key Takeaways
1. **Decode vs Prefill**: Local TP-8 is optimal for small decode payloads ($\le 128$ KiB) avoiding TCP latency hops, while TP-16 scales memory capacity for prefill.
2. **Network Throttling**: Throttling from 175G to 10G dramatically impacts multi-node latency (by ~7x to 23x for large tensors), demonstrating that network bandwidth is the primary bottleneck for distributed communication.
