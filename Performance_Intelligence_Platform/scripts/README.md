# Performance Intelligence Platform — Benchmark Automation Suite

Welcome to the **Benchmark Automation Suite** of the Performance Intelligence Platform. This folder contains all the executable test scripts, case manifests, profiling harnesses, and orchestrator tools engineered to characterize Large Language Model (LLM) serving on high-density GPU accelerator clusters.

The automation suite is organized into **7 specialized sub-folders** categorized by the type of characterization run, alongside convenient top-level entrypoints.

---

## 🗂️ Categorized Run-Type Directory Architecture

```text
Performance_Intelligence_Platform/scripts/
│
├── 01_preflight_and_diagnostics/         <- [RUN TYPE 1] Host qualification, PCIe Gen5 bandwidth, NUMA & Ray/NCCL readiness
│   ├── run_quickstart.sh                 <- 2-minute preflight sanity check
│   ├── 01_prepare_node.sh                <- CPU performance governor, GPU persistence & page cache flush
│   ├── 02_run_node_local.sh              <- Local host-to-device and peer-to-peer PCIe bandwidth tests
│   ├── 03_run_network_sweep.sh           <- Inter-node iperf3 / sockperf network latency sweeps
│   ├── 20_ray_nccl_env_audit.py          <- Environment variable & interface parity auditor across Ray actors
│   ├── 22_readiness.py                   <- vLLM worker process initialization & Ray cluster qualification
│   └── README.md                         <- Deep documentation for preflight tools
│
├── 02_single_node_baseline_matrix/       <- [RUN TYPE 2] Closed-loop concurrency sweeps (c1..c64) & KV-cache allocation
│   ├── 20_run_single_node_v6_aligned.sh  <- Master runner for single-node baseline matrices
│   ├── 10_vllm_surrogate_cases.json      <- Combinatorial test case manifest
│   ├── 11_run_vllm_surrogate.py          <- High-efficiency client request pipeline harness
│   ├── 13_generate_load_cases.py         <- Procedural test case generator
│   └── README.md                         <- Deep documentation for single-node baseline matrices
│
├── 03_open_loop_poisson_arrival/         <- [RUN TYPE 3] Stochastic Poisson arrival processes & queue delay analysis
│   ├── 09_metrics_sampler.py             <- 500ms Prometheus metrics harvester (queue depth, cache usage)
│   ├── 15_summarize_vllm.py              <- Open-loop trace aggregator & queue wait time analyzer
│   ├── 17_build_serving_analysis.py      <- Multi-variable arrival rate (λ) vs TTFT inflation correlation
│   └── README.md                         <- Deep documentation for open-loop runs
│
├── 04_scaleout_distributed_network/      <- [RUN TYPE 4] Multi-node distributed serving (TP16, TP8+PP2) & VPC network pacing
│   ├── 20_run_vllm_network_matrix.sh     <- Distributed sweep across TP16/PP1 vs TP8/PP2 under VPC 100G
│   ├── 10b_vllm_multi_node_cases.json    <- Multi-node distributed workload cases
│   ├── 12_run_vllm_multi_node.sh         <- Distributed launcher managing cross-node Ray workers
│   ├── 20_nccl_policy.sh                 <- NCCL socket buffer & transport tuning (NCCL_NET=Socket)
│   ├── 23_run_nccl_socket_tuning.sh      <- Linux TCP window auto-tuning evaluation
│   └── README.md                         <- Deep documentation for distributed network scaleout
│
├── 05_long_context_1m_extensions/        <- [RUN TYPE 5] Extreme 128K to 1M token sequence lengths & memory limits
│   ├── 10d_1m_extended_cases.json        <- 128K, 256K, 512K, and 1M context length workload manifest
│   ├── 24_audit_kv_and_trim_traces.py    <- KV-cache block allocation auditor & fragmentation tracker
│   ├── stage2_cases_single_node.json     <- Concurrency and memory stress parameters
│   └── README.md                         <- Deep documentation for long-context runs
│
├── 06_deep_kernel_and_torch_profiling/   <- [RUN TYPE 6] NVIDIA Nsight Systems & PyTorch Profiler Chrome traces
│   ├── 14_run_vllm_nsys_profile.sh       <- Nsight Systems full timeline profiler (.nsys-rep)
│   ├── 14b_run_vllm_torch_profile.sh     <- PyTorch Profiler Chrome trace generator (.pt.trace.json.gz)
│   ├── 14c_run_vllm_torch_profile_batched.sh <- Batched iteration profiling under high concurrency
│   ├── 21_run_vllm_capped_profiles.sh    <- Low-overhead targeted iteration window profiling
│   ├── 16_analyze_vllm_profiles.py       <- Kernel duration distribution & GEMM vs Attention breakdown
│   ├── 19_postprocess_nsys.py            <- Nsight SQLite / text export processor
│   └── README.md                         <- Deep documentation for kernel and operator profiling
│
├── 07_master_orchestration_and_stages/   <- [RUN TYPE 7] Autonomous multi-hour campaign orchestrator & stage runners
│   ├── 00_run_master_additional_runs.sh  <- Master campaign supervisor (Steps 01 to 15: ~21.5h wall-time)
│   ├── 01_run_stage1_quick_wins.sh       <- Stage 1 runner (Steps 01 to 08 quick wins: ~5h 23m)
│   ├── 02_run_stage2_failed_and_scaleout.sh <- Stage 2 runner (Steps 09 to 15 deep scaleout: ~12h 50m)
│   ├── stage1_cases.json                 <- Workload manifest for Stage 1
│   ├── stage2_cases_multi_node_load.json <- Workload manifest for distributed multi-node
│   └── README.md                         <- Deep documentation for campaign orchestration
│
├── run_quickstart.sh                     <- Root 2-minute preflight environment & sanity verifier
├── 00_run_master_additional_runs.sh      <- Root master campaign launcher
├── 01_run_stage1_quick_wins.sh           <- Root Stage 1 quick-wins launcher
├── 02_run_stage2_failed_and_scaleout.sh  <- Root Stage 2 deep scale-out launcher
├── RUN_CONFIG.env                        <- Active cluster configuration (IPs, engine flags)
├── RUN_CONFIG.env.example                <- Documented master configuration template
└── README.md                             <- Exhaustive scripts directory navigation guide (This File)
```

