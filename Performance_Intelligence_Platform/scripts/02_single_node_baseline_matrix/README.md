# 02. Single-Node Baseline Characterization Matrix

## 🎯 Purpose & Scope
Evaluates single-node serving dynamics across 4-GPU (`TP4/PP1`) and 8-GPU (`TP8/PP1`) topologies on an 8x RTX PRO 6000 Ada / Blackwell host. Establishes authoritative baselines across request concurrency levels ($c=1..64$), chunked prefill budgets, KV-cache utilization limits, and execution graph compilation modes.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `20_run_single_node_v6_aligned.sh`
* **Purpose:** Master runner executing the baseline single-node matrix.
* **Sweeps:**
  - Concurrency: `c1`, `c2`, `c4`, `c8`, `c16`, `c32`, `c64`.
  - Context Ratios: 8K prompt / 512 completion, 128K prompt / 1024 completion.
  - Scheduling: Eager mode PyTorch dispatch vs static CUDA graph execution.
* **Usage:**
  ```bash
  ./20_run_single_node_v6_aligned.sh
  ```

### 2. `11_run_vllm_surrogate.py`
* **Purpose:** High-efficiency surrogate harness executing closed-loop client request pipelines with sub-millisecond request timing and detailed timing extraction (`--save-detailed`).
* **Usage:**
  ```bash
  python3 11_run_vllm_surrogate.py --cases 10_vllm_surrogate_cases.json --out ./results --port 8000
  ```

### 3. `13_generate_load_cases.py`
* **Purpose:** Procedurally generates deterministic workload case manifests across combinatorial parameters.

### 4. `10_vllm_surrogate_cases.json`
* **Purpose:** Declarative test definitions for chunk budget A/B testing, short prompts, 128K sensitivity, and FP8 quantization.

---

## 📊 Key Systems Telemetry & Measured Results
- **P50 / P99 TTFT (ms):** Measures prompt prefill latency under varying batch loads (e.g., 245.9 ms baseline at $c=1$, scaling to 3,665 ms at $c=32$).
- **P50 / P99 TPOT (ms):** Time per output token during autoregressive token generation (e.g., 8.71 ms at $c=1$ on TP4, 5.42 ms on TP8).
- **Peak Throughput:** Discovers saturation knees (saturates at ~2,260 tok/s on TP4/PP1, ~2,300 tok/s on TP8/PP1).

## 🧊 Cold vs. Warm Cache Isolation Architecture
In order to prevent prefix caching distortion across concurrency levels, single-node runs enforce strict process-level isolation:
* **vLLM Process Termination:** `vllm serve` is cleanly stopped between concurrency evaluations.
* **VRAM Drain Barrier:** A barrier verifies complete GPU VRAM release before starting the next concurrency level.
* **Fresh Server Boot:** Each concurrency level runs against a newly booted instance with zero KV-cache hits.
* **Explicit Ledger Attribution:** Result files are stamped with `cache_state: "cold"` or `cache_state: "warm"` to distinguish lone read TTFT from multi-turn prefix reuse.

---

## 📖 Reference Guides
- Master Run Coverage Matrix (Steps 00-20): [`RUN_COVERAGE.md`](../../RUN_COVERAGE.md)
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](../../SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](../../PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
