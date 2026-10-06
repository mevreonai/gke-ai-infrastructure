# V8 Master Characterization Campaign — Kimi-Linear-48B

This directory contains the **consolidated, complete, and audited empirical dataset**, execution tools, raw cluster measurements, and interactive dashboards for the **vLLM V8 Characterization Campaign** (`Kimi-Linear-48B` on dual RTX PRO 6000 Ada/Blackwell servers).

---

## ⚡ 1-Minute Quickstart: How to Run the Benchmark

Anyone can re-run this benchmark suite in two simple steps:

### Step 1: Set Your Node IPs
Open [`suite/RUN_CONFIG.env`](file:///v8_full_results/suite/RUN_CONFIG.env) and set your two private cloud IPs:

```bash
export NODE0_IP="10.240.0.10"   # <-- Replace with Node 0 Private IP
export NODE1_IP="10.240.0.11"   # <-- Replace with Node 1 Private IP
```

### Step 2: Launch the Benchmark
Execute the beginner-friendly runner script:

```bash
cd suite
bash run_quickstart.sh
```

*(Or pass the IPs directly on the command line: `bash run_quickstart.sh 10.240.0.10 10.240.0.11`)*

---

## 🗂 Unified Directory Layout

Everything related to V8 is contained cleanly in this directory:

```
v8_full_results/
├── dashboards/                  <-- INTERACTIVE PRESENTATION DASHBOARDS
│   └── v4_dashboard/
│       ├── MASTER_CHARACTERIZATION_DASHBOARD.html # Standalone master dashboard (3.7 MB)
│       ├── DASHBOARD_CANONICAL_DATA.json          # Structured dataset powering the UI
│       ├── index.html                             # Web server production mirror
│       └── time_budget/                           # High-resolution time-budget PNGs & CSVs
│
├── suite/                       <-- EXECUTABLE BENCHMARK SUITE & RUNNERS
│   ├── RUN_CONFIG.env           # Edit this file to change IPs!
│   ├── run_quickstart.sh        # Beginner 1-click execution script
│   ├── 00_run_master_additional_runs.sh # Master test supervisor
│   ├── 01_run_stage1_quick_wins.sh      # Stage 1 runner (Steps 1–8)
│   ├── 02_run_stage2_failed_and_scaleout.sh # Stage 2 runner (Steps 9–15)
│   ├── stage1_cases.json        # Test case matrices
│   ├── stage2_cases_*.json      # Scale-out matrices
│   └── README.md                # Detailed guide for the suite folder
│
├── raw_runs/                    <-- AUTHENTIC DOWNLOADED CLUSTER EVIDENCE
│   ├── master_step_status.jsonl # Complete execution timeline and exit codes (rc: 0)
│   ├── stage1/                  # Raw logs, CSVs, and JSONs for Steps 1–8
│   ├── stage2/                  # Raw logs, traces, and CSVs for Steps 9–15
│   └── README.md                # Detailed guide for the raw evidence vault
│
├── combined_vllm_runs.csv       <-- Canonical baseline 126-run tabular dataset
├── release_specs/               <-- Frozen release snapshots and verification artifacts
└── results/                     <-- Hardware benchmark outputs and coverage audits
```

---

## 🧭 Sub-Folder Guides

For deep-dive documentation on each specific folder, refer to its dedicated README:

- 📘 [**Suite & Runner Documentation**](file:///v8_full_results/suite/README.md): Instructions on flags, environment variables, and preflight checks.
- 📙 [**Raw Runs & Measurement Evidence**](file:///v8_full_results/raw_runs/README.md): Detailed breakdown of each step folder and how to verify exit codes.
- 📕 [**Interactive Dashboard Guide**](file:///v8_full_results/dashboards/v4_dashboard/README.md): How to open the dashboard locally, explore tabs, and verify data.
- 📗 [**Master Architecture & Mathematical Guide**](file:///README_V8_SUITE_AND_DASHBOARD_GUIDE.md): Complete 1,589-line reference guide covering tensor math, script-by-script inventory, and the 72-rule verification suite.
