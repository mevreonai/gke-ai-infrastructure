# Master Benchmark Summary: Blackwell RTX PRO 6000 Kimi-Linear 48B Suite (V5)

**Environment:** Google Cloud Platform `g4-standard-384` / `g4-standard-96` (`us-central1-b`)  
**Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition (96 GB GDDR7 per GPU, Compute Capability 12.0)  
**Software Stack:** vLLM v0.29.0, CUDA 13.0, PyTorch 2.6, Python 3.12, Ray Cluster  
**Workload Model:** `moonshotai/Kimi-Linear-48B-A3B-Instruct` (48B hybrid linear attention + MoE surrogate)  

---

## 1. Executive Summary

This suite conducts an exhaustive, multi-dimensional characterization of large-context linear attention and Mixture-of-Experts (MoE) serving on NVIDIA Blackwell RTX PRO 6000 hardware across three progressive options:
1. **Option A (Single-Node vLLM Surrogate Sweep):** 8-GPU Tensor Parallelism (TP=8) evaluating prefill chunk sizes (4K, 8K, 16K), context lengths from 8K to 1M tokens, prefix caching, and concurrency scaling.
2. **Option B (Surgical Nsys CUDA Kernel Profiling):** Discrete layer-by-layer kernel tracing under eager execution, isolating Triton MoE, FlashAttention MLA, Kimi Delta Attention (KDA), and NCCL All-Reduce overheads.
3. **Option C (16-GPU Multi-Node Distributed Serving):** Multi-node scaling across two 8-GPU nodes comparing Pipeline Parallelism (`tp8_pp2_dist`) against distributed Tensor Parallelism (`tp16_pp1_dist`) over 10 Gbps GCP VPC networking.

---

## 2. Cross-Architecture Performance Matrix

| Metric | Option A (`tp8_cold_chunk8k`) | Option A (`tp4_chunk16k`) | Option B (Nsys Eager Profile) | Option C (`tp8_pp2_dist` 16-GPU) | Option C (`tp16_pp1_dist` 16-GPU) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Topology** | 1 Node (8 GPUs, TP8) | 1 Node (4 GPUs, TP4) | 1 Node (8 GPUs, Eager) | 2 Nodes (16 GPUs, TP8 PP2) | 2 Nodes (16 GPUs, TP16 PP1) |
| **Total VRAM** | 768 GB | 384 GB | 768 GB | 1,536 GB (1.536 TB) | 1,536 GB (1.536 TB) |
| **Test Context** | 8K input / 128 out | 128K input / 128 out | 128K input / 32 out | 128K input / 128 out | 128K input / 128 out |
| **TTFT (Cold)** | **278.45 ms** | **4,654.34 ms** | **4,970.15 ms** | **4,650.99 ms** | **8,216.91 ms** |
| **TTFT (Warmed)** | ~180 ms | ~2,750 ms | N/A (profiler overhead) | **2,810.45 ms** | 8,216.91 ms |
| **TPOT (Decode Latency)** | **6.88 ms / tok** | **5.71 ms / tok** | **31.46 ms / tok** (unbatched) | **7.49 ms / tok** | **11.57 ms / tok** |
| **Decode Throughput** | **145.3 tok/s** | **175.1 tok/s** | ~32 tok/s (overhead) | **133.4 tok/s** | **87.0 tok/s** |
| **Median ITL** | 6.85 ms | 5.69 ms | 31.26 ms | 7.48 ms | 11.55 ms |
| **E2E Latency** | 1,159 ms | 5,385 ms | 5,976 ms | 5,602.77 ms | 9,685.75 ms |

---

## 3. Detailed Option Findings

### Option A: Single-Node vLLM Surrogate Sweep
- **Chunked Prefill Scaling:** Increasing prefill chunk size from 4K to 16K reduces 128K TTFT from **5,451 ms down to 4,654 ms** (14.6% improvement) by maximizing SM tensor core occupancy during linear attention state updates.
- **Prefix Caching:** Automatic Prefix Caching achieves an instantaneous **1,278 ms TTFT** on shared 128K context prompts (a **3.64× acceleration** over cold prefill).
- **TP4 vs TP8 Intra-Node:** In single-socket 4-GPU NUMA configurations, TP4 achieves 5.01 ms decode TPOT (200 tok/s), avoiding cross-socket Intel UPI link traversal.

### Option B: Low-Level Kernel Decomposition
- **Kernel Verification:** Exact match of kernel executions confirms 80 model layers:
  - `fused_recurrent_kda_packed_decode_kernel`: exactly 2,480 instances ($31 \text{ decode steps} \times 80 \text{ layers}$).
  - `_causal_conv1d_update_kernel`: exactly 2,480 instances.
- **Discovered Blackwell Kernels:**
  - CUTLASS Blackwell MoE: `cutlass::gemm::kernel::MoeFCGemm` & `fused_moe::run_global`
  - Kimi Delta Attention: `chunk_gated_delta_rule_fwd_kernel_h_blockdim64` & `chunk_kda_fwd_kernel_intra_token_parallel`
  - MLA KV Packing: `vllm::kimi_k3_fused_ops::fusedKimiK3MLAKVConcatPackKernel`
- **Overhead Analysis:** Eager profiling adds ~25 ms CPU-GPU synchronization overhead per token during Nsys event interception.

### Option C: 16-GPU Multi-Node Distributed Serving
- **Pipeline Parallelism (`tp8_pp2_dist`) Dominates:**
  - Achieves **7.49 ms / token** decode latency (**133.4 tokens/sec**).
  - Keeps all heavy All-Reduce operations confined within the local 8-GPU chassis over PCIe Gen 5 (~128 GB/s bi-directional).
  - Only small Point-to-Point (P2P) hidden activation vectors cross the inter-node 10 Gbps Ethernet boundary between Node 0 and Node 1.
- **Tensor Parallelism across Nodes (`tp16_pp1_dist`) Suffers Network Penalty:**
  - Decode latency degrades to **11.57 ms / token** (35% slower than `tp8_pp2_dist`).
  - TTFT doubles to **8,216.91 ms**.
  - Forcing All-Reduce across 16 GPUs over standard 10 Gbps Ethernet introduces catastrophic communication stalls on every single transformer layer.

---

## 4. Production Architecture Recommendations

1. **For Single Node (8× RTX PRO 6000, 768 GB VRAM):**
   - Run **TP=8** with **16K chunked prefill** (`--max-num-batched-tokens 16384`) and `--enable-prefix-caching`.
   - Optimal for workloads up to 1M context with concurrency $\le 4$.
2. **For Multi-Node Scale-Out (16+ GPUs, Standard VPC Networking):**
   - **Always deploy Pipeline Parallelism across nodes (`TP=8, PP=N`)**; never cross standard cloud Ethernet with Tensor Parallelism.
   - Pair TP8 within each 8-GPU PCIe node with PP across nodes for linear layer scaling and sub-8ms decode latencies.
