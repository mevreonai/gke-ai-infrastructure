# V8 Benchmark Suite, Empirical Data & Dashboard Architecture Guide

This document provides a comprehensive, granular reference for the **V8 Characterization of MoonshotAI Kimi-Linear-48B on Dual-Node NVIDIA RTX PRO 6000 Blackwell Server Edition**.

It clarifies the exact role of the three `v8` folders, details every script and configuration file, explains how empirical data is integrated into the frontend dashboard, and establishes the audit provenance behind the v1.4 verification release.

---

## 1. Why Are There Three V8 Folders?

The repository contains three distinct `v8` directories to maintain strict separation of concerns across the benchmark lifecycle:

```
tpu/
├── v8_full_results/             [1] Canonical Baseline & Interactive Dashboard
├── v8_additional_runs_suite/    [2] Benchmark Runner Scripts & Case Definitions
└── v8_additional_runs_local/    [3] Downloaded Cluster Execution Outputs & Traces
```

### Summary of Differences

| Folder | What It Represents | Lifecycle Stage | Primary Audience |
| :--- | :--- | :--- | :--- |
| **`v8_full_results/`** | **The Canonical Results & Dashboard** | Production Release | Stakeholders, architects, and frontend viewers |
| **`v8_additional_runs_suite/`** | **The Test Runner Suite & Source Code** | Pre-Execution / Approval | Cloud engineers, cluster operators, and management |
| **`v8_additional_runs_local/`** | **The Raw Empirical Data Archive** | Post-Execution Data Capture | Performance auditors, profiling engineers, and data analysts |

---

### In-Depth Breakdown of Each Folder

#### 1. `v8_full_results/` — The Canonical Master & Frontend Dashboard
* **Purpose:** Serves as the authoritative source of truth for the primary V8 campaign (126 benchmark runs). It contains the interactive frontend dashboard, frozen CSV matrices, case manifests, and release validation metadata.
* **Key Components:**
  * `dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html`: The 10-tab standalone, self-contained interactive visualization dashboard (3.7 MB with embedded base64 time-budget charts).
  * `dashboards/v4_dashboard/index.html`: Web server entrypoint mirror of the master dashboard.
  * `dashboards/v4_dashboard/DASHBOARD_CANONICAL_DATA.json`: Structured JSON containing evidence registries, hardware baselines, and test descriptions.
  * `dashboards/v4_dashboard/chart.umd.js`: Local Chart.js v4.4.1 runtime for zero-dependency offline rendering.
  * `results/real_data/final_validation/combined_vllm_runs.csv`: The authoritative 126-run benchmark result dataset.
  * `release_specs/`: Frozen configuration and validation artifacts.
  * `RUNS_INDEX.json`: Global catalog of all campaign runs.

#### 2. `v8_additional_runs_suite/` — The Benchmark Execution Suite
* **Purpose:** The executable code package that was zipped (`v8_additional_runs_stage1_stage2.zip`), approved by engineering leadership, transferred to the GCP cluster VMs (`kimi-node-0` and `kimi-node-1`), and executed to resolve campaign gaps.
* **Key Components:**
  * Runner Bash scripts (`00_run_master_additional_runs.sh`, `01_run_stage1_quick_wins.sh`, `02_run_stage2_failed_and_scaleout.sh`).
  * JSON case definition files (`stage1_cases.json`, `stage2_cases_single_node.json`, `stage2_cases_multi_node_load.json`).
  * `README_FOR_BOSS_APPROVAL.md`: The executive authorization memo detailing ROI, cloud cost ($68 total), runtime bounds, and technical justification.
  * `rtx_g4_smoke_v5/`: The underlying 32-script benchmark harness for vLLM server lifecycle, client traffic generation, and metrics collection.
  * `rtx_g4_smoke_v8_hw/`: The 11-script hardware qualification suite (nvbandwidth, nccl-tests, BabelStream, iperf3).

#### 3. `v8_additional_runs_local/` — The Empirical Cluster Outputs Archive
* **Purpose:** The raw, unmodified measurement data downloaded locally from the cluster immediately after Stage 1 and Stage 2 runs completed, prior to shutting down the virtual machines.
* **Key Components:**
  * `master_step_status.jsonl`: Step-by-step execution receipts recording timestamps and exit codes (`rc: 0`).
  * `stage1/`: Output metrics, JSON logs, and analysis files for the 8 Stage 1 exploratory runs.
  * `stage2/`: Output metrics, manifests, and profiler captures for the 7 Stage 2 rerun/scaling benchmarks.
  * `env/`: System snapshots from both nodes (`nvidia-smi`, `python_stack`, `runtime_env`).
  * `logs/ADDITIONAL_RUNS_MASTER.log`: Master cluster console log capturing all stdout and stderr.
  * `SUITE_SOURCE_SHA256SUMS.txt`: Cryptographic hashes verifying cluster script integrity.

