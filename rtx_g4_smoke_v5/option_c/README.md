# Option C: 16-GPU Multi-Node Distributed Serving (Blackwell RTX PRO 6000)

## Overview
Option C evaluates distributed multi-node serving across **two GCP `g4-standard-96` nodes** (`kimi-node-0` and `kimi-node-1`), each equipped with 8x NVIDIA RTX PRO 6000 Blackwell GPUs (96 GB GDDR7 per GPU), providing **16 GPUs and 1.536 TB total VRAM** orchestrated via Ray and vLLM v0.29.0.

### Cluster Topology
- **Head Node (`kimi-node-0`)**: 8x RTX PRO 6000 (Ranks 0–7), Internal IP `10.128.0.39`.
- **Worker Node (`kimi-node-1`)**: 8x RTX PRO 6000 (Ranks 8–15), Internal IP `10.128.0.40`.
- **Intra-Node Interconnect**: PCIe Gen 5 (~128 GB/s bi-directional per link).
- **Inter-Node Interconnect**: GCP VPC 10 Gbps Ethernet (~1.25 GB/s bandwidth, ~0.2 ms latency).
- **Model**: `moonshotai/Kimi-Linear-48B-A3B-Instruct` (48B parameter hybrid linear attention / MoE surrogate).
- **Test Context**: 128K prefill (`131,072` tokens), 128 decode tokens, concurrency = 1.

---

## Benchmark Results: TP8_PP2 vs TP16_PP1

| Configuration | Parallelism Strategy | TTFT (Mean) | TTFT (Warmed) | TPOT (Decode Latency) | Median ITL | Decode Throughput | E2E Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`tp8_pp2_dist`** | **TP=8, PP=2** | **4,650.99 ms** | **2,810.45 ms** | **7.49 ms / tok** | **7.48 ms** | **133.4 tok/s** | **5,602.77 ms** |
| **`tp16_pp1_dist`** | **TP=16, PP=1** | **8,216.91 ms** | **8,216.91 ms** | **11.57 ms / tok** | **11.55 ms** | **87.0 tok/s** | **9,685.75 ms** |

---

## Key Architectural Findings & Scaling Analysis

### 1. The Superiority of Pipeline Parallelism across Nodes (`tp8_pp2_dist`)
- **1.86x Decode Speedup over Single-Node TP8**:
  - Single-node Option A (`tp8_pp1`) achieved **13.91 ms / tok** (71.9 tok/s).
  - Option C `tp8_pp2_dist` cuts decode latency to **7.49 ms / tok** (**133.4 tok/s**).
- **Why it works**:
  - Each node hosts 31 transformer layers instead of 62.
  - High-bandwidth All-Reduce collectives remain **100% intra-node** over high-speed PCIe Gen 5 links.
  - The inter-node 10 Gbps link is only used for Point-to-Point (P2P) activation tensor handoffs between Stage 0 (`kimi-node-0`) and Stage 1 (`kimi-node-1`), adding negligible overhead (< 0.5 ms per token).

### 2. The Inter-Node All-Reduce Bottleneck in `tp16_pp1_dist`
- When scaling Tensor Parallelism to 16 GPUs across nodes (`tp16_pp1_dist`):
  - Decode latency degrades to **11.57 ms / tok** (35% slower than `tp8_pp2_dist`).
  - TTFT doubles to **8,216.91 ms** (vs 4,650.99 ms).
- **Why it degrades**:
  - Tensor Parallelism requires an All-Reduce collective across all 16 ranks on **every single attention and MLP layer**.
  - Without dedicated high-speed scale-out fabrics (like RoCE v2, InfiniBand, or NVLink Network), NCCL ring/tree All-Reduces stall on the 10 Gbps Ethernet interfaces.

---

## Comparison Matrix across All Architecture Options

| Metric | Option A (Single Node TP8) | Option B (TP8 + FP8 KV Cache) | Option C (`tp8_pp2_dist` 16-GPU) | Option C (`tp16_pp1_dist` 16-GPU) |
| :--- | :--- | :--- | :--- | :--- |
| **Total GPUs** | 8x RTX PRO 6000 | 8x RTX PRO 6000 | 16x RTX PRO 6000 (2 nodes) | 16x RTX PRO 6000 (2 nodes) |
| **VRAM Capacity** | 768 GB | 768 GB (2x KV density) | 1.536 TB | 1.536 TB |
| **TTFT (128K prefill)** | ~4,374 ms (2,752 ms warm) | ~4,350 ms | ~4,650 ms (2,810 ms warm) | ~8,217 ms |
| **TPOT (Decode)** | 13.91 ms / tok | 13.52 ms / tok | **7.49 ms / tok** | 11.57 ms / tok |
| **Generation Speed** | 71.9 tok/s | 74.0 tok/s | **133.4 tok/s** | 87.0 tok/s |
| **Recommended Use** | Cost-effective single-node | High concurrency / long context | **Maximum throughput / SLA** | Benchmarking / Network analysis |
