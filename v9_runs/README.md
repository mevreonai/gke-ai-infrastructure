# V9 Full Characterization Runs & Benchmark Repository

## Overview
This repository contains the complete empirical data, test execution guides, coverage manifests, and interactive dashboard for the **V9 Characterization Campaign** targeting:
- **Workload**: `moonshotai/Kimi-Linear-48B-A3B-Instruct`
- **Cluster Architecture**: 2-Node GCP Cluster (2 × `g4-standard-384`, 16 × NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs, 1,536 GB aggregate GDDR7 VRAM, 768 host vCPUs)
- **Engine**: vLLM distributed with Ray orchestration and NCCL transport

---

## Directory Organization
- `dashboard/`:
  - `MASTER_CHARACTERIZATION_DASHBOARD_V9.html`: Fully interactive HTML dashboard strictly populated with V9 empirical data.
  - `index.html`: Entry point for hosting or local web viewing.
  - `v9_data.json`: Compiled JSON feed containing all 121 empirical run records.
- `data/`:
  - `v9_test2_combined_vllm_runs.csv`: 121 completed empirical runs with TTFT, TPOT, throughput, and latency percentiles across context lengths (1K to 1M) and network modes (Native vs 20G).
  - `v9_test2_coverage.csv`: Matrix execution audit (121 COMPLETED, 2 CAPABILITY_BLOCKED).
- `V9_FULL_CHARACTERIZATION_RUNS_AND_TIMINGS_GUIDE.md`: Comprehensive 3-Tier testing blueprint.
- `V9_THREE_TESTS_EXECUTION_AND_TIMINGS_GUIDE.md`: Execution timings and preflight instructions.

---

## Execution Status & Testing Tiers
1. **TEST 1 (Preflight & Smoke)**: ✅ COMPLETE (`v9_smoke_results/`).
2. **TEST 2 (Core Inference Benchmark)**: ✅ COMPLETE (121 runs in `v9_test2_results/`).
   - Run without active profilers to preserve unperturbed serving latency.
   - 2 Probes (`tp4_kv_fp8_probe`, `tp4_offload_probe`) classified as `CAPABILITY_BLOCKED` due to hybrid attention prefill query quantization and block hash alignment constraints.
3. **TEST 3 (Deep Nsight & PyTorch Profiler Suite)**: ⏳ Separate 12–16h run (reserved for kernel breakdowns and trace analysis).
