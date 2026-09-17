# ReduceScatter Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)

**Target Hardware:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster:** `kimi-node-0` & `kimi-node-1` on GCP VPC (us-central1-b)

### Benchmark Comparison Table (All Latencies in Milliseconds - ms)

| Payload Size | Milestone Description | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Multi-Node (175G) vs Local | 10G Capped vs Local |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8 KiB** | Min Size Floor | **0.02 ms** | **0.454 ms** | 0.331 ms | 0.212 ms | 0.212 ms | **0.602 ms** | 22.80x | 30.21x |
| **16 KiB** | Batch-1 Token Decode | **0.018 ms** | **0.172 ms** | 0.207 ms | 0.225 ms | 0.202 ms | **0.295 ms** | 9.47x | 16.28x |
| **32 KiB** | 32 KiB | **0.019 ms** | **0.175 ms** | 0.212 ms | 0.222 ms | 0.236 ms | **0.332 ms** | 9.15x | 17.38x |
| **64 KiB** | 64 KiB | **0.02 ms** | **0.183 ms** | 0.214 ms | 0.231 ms | 0.216 ms | **0.303 ms** | 9.26x | 15.34x |
| **128 KiB** | Small Activation | **0.03 ms** | **0.358 ms** | 0.397 ms | 0.424 ms | 0.43 ms | **0.51 ms** | 12.03x | 17.13x |
| **256 KiB** | 256 KiB | **0.051 ms** | **0.372 ms** | 0.55 ms | 0.444 ms | 0.448 ms | **0.514 ms** | 7.35x | 10.17x |
| **512 KiB** | 512 KiB | **0.091 ms** | **0.422 ms** | 0.592 ms | 0.471 ms | 0.504 ms | **0.918 ms** | 4.63x | 10.08x |
| **1 MiB** | 1 MiB Tensor | **0.076 ms** | **0.429 ms** | 0.632 ms | 0.472 ms | 0.483 ms | **0.849 ms** | 5.64x | 11.17x |
| **2 MiB** | 2 MiB | **0.125 ms** | **0.971 ms** | 0.935 ms | 0.853 ms | 0.882 ms | **1.641 ms** | 7.77x | 13.13x |
| **4 MiB** | 4 MiB | **0.187 ms** | **1.178 ms** | 1.302 ms | 1.247 ms | 1.803 ms | **3.298 ms** | 6.30x | 17.64x |
| **8 MiB** | 8 MiB | **0.349 ms** | **1.972 ms** | 2.136 ms | 2.203 ms | 3.278 ms | **6.621 ms** | 5.64x | 18.95x |
| **16 MiB** | 16 MiB Activation | **0.641 ms** | **3.55 ms** | 4.56 ms | 3.763 ms | 6.586 ms | **13.151 ms** | 5.54x | 20.52x |
| **32 MiB** | 32 MiB | **1.247 ms** | **5.916 ms** | 5.769 ms | 5.97 ms | 13.169 ms | **26.217 ms** | 4.74x | 21.02x |
| **64 MiB** | 64 MiB Chunk | **2.484 ms** | **9.07 ms** | 9.706 ms | 12.593 ms | 26.231 ms | **52.457 ms** | 3.65x | 21.12x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.967 ms** | **18.539 ms** | 18.903 ms | 21.558 ms | 53.192 ms | **105.581 ms** | 3.73x | 21.26x |
| **256 MiB** | Large Prefill (256 MiB) | **9.934 ms** | **30.598 ms** | 34.59 ms | 42.904 ms | 106.482 ms | **211.135 ms** | 3.08x | 21.25x |

### Algorithmic Bandwidth Comparison (GB/s)

| Payload Size | TP-8 Local Baseline | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 MiB** | **13.81 GB/s** | **2.45 GB/s** | 1.66 GB/s | 2.22 GB/s | 2.17 GB/s | **1.24 GB/s** |
| **2 MiB** | **16.77 GB/s** | **2.16 GB/s** | 2.24 GB/s | 2.46 GB/s | 2.38 GB/s | **1.28 GB/s** |
| **4 MiB** | **22.44 GB/s** | **3.56 GB/s** | 3.22 GB/s | 3.36 GB/s | 2.33 GB/s | **1.27 GB/s** |
| **8 MiB** | **24.01 GB/s** | **4.25 GB/s** | 3.93 GB/s | 3.81 GB/s | 2.56 GB/s | **1.27 GB/s** |
| **16 MiB** | **26.18 GB/s** | **4.73 GB/s** | 3.68 GB/s | 4.46 GB/s | 2.55 GB/s | **1.28 GB/s** |
| **32 MiB** | **26.91 GB/s** | **5.67 GB/s** | 5.82 GB/s | 5.62 GB/s | 2.55 GB/s | **1.28 GB/s** |
| **64 MiB** | **27.02 GB/s** | **7.4 GB/s** | 6.91 GB/s | 5.33 GB/s | 2.56 GB/s | **1.28 GB/s** |
| **128 MiB** | **27.02 GB/s** | **7.24 GB/s** | 7.1 GB/s | 6.23 GB/s | 2.52 GB/s | **1.27 GB/s** |
| **256 MiB** | **27.02 GB/s** | **8.77 GB/s** | 7.76 GB/s | 6.26 GB/s | 2.52 GB/s | **1.27 GB/s** |

### Key Takeaways
1. **Decode vs Prefill**: Local TP-8 is optimal for small decode payloads ($\le 128$ KiB) avoiding TCP latency hops, while TP-16 scales memory capacity for prefill.
2. **Network Throttling**: Throttling from 175G to 10G dramatically impacts multi-node latency (by ~7x to 23x for large tensors), demonstrating that network bandwidth is the primary bottleneck for distributed communication.
