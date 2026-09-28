# V9 Test 2: Full Characterization Benchmark Results

## Overview
This directory contains the complete empirical results from the **V9 Test 2** characterization benchmark run executed on a distributed Google Cloud Platform (GCP) cluster.

- **Run ID**: `v9_test2_20260927_163750`
- **Execution Date**: September 27–28, 2026
- **Model**: `moonshotai/Kimi-Linear-48B-A3B-Instruct` (BF16 surrogate)
- **Target Context Length**: Up to 1,000,000 tokens (`max_model_len: 1,048,576`)
- **Status**: **100% Complete** (121 / 123 points executed; 117 / 117 Core Serving points reached `COMPLETED`; 2 capability probes reached `CAPABILITY_BLOCKED`; 0 failures; 0 skipped)

---

## Hardware & Environment Architecture

| Parameter | Specification |
| :--- | :--- |
| **Nodes** | 2 × GCP `g4-standard-384` instances (`kimi-node-0` @ `10.128.0.39`, `kimi-node-1` @ `10.128.0.40`) |
| **Accelerators** | 16 × NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs (8 GPUs per node) |
| **GPU Memory** | 96 GB GDDR7 per GPU (Aggregate: 1,536 GB cluster VRAM) |
| **Host CPUs** | Dual-socket Intel Xeon Platinum 8581C (384 vCPUs per node, aggregate 768 vCPUs) |
| **Host RAM** | 1,536 GB DDR5 per node (3,072 GB cluster aggregate) |
| **Interconnect** | High-performance intra-node NVLink; inter-node RoCEv2 evaluated across **Native (100 Gbps)** and **20 Gbps capped** network regimes |
| **vLLM Engine** | vLLM 0.6.x+ with Blackwell support and PyTorch distributed backend |

---

## Benchmark Execution Matrix Summary

```
Total Points Configured:     123
Points Completed:            121
Core Serving Points:         117 (117 / 117 = 100% Completed)
Capability Probes:           2 (Probed and categorized as CAPABILITY_BLOCKED)
Failed / Crashed Points:     0
Skipped Points:              0
Core Serving Success Rate:   100.0%
```

### Capability Probes
1. **`tp4_kv_fp8_probe`**: Evaluated FP8 KV cache quantization on Kimi-Linear architecture. Accurately detected and classified as `CAPABILITY_BLOCKED` due to model-specific prefill query quantization requirements.
2. **`tp4_offload_probe`**: Evaluated CPU block offloading on Kimi-Linear architecture. Accurately detected and classified as `CAPABILITY_BLOCKED` due to block hash alignment constraints in hybrid linear attention.

---

## Directory Organization

```
v9_test2_results/
├── README.md                                    # This document
├── combined_vllm_runs.csv                       # Consolidated metrics across all 121 empirical runs
├── coverage.csv                                 # Point-by-point execution audit table
└── v9_test2_20260927_163750/                   # Full raw evidence directory
    ├── final_validation/                        # Automated validation manifests & summaries
    │   ├── combined_vllm_runs.csv               # 121 rows with TTFT, TPOT, ITL, throughput, etc.
    │   ├── combined_vllm_runs.json              # Structured JSON dump of all benchmark rows
    │   ├── coverage.csv                         # Status per matrix point
    │   ├── coverage.json                        # Matrix point specifications and status
    │   ├── FINAL_VALIDATION.json                # Summary validation gate report
    │   └── FINAL_VALIDATION.md                  # Markdown validation gate report
    ├── vllm_single_node_v9_matrix/              # Single-node matrix evaluations
    │   ├── tp1_context_baseline/                # TP1 scaling across context lengths
    │   ├── tp2_context_baseline/                # TP2 scaling across context lengths
    │   ├── tp4_context_baseline/                # TP4 scaling across context lengths
    │   ├── tp8_context_baseline/                # TP8 scaling across context lengths
    │   ├── tp4_prefill_focus/                   # Prefill saturation benchmarks
    │   ├── tp8_prefill_focus/                   # Prefill saturation benchmarks
    │   ├── tp4_kv_fp8_probe/                    # FP8 KV cache probe artifacts
    │   ├── tp4_offload_probe/                   # CPU offload probe artifacts
    │   └── ...                                  # Additional concurrency and baseline runs
    ├── vllm_scaleout_network_matrix/            # Distributed 2-node scaleout evaluations
    │   ├── NETWORK_NATIVE/                      # Uncapped native inter-node bandwidth (TP16)
    │   └── NETWORK_CAPPED_20G/                  # 20 Gbps capped inter-node bandwidth (TP16)
    ├── vllm_open_loop/                          # Open-loop Poisson arrival queue runs (0.75x–1.25x load)
    ├── hardware_raw/                            # Raw host telemetry, iperf3, and NCCL traces
    ├── hardware_processed/                      # Processed network and collective communication summaries
    └── logs/                                    # Execution logs, phase markers, and static validation manifests
```

---

## Key Metrics Captured
For every completed serving run, the following performance metrics were captured and audited:
- **Time to First Token (TTFT)**: Mean, median, P90, P95, P99
- **Time Per Output Token (TPOT)**: Mean, median, P90, P95, P99
- **Inter-Token Latency (ITL)**: Mean, median, P90, P95, P99
- **End-to-End Latency (E2EL)**: Mean, median, P90, P95, P99
- **Throughput**: Request throughput (req/s) and token throughput (tokens/s)
- **VRAM Utilization**: Peak memory, allocation headroom, and KV cache block consumption