---

## ⚡ Quickstart: Launching Benchmarks

### 1. Set Your Cluster Node IPs
Edit [`RUN_CONFIG.env`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/RUN_CONFIG.env):
```bash
export NODE0_IP="10.128.0.10"   # Head Node Private IP
export NODE1_IP="10.128.0.11"   # Worker Node Private IP
```

### 2. Run Preflight Sanity Check (< 2 Minutes)
```bash
cd Performance_Intelligence_Platform/scripts
./run_quickstart.sh
```

### 3. Launch Individual Run Types Independently
Every run type can be executed independently from its dedicated subfolder:
- **Preflight & Hardware Diagnostics:**
  ```bash
  cd 01_preflight_and_diagnostics && ./02_run_node_local.sh
  ```
- **Single-Node Baseline Concurrency Matrix:**
  ```bash
  cd 02_single_node_baseline_matrix && ./20_run_single_node_v6_aligned.sh
  ```
- **Open-Loop Poisson Arrival Distribution:**
  ```bash
  cd 03_open_loop_poisson_arrival && python3 09_metrics_sampler.py --interval 0.5
  ```
- **Scale-Out Distributed Network Sweeps:**
  ```bash
  cd 04_scaleout_distributed_network && ./20_run_vllm_network_matrix.sh
  ```
- **Extreme 1M Long-Context Stress:**
  ```bash
  cd 05_long_context_1m_extensions && python3 24_audit_kv_and_trim_traces.py
  ```
- **Deep Nsight & PyTorch Kernel Profiling:**
  ```bash
  cd 06_deep_kernel_and_torch_profiling && ./14_run_vllm_nsys_profile.sh
  ```
- **Full Autonomous 21.5-Hour Master Campaign:**
  ```bash
  cd 07_master_orchestration_and_stages
  nohup ./00_run_master_additional_runs.sh > ../../data/raw_runs/master_campaign_stdout.log 2>&1 &
  ```

---

## 🛡️ Operational Features
1. **State Resumption (`PLATFORM_RESUME=1`):** Automatically skips completed steps and resumes interrupted campaigns from the exact point of failure.
2. **Watchdog Daemon:** Periodically inspects GPU memory allocation and kills dangling Ray actors between steps.
3. **Inter-Step Cooldown:** 120-second resting period between intensive test phases with page cache flushes (`sync && echo 3 > /proc/sys/vm/drop_caches`) and GPU memory resets.
