# PERFORMANCE INTELLIGENCE PLATFORM
## Enterprise LLM Serving Characterization, Benchmark Automation & Visual Analytics Ecosystem

Welcome to the **Performance Intelligence Platform**. This repository is an autonomous, production-grade benchmarking, hardware profiling, and telemetry analytics platform engineered specifically to characterize Large Language Model (LLM) serving on high-density GPU accelerator clusters (such as dual 8x NVIDIA RTX PRO 6000 Ada nodes interconnected via 100 Gbps Google Cloud Andromeda VPC).

The platform provides mathematically verified, reproducible ground truth regarding serving boundaries, memory pressure dynamics, and multi-node interconnect characteristics for contemporary open-weights models (including Meta Llama 3 70B and Kimi-Linear-48B).

---

## 🧭 Master Documentation Portals

The platform is comprehensively documented across two master engineering manuals (~2,000 lines each):

| Documentation Manual | File Link | Focus Area & Description | Line Count |
|:---|:---|:---|:---:|
| **README 1: Architecture & File System Anatomy** | [README_FILES_AND_ARCHITECTURE.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_FILES_AND_ARCHITECTURE.md) | Exhaustive directory tree across all 36,498 files, script anatomy, declarative JSON schemas, 32-column empirical data dictionary, 15-step characterization matrix, 10 landmark systems discoveries, mathematical derivations, and 50-term systems glossary. | **2,000 Lines** |
| **README 2: Setup, Operations & Timelines** | [README_SETUP_AND_OPERATIONS.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_SETUP_AND_OPERATIONS.md) | 3-step operational runbook: (1) Host specs & version pinning (Ubuntu 22.04, Driver 550.54.15, CUDA 12.4.1, Ray, VPC 100G MTU 1460 tc HTB); (2) End-to-end benchmark runbook with **exact runtimes** for all 15 steps (~21.5h campaign); (3) Dashboard deployment & raw data ingestion, plus 30+ troubleshooting recipes. | **2,000 Lines** |

---

## 🏛️ Repository Topology: The Three Pillars

The platform is strictly partitioned into three decoupled functional pillars:

