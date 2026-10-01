# V9 DeepSeek V4.1 Flash Characterization & Full Dashboard Packaging Report

**Date**: October 1, 2026  
**Cluster**: Dual-Node 16× NVIDIA RTX PRO 6000 Blackwell Workstation (8 GPUs/node, PCIe Gen5, Dual 100GbE Interconnect, MTU 8896 Jumbo Frames)  
**Model**: DeepSeek V4.1 Flash (FP4 / MXFP8 Weights, 43 Layers, 64 Attention Heads, 24 Engram Hash Heads)  
**Cluster Infrastructure State**: **`TERMINATED`** (Google Cloud Compute Engine billing completely stopped)  
**Cron Status**: **`CLEARED / STOPPED`** (No background monitoring tasks active)  
**Git Synchronization**: Clean working tree committed and pushed to `origin/main` (`b82dd3a`)

---

## 1. Executive Summary & Cluster Power State

All benchmarking runs, dashboard transitions, and data governance tasks have been finalized with **100% genuine empirical metrics** (zero hallucinated/mocked data). Both Google Cloud VM instances were shut down and verified terminated.

| Cloud Resource | Zone | Machine Specs | GPU Configuration | Current State | Billing Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`kimi-node-0`** | `us-central1-b` | AMD EPYC 9654 (96 vCPU, 384GB RAM) | 8× RTX PRO 6000 Blackwell (96GB each) | **`TERMINATED`** | **Stopped** |
| **`kimi-node-1`** | `us-central1-b` | AMD EPYC 9654 (96 vCPU, 384GB RAM) | 8× RTX PRO 6000 Blackwell (96GB each) | **`TERMINATED`** | **Stopped** |
| **`kimi-node-2`** | `us-west1-a` | Standard compute instance | N/A | **`TERMINATED`** | **Stopped** |

---

## 2. Tab-by-Tab Breakdown: Successes, Failures, and Capability Boundaries

The master dashboard was transitioned 1-to-1 from the V8 template (`v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html`) into V9 (`v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html` and `v9_full_result/index.html`). Every tab accurately portrays real data, with failed or blocked runs explicitly highlighted.

```
+-----------------------------------+---------------------------------------------------------------+-------------------------------------------+
| Dashboard Tab                     | Target Workload / Test Run                                    | Outcome & Technical Mechanism             |
+-----------------------------------+---------------------------------------------------------------+-------------------------------------------+
| 🔬 Profiler                       | 45 Nsight & PyTorch Profiling Runs                            | FAILED: Missing ninja JIT build tool      |
| 🌐 Scale-Out                      | tp4_pp4_dist (TP=4, PP=4)                                     | FAILED: KV-sharing group PP split crash   |
| 🌐 Scale-Out                      | tp16_pp1_dist (TP=16, PP=1)                                   | BLOCKED: 24 Engram heads / 16 ranks       |
| 🌐 Scale-Out                      | tp8_pp2_dist (TP=8, PP=2)                                     | PASSED: 133.64s @ 1M (1.42x over TP8)     |
| 🖥️ Single-Node                    | 17 Matrix Configurations (TP4, TP8)                           | PASSED: 100% exit code 0                  |
| ⚡ Open-Loop                      | Poisson Request Serving Runs (8K, 32K, 128K)                  | PASSED: 100% exit code 0                  |
| 🔌 Hardware                       | PCIe Gen5 & Dual 100GbE Telemetry                             | PASSED: 100% empirical evidence captured  |
+-----------------------------------+---------------------------------------------------------------+-------------------------------------------+
```

---

### Tab 1: 🔬 Profiler Tab (`#profiler`)
* **Execution Status**: **`FAILED (0 / 45 Traces Captured)`**
* **Scope Attempted**:
  * Single-Node Nsight Systems sweeps (`tp4_pp1`, `tp8_pp1` decode and prefill).
  * PyTorch Operator Profiler traces (`torch/profiler_out_*.txt`).
  * Multi-Node Distributed Nsight timelines (`tp8_pp2`, `tp4_pp4`, `tp16_pp1`).
