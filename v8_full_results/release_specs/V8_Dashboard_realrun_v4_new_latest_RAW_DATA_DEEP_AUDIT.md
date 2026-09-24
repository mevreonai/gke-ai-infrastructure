# V8-FULL Dashboard Deep Audit Against Raw ZIP Results

**Dashboard audited:** `MASTER_CHARACTERIZATION_DASHBOARD_realrun_v4_new_latest(1).html`  
**Raw package:** `results_V8_runs.zip`  
**Canonical validation root:** `results/real_data/final_validation/`

## Executive verdict
The dashboard contains a substantial amount of legitimate measured data, especially the native scale-out TTFT series, the 1M single-node concurrency TTFT/TPOT series, chunk-size experiment, prefix-reuse result, max_num_seqs experiment, open-loop 8K sweep, and many evidence rows. However, it is **not yet publication-grade** because several high-level KPI states and multiple charts/tables are inconsistent with the canonical validation products or mix metrics/configurations.

The most important rule for the next version should be:

> **`FINAL_VALIDATION.json` + `coverage.json` + `combined_vllm_runs.json` are authoritative for status and E2E metrics. Raw profile CSV/JSON files are authoritative only for the exact profile they represent, and aggregate kernel share is not request critical-path wall time.**

---

# 1. Canonical campaign truth from final validation

From `final_validation/FINAL_VALIDATION.json` and `FINAL_VALIDATION.md`:

- Coverage rows: **126**
- Completed: **119**
- NOT_RUN: **7**
- Failed: **0**
- Native application runs: **95** = 80 fixed serving + 15 open-loop
- Auxiliary capped vLLM scale-out runs: **24** = 12 @ configured 100G + 12 @ configured 20G
- Hardware validation: **true**
- Both-node readiness: **true**
- Scale-out both-node telemetry: **true**
- 1M all topology × application network points completed: **true**
- Distributed profiles complete: **14 / 22**
- `profiles_all_complete`: **false**
- `nccl_policy_ok`: **false**
- `strict_full_coverage`: **false**
- `full_suite_valid`: **false**

### Immediate dashboard corrections
1. `Run Validation = PASS` must not imply the entire V8 suite fully passed. Better: **E2E RUN MATRIX VALIDATED / STRICT SUITE SIGN-OFF: NOT COMPLETE**.
2. `NCCL Policy = AUDITED` should become **PARTIAL / POLICY AUDIT INCOMPLETE**, because `NCCL_POLICY_AUDIT.json` reports `ok=false` and no Ray scale-out audits for the 12 application scale-out runs.
3. `14 CAPTURED` distributed profiles is correct as **complete profiles**, but the UI must also show **14/22 expected complete**, not suggest 22/22.
4. Hardware name must be **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Remove all RTX 6000 Ada remnants.

---

# 2. Network campaign truth

## Application-level vLLM network modes
The raw suite intentionally executed vLLM scale-out at:
- `GCP_NATIVE`
- `GCP_CAPPED_100G`
- `GCP_CAPPED_20G`

All **36 topology × context × application-network cells** completed.

50G and 10G were **not** vLLM application modes, but they **were measured in hardware/NCCL microbenchmarks**.

## Measured iperf forward bandwidth
Final validation reports approximately:
- Native: **173.58 Gb/s**
- configured 100G cap: **56.84 Gb/s measured**
- configured 20G cap: **16.48 Gb/s measured**

Hardware summary additionally includes:
- configured 50G: about **33.02 Gb/s**
- configured 10G: about **9.00 Gb/s**

### Critical UI rule
Never label a series simply `100G` or `20G` as though that was achieved throughput. Show:
- **Configured cap**
- **Measured iperf bandwidth**
- network provenance

Example: `GCP_CAPPED_100G · measured ~56.8 Gb/s`.

