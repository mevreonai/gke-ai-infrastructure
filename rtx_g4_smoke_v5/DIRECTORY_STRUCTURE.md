# RTX PRO 6000 Benchmark & Characterization Directory Structure

This directory organizes all empirical benchmarks, hardware characterization runs, distributed profiles, logs, and interactive dashboards.

```
rtx_g4_smoke_v5/
├── MASTER_BENCHMARK_SUMMARY.md                  <- Cross-suite executive summary
├── MASTER_CHARACTERIZATION_DASHBOARD.html      <- 1-to-1 Interactive characterization dashboard
│
├── 01_v5_baselines/                            <- Previous V5 Baselines
│   ├── option_a_pytorch/                       <- PyTorch / HuggingFace baseline runs
│   │   ├── results/                            <- VLLM_SUMMARY.md, vllm_runs.csv
│   │   └── scripts/                            <- Execution scripts
│   ├── option_b_deepspeed/                     <- DeepSpeed ZeRO-3 baselines
│   │   ├── results/                            <- OPTION_B_SUMMARY.md, traces
│   │   └── scripts/                            <- Execution scripts
│   └── option_c_nccl_hardware/                 <- NCCL interconnect & hardware network sweep
│       ├── results/                            <- AllReduce, AllGather, ReduceScatter across sockets
│       └── scripts/                            <- Runner scripts
│
├── 02_v6_production_suite/                     <- Complete V6 Benchmark Suite
│   ├── single_node_matrix/                     <- 22 Cases / 59 Empirical Benchmarks
│   │   ├── summary/
│   │   │   ├── vllm_runs.csv                   <- Full metrics across all 59 benchmark runs
│   │   │   ├── VLLM_SUMMARY.md                 <- Single-node analytical report
│   │   │   └── SERVING_ANALYSIS.md             <- Capacity, gating, and prefill/decode findings
│   │   └── qualification_logs/                 <- Detailed server.log, bench_stdout.log, metrics_gpu.jsonl
│   ├── multi_node_distributed/                 <- 16x GPU Multi-Node Cluster Runs
│   │   ├── summary/
│   │   │   └── MULTI_NODE_SUMMARY.md           <- Topology comparison (TP4_PP4 vs TP16)
│   │   ├── traces_and_logs/                    <- Per-topology raw server & client logs
│   │   │   ├── tp4_pp4_dist/                   <- Optimal multi-node topology logs & metrics
│   │   │   ├── tp4_pp2_dist/                   <- Remote-PP validation case
│   │   │   ├── tp8_pp2_dist/                   <- Intra-node TP8, cross-node PP2
│   │   │   └── tp16_pp1_dist/                  <- Cross-node TP16 AllReduce bound
│   │   └── archive/
│   │       └── vllm_multi_node.tar.gz          <- Compressed archive of all multi-node traces (3.8MB)
│   └── scripts/                                <- Autonomous harness & test manifests
│       ├── 07_preflight_v5.py
│       ├── 10_vllm_surrogate_cases.json
│       ├── 10b_vllm_multi_node_cases.json
│       ├── 11_run_vllm_surrogate.py
│       └── 12_run_vllm_multi_node.sh
│
└── 03_dashboards/                              <- Production Dashboards
    ├── MASTER_CHARACTERIZATION_DASHBOARD.html  <- Standalone 1-to-1 replica dashboard
    ├── v6_characterization_dashboard.html      <- Result dashboard
    └── build_characterization_dashboard.py     <- Dashboard generator script
```
