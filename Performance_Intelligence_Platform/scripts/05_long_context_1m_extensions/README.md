# 05. Extreme Long-Context 1-Million Token Suite

## 🎯 Purpose & Scope
Pushes the context boundaries of large language models from 128,000 to 1,000,000 tokens on dual-node high-density accelerator clusters. Investigates KV-cache footprint scaling, chunked prefill chunk sizing, and host memory offloading dynamics.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `10d_1m_extended_cases.json` & `stage2_cases_single_node.json`
* **Purpose:** Declarative test manifests specifying ultra-long sequence lengths (`128K`, `256K`, `512K`, `1M`).

### 2. `24_audit_kv_and_trim_traces.py`
* **Purpose:** Audits KV-cache block allocation tables, tracking memory fragmentation, block reuse, and prefix cache hit ratios during 1M prefill passes.
* **Usage:**
  ```bash
  python3 24_audit_kv_and_trim_traces.py --log-dir ../../data/raw_runs/stage2/step11_1m_high_concurrency
  ```

---

## 💡 Landmark Finding
Unchunked 512K/1M prefill causes fatal OOM. Setting `--max-num-batched-tokens 8192` partitions prompt evaluation into manageable chunks, bounding activation memory under 1.2 GiB while maintaining full tensor core throughput.
