# V8-FULL Characterization Dashboard — V4 Decision Intelligence

This directory contains the production-grade V4 characterization dashboard for the V8-FULL campaign on Native GCP Fabric (173.58 Gbps, MTU 8896, 0.05ms RTT) and dual-node 16x RTX 6000 Ada Blackwell Server Edition.

## Files
- index.html: Canonical self-contained HTML dashboard. Open directly in any browser.
- MASTER_CHARACTERIZATION_DASHBOARD.html: Exact matching distribution dashboard file.

## Features
- **7 Comprehensive Tabs**:
  1. 🏛 Executive Summary & KPI cards
  2. 📈 Scale-Up (TP4/PP1 vs TP8/PP1 on local PCIe/NUMA)
  3. 🌐 Scale-Out (Dynamic metric dropdown: TTFT, TPOT, Out TPS, Req TPS, KV %, Queue wait, Preemptions across 128K, 512K, 1M, and Network Sweeps)
  4. 📜 Long Context & 1M Serving Decisions
  5. ⚙ Scheduler & KV Capacity (Single-Node & Multi-Node Scale-Out Ledger)
  6. 🔬 Profiler & Trace Completeness (22 verified captures, Critical Path Ledger: 54% GPU / 46% AllReduce prefill, 13.7% GPU / 86.3% AllReduce decode)
  7. 📋 Evidence & Audit Ledger (126 live-filterable benchmark rows)
- **Zero Mock Data**: 100% directly bound to combined_vllm_runs.json, coverage.json, and 
sys_stats.txt.