* **Root Cause & Diagnostics**:
  * FlashInfer SM120 decode kernel specialization required dynamic JIT compilation via Ninja during vLLM engine initialization.
  * The execution container environment lacked `ninja` in its `PATH` at profiling time, causing the server processes to terminate immediately with **Return Code 1** before tracing could begin.
* **Why the Tab Initially Contained Data**:
  * During the initial template migration, raw HTML tables and Chart.js code retained static vestigial data from the previous V8 Kimi benchmark (`112,640 kernels traced`, `86.3% AllReduce`, `FlashAttention 6.24ms`, `251.5ms Self CUDA time`).
* **Current Dashboard State**:
  * **Top Alert Banner**: Displays a prominent red diagnostic card explaining the missing `ninja` build tool and zero-trace capture status.
  * **KPI Cards**: `AllReduce Barrier`, `FlashAttention fwd`, `Decode GEMV`, and `Host Launch` are all marked **`FAILED (0 Traces)`**.
  * **Charts**: All 4 charts (`chart_prof_kernel_categories`, `chart_prof_pytorch_operators`, `chart_prof_cuda_api`, `chart_prof_kernel_latency`) display empty datasets with an explicit red watermark: `⚠️ PROFILER EXECUTION FAILED / ZERO TRACES CAPTURED`.
  * **Audit Tables & Ledgers**: Replaced with notices confirming `ZERO EMPIRICAL PROFILER DATA AVAILABLE`, adhering strictly to zero-hallucination governance.

---

### Tab 2: 🌐 Scale-Out & Distributed Topology (`#scaleout`)

#### A. Verified Winner: `tp8_pp2_dist` (100% Pass)
* **Configuration**: Intra-node Tensor Parallelism of 8 (spanning all 8 GPUs per machine over PCIe Gen5) combined with Pipeline Parallelism of 2 across the dual 100GbE network interconnect.
* **Benchmark Results**:
  * **1K Context**: 146.40 ms TTFT, 11.23 ms TPOT.
  * **8K Context (c1)**: 457.77 ms TTFT, 10.96 ms TPOT.
  * **128K Context (c1)**: 9.33 s TTFT, 12.19 ms TPOT.
  * **1M Context (1,000,000 tokens)**: **133.64 s TTFT**, 78.07 ms TPOT, 2.10% peak KV cache utilization.
* **Key Finding**: Outperforms single-node TP8 (189.68 s TTFT) by **1.42×** at 1M tokens due to stage-pipelined prefill execution.

#### B. Failed Run: `tp4_pp4_dist`
* **Status**: **`SERVER_START_FAILED / CAPABILITY_BLOCKED`**
* **Technical Root Cause**: In DeepSeek V4.1 Flash, layers 20–42 share compressed KV caches with layer 20 (`kv_source_layer_ids = [2, 8, 14, 20]`). Under PP=4, the 43 layers are partitioned across 4 stages (~11 layers/stage). Stage 1 holds layer 20 while Stage 2 holds layers 22–32. When Stage 2 attempts to reference layer 20's attention state across the pipeline split, vLLM raises:
  ```text
  NotImplementedError: Compressed-KV source language_model.model.layers.20.attn not found on this rank;
  PP splits inside a v4.1 kv-sharing group are not supported.
  ```
* **Dashboard Representation**: Marked in red as **`FAILED: PP Split in KV-Sharing Group`** with `null` data curves across all scaling and comparison charts.

#### C. Blocked Configuration: `tp16_pp1_dist`
* **Status**: **`CAPABILITY_BLOCKED`**
* **Technical Root Cause**: DeepSeek V4.1 Flash features 24 Engram hash heads. Dividing 24 heads across 16 tensor-parallel ranks requires non-uniform sharding (ranks 0–11 receive 2 heads; ranks 12–15 receive 0 heads). vLLM rejects non-uniform head allocation because all TP ranks must have identical attention/Engram head counts.
* **Dashboard Representation**: Marked in red as **`BLOCKED: 24 Heads / 16 Ranks`** with `null` data curves.

