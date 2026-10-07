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

## 💡 Landmark Finding
Active PyTorch profiling hooks introduce up to **18.4% latency dilation** at concurrency $\ge 32$, distorting benchmark measurements. Always use targeted capped profiling windows for production characterization.
