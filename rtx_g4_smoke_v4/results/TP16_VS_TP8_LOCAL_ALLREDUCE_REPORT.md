# AllReduce Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)

**Target Hardware:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster:** `kimi-node-0` & `kimi-node-1` on GCP VPC (us-central1-b)

### Benchmark Comparison Table (All Latencies in Milliseconds - ms)

| Payload Size | Milestone Description | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Multi-Node (175G) vs Local | 10G Capped vs Local |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16 KiB** | Batch-1 Token Decode | **0.028 ms** | **0.273 ms** | 0.302 ms | 0.276 ms | 0.275 ms | **0.276 ms** | 9.72x | 9.81x |
| **32 KiB** | 32 KiB | **0.03 ms** | **0.279 ms** | 0.317 ms | 0.286 ms | 0.284 ms | **0.288 ms** | 9.28x | 9.57x |
| **64 KiB** | 64 KiB | **0.035 ms** | **0.277 ms** | 0.321 ms | 0.294 ms | 0.291 ms | **0.303 ms** | 7.87x | 8.61x |
| **128 KiB** | Small Activation | **0.05 ms** | **0.477 ms** | 0.47 ms | 0.381 ms | 0.401 ms | **0.423 ms** | 9.54x | 8.47x |
| **256 KiB** | 256 KiB | **0.087 ms** | **0.394 ms** | 0.447 ms | 0.407 ms | 0.474 ms | **0.845 ms** | 4.51x | 9.68x |
| **512 KiB** | 512 KiB | **0.162 ms** | **0.472 ms** | 0.617 ms | 0.475 ms | 0.849 ms | **1.652 ms** | 2.91x | 10.19x |
| **1 MiB** | 1 MiB Tensor | **0.138 ms** | **0.668 ms** | 0.889 ms | 0.697 ms | 1.722 ms | **3.297 ms** | 4.83x | 23.81x |
| **2 MiB** | 2 MiB | **0.231 ms** | **0.843 ms** | 0.941 ms | 0.793 ms | 1.651 ms | **3.303 ms** | 3.65x | 14.29x |
| **4 MiB** | 4 MiB | **0.355 ms** | **1.312 ms** | 1.124 ms | 1.366 ms | 3.298 ms | **6.591 ms** | 3.70x | 18.59x |
| **8 MiB** | 8 MiB | **0.656 ms** | **2.07 ms** | 2.812 ms | 2.639 ms | 6.586 ms | **13.183 ms** | 3.16x | 20.10x |
| **16 MiB** | 16 MiB Activation | **1.217 ms** | **3.296 ms** | 4.028 ms | 5.269 ms | 13.178 ms | **26.38 ms** | 2.71x | 21.68x |
| **32 MiB** | 32 MiB | **2.378 ms** | **5.572 ms** | 7.231 ms | 10.538 ms | 26.349 ms | **52.727 ms** | 2.34x | 22.17x |
| **64 MiB** | 64 MiB Chunk | **4.64 ms** | **11.243 ms** | 13.002 ms | 21.062 ms | 52.681 ms | **105.436 ms** | 2.42x | 22.72x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **9.021 ms** | **23.025 ms** | 25.195 ms | 42.149 ms | 105.424 ms | **210.938 ms** | 2.55x | 23.38x |
| **256 MiB** | Large Prefill (256 MiB) | **18.006 ms** | **45.886 ms** | 50.035 ms | 84.373 ms | 210.896 ms | **421.903 ms** | 2.55x | 23.43x |

### Algorithmic Bandwidth Comparison (GB/s)

| Payload Size | TP-8 Local Baseline | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 MiB** | **7.57 GB/s** | **1.57 GB/s** | 1.18 GB/s | 1.5 GB/s | 0.61 GB/s | **0.32 GB/s** |
| **2 MiB** | **9.08 GB/s** | **2.49 GB/s** | 2.23 GB/s | 2.65 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **4 MiB** | **11.83 GB/s** | **3.2 GB/s** | 3.73 GB/s | 3.07 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **8 MiB** | **12.79 GB/s** | **4.05 GB/s** | 2.98 GB/s | 3.18 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **16 MiB** | **13.79 GB/s** | **5.09 GB/s** | 4.17 GB/s | 3.18 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **32 MiB** | **14.11 GB/s** | **6.02 GB/s** | 4.64 GB/s | 3.18 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **64 MiB** | **14.46 GB/s** | **5.97 GB/s** | 5.16 GB/s | 3.19 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **128 MiB** | **14.88 GB/s** | **5.83 GB/s** | 5.33 GB/s | 3.18 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **256 MiB** | **14.91 GB/s** | **5.85 GB/s** | 5.36 GB/s | 3.18 GB/s | 1.27 GB/s | **0.64 GB/s** |

### Key Takeaways
1. **Decode vs Prefill**: Local TP-8 is optimal for small decode payloads ($\le 128$ KiB) avoiding TCP latency hops, while TP-16 scales memory capacity for prefill.
2. **Network Throttling**: Throttling from 175G to 10G dramatically impacts multi-node latency (by ~7x to 23x for large tensors), demonstrating that network bandwidth is the primary bottleneck for distributed communication.
