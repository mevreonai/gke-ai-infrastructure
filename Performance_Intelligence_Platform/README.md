# PERFORMANCE INTELLIGENCE PLATFORM
## High-Density GPU Serving Characterization, Benchmark Automation & Systems Verification

Welcome to the **Performance Intelligence Platform**. This repository is an autonomous, production-grade benchmarking, hardware profiling, and telemetry characterization platform engineered specifically to evaluate Large Language Model (LLM) serving on high-density GPU accelerator clusters (such as dual 8x NVIDIA Blackwell / RTX PRO 6000 Ada nodes interconnected via 100 Gbps Google Cloud Andromeda VPC).

The platform provides mathematically verified, reproducible ground truth regarding serving boundaries, memory pressure dynamics, kernel bottlenecks, continuous batching step budgets, and multi-node interconnect characteristics.

> [!NOTE]
> **Pure Execution & Automation Platform:** This repository contains the executable benchmark suite, hardware profilers, automated sanity smoke tests, continuous batching engines, and canonical raw telemetry datasets. Visual presentation dashboards are retained exclusively in dedicated analytics artifacts (`v8_full_results/dashboards/v4_dashboard/`).

---

## 🧭 Master Documentation & Runbooks

| Manual / Guide | File Link | Focus Area & Description |
|:---|:---|:---|
| **Run Coverage Matrix** | [`RUN_COVERAGE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/RUN_COVERAGE.md) | **Comprehensive coverage reference:** All 20 steps, 4 run profiles, profiling tools, concurrency grid ($c=1..64$), context lengths ($1K..1M$), cold/warm cache isolation methodology. |
| **Master Results & Benchmarks Compendium** | [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md) | **Exhaustive empirical results:** TTFT, TPOT, throughput, continuous batching blocks 1–7, step-cost linear fits, wave & stall telemetry, 1M context limits, and NUMA deltas. |
| **Scripts & Configuration Guide** | [`SCRIPTS_AND_RESULTS_GUIDE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/SCRIPTS_AND_RESULTS_GUIDE.md) | **Script-by-script operations:** How to configure `RUN_CONFIG.env` or CLI flags, select specific topologies/stages, and what exact files and metrics are written. |
| **Operations Runbook (New VM Setup)** | [`RUNBOOK_NEW_VM_SETUP.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/RUNBOOK_NEW_VM_SETUP.md) | Step-by-step instructions from taking a fresh GCP VM, installing CUDA/PyTorch/vLLM, running the smoke test, and executing benchmarks. |
| **Setup & Operations Manual** | [`README_SETUP_AND_OPERATIONS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_SETUP_AND_OPERATIONS.md) | Exhaustive systems operations: host specs, NUMA pinning, Ray cluster orchestration, 100G VPC traffic control, and troubleshooting. |
| **Architecture & File Anatomy** | [`README_FILES_AND_ARCHITECTURE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_FILES_AND_ARCHITECTURE.md) | Script anatomy, declarative JSON schemas, empirical telemetry data dictionary, and 20-step characterization matrix. |
| **Execution Scripts Guide** | [`scripts/README.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/README.md) | Command-line options, flag syntax, environment variables, and module documentation. |

---

## ⏱️ Comprehensive Execution Timelines & Run Profiles

The unified benchmark runner consolidates all systems characterization into reproducible workflows with zero skips or failures.

### Execution Profiles

| Profile | CLI Flag | Approx. Duration | Steps Executed | Primary Objective |
|:---|:---|:---:|:---:|:---|
| **Smoke** | `--profile smoke` | **~10 min** | Steps 00–01 (TP4 1k/8k c=1 only) | Quick sanity check on cluster hardware & serving stack |
| **Fast Dashboard** | `--profile fast-dashboard` | **~2h** | Steps 00–13 (Stage 1 + 2) | Minimum dataset required to populate the characterization dashboard |
| **Default** | `--profile default` (or `--all`) | **~9h** | Steps 00–17 (All Standard Stages) | Full characterization with strict cold/warm cache isolation |
| **Deep Profile** | `--profile deep-profile` | **~14h** | Steps 00–20 (All + Deep Sweeps) | V8 parity: adds Poisson RPS sweeps, scheduler sensitivity, observer overhead, heavy Nsys |

### Step-by-Step Breakdown

