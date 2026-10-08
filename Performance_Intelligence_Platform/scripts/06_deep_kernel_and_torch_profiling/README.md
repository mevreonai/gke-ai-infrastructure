# 06. Deep Kernel & PyTorch Profiling Suite

## 🎯 Purpose & Scope
Provides micro-architectural, kernel-level visibility into GPU serving execution using NVIDIA Nsight Systems and PyTorch Profiler. Quantifies profiler dilation and isolates CUDA stream execution timelines.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `14_run_vllm_nsys_profile.sh`
* **Purpose:** Launches vLLM under NVIDIA Nsight Systems (`nsys profile`), capturing CUDA runtime APIs, cuBLAS GEMM kernels, and OS thread scheduling.
* **Usage:**
  ```bash
  ./14_run_vllm_nsys_profile.sh --output-trace ../../data/results/real_data/profiles_single_node/nsys_master.nsys-rep
  ```

### 2. `14b_run_vllm_torch_profile.sh` & `14c_run_vllm_torch_profile_batched.sh`
* **Purpose:** Generates Chrome Trace JSONs (`.pt.trace.json.gz`) detailing operator-level call stacks (Linear, LayerNorm, RotaryEmbedding, FlashAttention).

### 3. `21_run_vllm_capped_profiles.sh`
* **Purpose:** Targeted, low-overhead profiling runs capturing only specific iteration windows (warmup step 10 to 15) to minimize profiler dilation.

### 4. `16_analyze_vllm_profiles.py` & `19_postprocess_nsys.py`
* **Purpose:** Parses Nsight SQLite / text exports to compute exact kernel execution time distributions and GEMM vs Attention breakdown.

---

## 📂 Canonical Artifact Placeholders & Storage Policy

All raw captures and processed profiler artifacts are strictly organized inside canonical run directories—**never left in volatile `/tmp` folders**.

### 1. Directory Structure & Placeholders
| Profiler Artifact | Primary Canonical Placement | Purpose & Consumer |
| :--- | :--- | :--- |
| **`.nsys-rep`** | `<RUN_ROOT>/profiles_single_node/tp<N>_<mode>/` or `<RUN_ROOT>/<topo>/<mode>/node<0/1>_capture/` | NVIDIA Nsight Systems binary trace timeline (view in Nsight Systems GUI) |
| **`.sqlite` (Co-located)** | Same directory as `.nsys-rep` (`vllm_profile.sqlite` or `<worker>.sqlite`) | Lightweight relational queries via Python `sqlite3`, DuckDB, and dashboards without GPU/Nsight dependencies |
| **`.sqlite` (Processed)** | `<trace_name>_processed/<trace_name>.sqlite` | Detailed per-trace isolation exported by `19_postprocess_nsys.py` |
| **Kernel / NVTX CSVs** | `<trace_name>_processed/*.csv` | Fast summary tables (`cuda_gpu_kern_sum.csv`, `nvtx_pushpop_sum.csv`, `cuda_api_sum.csv`) |
| **`.pt.trace.json(.gz)`** | `<RUN_ROOT>/torch_profiles/tp<N>/torch/` | PyTorch operator Chrome traces (Perfetto / Chrome tracing viewer) |
| **`NSYS_ANALYSIS.json`** | `<CASE_DIR>/NSYS_ANALYSIS.json` | High-level kernel aggregation and rank completeness validation manifest |
| **`PROFILE_METADATA.json`**| Case root alongside `bench.json` | Run provenance (model identity, tensor parallelism, token lengths, concurrency) |

### 2. Strict Storage & Cleanup Rules
* **Strict No-`/tmp` Policy:** Profiling scripts do not write final output files to `/tmp`. Remote worker samplers, Ray logs, and intermediate metrics generated during multi-node runs are automatically copied to their canonical `node<N>_capture/` folders, and all temporary files on `/tmp` (both local and remote) are immediately purged via `rm -f`.
* **Automatic Zero-Byte Suppression:** Ray worker initialization can spin up idle helper ranks that create 0-byte `.nsys-rep` stubs. All profiling scripts automatically purge `-size 0` stubs at capture time, preventing corrupted files from failing downstream `nsys export` or batch ingestion scripts.
* **Dual SQLite Placement:** To ensure seamless compatibility with both folder-scanning tools and per-trace analyzers, `19_postprocess_nsys.py` creates `.sqlite` databases directly in the case root alongside the `.nsys-rep` capture as well as within the dedicated `_processed` subdirectory.

---

## 💡 Landmark Finding
Active PyTorch profiling hooks introduce up to **18.4% latency dilation** at concurrency $\ge 32$, distorting benchmark measurements. Always use targeted capped profiling windows for production characterization.
