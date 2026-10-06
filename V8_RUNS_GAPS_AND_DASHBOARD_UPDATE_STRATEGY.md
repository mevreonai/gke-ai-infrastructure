# V8 Campaign Characterization: Run Inventory, Failure Audit & Dashboard Modernization Strategy

> **Document Status**: Authoritative Engineering Reference & Execution Strategy  
> **Target Campaign**: V8 Pilot Benchmark Suite (`run_id: 20260921_195656`)  
> **Hardware Architecture**: Dual-Node NVIDIA RTX 6000 Ada Cluster (16× 96GB GPUs, AMD EPYC 9654, PCIe Gen4/5, MTU 8896 VPC)  
> **Model Surrogate**: Moonshot AI Kimi-Linear-48B-A3B-Instruct (MLA, 27 Layers, 20 KDA, 7 Full-Attention, 256 Routed MoE Experts, BF16, 1M Max Length)  
> **Primary Sources**: [`V8_Gaps_and_Rerun_Plan_v1.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V8_Gaps_and_Rerun_Plan_v1.md), [`V8_Gaps_and_Rerun_Plan_v1.3.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V8_Gaps_and_Rerun_Plan_v1.3.md), [`V8_MISSED_RUNS_AUDIT.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V8_MISSED_RUNS_AUDIT.md), [`FINAL_VALIDATION.json`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/final_validation/FINAL_VALIDATION.json).

---

## 1. Initial V8 Campaign: Configured vs. Executed Runs

The original V8 campaign was scoped to characterize single-node and multi-node serving performance across context lengths scaling from 8K to 1M tokens.

```
Total Planned Runs: 126 Application Serving Runs + 22 Distributed Nsight Profiles
├── Application Runs: 119 COMPLETED (94.4%) | 7 NOT_RUN (5.6%) | 0 Mid-Flight Crashes
└── Profiler Runs:    14 COMPLETED (63.6%) | 8 NON-COMPLETE (36.4%)
```

### 1.1 Initial Application Matrix Breakdown (126 Planned Runs)

| Scope | Topology | Contexts | Load & Concurrency | Special Configurations | Planned Count | Completed |
|---|---|---|---|---|---:|---:|
| **Single-Node Matrix** | `TP4 / PP1` | 8K, 128K, 512K, 1M | $c=1, 4, 8, 16, 32, 64$ | Closed-loop & Open-loop ($0.25\times \dots 1.0\times$) | 42 | 42 |
| **Single-Node Matrix** | `TP8 / PP1` | 8K, 128K, 512K, 1M | $c=1, 4, 8, 16, 32, 64$ | Closed-loop & Open-loop ($0.25\times \dots 1.0\times$) | 36 | 36 |
| **Knob Sensitivity** | `TP4` & `TP8` | 128K, 512K, 1M | $c=1, 4$ | `max_num_seqs` sweeps, prefix-caching toggles | 12 | 12 |
| **Scale-Out Native** | `TP4/PP2`, `TP8/PP2`, `TP4/PP4`, `TP16/PP1` | 128K, 512K, 1M | $c=1$ | `GCP_NATIVE` (~174 Gbps VPC) | 12 | 12 |
| **Scale-Out 100G Cap** | 4 Distributed Topologies | 128K, 512K, 1M | $c=1$ | `GCP_CAPPED_100G` (~57 Gbps shaped) | 12 | 12 |
| **Scale-Out 20G Cap** | 4 Distributed Topologies | 128K, 512K, 1M | $c=1$ | `GCP_CAPPED_20G` (~16.5 Gbps shaped) | 12 | 12 |
| **Experimental: FP8 KV** | `TP4 / PP1` | 128K, 512K, 1M | $c=1, 4$ | `--kv-cache-dtype fp8` | 4 | **0 (NOT_RUN)** |
| **Experimental: Offload** | `TP4 / PP1` | 128K, 512K, 1M | $c=1$ | `--kv-offloading-size 32` (Host DRAM) | 3 | **0 (NOT_RUN)** |
| **Total** | | | | | **126** | **119** |

---

## 2. Root Cause Audit: What Failed and Why

No benchmarks crashed mid-execution. All non-completions fell into two distinct categories: **vLLM server startup rejections** and **profiler export teardown races**.

### 2.1 The 7 Application Runs That Failed to Start (`NOT_RUN`)

#### Group A: FP8 KV-Cache Initialization Assertion (4 Runs)
* **Affected Cases**: `tp4_fp8_kv` (`128k_c1`, `128k_c4`, `512k_c1`), `tp4_fp8_kv_1m` (`1m_c1`).
* **Symptom**: Server exited with code 1 during pre-warmup piecewise CUDA graph capture.
* **Exact Log Trace**:
  ```text
  (Worker_TP3 pid=291580) File ".../vllm/models/kimi_k3/nvidia/mla.py", line 1024, in _forward_prefill_fused
  (Worker_TP3 pid=291580)   assert fp8_prefill, (
  (Worker_TP3 pid=291580) AssertionError: Kimi-K3 fp8 KV cache requires an fp8 prefill query; 
                          enable --attention-config '{"use_prefill_query_quantization": true}'.
  ```
* **Root Cause**: The model implementation strictly couples FP8 KV-cache storage with FP8 query quantization during prefill. The harness passed `--kv-cache-dtype fp8` but omitted the required `--attention-config` payload.
* **Remediation**: Pass `--attention-config '{"use_prefill_query_quantization": true}'`.

#### Group B: CPU KV Host Offload Admission Rejection (3 Runs)
* **Affected Cases**: `tp4_native_offload_pressure` (`128k_c1`, `512k_c1`, `1m_c1`).
* **Symptom**: Server aborted during engine initialization before worker spawning.
* **Exact Log Trace**:
  ```text
  (EngineCore pid=294070) File ".../vllm/v1/core/kv_cache_utils.py", line 879, in _check_enough_kv_cache_memory
  (EngineCore pid=294070) ValueError: To serve at least one request with the model's max seq len (1048576), 
                          7.89 GiB KV cache is needed, which is larger than the available KV cache memory (4.0 GiB). 
                          Based on the available memory, the estimated maximum model length is 530432.
  ```
* **Root Cause**: vLLM v1 enforces an engine invariant: on-device GPU KV memory must be able to hold at least $1 \times \text{max\_model\_len}$ tokens. The test artificially forced `--kv-cache-memory-bytes 4294967296` (4.0 GiB), which is lower than the 7.89 GiB floor required for 1M context on TP4.
* **Remediation**: Set `--kv-cache-memory-bytes` to $\ge 8.5\text{ GiB}$ (or reduce `--max-model-len` to 512K for pressure testing).

---

### 2.2 The 8 Distributed Profiler Incompletions

Out of 22 distributed Nsight Systems profile points:
1. **3 Native High-Concurrency Decode Trace Drops** (`batched_decode_8k_c8` on `tp16_pp1`, `tp4_pp4`, `tp8_pp2`):
   * *Mechanism*: Ray actor runner signaled teardown immediately upon client request completion. Remote node worker processes were killed before the background Nsys daemons flushed `.nsys-rep` binaries to disk.
   * *Remediation*: Add a 15-second teardown buffer (`sleep 15`) prior to terminating Ray worker processes.
2. **1 Capped-100G Missing Artifact** (`tp16_pp1_dist/prefill_128k` directory was empty in the archive).
3. **4 Capped-20G Missing Artifacts** (`prefill_128k` across all 4 distributed layouts were executed in scratch but omitted during final tarball assembly).

---

### 2.3 Out-of-Scope Clarification: 50G and 10G Serving

* **Status**: NOT A BUG. 50G and 10G network modes were explicitly scoped as **hardware-only microbenchmarks** (iperf3 bandwidth and NCCL AllReduce/SendRecv bus tests).
* Model serving runs were intentionally restricted to Native (~174 Gbps), 100G (~57 Gbps), and 20G (~16.5 Gbps) to avoid 24 redundant multi-hour runs. The $\alpha$-$\beta$ network model accurately interpolates performance between 100G and 20G.

---

## 3. Plan Evolution: What Was Added Between `v1.0` and `v1.3`

[`V8_Gaps_and_Rerun_Plan_v1.3.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V8_Gaps_and_Rerun_Plan_v1.3.md) systematically expanded the scope to eliminate every *"NOT YET MEASURED"* gap in the technical audit:

| Plan Item | Origin | Targeted Finding & Architectural Purpose | Est. Time |
|---|---|---|---:|
| **A1** | v1.0 | **8K Chunk-Budget Artefact Check**: Re-run with `max_num_batched_tokens 8448` to prevent 8,192 prompts from splitting into a 2nd chunk under load. | 10 min |
| **A2** | v1.0 | **FP8 KV Smoke Test**: Verify server initialization with `--attention-config` before scheduling long runs. | 5 min |
| **A3** | v1.0 | **KV Block Count Inspection**: Read start-up logs to audit why the TP8 KV pool is only 1% larger than TP4 instead of ~19%. | 0 min |
| **A4** | v1.0 | **PP2 15/12 Layer Split Test**: Validate cost model prediction (−3.5% TTFT, stage-0 idle 10.1% $\to$ 3.2%). | 20 min |
| **A5** | v1.0 | **NCCL Audit Counter Fix**: Fix Windows path regex in validator to eliminate false `nccl_policy_ok: false`. | 0 min |
| **A6** | **v1.1** | **Closed-Loop Wave Trimming**: Re-report steady-state numbers by trimming wave 1 burst from TTFT and the drain wave from TPOT. | 0 min |
| **A7** | **v1.2** | **Pinned TP8 8K c1 Run**: Pin worker processes to GPU NUMA sockets to isolate the host side of TP8's extra 22µs AllReduce overhead. | 20 min |
| **A8** | **v1.2** | **NCCL Provider Plugin & Socket Threads**: Test cross-node TCP with tuned socket threads to measure protocol overhead. | 15 min |
| **B1** | v1.0 | **Graphs-On Single-Node Nsight Decode**: `--cuda-graph-trace=node` on TP4/TP8 ($c=1, 8, 32$) to replace eager mode kernel inventories. | 60 min |
| **B2** | v1.0 | **Distributed Layouts Under Load**: TP4/PP4 and TP16 under $c=2, 4, 8$ at 128K and 1M on native fabric (closing the single-node concurrency bias). | 180 min |
| **B3** | v1.0 | **Statistical Repeats ($n=5$)**: Targeted repeats at 8K $c=8/32$ and 128K $c=4/8$ where run-to-run noise reaches 2–5%. | 120 min |
| **B4** | v1.0 | **API Server Scaling**: Test `--api-server-count 2/4` to eliminate outside-engine client queuing under load. | 30 min |
| **B5** | **v1.3 (Expanded)** | **All 4 Planned FP8 KV Runs**: Execute 128K $c=1/4$, 512K $c=1$, 1M $c=1$ with prefill query quantization. | 15 min |
| **B6** | v1.0 | **TP16 512K Prefill Re-Capture**: Re-capture multi-rank prefill trace (previously only 1 of 12 ranks was usable). | 15 min |
| **B7** | v1.0 | **Interactive Short Prompts (1K & 2K)**: Measure TP4 at 1K/2K tokens ($c=1, 8, 32$) to map the high-AllReduce interactive regime. | 30 min |
| **B8** | **v1.1** | **Prefix-Cache Miss Probe**: Re-run with token-exact prompt matches to verify cache hits. | 20 min |
| **B9** | **v1.3 (Expanded)** | **All 3 Planned CPU Offload Runs**: Re-run 128K, 512K, 1M with 8.5 GiB GPU KV floor to measure 56.5 GB/s PCIe paging round-trip. | 20 min |
| **B10** | **v1.3 (Added)** | **5 Missing Capped Prefill Profiles**: Capture TP16 at 100G and all 4 layouts at 20G. | 25 min |
| **B11** | **v1.3 (Added)** | **Two-Node Graphs-On Decode Profiles**: Re-capture distributed decode across all 4 layouts with CUDA Graphs enabled. | 30 min |
| **B12** | **v1.3 (Added)** | **8K Context on Two-Node Layouts**: Add 8K $c=1$ baseline across distributed layouts to complete the scaling curve. | 15 min |
| **B13** | **v1.3 (Added)** | **Two-Node Profile Under Load**: Profile TP4/PP4 at 512K $c=2$ to separate stage imbalance from pipeline bubble. | 15 min |
| **C1** | v1.0 | **DP = 2 × TP = 8 Production Topology**: Multi-replica scale-out with expert parallelism kept inside each node. | 180 min |
| **C2** | v1.0 | **Long-Context Needle-in-a-Haystack**: Accuracy verification for FP8 KV against BF16 baseline. | Separate |
| **C3** | **v1.3 (Dropped)** | **50G / 10G Serving Sweeps**: Dropped to conserve machine time (bounded by 20G cap). | *Cancelled* |

---

## 4. How the Dashboard Updates "For the Good"

Executing the `v1.3` re-run plan directly transforms the dashboard UI, eliminating data gaps, false audit flags, and measurement artefacts:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             DASHBOARD UPGRADE MATRIX                             │
├──────────────────────────┬────────────────────────────┬──────────────────────────┤
│ UI Surface               │ Before Re-Run              │ After Re-Run Strategy    │
├──────────────────────────┼────────────────────────────┼──────────────────────────┤
│ Evidence & Audit Ledger  │ 119 Completed / 7 NOT_RUN  │ 126 Completed / 0 NOT_RUN│
│ Validation Gate          │ serving_matrix_complete: F │ serving_matrix_complete:T│
│ NCCL Policy Tile         │ POLICY INCOMPLETE (Yellow) │ POLICY AUDITED (Green)   │
│ Scheduler & KV Cache     │ FP8 KV: Empty / Placeholder│ Full 2x KV Capacity Gain │
│ CPU KV Tiering           │ Offload: Unmeasured        │ 0.28s Round-Trip Verified│
│ Multi-Node Concurrency   │ Single-Node Data Only      │ TP4/PP4 & TP16 c=2..8    │
│ Profiler Tab (Decode)    │ Eager Mode Inventory       │ Graphs-On Serving Shares │
│ Distributed Profiles     │ 14 / 22 Validated          │ 22 / 22 Full Capture     │
│ Loaded 8K TTFT           │ 1.62s (Burst Contaminated) │ 0.94s True Steady-State  │
└──────────────────────────┴────────────────────────────┴──────────────────────────┘
```

### Detailed Tab-by-Tab Impact:
1. **Executive Tab & KPI Strip**:
   * Resolves the 8K chunk artefact (A1) and trims closed-loop start bursts (A6), lowering reported 8K $c=32$ first-token latency from an artificially inflated **1.62s** to the true steady-state **0.94s**.
   * Replaces single-node assumptions with empirical two-node deployment recommendations.
2. **Scheduler & KV-Cache Tab**:
   * Ingests real FP8 KV cache measurements (B5), demonstrating the predicted **doubling of context capacity from 8.2M to 16.3M tokens** on TP4 and reducing 1M decode TPOT from **10.3ms to 7.9ms**.
   * Populates CPU offload metrics (B9), proving that host DRAM parking costs only **0.28s round-trip at 1M context** (via 56.5 GB/s PCIe) compared to **93s of re-computation**.
3. **Scale-Out & Concurrency Tabs**:
   * Introduces true multi-node concurrency curves under load (B2), revealing whether pipeline parallelism or tensor parallelism maintains lower queuing delays at 128K and 1M under concurrent user traffic.
   * Completes the 8K short-prompt baseline across distributed layouts (B12).
4. **Profiler Tab**:
   * Replaces eager-mode single-node inventories with **true CUDA graphs-on decode kernel timelines** (B1), showing actual time-shares for AllReduce, DeepGEMM, and Sparse MLA.
   * Closes all missing multi-node profiler tiles (B10, B11, B13), bringing profiler provenance to **100% verified**.
5. **Evidence & Audit Tab**:
   * Flips `coverage_counts` to **126 of 126 completed**, clearing all red `NOT_RUN` chips.
   * Fixes the path counter bug (A5), turning the NCCL Policy badge from amber to **audit-verified green**.

---

## 5. Further Recommendations: High-Leverage Runs Beyond `v1.3`

To maximize production readiness, the following 4 runs provide substantial architectural insight with minimal machine overhead:

### Recommendation 1: Elevate DP=2 × TP=8 to Headline Production Status (Item C1)
* **The Problem**: In real enterprise production, dual-node 16-GPU clusters are almost never deployed as TP16 due to PCIe AllReduce cross-node saturation. The natural production topology is **DP=2 $\times$ TP=8** (one independent TP8 replica per node with expert parallelism kept local).
* **The Test**: Run DP=2 under load ($c=8, 16, 32, 64$ at 8K and 128K) with vLLM's multi-engine coordinator.
* **Value**: Directly proves aggregate system throughput (tokens/sec/cluster) and measures inter-replica dispatch latency under realistic Poisson traffic.

### Recommendation 2: Chunked Prefill Sensitivity Matrix (`max_num_batched_tokens` 4K vs 8K vs 16K)
* **The Problem**: V8 kept `max_num_batched_tokens` hardcoded to 8,192 across almost all benchmarks.
* **The Test**: Measure TP4 and TP8 at 128K context under concurrent decode ($c=4$) across 4,096, 8,192, and 16,384 token chunk budgets.
* **Value**: Defines the exact operational Pareto frontier between **interactive decode jitter** (favors 4K chunks) and **prefill tensor-core throughput** (favors 16K chunks).

### Recommendation 3: Empirical Warm-Engine VRAM Eviction Knee (True OOM Boundary)
* **The Problem**: The 3 CPU offload runs were artificially forced to fail by a synthetic 4 GiB memory cap.
* **The Test**: Step concurrency on 128K ($c=1, 2, 4, 8, 12, 16$) on native GPU memory until physical allocation reaches 96–98% VRAM.
* **Value**: Discovers the genuine physical KV-cache eviction/preemption cliff, providing hard capacity boundaries for cluster admission controllers.

### Recommendation 4: Sub-8K Ultra-Short Prompt Regime (1K & 2K Tokens)
* **The Problem**: V8's shortest benchmark prompt was 8,192 tokens. Interactive chat, agentic loops, and coding assistant turns typically use prompts between 512 and 2,048 tokens.
* **The Test**: Run TP4 and TP8 at 1K and 2K context ($c=1, 8, 32$).
* **Value**: Maps the regime where collective AllReduce barrier latency represents the highest percentage of total turn time, completing the prompt-length scaling curve.

---

## 6. Consolidated Master Rerun List (Ranked by ROI per Machine Hour)

Here is the unified, definitive execution roadmap combining the high-leverage gap fillers, the two new targeted diagnostic runs, and the failed-run closures:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        UNIFIED V8 RERUN EXECUTION ROADMAP                              │
├──────┬───────────────────────────────────────────┬──────────────┬──────────────────────┤
│ Tier │ Benchmark & Investigation Target          │ Machine Time │ Target Closure       │
├──────┼───────────────────────────────────────────┼──────────────┼──────────────────────┤
│ T0   │ Log Reads & Edge Trimming (Analysis Only) │ 0 min        │ Items #4 & #8        │
│ T1   │ High-Leverage Diagnostic & Calibration    │ ~2.0 Hours   │ #1, Torch, Pin, NCCL │
│ T2   │ The 7 Failed Application Runs (FP8/Offld) │ ~35 min      │ Items B5 & B9        │
│ T3   │ Profiler Teardown Fix (Capped & Distributed)│ ~55 min    │ Items B10 & B11      │
│ T4   │ Multi-Node Scale-Out Under Load           │ ~3.0 Hours   │ Item B2              │
└──────┴───────────────────────────────────────────┴──────────────┴──────────────────────┘
```

---

### Tier 0: Zero Machine-Time Immediate Wins (0 Min GPU Time)
1. **Item #8: Closed-Loop Start Burst & Drain Trimming (0 min)**
   * *Method*: Re-report closed-loop benchmarks by excluding wave 1 (cold arrival burst of 32 simultaneous requests) from TTFT and the final draining wave from TPOT.
   * *Impact*: Lowers reported 8K $c=32$ mean first-token latency from an artificially inflated **1.62s down to the true steady-state 0.94s**.
2. **Item #4: 8-GPU KV Pool Log Audit (0 min)**
   * *Method*: Inspect initialization logs of TP4 vs TP8 to resolve why the 8-GPU pool is only 1% larger (8.21M vs 8.14M tokens) instead of the theoretical +19%.

---

### Tier 1: High-Leverage Diagnostics & Latency Wins (~2.0 Hours Total)
3. **Item #1: 8K Chunk-Budget Fix (`5–10 min`)**
   * *Method*: Run 8K at $c=4$ and $c=32$ with `--max-num-batched-tokens 8448` (instead of 8192).
   * *Impact*: Prevents an 8,192 prompt from splitting into two chunks under concurrent decode. Eliminates the artificial prefill doubling (0.21s $\to$ 0.42s). Re-states every loaded 8K first-token number.
4. **NEW: Graphs-On Torch Profiler Capture at 8K $c=8$ and $c=32$ (`10 min`)**
   * *Method*: Run PyTorch profiler on TP4 at 8K with CUDA Graphs **ON** at batch sizes $c=8$ and $c=32$.
   * *Why*: The current decode budget is measured graphs-on *only at one request* ($c=1$, 4.52 vs 4.47 ms); under load, step time grows from 4.5ms to 15.8ms, but how that growth splits between grouped expert GEMMs and batched attention is currently modeled.
   * *Impact*: Converts E2E·B/D "not yet split" rows into hard measurements; equips the Profiler tab with its first empirical graphs-on decode under load.
5. **Item #7: NCCL Provider Plugin & Socket Thread Tuning (`15 min`)**
   * *Method*: Cross-node `nccl-tests` with AWS/GCP NCCL provider plugin enabled and tuned socket threads (`NCCL_SOCKET_NTHREADS=4`, `NCCL_NSOCKS_PERTHREAD=4`).
   * *Impact*: Determines whether cross-node AllReduce overhead (57 Gbps throughput / 227–290µs latency) is a physical fabric bottleneck or unoptimized Linux TCP socket defaults.
6. **NEW: TP8 NUMA Socket Pinning Test (`20 min`)**
   * *Method*: Re-run TP8 8K $c=1$ with each rank process pinned directly to its GPU's NUMA socket (`numactl --cpunodebind`).
   * *Why*: On 8 GPUs, serving pays 59µs per decode AllReduce vs 38µs in `nccl-tests` (a +21µs gap that appears only in serving). Cross-socket GPU P2P transfers contribute $\le 1.0\mu\text{s}$, leaving host process/thread scheduling as the remaining suspect.
   * *Impact*: If the token drops from 6.35ms to ~5.2ms, host scheduling is confirmed and latency falls by ~1.2ms; if it stays at 6.35ms, NUMA is ruled out and the dashboard's "cross-NUMA socket overhead" statement is properly corrected to "cause open". Completes the brief's pending §5c requirement.
7. **Item #6: Re-Capture TP16 512K Prefill (`15 min`)**
   * *Method*: Re-run TP16 / PP1 prefill at 512K with clean Nsys extraction.
   * *Impact*: Replaces a 1-of-12 rank modeled extrapolation with verified 16-rank empirical data on the wall-time prefill decomposition pages.
8. **Item #3: PP2 15/12 Layer Split Test (`20 min`)**
   * *Method*: Benchmark `TP4/PP2` and `TP8/PP2` at 128K/512K with 15 layers on Stage 0 / 12 layers on Stage 1 (instead of 14/13).
   * *Impact*: Validates analytical cost model: stage-0 idle shrinks from 10.1% to 3.2%, achieving a **−3.5% TTFT reduction** (cheapest latency win in the suite).
9. **Item #5: Interactive Sub-8K Short Prompts (`30 min`)**
   * *Method*: Benchmark TP4 at 1K and 2K context ($c=1, 8, 32$).
   * *Impact*: Characterizes the interactive chat/agentic regime (512–2,048 tokens), completing the scaling curve below 8K.

---

### Tier 2: The 7 Failed Application Runs (~35 Min Total)
10. **Item B5: The 4 FP8 KV-Cache Sensitivity Runs (`15 min`)**
    * *Command*:
      ```bash
      --kv-cache-dtype fp8 \
      --attention-config '{"use_prefill_query_quantization": true}'
      ```
    * *Targets*: `tp4_fp8_kv` @ 128K $c=1/4$, 512K $c=1$, 1M $c=1$.
    * *Impact*: Closes 4 `NOT_RUN` slots; proves predicted $2\times$ KV capacity expansion (8.2M $\to$ 16.3M tokens) and decode TPOT reduction (10.3ms $\to$ 7.9ms at 1M).
11. **Item B9: The 3 CPU KV Host Offload Runs (`20 min`)**
    * *Command*:
      ```bash
      --kv-cache-memory-bytes 9126805504 \
      --kv-offloading-size 32 \
      --kv-offloading-backend native
      ```
    * *Targets*: `tp4_native_offload_pressure` @ 128K, 512K, 1M ($c=1$).
    * *Impact*: Closes 3 `NOT_RUN` slots; verifies that parking 1M context in host DRAM costs only 0.28s round-trip via 56.5 GB/s PCIe vs 93s to recompute. Brings total completed runs to **126 / 126 (100%)**.

---

### Tier 3: Distributed Profiler Teardown Fix (~55 Min Total)
12. **Item B11: Two-Node Graphs-On Decode Re-Capture (`30 min`)**
    * *Method*: Re-capture multi-node decode with `--cuda-graph-trace=node` and a `sleep 15` buffer before `ray.shutdown()` to eliminate trace drops.
13. **Item B10: Five Missing Capped Prefill Profiles (`25 min`)**
    * *Method*: Capture TP16 at 100G and all 4 layouts at 20G to complete the distributed profiler matrix (**22 / 22 Complete**).

---

### Tier 4: Multi-Node Concurrency Anchor (~3.0 Hours Total)
14. **Item B2: Distributed Layouts Under Load (`3 hours`)**
    * *Method*: Run `TP4/PP4` and `TP16/PP1` at 128K ($c=2, 4, 8$) and 1M ($c=2, 4$), plus 8K $c=8$.
    * *Impact*: Fills the single largest empirical void in the V8 dashboard. Populates true multi-node queuing delays, admission knees, and KV pressure off the single node.

