# Performance Intelligence Platform — Benchmark Automation Suite
## Unified Master Execution, Kernel Characterization & Automated Smoke Test

Welcome to the **Benchmark Automation Suite** of the Performance Intelligence Platform. This folder contains all executable test scripts, case manifests, profiling harnesses, and orchestrator tools engineered to characterize Large Language Model (LLM) serving on high-density GPU accelerator clusters.

The automation suite is organized into **7 specialized sub-folders** categorized by the type of characterization run, alongside convenient top-level entrypoints and analytical post-processors:
* [`run_smoke_test.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/run_smoke_test.sh): 10-check automated sanity verifier (~3–5 minutes) ensuring all toolchains, MoE flags, schemas, and dry-run flows are qualified.
* [`run_master_benchmark.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/run_master_benchmark.sh): Unified master campaign orchestrator executing Steps 00–20 across 4 configurable run profiles.
* [`run_continuous_batching.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/run_continuous_batching.sh) / [`run_continuous_batching.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/run_continuous_batching.py): Configurable runner for Continuous Batching characterization (Blocks 1–7).
* Reference Guides:
  - [`RUN_COVERAGE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/RUN_COVERAGE.md): Comprehensive reference for all 20 steps, profiler tools, concurrency sweeps ($c=1..64$), context lengths ($1K..1M$), topologies, and cold/warm cache isolation.
  - [`SCRIPTS_AND_RESULTS_GUIDE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/SCRIPTS_AND_RESULTS_GUIDE.md): Exhaustive guide for all scripts, configuration selection options, and output artifacts.
  - [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md): Master empirical results table, model curves, and telemetry compendium.

---

## ⏱️ Wall-Clock Time Budgets & Execution Schedule

### Predefined Run Profiles

| Profile | CLI Flag | Approx. Duration | Steps Executed | Primary Objective |
|:---|:---|:---:|:---:|:---|
| **Smoke** | `--profile smoke` | **~10 min** | Steps 00–01 (TP4 1k/8k c=1 only) | Fast cluster hardware sanity check |
| **Fast Dashboard** | `--profile fast-dashboard` | **~2h** | Steps 00–13 (Stage 1 + 2) | Minimum dataset required to build the characterization dashboard |
| **Default** | `--profile default` (or `--all`) | **~9h** | Steps 00–17 (All Standard Stages) | Full characterization with strict cold/warm cache isolation |
| **Deep Profile** | `--profile deep-profile` | **~14h** | Steps 00–20 (All + Deep Sweeps) | V8 parity: adds Poisson RPS sweeps, scheduler sensitivity, observer overhead, heavy Nsys |

### Detailed Step Schedule

| Stage / Component | Steps Included | Key Workloads | Estimated Duration |
|:---|:---|:---|:---:|
| **Sanity Smoke Test** | Checks 1 – 10 | Toolchains, PyTorch/vLLM stack, Cutlass MoE flags, Cases JSON, Linux utils, Wave trimming, Synthetic micro-benchmark, Master runner dry-run | **~3 – 5 min** |
| **Stage 1: Quick Wins & Single-Node** | Steps 00 – 07 | 8.4K chunk budget A/B test, PyTorch batched profiles (c8, c32), NCCL socket tuning, TP8 host NUMA pinning, Sub-8K short prompts, 128K knee repeats, R1 continuous context curve, KV pool audit | **~1h 10m** |
| **Stage 2: Scale-Out Concurrency** | Steps 08 – 13 | FP8 quantization evaluation, DDR5 CPU offload reuse, R2 agentic decay, Multi-node concurrency under load (c=1..8 across TP16, TP8+PP2, TP4+PP4), 15/12 asymmetric PP split (+27.58% TTFT speedup), R3 network resilience (Native, 100G, 20G, 0.05% loss), TP16 512K context serving | **~3h 30m** |
| **Stage 3: Deep Profiling & Continuous Batching** | Steps 14 – 17 | B1 CUDA Graphs-ON Nsight Systems decode trace (~4.47ms target), Single-node Nsys trace, PyTorch Chrome batched traces, B11 multi-node decode trace, Canonical telemetry compilation & 72-rule invariant audit, Waves & stalls scan, Continuous Batching Blocks 1–7 | **~4h 15m** |
| **Stage 3 Deep Extensions** | Steps 18 – 20 | Step 18: Open-Loop Poisson Arrival Rate Sweep (RPS=1,2,4,8,∞), Step 19: Scheduler `max_num_seqs` Sensitivity (8, 16, 64, 128), Step 20: Observability Overhead Test (Minimal vs Full Prometheus) | **~1h 10m** |
| **Total Full Campaign (Default)** | **Steps 00 – 17** | **Standard production characterization across single-node and multi-node** | **~8h 55m** |
| **Total Deep Profile Campaign** | **Steps 00 – 20** | **Complete V8 parity with all deep sweeps and heavy profiler traces** | **~14h 00m** |

