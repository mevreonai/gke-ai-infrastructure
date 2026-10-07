# Master Benchmark Campaign Orchestrator (`07_master_campaign_orchestration/`)

## Unified Master Benchmark Runner
This module contains the unified orchestrator for executing the complete 15-step benchmark campaign across both nodes in an autonomous, end-to-end execution.

All benchmark phases are integrated directly into a single unified runner: **`run_master_benchmark.sh`**. There are no separate or disjoint stage runners; every step executes sequentially with built-in checkpointing, idempotency, and automated recovery.

---

## Tool Catalog & Key Artifacts

| Tool / File | Type | Description |
|:---|:---:|:---|
| **`run_master_benchmark.sh`** | Bash Script | Unified master campaign orchestrator supervising all 15 benchmark steps sequentially (~21.5h runtime). |
| **`master_benchmark_cases.json`** | JSON Manifest | Unified benchmark cases declaration defining serving configurations, models, and batch parameters. |
| **`RUN_CONFIG.env.example`** | Env Template | Standardized environment template defining cluster IPs, SSH keys, and virtualenv paths. |

---

## Execution Commands

### Execute All 15 Steps End-to-End
```bash
chmod +x run_master_benchmark.sh
nohup ./run_master_benchmark.sh --all > ../../data/raw_runs/master_campaign_stdout.log 2>&1 &
echo "Campaign running with PID $!"
```

### Execute a Specific Step (e.g. Step 4 NUMA Pinning)
```bash
./run_master_benchmark.sh --step 4
```

### Resume After Power Cycle or Interruption
```bash
# Resumes automatically from the first uncompleted step
export RESUME=1
./run_master_benchmark.sh
```
