# Master Benchmark Campaign Orchestrator (`07_master_campaign_orchestration/`)

## Unified Master Benchmark Runner
This module contains the master orchestrator for executing the complete 17-step benchmark campaign across both nodes in an autonomous, end-to-end execution.

All benchmark phases are integrated directly into a single unified runner: **`run_master_benchmark.sh`**. There are no separate or disjoint stage runners; every step executes sequentially with built-in checkpointing, idempotency, and automated recovery.

---

## Tool Catalog & Key Artifacts

| Tool / File | Type | Description |
|:---|:---:|:---|
| **`run_master_benchmark.sh`** | Bash Script | Unified master campaign orchestrator supervising all 17 benchmark steps sequentially (~8h 55m runtime). |
| **`master_benchmark_cases.json`** | JSON Manifest | Unified benchmark cases declaration defining serving configurations, models, and batch parameters. |
| **`RUN_CONFIG.env.example`** | Env Template | Standardized environment template defining cluster IPs, SSH keys, topology filters, and virtualenv paths. |

---

## Execution Commands

### Execute All 17 Steps End-to-End
```bash
chmod +x run_master_benchmark.sh
nohup ./run_master_benchmark.sh --all > ../../data/raw_runs/master_campaign_stdout.log 2>&1 &
echo "Campaign running with PID $!"
```

### Execute a Specific Step (e.g. Step 4 NUMA Pinning)
```bash
./run_master_benchmark.sh --step 4
```

### Execute Specific Topology & Stage Selections
```bash
# Run only TP4 topologies on Stage 1
./run_master_benchmark.sh --topologies tp4_pp1,tp4_pp2 --stage 1
```

### Resume After Power Cycle or Interruption
```bash
# Resumes automatically from the first uncompleted step via .done markers
export RESUME=1
./run_master_benchmark.sh
```

---

## 📖 Reference Guides
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