---

## 2. Granular Script & File Inventory

### A. Inside `v8_additional_runs_suite/` (Execution Scripts)

| Script / File | Purpose & Detailed Behavior |
| :--- | :--- |
| `00_run_master_additional_runs.sh` | **Master Runner Script:** Verifies environment variables, captures hardware snapshots on both nodes, executes Stage 1, executes Stage 2, records timing, and generates `master_step_status.jsonl`. |
| `01_run_stage1_quick_wins.sh` | **Stage 1 Quick-Wins Runner:** Orchestrates the 8 rapid experiments: chunk-size budget A/B, PyTorch batched decode operator profiles, NCCL socket tuning, CPU thread pinning, short-prompt qualification, and KV pool trace auditing. |
| `02_run_stage2_failed_and_scaleout.sh` | **Stage 2 Failed Runs & Scale-Out Runner:** Orchestrates the 7 remediation benchmarks: FP8 KV cache RCA, CPU offloading with 1M tokens, multi-node concurrent load scaling, PP2 15/12 layer rebalance, and multi-node 100G Nsight traces. |
| `README_FOR_BOSS_APPROVAL.md` | **Executive Approval Memo:** Formal briefing document outlining test objectives, risk mitigations, compute budget, and deployment rules. |
| `stage1_cases.json` | Case matrix defining parameters for Stage 1 runs (chunk sizes, context lengths, concurrency levels). |
| `stage2_cases_single_node.json` | Case matrix defining single-node Stage 2 runs (`--kv-cache-dtype fp8`, `--cpu-offload-gb 40`). |
| `stage2_cases_multi_node_load.json` | Case matrix defining distributed multi-node load testing (`TP4/PP4`, `TP8/PP2`, `TP16/PP1` across 128K, 512K, and 1M contexts). |
| `PILOT_STAGE1_ANALYSIS_RESULTS.json` | Pre-flight validation metrics and baseline performance targets. |
| `rtx_g4_smoke_v5/` | Complete modular test execution engine (includes `00_start_vllm.sh`, `01_run_bench.sh`, `09_metrics_sampler.py`, etc.). |
| `rtx_g4_smoke_v8_hw/` | Hardware qualification test framework (includes `run_nvbandwidth.sh`, `run_nccl_tests.sh`, `run_babelstream.sh`). |

---

### B. Inside `v8_additional_runs_local/` (Raw Empirical Data)

| Directory / File | Contents & Role in Verification |
| :--- | :--- |
| `master_step_status.jsonl` | Execution receipt log containing JSON objects with `step`, `rc: 0`, `start`, and `end` timestamps. |
| `env/node0_nvidia_smi.txt` | GPU driver and PCIe hardware topology dump for Node 0 (Driver 580.173.02, CUDA 13.0). |
| `env/node0_python_stack.txt` | Python package freeze (`vLLM 0.29.0`, `PyTorch 2.13.0`, `Ray 2.58.0`, `Triton 3.7.1`, `FlashInfer 0.6.18`). |
| `logs/ADDITIONAL_RUNS_MASTER.log` | Consolidated execution log containing complete server startup traces and benchmark client stats. |
| `stage1/01_chunk_budget_ab/` | Raw output JSONs comparing 8,192 vs 8,448 prompt token budgets. |
| `stage1/02_torch_profiles_batched/` | PyTorch profiler traces for batched decode across concurrencies 1, 4, 8, 16, 32. |
| `stage1/04_tp8_pinning/` | Benchmark metrics evaluating `numactl --cpunodebind=0` vs unpinned Ray worker processes. |
| `stage2/01_fp8_kv_rerun/` | Execution logs and Python traceback proving the SM100 architecture requirement in `mla_attention.py`. |
| `stage2/02_cpu_offload_reuse/` | Benchmark logs evaluating 1M context with DDR5 offloading at 99.8% GPU memory fill (41.39s TTFT reuse). |
| `stage2/03_multi_node_load/` | Multi-node concurrent scaling logs (TP4/PP4 achieving 2.4× faster TTFT at 1M under concurrency). |
| `stage2/04_pp2_split_evaluation/` | Benchmark outputs comparing uniform 14/13 PP2 layer split vs 15/12 rebalanced split (+1.18% TPOT gain). |
| `stage2/05_capped_profiles/` | 100G Nsight Systems SQLite exports and per-rank kernel attribution CSVs. |

