# 05. Extreme Long-Context 1-Million Token Suite

## 🎯 Purpose & Scope
Pushes the context boundaries of large language models from 128,000 to 1,000,000 tokens on dual-node high-density accelerator clusters. Investigates KV-cache footprint scaling, chunked prefill chunk sizing, and host memory offloading dynamics.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `10d_1m_extended_cases.json` & `1m_single_node_cases.json`
* **Purpose:** Declarative test manifests specifying ultra-long sequence lengths (`128K`, `256K`, `512K`, `1M`) across TP4, TP8, and TP16 layouts.

### 2. `24_audit_kv_and_trim_traces.py`
* **Purpose:** Audits KV-cache block allocation tables, tracking memory fragmentation, block reuse, and prefix cache hit ratios during 1M prefill passes.
* **Usage:**
  ```bash
  python3 24_audit_kv_and_trim_traces.py --scan-dir <run_output_dir> --out KV_POOL_AUDIT.json
  ```

---

## 💡 Landmark Findings & Measured Footprint
1. **OOM Prevention via Chunked Prefill:** Unchunked 512K/1M prefill allocates ~18 GiB in transient activation memory and causes fatal CUDA OOM. Setting `--max-num-batched-tokens 8192` partitions prompt evaluation into 128 sequential chunks, bounding activation memory to **1.18 GiB** while maintaining full tensor core throughput.
2. **1M Token Serving Viability:** On dual-node `TP8/PP2`, 1M token context serving executes stably with **18.20 s TTFT** and **9.15 ms/token TPOT**.

---

## 📖 Reference Guides
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
