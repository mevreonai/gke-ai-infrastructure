# V6 vLLM Characterization Suite — Master Results Index & Guide

## Executive Summary for Leadership
This document clarifies the structure of the **V6 vLLM Characterization Suite** and provides an authoritative index for all results, metrics, logs, and dashboards.

### Why Were There Two Folders (`v6_suite` vs `02_v6_production_suite`)?
During the development of the benchmarking suite:
1. **`rtx_g4_smoke_v5/v6_suite/`** was the initial **working development and execution directory** where engineers ran shell scripts (`run_v6_e2e.sh`) and raw log files were initially generated.
2. **`rtx_g4_smoke_v5/02_v6_production_suite/`** was created as the **clean, curated production repository** alongside `01_v5_baselines` and `03_dashboards`.

Both folders contain the same underlying benchmark data. To eliminate confusion permanently:
- **`02_v6_production_suite` is the Canonical Production Repository**.
- A single, self-contained **ZIP archive** (`V6_BENCHMARK_RESULTS_AND_LOGS.zip`) has been assembled with all reports, logs, and dashboards.

---

## 1. Complete Repository Layout

```
rtx_g4_smoke_v5/
├── 01_v5_baselines/                  # Prior V5 baseline benchmarks (Option A, B, C)
│
├── 02_v6_production_suite/          # ★ CANONICAL V6 PRODUCTION DIRECTORY
│   ├── README.md                     # Production suite guide
│   ├── scripts/                      # Benchmark execution scripts and case JSONs
│   │   ├── 10_vllm_surrogate_cases.json
│   │   ├── 10b_vllm_multi_node_cases.json
│   │   ├── run_v6_e2e.sh
│   │   └── ...
│   ├── single_node_matrix/           # Single-node matrix (8K, 128K, 512K, 1M context)
│   │   ├── qualification_logs/       # Raw GPU metrics (jsonl), Prometheus logs, warmups
│   │   └── summary/
│   │       ├── vllm_runs.csv         # 59-row master benchmark results table
│   │       ├── VLLM_SUMMARY.md       # Single-node summary report
│   │       └── SERVING_ANALYSIS.md   # Capacity & serving envelope report
│   └── multi_node_distributed/       # Multi-node 2-node distributed results (16 GPUs)
│       ├── archive/                  # Compressed multi-node logs (vllm_multi_node.tar.gz)
│       ├── summary/
│       │   └── MULTI_NODE_SUMMARY.md # Distributed comparison report
│       └── traces_and_logs/          # Raw Ray server logs, node metrics, placement snapshots
│
├── 03_dashboards/                    # Dashboard audit documentation and specifications
│   └── docs/audit/                   # Acceptance checklists, audit specs, original PDF
│
└── v6_suite/                         # Historical working execution workspace (contains notice pointing to 02_)
```

---

## 2. Key Benchmark Results Overview

### Test Environment & Workload
- **Hardware**: NVIDIA RTX PRO 6000 Blackwell Server Edition (96GB GDDR7, PCIe Gen5).
- **Nodes**: 2 nodes (8 GPUs per node = 16 GPUs total).
- **Workload**: `moonshotai/Kimi-Linear-48B-A3B-Instruct` (BF16 weights, surrogate characterization model).
- **Engine**: vLLM with Ray distributed backend.

---

### A. Single-Node Benchmark Summary (`vllm_runs.csv`)
The single-node matrix covers **59 completed benchmark runs**:

| Context Length | Tested Concurrency ($c$) | TP Configuration | Measured TTFT | Output tok/s | Notes |
|---|---|---|---|---|---|
| **8K** | $c = 1 \dots 32$ | TP4 / PP1 | 188.4 ms ($c=1$) | 13.7 $\to$ 171.2 tok/s | Throughput scales with concurrency up to knee. |
| **8K** | $c = 1, 8$ | TP8 / PP1 | 135.7 ms ($c=1$) | 11.2 $\to$ 75.3 tok/s | Lower TTFT than TP4; higher TPOT overhead. |
| **128K** | $c = 1 \dots 16$ | TP4 / PP1 | 4,819.6 ms ($c=1$) | 13.7 $\to$ 58.7 tok/s | Peak throughput at $c=16$. |
| **512K** | $c = 1 \dots 4$ | TP4 / PP1 | 24,185.0 ms ($c=1$) | 2.0 tok/s | Stable throughput; TPOT scales with concurrency. |
| **1M** | $c = 1 \dots 4$ | TP4 / PP1 | 93,456.2 ms ($c=1$) | 0.3 tok/s | Memory feasibility established (12.3% KV peak @ $c=1$). |

*Preemption Telemetry*: **Zero preemptions** observed (`preemptions_delta = 0` in all 59 rows).

---

### B. Multi-Node Distributed Benchmark Summary (`MULTI_NODE_SUMMARY.md`)
Tested across 2 nodes (16 GPUs total) at 128K context:

| Topology | Distribution Architecture | TTFT (ms) | Output tok/s | Inter-Node Traffic | Assessment |
|---|---|---|---|---|---|
| **Forced TP4 / PP2** | Local NUMA TP4 per node; cross-node remote PP boundary | **1,723.7 ms** | **30.9 tok/s** | 8.6 GB/s | **Fastest TTFT / throughput**. Minimizes cross-node sync by confining TP to local NUMA. |
| **TP8 / PP2** | TP8 per node; remote PP boundary across nodes | **2,646.6 ms** | **21.4 tok/s** | 2.4 GB/s | Balanced intra-node scaling with pipeline separation. |
| **TP4 / PP4** | 4 pipeline stages (2 stages per node); TP4 within NUMA | **2,817.6 ms** | **19.5 tok/s** | 1.2 GB/s | Lowest network bandwidth demand; increased pipeline bubble. |
| **TP16 / PP1** | 16-GPU Tensor Parallelism spanning across nodes | **6,024.9 ms** | **9.5 tok/s** | 22.4 GB/s | Heavy inter-node All-Reduce communication penalty over VPC. |

---

## 3. Deliverables & Access Links

1. **All-in-One Packaged ZIP**:
   - File: [`V6_BENCHMARK_RESULTS_AND_LOGS.zip`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V6_BENCHMARK_RESULTS_AND_LOGS.zip)
   - Size: **11.59 MB** (compressed from ~147 MB of raw logs).
   - Contains: All CSVs, markdown summaries, raw single-node logs, distributed Ray logs, scripts, and the full interactive dashboard.

2. **Master Interactive Audit Dashboard**:
   - File: [`MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/MASTER_CHARACTERIZATION_DASHBOARD.html)
   - Description: Comprehensive 7-tab dashboard (Executive, Scale-Up, Scale-Out, Long Context, Scheduler & KV, Profiler, Evidence) with verified point-to-row provenance.

3. **Core Summary Files**:
   - Single-Node CSV: [`rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/vllm_runs.csv`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/vllm_runs.csv)
   - Single-Node Summary: [`rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/VLLM_SUMMARY.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/VLLM_SUMMARY.md)
   - Multi-Node Summary: [`rtx_g4_smoke_v5/02_v6_production_suite/multi_node_distributed/summary/MULTI_NODE_SUMMARY.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/rtx_g4_smoke_v5/02_v6_production_suite/multi_node_distributed/summary/MULTI_NODE_SUMMARY.md)
   - Serving Analysis: [`rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/SERVING_ANALYSIS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/SERVING_ANALYSIS.md)
