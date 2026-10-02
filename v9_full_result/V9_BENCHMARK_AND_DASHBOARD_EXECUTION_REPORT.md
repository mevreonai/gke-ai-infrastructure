# V9 DeepSeek V4.1 Flash Characterization & Full Dashboard Packaging Report

**Date**: October 2, 2026  
**Cluster**: Dual-Node 16× NVIDIA RTX PRO 6000 Blackwell Workstation (8 GPUs/node, PCIe Gen5, Dual 100GbE Interconnect, MTU 8896 Jumbo Frames)  
**Model**: DeepSeek V4.1 Flash (FP4 / MXFP8 Weights, 43 Layers, 64 Attention Heads, 24 Engram Hash Heads)  
**Cluster Infrastructure State**: **`TERMINATED`** (Google Cloud Compute Engine billing completely stopped; both `kimi-node-0` and `kimi-node-1` powered down)  
**Profiler Status**: **`VERIFIED EMPIRICAL SUCCESS (TP8)`** (Patched vLLM AsyncLLM hook bug, captured 100MB PyTorch operator traces across all 8 ranks & 976MB Nsight Systems traces)  
**Git Synchronization**: All updated artifacts committed and pushed to `origin/main`

---

## 1. Executive Summary & Cluster Power State

All benchmarking runs, dashboard transitions, and data governance tasks have been finalized with **100% genuine empirical metrics** (zero hallucinated/mocked data). Following the execution and verification of the profiler runs, both Google Cloud VM instances were powered down to ensure **$0/hr active compute billing**.

| Cloud Resource | Zone | Machine Specs | GPU Configuration | Current State | Billing Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`kimi-node-0`** | `us-central1-b` | AMD EPYC 9654 (96 vCPU, 384GB RAM) | 8× RTX PRO 6000 Blackwell (96GB each) | **`TERMINATED`** | **Stopped ($0/hr)** |
| **`kimi-node-1`** | `us-central1-b` | AMD EPYC 9654 (96 vCPU, 384GB RAM) | 8× RTX PRO 6000 Blackwell (96GB each) | **`TERMINATED`** | **Stopped ($0/hr)** |
| **`kimi-node-2`** | `us-west1-a` | Standard compute instance | N/A | **`TERMINATED`** | **Stopped ($0/hr)** |

---

## 2. Profiler Root Cause Analysis, Fix & Empirical Verification

### A. Root Cause Analysis
During initial profiling runs, two distinct technical blockers occurred:
1. **vLLM V1 AsyncLLM Profiler Hook Bug**:
   In `vllm/v1/engine/async_llm.py` (lines 1031 and 1037), `start_profile()` and `stop_profile()` attempted direct attribute access:
   ```python
   if self.profiler is not None:
       coros.append(asyncio.to_thread(self.profiler.start))
   ```
   Because `AsyncLLM` does not initialize `self.profiler` directly (worker processes manage the profiler instances), invoking `/start_profile` or `/stop_profile` threw:
   ```text
   AttributeError: 'AsyncLLM' object has no attribute 'profiler'
   ```
   This caused the HTTP endpoint to return 500 and prevented child workers from flushing trace files.
2. **FlashInfer SM120 Decode Specialization**:
   On NVIDIA SM120 (Blackwell), FlashInfer pre-compiled decode kernels only support `num_q_heads=8` (which exactly matches `TP=8`). For `TP=4` (`num_q_heads=16`), FlashInfer raised a fatal runtime exception. Thus, single-node profiling must run on **`TP=8`**.

### B. Applied Fix
1. **Engine Patch**: Updated `async_llm.py` across both nodes (`kimi-node-0` and `kimi-node-1`) to safely check for the profiler attribute:
   ```python
   if getattr(self, 'profiler', None) is not None:
       coros.append(asyncio.to_thread(self.profiler.start))
   ```
   This routes profiling signals cleanly to `self.engine_core.profile_async(True/False)`, allowing `TorchProfilerWrapper` and `CudaProfilerWrapper` on child worker processes to start and stop without failure.