---

### Tab 3: 💡 Executive Summary & Key Discoveries (`#keydiscoveries`)
* **Purge of Residual V8 Numbers**: Expunged all old V8 numbers (`28.57s` for TP4/PP4, `68.20s` for TP16/PP1, `35.2%` utilization, `457 GPU-s`).
* **Updated V9 Insights**:
  * Positions **`TP8/PP2`** as the sole verified multi-node serving topology for 1M context tokens.
  * Formulates the architectural boundary rules for DeepSeek V4.1 Flash (PP splits cannot cut across KV-sharing groups, and TP rank count must divide 24 Engram heads evenly).

---

### Tab 4: 🖥️ Single-Node Matrix (`#singlenode`)
* **Status**: **`100% PASS`** (All 17 matrix test cases completed exit code 0).
* **Summary Metrics**:
  * **TP8 Single-Node**: 111.45 ms TTFT at 1K; 13.91 s TTFT at 128K; 189.68 s TTFT at 1M.
  * **TP4 Single-Node**: 108.20 ms TTFT at 1K; 19.46 s TTFT at 128K; OOM at 1M tokens.
  * **Tradeoff**: TP8 delivers 1.40× faster TTFT at 128K context compared to TP4.

---

### Tab 5: ⚡ Open-Loop Serving (`#openloop`)
* **Status**: **`100% PASS`** (All 3 context workloads completed exit code 0).
* Evaluated Poisson request arrival distributions across 8K, 32K, and 128K context tokens to measure tail latency degradation and queue saturation points.

---

### Tab 6: 🔌 Hardware & Network Telemetry (`#hardware`)
* **Status**: **`100% PASS`** (`HARDWARE_POINTS.json`).
* Verified physical hardware baselines:
  * **PCIe Gen5 Bandwidth**: 24.8 GB/s bidirectional host-to-device bandwidth per GPU.
  * **Dual 100GbE VPC Interconnect**: 94.2 Gbps aggregate bandwidth measured via iperf3.
  * **MTU 8896**: Jumbo frame packet delivery validated across nodes with zero packet drop.

---

## 3. Package File Manifest (`v9_full_result/`)

All generated deliverables, validation summaries, and dashboards reside in `v9_full_result/`:

1. **Dashboards**:
   * `MASTER_CHARACTERIZATION_DASHBOARD.html` (1.18 MB master interactive HTML report)
   * `index.html` (Production entrypoint)
   * `chart.umd.js` (Offline Chart.js bundle)
2. **Empirical Evidence Data**:
   * `final_validation/combined_vllm_runs.json` (77 raw execution logs and parsed run outputs)
   * `final_validation/combined_vllm_runs.csv`
   * `final_validation/coverage.json` & `coverage.csv`
   * `final_validation/FINAL_VALIDATION.json` & `FINAL_VALIDATION.md`
   * `final_validation/PROFILE_COVERAGE.json`
   * `v9_full_production_20260930_143117_FULL_EVIDENCE.tar.gz.sha256` (126.29 MB tarball checksum)
3. **Execution Status**:
   * `v9_execution_tracker.json` (`"status": "COMPLETED"`, `"progress_pct": 100.0`)

---

## 4. GitHub Synchronization

All modifications, dashboard files, and validation reports have been pushed to GitHub:

* **Repository**: `https://github.com/unrealayush/gke-ai-infrastructure.git`
* **Commits**:
  * `714e9b5`: `feat(v9): finalize V9 DeepSeek V4.1 Flash benchmark results, dashboard, and validation`
  * `b82dd3a`: `fix(v9): purge vestigial V8 data from profiler tab and explicitly mark failed/blocked runs`
* **Branch**: `main`
* **Working Tree**: Completely clean (`nothing to commit, working tree clean`).
