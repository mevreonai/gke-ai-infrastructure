# AllGather Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)

**Target Hardware:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster:** `kimi-node-0` & `kimi-node-1` on GCP VPC (us-central1-b)

### Benchmark Comparison Table (All Latencies in Milliseconds - ms)

| Payload Size | Milestone Description | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Multi-Node (175G) vs Local | 10G Capped vs Local |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8 KiB** | Min Size Floor | **0.018 ms** | **0.696 ms** | 0.602 ms | 0.222 ms | 0.209 ms | **0.423 ms** | 38.71x | 23.52x |
| **16 KiB** | Batch-1 Token Decode | **0.017 ms** | **0.285 ms** | 0.345 ms | 0.322 ms | 0.215 ms | **0.252 ms** | 16.72x | 14.80x |
| **32 KiB** | 32 KiB | **0.019 ms** | **0.266 ms** | 0.341 ms | 0.221 ms | 0.214 ms | **0.249 ms** | 13.69x | 12.82x |
| **64 KiB** | 64 KiB | **0.02 ms** | **0.315 ms** | 0.41 ms | 0.224 ms | 0.229 ms | **0.25 ms** | 15.60x | 12.40x |
| **128 KiB** | Small Activation | **0.029 ms** | **0.512 ms** | 0.512 ms | 0.412 ms | 0.38 ms | **0.531 ms** | 17.46x | 18.11x |
| **256 KiB** | 256 KiB | **0.047 ms** | **0.526 ms** | 0.61 ms | 0.463 ms | 0.425 ms | **0.54 ms** | 11.07x | 11.37x |
| **512 KiB** | 512 KiB | **0.084 ms** | **0.877 ms** | 0.627 ms | 0.541 ms | 0.462 ms | **0.911 ms** | 10.47x | 10.88x |
| **1 MiB** | 1 MiB Tensor | **0.076 ms** | **0.796 ms** | 0.584 ms | 0.506 ms | 0.475 ms | **0.839 ms** | 10.43x | 11.00x |
| **2 MiB** | 2 MiB | **0.118 ms** | **0.969 ms** | 0.92 ms | 0.889 ms | 0.831 ms | **1.66 ms** | 8.23x | 14.11x |
| **4 MiB** | 4 MiB | **0.182 ms** | **1.268 ms** | 1.256 ms | 1.25 ms | 1.701 ms | **3.284 ms** | 6.98x | 18.08x |
| **8 MiB** | 8 MiB | **0.334 ms** | **1.968 ms** | 2.113 ms | 2.148 ms | 3.291 ms | **6.588 ms** | 5.90x | 19.75x |
| **16 MiB** | 16 MiB Activation | **0.634 ms** | **3.802 ms** | 4.255 ms | 4.003 ms | 6.633 ms | **13.218 ms** | 6.00x | 20.86x |
| **32 MiB** | 32 MiB | **1.238 ms** | **5.504 ms** | 5.249 ms | 6.719 ms | 13.246 ms | **26.52 ms** | 4.45x | 21.43x |
| **64 MiB** | 64 MiB Chunk | **2.464 ms** | **8.498 ms** | 8.914 ms | 12.088 ms | 26.452 ms | **52.455 ms** | 3.45x | 21.29x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.928 ms** | **16.203 ms** | 17.063 ms | 21.975 ms | 52.647 ms | **105.686 ms** | 3.29x | 21.45x |
| **256 MiB** | Large Prefill (256 MiB) | **9.85 ms** | **30.537 ms** | 32.207 ms | 43.084 ms | 106.068 ms | **211.073 ms** | 3.10x | 21.43x |

### Algorithmic Bandwidth Comparison (GB/s)

| Payload Size | TP-8 Local Baseline | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 MiB** | **13.74 GB/s** | **1.32 GB/s** | 1.8 GB/s | 2.07 GB/s | 2.21 GB/s | **1.25 GB/s** |
| **2 MiB** | **17.82 GB/s** | **2.16 GB/s** | 2.28 GB/s | 2.36 GB/s | 2.52 GB/s | **1.26 GB/s** |
| **4 MiB** | **23.1 GB/s** | **3.31 GB/s** | 3.34 GB/s | 3.35 GB/s | 2.47 GB/s | **1.28 GB/s** |
| **8 MiB** | **25.15 GB/s** | **4.26 GB/s** | 3.97 GB/s | 3.9 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **16 MiB** | **26.48 GB/s** | **4.41 GB/s** | 3.94 GB/s | 4.19 GB/s | 2.53 GB/s | **1.27 GB/s** |
| **32 MiB** | **27.11 GB/s** | **6.1 GB/s** | 6.39 GB/s | 4.99 GB/s | 2.53 GB/s | **1.27 GB/s** |
| **64 MiB** | **27.23 GB/s** | **7.9 GB/s** | 7.53 GB/s | 5.55 GB/s | 2.54 GB/s | **1.28 GB/s** |
| **128 MiB** | **27.24 GB/s** | **8.28 GB/s** | 7.87 GB/s | 6.11 GB/s | 2.55 GB/s | **1.27 GB/s** |
| **256 MiB** | **27.25 GB/s** | **8.79 GB/s** | 8.33 GB/s | 6.23 GB/s | 2.53 GB/s | **1.27 GB/s** |

### Key Takeaways
1. **Decode vs Prefill**: Local TP-8 is optimal for small decode payloads ($\le 128$ KiB) avoiding TCP latency hops, while TP-16 scales memory capacity for prefill.
2. **Network Throttling**: Throttling from 175G to 10G dramatically impacts multi-node latency (by ~7x to 23x for large tensors), demonstrating that network bandwidth is the primary bottleneck for distributed communication.