## High-value topology sensitivity finding
TTFT delta vs Native at 1M:
- TP4/PP2 @ 100G: **+0.13%**
- TP4/PP2 @ 20G: **+1.14%**
- TP8/PP2 @ 100G: **-0.13%** (noise-level)
- TP8/PP2 @ 20G: **-0.10%** (noise-level)
- TP4/PP4 @ 100G: **+1.04%**
- TP4/PP4 @ 20G: **+3.91%**
- TP16/PP1 @ 100G: **+36.36%**
- TP16/PP1 @ 20G: **+276.69%**

This is one of the strongest campaign discoveries and should be a first-class Scale-Out and Executive view.

---

# 3. Tab-by-tab audit

## A. Executive tab

### KPI cards
| Element | Verdict | Raw-data justification / required change |
|---|---|---|
| Run Validation PASS | **Incorrect / overstated** | `full_suite_valid=false`, `strict_full_coverage=false`. Show partial validation state. |
| Fixed Serving 80/87 | **Correct** | 80 completed fixed native, 7 NOT_RUN. |
| Distributed 1M 12/12 | **Ambiguous wording** | 12 native scale-out runs = 4 topologies × **3 contexts**, not “distributed 1M scope”. For 1M specifically there are 4 Native + 4 100G + 4 20G = 12 application-network points. Rename. |
| Native Distributed Profiles 14 captured | **Correct with denominator missing** | Must say **14/22 expected complete**. |
| Hardware Validation | **Correct** | Hardware required validation true. Fix GPU SKU text to Blackwell. |
| NCCL Policy Audited | **Incorrect** | `nccl_policy_ok=false`; `ray_policy_complete=false`. |
| Native Network 173.58 Gb/s | **Correct** | Final validation supports this. |
| Both-node telemetry verified | **Correct** | `scaleout_telemetry_ok=true`. |

### Deployment Decision Map
- **8K interactive TP4/PP1:** observation 4.49 ms vs TP8 6.37 ms is legitimate for matched `tp4_qualification/8k_c1` vs `tp8_qualification/8k_c1`.
- **128K TP4/PP4 TTFT 1.71 s:** legitimate.
- **512K TP4/PP4 10.22 s:** legitimate. The comparison “vs 27.8s TP8” is stale; canonical TP8 context baseline is ~28.09 s and TP4 baseline is ~31.92 s.
- **1M TP4/PP4 28.57 s:** legitimate. `~35,005 input tok/s` is a **derived prompt-ingestion rate** (`1,000,000 / TTFT`), not output TPS. Label formula explicitly.
- **1M concurrent TP4/PP4 c≤2:** **invalid configuration contamination**. c1/c2/c4 concurrency data belongs to TP4/PP1 and TP8/PP1 single-node. Distributed TP4/PP4 only has c1 application points.
- **“0 queue at c≤2; 1.45s at c4”: incorrect.** Canonical TP4/PP1 queue histogram mean is ~44.34 s at c2 and ~134.43 s at c4. TP8 is ~35.28 s at c2 and ~106.91 s at c4.
- **Causal claims** such as PP “avoids TCP all-reduce stalls” must be reduced to hypothesis unless exact distributed timeline evidence supports that topology/workload.

### Campaign Scope / Gaps
Current text saying cap sensitivity is deferred is **stale**.
Correct structure:
- Application E2E sensitivity: Native / configured-100G / configured-20G measured.
- Hardware microbench sensitivity: Native / 100G / 50G / 20G / 10G measured.
- Local physical 2×10GbE equivalence: **not established**.

### Executive TTFT chart
**Partially correct.**
- Distributed Native values are canonical.
- TP4 single-node 512K should be ~31.92 s, not 35.80 s.
- TP8 single-node 512K should be ~28.09 s, not 27.80 s.
- 1M baseline should use one consistent case lineage (context baseline or V8 extension), not mix them silently.