---

## 🚀 Root Runner Execution & Dynamic Flags

The master runner (`run_master_benchmark.sh`) and smoke test (`run_smoke_test.sh`) allow granular, dynamic selection of models, revisions, stages, topologies, bandwidth modes, and continuous batching blocks:

```bash
bash run_master_benchmark.sh [OPTIONS]
```

### Supported CLI Flags

* `--profile <name>`: Select a predefined run profile (`smoke`, `fast-dashboard`, `default`, `deep-profile`).
* `--model <id_or_path>`: Target model (Default: `moonshotai/Kimi-Linear-48B-A3B-Instruct`).
* `--revision <git_sha>`: Exact git revision for weights provenance.
* `--stage <1|2|3|all>`: Filter execution to specific stage:
  - `1`: Stage 1 Quick Wins & Single-Node (Steps 1–7: ~1h 10m)
  - `2`: Stage 2 Scale-Out Concurrency & Asymmetric PP (Steps 8–13: ~3h 30m)
  - `3`: Stage 3 Deep Profiling & Continuous Batching (Steps 14–17: ~4h 15m; Steps 14–20 with deep extensions)
  - `all`: Full campaign (Steps 00–17 default, or 00–20 with deep-profile)
* `--topologies <list|all>`: Filter topologies (e.g. `tp4_pp1,tp8_pp1,tp4_pp2,tp8_pp2,tp4_pp4,tp16_pp1`).
* `--contexts <list|all>`: Filter context lengths (e.g. `1k,8k,128k,512k,1m` or `all`).
* `--concurrencies <list|all>`: Filter concurrencies (e.g. `1,2,4,8,16,32` or `all`).
* `--bandwidth <list|all>`: Filter network bandwidth states for Step 12 (e.g. `native,100g,20g,impaired`).
* `--continuous-batching` (`-cb`): Executes Step 17 continuous batching characterization suite.
* `--cb-blocks <list|all>`: Selects specific continuous batching blocks (e.g. `1,2,4` or `all`).
* `--dry-run`: Validates all script workflows, commands, and schemas without launching GPU workloads.
* `--step <N>`: Executes a single target step (0 to 20).
* `--from-step <N>`: Resumes execution starting from step N.
* `--new-run`: Forces a clean run directory without reading resume markers.

---

## 🧊 Cold vs. Warm Cache Isolation Methodology

To prevent prefix caching bias from distorting TTFT and TPOT readings across different concurrency levels:
1. `vllm serve` and any remote Ray worker processes are terminated (`SIGTERM` + `pkill -9`) between concurrency sweeps.
2. A VRAM drain barrier confirms GPU memory allocations drop to 0 bytes and OS file descriptors are released.
3. A clean `vllm serve` instance is booted for each concurrency level, ensuring an unpopulated KV cache pool.
4. Measurements are tagged with explicit `cache_state: "cold"` or `cache_state: "warm"` metadata in the JSON output ledger.

---

## 🛠️ Standalone Analytical & Telemetry Tools

The platform provides a suite of high-precision analytical tools that operate on benchmark logs and JSON result files:

| Script | Purpose | Usage Example |
|:---|:---|:---|
| [`pip_waves.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/pip_waves.py) | Analyzes detailed request timings; extracts lone read $R$, first-wave spacing, stalls (>100ms), and decode pauses ($\ge 3$ normal steps). | `python3 pip_waves.py <run.json> [--budget 8192]` |
| [`pip_scan.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/pip_scan.py) | Recursively scans result directories for pauses, stalls, and burst fractions; outputs CSV/JSON summaries. | `python3 pip_scan.py <dir> --csv scan.csv` |
| [`pip_timeline.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/pip_timeline.py) | Generates publication-quality timeline diagrams showing prompt reading (red), answer writing (blue), stalls, and pauses. | `python3 pip_timeline.py <run.json> --out timeline.png` |
| [`pip_step_cost.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/pip_step_cost.py) | Fits the continuous batching step-cost linear model ($T \approx a + b\cdot gen + c\cdot ctx$) from `server.log`. | `python3 pip_step_cost.py <server.log> --json fit.json` |
| [`pip_mixed_traffic.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/pip_mixed_traffic.py) | Evaluates interference between concurrent short streams (1K) and long streams (128K); computes TTFT penalty ratio. | `python3 pip_mixed_traffic.py --short s.json --long l.json` |
| [`ttft_waves.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/ttft_waves.py) | Decomposes the first wave of requests, comparing measured waiting times to the theoretical $(C+1)/2$ rule. | `python3 ttft_waves.py <run.json>` |
| [`bench_summary.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/bench_summary.py) | Command-line aggregator that prints clean tables summarizing TTFT, TPOT, throughput, pause indicators, and max token gaps. | `python3 bench_summary.py <run.json or dir>` |
| [`generate_result_summary.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/generate_result_summary.py) | Generates `RESULT_SUMMARY.md` and per-block Markdown reports from continuous batching manifests. | `python3 generate_result_summary.py <out_dir>` |
| [`server_log.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/server_log.py) | Parses microsecond timestamped server logs; extracts logs 2s before to 1s after any detected pause to identify root cause. | `python3 server_log.py <server.log> --run <run.json>` |
| [`metrics_diff.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/metrics_diff.py) | Validates Prometheus scrapes (`metrics_node0.jsonl`) against client request timelines; verifies queue gauges. | `python3 metrics_diff.py <metrics.jsonl> --run <run.json>` |

