# PERFORMANCE INTELLIGENCE PLATFORM
## Enterprise Platform LLM Serving Characterization, Benchmark Automation & Visual Analytics Ecosystem

Welcome to the **Performance Intelligence Platform**. This repository is an autonomous, production-grade benchmarking, hardware profiling, and telemetry analytics platform engineered specifically to characterize Large Language Model (LLM) serving on high-density GPU accelerator clusters.

---

## 🧭 Master Documentation Portals

The platform is comprehensively documented across two master manuals (~2,000 lines each):

| Documentation Manual | File Link | Focus Area & Description | Line Count |
|:---|:---|:---|:---:|
| **README 1: Architecture & File System Anatomy** | [README_FILES_AND_ARCHITECTURE.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_FILES_AND_ARCHITECTURE.md) | Exhaustive directory tree, script anatomy, declarative JSON schemas, 32-column empirical data dictionary, 15-step characterization matrix, 10 landmark systems discoveries, mathematical derivations, and 50-term systems glossary. | **1,995 Lines** |
| **README 2: Setup, Operations & Timelines** | [README_SETUP_AND_OPERATIONS.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_SETUP_AND_OPERATIONS.md) | 3-step operational runbook: (1) Host specs & version pinning (Ubuntu 22.04, Driver 550.54.15, CUDA 12.4.1, Ray, VPC 100G MTU 1460 tc HTB); (2) End-to-end benchmark runbook with **exact runtimes** for all 15 steps (~21.5h campaign); (3) Dashboard deployment & raw data ingestion, plus 30+ troubleshooting recipes. | **1,997 Lines** |

---

## 🏛️ Repository Topology: The Three Pillars

The platform is strictly partitioned into three decoupled functional directories:

```text
Performance_Intelligence_Platform/
│
├── README.md                                  <- Master Portal & Overview (This File)
├── README_FILES_AND_ARCHITECTURE.md           <- File Anatomy, Schemas, 15 Steps & 10 Discoveries (~2,000 lines)
├── README_SETUP_AND_OPERATIONS.md             <- 3-Step Operations Manual, VM Environment & Timelines (~2,000 lines)
│
├── scripts/                                   <- [PILLAR 1] BENCHMARK AUTOMATION SUITE
│   ├── 00_run_master_additional_runs.sh       <- Master Campaign Orchestrator, Watchdog & Resumption (`PLATFORM_RESUME=1`)
│   ├── 01_run_stage1_quick_wins.sh            <- Stage 1 Benchmark Runner (Steps 1 to 8: ~5h 23m)
│   ├── 02_run_stage2_failed_and_scaleout.sh   <- Stage 2 Benchmark Runner (Steps 9 to 15: ~12h 50m)
│   ├── run_quickstart.sh                      <- 2-Minute Preflight Environment & Smoke Verifier
│   ├── RUN_CONFIG.env                         <- Active Runtime Configuration, IPs & Engine Flags
│   ├── RUN_CONFIG.env.example                 <- Documented Master Configuration Template
│   ├── stage1_cases.json                      <- Workload Manifest for Stage 1 (Steps 1 to 8)
│   ├── stage2_cases_multi_node_load.json      <- Distributed Multi-Node Workload Manifest (TP16, PP2)
│   ├── stage2_cases_single_node.json          <- Extreme Concurrency Single-Node Manifest (1M Stress)
│   ├── rtx_g4_smoke_v5/                       <- Legacy Qualification Smoke Test Suite
│   └── rtx_g4_hardware_diagnostics/                    <- Hardware Diagnostics Suite platform (PCIe Gen5, NUMA, NCCL, NVML)
│
├── data/                                      <- [PILLAR 2] IMMUTABLE EMPIRICAL DATA REPOSITORY (TOP-TO-BOTTOM)
│   ├── combined_vllm_runs.csv                 <- Canonical 126-Run Master Tabular Dataset (32 Systems Metrics)
│   ├── combined_vllm_runs.json                <- Canonical JSON Representation of All 126 Benchmark Runs
│   ├── PLATFORM_FULL_RELEASE.json                   <- Frozen Audited Enterprise Platform Release Dataset
│   ├── RUNS_INDEX.json                        <- Master JSON Registry of All 15+ Characterization Phases
│   ├── master_step_status.jsonl               <- Real-Time Line-Delimited Telemetry Stream of Master Execution
│   ├── release_specs/                         <- Hardware, Network & Software Bill of Materials (SBOM) & Audit Specs
│   ├── results/                               <- Complete Multi-Phase Characterization Data & Trace Archives
│   │   ├── logs/                              <- Preflight & Readiness Microbenchmarks
│   │   │   ├── preflight_node0/ & node1/      <- Hardware p2p, PCIe Gen5, NUMA & microbenchmark logs
│   │   │   └── readiness_node0/ & node1/      <- Ray cluster qualification & health telemetry
│   │   └── real_data/                         <- Historical Baseline Suites, Profiles & Telemetry Vaults
│   │       ├── vllm_single_node_v6_matrix/    <- Baseline Matrix (c1 to c64 concurrency, KV-cache, CUDA graphs)
│   │       ├── vllm_open_loop/                <- Open-Loop Poisson Arrival Distribution & Queuing Delays
│   │       ├── vllm_scaleout_network_matrix/  <- Inter-Node Scaling (TP16, TP8+PP2, VPC 100G MTU 1460/9000, tc HTB)
│   │       ├── vllm_single_node_1m_extensions/ <- Extreme 1-Million Token Context Sweeps (128K to 1M)
│   │       ├── profiles_single_node/          <- Nsight Systems Kernel Traces (.nsys-rep / .qdrep)
│   │       ├── profiles_torch_single_node/    <- PyTorch Profiler Chrome Trace JSONs (Operator Call Stacks)
│   │       ├── profiles_multi_node_native/    <- Distributed Multi-Node Ray & NCCL Native Profiling Traces
│   │       ├── profiles_multi_node_capped/    <- Distributed Multi-Node Traces under Network Capping & HTB Shaping
│   │       ├── hardware_raw/                  <- 100ms NVML GPU Telemetry (Watts, Temps, Clocks, PCIe Throughput)
│   │       ├── hardware_processed/            <- Processed MFU, TFLOPS & Hardware Efficiency Metrics
│   │       └── final_validation/              <- Master Canonical Release Dataset & Static Integrity JSONs
│   └── raw_runs/                              <- Additional Master Execution Logs & Evidence Trees
│       ├── stage1/                            <- Master Additional Steps 01 to 08 Raw Execution Trees
│       ├── stage2/                            <- Master Additional Steps 09 to 15 Raw Execution Trees
│       ├── logs/                              <- Supervisory Watchdog & Campaign stdout/stderr Logs
│       └── env/                               <- Cluster Environment, Driver, CUDA & OS Dumps
│
└── dashboard/                                 <- [PILLAR 3] CLIENT-SIDE VISUAL ANALYTICS ENGINE
    ├── MASTER_CHARACTERIZATION_DASHBOARD.html <- Standalone Master Interactive Visual Analytics UI (Offline v4)
    ├── DASHBOARD_CANONICAL_DATA.json          <- Canonical Processed JSON Driving the Dashboard UI
    ├── chart.umd.js                           <- Vendored Offline Chart.js v4.4.1 Engine
    ├── index.html                             <- Fast Landing Entrypoint & Redirection Page
    ├── time_budget/                           <- High-Resolution Wall-Time Budget Charts & CSVs
    └── v5_dashboard/                          <- Master Decision Dashboard V5 Extension
        ├── MASTER_DECISION_DASHBOARD_V5.html  <- Enterprise Decision Matrix & Executive Dashboard v5
        └── index.html                         <- V5 Web Server Landing Page
```