### Executive TPOT chart
**Partially invalid.**
- TP4/TP8 8K and 128K qualification points are legitimate.
- Single-node 512K values currently shown elsewhere as 7.84/8.41 are not the matched context-baseline values (~7.57 / ~9.46 ms).
- Distributed 8K values `TP4/PP4 5.20/9.80` and `TP16 8.50/16.40` are not supported by the raw distributed profile bench results. Raw profile-run TPOT is materially higher and profile-instrumented, so should not be mixed into normal benchmark charts.

### Executive Capacity chart
**Invalid legacy curve.**
The plotted TP4/TP8 c1/c8/c16/c32/c48/c64 output TPS values are not present in canonical `combined_vllm_runs`.
- TP4 real closed-loop 8K points exist through c32.
- There is no canonical c48/c64 closed-loop result.
- There is no matching TP8 high-concurrency sweep beyond c8 in the 119-run table.

**Replace with:**
1. Real TP4 8K closed-loop c1/c4/c8/c16/c32; and/or
2. Real TP4 8K open-loop offered-RPS curve.

---

## B. Scale-Up tab

### TTFT vs Context
**Partially correct; stale 512K values.**
Recommended canonical lineage: `tp4_context_baseline` vs `tp8_context_baseline`:
- 8K: 0.222 s vs 0.263 s
- 128K: 4.532 s vs 4.810 s
- 512K: 31.916 s vs 28.089 s
- 1M: 93.248 s vs 74.688 s

This demonstrates a real crossover: TP4 is better at shorter contexts; TP8 becomes better at long prefill.

### TPOT vs Context
**Current values are partly wrong.**
Canonical context-baseline values:
- TP4: 4.475 / 5.106 / 7.565 / 10.267 ms
- TP8: 6.350 / 7.098 / 9.455 / 12.102 ms

The current 512K 7.84/8.41 pair should not be used as the context-baseline comparison.

### Output Throughput — Matched Workload
**Invalid at 1M and mixed semantics.**
- 1M output throughput is about 0.342 tok/s TP4 and 0.426 tok/s TP8 for the context-baseline runs, not 10.3 / 12.1.
- 10.3 and 12.1 are approximately TPOT values, so the chart is mixing units.

### TTFT / TPOT vs Concurrency
**Invalid legacy arrays.**
Current c48/c64 values are not in canonical results. Replace with real TP4 closed-loop c1/c4/c8/c16/c32 and clearly separate TP8 where data exists.

### Local TP4/TP8 NCCL Correlation
**Raw NCCL exists, but current curve is partly interpolated / mislabeled.**
The hardware summary has exact message sizes such as 16K, 128K, 512K, 64M, 128M, 256M. Current chart labels 64K/256K/1M/4M/16M without exact raw support. Do not interpolate unless explicitly labeled DERIVED.

### Scale-Up Decision table
Corrections:
- “7.84 vs 8.41 ms = 7.2%” is not the clean matched 8K c1 evidence. Use 4.49 vs 6.37 ms (~29.6% lower TPOT for TP4) for interactive c1.
- “512K 27.8 vs 35.8 = 22%” is stale. Canonical context baseline is ~28.09 vs ~31.92 s, ~12.0% lower TTFT on TP8.
- High-throughput `c32 1240 tok/s, c48/c64` claim is unsupported by canonical run table.
- 1M TP8 ~74.7/74.9 s vs TP4 ~93.25/93.39 s is legitimate.

---

## C. Scale-Out tab

### Topology Comparison @ Selected Context
**Chart itself is correct** for Native TTFT:
- TP4/PP2: 2.647 / 17.945 / 52.526 s
- TP8/PP2: 2.788 / 15.576 / 41.515 s
- TP4/PP4: 1.710 / 10.222 / 28.568 s
- TP16/PP1: 6.420 / 29.624 / 68.197 s

The analysis strip beneath it is **wrong/cross-contaminated** (it talks about 8K open-loop RPS, all 119 preemptions, etc.). Replace with topology-specific observation/delta/evidence.

