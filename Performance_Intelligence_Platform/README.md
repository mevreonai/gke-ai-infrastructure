# PERFORMANCE INTELLIGENCE PLATFORM
## High-Density GPU Serving Characterization, Benchmark Automation & Systems Verification

Welcome to the **Performance Intelligence Platform**. This repository is an autonomous, production-grade benchmarking, hardware profiling, and telemetry characterization platform engineered specifically to evaluate Large Language Model (LLM) serving on high-density GPU accelerator clusters (such as dual 8x NVIDIA Blackwell / RTX PRO 6000 Ada nodes interconnected via 100 Gbps Google Cloud Andromeda VPC).

The platform provides mathematically verified, reproducible ground truth regarding serving boundaries, memory pressure dynamics, kernel bottlenecks, and multi-node interconnect characteristics.

> [!NOTE]
> **Pure Execution & Automation Platform:** This repository contains the executable benchmark suite, hardware profilers, automated sanity smoke tests, and canonical raw telemetry datasets. Visual presentation dashboards are retained exclusively in dedicated analytics artifacts (`v8_full_results/dashboards/v4_dashboard/`).

---

## 🧭 Master Documentation & Runbooks

| Manual / Guide | File Link | Focus Area & Description |
|:---|:---|:---|
| **Operations Runbook (New VM Setup)** | [`RUNBOOK_NEW_VM_SETUP.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/RUNBOOK_NEW_VM_SETUP.md) | Step-by-step instructions from taking a fresh GCP VM, installing CUDA/PyTorch/vLLM, running the smoke test, and executing benchmarks. |
| **Setup & Operations Manual** | [`README_SETUP_AND_OPERATIONS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_SETUP_AND_OPERATIONS.md) | Exhaustive systems operations: host specs, NUMA pinning, Ray cluster orchestration, 100G VPC traffic control, and troubleshooting. |
| **Architecture & File Anatomy** | [`README_FILES_AND_ARCHITECTURE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/README_FILES_AND_ARCHITECTURE.md) | Script anatomy, declarative JSON schemas, empirical telemetry data dictionary, and 15-step characterization matrix. |
| **Execution Scripts Guide** | [`scripts/README.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/README.md) | Command-line options, flag syntax, environment variables, and module documentation. |

---

## ⏱️ Comprehensive Execution Timelines & Time Budgets

The unified benchmark runner consolidates all empirical characterization into a single sequential workflow with zero skips or failures.

| Stage / Component | Steps Included | Key Workloads & Focus Areas | Wall-Clock Estimate |
|:---|:---|:---|:---:|
| **Sanity Smoke Test** | Checks 1 – 9 | Toolchain, PyTorch/vLLM stack, Cutlass MoE flags, Cases JSON, Linux utils, Wave trimming, Synthetic benchmark, Master runner dry-run | **~3 – 5 min** |
| **Stage 1: Quick Wins & Baselines** | Steps 00 – 07 | 8.4K chunk budget A/B test, PyTorch batched profiles (c8, c32), NCCL socket tuning, TP8 host NUMA pinning, Sub-8K short prompts, 128K context knee repeats, R1 continuous context curve, KV pool audit | **~1h 10m** |
| **Stage 2: Scale-Out Concurrency** | Steps 08 – 13 | FP8 quantization evaluation, DDR5 CPU offload reuse, R2 agentic decay, Multi-node concurrency under load (c=1..8 across TP16, TP8+PP2, TP4+PP4), 15/12 asymmetric PP split (+27.58% speedup), R3 network resilience (Native, 100G, 20G, 0.05% loss), TP16 512K context serving | **~3h 30m** |
| **Stage 3: Deep Profiling & Sweeps** | Steps 14 – 15 | B1 CUDA Graphs-ON Nsight Systems decode trace (~4.47ms target), Single-node Nsys trace, PyTorch Chrome batched traces, B11 multi-node decode trace, Canonical telemetry compilation & 72-rule invariant audit | **~2h 30m** |
| **Total Full Campaign** | **Steps 00 – 15** | **Complete end-to-end systems characterization across single-node and multi-node** | **~7h 10m** |

---

## ⚙️ Dynamic Execution Flags & Options

The master benchmark runner (`scripts/run_master_benchmark.sh`) and smoke test (`scripts/run_smoke_test.sh`) dynamically support model, topology, bandwidth, and stage selection:

```bash
bash scripts/run_master_benchmark.sh [OPTIONS]
```

### Supported CLI Flags

