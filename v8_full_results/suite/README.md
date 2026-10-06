# V8 Benchmark Suite — Beginner Quickstart & Runner Guide

Welcome! This folder contains all the executable test scripts, case matrices, and launch tools to run the **V8 Characterization Suite** (Stage 1 & Stage 2) for `Kimi-Linear-48B` on dual RTX PRO 6000 Ada/Blackwell servers.

---

## 🚀 30-Second Quickstart (For Complete Beginners)

You only need to do **two steps** to start the entire benchmark run:

### Step 1: Set Your Node IPs
Open [`RUN_CONFIG.env`](file:///v8_full_results/suite/RUN_CONFIG.env) in any text editor and change the two IP addresses to match your cloud VM private IPs:

```bash
export NODE0_IP="10.240.0.10"   # <-- Replace with Node 0 Private IP
export NODE1_IP="10.240.0.11"   # <-- Replace with Node 1 Private IP
```

*(Alternatively, you don't even have to edit the file—you can just pass the IPs directly on the command line in Step 2!)*

### Step 2: Run the Benchmark
Run this single command:

```bash
# If you edited RUN_CONFIG.env:
bash run_quickstart.sh

# OR pass the IPs directly on the command line:
bash run_quickstart.sh 10.240.0.10 10.240.0.11
```

That's it! The script will automatically:
1. Verify CUDA, drivers, and network connectivity between nodes.
2. Run Stage 1 (Quick-win microbenchmarks, chunking tests, socket tuning).
3. Run Stage 2 (Multi-node concurrency sweeps, pipeline layer balancing, extreme 1M context tests).
4. Save clean execution receipts into `master_step_status.jsonl`.

---

## 🎛 Common Run Options

| If you want to... | Run this command: |
| :--- | :--- |
| **Run Everything (Stage 1 + Stage 2)** | `bash run_quickstart.sh` |
| **Run Stage 1 Only (~2 hours)** | `bash run_quickstart.sh --stage1-only` |
| **Run Stage 2 Only (~3.5 hours)** | `bash run_quickstart.sh --stage2-only` |
| **Resume an interrupted run** | `bash run_quickstart.sh` *(automatically resumes from last checkpoint)* |
| **Force a clean new run from scratch** | `bash run_quickstart.sh --new-run` |

---

## 📂 File Inventory: What Each File Does

```
v8_full_results/suite/
├── RUN_CONFIG.env.example         # Template configuration (copy to RUN_CONFIG.env)
├── RUN_CONFIG.env                 # Active IP and cluster configuration (EDIT THIS!)
├── run_quickstart.sh              # 1-Click beginner wrapper script
├── 00_run_master_additional_runs.sh # Master supervisor script that sequences everything
├── 01_run_stage1_quick_wins.sh    # Runner for Stage 1 (Steps 1–8: chunking, socket tuning, KV audits)
├── 02_run_stage2_failed_and_scaleout.sh # Runner for Stage 2 (Steps 9–15: multi-node, PP2 rebalance, 1M context)
├── stage1_cases.json              # Test parameters for Stage 1
├── stage2_cases_single_node.json  # Single-node 1M token test definitions
├── stage2_cases_multi_node_load.json # Multi-node TP4/PP4 test definitions
├── README_FOR_BOSS_APPROVAL.md    # Executive proposal submitted prior to VM execution
├── PILOT_STAGE1_ANALYSIS_RESULTS.json # Pilot run baseline data
├── rtx_g4_smoke_v5/               # Helper tools (telemetry collector, Ray checkers, profilers)
└── rtx_g4_smoke_v8_hw/            # Hardware stress tools (PCIe, bandwidth, thermal burn-in)
```

---

## 🔧 Frequently Asked Questions & Troubleshooting

### Q: Where do the outputs go?
**A:** Outputs are saved in `v8_full_results/raw_runs/` (or `~/v8_additional_runs/<RUN_ID>/` on the VM). You will see real-time updates in `master_step_status.jsonl`.

### Q: What if a step fails or is interrupted?
**A:** You do not have to restart from scratch! Just re-run `bash run_quickstart.sh`. It checks `.done/<step_name>` markers and automatically picks up right where it left off.

### Q: How do I verify the cluster before running long benchmarks?
**A:** Run the fast preflight check:
```bash
python3 rtx_g4_smoke_v5/07_preflight_v5.py
```
If it reports all green, your GPUs, drivers, and Ray cluster are ready to run.