---

### C. Inside `tools/` (Validation & Patching Utilities)

| Tool Script | Exact Operational Behavior |
| :--- | :--- |
| `tools/run_v1_4_verification.py` | **Comprehensive 72-Point Audit Suite:** Tests `MASTER_CHARACTERIZATION_DASHBOARD.html` against every requirement in `Dashboard_Fix_Verification_v1.4-for-V8.md` (Blockers B1–B8, N1–N22, P1–P17). Returns 100% PASS. |
| `tools/apply_complete_v1_4_fixes.py` | Applies surgical text, table, and data replacements directly in the dashboard HTML. |
| `tools/apply_kd_pages_fixes.py` | Updates the `KD_PAGES_DATA` array and initializes Key Discoveries interactive Chart.js instances. |
| `tools/apply_coverage_table_fixes.py` | Aligns the Profiler coverage table with genuine archive captures and planned points. |
| `tools/generate_exact_heatmap.py` | Recomputes all 36 cells of the Topology × Network Sensitivity Heatmap directly from `combined_vllm_runs.csv`. |
| `tools/fix_remaining_4.py` | Resolves HTML replacement edge cases and synchronizes the 16-rank aggregate chart title. |

---

## 3. Frontend Architecture: What Was Added & How Data Flows

The master dashboard ([`v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html)) is organized into 10 interactive tabs:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ MASTER CHARACTERIZATION DASHBOARD — MoonshotAI Kimi-Linear-48B (RTX PRO 6000 Blackwell) │
├───────────┬───────────┬───────────┬───────────┬───────────┬──────────┬─────────────────┤
│ Executive │ Key Discov│ Scale-Up  │ Scale-Out │ Long Ctx  │ Sched/KV │ Profiler/Traces │
│ Summary   │ (Top 10)  │ (NVLink)  │ (Fabric)  │ (1M Ctx)  │ (Memory) │ (Traces & P2P)  │
└───────────┴───────────┴───────────┴───────────┴───────────┴──────────┴─────────────────┘
```

### Where Additional Runs Data Fits Into the Frontend

#### 1. Long Context & 1M Tab (`#longcontext`)
* **FP8 KV Cache RCA Card (`#fp8-kv-cache-card`):**
  * Displays the exact root cause why `--kv-cache-dtype fp8` failed (`rc=1`): In `vllm/model_executor/layers/attention/mla_attention.py`, `backend_supports_prefill_query_quantization()` strictly checks `current_platform.is_device_capability_family(100)`. Because RTX PRO 6000 Blackwell is SM120 (`family 120`), FP8 MLA KV cache is disabled in software and strictly requires datacenter GB200/B200 (SM100).
* **CPU Offload Tiering Card (`#offload-card`):**
  * Displays the empirical metrics of 1M context with DDR5 offloading: Sustains 1,000,000 tokens at 99.8% GPU KV cache fill with DDR5 swapping, delivering 41.39s TTFT on 600K token reuse.

#### 2. Scale-Out Tab (`#scaleout`)
* **§4.7 Pipeline Stage Distribution & PP2 15/12 Optimization:**
  * Documents the +1.18% TPOT speedup (5.965 ms vs 6.036 ms) achieved by placing 15 layers on Stage 0 and 12 layers on Stage 1, perfectly balancing the compute load created by Stage 1's final LM Head projection.
* **Topology × Network Sensitivity Heatmap (`#scaleout-sensitivity-heatmap`):**
  * Displays all 36 cells recomputed directly from `combined_vllm_runs.csv`.
  * Strictly follows the classification rule: `< 15%` = `HIGH NETWORK RESILIENCE`, `> 50%` = `HIGH CAP SENSITIVITY / EXPOSED`.

#### 3. Scheduler & KV Tab (`#scheduler`)
* **Scale-Out Multi-Node Serving Ledger:**
  * Queue wait times populated with exact empirical measurements: `0.012ms`, `0.016ms`, `0.020ms`, `0.023ms`, `0.021ms`, `0.038ms`, and `0.019ms`.
* **Finding Cards (Chunk Headroom & MoE Uniform Routing):**
  * Clarifies that 211 ms is a predicted saving from expanding token headroom to 8,448 tokens (tested in Plan A1).
  * Notes that 163 and 222 active experts represent upper estimates under assumed uniform routing.

#### 4. Profiler & Traces Tab (`#profiler`)
* **End-to-End Wall-Time Budget Panel:**
  * Inlines all 4 time-budget PNG charts as Base64 Data URIs (`data:image/png;base64,...`), eliminating broken external file links and guaranteeing offline rendering.
* **Kernel Composition Across All 6 Layouts Table (§6.1):**
  * Displays all 56 cells exactly matching `prefill_composition_128k_by_layout.csv`.
* **Nsight Systems & PyTorch Operator Breakdown:**
  * Displays graphs-on serving budgets (1.04 ms on TP4 vs 3.23 ms on TP8, 18.9 µs vs 58.7 µs per AllReduce call).

#### 5. Comprehensive Evidence Tab (`#evidence`)
* **Cluster Readiness & Software Stack Audit:**
  * Replaces invented versions with exact archive versions: `vLLM 0.29.0`, `PyTorch 2.13.0`, `Ray 2.58.0`, `Triton 3.7.1`, `FlashInfer 0.6.18`, `nvidia-nccl-cu13 2.29.7` (worker lib `libnccl.so.2.31.2`), `Driver 580.173.02`, `CUDA 13.0`.
  * Transport verified as `NCCL_NET=Socket` on `ens3` (MTU 1460, provider plugin disabled).
* **Comprehensive Evidence Ledger (126 Canonical Runs):**
  * Restored `<div class="card mb8" id="perf-evidence-table-container">`.
  * Aligned all 126 rows to 15 columns, matching the 15 headers with exact warmup and prompt request counts.

---

## 4. Key Discoveries (Top 10) Architecture & Data Mapping

All 10 Key Discoveries explorer pages and modals are driven by `KD_PAGES_DATA`:

| Finding ID | Name | Primary Evidence Mapping | Key Empirical Metric |
| :---: | :--- | :---: | :--- |
| **KD#1** | Fabric Exposure | `EV-111` | TP16 TTFT increases +276.7% at 20G cap vs +3.9% on TP4/PP4. |
| **KD#2** | Concurrency Serialization | `EV-067` | Prefills serialize sequentially (arrival ladder 93.5s, 185.4s, 277.3s, 368.9s). |
| **KD#3** | Resource-Pressure Shift | `PR-007` | Full-attention work grows ~15.7× (128K→512K); SendRecv 4.5× (4.31→19.29s), AllReduce 2.7× (12.44→33.75s). |
| **KD#4** | Prefix Reuse | `EV-075` | Near-linear scaling (p≈1.00); 128K achieves 7 of 7 repeat hits (87.3%). |
| **KD#5** | Prompt-Token Admission | `EV-116` | 1.8× usable throughput gap (24,977 vs 13,967 tok/s prompt + output) under SLO gating. |
| **KD#6** | Parallelism Frontier | `EV-081` | TP4/PP4 consumes 143.1 J/1K tokens (310 W) vs TP16 247.2 J/1K tokens (225 W). |
| **KD#7** | TP Decode Communication | `PR-003` | 1.98× NCCL barrier latency (19.0 vs 37.6 µs); 3.10× PyTorch AllReduce CUDA time (132.3 vs 409.9 ms). |
| **KD#8** | Runtime Knobs | `EV-027` | 16K chunk size cuts TTFT by -27.1% at 1M; max_num_seqs ceiling is non-binding. |
| **KD#9** | Busy GPU ≠ Efficient Serving | `EV-084` | TP16 reports 80.6% GPU activity but draws only 225 W (stalled on VPC). |
| **KD#10** | KV Cache vs VRAM | `EV-084` | PP depth multiplies KV capacity (TP4/PP1 8.14M tokens → TP4/PP4 36.4M tokens). |

---

## 5. Verification & Audit Compliance Status

Every item in the audit punch list has been verified using the automated test suite:

```powershell
python tools/run_v1_4_verification.py
```

```
=== COMPREHENSIVE V1.4 AUDIT VERIFICATION (72 CHECKS) ===
[PASS] B1: vLLM 0.29.0 present
[PASS] B1: CUDA 13.0 present
[PASS] B1: PyTorch 2.13.0 present
[PASS] B1: Driver 580.173.02 present
[PASS] B1: NCCL 2.29.7 present
[PASS] B1: No invented AWS-OFI plugin
[PASS] B1: NCCL_NET=Socket present
[PASS] B2: Off-cluster path defect present
[PASS] B3: No 'safety-gated configurations not executed'
[PASS] B3: Attempted / rc=1 reason stated
[PASS] B4: <div class="card mb8" id="perf-evidence-table-container"> restored
[PASS] B4: No stray 'id="perf-evidence-table-container">' text
[PASS] B4: No orphan Cold Load header
[PASS] B5: Base64 embedded time-budget PNGs
[PASS] B6: confidence_note rendered
[PASS] B6: scope_note rendered
[PASS] B6: KD#6 4 scale-out + 2 scale-up in note
[PASS] B6: KD#9 nvidia-smi sampler in note
[PASS] B7: Key Finds tab button commented out
[PASS] P1: EV-111 mapped for finding 1
[PASS] P1: EV-067 mapped for finding 2
[PASS] P1: PR-007 mapped for finding 3
[PASS] P1: EV-075 mapped for finding 4
[PASS] P1: EV-116 mapped for finding 5
[PASS] P1: EV-081 mapped for finding 6
[PASS] P1: PR-003 mapped for finding 7
[PASS] P1: EV-027 mapped for finding 8
[PASS] P1: EV-084 mapped for finding 9
[PASS] P1: EV-084 mapped for finding 10
[PASS] N5: Stage 3 wait 17.2-21.9%
[PASS] N5: No 'Stages 1–3 wait 17–22%'
[PASS] N6: KD#6 1M energy TP16 247.2 J
[PASS] N6: KD#6 1M energy TP4/PP4 143.1 J
[PASS] N8: PP2 3 vs 4 full-attention layers
[PASS] N8: No '6 vs 8 full-attention'
[PASS] N9: TP8/PP2 128K 100G delta +1.36%
[PASS] N9: TP4/PP2 rows classified as HIGH NETWORK RESILIENCE
[PASS] N10: PR-002 43% compute
[PASS] N10: PR-003 26% compute
[PASS] N10: PR-003 weight streaming 27% BW
[PASS] N22: PR-002 artifact path profiler_out_0.txt
[PASS] N11: No duplicate mode badge line
[PASS] N13: No duplicate pointer in KD#7
[PASS] N14: No duplicate scenario chips
[PASS] N15: prMap covers all 7 datasets
[PASS] N16: No 'eliminates this 211 ms penalty'
[PASS] N16: No 'forces uniform routing to touch 163 of 256 experts'
[PASS] N17: Scheduler queue TP4/PP4 512K 0.016ms
[PASS] N17: Scheduler queue TP4/PP2 512K 0.023ms
[PASS] N17: Scheduler queue TP8/PP2 1M 0.038ms
[PASS] N17: Scheduler queue TP16 128K 0.019ms
[PASS] P7: GEMV tooltip 44.6ms faster
[PASS] P7: Operator card part order
[PASS] P8: D2H 56.5 GB/s
[PASS] P8: No 'mathematically certain'
[PASS] P10: 1.98x barrier latency
[PASS] P11: Campaign scope two-node decode
[PASS] P12: 8K TTFT AllReduce 54%
[PASS] P12: Single-node TP range 16-57%
[PASS] P13: 54% memory-speed floor label
[PASS] P16: PR-001 84,456 launches
[PASS] C1: 8 with usable exports
[PASS] C3: Chunk Pareto clarified
[PASS] KD#3: SendRecv 4.5x in hero
[PASS] KD#3: AllReduce 2.7x in hero
[PASS] KD#3: 16-rank aggregate chart title
[PASS] Coverage: TP4/PP2 decode incomplete status
[PASS] Coverage: TP4/PP2 batched incomplete status
[PASS] Coverage: TP16 decode incomplete status
[PASS] Coverage: TP16 512K incomplete status
[PASS] Coverage: Capped 20G planned prefill rows present
[PASS] Coverage: No fake capped 8K decode rows

Final Result: ALL 72 VERIFICATIONS PASSED (100%)!
```

---

## 6. Accessing the Dashboard

The dashboard is completely self-contained and can be viewed directly in any modern browser without a local web server:

```
file:///C:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html
```

Or via the root mirror:

```
file:///C:/Users/ayu23/OneDrive/Desktop/tpu/MASTER_CHARACTERIZATION_DASHBOARD_V4_5thOct_4amIST_V8_KIMI48B.html
```