### Context Scaling by Topology
**Numerically correct** for Native TTFT.
Profiler commentary beneath it is **wrongly scoped**: 46%/86.3% are single-node TP4 aggregate kernel shares, not generic distributed topology critical-path shares.

### Native Topology × Metric Decision Matrix
**Stale / incorrect. Replace entirely from canonical Native rows.**
Correct 128K Native values:
- TP4/PP2: TTFT 2647 ms, TPOT 5.507 ms, output 21.373 tok/s, KV 0.785%
- TP8/PP2: TTFT 2788 ms, TPOT 7.541 ms, output 19.614 tok/s, KV 0.776%
- TP4/PP4: TTFT 1710 ms, TPOT 5.632 ms, output 30.993 tok/s, KV 0.365%
- TP16/PP1: TTFT 6420 ms, TPOT 14.942 ms, output 8.693 tok/s, KV 1.595%

### Native 1M matrix
TTFT values are correct. Replace `35k tok/s` with **~35k input-token/s derived ingestion rate** and keep output throughput separate (~1.107 output tok/s).

### Network verification table
- Native ~173.58 Gb/s is supported.
- Reverse should be sourced directly; hardware summary is ~173.59 Gb/s rather than 173.42.
- NCCL SendRecv should use exact raw `alg_bw/bus_bw` by message size. A blanket “21.84 GB/s” is not supported by the processed summary values; large-message native SendRecv is around 7.1 GB/s in the shown NCCL test output. Reconcile before publishing.
- “Local TP4/TP8/TP16 collectives” is wrong terminology: TP16 is not local on an 8-GPU node.

### What to add
**Network Sensitivity Heatmap**: topology × context, color = `% TTFT change vs Native`, for 100G and 20G. This is much more insightful than a disabled network selector.

---

## D. Long Context tab

### Fit / Finish
Broadly supported:
- 1M completes.
- no preemptions in all 119 completed runs.
- GPU memory peaks are around high-80s GiB depending topology; use actual `gpu_node_stats_json`, not a single universal 88.7 GB value.

### “c≤2 viable” KPI
**Incorrect. Remove.**
Canonical TP4/PP1 V8 extension:
- c1: TTFT 93.39 s, TPOT 10.23 ms, queue ~0 s
- c2: TTFT 139.37 s, TPOT 181.97 ms, **queue 44.34 s**
- c4: TTFT 231.27 s, TPOT 267.41 ms, **queue 134.43 s**

TP8/PP1:
- c1: 74.89 s / 12.05 ms / ~0 s queue
- c2: 111.74 s / 177.21 ms / **35.28 s queue**
- c4: 184.88 s / 259.50 ms / **106.91 s queue**

This shows the queue/latency cliff starts at **c2**, not c4.

### 1M Concurrency TTFT chart
**Correct.**

### “Scheduler Sensitivity @ 1M c4” chart
**Card/chart mismatch.** The current chart actually plots TPOT vs c1/c2/c4 for TP4/TP8; it does not show max_num_seqs 4/8/16. The real max_num_seqs chart exists later in Scheduler.

### Chunked Prefill chart
**Correct** for TTFT:
- 4K: 122.049 s
- 8K: 93.28 s
- 16K: 88.95 s

Do not call 4K the compromise unless fairness/jitter metrics are shown. For TTFT alone, 16K wins.

### FP8 KV chart
Use `null/NOT_RUN`, as current chart correctly does. However, do not claim a backend architectural reason unless a log or explicit guardrail file proves it; coverage itself only says NOT_RUN.

### Prefix Reuse 1M
The 1M result is legitimate:
- cold/reference ~93.39 s
- repeated-prefix case ~48.35 s
- ~48.2% reduction

**Additional opportunity:** also show 128K and 512K prefix cases:
- 128K prefix case TTFT ~0.902 s vs baseline ~4.532 s
- 512K prefix case TTFT ~16.866 s vs baseline ~31.916 s
- 1M prefix case ~48.349 s vs baseline ~93.39 s