| Stage / Component | Steps Included | Key Workloads & Focus Areas | Wall-Clock Estimate |
|:---|:---|:---|:---:|
| **Sanity Smoke Test** | Checks 1 – 10 | Toolchain, PyTorch/vLLM stack, Cutlass MoE flags, Cases JSON, Linux utils, Wave trimming, Synthetic benchmark, Master runner dry-run | **~3 – 5 min** |
| **Stage 1: Quick Wins & Baselines** | Steps 00 – 07 | 8.4K chunk budget A/B test, PyTorch batched profiles (c8, c32), NCCL socket tuning, TP8 host NUMA pinning, Sub-8K short prompts, 128K context knee repeats, R1 continuous context curve, KV pool audit | **~1h 10m** |
| **Stage 2: Scale-Out Concurrency** | Steps 08 – 13 | FP8 quantization evaluation, DDR5 CPU offload reuse, R2 agentic decay, Multi-node concurrency under load (c=1..8 across TP16, TP8+PP2, TP4+PP4), 15/12 asymmetric PP split A/B evaluation against default, R3 network resilience (Native, 100G, 20G, 0.05% loss), TP16 512K context serving | **~3h 30m** |
| **Stage 3: Deep Profiling & Sweeps** | Steps 14 – 17 | B1 CUDA Graphs-ON Nsight Systems decode trace (~4.47ms target), Single-node Nsys trace, PyTorch Chrome batched traces, B11 multi-node decode trace, Canonical telemetry compilation & 72-rule invariant audit, Waves & stalls audit, Continuous Batching Blocks 1–7 | **~4h 15m** |
| **Stage 3 Deep Extensions** | Steps 18 – 20 | Step 18: Open-Loop Poisson Arrival Rate Sweep (RPS=1,2,4,8,∞), Step 19: Scheduler `max_num_seqs` Sensitivity (8, 16, 64, 128), Step 20: Observability Overhead Test (Minimal vs Full Prometheus) | **~1h 10m** |
| **Total Full Campaign (Default)** | **Steps 00 – 17** | **Standard production characterization across single-node and multi-node** | **~8h 55m** |
| **Total Deep Profile Campaign** | **Steps 00 – 20** | **Complete V8 parity with all deep sweeps and heavy profiler traces** | **~14h 00m** |

---

## ⚙️ Dynamic Execution Flags & Options

The master benchmark runner (`scripts/run_master_benchmark.sh`) and smoke test (`scripts/run_smoke_test.sh`) dynamically support model, topology, bandwidth, and stage selection:

```bash
bash scripts/run_master_benchmark.sh [OPTIONS]
```

### Supported CLI Flags

* `--profile <name>`: Select a predefined run profile:
  - `smoke`: Quick ~10 min sanity check (TP4 1k/8k $c=1$ only)
  - `fast-dashboard`: ~2h fast build (Stages 1+2, minimum dataset for dashboard)
  - `default`: ~9h full characterization across all topologies and contexts (Steps 00–17)
  - `deep-profile`: ~14h exhaustive V8-parity deep characterization (Steps 00–20)
* `--model <hf_id_or_path>`: Target HuggingFace model or local path (Default: `moonshotai/Kimi-Linear-48B-A3B-Instruct`).
* `--revision <git_sha>`: Exact model commit hash for provenance verification.
* `--stage <1|2|3|all>`: Filter execution to a specific characterization stage:
  - `1`: Stage 1 Quick Wins & Single-Node (Steps 1–7: ~1h 10m)
  - `2`: Stage 2 Scale-Out Concurrency & Asymmetric PP (Steps 8–13: ~3h 30m)
  - `3`: Stage 3 Deep Profiling & Continuous Batching (Steps 14–17: ~4h 15m; Steps 14–20 with deep extensions)
  - `all`: Full campaign (Steps 00–17 default, or 00–20 with deep-profile)
* `--topologies <list|all>`: Comma-separated list of target topologies to execute:
  - `tp4_pp1`: Single-node 4-GPU baseline
  - `tp8_pp1`: Single-node 8-GPU baseline (NUMA pinning, continuous context)
  - `tp4_pp2`: Dual-node 8-GPU pipeline parallel configuration
  - `tp8_pp2`: Dual-node 16-GPU scale-out (15/12 asymmetric partition)
  - `tp4_pp4`: Dual-node 16-GPU deep pipeline parallel configuration
  - `tp16_pp1`: Dual-node 16-GPU distributed tensor parallel configuration
  - `all`: Runs all topologies defined in the cases manifest
