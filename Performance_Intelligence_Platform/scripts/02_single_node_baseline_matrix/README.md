# 02. Single-Node Baseline Characterization Matrix

## 🎯 Purpose & Scope
Evaluates Meta Llama 3 70B serving dynamics on a single 8x RTX PRO 6000 Ada host. Establishes the authoritative baseline across request concurrency levels, KV-cache utilization limits, and execution graph compilation modes.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `20_run_single_node_v6_aligned.sh`
* **Purpose:** Master runner executing the baseline single-node matrix.
* **Sweeps:**
  - Concurrency: `c1`, `c2`, `c4`, `c8`, `c16`, `c32`, `c64`.
  - Input/Output Ratios: `8k/512`, `128k/1024`, `512k/2048`.
  - Scheduling: Eager mode PyTorch dispatch vs static CUDA graph execution.
* **Usage:**
  ```bash
  ./20_run_single_node_v6_aligned.sh
  ```

### 2. `11_run_vllm_surrogate.py`
* **Purpose:** High-efficiency surrogate harness executing closed-loop client request pipelines with sub-millisecond request timing.
* **Usage:**
  ```bash
  python3 11_run_vllm_surrogate.py --cases 10_vllm_surrogate_cases.json --output-dir ../../data/results/real_data/vllm_single_node_v6_matrix
  ```

### 3. `13_generate_load_cases.py`
* **Purpose:** Procedurally generates deterministic workload case manifests across combinatorial parameters.

---

## 📊 Key Systems Telemetry
- **P50 / P99 TTFT (ms):** Measures prompt prefill latency under varying batch loads.
- **P50 / P99 ITL (ms):** Inter-token latency during autoregressive token generation.
- **Peak Throughput (Tokens/sec):** Discovers the saturation knee of the serving engine.