Show hit/query counters alongside latency to avoid calling every improvement a pure “cache hit” without context.

### CPU Offload chart
**Unit error.** `10.23` is TPOT in ms, not tok/s. Offload cases are NOT_RUN. The chart should be a status card, not a quantitative comparison.

---

## E. Scheduler & KV tab

### Peak KV Usage chart
**Largely incorrect / legacy values.** Replace from `peak_kv_usage` directly.

Canonical single-node context baseline KV%:
- TP4: 8K 0.126%, 128K 1.633%, 512K 6.456%, 1M 12.290%
- TP8: 8K 0.112%, 128K 1.607%, 512K 6.391%, 1M 12.177%

Canonical Native scale-out KV%:
- TP4/PP4: 128K 0.365%, 512K 1.444%, 1M 2.748%
- TP8/PP2: 0.776%, 3.087%, 5.882%
- TP4/PP2: 0.785%, 3.105%, 5.911%
- TP16/PP1: 1.595%, 6.362%, 12.129%

Do not invent 8K or c4 distributed points when no application evidence row exists.

### Running vs Waiting
Using `peak_running=1` and `peak_waiting=0` at c1 is legitimate, but label as **peak**, not generic active/average state. Mean running is <1 because telemetry samples span idle periods.

### Queue Mean chart
**P0 incorrect for 1M c2/c4.** Replace with canonical histogram values noted above. Distributed c1 microsecond-scale queues are legitimate.

### Preemptions
**Correct:** all 119 completed runs have `preemptions_delta=0`.

### max_num_seqs @ 1M c4
**Correct and useful:**
- 4: 232.342 s
- 8: 232.364 s
- 16: 232.250 s

The flatness is strong evidence that max_num_seqs is not the limiter for this specific 1M c4 TP4 workload.

### Offload bytes
Current numeric 0 is not directly supported because the combined field is missing/NaN rather than measured zero. Since offload tests were NOT_RUN, show `NOT_RUN / NO OFFLOAD MEASUREMENT`, not a bar at zero.

### Open-loop 8K
**Correct.** Exact canonical values match the chart.

### Scale-Out scheduler/KV ledger
KV percentages for TP4/PP4, TP8/PP2 and TP16 are close to canonical; TP4/PP2 values need correction. The “Pipeline Stage Memory” column is **misleading/incorrect**: values like 11.3/44.8/88.7 GB are not the measured per-GPU peak memory. Actual per-GPU total memory peaks are approximately constant by topology across contexts because weights dominate:
- TP4/PP2: ~88.69 GiB
- TP8/PP2: ~87.51 GiB
- TP4/PP4: ~88.83 GiB
- TP16/PP1: ~86.71 GiB

Keep **KV cache %** separate from **total GPU memory used**.

### Capacity Knee / Admission Decision
**Current card is not supported.**
- c48/c64 short-context points are not canonical application runs.
- `c32 = 1240 tok/s` is not the canonical TP4 closed-loop output throughput; real TP4 closed-loop c32 output throughput is ~784 tok/s.
- 1M c2 is not a safe point by queue or TPOT.
- There is no distributed c2 evidence, so “hard admission cap c2 per 16-GPU cluster” cannot be claimed.

Replace with an SLO-driven envelope based only on measured points.

### Add 128K open-loop
This is highly valuable and currently missing. It shows a much earlier/smaller load envelope than 8K and a dramatic latency/queue cliff near higher offered RPS.

---

## F. Profiler tab

This tab requires the largest semantic correction.

### Profile completeness
Canonical state:
- single-node Nsight metadata: 6
- PyTorch profiles complete: 2
- distributed expected: 22
- distributed validation files present: 17
- distributed complete: **14**
- profiles_all_complete: **false**

