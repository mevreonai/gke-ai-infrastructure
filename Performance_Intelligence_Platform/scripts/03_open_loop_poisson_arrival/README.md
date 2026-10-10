# 03. Open-Loop Poisson Arrival Distribution Suite

## 🎯 Purpose & Scope
Characterizes serving behavior under realistic stochastic traffic. In contrast to synthetic closed-loop benchmarks where new requests wait for prior responses, open-loop benchmarks inject requests according to a Poisson arrival process regardless of server queue depth, exposing queue starvation and latency degradation under micro-bursts.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `09_metrics_sampler.py`
* **Purpose:** High-frequency non-intrusive Prometheus metrics harvester polling vLLM `/metrics` endpoint at 500ms intervals.
* **Metrics Harvested:**
  - `vllm:num_requests_waiting`: Requests stalled in queue waiting for memory or batch slots.
  - `vllm:num_requests_running`: Requests actively executing across prefill and decode.
  - `vllm:gpu_cache_usage_factor`: KV-cache memory utilization fraction.
* **Usage:**
  ```bash
  python3 09_metrics_sampler.py --url http://localhost:8000/metrics --interval 0.5 --output metrics_stream.jsonl
  ```

### 2. `15_summarize_vllm.py`
* **Purpose:** Aggregates open-loop and closed-loop request logs, computes queue wait time distributions, extracts percentile metrics, and produces `vllm_runs.csv`.
* **Usage:**
  ```bash
  python3 15_summarize_vllm.py <results_dir> --out <summary_dir>
  ```

### 3. `17_build_serving_analysis.py`
* **Purpose:** Compiles multi-variable plots correlating arrival rate ($\lambda$) against P99 TTFT inflation.

---

## 💡 Landmark Finding
Under high arrival bursts ($\lambda \ge 4\text{ req/s}$ with burstiness), TTFT P99 latency inflates by up to **324%** (382 ms $\to$ 1,240 ms) due to temporary queue depth accumulation, while raw compute execution time remains constant.

---

## 📖 Reference Guides
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
