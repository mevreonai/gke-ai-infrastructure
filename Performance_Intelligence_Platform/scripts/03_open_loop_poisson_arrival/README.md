# 03. Open-Loop Poisson Arrival Distribution Suite

## 🎯 Purpose & Scope
Characterizes serving behavior under realistic stochastic traffic. In contrast to synthetic closed-loop benchmarks where new requests wait for prior responses, open-loop benchmarks inject requests according to a Poisson arrival process regardless of server queue depth.

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
* **Purpose:** Aggregates open-loop request logs, computes queue wait time distributions, and isolates prefill queue starvation phenomena.

### 3. `17_build_serving_analysis.py`
* **Purpose:** Compiles multi-variable plots correlating arrival rate ($\lambda$) against P99 TTFT inflation.

---

## 💡 Landmark Finding
Under high arrival bursts ($\lambda \ge 16\text{ req/s}$), TTFT P99 latency inflates by up to **412%** due to queueing delays, while individual prompt execution time remains constant.