Three Native batched-decode profiles are incomplete:
- TP16/PP1 c8: node1 Nsight report missing
- TP4/PP4 c8: node0 and node1 reports missing
- TP8/PP2 c8: node0 report missing

Additional expected capped profile points were not all captured.

The current “22 CAPTURED = 14 distributed +6+2” wording is misleading because 14 distributed is only 14/22 expected.

### Critical Path Ledger
**Do not publish current percentages as critical-path wall time.**
The exact 46.0% prefill and 86.3% decode numbers are real, but they come from **single-node TP4 `cuda_gpu_kern_sum.csv` aggregate GPU kernel-time share**:
- TP4 prefill: NCCL AllReduce 46.0% of aggregate GPU kernel time
- TP4 decode: NCCL AllReduce 86.3% of aggregate GPU kernel time

The raw `PROFILE_ANALYSIS.json` explicitly states:
- semantic attribution is heuristic unless correlated with layerwise NVTX
- aggregate GPU kernel work is **not wall-clock critical-path time**

Therefore:
- rename these charts **Aggregate GPU Kernel-Time Composition — TP4/PP1 Single Node**
- never add CPU API %, GPU %, runtime %, NCCL % into a 100% wall-clock ledger unless a true timeline join was performed
- remove `Residual = 0%`
- remove generic `PP boundary measured` claims from the same ledger unless tied to a specific distributed trace

### Kernel / Activity Categories chart
**Numbers are legitimate for exact TP4 single-node raw profiles, but scope is wrong.**
Keep the values only if the chart title and provenance say precisely:
- TP4/PP1 single-node 128K prefill profile
- TP4/PP1 single-node 8K decode profile
- metric = aggregate GPU kernel time share

### Framework / Operator Attribution chart
The average durations are largely traceable to Nsight `cuda_gpu_kern_sum.csv`; the card says “PyTorch Profiler,” which is the wrong provenance. Either:
- relabel it as **Nsight kernel average duration**, or
- rebuild it from the PyTorch profiler output if framework operator attribution is desired.

### Distributed completeness chart
Current 7 bars all at 100% are not a valid representation of 14/22 completeness and hide incomplete profiles. Replace with a 22-cell matrix:
- topology
- network mode
- workload
- node0 report status
- node1 report status
- complete/incomplete

### Good raw-data additions
- Per-profile top NCCL kernel share, but explicitly aggregate-kernel-time.
- Node0 vs Node1 capture symmetry.
- profile-instrumented E2E vs uninstrumented E2E ratio (to show profiler perturbation).
- exact NCCL call count and average duration by topology, with no critical-path inference unless timeline-correlated.

---

## G. Evidence tab

This is the strongest foundation in the dashboard.

### What is legitimate
- 126 coverage rows
- 119 completed / 7 NOT_RUN
- primary Native and auxiliary capped cases
- case manifests and source-summary lineage
- missing values preserved instead of coerced to zero in many places

### Changes needed
1. CAPPED_SWEEP rows are **COMPLETED auxiliary measurements**, not “unresolved” results. Use two fields: `execution_status=COMPLETED`, `evidence_class=AUXILIARY_SENSITIVITY`.
2. Replace developer-local `C:\Users\...` paths with artifact-relative paths or a stable evidence ID.
3. Add direct columns for:
   - run/suite lineage
   - exact model revision
   - TP/PP/DP/EP
   - max_num_batched_tokens
   - max_num_seqs
   - KV dtype
   - prefix caching
   - configured network cap
   - measured network bandwidth
   - p95/p99 reliability flags
4. Surface `p95_reliable` / `p99_reliable`; many low-N rows must not show p95/p99 as production SLO evidence.
5. Add a one-click mapping from each chart point to its exact evidence row.

---

# 4. Chart-by-chart legitimacy summary

