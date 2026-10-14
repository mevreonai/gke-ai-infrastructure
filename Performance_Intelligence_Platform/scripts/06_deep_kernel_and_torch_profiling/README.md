# 06. Deep Kernel & PyTorch Profiling Suite

## 🎯 Purpose & Scope
Provides micro-architectural, kernel-level visibility into GPU serving execution using NVIDIA Nsight Systems and PyTorch Profiler. Quantifies profiler dilation, captures CUDA stream execution timelines, and isolates operator execution on CUDA graphs.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `14_run_vllm_nsys_profile.sh`
* **Purpose:** Launches vLLM under NVIDIA Nsight Systems (`nsys profile`), capturing CUDA runtime APIs, cuBLAS GEMM kernels, and OS thread scheduling.
* **Usage:**
  ```bash
  ./14_run_vllm_nsys_profile.sh
  ```

### 2. `14b_run_vllm_torch_profile.sh` & `14c_run_vllm_torch_profile_batched.sh`
* **Purpose:** Generates Chrome Trace JSONs (`.pt.trace.json.gz`) detailing operator-level call stacks (Linear, LayerNorm, FlashAttention, Triton MoE) under single-request and batched ($c=8, 32$) load.

### 3. `18_run_vllm_multi_node_profiles.sh`
* **Purpose:** Coordinates multi-node distributed Nsight captures across Node 0 and Node 1 simultaneously, synchronizing traces over SSH.

### 4. `21_run_vllm_capped_profiles.sh`
* **Purpose:** Targeted, low-overhead profiling runs capturing only specific iteration windows (warmup steps 10 to 15) to minimize profiler dilation.

### 6. `14d_run_vllm_torch_profile_multi_node.sh`
* **Purpose:** Multi-node distributed PyTorch Chrome trace capture across 16-GPU configurations (`tp4_pp4_dist`, `tp8_pp2_dist`, `tp16_pp1_dist`) at $c=8$.

---

## 📂 Canonical Artifact Storage Policy

All raw captures and processed profiler artifacts are strictly organized inside canonical run directories—**never left in volatile `/tmp` folders**.

| Profiler Artifact | Primary Canonical Placement | Purpose & Consumer |
| :--- | :--- | :--- |
| **`.nsys-rep`** | `<RUN_ROOT>/step14_timeline_profiles/` | NVIDIA Nsight Systems binary trace timeline (view in Nsight GUI) |
| **`.sqlite`** | Co-located with `.nsys-rep` | Lightweight relational queries via Python `sqlite3` without Nsight dependencies |
| **`.pt.trace.json`** | `<RUN_ROOT>/step02_torch_profiles_batched/` | PyTorch operator Chrome traces (Perfetto / Chrome tracing viewer) |
| **`NSYS_ANALYSIS.json`** | Trace case root | High-level kernel aggregation and rank completeness validation manifest |

---

## 🔬 Profiling Workloads & Protocols (V8 Parity)
1. **B1 Production Serving Critical Path (Step 14):** Nsight Systems decode trace with CUDA Graphs enabled (ENFORCE_EAGER=0) at 8K context, capturing true production serving breakdown: **4.47 ms total** (CUTLASS MoE 45.0%, FlashInfer 38.0%, NCCL AllReduce 15.0%).
2. **Protocol Disclosure (Eager vs Graphs):** Eager mode Nsight profiling adds Python dispatch overhead, yielding ~30.5 ms decode step time. The B1 capture demonstrates that true production serving runs in 4.47 ms.
3. **Multi-Node Distributed Traces (B11):** Synchronized 16-rank Nsight Systems traces captured during Step 13 (TP16 512K prefill) and Step 14 (multi-node decode).
4. **PyTorch Chrome Traces:** Batched operator-level call stacks at $c=8$ and $c=32$ on single-node and multi-node clusters.

---

## 💡 Landmark Finding
Active PyTorch profiling hooks introduce up to **18.4% latency dilation** at concurrency $\ge 32$, distorting benchmark measurements. Always use targeted capped profiling windows for production characterization.

---

## 📖 Reference Guides
- Master Run Coverage Matrix (Steps 00-20): [`RUN_COVERAGE.md`](../../RUN_COVERAGE.md)
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](../../SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](../../PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