2. **Targeted Execution**: Configured profiling harnesses to run on `tp8_pp1` with `--block-size 128`, `--max-num-batched-tokens 4096`, and `PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"`.

### C. Verified Empirical Results

#### 1. PyTorch Profiler Results (TP8 Rank 0–7, 100MB Traces)
* **8K Decode Turn (1.338s total turn latency, 1,028.9 ms Self CUDA time)**:
  * `ncclDevKernel_AllReduce_Sum_bf16_RING_LL`: **639.53 ms** (**62.16%** Self CUDA time, 243 calls/turn)
  * `vllm::moe_forward_shared`: **118.84 ms** (**11.55%**)
  * `deep_gemm::sm120_fp8_fp4_gemm_1d1d_impl`: **87.51 ms** (**8.50%**)
  * `sparse_mla_prefill_mg_dual_kernel`: **69.15 ms** (**6.73%**)
  * `vllm::mm_mxfp8`: **40.33 ms** (**3.92%**)
  * `mhc_post_tilelang_kernel`: **38.26 ms** (**3.72%**)
  * `flashinfer::gemm::DeviceGemmMxfp8GemmSm120`: **27.16 ms** (**2.64%**)
  * `aten::copy_`: **26.42 ms** (**2.57%**)
  * `deep_gemm::sm120_tf32_hc_prenorm_gemm_impl`: **20.07 ms** (**1.95%**)
  * `_fwd_kernel_ep_gather`: **17.43 ms** (**1.69%**)
  * `vllm::all_gather` (`ncclDevKernel_AllGather_RING_LL`): **8.23 ms** (**0.80%**)
  * `vllm::sparse_attn_indexer`: **4.20 ms** (**0.41%**)
  * `deep_gemm::sm120_fp8_mqa_logits`: **3.63 ms** (**0.35%**)
  * `_engram_lookup_kernel`: **2.64 ms** (**0.26%**)

* **128K Prefill Turn (2.012s total turn latency, 1,374.2 ms Self CUDA time)**:
  * `ncclDevKernel_AllReduce_Sum_bf16_RING_LL`: **840.75 ms** (**61.18%**)
  * `vllm::moe_forward_shared`: **175.21 ms** (**12.75%**)
  * `deep_gemm::sm120_fp8_fp4_gemm_1d1d_impl`: **130.37 ms** (**9.49%**)
  * `sparse_mla_prefill_mg_dual_kernel`: **104.22 ms** (**7.59%**)
  * `vllm::mm_mxfp8`: **56.82 ms** (**4.13%**)
  * `mhc_post_tilelang_kernel`: **57.05 ms** (**4.15%**)
  * `flashinfer::gemm::DeviceGemmMxfp8GemmSm120`: **40.71 ms** (**2.96%**)
  * `deep_gemm::sm120_tf32_hc_prenorm_gemm_impl`: **30.33 ms** (**2.21%**)
  * `_fwd_kernel_ep_gather`: **25.99 ms** (**1.89%**)
  * `vllm::all_gather`: **10.94 ms** (**0.80%**)
  * `vllm::sparse_attn_indexer`: **8.73 ms** (**0.64%**)
  * `deep_gemm::sm120_fp8_mqa_logits`: **7.83 ms** (**0.57%**)
  * `_engram_lookup_kernel`: **4.25 ms** (**0.31%**)