| # | Chart | Verdict | Action |
|---:|---|---|---|
| 1 | Executive TTFT vs Context | 🟠 Partial | Correct 512K single-node values; lock one case lineage. |
| 2 | Executive TPOT vs Context | 🔴 Mixed/invalid | Remove unsupported distributed 8K points; correct 512K single-node. |
| 3 | Executive Capacity/SLO | 🔴 Invalid legacy | Rebuild from real closed/open-loop rows. |
| 4 | Scale-Up TTFT | 🟠 Partial | Correct stale 512K values. |
| 5 | Scale-Up TPOT | 🟠 Partial | Use context-baseline values. |
| 6 | Scale-Up Throughput | 🔴 Unit/data error | 1M values are not output TPS. |
| 7 | Scale-Up Concurrency | 🔴 Unsupported | c48/c64 + TP8 high-concurrency curve not in canonical data. |
| 8 | Scale-Up NCCL | 🔴 Interpolated/mislabeled | Use exact message sizes from hardware summary only. |
| 9 | Scale-Out Topology Comparison | 🟢 Correct | Keep; add sensitivity selector. |
| 10 | Scale-Out Context Scaling | 🟢 Correct values | Fix profiler commentary scope. |
| 11 | 1M TTFT vs concurrency | 🟢 Correct | Keep. |
| 12 | Long “Scheduler Sensitivity” | 🔴 Wrong chart for card | Data is TPOT vs concurrency, not max_num_seqs. |
| 13 | Chunk-size TTFT | 🟢 Correct | Add TPOT/queue if objective says compromise. |
| 14 | FP8 KV | 🟢 Correct status | Keep null/NOT_RUN; avoid unsupported reason. |
| 15 | Prefix reuse 1M | 🟢 Correct | Add 128K/512K scaling + hit/query counters. |
| 16 | CPU Offload | 🔴 Unit error | 10.23 is TPOT ms, not tok/s; show NOT_RUN state only. |
| 17 | Scheduler KV utilization | 🔴 Largely wrong | Rebuild directly from `peak_kv_usage`. |
| 18 | Running/Waiting | 🟠 Mostly valid | Label as peak states; optionally plot mean separately. |
| 19 | Queue Mean | 🔴 P0 wrong | Replace c2/c4 with 44.34s/134.43s TP4 etc. |
| 20 | Preemptions | 🟢 Correct | Keep. |
| 21 | max_num_seqs | 🟢 Correct | Keep; strong low-sensitivity finding. |
| 22 | Offload bytes | 🟠 Unsupported zero | Show NOT_RUN/metric unavailable, not zero. |
| 23 | 8K Open-loop | 🟢 Correct | Keep; add queue and output throughput or separate panel. |
| 24 | Profiler Kernel Categories | 🟠 Real values, wrong semantics | Rename as aggregate TP4 GPU kernel-time composition. |
| 25 | Profiler Operator Attribution | 🟠 Real Nsight values, wrong provenance | Relabel or rebuild from PyTorch profiler. |
| 26 | Profile Completeness | 🔴 Misleading | Replace with 14/22 matrix, including incomplete nodes. |

---

# 5. Highest-value new views available from the ZIP

## 1. Topology × Network Sensitivity Heatmap
**Rows:** TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1  
**Columns:** 128K, 512K, 1M  
**Panels:** configured 100G and 20G  
**Color:** TTFT % delta vs Native

Why it matters: instantly demonstrates that TP16/PP1 is dramatically more bandwidth-sensitive than PP-oriented structures.

## 2. Configured cap vs measured bandwidth panel
Show:
- Native 173.6 Gb/s
- 100G configured → ~56.8 measured
- 50G configured → ~33 measured hardware-only
- 20G configured → ~16.5 measured
- 10G configured → ~9 measured hardware-only

This prevents false interpretation of cap labels.

## 3. 1M SLO Degradation Waterfall
For TP4 and TP8 c1/c2/c4 show simultaneously:
- TTFT
- TPOT
- queue histogram mean
- KV%
- preemptions

Key discovery: queue and TPOT collapse already at c2 even though memory/preemptions remain healthy.