---

## ⚡ Quickstart Execution

### 1. Preflight Validation (< 2 minutes)
```bash
cd Performance_Intelligence_Platform/scripts
chmod +x *.sh
./run_quickstart.sh
```

### 2. Launch Full 21.5-Hour Benchmark Campaign
```bash
cd Performance_Intelligence_Platform/scripts
nohup ./00_run_master_additional_runs.sh > ../data/raw_runs/master_campaign_stdout.log 2>&1 &
echo "Campaign launched in background. Tail logs with: tail -f ../data/raw_runs/master_campaign_stdout.log"
```

### 3. Launch Interactive Visual Analytics Dashboard
```bash
cd Performance_Intelligence_Platform/dashboard
python3 -m http.server 8080 --bind 0.0.0.0
# Navigate to http://localhost:8080 in your web browser
```

---

## 📊 Summary of Master Benchmark Campaign Timelines

| Phase / Step | Name & Focus Area | Exact Wall-Clock Duration | Cumulative Time |
|:---|:---|:---:|:---:|
| **Phase 0–2** | Preflight, Microbenchmarks & Engine Qualification | **01h 20m 00s** | 01h 20m 00s |
| **Step 01** | Chunked Prefill Sizing (512 vs 2048) | **00h 40m 07s** | 02h 00m 07s |
| **Step 02** | PyTorch Profiler Overhead Dilation (c8/c32) | **01h 15m 18s** | 03h 15m 25s |
| **Step 03** | NCCL Intra-Node Communication Tuning | **00h 34m 42s** | 03h 50m 07s |
| **Step 04** | NUMA CPU Core & Memory Affinity | **00h 31m 10s** | 04h 21m 17s |
| **Step 05** | Short Prompt vs Long Decode Scaling | **00h 21m 05s** | 04h 42m 22s |
| **Step 06** | 128K Ultra-Long Context Chunked Prefill | **00h 44m 55s** | 05h 27m 17s |
| **Step 07** | KV-Cache Memory Trim Optimization | **00h 36m 20s** | 06h 03m 37s |
| **Step 08** | Automatic Prefix Caching Eviction Dynamics | **00h 39m 50s** | 06h 43m 27s |
| **Step 09** | FP8 Quantization Root Cause Analysis | **00h 28m 15s** | 07h 26m 42s |
| **Step 10** | Host CPU KV-Cache Offloading Latency | **00h 49m 40s** | 08h 16m 22s |
| **Step 11** | 1M Ultra-High Concurrency Stress Test | **02h 42m 10s** | 10h 58m 32s |
| **Step 12** | Pipeline Parallelism (PP 15/12) Rebalancing | **01h 28m 30s** | 12h 27m 02s |
| **Step 13** | Capped Profiling Runs (Low-Overhead) | **03h 16m 45s** | 15h 43m 47s |
| **Step 14** | Multi-Node TP16 512K Context Serving | **01h 44m 20s** | 17h 28m 07s |
| **Step 15** | Full Timeline Nsight Systems Traces | **02h 21m 15s** | 19h 49m 22s |
| **Phase 5** | Telemetry Aggregation & Invariant Audit | **00h 25m 00s** | 20h 14m 22s |
| **Cooldowns**| Inter-step quiescence & VRAM flushes | **01h 15m 00s** | **21h 29m 22s** |

---

*Refer to [README_FILES_AND_ARCHITECTURE.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_FILES_AND_ARCHITECTURE.md) and [README_SETUP_AND_OPERATIONS.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_SETUP_AND_OPERATIONS.md) for full engineering specifications.*