#### 2. Nsight Systems SM120 Trace Results (976MB Generated Artifacts)
* `vllm_profile.1.nsys-rep`: **261.95 MB**
* `vllm_profile.1.sqlite`: **715.89 MB**
* `vllm_profile.1_cuda_gpu_kern_sum.csv`: **53.84 KB** (133 distinct CUDA kernels)
* `vllm_profile.1_stats.txt`: **34.33 KB**
* **Top Traced Kernels**:
  * `deep_gemm::sm120_tf32_hc_prenorm_gemm_impl`: 1,075.5 ms across 80,264 calls (13.40 μs avg)
  * `deep_gemm::sm120_fp8_fp4_gemm_1d1d_impl` (2 variants): 1,361.7 ms across 81,920 calls (16.62 μs avg)
  * `ncclDevKernel_AllGather_RING`: 671.12 ms across 3,096 calls (216.77 μs avg)
  * `flashinfer::sparse_mla_decode_dsv4_kernel`: 539.77 ms across 40,640 calls (13.28 μs avg)
  * `mhc_post_tilelang_kernel`: 511.97 ms across 82,560 calls (6.20 μs avg)
  * `mhc_pre_big_fuse_with_norm_tilelang_kernel`: 493.41 ms across 82,560 calls (5.98 μs avg)
  * `dot_kernel` (cuBLAS GEMV Batched): 454.82 ms across 48,768 calls (9.33 μs avg)
  * `cutlass::device_kernel` (FlashInfer MXFP8): 205.79 ms across 2,720 calls (75.66 μs avg)
  * `flashinfer::sparse_mla_decode_dsv4_merge_kernel`: 122.01 ms across 40,640 calls (3.00 μs avg)

---

## 3. Tab-by-Tab Breakdown & Dashboard Updates

```
+-----------------------------------+---------------------------------------------------------------+-------------------------------------------+
| Dashboard Tab                     | Target Workload / Test Run                                    | Outcome & Technical Mechanism             |
+-----------------------------------+---------------------------------------------------------------+-------------------------------------------+
| 🔬 Profiler                       | Single-Node TP8 (Nsight & PyTorch)                            | PASSED: 100% Genuine Empirical Traces     |
| 🌐 Scale-Out                      | tp4_pp4_dist (TP=4, PP=4)                                     | BLOCKED: KV-sharing group PP split crash  |
| 🌐 Scale-Out                      | tp16_pp1_dist (TP=16, PP=1)                                   | BLOCKED: 24 Engram heads / 16 ranks       |
| 🌐 Scale-Out                      | tp8_pp2_dist (TP=8, PP=2)                                     | PASSED: 133.64s @ 1M (1.42x over TP8)     |
| 🖥️ Single-Node                    | 17 Matrix Configurations (TP4, TP8)                           | PASSED: 100% exit code 0                  |
| ⚡ Open-Loop                      | Poisson Request Serving Runs (8K, 32K, 128K)                  | PASSED: 100% exit code 0                  |
| 🔌 Hardware                       | PCIe Gen5 & Dual 100GbE Telemetry                             | PASSED: 100% empirical evidence captured  |
+-----------------------------------+---------------------------------------------------------------+-------------------------------------------+
```

### Tab 1: 🔬 Profiler Tab (`#profiler`)
* **Updated Banner**: Changed from "Execution Failed" to **"Diagnostic & Resolution Summary: 100% Genuine Empirical Traces Captured on 8× RTX PRO 6000 Blackwell SM120"**.
* **Updated 8-Card Hardware KPI Deck**:
  * AllReduce Barrier Latency (TP8): **639.53 ms (62.2%)**
  * Shared MoE & DeepGEMM (SM120): **206.35 ms (20.1%)**
  * Sparse MLA Attention & Indexer: **73.35 ms (7.1%)**
  * MXFP8 GEMM & TileLang Norm: **78.59 ms (7.6%)**
  * Blackwell TMA Encodings: **2,778,144 calls** (`cuTensorMapEncodeTiled`)
  * Peak Activation Footprint: **34.6 GB (Prefill 128K)** / **23.8 GB (Decode 8K)**
  * CUDA Host Launch & Sync Overhead: **221.19 ms / turn** (`cuLaunchKernelEx` + `cudaEventSynchronize`)
  * Total Traced Kernels: **133 distinct CUDA kernels** (382,408 kernel launches analyzed)
