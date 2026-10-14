# Master Benchmark Campaign Orchestrator (`07_master_campaign_orchestration/`)

## Unified Master Benchmark Runner
This module contains the master orchestrator for executing the complete 20-step benchmark campaign across cluster nodes in an autonomous, end-to-end execution.

All benchmark phases are integrated directly into a single unified runner: **`run_master_benchmark.sh`**, with built-in checkpointing, idempotency, automated recovery, and strict **Cold vs. Warm Cache Isolation** between concurrency sweeps.

---

## Tool Catalog & Key Artifacts

| Tool / File | Type | Description |
|:---|:---:|:---|
| **`run_master_benchmark.sh`** | Bash Script | Unified master campaign orchestrator supervising all 20 benchmark steps across 4 run profiles. |
| **`RUN_COVERAGE.md`** | Reference | Comprehensive coverage reference detailing all steps, profiles, concurrencies, contexts, and profilers. |
| **`master_benchmark_cases.json`** | JSON Manifest | Unified benchmark cases declaration defining serving configurations, models, and batch parameters. |
| **`RUN_CONFIG.env.example`** | Env Template | Standardized environment template defining cluster IPs, SSH keys, topology filters, and virtualenv paths. |

---

## Run Profiles

| Profile | Flag | Approx. Duration | Steps Executed |
|:---|:---|:---:|:---:|
| **Smoke** | `--profile smoke` | ~10 min | Steps 00–01 (TP4 1k/8k c=1 sanity check) |
| **Fast Dashboard** | `--profile fast-dashboard` | ~2h | Steps 00–13 (Stage 1 + 2) |
| **Default** | `--profile default` (or `--all`) | ~9h | Steps 00–17 (All Standard Stages) |
| **Deep Profile** | `--profile deep-profile` | ~14h | Steps 00–20 (All + Deep Sweeps) |

---

## Execution Commands

### Execute via Predefined Profile
```bash
# Default standard campaign (~9h)
./run_master_benchmark.sh --profile default

# Exhaustive V8-parity deep profile (~14h)
./run_master_benchmark.sh --profile deep-profile
```

### Execute a Specific Step (e.g. Step 18 Poisson Sweep)
```bash
./run_master_benchmark.sh --step 18
```

### Resume After Power Cycle or Interruption
```bash
# Resumes automatically from the first uncompleted step via .done markers
export RESUME=1
./run_master_benchmark.sh
```

---

## 📖 Reference Guides
- Master Run Coverage Matrix (Steps 00-20): [`RUN_COVERAGE.md`](../../RUN_COVERAGE.md)
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](../../SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](../../PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