## 4. Prefix-Reuse Scaling
128K / 512K / 1M:
- baseline TTFT
- prefix-enabled TTFT
- reduction %
- hit/query counter ratio

This is a highly actionable runtime optimization story.

## 5. Closed-loop vs Open-loop Capacity
Separate charts by semantics:
- Closed-loop concurrency sweep: actual c1/c4/c8/c16/c32 at 8K
- Open-loop offered RPS sweep: 8K and 128K

Never mix concurrency and offered RPS on one x-axis.

## 6. Profiler Coverage Matrix
22 expected distributed profile cells, status by node/report.
This makes profiling completeness auditable instead of hiding missing traces.

## 7. Application vs Hardware Network Layers
Two linked views:
- hardware: iperf + NCCL SendRecv + cross-node collectives across 100/50/20/10/native
- application: TTFT/TPOT/output throughput across native/100/20

This creates a true **hardware ceiling → runtime achieved → application impact** chain.

## 8. Sample Reliability / Statistical Strength
For each E2E point show:
- prompt/sample count
- p95 reliable? p99 reliable?
- repeated vs one-shot

Especially important because many c1 long-context points have N=1 and should not be presented as stable p95/p99 SLOs.

---

# 6. Recommended V7/V8 data architecture

Do not hand-maintain numeric arrays in HTML.

Generate all visual datasets from a normalized analysis object built from:
1. `FINAL_VALIDATION.json`
2. `coverage.json`
3. `combined_vllm_runs.json`
4. `hardware_processed/summary.json`
5. `NCCL_POLICY_AUDIT.json`
6. `SCALEOUT_TELEMETRY_AUDIT.json`
7. per-profile `PROFILE_VALIDATION.json`
8. exact raw profiler CSVs only for profile-specific views

Every plotted point should carry:
- evidence_id
- case
- bench
- model revision
- TP/PP
- context
- load semantics (`concurrency` or `request_rate`)
- network provenance
- configured cap
- measured bandwidth if relevant
- metric
- metric unit
- sample count/reliability
- evidence class
- raw artifact path

---

# 7. Publication gates before calling the dashboard validated

1. No `PASS` if `full_suite_valid=false`; distinguish run-matrix success from strict suite sign-off.
2. No chart value without a canonical evidence row or explicitly named raw profile artifact.
3. No c48/c64 point unless it exists in canonical data.
4. No distributed c2/c4 capacity claim unless executed.
5. No queue number except `queue_mean_s_from_hist` (or another explicitly named metric) with metric name visible.
6. No `tok/s` when the source field is TPOT milliseconds.
7. No aggregate kernel `%` called critical-path wall time.
8. No profile completeness chart that hides incomplete node captures.
9. No “100G/20G achieved” wording without measured iperf.
10. No hardware/memory statement that conflates KV cache utilization with total GPU memory.
11. No causal claim such as “PP avoids all-reduce stalls” without topology-specific timeline attribution.
12. No p95/p99 SLO promotion when reliability flags are false.

---

# Bottom line
The raw ZIP is **more valuable than the current dashboard exposes**. The strongest real campaign narrative is not simply “TP4/PP4 wins.” It is:

1. **Workload phase changes the best local TP choice.**
2. **PP-oriented distributed structures are much less sensitive to constrained fabric than TP16/PP1 in these runs.**
3. **1M memory fit is not the bottleneck; queue/latency explodes with concurrency before preemption occurs.**
4. **Prefix reuse materially reduces long-context prefill latency.**
5. **Some scheduler knobs are empirically low-sensitivity, so tuning effort should move elsewhere.**
6. **Profiler data can explain kernel composition, but current artifacts do not justify turning aggregate kernel shares into exact request critical-path percentages.**

The next dashboard should preserve the useful V4 structure, but regenerate the charts from canonical JSON/CSV rather than legacy hard-coded arrays.