---

## 🛡️ Cutlass & Triton MoE Kernel Execution Invariants

The runner strictly exports and enforces the following kernel execution invariants across all local and remote worker processes:

```bash
# 1. Enforce physical PCI bus order mapping
export CUDA_DEVICE_ORDER="PCI_BUS_ID"

# 2. Triton Cutlass MoE Kernel Backend
export VLLM_MOE_BACKEND="triton"

# 3. FlashInfer JIT Autotuning
export VLLM_FLASHINFER_AUTOTUNE="1"

# 4. Critical FlashInfer Skip-Ops (Eliminates 45-min Triton MoE Warmup Hang)
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"

# 5. Pipeline Parallel Layer Partition (15/12 Split for 27-Layer Architectures)
export VLLM_PP_LAYER_PARTITION="15,12"

# 6. NCCL Inter-Node Transport Tuning
export NCCL_SOCKET_IFNAME="ens3"
export NCCL_NET="Socket"
export NCCL_CROSS_NIC="0"       # Avoids cross-socket PCIe saturation
export NCCL_ALGO="Tree"         # High-efficiency multi-node collective tree
export NCCL_PROTO="Simple"      # Stable streaming protocol
export NCCL_BUFFSIZE="4194304"  # 4 MB socket buffer
```

---

## 🗂️ Categorized Run-Type Directory Architecture

```text
Performance_Intelligence_Platform/scripts/
│
├── run_smoke_test.sh                     <- 10-Check Automated Sanity Smoke Test (~3-5 min)
├── run_master_benchmark.sh               <- Unified Master Benchmark Runner (Steps 00-17: ~8h 55m)
├── run_continuous_batching.sh / .py      <- Continuous Batching Suite Runner (Blocks 1-7)
├── master_benchmark_cases.json           <- Unified Declarative Cases Manifest across All Topologies
├── continuous_batching_cases.json         <- Case Manifest for Continuous Batching Sweeps
├── expected_values.json                   <- Cryptographic Ground-Truth Fixtures & Reference Numbers
├── RUN_CONFIG.env                         <- Active Runtime Configuration (IPs, Engine Flags)
├── RUN_CONFIG.env.example                 <- Documented Master Configuration Template
│
├── pip_waves.py                           <- Request Wave Decomposition & Stall Reference Tool
├── pip_scan.py                            <- Recursive Directory Pause & Stall Scanner
├── pip_timeline.py                        <- Publication-Quality Timeline Diagram Plotter
├── pip_step_cost.py                       <- Continuous Batching Step-Cost Linear Model Fitter
├── pip_mixed_traffic.py                   <- Short + Long Concurrent Stream Interference Analyzer
├── ttft_waves.py                          <- First-Wave TTFT Decomposition & Burst Analyzer
├── bench_summary.py                       <- Aggregator with Pause & Stall Indicators
├── generate_result_summary.py             <- Markdown Report Generator for Benchmark Runs
├── v5_runner_lib.py                       <- Shared Runtime Helper Library
│
├── 01_preflight_and_diagnostics/         <- [RUN TYPE 1] Host qualification, PCIe Gen5 bandwidth, NUMA & Ray/NCCL readiness
├── 02_single_node_baseline_matrix/       <- [RUN TYPE 2] Closed-loop concurrency sweeps (c1..c64) & KV-cache allocation
├── 03_open_loop_poisson_arrival/         <- [RUN TYPE 3] Stochastic Poisson arrival processes & queue delay analysis
├── 04_scaleout_distributed_network/      <- [RUN TYPE 4] Multi-node distributed serving (TP16, TP8+PP2) & VPC network pacing
├── 05_long_context_1m_extensions/        <- [RUN TYPE 5] Extreme 128K to 1M token sequence lengths & memory limits
├── 06_deep_kernel_and_torch_profiling/   <- [RUN TYPE 6] NVIDIA Nsight Systems & PyTorch Profiler Chrome traces
└── 07_master_campaign_orchestration/     <- [RUN TYPE 7] Autonomous master campaign orchestrator supervising all 20 steps (4 profiles)
```