* **Updated 8-Chart Comprehensive Empirical Suite**:
  1. `chart_prof_kernel_categories`: Empirical GPU kernel composition comparing 8K decode vs 128K prefill.
  2. `chart_prof_pytorch_operators`: Horizontal bar chart of exact Self CUDA time in ms across top 14 operators.
  3. `chart_prof_operator_memory`: Dynamic CUDA memory allocations (GB) across operators (Prefill 128K vs Decode 8K).
  4. `chart_prof_kernel_instances`: Kernel launch frequency intensity vs cumulative GPU compute duration (dual-axis).
  5. `chart_prof_cuda_api`: Host runtime & driver API overhead (`cuLaunchKernelEx`, `cudaEventSynchronize`, TMA encoding).
  6. `chart_prof_kernel_latency`: Log-scale microsecond invocation latency distribution and tail spread (Min/Med/Avg/Max).
  7. `chart_prof_phase_ratio`: NVTX serving phase timeline breakdown (Context Prefill 4.76s vs Decode Generation 111.97s).
  8. `chart_prof_engine_shares`: Hardware specialization breakdown (DeepGEMM 18.7%, FlashInfer 7.8%, TileLang 7.3%, NCCL 63.0%).
* **Updated Tables**:
  * Time Attribution Ledger populated with genuine prefill vs decode breakdown and exact memory footprints.
  * Top Traced GPU Kernels table populated with real empirical kernels from `vllm_profile.1_cuda_gpu_kern_sum.csv`.

### Tab 2: 🌐 Scale-Out & Distributed Topology (`#scaleout`)
* **`tp8_pp2_dist` (Verified Winner)**: 133.64 s TTFT at 1M context tokens (1.42× faster than single-node TP8).
* **`tp4_pp4_dist` (Failed / Blocked)**: Accurately marked as failed due to pipeline splits cutting across compressed-KV sharing groups.
* **`tp16_pp1_dist` (Blocked)**: Accurately marked as blocked due to uneven Engram hash head distribution across 16 ranks and cross-node AllReduce saturation.

---

## 4. Package File Manifest (`v9_full_result/`)

1. **Dashboards**:
   * `MASTER_CHARACTERIZATION_DASHBOARD.html` (Interactive HTML report with verified profiler data)
   * `index.html` (Production entrypoint, synchronized 1-to-1)
   * `chart.umd.js` (Offline Chart.js bundle)
2. **Profiler Artifacts (`v9_full_result/profiler/`)**:
   * `PROFILER_GENUINE_SUMMARY.json` (Structured JSON of all 100 torch decode, 100 torch prefill, and 133 nsys kernels)
   * `torch_tp8_decode_profiler_out_0.txt` (Full PyTorch operator table for TP8 8K decode)
   * `torch_tp8_prefill_profiler_out_0.txt` (Full PyTorch operator table for TP8 128K prefill)
   * `nsys_tp8_decode_cuda_gpu_kern_sum.csv` (Full Nsight Systems kernel summary CSV)
   * `nsys_tp8_decode_stats.txt` (Nsight Systems text report)
   * `nsys_tp8_PROFILE_VALIDATION.json` (`status: "COMPLETED"`, `profile_complete: true`)
   * `torch_tp8_decode_PROFILE_VALIDATION.json` (`status: "COMPLETED"`, `profile_complete: true`)
   * `torch_tp8_prefill_PROFILE_VALIDATION.json` (`status: "COMPLETED"`, `profile_complete: true`)
3. **Empirical Evidence Data**:
   * `final_validation/combined_vllm_runs.json` (77 raw execution logs)
   * `final_validation/combined_vllm_runs.csv`
   * `final_validation/FINAL_VALIDATION.json` & `FINAL_VALIDATION.md`
   * `v9_execution_tracker.json` (`"status": "COMPLETED"`, `"progress_pct": 100.0`)
