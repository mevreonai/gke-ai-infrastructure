# V8 Raw Runs Vault — Empirical Cluster Output Guide

This folder contains the **authentic, immutable empirical measurements** downloaded directly from the dual-node GCP cluster (`kimi-node-0` and `kimi-node-1`) upon completion of the Stage 1 and Stage 2 characterization sweeps.

---

## 🗂 Vault Directory Structure

```
v8_full_results/raw_runs/
├── master_step_status.jsonl       # Master timeline ledger recording start/end time and exit codes
├── SUITE_SOURCE_SHA256SUMS.txt    # Cryptographic SHA256 hashes of all scripts executed on cluster
├── env/                           # Node environment snapshots (nvidia-smi, python versions, pip packages)
├── logs/                          # Top-level orchestrator terminal logs (ADDITIONAL_RUNS_MASTER.log)
├── stage1/                        # Raw outputs from Stage 1 (Steps 1 to 8)
└── stage2/                        # Raw outputs from Stage 2 (Steps 9 to 15)
```

---

## 🔬 What Each Test Folder Contains

### Stage 1: Quick-Win Microbenchmarks (`stage1/`)

| Folder | What Was Tested | Key Output File |
| :--- | :--- | :--- |
| **`01_chunk_budget_ab/`** | Chunked prefill evaluation (512 vs 2048/8192 chunk budgets) | `chunk_budget_results.json` |
| **`02_torch_profiles_batched/`** | PyTorch Kineto operator timelines under concurrency ($c=8, 32$) | `trace_c8.pt.trace.json`, `trace_c32.pt.trace.json` |
| **`03_nccl_tuning/`** | Inter-node TCP socket tuning on `ens3` (MTU 1460) | `all_reduce_16k.json`, `sendrecv_256m.json` |
| **`04_tp8_pinning/`** | NUMA socket core affinity impact on host-to-device transfers | `pinning_evaluation.json` |
| **`05_short_prompts/`** | Short context baseline floors (1K, 2K, 4K prompt lengths) | `tp4_short_prompts/1k_c1/METRICS_COMMAND.txt` |
| **`06_chunk_and_knee_repeats/`** | 128K chunk sensitivity sweeps & throughput knee repeatability | `128k_c1/METRICS_COMMAND.txt` |
| **`07_kv_pool_and_trace_audit/`** | VRAM KV cache block pool allocation & trace trimming | `kv_audit.json` |

---

### Stage 2: Scale-Out & Diagnostic Sweeps (`stage2/`)

| Folder | What Was Tested | Key Output File |
| :--- | :--- | :--- |
| **`01_fp8_kv_rerun/`** | FP8 KV cache execution & root-cause analysis (SM100 architecture requirement) | `stderr.log` *(contains SM100 assertion traceback)* |
| **`02_cpu_offload_reuse/`** | Host DDR5 RAM offload tiering & 600K revisit latency penalty | `offload_revisit_a/METRICS_COMMAND.txt` *(41.39s TTFT)* |
| **`03_multi_node_load/`** | Multi-node concurrency stress ($c=1, 2, 4$) across 128K, 512K, and 1M tokens | `multi_node_1m_c4.json` *(TP4/PP4 2.4× speedup)* |
| **`04_pp2_split_evaluation/`** | Pipeline parallel 2-stage layer rebalance (15/12 split vs 14/13 split) | `pp2_comparison.csv` *(+1.18% TPOT speedup)* |
| **`05_capped_profiles/`** | Context-capped Nsight Systems profiling (32K tokens) | `cuda_gpu_kern_sum.csv`, `nvtx_pushpop_sum.csv` |
| **`06_tp16_512k_prefill/`** | Cross-node TP16 512K prefill feasibility evaluation | `node0_capture/`, `node1_capture/` |

---

## 🔍 How to Read the Execution Receipts

To verify that all benchmarks completed successfully without opening dozens of subfolders, inspect `master_step_status.jsonl`:

```bash
cat master_step_status.jsonl
```

Each line records:
```json
{"step": "run_stage1", "rc": 0, "start": 1791247104, "end": 1791248294}
{"step": "run_stage2", "rc": 0, "start": 1791287444, "end": 1791293911}
```
* `rc: 0` confirms that the benchmark suite ran to completion with exit code 0.
