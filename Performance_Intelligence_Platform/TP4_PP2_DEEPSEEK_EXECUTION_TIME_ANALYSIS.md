# Execution Time Analysis: TP4/PP2 on DeepSeek Model Across All Concurrencies & Network Topologies (Including SQLite, Nsys & PyTorch Trace Generation)

**Document ID:** `PIP-TIME-TP4PP2-DEEPSEEK-PROFILED-20261016`  
**Target Topology:** `TP4/PP2` (8× GPUs: 4 GPUs on `kimi-node-0`, 4 GPUs on `kimi-node-1`)  
**Target Architecture:** `DeepSeek-V4.1-Flash` (FP8 MoE) / `Kimi-Linear-48B-A3B-Instruct`  
**Cluster Interconnect:** Dual-Node 100 Gbps Google Cloud Andromeda VPC (Native RoCEv2 vs. 100G Capped vs. 20G Capped)  
**Execution Platform:** [Performance Intelligence Platform (PIP)](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform)  
**Profile Artifacts Generated in Run:** NVIDIA Nsight Systems (`.nsys-rep`), Exported Timeline Databases (`.sqlite`), and PyTorch Chrome Traces (`.pt.trace.json.gz`)  
**Automated Campaign Script:** [`scripts/run_tp4pp2_deepseek_profiled_campaign.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/run_tp4pp2_deepseek_profiled_campaign.sh)  

---

## 1. Executive Summary & Total Run Time Matrix

When the benchmark run includes **all concurrency sweeps** ($c=1, 2, 4, 8, 32$), **all context lengths** (1K, 8K, 128K, 512K, 1M), AND **deep profiling captures** (Nsight Systems profiles, SQLite database exports, and multi-node PyTorch Chrome traces), the total wall-clock execution time is:

| Network Configuration | Standard Serving Benchmarks | Multi-Node PyTorch Tracing | Nsys Profiles & SQLite Exports | Server JIT & Cooldown | Total Wall-Clock Execution Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **GCP Native (175G RoCEv2 / Native VPC)** | ~17.7 min | ~5.0 min | ~23.5 min | ~5.5 min | **~51.7 minutes (~0.86 hours)** |
| **GCP Capped 100G (100 Gbps Interconnect)** | ~18.0 min | ~5.2 min | ~24.1 min | ~5.5 min | **~52.8 minutes (~0.88 hours)** |
| **GCP Capped 20G (20 Gbps Standard VPC)** | ~19.6 min | ~5.6 min | ~26.4 min | ~5.5 min | **~57.1 minutes (~0.95 hours)** |
| **ALL THREE Combined (Native + 100G + 20G)** | **~55.3 min** | **~15.8 min** | **~74.0 min** | **~16.5 min** | **~161.6 minutes (~2h 42m)** |

> [!IMPORTANT]
> **Comparison with Pure Serving (No Traces):**
> * A **pure serving run** (benchmarks only, no traces) takes **~21.6 minutes** on Native.
> * A **fully profiled run** (benchmarks + `.nsys-rep` + `.sqlite` + `.pt.trace`) takes **~51.7 minutes** on Native (+30 minutes for deep profiling and trace database conversion across 8 GPU ranks).
> * Running **all three network modes** with full profiling and trace generation takes **~2 hours 42 minutes**.

---

## 2. Granular Time Breakdown by Phase

### Phase 1: Full Concurrency & Context Serving Benchmarks (~17.7 min)
Amortized under a single vLLM server session running production CUDA Graphs across all 16 canonical `TP4/PP2` benchmark points:

| Context Horizon | Concurrency Grid ($c$) | Prompts Tested | GCP Native | GCP Capped 100G | GCP Capped 20G | Phase Details |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1K Tokens** | $c=1, 8, 32$ | 220 prompts | **16.2s** | 16.5s | 17.2s | TTFT floor (~24 ms) and queue throughput |
| **8K Tokens** | $c=1, 8, 32$ | 172 prompts | **73.3s** | 74.7s | 78.9s | Standard production conversational load |
| **128K Tokens** | $c=1, 2, 4, 8$ | 74 prompts | **346.2s (~5.8m)** | 350.5s (~5.8m) | 371.0s (~6.2m) | Chunked prefill (8,192 tokens/chunk) |
| **512K & 1M Tokens** | $c=1, 2, 4$ | 22 prompts | **626.6s (~10.4m)**| 632.4s (~10.5m)| 668.2s (~11.1m)| Activation transfers across PP boundaries |
| **Subtotal Phase 1** | — | **488 prompts** | **~17.7 min** | **~18.0 min** | **~19.6 min** | Generates raw latency & throughput JSONs |

---

### Phase 2: Multi-Node Distributed PyTorch Chrome Tracing (~5.0 min)
Executed via [`14d_run_vllm_torch_profile_multi_node.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/06_deep_kernel_and_torch_profiling/14d_run_vllm_torch_profile_multi_node.sh):
* Launches distributed Ray cluster across Node 0 and Node 1.
* Boots `DeepSeek-V4.1-Flash` with `--profiler-config` enabled.
* Reaches steady-state decode at $c=1$ and $c=8$.
* Fires `/start_profile`, captures 4.0 seconds of kernel execution across all 8 GPU ranks, and fires `/stop_profile`.
* Automatically retrieves and aggregates traces from Node 1 via SCP.
* **Output:** Produces 8 rank Chrome trace files (`*.pt.trace.json.gz`), viewable in Chrome (`chrome://tracing`) or Perfetto.
* **Duration:** ~2.5 min for $c=1$ + ~2.5 min for $c=8$ = **~5.0 minutes**.

