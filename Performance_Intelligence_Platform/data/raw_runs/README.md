# Platform Raw Runs Vault — Empirical Cluster Output Guide

This folder contains the **authentic, immutable empirical measurements** downloaded directly from the dual-node GCP cluster (`v8-smoke-node-0` and `v8-smoke-node-1`) upon completion of the characterization sweeps.

---

## 🗂 Vault Directory Structure

```text
Performance_Intelligence_Platform/data/raw_runs/
├── master_step_status.jsonl       # Master timeline ledger recording start/end time and exit codes
├── SUITE_SOURCE_SHA256SUMS.txt    # Cryptographic SHA256 hashes of all scripts executed on cluster
├── env/                           # Node environment snapshots (nvidia-smi, python versions, pip packages)
├── logs/                          # Top-level orchestrator terminal logs (MASTER_BENCHMARK_RUN.log)
├── stage1/                        # Raw outputs from Stage 1 (Steps 1 to 7)
├── stage2/                        # Raw outputs from Stage 2 (Steps 8 to 13)
├── stage3/                        # Raw outputs from Stage 3 (Steps 14 to 15: Nsight & Chrome traces)
└── stage4/                        # Raw outputs from Stage 4 (Steps 16 to 17: Waves, Stalls & Continuous Batching)
```

---

## 🔬 What Each Test Folder Contains

### Stage 1: Quick-Win Microbenchmarks (`stage1/`)

| Folder | What Was Tested | Key Output File |
| :--- | :--- | :--- |
| **`01_chunk_budget_ab/`** | Chunked prefill evaluation (8192 control vs 8448 fix chunk budget) | `chunk_budget_results.json` |
| **`02_torch_profiles_batched/`** | PyTorch Kineto operator timelines under concurrency ($c=8, 32$) | `trace_c8.pt.trace.json`, `trace_c32.pt.trace.json` |
| **`03_nccl_tuning/`** | Inter-node TCP socket tuning on `ens3` (MTU 1460) | `nccl_tests.log`, `allreduce.json` |
| **`04_tp8_pinning/`** | NUMA socket core affinity impact on host-to-device transfers | `PINNING_COMPARISON.json` |
| **`05_short_prompts/`** | Short context baseline floors (1K, 2K, 4K prompt lengths) | `tp4_short_prompts/1k_c1/1k_c1.json` |
| **`06_chunk_and_knee_repeats/`** | 128K chunk sensitivity sweeps & throughput knee repeatability | `128k_c1/128k_c1.json` |
| **`07_kv_pool_and_trace_audit/`** | VRAM KV cache block pool allocation & trace trimming | `KV_POOL_AUDIT.json` |

---

### Stage 2: Scale-Out & Diagnostic Sweeps (`stage2/`)

| Folder | What Was Tested | Key Output File |
| :--- | :--- | :--- |
| **`08_fp8_kv_rerun/`** | FP8 KV cache execution & memory capacity bounds | `summary/vllm_runs.csv` |
| **`09_cpu_offload_reuse/`** | Host DDR5 RAM offload tiering & multi-turn prefix reuse | `summary/vllm_runs.csv` |
| **`10_multi_node_load/`** | Multi-node concurrency stress ($c=1..8$) across TP16, TP8+PP2, TP4+PP4 | `summary/vllm_runs.csv` |
| **`11_pp2_split_evaluation/`** | Pipeline parallel 2-stage layer rebalance (15/12 split vs default) | `summary/vllm_runs.csv` *(+27.58% TTFT speedup)* |
| **`12_capped_profiles/`** | Network resilience sweeps (Native vs 100G vs 20G vs 0.05% loss) | `RESILIENCE_COMPARISON.json` |
| **`13_tp16_512k_prefill/`** | Cross-node TP16 512K prefill feasibility evaluation | `node0_capture/`, `node1_capture/` |

---

### Stage 3: Deep Kernel Timelines (`stage3/`)

| Folder | What Was Tested | Key Output File |
| :--- | :--- | :--- |
| **`14_timeline_profiles/`** | Nsight Systems & PyTorch Chrome traces (B1 CUDA graphs decode critical path) | `*.nsys-rep`, `timeline.sqlite`, `torch_trace_batched.json` |
| **`15_canonical_aggregation/`** | Post-execution telemetry aggregation & 72-rule invariant audit | `audit_report.json` |

---

### Stage 4: Waves, Stalls & Continuous Batching (`stage4/`)

| Folder | What Was Tested | Key Output File |
| :--- | :--- | :--- |
| **`16_waves_stalls/`** | Request wave decomposition, burst shares, and stall detections (>100ms) | `PAUSE_AND_STALL_SCAN.csv`, `BENCH_SUMMARY_WAVES.txt` |
| **`17_continuous_batching/`** | Continuous Batching characterization across Blocks 1 to 7 | `continuous_batching_manifest.json`, `RESULT_SUMMARY.md`, `pause_scan.csv` |

---

## 🔍 How to Read the Execution Receipts

To verify that all benchmarks completed successfully without opening dozens of subfolders, inspect `master_step_status.jsonl`:

```bash
cat master_step_status.jsonl
```

Each line records:
```json
{"step_num": 1, "step_name": "chunk_budget_ab", "rc": 0, "dry_run": false, "start": 1791247104, "end": 1791248294}
{"step_num": 17, "step_name": "continuous_batching_characterization", "rc": 0, "dry_run": false, "start": 1791287444, "end": 1791293911}
```
* `rc: 0` confirms that the benchmark step ran to completion with exit code 0.