* `--contexts <list|all>`: Comma-separated list of context lengths (e.g. `1k,8k,128k,512k,1m` or `all`).
* `--concurrencies <list|all>`: Comma-separated list of concurrencies (e.g. `1,2,4,8,16,32` or `all`).
* `--bandwidth <list|all>`: Comma-separated list of network modes for Step 12 resilience testing:
  - `native`: Uncapped GCP Andromeda VPC (100 Gbps line rate)
  - `100g`: Shaped 100 Gbps via Linux `tc` HTB
  - `20g`: Shaped 20 Gbps via Linux `tc` HTB
  - `impaired`: Synthetic 0.05% packet loss + 0.2ms jitter via Linux `tc` netem
  - `all`: Tests all four network states sequentially
* `--continuous-batching` (`-cb`): Executes Step 17 continuous batching characterization suite.
* `--cb-blocks <list|all>`: Selects specific continuous batching blocks (e.g. `1,2,4` or `all`).
* `--dry-run`: Validates all script workflows, flags, argument parsing, directory creations, and environment setups without launching heavy GPU workloads.
* `--step <N>`: Executes a single target step (0 to 20).
* `--from-step <N>`: Resumes execution starting at step N.
* `--new-run`: Generates a fresh run directory without reading previous resume markers.

---

## 🧊 Cold vs. Warm Cache Isolation Methodology