* `--model <hf_id_or_path>`: Target HuggingFace model or local path (Default: `moonshotai/Kimi-Linear-48B-A3B-Instruct`).
* `--revision <git_sha>`: Exact model commit hash for provenance verification.
* `--stage <1|2|3|all>`: Filter execution to a specific characterization stage:
  - `1`: Stage 1 Quick Wins & Single-Node (Steps 1–7: ~1h 10m)
  - `2`: Stage 2 Scale-Out Concurrency & Asymmetric PP (Steps 8–13: ~3h 30m)
  - `3`: Stage 3 Deep Profiling & Canonical Telemetry (Steps 14–15: ~2h 30m)
  - `all`: Full 15-step characterization (~7h 10m)
* `--topologies <list|all>`: Comma-separated list of target topologies to execute:
  - `tp4_pp1`: Single-node 4-GPU baseline
  - `tp8_pp1`: Single-node 8-GPU baseline (NUMA pinning, continuous context)
  - `tp4_pp2`: Dual-node 8-GPU pipeline parallel configuration
  - `tp8_pp2`: Dual-node 16-GPU scale-out (15/12 asymmetric partition)
  - `tp4_pp4`: Dual-node 16-GPU deep pipeline parallel configuration
  - `tp16_pp1`: Dual-node 16-GPU distributed tensor parallel configuration
  - `all`: Runs all topologies defined in the cases manifest
* `--bandwidth <list|all>`: Comma-separated list of network modes for Step 12 resilience testing:
  - `native`: Uncapped GCP Andromeda VPC (100 Gbps line rate)
  - `100g`: Shaped 100 Gbps via Linux `tc` HTB
  - `20g`: Shaped 20 Gbps via Linux `tc` HTB
  - `impaired`: Synthetic 0.05% packet loss + 0.2ms jitter via Linux `tc` netem
  - `all`: Tests all four network states sequentially
* `--dry-run`: Validates all script workflows, flags, argument parsing, directory creations, and environment setups without launching heavy GPU workloads.
* `--step <N>`: Executes a single target step (0 to 15).
* `--from-step <N>`: Resumes execution starting at step N.
* `--new-run`: Generates a fresh run directory without reading previous resume markers.

---

## 🛡️ Cutlass & Triton MoE Kernel Execution Invariants

To guarantee deterministic kernel performance and avoid Triton JIT compilation hangs or PCIe bus inversions, the following environment invariants are strictly enforced across all runner scripts:

```bash
# 1. Enforce physical PCI bus order mapping
export CUDA_DEVICE_ORDER="PCI_BUS_ID"

# 2. Triton Cutlass MoE Kernel Backend
export VLLM_MOE_BACKEND="triton"

# 3. FlashInfer JIT Autotuning
export VLLM_FLASHINFER_AUTOTUNE="1"

# 4. Critical FlashInfer Skip-Ops (Prevents 45-min Triton MoE Warmup Hang)
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

## 🏛️ Repository Topology

```text
Performance_Intelligence_Platform/
├── README.md                                  <- Master Platform Overview & Timelines (This File)
├── RUNBOOK_NEW_VM_SETUP.md                    <- Complete End-to-End Runbook for Fresh VM Provisioning
├── README_FILES_AND_ARCHITECTURE.md           <- In-Depth Script & Data Architecture Manual
├── README_SETUP_AND_OPERATIONS.md             <- Cluster Setup & Systems Operations Manual
│
├── scripts/                                   <- EXECUTABLE BENCHMARK AUTOMATION SUITE
│   ├── run_smoke_test.sh                      <- 9-Check Automated Sanity Smoke Test (~3-5 min)
│   ├── run_master_benchmark.sh               <- Unified Master Benchmark Runner (Steps 00-15: ~7h 10m)
│   ├── master_benchmark_cases.json           <- Declarative Cases Manifest across All Topologies
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
    ├── combined_vllm_runs.csv                 <- 126-Run Master Tabular Telemetry
    ├── combined_vllm_runs.json                <- Master JSON Representation of Serving Metrics
    ├── PLATFORM_FULL_RELEASE.json             <- Frozen Audited Release Dataset
    ├── master_step_status.jsonl               <- Real-Time Telemetry Stream of Master Execution
    └── results/                               <- Multi-Phase Characterization Traces & Archive Vaults
```

---

## 🚀 Quickstart: Running on a Fresh VM

```bash
# 1. Clone or copy platform to VM
cd ~/Performance_Intelligence_Platform/scripts

# 2. Configure cluster IPs (if running multi-node)
cp RUN_CONFIG.env.example RUN_CONFIG.env
nano RUN_CONFIG.env

# 3. Execute Automated Smoke Test (~3-5 min)
bash run_smoke_test.sh

# 4. Launch Unified Master Benchmark (Stage 1 or Full Campaign)
# Stage 1 Quick Wins (~1h 10m):
bash run_master_benchmark.sh --stage 1

# Full 15-Step Campaign (~7h 10m):
bash run_master_benchmark.sh --all
```
