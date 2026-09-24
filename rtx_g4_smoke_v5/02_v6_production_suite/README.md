# V6 Production Suite — Canonical Results & Architecture

## Overview
This directory is the **canonical, production-grade repository** for the V6 vLLM characterization benchmarks executed on **NVIDIA RTX PRO 6000 Blackwell Server Edition (96GB GDDR7, PCIe Gen5)** nodes.

> **Note on Directory History**:
> Previously, benchmark runs were conducted in the flat working workspace `rtx_g4_smoke_v5/v6_suite/`. This directory (`02_v6_production_suite`) is the clean, structured, and archived production hierarchy intended for long-term reference and stakeholder reporting.

---

## Directory Structure

```
02_v6_production_suite/
├── scripts/                          # All benchmark runner scripts and JSON test case definitions
│   ├── 10_vllm_surrogate_cases.json  # Single-node 59-run test matrix definition
│   ├── 10b_vllm_multi_node_cases.json# Multi-node distributed test case definitions
│   ├── run_v6_e2e.sh                 # Full end-to-end suite runner
│   ├── 11_run_vllm_surrogate.py      # Single-node test executor
│   ├── 12_run_vllm_multi_node.py     # Multi-node test executor
│   ├── 15_summarize_vllm.py          # Metrics extraction and CSV builder
│   └── README_V6.md                  # Comprehensive script & execution guide
│
├── single_node_matrix/               # Single-node qualification and scaling matrix (8K to 1M tokens)
│   ├── qualification_logs/           # Raw GPU logs, Prometheus logs, and warmup logs (TP4 & TP8)
│   └── summary/                      # Core summary reports
│       ├── vllm_runs.csv             # The master 59-row benchmark results CSV
│       ├── VLLM_SUMMARY.md           # Markdown summary of single-node throughput, TTFT, and TPOT
│       └── SERVING_ANALYSIS.md       # Serving capacity and latency envelope analysis
│
└── multi_node_distributed/           # Multi-node 2-node distributed benchmark results (16 GPUs)
    ├── archive/                      # Compressed raw logs archive (vllm_multi_node.tar.gz)
    ├── summary/                      # Multi-node summary report
    │   └── MULTI_NODE_SUMMARY.md     # Comparison of TP4/PP4, TP4/PP2, TP8/PP2, and TP16/PP1
    └── traces_and_logs/              # Raw multi-node Ray server logs, placement snapshots, and node telemetry
```

---

## Key References
- **Interactive Characterization Dashboard**: [`c:/Users/ayu23/OneDrive/Desktop/tpu/MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/MASTER_CHARACTERIZATION_DASHBOARD.html)
- **All-in-One Downloadable ZIP Archive**: [`c:/Users/ayu23/OneDrive/Desktop/tpu/V6_BENCHMARK_RESULTS_AND_LOGS.zip`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V6_BENCHMARK_RESULTS_AND_LOGS.zip)
- **Master Index & Stakeholder Guide**: [`c:/Users/ayu23/OneDrive/Desktop/tpu/V6_MASTER_RESULTS_INDEX.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V6_MASTER_RESULTS_INDEX.md)
