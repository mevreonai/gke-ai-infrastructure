# V8-FULL Characterization Campaign Results & Dashboards Tree

This directory contains the unified and complete empirical dataset, raw benchmark telemetry, hardware validation traces, production dashboards, and release specifications for the **vLLM V8 Characterization Campaign** on Dual RTX 6000 Ada Server Edition nodes connected over Google Cloud VPC.

---

## 🗂 Unified Directory Layout

The campaign results, logs, specifications, and dashboards are organized into a clean, intuitive structure:

| Root Folder | Subdirectory | Content Summary |
| :--- | :--- | :--- |
| **`dashboards/`** | `v4_dashboard/` | **V4 Characterization Dashboard**: Interactive UI with latency/throughput, scheduling, and profiler views (`index.html`) |
| | `v5_dashboard/` | **V5 Decision-Intelligence Dashboard**: Complete operator decision funnel, 60-second briefs, interactive command inspector for all 126 runs (`index.html`) |
| **`results/`** | **`real_data/`** | **Empirical Benchmark & Hardware Data**: 100% of tested runs, case manifests, verification summaries (`coverage.json`, `combined_vllm_runs.json`, `FINAL_VALIDATION.json`), hardware benchmarks, and profiler traces |
| | | ├── `final_validation/`: Aggregated publication gates, coverage matrix, and combined runs |
| | | ├── `vllm_single_node_v6_matrix/`: 58 runs across TP4/TP8, chunk sweeps, decode focus |
| | | ├── `vllm_single_node_v8_1m_extensions/`: 10 runs (1M concurrency c1-c4, prefix caching, max_num_seqs) |
| | | ├── `vllm_scaleout_network_matrix/`: 36 scale-out runs across TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 |
| | | ├── `vllm_open_loop/`: 15 Poisson arrival rate sweeps for queue latency knee analysis |
| | | ├── `hardware_processed/`: BabelStream (1,716 GB/s), NVBandwidth, iperf (173.58 Gbps), NCCL bus tests |
| | | └── `profiles_multi_node_native/`: Nsight Systems & PyTorch profiler traces across both nodes |
| | **`logs/`** | **System & Telemetry Logs**: Runner stdout/stderr logs, node 0 and node 1 preflight verifications, readiness logs, step status, and environment configurations |
| | | ├── `run_logs/`: Suite execution output logs |
| | | ├── `preflight_node0/` & `preflight_node1/`: Environment and driver sanity checks |
| | | ├── `readiness_node0/` & `readiness_node1/`: Hardware initialization and fabric verification |
| | | ├── `step_status.jsonl`: Step-by-step suite execution state machine |
| | | └── `RUN_CONFIG.env`: Active environment variable specifications |
| **`release_specs/`** | | **Release Documentation & Suite**: Specifications, validation criteria, prompt guides, and suite execution scripts |
| | | ├── `V8_FULL_DASHBOARD_DECISION_INTELLIGENCE_SPEC.md` |
| | | ├── `V8_FULL_README.md` |
| | | ├── `V8_FULL_RELEASE_VALIDATION.md` |
| | | ├── `V8_FULL_TEAM_DASHBOARD_MIGRATION_PROMPT.md` |
| | | ├── `V8_FULL_vLLM_RTXPRO6000_Characterization.zip` |
| | | └── `suite_scripts/`: Production runner scripts (`00_run_v8_full.sh`, `21_static_validate_suite.py`, etc.) |
| **`RUNS_INDEX.json`** | | **Machine-Readable Runs Index**: Complete structured index of all 126 test points with metrics and relative file paths |

---

## 📊 Campaign Summary & Run Counts

* **Total Configured Scope:** 126 Cases
  * **95 Native/Local Completed Runs:**
    * 58 Single-Node V6 Base Runs (`SINGLE_NODE_LOCAL`)
    * 10 Single-Node V8 1M Extensions (`SINGLE_NODE_LOCAL`)
    * 12 Native Scale-Out Runs (`GCP_NATIVE`: 4 topologies × 3 contexts: 128K, 512K, 1M)
    * 15 Open-Loop Poisson Sweeps (`SINGLE_NODE_LOCAL`)
  * **24 Auxiliary Capped Sweeps:**
    * 12 `GCP_CAPPED_100G` Scale-Out Runs
    * 12 `GCP_CAPPED_20G` Scale-Out Runs
  * **7 Safety-Guarded NOT_RUN Cases:**
    * 4 FP8 KV cache runs (Guarded: KDA linear model requires BF16 KV cache backend)
    * 3 Host CPU offload runs (Guarded: Prevents PCIe thrashing / host memory OOM)

---

## 🌐 Fabric & Hardware Ground Truth

* **Hardware:** Dual Supermicro Server Nodes, 2×8 NVIDIA RTX 6000 Ada (96GB VRAM per GPU).
* **Interconnect:** PCIe Gen5 over dual-socket AMD EPYC (NUMA).
* **Fabric:** Google Cloud Native VPC, `ens4`, MTU 8896 (Jumbo Frames), measured forward bandwidth: **173.58 Gbps**, reverse: **173.42 Gbps**, RTT: **0.05 ms**, packet drops: **0**.
* **Memory Roof Reference:** BabelStream Copy measures **1,716 GB/s** effective bandwidth with L2 cache amplification (published theoretical DRAM spec is 1,597 GB/s).

---

## 🖥 Production Dashboards

* **V5 Decision-Intelligence Dashboard (Latest):**
  * [`dashboards/v5_dashboard/index.html`](file:///./dashboards/v5_dashboard/index.html)
* **V4 Characterization Dashboard:**
  * [`dashboards/v4_dashboard/index.html`](file:///./dashboards/v4_dashboard/index.html)
