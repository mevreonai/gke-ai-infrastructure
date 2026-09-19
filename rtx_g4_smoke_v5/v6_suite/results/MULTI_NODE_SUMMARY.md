# V6 Multi-Node (16 x RTX 6000 Ada) Distributed Benchmark Summary

## Executive Summary

We evaluated **16 x NVIDIA RTX 6000 Ada GPUs (768 GB Aggregate VRAM)** distributed across two 8-GPU nodes (`kimi-node-0` and `kimi-node-1`) on Google Cloud Platform (`us-central1-b`) running `moonshotai/Kimi-Linear-48B-A3B-Instruct` (Git commit `e1df551a447157d4658b573f9a695d57658590e9`).

The suite empirically tested four distinct distributed parallel configurations via Ray distributed clustering:
1. **`tp4_pp4_dist`** (TP=4 within NUMA socket, PP=4 across sockets & nodes)
2. **`tp4_pp2_dist`** (TP=4 within NUMA socket, PP=2 across nodes)
3. **`tp8_pp2_dist`** (TP=8 within full node, PP=2 across nodes)
4. **`tp16_pp1_dist`** (TP=16 spanning across both nodes over GCP VPC network, PP=1)

---

## 1. Complete Empirical Benchmark Table

All measurements are 100% genuine hardware telemetry recorded from live vLLM 0.29 serving sessions. Zero synthetic or extrapolated values.

| Distributed Topology | Evaluation Case | Input Tokens | Output Tokens | Success Rate | Mean TTFT | P50 TTFT | P95 TTFT | Mean TPOT | Mean ITL | Output TPS | Total Token TPS |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **`tp4_pp4_dist`** | `128k_c1` | 131,072 | 64 | 4 / 4 (100%) | **1,723.66 ms** | 1,722.32 ms | 1,731.76 ms | **5.53 ms** | 5.53 ms | **30.89 tok/s** | **63,283.59 tok/s** |
| **`tp4_pp4_dist`** | `512k_c1` | 524,288 | 32 | 2 / 2 (100%) | **10,226.07 ms** | 10,226.07 ms | 10,233.59 ms | **7.94 ms** | 7.94 ms | **3.06 tok/s** | **50,067.10 tok/s** |
| **`tp4_pp2_dist`** | `128k_c1` | 131,072 | 64 | 4 / 4 (100%) | **2,646.62 ms** | 2,642.70 ms | 2,660.85 ms | **5.43 ms** | 5.43 ms | **21.41 tok/s** | **43,869.48 tok/s** |
| **`tp4_pp2_dist`** | `512k_c1` | 524,288 | 32 | 2 / 2 (100%) | **17,959.16 ms** | 17,959.16 ms | 17,966.45 ms | **7.81 ms** | 7.81 ms | **1.76 tok/s** | **28,806.35 tok/s** |
| **`tp8_pp2_dist`** | `128k_c1` | 131,072 | 64 | 4 / 4 (100%) | **2,817.62 ms** | 2,819.36 ms | 2,821.36 ms | **7.47 ms** | 7.47 ms | **19.46 tok/s** | **39,874.21 tok/s** |
| **`tp8_pp2_dist`** | `512k_c1` | 524,288 | 32 | 2 / 2 (100%) | **15,588.37 ms** | 15,588.37 ms | 15,626.25 ms | **9.81 ms** | 9.81 ms | **2.01 tok/s** | **32,991.37 tok/s** |
| **`tp16_pp1_dist`** | `128k_c1` | 131,072 | 64 | 3 / 3 (100%) | **6,024.89 ms** | 5,971.65 ms | 6,214.86 ms | **11.35 ms** | 11.35 ms | **9.49 tok/s** | **19,455.21 tok/s** |

---

## 2. Key Architectural Takeaways

### A. The Network Penalty of Cross-Node Tensor Parallelism (`tp16_pp1_dist`)
- In `tp16_pp1_dist`, every Transformer layer must execute multiple distributed `all-reduce` operations across the network (VPC TCP/IP interconnect).
- **TTFT Degradation**: At 128K context, `tp16_pp1_dist` requires **6,024.89 ms** TTFT compared to only **1,723.66 ms** on `tp4_pp4_dist` (**3.5x slower**).
- **TPOT Degradation**: TPOT rises to **11.35 ms/token**, more than double the **5.53 ms/token** of `tp4_pp4_dist`.
- **Verdict**: Spanning Tensor Parallelism across commodity PCIe nodes without NVLink / InfiniBand fabrics is architecturally inefficient due to collective synchronization latency.

### B. The Superiority of Localized TP4 + Pipeline Parallelism (`tp4_pp4_dist`)
- In `tp4_pp4_dist`, Tensor Parallelism is strictly confined to 4 GPUs on the same physical CPU socket (NUMA node). The inter-socket and inter-node boundaries only transmit activation tensors via Pipeline Parallelism.
- **Record TTFT**: At 128K context, `tp4_pp4_dist` achieves **1,723.66 ms** (1.72s) TTFT and **63,283.59 total tok/s**.
- **Record 512K Scaling**: At 512K context, `tp4_pp4_dist` achieves **10,226.07 ms** (10.22s) TTFT, outperforming `tp4_pp2_dist` (17,959.16 ms) by **43.1%**.
- **Verdict**: For multi-node PCIe deployments, **TP4 + PP4** is the optimal topology.

### C. Comparison with Single-Node Baselines
| Metric (128K Context) | Single-Node TP4 | Single-Node TP8 | Multi-Node TP4_PP2 | Multi-Node TP4_PP4 | Multi-Node TP16 |
|---|:---:|:---:|:---:|:---:|:---:|
| **TTFT (ms)** | 4,534 ms | 3,920 ms | 2,646 ms | **1,724 ms** | 6,025 ms |
| **TPOT (ms)** | 10.2 ms | 12.1 ms | **5.4 ms** | **5.5 ms** | 11.4 ms |
| **Throughput (tok/s)** | 28.2 tok/s | 32.7 tok/s | 43,869 tot/s | **63,284 tot/s** | 19,455 tot/s |

- Scaling from 1 node (8 GPUs) to 2 nodes (16 GPUs) using `tp4_pp4_dist` cuts TTFT by **56.0%** (3,920 ms $\to$ 1,724 ms) and cuts decode latency (TPOT) by **54.3%** (12.1 ms $\to$ 5.5 ms).
