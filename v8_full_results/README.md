# V8-FULL Characterization Campaign Results Tree

This directory contains the complete empirical dataset, raw benchmark telemetry, hardware validation traces, and validation gates for the **vLLM V8 Characterization Campaign** on Dual RTX 6000 Ada Server Edition nodes connected over Google Cloud VPC.

---

## 🗂 Structured Directory Layout

The campaign results and production dashboards are organized cleanly as follows:

| Path | Scope / Description | Content Summary |
| :--- | :--- | :--- |
| [`dashboards/v4_dashboard/`](file:///./dashboards/v4_dashboard) | **Production V4 Dashboard** | Complete interactive characterization UI (`index.html` & `MASTER_CHARACTERIZATION_DASHBOARD.html`) |
| [`20260921_195656/`](file:///./20260921_195656) | **Canonical Campaign Run Directory** | Full empirical data tree across all single-node, scale-out, open-loop, hardware, and profiling runs |
| ├── `final_validation/` | **Publication Gates & Aggregated Trees** | `coverage.json`, `combined_vllm_runs.json`, `FINAL_VALIDATION.json` |
| ├── `vllm_single_node_v6_matrix/` | **Single-Node Base Matrix (V6 Lineage)** | 58 runs: TP4 vs TP8, chunk size sweeps (4K/8K/16K), decode focus, qualifications |
| ├── `vllm_single_node_v8_1m_extensions/` | **Single-Node 1M Context Extensions** | 10 runs: 1M concurrency (c1, c2, c4), 1M prefix reuse, `max_num_seqs` (4, 8, 16) |
| ├── `vllm_scaleout_network_matrix/` | **Distributed Scale-Out Matrix (2 Nodes)** | 36 runs across TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 on `GCP_NATIVE`, `GCP_CAPPED_100G`, `GCP_CAPPED_20G` |
| ├── `vllm_open_loop/` | **Poisson Arrival Rate Sweeps** | 15 runs: 8K and 128K offered RPS sweeps to identify queue latency capacity knees |
| ├── `hardware_processed/` | **Hardware & Fabric Characterization** | BabelStream (1,716 GB/s), NVBandwidth, iperf (173.58 Gbps), NCCL SendRecv, collective sweeps |
| └── `profiles_multi_node_native/` | **Nsight & PyTorch Profiler Traces** | 14 captured distributed Nsight traces + 6 single-node + 2 PyTorch operator traces |
| [`RUNS_INDEX.json`](file:///./RUNS_INDEX.json) | **Machine-Readable Runs Index** | Complete structured index of all 126 test points with metrics and relative file paths |

---

## 📊 Campaign Summary & Run Counts

* **Total Configured Scope:** 126 Cases
  * **95 Native/Local Completed Runs:**
    * 58 Single-Node V6 Base Runs (`SINGLE_NODE_LOCAL`)
    * 10 Single-Node V8 1M Extensions (`SINGLE_NODE_LOCAL`)
    * 12 Native Scale-Out Runs (`GCP_NATIVE`: 4 topologies × 3 contexts)
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

## 🖥 Production V4 Dashboard

The interactive decision-intelligence dashboard generated directly from this dataset is located at:
* [`dashboards/v4_dashboard/index.html`](file:///./dashboards/v4_dashboard/index.html)
* [`dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///./dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html)

