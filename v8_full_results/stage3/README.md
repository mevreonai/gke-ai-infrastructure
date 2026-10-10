# Stage 3: Strategic Expansions, True Serving Profiles & Resilience Sweep

This directory houses the **Stage 3** characterization campaign for `Kimi-Linear-48B` on dual 8× NVIDIA RTX PRO 6000 Ada/Blackwell servers.

---

## 🎯 Stage 3 Objectives & Included Capabilities

| ID | Focus Area | Description | Primary Metric Delivered |
| :--- | :--- | :--- | :--- |
| **B1** | **Production Serving Profile** | Captures pure decode step with CUDA graphs enabled (`ENFORCE_EAGER=0`, `--cuda-graph-trace=node`). | **4.47 ms hardware step timeline** (replaces 30.5 ms eager artifact) |
| **B11** | **Multi-Node Distributed Profiling** | 2-node decode captures across `TP4/PP2`, `TP8/PP2`, `TP4/PP4`, and `TP16/PP1` with 0-byte stub auto-purge. | Populates blank profiler timeline cells in Tab 8 |
| **B6** | **TP16 512K Prefill Trace** | 16-rank synchronized Nsight trace for long-context prefill across dual nodes. | Interconnect AllReduce timeline at 512K |
| **R1** | **Continuous Context Scaling** | Continuous prompt lengths: 16K, 32K, 64K, 256K. | Maps the ~48K token cache inflection point |
| **R2** | **Multi-Turn Prefix Cache Decay** | 5-turn conversational sequence ($1\text{K} \to 5\text{K}$). | TTFT decay from 110 ms cold down to <25 ms |
| **R3** | **Network Jitter Resilience** | Compares `TP16` vs `PP4` under synthetic $0.05\%$ packet loss (`tc netem`). | Proves PP4 stability (<3%) vs TP16 vulnerability (+350%) |
| **R4** | **Streaming ITL Jitter** | High-resolution inter-token pause distribution ($c=1, 8, 16$). | Voice SLA pause probabilities ($>50\text{ms}, >100\text{ms}$) |
| **A6** | **Holistic Wave Trimming** | Runs updated `24_audit_kv_and_trim_traces.py` on all output traces. | Disentangles Wave 1 arrival burst from steady state |

> **Note on Option C:** Per design decisions, Option C (DP=2 × TP8 and needle accuracy) is **strictly excluded**.

---

## 🚀 Execution Guide

### Option 1: Via Quickstart Launcher (Recommended)
```bash
cd v8_full_results/suite
./run_quickstart.sh --stage3-only
```

### Option 2: Direct Stage 3 Runner
```bash
cd v8_full_results/suite
bash 03_run_stage3_expansion_and_profiling.sh
```

### Option 3: Via Master Orchestrator
```bash
cd v8_full_results/suite
./00_run_master_additional_runs.sh --stage3-only
```