---

### Phase 3: Nsight Systems Profiling & SQLite Database Exports (~23.5 min)
Executed via [`18_run_vllm_multi_node_profiles.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/rtx_g4_smoke_v5/18_run_vllm_multi_node_profiles.sh) and [`19_postprocess_nsys.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/rtx_g4_smoke_v5/19_postprocess_nsys.py):
Captures representative kernel profiles across the execution spectrum:
1. `decode_8k` ($c=1$, prompt=8192, gen=512)
2. `batched_decode_8k_c8` ($c=8$, prompt=8192, gen=512)
3. `prefill_128k` ($c=1$, prompt=131072, gen=8)
4. `extreme_prefill_1m` ($c=1$, prompt=1000000, gen=8)

For each profile mode:
* vLLM launches with `--ray-workers-use-nsight` (launches `nsys profile` per worker rank).
* Executes benchmark and flushes traces: ~1.5 to 2.5 min.
* Trace collection from Node 1: ~30s.
* **Automated SQLite Conversion:** `nsys export --type sqlite` executed across all 8 rank `.nsys-rep` captures: ~1.5 to 2.5 min.
* **Output:** Generates both the `.nsys-rep` GUI profile and the structured `.sqlite` SQL database for timeline querying.
* **Subtotal for 4 profile modes:** **~23.5 minutes**.

---

## 3. Directory Layout of Generated Traces in the Run

When [`run_tp4pp2_deepseek_profiled_campaign.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/run_tp4pp2_deepseek_profiled_campaign.sh) completes, the run directory contains:

```
$HOME/pip_runs/tp4_pp2_deepseek_<TIMESTAMP>/
├── CAMPAIGN_MANIFEST.json             <-- Overall run manifest with wall-clock time
├── native/                            <-- (or capped_100g / capped_20g)
│   ├── benchmarks/                    <-- All 16 benchmark latency JSONs (1k..1m, c=1..32)
│   ├── sqlite_traces/                 <-- All exported *.sqlite databases ready for SQL analysis
│   │   ├── tp4_pp2_decode_8k_rank0..7.sqlite
│   │   ├── tp4_pp2_batched_decode_8k_c8_rank0..7.sqlite
│   │   ├── tp4_pp2_prefill_128k_rank0..7.sqlite
│   │   └── tp4_pp2_extreme_prefill_1m_rank0..7.sqlite
│   ├── nsys_profiles/                 <-- All *.nsys-rep files loadable in Nsight Systems GUI
│   │   ├── node0_capture/*.nsys-rep
│   │   └── node1_capture/*.nsys-rep
│   └── pytorch_traces/                <-- All *.pt.trace.json.gz Chrome timeline traces
│       ├── c1/torch/node0/*.pt.trace.json.gz
│       ├── c1/torch/node1/*.pt.trace.json.gz
│       ├── c8/torch/node0/*.pt.trace.json.gz
│       └── c8/torch/node1/*.pt.trace.json.gz
```

---

## 4. How to Execute the Profiled Campaign

Run the turnkey script to generate all benchmark data, SQLite databases, Nsys profiles, and PyTorch traces:

```bash
# Option 1: Run Native mode only (~51.7 minutes total)
bash scripts/run_tp4pp2_deepseek_profiled_campaign.sh <NODE1_IP> --network native

# Option 2: Run Capped 100G only (~52.8 minutes total)
bash scripts/run_tp4pp2_deepseek_profiled_campaign.sh <NODE1_IP> --network capped_100g

# Option 3: Run Capped 20G only (~57.1 minutes total)
bash scripts/run_tp4pp2_deepseek_profiled_campaign.sh <NODE1_IP> --network capped_20g

# Option 4: Run ALL THREE sequentially (~2h 42m total)
bash scripts/run_tp4pp2_deepseek_profiled_campaign.sh <NODE1_IP> --network all
```
