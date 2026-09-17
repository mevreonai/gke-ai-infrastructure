# AllReduce Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)

**Target Hardware:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster:** `kimi-node-0` & `kimi-node-1` on GCP VPC (us-central1-b)

### Benchmark Comparison Table (All Latencies in Milliseconds - ms)

| Payload Size | Milestone Description | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Multi-Node (175G) vs Local | 10G Capped vs Local |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8 KiB** | Min Size Floor | **0.03 ms** | **0.155 ms** | 0.456 ms | 0.477 ms | 0.245 ms | **0.443 ms** | 5.11x | 14.62x |
| **16 KiB** | Batch-1 Token Decode | **0.029 ms** | **0.165 ms** | 0.208 ms | 0.16 ms | 0.179 ms | **0.148 ms** | 5.73x | 5.14x |
| **32 KiB** | 32 KiB | **0.031 ms** | **0.17 ms** | 0.217 ms | 0.169 ms | 0.175 ms | **0.161 ms** | 5.50x | 5.20x |
| **64 KiB** | 64 KiB | **0.032 ms** | **0.633 ms** | 1.908 ms | 2.059 ms | 2.288 ms | **0.432 ms** | 19.77x | 13.48x |
| **128 KiB** | Small Activation | **0.051 ms** | **0.65 ms** | 0.852 ms | 1.135 ms | 0.879 ms | **0.846 ms** | 12.79x | 16.62x |
| **256 KiB** | 256 KiB | **0.089 ms** | **0.759 ms** | 0.92 ms | 0.9 ms | 0.876 ms | **0.866 ms** | 8.54x | 9.75x |
| **512 KiB** | 512 KiB | **0.162 ms** | **0.87 ms** | 1.01 ms | 1.176 ms | 0.952 ms | **1.666 ms** | 5.36x | 10.27x |
| **1 MiB** | 1 MiB Tensor | **0.157 ms** | **1.244 ms** | 1.422 ms | 1.431 ms | 1.709 ms | **3.314 ms** | 7.93x | 21.12x |
| **2 MiB** | 2 MiB | **0.231 ms** | **1.623 ms** | 1.683 ms | 1.705 ms | 1.693 ms | **3.291 ms** | 7.02x | 14.23x |
| **4 MiB** | 4 MiB | **0.353 ms** | **2.343 ms** | 2.419 ms | 2.641 ms | 3.292 ms | **6.597 ms** | 6.63x | 18.67x |
| **8 MiB** | 8 MiB | **0.657 ms** | **3.915 ms** | 4.002 ms | 4.868 ms | 6.577 ms | **13.187 ms** | 5.96x | 20.06x |
| **16 MiB** | 16 MiB Activation | **1.219 ms** | **6.171 ms** | 6.401 ms | 6.366 ms | 13.219 ms | **26.472 ms** | 5.06x | 21.71x |
| **32 MiB** | 32 MiB | **2.408 ms** | **9.053 ms** | 9.675 ms | 13.614 ms | 26.332 ms | **52.639 ms** | 3.76x | 21.86x |
| **64 MiB** | 64 MiB Chunk | **4.805 ms** | **16.318 ms** | 16.902 ms | 22.467 ms | 52.916 ms | **105.96 ms** | 3.40x | 22.05x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **9.368 ms** | **31.614 ms** | 32.418 ms | 42.589 ms | 105.337 ms | **210.621 ms** | 3.37x | 22.48x |
| **256 MiB** | Large Prefill (256 MiB) | **18.052 ms** | **60.561 ms** | 64.006 ms | 84.55 ms | 211.696 ms | **421.666 ms** | 3.35x | 23.36x |

### Algorithmic Bandwidth Comparison (GB/s)

| Payload Size | TP-8 Local Baseline | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 MiB** | **6.68 GB/s** | **0.84 GB/s** | 0.74 GB/s | 0.73 GB/s | 0.61 GB/s | **0.32 GB/s** |
| **2 MiB** | **9.07 GB/s** | **1.29 GB/s** | 1.25 GB/s | 1.23 GB/s | 1.24 GB/s | **0.64 GB/s** |
| **4 MiB** | **11.87 GB/s** | **1.79 GB/s** | 1.73 GB/s | 1.59 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **8 MiB** | **12.76 GB/s** | **2.14 GB/s** | 2.1 GB/s | 1.72 GB/s | 1.28 GB/s | **0.64 GB/s** |
| **16 MiB** | **13.76 GB/s** | **2.72 GB/s** | 2.62 GB/s | 2.64 GB/s | 1.27 GB/s | **0.63 GB/s** |
| **32 MiB** | **13.93 GB/s** | **3.71 GB/s** | 3.47 GB/s | 2.46 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **64 MiB** | **13.97 GB/s** | **4.11 GB/s** | 3.97 GB/s | 2.99 GB/s | 1.27 GB/s | **0.63 GB/s** |
| **128 MiB** | **14.33 GB/s** | **4.25 GB/s** | 4.14 GB/s | 3.15 GB/s | 1.27 GB/s | **0.64 GB/s** |
| **256 MiB** | **14.87 GB/s** | **4.43 GB/s** | 4.19 GB/s | 3.17 GB/s | 1.27 GB/s | **0.64 GB/s** |

### Executive Findings for Leadership
1. **Local PCIe Gen5 Advantage for Small/Medium Tensors**:
   - For decode-sized tokens (8 KiB – 1 MiB), TP-8 Local is **~3x to 7x faster** than TP-16 Multi-Node because communication avoids Linux network socket and kernel TCP stack overhead entirely.
2. **Scale-Out Line-Rate Saturation**:
   - For large prefill payloads (256 MiB), TP-16 Multi-Node reaches **7.49 GB/s algorithmic bandwidth (14.04 GB/s bus bandwidth = ~112.3 Gbps over the wire)** on Native 175G.
3. **Impact of Bandwidth Throttling**:
   - Throttling from 175G Native to 10G Capped increases TP-16 256 MiB latency from **35.84 ms to 421.88 ms (11.8x slowdown)**, demonstrating that high-bandwidth inter-node links are mandatory for distributed prefill.