In production LLM serving systems, prefix caching (e.g., vLLM's automatic prefix caching) can introduce substantial measurement bias: if multiple concurrency levels or prompt lengths are benchmarked against the same long-running `vllm serve` instance, subsequent requests reuse KV blocks from earlier requests, creating artificially low Time-To-First-Token (TTFT) readings (e.g., showing <15 ms when true cold TTFT is >1.2 s).

To eliminate this bias, PIP v2.0 enforces **Strict Cold/Warm Cache Isolation**:

1. **Process-Level Server Restart:** Between each concurrency level within a benchmark case, the `vllm serve` process (and any lingering Ray workers) is cleanly terminated (`SIGTERM` followed by `pkill -9`).
2. **VRAM Drain Barrier:** A post-kill VRAM drain barrier waits for all GPU memory allocations to drop to zero and releases OS file descriptors.
3. **Fresh vLLM Boot:** The server is booted afresh for each concurrency level, ensuring a completely empty KV cache pool.
4. **Explicit Cold vs. Warm Separation:**
   - **Cold Pass:** Conducted on the fresh server instance with 0 prefix cache hits. Reflects real-world initial request latency.
   - **Warm Pass:** Conducted with controlled prefix cache warming passes to evaluate multi-turn prefix caching dynamics (e.g., in Step 09 R2 agentic decay).
   - **Metrics Attribution:** Every result JSON payload explicitly stamps `cache_state: "cold"` or `cache_state: "warm"` in its metadata ledger.

---

## 🛡️ Cutlass & Triton MoE Kernel Execution Invariants

To guarantee deterministic kernel performance and avoid Triton JIT compilation hangs or PCIe bus inversions, the following environment invariants are strictly enforced across all runner scripts:

```bash
# 1. Enforce physical PCI bus order mapping
export CUDA_DEVICE_ORDER="PCI_BUS_ID"

# 2. FlashInfer CUTLASS MoE Kernel Backend (~29% faster on Blackwell/Ada; use 'triton' for A/B tests)
export VLLM_MOE_BACKEND="flashinfer_cutlass"
export MOE_BACKEND="flashinfer_cutlass"

# 3. FlashInfer JIT Autotuning
export VLLM_FLASHINFER_AUTOTUNE="1"

# 4. Critical FlashInfer Skip-Ops (Prevents 30-min TRTLLM MoE Warmup Hang)
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"

# 5. Pipeline Parallel Layer Partition (Left unset so vLLM native defaults apply: 14/13 PP2, 7/7/7/6 PP4)
unset VLLM_PP_LAYER_PARTITION 2>/dev/null || true

# 6. NCCL Inter-Node Transport Tuning (Stage 1/Stage 2 clean isolation)
export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export NCCL_SOCKET_IFNAME="ens3"
export NCCL_NET="Socket"
export NCCL_BUFFSIZE="4194304"
export GLOO_SOCKET_IFNAME="ens3"
unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL 2>/dev/null || true
# NCCL_CROSS_NIC dropped (single NIC on Blackwell VM)
```

---

## 🏛️ Repository Topology

```text
Performance_Intelligence_Platform/
├── README.md                                  <- Master Platform Overview & Timelines (This File)
├── RUN_COVERAGE.md                            <- Comprehensive Run Coverage Reference Matrix (All 20 Steps)
├── PIP_MASTER_RESULTS_AND_BENCHMARKS.md       <- Definitive Ground-Truth Benchmark Results Compendium
├── SCRIPTS_AND_RESULTS_GUIDE.md               <- Script-by-Script Operations & Results Manual
├── RUNBOOK_NEW_VM_SETUP.md                    <- Complete End-to-End Runbook for Fresh VM Provisioning
├── README_FILES_AND_ARCHITECTURE.md           <- In-Depth Script & Data Architecture Manual
├── README_SETUP_AND_OPERATIONS.md             <- Cluster Setup & Systems Operations Manual
│
├── scripts/                                   <- EXECUTABLE BENCHMARK AUTOMATION SUITE
│   ├── run_smoke_test.sh                      <- 10-Check Automated Sanity Smoke Test (~3-5 min)
│   ├── run_master_benchmark.sh               <- Unified Master Benchmark Runner (Steps 00-20, 4 Profiles)
│   ├── run_continuous_batching.sh / .py      <- Continuous Batching Suite Runner (Blocks 1-7)
│   ├── pip_waves.py                           <- Request Wave Decomposition & Stall Reference Tool
│   ├── pip_scan.py                            <- Recursive Directory Pause & Stall Scanner
│   ├── pip_timeline.py                        <- Publication-Quality Timeline Diagram Plotter
│   ├── pip_step_cost.py                       <- Continuous Batching Step-Cost Linear Model Fitter
│   ├── pip_mixed_traffic.py                   <- Short + Long Concurrent Stream Interference Analyzer
│   ├── ttft_waves.py                          <- First-Wave TTFT Decomposition & Burst Analyzer
│   ├── bench_summary.py                       <- Aggregator with Pause & Stall Indicators
│   ├── generate_result_summary.py             <- Markdown Report Generator for Benchmark Runs
│   ├── master_benchmark_cases.json           <- Declarative Cases Manifest across All Topologies
│   ├── continuous_batching_cases.json         <- Case Manifest for Continuous Batching Sweeps
│   ├── expected_values.json                   <- Cryptographic Ground-Truth Fixtures & Reference Numbers
│   ├── RUN_CONFIG.env                         <- Active Runtime Configuration (IPs, Engine Flags)
│   ├── RUN_CONFIG.env.example                 <- Documented Configuration Template
│   ├── 01_preflight_and_diagnostics/          <- Node Qualification & PCIe/Interconnect Diagnostics
│   ├── 02_single_node_baseline_matrix/        <- Single-Node Surrogate Runners & Concurrency Sweeps
│   ├── 03_open_loop_poisson_arrival/          <- Poisson Arrival Process Benchmark
│   ├── 04_scaleout_distributed_network/       <- Multi-Node Ray/NCCL Serving (TP16, TP8+PP2) & VPC Shaping
│   ├── 05_long_context_1m_extensions/         <- Extreme Context Sweeps & KV Cache Trace Trimming
│   ├── 06_deep_kernel_and_torch_profiling/    <- Nsight Systems & PyTorch Profiler Chrome Trace Captures
│   └── 07_master_campaign_orchestration/      <- Orchestration Helpers & Invariant Audit Scripts
│
└── data/                                      <- CANONICAL EMPIRICAL TELEMETRY REPOSITORY
    ├── README.md                              <- Telemetry Repository Manual & Schema
    ├── raw_runs/                              <- Raw Execution Trees and Case Logs
    └── results/                               <- Multi-Phase Characterization Traces & Archive Vaults
```

---

## 🚀 Quickstart: Running on a Fresh VM

```bash
# 1. Navigate to platform scripts directory
cd ~/Performance_Intelligence_Platform/scripts

# 2. Configure cluster IPs and selections
cp RUN_CONFIG.env.example RUN_CONFIG.env
nano RUN_CONFIG.env

# 3. Execute Automated Smoke Test (~3-5 min)
bash run_smoke_test.sh

# 4. Launch Benchmark via Profiles:
# Dry run verification:
bash run_master_benchmark.sh --dry-run

# Smoke Profile (~10 min): TP4 1k/8k c=1 sanity check
bash run_master_benchmark.sh --profile smoke

# Fast Dashboard Profile (~2h): Stage 1+2 data for dashboard
bash run_master_benchmark.sh --profile fast-dashboard

# Default Full Campaign (~9h): Steps 00-17 with cold/warm cache isolation
bash run_master_benchmark.sh --profile default
# (or simply: bash run_master_benchmark.sh --all)

# Deep Profile (~14h): Steps 00-20 with Poisson, scheduler sweeps, and observer overhead
bash run_master_benchmark.sh --profile deep-profile
```
