# 07. Master Orchestration & Benchmark Stage Runners

## 🎯 Purpose & Scope
Hosts the supervisory campaign harnesses capable of autonomously orchestrating multi-hour, multi-step benchmarking campaigns with automated crash recovery and state resumption.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `00_run_master_additional_runs.sh`
* **Purpose:** The master campaign orchestrator supervising all 15 benchmark steps (~21.5 hours total runtime).
* **Key Features:**
  - Watchdog daemon monitoring GPU health and memory leaks.
  - Step resumption: `export PLATFORM_RESUME=1` skips completed steps and resumes from failures.
  - Inter-step cooldown: 120s pause between steps with GPU memory flushes and cache clearing.
* **Usage:**
  ```bash
  nohup ./00_run_master_additional_runs.sh > master_stdout.log 2>&1 &
  ```

### 2. `01_run_stage1_quick_wins.sh`
* **Purpose:** Executes Stage 1 Quick-Wins (Steps 01 to 08: ~5h 23m wall-clock duration).
* **Steps:** Chunked prefill sizing, profiler dilation, NCCL tuning, NUMA affinity, short prompt scaling, 128K context, KV trim, APC eviction.
* **Usage:**
  ```bash
  ./01_run_stage1_quick_wins.sh
  ```

### 3. `02_run_stage2_failed_and_scaleout.sh`
* **Purpose:** Executes Stage 2 Deep Scaleout & Remediation (Steps 09 to 15: ~12h 50m wall-clock duration).
* **Steps:** FP8 quantization RCA, host CPU KV-cache offload, 1M stress, PP 15/12 rebalance, capped profiles, TP16 512K serving, full timeline Nsight capture.
* **Usage:**
  ```bash
  ./02_run_stage2_failed_and_scaleout.sh
  ```

### 4. Case Manifests:
- `stage1_cases.json`: Test parameters for Stage 1 workloads.
- `stage2_cases_multi_node_load.json`: Distributed multi-node test parameters.
- `stage2_cases_single_node.json`: Concurrency and memory stress parameters.
