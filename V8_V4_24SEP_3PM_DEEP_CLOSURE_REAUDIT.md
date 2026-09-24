# V8 Dashboard 24 Sept 3pm — Closure Re-Audit Against Raw Results

**Reviewed dashboard:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_24rdSept_3pmIST.html`  
**Closure checklist:** `V8_V4_23SEP_9PM_CLOSURE_AUDIT_new.md`  
**Raw validation package:** `results_V8_runs(3).zip`  
**Canonical sources re-opened:** `FINAL_VALIDATION.json`, `coverage.json`, `combined_vllm_runs.csv`, `model_validation.json`, `hardware_processed/*`, single-node Nsight/PyTorch exports, distributed `PROFILE_VALIDATION.json` and per-rank Nsight CSVs.

## 0. Executive verdict

The 24 Sept 3pm build closes a **large majority** of the 23 Sept closure comments. The global campaign status, memory units, capped-network scope, scale-up baselines, scale-out sensitivity heatmap, prefix first/repeat semantics, 128K open-loop data, CUDA API table, reliability flags, and 22-point profiler-coverage matrix are materially improved.

However, it is **not yet data-signoff/publication ready**. I found several remaining issues, including **two new numerical regressions caused by mixing legitimate but different run lineages**:

1. **TP4 1M c2 lineage is mixed** in Long Context / Scheduler / Claim Registry:
   - The intended V8 extension series is `tp4_1m_concurrency_extension`.
   - Canonical c2: **TTFT 139.3736 s, TPOT 181.9740 ms, queue 44.3402 s, KV 15.5175%**.
   - The 3pm UI instead uses **TTFT 150.54 s / queue 55.40 s** in several places. Those numbers are real, but belong to the older `tp4_closedloop_1m / c2` row, whose TPOT is **239.07 ms**. The UI therefore mixes c2 fields from two different runs.
   - This is a **P0 lineage/data-consistency blocker**.

2. **Executive TPOT chart has one wrong point**:
   - `TP16/PP1 · Native · 512K` is plotted as **16.892 ms**.
   - Canonical `combined_vllm_runs.csv`: **17.4131 ms**.
   - This is a **P0 chart-value blocker**.

There are also unresolved profiler semantics/provenance problems, non-exact chart→Evidence mapping for several distributed/profile points, and SLO/admission recommendations that still lack an explicit SLO.

---

# 1. Canonical campaign truth revalidated from the ZIP

| Item | Canonical truth |
|---|---:|
| Configured coverage rows | **126** |
| Completed application rows | **119** |
| NOT_RUN | **7** |
| Failed application rows | **0** |
| Native application rows | **95** |
| Auxiliary capped application rows | **24** |
| Distributed profiles expected | **22** |
| Distributed validation files present | **17** |
| Distributed profiles complete | **14** |
| Complete profile composition | **11 Native + 3 configured-100G** |
| `profiles_all_complete` | **false** |
| `nccl_policy_ok` | **false** |
| `strict_full_coverage` | **false** |
| `full_suite_valid` | **false** |

Reliability attributes in the 3pm Evidence table also reconcile correctly with canonical data:

- **93** completed rows: p95=false, p99=false
- **19** completed rows: p95=true, p99=false
- **7** completed rows: p95=true, p99=true
- **7** NOT_RUN

The **126-row Evidence ledger is still strong**. I re-parsed all 126 rendered Evidence rows and reconciled TTFT, TPOT, peak KV, and queue against the raw `combined_vllm_runs.csv`; all **119 completed rows match within display rounding** when network provenance is included in the join key.

Model-manifest guardrail revalidated from `model_validation.json`:

- hidden size **2304**
- hidden layers **27**
- KDA layers **20**
- full-attention layers **7**
- experts **256**
- experts/token **8**
- checkpoint dtype **BF16**
- model max length **1,048,576**
- revision `e1df551a447157d4658b573f9a695d57658590e9`

---

# 2. GLOBAL / CROSS-TAB CHECKLIST

| Audit ID | Status | 24 Sept 3pm finding |
|---|---|---|
| G-01 Title native-only | ✅ CLOSED | Header now says Primary Fabric & Network Sensitivity Edition. |
| G-02 Subtitle `GCP_NATIVE only` | ✅ CLOSED | Primary Native + auxiliary configured-100G/20G is explicit. |
| G-03 119/119 confusing sign-off | ✅ CLOSED | Now 119/126 with 7 guarded NOT_RUN and strict sign-off incomplete. |
| G-04 Profiler denominator | ✅ CLOSED | Executive shows 14/22 and 11 Native + 3 capped-100G. |
| G-05 Ada remnants | ✅ CLOSED | No `RTX PRO 6000 Ada` remains in rendered content. |
| G-06 Footer native-only | ✅ CLOSED | Removed. (`native-only` remains only as a CSS class name, not campaign semantics.) |
| G-07 “no fabricated values” claim | ✅ CLOSED | Removed. |

---

# 3. EXECUTIVE TAB — ITEM-BY-ITEM

| Audit item | Status | Review |
|---|---|---|
| E-01 Distributed profile KPI | ✅ CLOSED | Correct `14/22`, `11 Native + 3 configured-100G`. |
| E-02 8K KV/memory | ✅ CLOSED | `~0.126% KV · 88,769 MiB (~86.69 GiB)` is correct. |
| E-03 TP4/PP4 128K memory | ✅ CLOSED | `90,967 MiB (~88.84 GiB)` is correct. |
| E-04 Memory units/headroom | 🟡 MOSTLY CLOSED | Executive uses MiB/GiB consistently. One profiler-completeness note still says `88.8GB VRAM`; change to GiB or MiB. |
| E-05 1M c1 causal confidence | ✅ CLOSED | Mechanism softened to MEDIUM/CROSS-VALIDATED and timeline boundary stated. |
| E-06 1M strict c1 cap | ✅ CLOSED | Now “c1 cleanest measured; production cap depends on explicit SLO.” |
| E-07 Scale-out causal overclaim | ✅ CLOSED in Decision Map | Observation separated from mechanism and timeline boundary stated. |
| E-08 Campaign scope/gaps | ✅ CLOSED | Native/100G/20G app sweeps and 50G/10G HW-only distinction correct. |
| E-09 Guidance `post-run` rows | ✅ CLOSED | Populated. |
| E-10 Network unresolved footer | ✅ CLOSED | Measured sensitivity now surfaced. |
| `chart_exec_ttft` values | ✅ CLOSED | Canonical values. |
| `chart_exec_ttft` Evidence mapping | 🟡 PARTIAL | `_dist` case names fixed, but distributed queries omit network provenance; each matches Native/100G/20G and depends on row ordering to land Native. Use exact Evidence ID or case+bench+network. |
| `chart_exec_tpot` values | 🔴 OPEN / P0 | TP16 512K is **16.892 ms**, canonical is **17.4131 ms**. Other points are good. |
| `chart_exec_tpot` mapping | 🟡 PARTIAL | Same network-ambiguity problem for distributed series. |
| `chart_exec_capacity` | ✅ CLOSED | 784.1 tok/s c32, correct TP4 lineage and click IDs; no “c32 optimal” claim. |
| E-11 BabelStream | ✅ CLOSED | Copy ~1.72 TB/s and Triad ~1.46 TB/s explicitly labeled. |
| E-12 Nsight/PyTorch semantics | ✅ CLOSED | Critical path now requires timeline reconciliation. |
| E-13 TP width values | ✅ CLOSED | 4.475/6.350 ms and 31.916/28.089 s are correct. |
| E-14 Chunk fairness claim | ✅ CLOSED | 16K lowest c1 TTFT; fairness/decode-interference unresolved. |
| E-15 max_num_seqs recommendation | ✅ CLOSED | No “set to 32”; correctly called non-binding at tested 1M c4. |
| E-16 FP8-KV unsupported cause | ✅ CLOSED | Guarded NOT_RUN / backend acceptance unvalidated. |
| E-17 Prefix mixed mean | ✅ CLOSED | Uses 94.23 → 2.61 s repeat median at 1M. |
| E-18 Network sensitivity | ✅ CLOSED | Marked measured sensitivity. |
| E-19 8K stale TPOT | ✅ CLOSED | Canonical values used. |
| E-20 c1→c64 unsupported | ✅ CLOSED | Now c1→c32. |
| E-21 “Compute Bound” 128K | ✅ CLOSED | Rephrased as prefill-dominated/high activity rather than roofline claim. |
| E-22 “Compute & VRAM” 512K | ✅ CLOSED | Rephrased as prefill dominated. |
| E-23 stale 1.45 s queue | ✅ CLOSED | 134.43 s / 107.01 s shown. |
| Deployment Recipe | 🟡 PARTIAL | Filled, but still uses unproven `FLOP/pipeline dominated` and deterministic “Primary limiter” language without NCU/timeline proof. |
| What Not To Do | ✅ CLOSED | Correct measured-range wording. |

### Executive new issue
The Deployment Recipe should not say:
- `prefill (FLOP/pipeline dominated)` or
- `Primary limiter: Decode: NUMA/PCIe ring AllReduce latency; Prefill: head compute / pipeline bubbles`

as established facts. The decode synchronization contribution is cross-validated; the prefill “FLOP dominated” statement still requires NCU/roofline evidence.

---

# 4. SCALE-UP TAB

| Audit item | Status | Review |
|---|---|---|
| C1 `chart_scaleup_ttft` | ✅ CLOSED | Canonical context-baseline values, analysis populated, crossover labeled DERIVED. |
| C2 `chart_scaleup_tpot` | 🟡 MOSTLY CLOSED | Values correct. Interpretation still speaks deterministically about NUMA avoidance; better badge it CROSS-VALIDATED. |
| C3 `chart_scaleup_tps` | ✅ CLOSED | Rebuilt on one matched context-baseline lineage with exact clicks. |
| C4 `chart_scaleup_concurrency` | ✅ CLOSED | Correct title, TP8 nulls, exact TP4/TP8 lineages. |
| C5 `chart_scaleup_nccl` | ✅ CLOSED | Exact measured message sizes, BusBW, PCIe/NUMA wording, no NVLink. |
| C6 Scale-Up Decision Output | 🟡 PARTIAL | Populated and workload-scoped. But `8-GPU prefill compute FLOP scaling outweighs...` is not roofline-proven. Rephrase to “TP8 lowers measured long-prefill TTFT; exact compute-vs-communication balance requires NCU/timeline evidence.” |

---

# 5. SCALE-OUT TAB

| Audit item | Status | Review |
|---|---|---|
| D1 TP4/PP2 KV dynamic bug | ✅ CLOSED | 0.7853 / 3.1048 / 5.9106% correctly used in all 3 network objects. |
| D2 hard-coded TP4/PP4 winner | ✅ CLOSED dynamically | Leader is now metric-specific and computed per context. |
| D3 execution status vs poor performance | ✅ CLOSED | TP16 capped rows are marked completed/high sensitivity, not failed. |
| D4 network-sensitivity heatmap | ✅ CLOSED | Exact raw deltas verified. |
| D5 NVLink | ✅ CLOSED | Removed. |
| D6 61-layer contamination | 🟡 PARTIAL | `61` is gone, but one profiler matrix row now says **“27 layerwise cross-node AllReduce barriers per token.”** Layer count is not a valid substitute for measured collective count. Use trace-derived call count only. |
| D7 configured vs achieved transport | 🟡 MOSTLY CLOSED | Native fwd/smoke rev is reconciled; causal text softened. Replace `OPTIMAL (100% BASELINE)` with neutral `NATIVE BASELINE`. |
| D8 SendRecv 21.84 GB/s | ✅ CLOSED | Now message-size-specific 64M/128M/256M ~7.24/6.98/7.11 GB/s. |
| D9 “Local TP16” | ✅ CLOSED | Local TP4/TP8 vs cross-node TP16 correctly separated. |
| D10 1M matrix tok/s | ✅ CLOSED numerically | Input-ingestion rate and output tok/s separated. Static matrix still says `SLO BOTTLENECK` without an explicit SLO; use `HIGHEST TTFT AMONG TESTED` instead. |

### Heatmap raw-data recheck
TTFT deltas vs Native exactly match the ZIP (rounded):

- TP4/PP4: +2.97/+14.67% (128K), +1.64/+8.93% (512K), +1.04/+3.91% (1M)
- TP8/PP2: +1.36/+0.81%, −0.18/−0.19%, −0.13/−0.10%
- TP4/PP2: +0.66/+8.01%, +0.20/+2.37%, +0.13/+1.14%
- TP16/PP1: +51.64/+383.66%, +45.47/+333.01%, +36.36/+276.69%

(100G / 20G respectively)

---

# 6. LONG CONTEXT TAB

| Audit item | Status | Review |
|---|---|---|
| E1 1M waterfall TPOT | ✅ CLOSED | TPOT 181.97/267.41 and 177.21/259.50 now correct. |
| E1 1M waterfall KV | ✅ CLOSED | KV c1/c2/c4 now varies correctly. |
| E1 TP4 c2 TTFT/queue lineage | 🔴 **NEW REGRESSION / P0** | UI uses **150.54 s / 55.40 s**, from `tp4_closedloop_1m/c2`. Intended extension series is **139.37 s / 44.34 s** from `tp4_1m_concurrency_extension/1m_c2`. |
| E1 queue-accounting narrative | 🔴 INTERNALLY INCONSISTENT | Text quotes ~96.4% queue closure, which is derived from the extension 44.34 s value, while the table renders 55.40 s from the older V6 row. |
| E2 Prefix scaling | ✅ CLOSED | Correct first/cold, repeat median, hit/query counters, and ratios. |
| E3 `chart_long_concurrency` | 🔴 **OPEN / P0** | TP4 c2 plotted as **150.54 s** but click maps to `tp4_1m_concurrency_extension 1m_c2`, whose raw value is **139.37 s**. Data and provenance disagree. |
| E4 `chart_long_scheduler` | ✅ CLOSED | Correct 4/8/16 max_num_seqs sweep. |
| E5 `chart_long_chunk` | ✅ CLOSED | Correct values, no fairness claim, case IDs fixed. |
| E6 `chart_long_fp8` | 🟡 PARTIAL | Correct NOT_RUN state, but still rendered as a quantitative BF16 total-VRAM vs null chart under “KV dtype sensitivity.” Prefer a status card; no FP8 delta exists. |
| E7 CPU offload | ✅ CLOSED | No quantitative stale chart; NOT_RUN only. |
| E8 Long KPI cards | ✅ CLOSED | Fit and c1 cleanest/SLO-driven wording fixed. |
| E9 Distributed 1M matrix | 🟡 MOSTLY CLOSED | Data correct; remove `SLO BOTTLENECK` without explicit SLO. |
| E10 1M Serving Decision | 🔴 **OPEN / P0** | TP4 c2 again uses 150.5 s / 55.40 s while c4 comes from extension; mixed lineage. |

### Correct TP4 V8-extension 1M series
`tp4_1m_concurrency_extension`:

| c | TTFT | TPOT | Queue | KV | Output TPS |
|---|---:|---:|---:|---:|---:|
| c1 | 93.3949 s | 10.2275 ms | 0.000020 s | 12.2896% | 0.34147 |
| c2 | **139.3736 s** | **181.9740 ms** | **44.3402 s** | **15.5175%** | 0.34486 |
| c4 | 231.2675 s | 267.4106 ms | 134.4277 s | 15.5112% | 0.34666 |

The older `tp4_closedloop_1m/c2` row is a valid measurement (**150.5393 s / 239.0703 ms / 55.4011 s**) but must not be spliced into the extension c1/c2/c4 series.

---

# 7. SCHEDULER & KV TAB

| Audit item | Status | Review |
|---|---|---|
| F1 `chart_sched_kv` | ✅ NUMERIC / 🟡 MAPPING | Data correct. Distributed click queries omit network and can match 3 rows. |
| F2 running/waiting | ✅ CLOSED | Peak semantics explicit. |
| F3 queue chart | ✅ CLOSED | Correct canonical queue values and exact extension case+bench queries. |
| F4 preemptions | 🟡 MINOR | Zero preemptions is correct. Label `Zero Memory Thrashing` is stronger than the metric proves; say `0 scheduler preemptions observed`. |
| F5 max_num_seqs | ✅ CLOSED | Correct and scoped. |
| F6 scale-out runtime ledger numbers | ✅ CLOSED | KV, queue, total memory corrected. |
| F6 interpretation/SLO columns | 🟡 OPEN | `Interactive TTFT Compliant`, `Sub-15s Prefill Compliant`, etc. introduce unstated SLOs. `4-way pipeline stage KV distribution` should be “consistent with active KV being distributed across stages,” not asserted allocator mechanism. |
| F7 8K open-loop | ✅ DATA / 🟡 DECISION | Data correct and offered vs achieved distinction improved. “Capacity knee” remains a derived heuristic unless an SLO/criterion is stated. |
| F8 128K open-loop | ✅ CLOSED | Offered RPS, TTFT, queue and TPOT match raw data. |
| F9 Capacity Knee / Admission card | 🔴 OPEN | Calls points `SLO-safe` without any SLO definition; chooses 128K 0.75× as safe/knee without an explicit criterion; uses wrong TP4 1M c2 queue **55.4 s**. |

The 128K open-loop graph itself is now correct. Keep the empirical cliff description, but the operating-point recommendation must state the exact objective/threshold used.

---

# 8. PROFILER TAB

The profiler remains the largest semantic/provenance risk.

| Audit item | Status | Review |
|---|---|---|
| G1 Blackwell identity | ✅ CLOSED |
| G1 completeness | ✅ CLOSED | 14/22, 11 Native + 3 capped-100G. |
| G2 kernel categories — single-node values | ✅ VALID | TP4 prefill/decode and TP8 decode aggregate GPU-work shares are real. |
| G2 semantic label | 🟡 PARTIAL | Chart title/Y-axis now say aggregate GPU kernel-work, but analysis still says “AllReduce consumes 86.3%… of **decode time**.” Must say aggregate GPU kernel work in the exact captured profile. |
| G2 distributed aggregation | 🔴 OPEN | TP16 raw AllReduce share across valid rank CSVs is ~76.3–79.4%, mean **77.61%**, median **77.65%**. UI plots 76.2% while labeling “Rank 0; Multi-Rank Mean 77.6%.” TP4/PP4 ranks span ~22.8–41.7% AllReduce (median ~32.65%) and ~8.0–21.9% SendRecv (median ~9.6%). Current 40.0/8.3 series is not documented as one exact rank or an aggregation rule. |
| G3 PyTorch operators | 🟡 PARTIAL | 251.5 vs 583.9 ms AllReduce and 7040 calls are strong. “Sum of Selected Operator Groups” is now honestly named, but grouping recipes for addmm/MoE/etc. are still not documented. |
| G4 CUDA API | ✅ NUMERIC / 🟡 WORDING | Rebuilt correctly: 3.638/3.466/1.530/0.710/0.361/0.359/0.286 s and percentages. Use `aggregate host API time` rather than `Host API Wall-Clock Time` if API calls can overlap across threads. |
| G5 kernel latency | 🟡 PARTIAL | Title improved, but badge still says `KERNEL ROOFLINE`; tooltip still says `100% empirical`; P2P series lacks exact rank/aggregation provenance. |
| G6 Resource-Pressure ledger title | ✅ CLOSED | No longer presented as a 100% wall-clock critical path. |
| G6 ledger content | 🔴 OPEN | Still says `FLOP bound`, `Memory bandwidth bound`, `single greatest latency contributor`, and `Mitigated via CUDA graph captures` without NCU/roofline or A/B proof. |
| G7 Top 15 kernel table | ✅ STRUCTURALLY IMPROVED | Profile/phase/topology column added. Continue validating each row against one exact raw rank CSV. |
| G8 22-point completeness matrix | ✅ CLOSED structurally | 22 rows; status counts = 14 COMPLETE / 3 INCOMPLETE / 5 NOT_CAPTURED; 11 Native + 3 capped complete. |
| G8 matrix narrative | 🔴 PARTIAL | Contains `27 layerwise cross-node AllReduce barriers per token` and `avoids AllReduce barrier stalls`; both exceed the evidence. |
| G9 61-layer contamination | ✅ REMOVED | But do **not** replace model layer count with physical collective count. |
| G10 root-cause table | 🟡 PARTIAL | Main deltas corrected, but some causal/prescriptive claims still too strong. |

### Profiler-specific remaining text to remove/soften
Current 3pm HTML still contains:

- `FLOP bound during prefill`
- `Memory bandwidth bound during decode`
- `Memory bandwidth bound elementwise kernels`
- `The single greatest latency contributor in decode`
- `Mitigated via CUDA graph captures`
- `27 layerwise cross-node AllReduce barriers per token`
- `avoids AllReduce barrier stalls`
- `100% empirical evidence`
- badge `KERNEL ROOFLINE`

These were explicitly disallowed or required qualification by the closure audit.

### Profiler raw aggregation validation
From raw distributed Nsight CSVs:

**TP16/PP1 128K prefill**
- valid rank CSVs parsed: 12
- aggregate AllReduce work share range: **76.3–79.4%**
- mean: **77.61%**
- median: **77.65%**

**TP4/PP4 128K prefill**
- valid rank CSVs parsed: 16
- AllReduce share range: **22.8–41.7%**
- mean: **32.68%**
- median: **32.65%**
- SendRecv share range: **8.0–21.9%**
- median: **9.6%**

Therefore a topology-wide percentage must use:
- a named exact rank, or
- median + range, or
- another explicit aggregation function.

Do not mix a selected-rank AllReduce percentage with a SendRecv percentage from a different rank and call it one “stage” composition.

---

# 9. EVIDENCE TAB

| Audit item | Status | Review |
|---|---|---|
| H1 Status Contract | ✅ CLOSED | Primary Native + auxiliary capped + guarded status is correct. |
| H2 Scope filter | ✅ CLOSED | `MULTI_V8` now matches actual row scope. |
| H3 p95/p99 reliability | ✅ CLOSED | Separate p95/p99 flags and filters implemented with correct 93/19/7/7 counts. |
| H4 chart→Evidence exact mapping | 🔴 PARTIAL | Several handlers still use fuzzy substring queries. Distributed Executive queries match 3 network rows and happen to land Native only because row ordering currently puts Native first. Profiler queries often match multiple unrelated benchmark rows or no Evidence row. |
| H5 Decision Claim Registry | 🔴 PARTIAL | Several rows improved, but scale-out row still says PP “avoids cross-node AllReduce stalls”; 1M admission row uses wrong TP4 c2 queue 55.4 s and “Strict c=1” without a defined SLO. |
| H6 Runtime Acceptance | ✅ CLOSED | Primary/auxiliary network contract corrected. |
| H7 Post-run source | ✅ CLOSED | `SCALEOUT_NETWORK_COVERAGE.md` used instead of stale deferred-gap source. |

### Exact mapping examples still unresolved
Current fuzzy query behavior:

- `tp4_pp4_dist 128k` → **3 matches** (Native, 100G, 20G)
- `tp4_pp4_dist 1m` → **3 matches**
- `tp16_pp1_dist 1m` → **3 matches**
- `tp4_pp4 1m` → **3 matches**
- `tp4_prefill` → **4 benchmark Evidence rows**, not a unique profile artifact
- `tp4_decode` → **3 benchmark Evidence rows**
- `tp8_decode` → **0 matches**
- `flash`, `allreduce`, `sendrecv` → **0 matches**

The audit requirement was datum-level exact identity. The correct fix remains:
`evidence_id` or exact `case + bench + network_provenance`, plus a separate profile-artifact identifier for profiler-only evidence.

---

# 10. CROSS-CUTTING / DATA CONTRACT

| Audit item | Status | Review |
|---|---|---|
| I1 hard-coded performance arrays | ❌ OPEN | The 3pm HTML still manually embeds most Chart.js data arrays and the scale-out data object. Evidence says arrays are not source of truth, but implementation still carries them. |
| I2 decorative selectors | ✅ MOSTLY CLOSED | Scale-Up/Long/Scheduler “selectors” are now rendered as scope labels. Scale-Out selectors are functional. Profiler scenario chips filter the Top-15 table, though they do not re-render all profiler charts. |
| I3 `s-failed` for slow runs | ✅ CLOSED | `s-failed` remains only in CSS definition; no completed slow row uses it. |
| I4 model-manifest guardrail | 🟡 PARTIAL | 27L/20KDA/7 full-attn appears correctly in one place, but formulas/architecture values are not consistently generated from one manifest-bound object. Hard-coded architecture text still exists. |

---

# 11. COMPLETE 27-CHART RE-CHECK

| # | Canvas | 24 Sept 3pm status | Remaining action |
|---:|---|---|---|
| 1 | `chart_exec_ttft` | 🟡 | Values correct; make distributed Evidence mapping exact incl. network. |
| 2 | `chart_exec_tpot` | 🔴 | TP16 512K must be **17.413 ms**, not 16.892; mapping exactness too. |
| 3 | `chart_exec_capacity` | ✅ | Closed. |
| 4 | `chart_scaleup_ttft` | ✅ | Closed; keep crossover DERIVED. |
| 5 | `chart_scaleup_tpot` | 🟡 | Values correct; soften deterministic NUMA mechanism wording. |
| 6 | `chart_scaleup_tps` | ✅ | Matched lineage fixed. |
| 7 | `chart_scaleup_concurrency` | ✅ | Title/mapping fixed. |
| 8 | `chart_scaleup_nccl` | ✅ | Exact sizes / BusBW / PCIe-NUMA. |
| 9 | `chart_scaleout_comparison` | ✅ dynamic data | TP4/PP2 KV fixed; metric leader dynamic. |
| 10 | `chart_scaleout_context_scaling` | ✅ dynamic data | Same. |
| 11 | `chart_long_concurrency` | 🔴 | TP4 c2 wrong lineage: 150.54 → **139.37 s**. |
| 12 | `chart_long_scheduler` | ✅ | Closed. |
| 13 | `chart_long_chunk` | ✅ | Closed. |
| 14 | `chart_long_fp8` | 🟡 | Prefer NOT_RUN status card; no measured FP8 delta. |
| 15 | `chart_long_prefix` | ✅ | Correct first/repeat semantics. |
| 16 | `chart_long_offload` | ✅ | Quantitative dataset removed; NOT_RUN. |
| 17 | `chart_sched_kv` | 🟡 | Values correct; distributed Evidence mapping ambiguous. |
| 18 | `chart_sched_running_waiting` | ✅ | Peak semantics correct. |
| 19 | `chart_sched_queue_mean` | ✅ | Correct values and extension mapping. |
| 20 | `chart_sched_preemptions` | 🟡 | Numeric correct; remove “Zero Memory Thrashing” inference. |
| 21 | `chart_sched_max_seqs` | ✅ | Closed. |
| 22 | `chart_sched_open_loop_8k` | ✅ data / 🟡 decision | Data correct; capacity knee needs explicit criterion/SLO. |
| 23 | `chart_sched_open_loop_128k` | ✅ | Correct canonical data. |
| 24 | `chart_prof_kernel_categories` | 🔴 semantic/provenance | Single-node real; distributed rank aggregation and “decode time” wording remain. |
| 25 | `chart_prof_pytorch_operators` | 🟡 | AR data strong; grouping recipe still missing. |
| 26 | `chart_prof_cuda_api` | ✅ numeric / 🟡 wording | Rebuilt correctly; call it aggregate API time. |
| 27 | `chart_prof_kernel_latency` | 🟡 | Remove roofline/100%-empirical wording; add rank provenance. |

---

# 12. NEW REGRESSIONS / ISSUES INTRODUCED IN 3PM BUILD

These are important because they were not simply “comments not implemented”; they were introduced while implementing the closure fixes.

## N-01 — TP4 1M c2 mixed-lineage regression (P0)
Appears in:
- Long SLO table
- `chart_long_concurrency`
- 1M Serving Decision table
- Scheduler Capacity/Admission card
- Decision Claim Registry

Wrong/mixed values:
`150.54s`, `55.40s` combined with extension TPOT/KV or c4 data.

Correct V8-extension c2:
`139.3736s`, `181.9740ms`, `44.3402s`, `15.5175%`.

## N-02 — Executive TP16 512K TPOT regression (P0)
Current: `16.892ms`  
Canonical: `17.4131ms`

## N-03 — 27-layer count converted into a collective-count claim (P1)
`27 hidden layers` is real model metadata.  
`27 layerwise cross-node AllReduce barriers per token` is **not established by the model manifest**. Physical collective launches must come from trace data.

## N-04 — SLO-safe labels without an SLO (P1)
New scheduler decision text introduces:
- `Interactive TTFT Compliant`
- `Sub-15s Prefill Compliant`
- `Leading SLO-safe operating point`
- `SLO BOTTLENECK`

without defining a product SLO. Replace with measured ordering or explicitly define the threshold first.

## N-05 — Profiler semantic overclaims survive despite new resource-pressure title (P1)
The title was fixed, but body text reintroduces:
- FLOP-bound
- memory-bandwidth-bound
- latency contributor
- CUDA Graph mitigation
as established facts.

---

# 13. P0 FIX LIST BEFORE NEXT DATA-SIGNOFF REVIEW

1. **Use one TP4 1M concurrency lineage consistently.**
   - For the c1/c2/c4 extension story, use `tp4_1m_concurrency_extension` throughout.
   - Replace every 150.54/55.40 c2 value in that story with 139.37/44.34.
   - Do not delete the older `tp4_closedloop_1m/c2` Evidence row; it is a legitimate separate measurement.

2. **Fix `chart_exec_tpot` TP16/PP1 512K**
   - 16.892 → **17.413 ms**.

3. **Make chart→Evidence linkage exact**
   - add `evidence_id` or `case+bench+network_provenance` to every datum.
   - profiler charts need profile-artifact IDs, not fuzzy E2E-run text searches.

4. **Remove remaining profiler denominator/causality violations**
   - `86.3% of decode time` → `86.3% of aggregate GPU kernel work in exact TP4 decode profile`.
   - distributed shares must state rank or median/range aggregation.

5. **Remove/qualify all unsupported profiler bottleneck labels**
   - FLOP-bound / memory-bandwidth-bound only with NCU/roofline.
   - CUDA Graph only as follow-up A/B candidate.

6. **Remove `27 layerwise AllReduce barriers/token`**
   - use trace-derived physical launch/call count if needed.

7. **Remove unstated SLO verdicts**
   - Scheduler and static scale-out matrices must not use “SLO-safe/compliant/bottleneck” without an explicit threshold.

---

# 14. P1 FIX LIST

1. Replace Native `OPTIMAL (100% BASELINE)` with `NATIVE BASELINE`.
2. Replace FP8-KV quantitative chart with a NOT_RUN status card, or make the BF16 total-memory baseline explicitly non-comparative.
3. Change `Zero Memory Thrashing` to `0 scheduler preemptions observed`.
4. Rephrase Scale-Up long-prefill “FLOP scaling” mechanism as an interpretation requiring NCU/timeline proof.
5. In the profiler completeness matrix, replace “avoids AllReduce barrier stalls” with measured communication-structure language.
6. Make TP16/PP1 and TP4/PP4 distributed profiler composition use one reproducible aggregation rule.
7. Document PyTorch operator grouping recipes.
8. Remove `KERNEL ROOFLINE` badge and `100% empirical` phrasing.
9. Use `aggregate CUDA API time` rather than “Host API Wall-Clock Time” where concurrency/overlap could matter.
10. Change static `RECOMMENDED` / `SLO BOTTLENECK` fallback labels to neutral measured descriptors.

---

# 15. P2 / ARCHITECTURE HARDENING

The largest remaining engineering debt is unchanged:

```text
raw artifacts
  -> FINAL_VALIDATION / coverage / combined_vllm_runs
  -> normalized hardware/profile joins
  -> DASHBOARD_CANONICAL_DATA.json
  -> derived calculation functions
  -> chart data with exact provenance
  -> UI
```

Every chart datum should carry:

```text
evidence_id
case
bench
network_provenance
TP / PP
context / load
metric
unit
value
sample_count
p95_reliable
p99_reliable
evidence_class
artifact_path
```

For profiler-only datapoints also carry:

```text
profile_id
node
rank / worker
phase
aggregation_method
PROFILE_VALIDATION status
raw CSV path
```

This is the durable way to prevent the exact regression seen in the 3pm build, where two legitimate TP4 c2 runs were accidentally mixed.

---

# 16. FINAL SIGN-OFF ASSESSMENT

## What is now genuinely strong
- Campaign status truth
- Primary vs auxiliary network scope
- Evidence ledger and reliability gating
- Scale-Up matched baseline charts
- Scale-Out application sensitivity data
- Configured-vs-achieved network presentation
- Prefix first/repeat analysis
- 128K open-loop chart
- max_num_seqs experiment
- CUDA API numerical rebuild
- 22-point profiler coverage matrix

## What still blocks publication/data sign-off
- TP4 1M c2 mixed-lineage regression
- TP16 512K TPOT wrong point
- profiler aggregation/denominator/causal overclaims
- non-exact chart→Evidence mapping
- SLO/admission verdicts without a defined SLO

### Bottom line
**The team implemented most of the closure audit correctly, but not all of it.** The 3pm build is substantially closer to sign-off than the 9pm build, yet it should remain **“data-signoff pending”** until the P0 items above are corrected and revalidated.

The most important implementation lesson from this pass is that **valid measurements from different run lineages must never be spliced into one visual or recommendation**. The dashboard needs exact datum-level provenance, not fuzzy case-family matching.