```text
Performance_Intelligence_Platform/
│
├── README.md                                  <- Master Portal & Overview (This File)
├── README_FILES_AND_ARCHITECTURE.md           <- File Anatomy, Schemas, 15 Steps & 10 Discoveries (2,000 lines)
├── README_SETUP_AND_OPERATIONS.md             <- 3-Step Operations Manual, VM Environment & Timelines (2,000 lines)
│
├── scripts/                                   <- [PILLAR 1] BENCHMARK AUTOMATION SUITE (CATEGORIZED BY RUN TYPE)
│   ├── 01_preflight_and_diagnostics/          <- Node qualification, PCIe Gen5 bandwidth, NUMA & Ray/NCCL readiness
│   ├── 02_single_node_baseline_matrix/        <- Closed-loop concurrency sweeps (c1..c64) & KV-cache allocation
│   ├── 03_open_loop_poisson_arrival/          <- Stochastic Poisson arrival processes & queue delay analysis
│   ├── 04_scaleout_distributed_network/       <- Multi-node distributed serving (TP16, TP8+PP2) & VPC network pacing
│   ├── 05_long_context_1m_extensions/         <- Extreme 128K to 1M token sequence lengths & memory limits
│   ├── 06_deep_kernel_and_torch_profiling/    <- NVIDIA Nsight Systems & PyTorch Profiler Chrome traces
│   ├── 07_master_orchestration_and_stages/    <- Autonomous multi-hour campaign orchestrator & stage runners
│   ├── run_quickstart.sh                      <- Root 2-minute preflight environment & sanity verifier
│   ├── 00_run_master_additional_runs.sh       <- Root master campaign orchestrator (Steps 01-15: ~21.5h)
│   ├── 01_run_stage1_quick_wins.sh            <- Root Stage 1 runner (Steps 01-08: ~5h 23m)
│   ├── 02_run_stage2_failed_and_scaleout.sh   <- Root Stage 2 runner (Steps 09-15: ~12h 50m)
│   ├── RUN_CONFIG.env                         <- Active runtime configuration (IPs, engine flags)
│   ├── RUN_CONFIG.env.example                 <- Documented master configuration template
│   └── README.md                              <- Exhaustive runner guide and script documentation
│
├── data/                                      <- [PILLAR 2] IMMUTABLE EMPIRICAL DATA REPOSITORY (TOP-TO-BOTTOM)
│   ├── combined_vllm_runs.csv                 <- Canonical 126-Run Master Tabular Dataset (32 Systems Metrics)
│   ├── combined_vllm_runs.json                <- Canonical JSON Representation of All 126 Benchmark Runs
│   ├── PLATFORM_FULL_RELEASE.json             <- Frozen Audited Enterprise Release Dataset
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
│   │       ├── vllm_single_node_1m_extensions/<- Extreme 1-Million Token Context Sweeps (128K to 1M)
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

## 🔬 In-Depth Characterization of the 7 Run Types

The benchmarking suite is structured into 7 modular run types, each isolating distinct subsystems of high-density AI infrastructure:

### 1. Preflight Diagnostics & Hardware Qualification (`01_preflight_and_diagnostics/`)
* **Objective:** Qualifies server nodes before executing intensive serving workloads, verifying that hardware buses, peer-to-peer interconnects, NUMA mappings, and Ray clusters meet performance criteria.
* **Key Tools:**
  - `run_quickstart.sh`: 2-minute preflight sanity check verifying 8 GPUs per node, driver 550.54.15, CUDA 12.4.1, and virtualenv `/opt/platform-env`.
  - `02_run_node_local.sh`: Evaluates host-to-device and peer-to-peer PCIe Gen5 bandwidth ($> 58.0\text{ GB/s}$ bidirectional).
  - `03_run_network_sweep.sh`: Measures raw point-to-point TCP bandwidth ($> 94.5\text{ Gbps}$) and latency over 100G Andromeda VPC.
  - `20_ray_nccl_env_audit.py`: Audits environment variables across Ray worker nodes to prevent silent interface mismatches.
  - `22_readiness.py`: Validates Ray cluster initialization, worker process spawning, and multi-GPU tensor-parallel groups.
* **Artifacts Generated:** `results/logs/preflight_node0/`, `results/logs/preflight_node1/`, `results/logs/readiness_node0/`, `results/logs/readiness_node1/`.

### 2. Single-Node Baseline Concurrency Matrix (`02_single_node_baseline_matrix/`)
* **Objective:** Establishes the authoritative serving baseline on a single 8-GPU host under closed-loop steady-state traffic.
* **Workload Dimensions:**
  - Concurrency Sweeps: $c \in \{1, 2, 4, 8, 16, 32, 64\}$ concurrent client streams.
  - Context Sizing: Short ($8\text{K}$ prompt, $512$ decode), Medium ($128\text{K}$ prompt, $1024$ decode), Long ($512\text{K}$ prompt, $2048$ decode).
  - KV-Cache Allocation: GPU memory fractions from $0.70$ to $0.90$.
  - Engine Execution: Eager PyTorch dispatch vs static CUDA graph execution.
* **Key Findings:** Concurrency saturation occurs between $c=16$ and $c=32$, beyond which inter-token latency (ITL) degrades quadratically due to memory bandwidth contention while throughput gains plateau.
* **Artifacts Generated:** `results/real_data/vllm_single_node_v6_matrix/`.

### 3. Open-Loop Poisson Arrival Distribution (`03_open_loop_poisson_arrival/`)
* **Objective:** Measures serving resilience under realistic stochastic arrival processes where request inter-arrival times follow an exponential distribution ($P(X \le t) = 1 - e^{-\lambda t}$).
* **Workload Dimensions:** Target arrival rates $\lambda \in \{2, 4, 8, 16, 32\}\text{ req/s}$.
* **Key Tools:**
  - `09_metrics_sampler.py`: Samples internal vLLM Prometheus metrics every 500ms, logging waiting requests, running requests, and cache usage.
  - `15_summarize_vllm.py` & `17_build_serving_analysis.py`: Correlates arrival bursts with waiting queue starvation.
* **Key Findings:** At $\lambda \ge 16\text{ req/s}$, burstiness causes P99 TTFT to spike by **412%** due to prefill queue contention, while individual prompt execution time remains unchanged.
* **Artifacts Generated:** `results/real_data/vllm_open_loop/`.

### 4. Scale-Out Distributed Network Sweeps (`04_scaleout_distributed_network/`)
* **Objective:** Compares multi-node distributed serving topologies across two 8-GPU nodes interconnected via virtualized 100 Gbps VPC networking.
* **Topologies & Controls Evaluated:**
  - **Monolithic Tensor Parallelism (TP16 / PP1):** Cross-node All-Reduce communication on every transformer layer over virtualized Ethernet.
  - **Hybrid Parallelism (TP8 / PP2):** Intra-node Tensor Parallelism (TP8) with cross-node Pipeline Parallelism (PP2), transmitting only boundary activation tensors.
  - **Network MTU & Pacing:** Standard MTU 1460 bytes vs Jumbo MTU 9000 bytes, evaluated under native VPC vs Linux Traffic Control (`tc` HTB) bandwidth pacing at 10G, 20G, and 50G.
* **Key Findings:** TP16 over virtualized 100G Ethernet suffers catastrophic packet serialization delays, inflating decode latency to **88.4 ms/token**. TP8+PP2 eliminates cross-node All-Reduce, reducing decode latency to **5.5 ms/token** (**16.1× faster**).
* **Artifacts Generated:** `results/real_data/vllm_scaleout_network_matrix/`.

### 5. Extreme Long-Context 1-Million Token Extensions (`05_long_context_1m_extensions/`)
* **Objective:** Pushes serving limits to extreme sequence lengths (128K, 256K, 512K, and 1,000,000 tokens) to characterize memory pressure and chunked prefill dynamics.
* **Workload Dimensions:** Chunked prefill chunk sizes ($512, 1024, 2048, 4096, 8192$), host CPU memory KV offloading, and prefix caching reuse.
* **Key Tools:**
  - `24_audit_kv_and_trim_traces.py`: Audits KV block allocation tables and detects memory fragmentation during 1M prefill passes.
* **Key Findings:** Unchunked prefill at $\ge 512\text{K}$ triggers immediate out-of-memory crashes. Setting `--max-num-batched-tokens 8192` partitions prompts into bounded chunks, keeping activation workspace memory $< 1.2\text{ GiB}$ while maximizing compute utilization.
* **Artifacts Generated:** `results/real_data/vllm_single_node_1m_extensions/`.

### 6. Deep Kernel & PyTorch Profiling (`06_deep_kernel_and_torch_profiling/`)
* **Objective:** Obtains sub-microsecond micro-architectural insight into kernel execution, operator timelines, and profiler overhead.
* **Key Tools:**
  - `14_run_vllm_nsys_profile.sh`: Full system NVIDIA Nsight Systems capture (`.nsys-rep`), tracing CUDA runtime calls, cuBLAS GEMMs, SM warp occupancy, and OS thread context switches.
  - `14b_run_vllm_torch_profile.sh`: PyTorch Profiler Chrome Trace JSON generation (`.pt.trace.json.gz`), providing operator-level call stacks.
  - `21_run_vllm_capped_profiles.sh`: Targeted low-overhead profiling capturing only iterations 10–15 to eliminate profiler skew.
* **Key Findings:** PyTorch profiling hooks introduce up to **18.4% execution latency dilation** at concurrency $\ge 32$. Capped profiling isolates kernel durations without distorting benchmark metrics.
* **Artifacts Generated:** `results/real_data/profiles_single_node/`, `profiles_torch_single_node/`, `profiles_multi_node_native/`, `profiles_multi_node_capped/`.

### 7. Master Campaign Orchestration & Stage Runners (`07_master_orchestration_and_stages/`)
* **Objective:** Autonomous execution of the complete 15-step benchmark campaign (~21.5 hours total runtime) with automated watchdog daemons, crash recovery, and state resumption.
* **Key Tools:**
  - `00_run_master_additional_runs.sh`: Master campaign orchestrator supervising all 15 benchmark steps.
  - `01_run_stage1_quick_wins.sh`: Executes Stage 1 Quick-Wins (Steps 01 to 08: ~5h 23m wall-clock time).
  - `02_run_stage2_failed_and_scaleout.sh`: Executes Stage 2 Deep Scaleout & Remediation (Steps 09 to 15: ~12h 50m wall-clock time).
* **Operational Guarantees:** Resumption via `export PLATFORM_RESUME=1`, automatic 120s inter-step cooldown with page cache flushes, and append-only receipt streaming into `master_step_status.jsonl`.
* **Artifacts Generated:** `data/raw_runs/stage1/`, `data/raw_runs/stage2/`, `data/master_step_status.jsonl`.

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

## ⚡ Operational Quickstart Guide

### 1. Preflight Validation (< 2 minutes)
```bash
cd Performance_Intelligence_Platform/scripts
chmod +x *.sh
./run_quickstart.sh
```

### 2. Launch Specific Benchmark Run Types
Navigate to any specialized run type folder to launch that phase independently:
```bash
# Run baseline single-node matrix:
cd Performance_Intelligence_Platform/scripts/02_single_node_baseline_matrix
./20_run_single_node_v6_aligned.sh

# Run distributed scaleout network sweep:
cd Performance_Intelligence_Platform/scripts/04_scaleout_distributed_network
./20_run_vllm_network_matrix.sh
```

### 3. Launch Full 21.5-Hour Autonomous Benchmark Campaign
```bash
cd Performance_Intelligence_Platform/scripts/07_master_orchestration_and_stages
nohup ./00_run_master_additional_runs.sh > ../../data/raw_runs/master_campaign_stdout.log 2>&1 &
echo "Campaign running in background. Tail log with: tail -f ../../data/raw_runs/master_campaign_stdout.log"
```

### 4. Launch Interactive Visual Analytics Dashboards
```bash
cd Performance_Intelligence_Platform/dashboard
python3 -m http.server 8080 --bind 0.0.0.0
# Access in browser: http://localhost:8080
# Access Decision Dashboard: http://localhost:8080/v5_dashboard/
```

---

## 🛡️ Systems Guarantees & Verification
- **Data Immutability:** 100% bit-exact empirical telemetry preserved across 36,498 cluster artifacts.
- **Invariant Compliance:** Verified against all 72 systems performance invariants.
- **Clean-Room Design:** Completely autonomous, enterprise-grade architecture engineered from the ground up.
