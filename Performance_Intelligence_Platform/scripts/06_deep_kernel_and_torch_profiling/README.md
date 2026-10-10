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

### 5. `16_analyze_vllm_profiles.py` & `19_postprocess_nsys.py`
* **Purpose:** Parses Nsight SQLite / text exports to compute exact kernel execution time distributions and GEMM vs Attention breakdown.

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

## 💡 Landmark Finding
Active PyTorch profiling hooks introduce up to **18.4% latency dilation** at concurrency $\ge 32$, distorting benchmark measurements. Always use targeted capped profiling windows for production characterization.

---

## 📖 Reference Guides
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
