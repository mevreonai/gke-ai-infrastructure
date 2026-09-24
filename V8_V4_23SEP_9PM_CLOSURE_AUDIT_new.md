# V8-FULL Dashboard — FINAL Closure Audit for 23 Sept 9pm V4

**Dashboard reviewed:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_23rdSept_9pmIST.html`  
**Previous core audit:** `V8_Dashboard_realrun_v4_new_latest_RAW_DATA_DEEP_AUDIT.md`  
**Raw result package:** `results_V8_runs.zip`  
**Canonical validation root:** `results/real_data/final_validation/`  
**Purpose of this revision:** one consolidated closure checklist that tells the implementation team **exactly which TAB, graph/card/table, HTML locator, value/text and evidence source must change** before data sign-off.

---

# 0. Final review verdict

The 23 Sept 9pm build is materially better than the earlier V4 and closes a large portion of the original audit. The numerical Evidence ledger is now particularly strong.

However, the dashboard is **not yet publication/data-signoff ready**.

The remaining problems fall into four classes:

1. **Incorrect numerical data still rendered in a few new views**
   - 1M SLO waterfall TPOT/KV
   - 128K open-loop chart
   - prefix hit-conditioned latency and cache-hit ratios
   - TP4/PP2 KV values in the interactive Scale-Out data object
   - several static Executive memory values

2. **Correct raw numbers given the wrong semantics**
   - aggregate Nsight GPU kernel work called “critical path”
   - CUDA API aggregate time mixed with GPU-time percentages
   - total VRAM called KV memory
   - configured cap labels confused with achieved transport
   - production/SLO verdicts without an explicit SLO

3. **Stale text / model-topology contamination**
   - `61 layers` appears although the actual model has **27 layers**
   - `NVLINK` appears although this RTX/G4 setup is PCIe/NUMA
   - `RTX PRO 6000 Ada` remains in two places
   - stale `1.45s` queue, `7.84/8.41ms`, `27.80s / 22%`, `1,240 tok/s`
   - “native-only / cap sensitivity deferred” remains although capped application sweeps were executed

4. **UI/evidence wiring issues**
   - several chart clicks do not resolve to the exact Evidence row
   - Scale-Out dynamic table always calls TP4/PP4 `RECOMMENDED` regardless of selected metric
   - Evidence reliability combines p95 and p99 into one invalid “High-N” flag
   - some selectors are decorative rather than functional
   - frontend still manually carries numerical arrays instead of consuming one canonical normalized object

---

# 1. What was revalidated in this final pass

## 1.1 Complete HTML surface

Reviewed all **7 tabs**:

1. Executive
2. Scale-Up
3. Scale-Out
4. Long Context
5. Scheduler & KV
6. Profiler
7. Evidence

Reviewed all **27 canvas/chart IDs**:

```text
chart_exec_ttft
chart_exec_tpot
chart_exec_capacity

chart_scaleup_ttft
chart_scaleup_tpot
chart_scaleup_tps
chart_scaleup_concurrency
chart_scaleup_nccl

chart_scaleout_comparison
chart_scaleout_context_scaling

chart_long_concurrency
chart_long_scheduler
chart_long_chunk
chart_long_fp8
chart_long_prefix
chart_long_offload

chart_sched_kv
chart_sched_running_waiting
chart_sched_queue_mean
chart_sched_preemptions
chart_sched_max_seqs
chart_sched_open_loop_8k
chart_sched_open_loop_128k

chart_prof_kernel_categories
chart_prof_pytorch_operators
chart_prof_cuda_api
chart_prof_kernel_latency
```

Also reviewed:
- KPI cards
- Deployment Decision Map
- configuration guidance tables
- topology/network heatmap
- scale-out dynamic decision matrix
- 1M SLO waterfall
- prefix table
- scheduler runtime ledger
- distributed profiler completeness table
- profiler root-cause table
- Evidence filters
- Decision Claim Registry
- chart→Evidence drill-down code
- footer/status-contract wording.

---

## 1.2 Evidence ledger reconciliation

The 9pm HTML contains **126 Evidence rows**, matching `coverage.json`.

For the **119 completed rows**, I programmatically reconciled the rendered:

- TTFT
- TPOT
- peak KV
- queue mean

against `combined_vllm_runs.csv`.

Result:

> **118/119 rows match canonical data within normal display rounding.**

The remaining row is also just display rounding:
- `tp4_closedloop_8k / c16` rendered 1.16s vs canonical 1.155996s.

Therefore:

> **The Evidence row-level metric ledger is fundamentally sound.**

The main remaining Evidence problems are **reliability classification, stale scope wording and drill-down wiring**, not the core row metrics.

---

# 2. Canonical campaign truth that every tab must respect

From `FINAL_VALIDATION.json`, `coverage.json`, `combined_vllm_runs.csv`:

```text
coverage rows                         126
completed application rows           119
NOT_RUN                               7
failed application rows              0

native application rows              95
  fixed native                       80
  open-loop native                   15

auxiliary capped application rows    24
  configured 100G                    12
  configured 20G                     12

distributed profiles expected        22
distributed profile validation files 17
distributed profiles complete        14

profiles_all_complete                false
nccl_policy_ok                       false
strict_full_coverage                 false
full_suite_valid                     false
```

### Critical profiler denominator

The **14 complete distributed profiles are not “14 native profiles.”**

They consist of:
- **11 complete Native distributed profiles**
- **3 complete configured-100G distributed profiles**

Three Native profiles are incomplete:
- TP8/PP2 batched decode c8: Node0 missing
- TP4/PP4 batched decode c8: Node0 + Node1 missing
- TP16/PP1 batched decode c8: Node1 missing

So the correct KPI is:

```text
Distributed profile coverage: 14 / 22 expected complete
  11 Native complete
  3 capped-100G complete
```

Do not label this `Native Distributed Profiles = 14/22`.

---

# 3. MASTER IMPLEMENTATION CHANGE MAP

The tables below are the final implementation checklist.

Legend:

- **P0** = data/provenance/sign-off blocker
- **P1** = important semantic/decision correctness
- **P2** = UI/data-contract hardening

---

# A. GLOBAL HEADER / CROSS-TAB STATUS

| ID | Priority | Exact location | Current issue | Required correction | Source |
|---|---|---|---|---|---|
| G-01 | P1 | Topbar, HTML ~97 | Title says `Native-Only Decision-Intelligence Mockup v4` | Rename to primary-native + auxiliary-sensitivity wording | `FINAL_VALIDATION.json` |
| G-02 | P1 | Topbar subtitle, ~97 | Says `GCP_NATIVE only` | `Primary deployment evidence: GCP_NATIVE · auxiliary application sensitivity: configured-100G / configured-20G` | coverage |
| G-03 | P1 | Executive KPI, ~126 | `Strict Suite Sign-off: Not Complete (119/119 runs)` is confusing | Say `119 completed / 126 configured coverage rows · 7 guarded NOT_RUN · strict sign-off incomplete` | FINAL_VALIDATION |
| G-04 | P0 | Executive KPI, ~129 | `Native Distributed Profiles 14/22` | Rename `Distributed Profiles 14/22 complete`; show `11 Native + 3 capped-100G` | profile validation |
| G-05 | P0 | Profiler ~662; Scheduler ~577 | `RTX PRO 6000 Ada` remains | Replace everywhere with `NVIDIA RTX PRO 6000 Blackwell Server Edition` | hardware raw |
| G-06 | P1 | Footer ~3162 | Says `native-only UI mockup` | Remove native-only wording | campaign scope |
| G-07 | P1 | Footer ~3162 | Claims `Preview contains no fabricated V8 performance values` | Remove until P0 corrections below are closed | this audit |

---

# B. EXECUTIVE TAB — EXACT FIXES

## B1. KPI row

### E-01 — Distributed profiler KPI denominator

**Location**
- Tab: **Executive**
- KPI: `Native Distributed Profiles`
- HTML ~129

**Current**
```text
14 / 22 COMPLETE
Native Distributed Profiles
```

**Problem**
14 includes three capped-100G complete profiles.

**Replace with**
```text
Distributed Profile Coverage
14 / 22 COMPLETE
11 Native + 3 configured-100G complete
8 expected points incomplete/missing
```

**Source**
```text
final_validation/FINAL_VALIDATION.json
profiles_multi_node_native/**/PROFILE_VALIDATION.json
profiles_multi_node_100g/**/PROFILE_VALIDATION.json
```

---

## B2. Deployment Decision Map

### E-02 — 8K memory/KV is wrong

**Location**
- Tab: Executive
- Card: `Deployment Decision Map`
- Row: `Short-context interactive (8K)`
- HTML ~141

**Current**
```text
1.25% KV · 29.8 GB VRAM
```

**Canonical**
TP4/PP1 qualification 8K c1:

```text
peak_kv_usage = 0.001259... = 0.126%
gpu_mem_used_peak_mb = 88,769 MiB ≈ 86.69 GiB
```

**Replace with**
```text
~0.126% KV · ~88,769 MiB (~86.69 GiB) peak GPU memory
```

Do not call it 29.8 GB.

**Source**
```text
combined_vllm_runs.csv
case=tp4_qualification
bench=8k_c1
```

---

### E-03 — TP4/PP4 128K VRAM is wrong

**Location**
- Deployment Decision Map
- Row `Long prompt, c1 (128K)`
- HTML ~142

**Current**
```text
45.2 GB VRAM
```

**Canonical**
TP4/PP4 Native 128K:
```text
gpu_mem_used_peak_mb = 90,967 MiB ≈ 88.84 GiB
```

**Replace**
Use the canonical telemetry value.

---

### E-04 — memory units/headroom must be consistent

**Locations**
- Executive Decision Map ~143–144
- Long Context KPI ~494
- Scheduler Scale-Out ledger
- FP8/offload cards

**Problem**
The UI mixes:
- marketed `96 GB`
- telemetry `MiB`
- display `GB`
- derived headroom

without unit conversion.

Hardware raw reports total device memory approximately:
```text
97,887 MiB
```

Example TP4/PP4 peak:
```text
90,967 MiB
```

So telemetry headroom is:
```text
6,920 MiB ≈ 6.76 GiB
```

**Required rule**
Keep one of:
```text
90,967 MiB / 97,887 MiB
```
or
```text
88.84 GiB peak; ~6.76 GiB telemetry headroom
```

Do not subtract a GiB-style measurement from a marketing `96 GB` number without labeling the conversion.

---

### E-05 — 1M c1 mechanism confidence too strong

**Location**
- Deployment Decision Map 1M c1 row ~144

**Current**
```text
Interpretation [HIGH]:
pipelined P2P activations ... avoid cross-node all-reduce
```

**Correction**
Observation is HIGH confidence.
Mechanism should remain **MEDIUM / CROSS-VALIDATED**, not HIGH causal proof.

Suggested:
```text
Observed: TP4/PP4 is lowest TTFT among tested native c1 topologies.
Interpretation [MEDIUM]: communication structure is consistent with lower
cross-node TP exposure; exact critical-path contribution requires topology-
matched timeline attribution.
```

---

### E-06 — 1M concurrency row overstates “strict cap”

**Location**
- Deployment Decision Map ~145

**Current**
```text
Strict admission cap c=1 required
Interpretation: compute saturation and KV prefill contention
```

**Data supports**
- c2 already has severe queue + TPOT degradation.
- c1 is the cleanest measured point.
- KV remains only ~15%, so “KV contention” is not demonstrated.

**Replace**
```text
c1 is the cleanest measured operating point.
c2 already incurs 35–44s queue and ~177–182ms TPOT.
Production admission cap must be selected against an explicit TTFT/TPOT SLO.
Exact hardware/runtime cause beyond queueing is unresolved without a matched timeline.
```

---

### E-07 — scale-out causal wording too strong

**Location**
- Deployment Decision Map ~146

**Current**
```text
P2P ... avoid cross-node all-reduce collective barrier stalls
```

**Keep observation**
```text
TP4/PP4 +3.91% TTFT at configured-20G versus TP16/PP1 +276.7% at 1M
```

**Change mechanism**
to:
```text
CROSS-VALIDATED interpretation: topology produces radically different fabric
exposure; exact exclusive critical-path mechanism remains timeline-scoped.
```

---

## B3. Campaign Scope / Gaps

### E-08 — stale cap-deferred statement

**Location**
- `Campaign Scope / Gaps`
- HTML ~151–153

**Current**
```text
Measured campaign dimension: GCP_NATIVE
Deferred by design: 100G/50G/20G/10G bandwidth-cap sensitivity
```

**Wrong**

Correct:
```text
Application E2E:
  Native + configured-100G + configured-20G measured

Hardware microbench:
  Native + 100G + 50G + 20G + 10G measured

Not established:
  application E2E at 50G/10G
  local physical 2×10GbE equivalence
  minimum production bandwidth threshold
```

---

## B4. Configuration Guidance Matrix

### E-09 — all `post-run` rows must be populated or removed

**Location**
- Card ID `executive-config-guidance`
- HTML ~156–186

There are seven rows still carrying `post-run`.

The data already exists. Populate with measured/derived guidance or remove the table from production UI.

At minimum:

```text
Interactive c1:
TP4/PP1 has lower TPOT than TP8/PP1.

Long single-node prefill:
TP8/PP1 overtakes TP4/PP1 at long context; use exact context/SLO.

Distributed long prompt c1:
TP4/PP4 has lowest TTFT among the four tested Native topologies.

1M concurrency:
c2 already shows severe queue/TPOT degradation; no distributed c2/c4 evidence.

Network sensitivity:
measured on Native/configured-100G/configured-20G.
```

---

### E-10 — guidance footer says network unresolved

**Location**
- ~183–185

**Current**
```text
Bandwidth-cap sensitivity remains unresolved in this native-only campaign.
```

**Replace**
Application sensitivity is measured at configured 100G/20G; only unmeasured conditions remain unresolved.

---

## B5. `chart_exec_ttft`

**Canvas:** `chart_exec_ttft`  
**HTML card:** ~188  
**JS:** ~3355–3376

### Numerical verdict
✅ Current plotted TTFT values are canonical context-baseline / Native values.

### Required changes
- distributed click mapping currently uses `tp4_pp4` / `tp16_pp1`; Evidence cases are `tp4_pp4_dist` / `tp16_pp1_dist`.
- analysis strip should not contain a concurrency claim unrelated to the chart.
- change `c > 2 induces queue stall` to no concurrency statement here; if retained elsewhere, use `c >= 2` for 1M single-node.

---

## B6. `chart_exec_tpot`

**Canvas:** `chart_exec_tpot`  
**HTML ~189; JS ~3379–3400**

### Numerical verdict
✅ Current TPOT points are now consistent with canonical c1 rows.

### Required changes
- distributed click mapping needs `_dist` case IDs.
- wording such as `4-GPU barrier vs 8-GPU FLOPS` must be a cross-validated interpretation, not direct measurement.
- TP4/PP2 actually has slightly lower distributed TPOT than TP4/PP4 at several long-context points; do not imply TP4/PP4 wins every metric.

---

## B7. `chart_exec_capacity`

**Canvas:** `chart_exec_capacity`  
**HTML ~190; JS ~3402–3422**

### Data arrays
TP4 c1/c4/c8/c16/c32:
✅ canonical `tp4_closedloop_8k`.

TP8 c1/c8:
✅ measured, but comes from a different qualification lineage.

### Still wrong in card text
```text
c=32 (1,240 tok/s saturation)
Cap concurrency at c=32
```

Canonical TP4 closed-loop c32:
```text
~784.06 output tok/s
```

### Required UI rule
Do not define c32 as “safe/optimal” without a TPOT/TTFT SLO.

### Evidence click bug
The TP4 chart click code sends:
```text
tp4_qualification 8k_c4
tp4_qualification 8k_c16
...
```
but those points belong to:
```text
tp4_closedloop_8k / c4,c8,c16,c32
```

Fix click mapping.

---

## B8. Hardware Ceiling ↔ Application Achieved

**Location**
- Executive ~210

### E-11 — BabelStream metric needs exact kernel provenance

Current:
```text
BabelStream 1,716 GB/s measured
```

Raw values include approximately:
```text
Copy  ~1,710–1,719 GB/s
Triad ~1,463–1,466 GB/s
```

Therefore label the kernel:
```text
BabelStream Copy peak ~1.72 TB/s effective benchmark rate
BabelStream Triad ~1.46 TB/s
```

Do not call the >spec value “L2 amplified” as a measured fact unless that mechanism was separately proven.

### E-12 — Nsight source description
Current:
```text
Nsight / PyTorch = critical path / operator attribution
```

Change to:
```text
Nsight = kernel/resource/timeline evidence
PyTorch = framework/operator evidence
critical path only when timeline-exclusive analysis exists
```

---

## B9. Knobs That Matter / Do Not

**Location**
- Executive ~211–218

### E-13 — TP width values stale

Current:
```text
7.84 vs 8.41 ms
7.2% faster
TP8 22% faster at 512K
```

Canonical matched context baseline:
```text
8K TPOT:
TP4 4.475ms
TP8 6.350ms
TP4 is ~29.5% lower TPOT
(or TP8 ~41.9% higher)

512K TTFT:
TP4 31.916s
TP8 28.089s
TP8 is ~12.0% lower TTFT
```

---

### E-14 — chunk 4K fairness claim unsupported

Current:
```text
4K candidate compromise for throughput/jitter
```

The available c1 chunk experiment proves only:
```text
4K  122.049s
8K   93.277s
16K  88.951s
```

No matched fairness/jitter evidence proves 4K is the compromise.

Use:
```text
16K lowest measured c1 TTFT.
Fairness/decode-interference optimum remains unresolved.
```

---

### E-15 — max_num_seqs recommendation unsupported

Current:
```text
Set to 32 for optimal throughput/latency trade-off
```

This mixes:
- max_num_seqs sweep
- closed-loop concurrency

The 1M c4 max_num_seqs experiment tests **4/8/16**, not 32.

Measured conclusion:
```text
max_num_seqs 4/8/16 has ~0.05% TTFT spread at TP4/PP1 1M c4.
It is non-binding in that tested state.
```

Do not recommend 32 from this experiment.

---

### E-16 — FP8-KV reason unsupported by coverage

Current:
```text
KDA linear architecture requires BF16 KV backend
Do not attempt FP8 KV cache
```

Coverage says `NOT_RUN`; it does not by itself prove that architectural rule.

Use:
```text
GUARDED NOT_RUN / backend acceptance not validated in this campaign.
```

If an explicit server/backend log gives the rejection reason, link that exact log before publishing a stronger statement.

---

### E-17 — prefix line uses mixed mean as hit

Current:
```text
93.39s -> 48.35s warm prefix hit
```

This is not hit-conditioned repeat latency.

Use the Top/Long Context correction in section F below.

---

### E-18 — network cap marked unresolved

Current:
```text
UNRESOLVED
```

Change to:
```text
MEASURED AUXILIARY SENSITIVITY
```
for Native/100G/20G application comparisons.

---

## B10. Bottleneck Regime Map

**Location**
- Executive ~221–226

### E-19 — 8K TPOT stale
Replace 7.84/8.41 with canonical matched values.

### E-20 — c=1 to c=64 is unsupported
There is no canonical c64 closed-loop concurrency point.
The open-loop client concurrency field is not equivalent to a c64 closed-loop sweep.

### E-21 — “Compute Bound” at 128K is not established
`GPU util peak=100%` does not prove compute-bound.
Use:
```text
high GPU activity / prefill dominated
```
unless NCU/roofline/timeline evidence proves compute-bound.

### E-22 — 512K `Compute & VRAM` as bottleneck is too strong
Memory occupancy can be high without being the critical bottleneck.

### E-23 — stale 1M queue
Current:
```text
c4 queue mean 1.45s
```
Canonical TP4 c4:
```text
134.4277s
```

Also do not combine distributed TP4/PP4 c1 TTFT with single-node concurrency queue in one observation without explicitly separating configurations.

---

## B11. Deployment Recipe Card

**Location**
- Executive ~227

Still almost entirely placeholder.

**Action**
Populate from the now available validated data or remove from the production page.

Also change:
```text
bandwidth sensitivity unresolved
```
to the measured-sensitivity wording.

---

## B12. “What Not To Do”

**Location**
- Executive ~229

Current:
```text
Do not infer bandwidth sensitivity from a native-only campaign.
```

Campaign is no longer native-only.

Replace:
```text
Do not extrapolate beyond the measured Native / configured-100G /
configured-20G application points; do not infer 50G/10G application
behavior or local 2×10GbE equivalence without runs.
```

---

# C. SCALE-UP TAB — EXACT FIXES

## C1. `chart_scaleup_ttft`

**Canvas:** `chart_scaleup_ttft`  
**HTML ~259; JS ~3426–3445**

✅ Numerical series are correct and use `tp4_context_baseline` / `tp8_context_baseline`.

**Remaining**
- fill the analysis strip instead of `post-run`.
- if showing a crossover, label it **DERIVED**, not measured.

---

## C2. `chart_scaleup_tpot`

**Canvas:** `chart_scaleup_tpot`  
**HTML ~260; JS ~3448–3467**

✅ Numerical series correct.

**Remaining**
- fill analysis strip.
- keep mechanism as cross-validated rather than exact critical-path attribution.

---

## C3. `chart_scaleup_tps`

**Canvas:** `chart_scaleup_tps`  
**HTML ~263; JS ~3470–3496**

### Problem: “Matched Workload” silently mixes lineages

Current 8K TP4 values use `tp4_closedloop_8k`; TP8 values use `tp8_qualification`.

For the cleanest matched comparison, use one lineage.

Recommended rebuild:
```text
tp4_context_baseline vs tp8_context_baseline:
8K c1
128K c1
512K c1
1M c1
```

Canonical output TPS:

```text
TP4:
161.892
24.707
1.976
0.342

TP8:
119.633
22.412
2.231
0.426
```

If retaining 8K c8, use a clearly matched qualification pair:
```text
tp4_qualification 8k_c8 ~551.51
tp8_qualification 8k_c8 ~445.94
```

Do not silently mix campaigns.

### Click mapping
Current generic `tp4 8k_c1` query does not resolve to a unique Evidence row.

Use exact Evidence IDs or exact case+bench.

---

## C4. `chart_scaleup_concurrency`

**Canvas:** `chart_scaleup_concurrency`  
**HTML ~264; JS ~3498–3509**

### Current title is wrong
Card says:
```text
TTFT / TPOT vs Concurrency
```
but chart plots:
```text
Output Tokens / Second
```

Rename:
```text
8K Closed-Loop Output Throughput vs Concurrency
```

or actually add TTFT/TPOT series.

### TP8 series
Only c1/c8 exist in the canonical qualification lineage; keep nulls elsewhere.

### Evidence
Add exact click mapping and case lineage.

---

## C5. `chart_scaleup_nccl`

**Canvas:** `chart_scaleup_nccl`  
**HTML ~265; JS ~3512–3522**

✅ Message sizes now match measured hardware points:
```text
16K / 128K / 512K / 64M / 128M / 256M
```

### Remaining wording
Make clear:
- this is **NCCL bus bandwidth**, not application bandwidth;
- TP8 spans the node's PCIe/NUMA layout;
- no NVLink terminology.

---

## C6. Scale-Up Decision Output

**Location**
- `scaleup-decision-output` ~267–282

Still placeholders.

Populate or remove.

Suggested measured points:
```text
8K c1: TP4 lower TPOT
128K c1: TP4 lower TTFT
512K c1: TP8 lower TTFT by ~12%
1M c1: TP8 lower TTFT by ~19.9%, TP4 still lower TPOT
```

No universal TP winner.

---

# D. SCALE-OUT TAB — EXACT FIXES

## D1. `chart_scaleout_comparison`

**Canvas:** `chart_scaleout_comparison`  
**JS ~3608 onward**

✅ TTFT values are correct for Native and dynamic cap modes.

### P0 dynamic data bug: TP4/PP2 KV values

In `scaleoutMetricsData`, current TP4/PP2 KV:

```text
128K 0.74%
512K 2.88%
1M   5.50%
```

Canonical:
```text
128K 0.7853%
512K 3.1048%
1M   5.9106%
```

Correct in **all three network-mode objects**, because the KV field is the same canonical runtime value for those runs.

---

## D2. `chart_scaleout_context_scaling`

**Canvas:** `chart_scaleout_context_scaling`

✅ TTFT data correct.

### Dynamic recommendation logic is wrong

**JS ~3720–3722**

Current:
```javascript
const isBest = (t.id === 'tp4_pp4');
const verdict = isBest ? 'RECOMMENDED' : ... 'VIABLE';
```

This hard-codes TP4/PP4 as recommended **for every selected metric**.

That is false:
- for Native 1M TPOT, TP4/PP2 = 10.54ms vs TP4/PP4 = 10.64ms
- 128K TPOT TP4/PP2 = 5.507ms vs TP4/PP4 = 5.632ms
- queue/KV/objective can produce different ordering
- no SLO exists for generic “RECOMMENDED.”

**Fix**
Compute metric-specific leader only when the objective is directionally defined, and render:
```text
lowest measured <metric> among tested cells
```
rather than `RECOMMENDED`.

---

## D3. Scale-Out dynamic table status semantics

Current:
- TP16 20G becomes `s-failed / CROSS-NODE BARRIER STALL`

Execution actually completed.

Separate:
```text
execution_status = COMPLETED
sensitivity = HIGH
SLO_status = only if an explicit SLO is supplied
```

Do not style completed auxiliary measurements as failed runs.

---

## D4. Topology × Network Sensitivity Heatmap

**Location**
- ~355–380

### Values broadly correct, but regenerate exact deltas

Canonical TTFT delta vs Native:

```text
TP4/PP4
128K  +2.967% / +14.673%
512K  +1.639% / +8.927%
1M    +1.042% / +3.905%

TP8/PP2
128K  +1.365% / +0.805%
512K  -0.176% / -0.194%
1M    -0.127% / -0.104%

TP4/PP2
128K  +0.659% / +8.007%
512K  +0.204% / +2.374%
1M    +0.134% / +1.144%

TP16/PP1
128K  +51.638% / +383.660%
512K  +45.473% / +333.011%
1M    +36.358% / +276.689%
```

Current table rounds a few TP4/PP2 / TP8 values incorrectly.

Generate, don't hand-maintain.

---

### D5 — remove NVLink

**Location**
- Heatmap TP8/PP2 128K row ~367

Current:
```text
INTRA-NODE NVLINK DOMINATED
```

Incorrect for this G4 RTX topology.

Use:
```text
LOW APPLICATION TTFT SENSITIVITY IN THIS MEASURED CAP SWEEP
```

Do not infer the mechanism from E2E only.

---

### D6 — remove 61-layer contamination

**Location**
- Heatmap finding ~379

Current:
```text
TP16 requires 61 layerwise AllReduce operations...
```

Actual 48B model manifest:
```text
num_hidden_layers = 27
20 KDA layers
7 full-attention layers
```

More importantly, **physical NCCL launch count cannot be inferred from layer count anyway**.

Delete `61 layerwise AllReduce operations`.

Use actual trace call counts only for the exact profiled workload/rank.

**Source**
```text
results/real_data/model_validation.json
```

---

## D7. Configured vs Measured Transport panel

**Location**
- Card ID `network-layer-bandwidth-panel`
- ~384–399

### Native reverse value wrong/unsupported
Current:
```text
173.58 fwd (171.2 rev)
```

Hardware smoke:
```text
173.603 fwd
173.593 rev
```

Application `IPERF_VALIDATION.json` records forward ~173.585 only.

Use one source consistently and name it.

### Causal takeaway too strong
Current:
```text
P2P pipeline stages fully absorb rate limits
```

Replace:
```text
PP-oriented tested topologies show substantially lower application-level
TTFT sensitivity than TP16/PP1 over the measured cap points.
```

No “fully absorb”.

---

## D8. Native Network Verification — NCCL SendRecv

Wherever the UI shows:
```text
NCCL SendRecv 21.84 GB/s cross-node
```
remove it.

Large-message Native SendRecv processed points are approximately:
```text
64M   ~7.24 GB/s
128M  ~6.98 GB/s
256M  ~7.11 GB/s
```

Show:
- message size
- alg_bw
- bus_bw
- network provenance

Do not conflate the ~173.6 Gb/s iperf roof with NCCL transport bandwidth.

---

## D9. “Local TP4/TP8/TP16” terminology

TP16 cannot be local on an 8-GPU node.

Use:
```text
local TP4
local TP8
cross-node TP16
```

---

## D10. Native 1M matrix / Scale-Out decision table

Locations ~345 and ~412.

Current:
```text
35k tok/s
35,014 tok/s
```

Always label:
```text
~35,005 input tokens/s derived prompt-ingestion rate
```

Keep output throughput separately:
```text
~1.107 output tok/s
```

---

# E. LONG CONTEXT TAB — EXACT FIXES

## E1. 1M SLO Degradation Waterfall

**Card ID:** `slo-waterfall-card`  
**HTML ~429–444**

This is a **P0 numerical blocker**.

### TPOT currently wrong

Current table:
```text
TP4 c2 15.34ms
TP4 c4 25.45ms
TP8 c2 18.06ms
TP8 c4 29.89ms
```

Canonical:

```text
TP4/PP1
c1  10.2275ms
c2 181.9740ms
c4 267.4106ms

TP8/PP1
c1  12.0534ms
c2 177.2082ms
c4 259.4953ms
```

The current values appear to scale baseline TPOT using the TTFT multiplier instead of reading `mean_tpot_ms`.

---

### KV currently wrong

Current table holds KV constant.

Canonical:

```text
TP4
c1 12.2896%
c2 15.5175%
c4 15.5112%

TP8
c1 12.1773%
c2 15.2699%
c4 15.3695%
```

---

### Verdict wording
Do not label c1 `PRODUCTION VIABLE` or c4 `SLO VIOLATION` unless an explicit SLO is shown.

Use:
```text
c1 = cleanest measured point
c2 = queue/TPOT cliff begins
c4 = severe measured degradation
```

---

### “KV identical” narrative is false
Replace with:
```text
KV increases modestly to ~15% but remains far from exhaustion; preemptions stay zero.
```

---

### Queue-accounting opportunity
Derived from measured values:

```text
TP4 c1->c2: ~96.4% of added TTFT numerically matches added queue residence
TP4 c1->c4: ~97.5%

TP8 c1->c2: ~95.7%
TP8 c1->c4: ~97.2%
```

This is a valid DERIVED insight if clearly labeled.

---

## E2. Prefix-Reuse Scaling Across Context Horizons

**Card ID:** `prefix-scaling-card`  
**HTML ~447–459**  
**Canvas:** `chart_long_prefix` ~3855–3874

P0 correction.

Current values:
```text
0.902s / 16.866s / 48.349s
```

are mixed experiment `mean_ttft_ms`, not repeat-hit latency.

### Canonical prefix fields

| Context | First/cold | Repeat median | Hits | Queries | Hit/query |
|---|---:|---:|---:|---:|---:|
| 128K | 4.8965s | **0.3307s** | 917,504 | 1,050,624 | **87.33%** |
| 512K | 32.5762s | **1.1679s** | 1,048,576 | 2,098,177 | **49.98%** |
| 1M | 94.2272s | **2.6140s** | 1,998,848 | 4,000,000 | **49.97%** |

Use:
```text
prefix_first_ttft_ms
prefix_repeat_ttft_median_ms
prefix_hits_delta
prefix_queries_delta
```

### Remove current hit ratios
```text
99.4%
96.8%
94.2%
```
They are not canonical.

### Recommendation wording
Do not say:
```text
enable prefix caching unconditionally
```

Use:
```text
high-value for workloads with demonstrated repeated-prefix reuse;
production value depends on hit rate and cache residency.
```

### Click mapping bug
Current chart uses:
```text
tp4_prefix_128k
tp4_prefix_512k
tp4_prefix_1m
```

Actual cases:
```text
tp4_prefix128k
tp4_prefix512k
tp4_prefix1m
```

---

## E3. `chart_long_concurrency`

**Canvas:** `chart_long_concurrency`

✅ TTFT numerical curve is correct.

### Click mapping bug
Current query:
```text
tp4_1m_concurrency
```
Actual:
```text
tp4_1m_concurrency_extension
tp8_1m_concurrency_extension
```

Use exact IDs.

---

## E4. `chart_long_scheduler`

**Canvas:** `chart_long_scheduler`

✅ `max_num_seqs` values are correct.

Keep:
```text
232.34 / 232.36 / 232.25s
```

Interpret only:
```text
low sensitivity in TP4/PP1 1M c4 tested range 4/8/16
```

Do not generalize to all workloads.

---

## E5. `chart_long_chunk`

**Canvas:** `chart_long_chunk`

✅ numerical TTFT:
```text
122.05 / 93.28 / 88.95
```

### Fix label
Current:
```text
4K [Fairness/Jitter]
```

No matched fairness/jitter measurement supports this label.

Use:
```text
4K
8K
16K [Lowest measured c1 TTFT]
```

### Click mapping bug
Current cases:
```text
tp4_1m_chunk4096
tp4_1m_chunk8192
tp4_1m_chunk16384
```

Actual cases:
```text
tp4_chunk4k
tp4_chunk8k
tp4_chunk16k
```

and select the 1M bench within each case.

---

## E6. `chart_long_fp8`

**Canvas:** `chart_long_fp8`

Current:
```text
BF16 KV (Measured: 88.7 GB)
```

Problem:
88.7 is total GPU memory, not KV-cache memory.

Better:
- render as a **status card**, not a quantitative FP8 comparison;
- show `FP8-KV = NOT_RUN`;
- matched baseline total GPU peak memory can be shown separately only if the exact TP4/PP1 configuration is named.

Do not imply an FP8 memory delta was measured.

---

## E7. CPU Offload status

**Location**
- Long ~517
- Scheduler ~577
- hidden `chart_long_offload`

Correct that the experiment is NOT_RUN.

Remove unsupported:
```text
1M KV state ~11.8 GB/GPU
PCIe causes >10× decode penalty
```

Neither is demonstrated by a completed offload run in this campaign.

Coverage purpose says the offload experiment was **NOT_RUN**.

Also remove remaining `Ada`.

Remove the hidden chart's stale 88.7GB numeric dataset if the chart is not shown.

---

## E8. Long Context top KPI cards

Current:
```text
YES (88.7 GB)
c=1 STRICT CAP
```

Change to:
```text
All measured c1 topologies fit; exact memory is topology-specific.
c1 is cleanest measured single-node 1M point; production cap is SLO-driven.
```

---

## E9. Distributed 1M matrix

Current TP4/PP4:
```text
TTFT 28.56s · 35k tok/s
```

Change to:
```text
TTFT 28.57s
~35.0k input tok/s derived ingestion rate
~1.107 output tok/s
```

---

## E10. `1M Serving Decision` table

**Location**
- `long-serving-decision` ~521 onward

Still all `post-run`.

Populate from canonical c1/c2/c4 rows or remove before publication.

---

# F. SCHEDULER & KV TAB — EXACT FIXES

## F1. `chart_sched_kv`

✅ Canonical KV data now correct.

Do not infer total VRAM from this percentage.

---

## F2. `chart_sched_running_waiting`

✅ Values are valid as **peak** c1 state.

Keep “Peak” wording.

---

## F3. `chart_sched_queue_mean`

✅ Correct canonical 1M queue values.

### Click mapping
Queries use abbreviated cases such as:
```text
tp4_1m_concurrency
tp4_pp4
```
which do not resolve exactly.

Use exact case IDs/Evidence IDs.

---

## F4. `chart_sched_preemptions`

✅ Correct:
```text
0 preemptions across all 119 completed application rows
```

Do not call this proof that memory pressure never matters outside the tested scope.

---

## F5. `chart_sched_max_seqs`

✅ Correct and useful.

Keep conclusion tightly scoped.

---

## F6. Scale-Out Scheduler & KV Runtime Ledger

**Card ID:** `scheduler-scaleout-matrix`  
**HTML ~580–605**

### Numerical table
KV and total GPU memory values are now mostly correct.

### Fix these verdicts
Current:
```text
OPTIMAL PIPELINE PARTITIONING
PRODUCTION VIABLE @ 1M
CROSS-NODE BARRIER STALL
TCP ALLREDUCE BOTTLENECK
```

These mix:
- scheduler telemetry
- causal interpretation
- production verdict.

Use columns:
```text
Measured scheduler state
Cross-validated interpretation
SLO decision (only if SLO specified)
```

### Queue summary wrong
Current takeaway:
```text
queue wait remains below 0.00002s across all scale-out points
```

Native TP8/PP2 1M is about:
```text
0.000038s
```

Use:
```text
< 0.00004s across these Native c1 scale-out rows
```

### Remove unsupported memory attribution
Current:
```text
static model weights (~70 GB) dominate
```

No memory-allocation decomposition in the canonical data proves `~70 GB` as the per-GPU static weight component.

Use:
```text
total GPU memory remains ~86.7–88.8 GiB while KV utilization varies;
the exact allocator breakdown is not measured here.
```

---

## F7. `chart_sched_open_loop_8k`

✅ Current plotted TTFT/TPOT values match canonical data.

### Card/narrative adjustments

Current:
```text
Capacity Knee @ 3.81 RPS
```

Treat the knee as **DERIVED / SLO-dependent**, not direct fact.

At 0.90x:
```text
offered request_rate ~3.811 RPS
achieved request throughput ~3.302 req/s
```

Show offered vs achieved distinctly.

Current note:
```text
queue remains <0.25s
```

Canonical max is approximately:
```text
0.25375s at 1.00x
```

Use `~0.254s max in measured sweep`.

---

## F8. `chart_sched_open_loop_128k`

**Canvas:** `chart_sched_open_loop_128k`  
**JS ~4007–4028**

P0: rebuild the entire dataset.

### Correct offered rates

```text
0.25x  0.0570 RPS
0.50x  0.1141
0.75x  0.1711
0.90x  0.2053
1.00x  0.2281
1.10x  0.2509
1.25x  0.2851
```

### Correct TTFT and queue

| Load | TTFT s | Queue s | TPOT ms |
|---|---:|---:|---:|
| 0.25x | 5.105 | 0.422 | 12.712 |
| 0.50x | 7.511 | 2.520 | 36.743 |
| 0.75x | 6.936 | 1.941 | 50.569 |
| 0.90x | 10.009 | 4.738 | 131.550 |
| 1.00x | 21.107 | 15.695 | 178.510 |
| 1.10x | 21.471 | 16.115 | 166.731 |
| 1.25x | 21.551 | 16.131 | 184.857 |

Current labels/points such as:
```text
0.07 / 0.13 / 0.20 ...
24.5s / 29.8s
18.9s / 23.4s queue
```
are not canonical.

### Terminology
Current:
```text
1.00x RPS
```
should be:
```text
1.00× offered-load point (~0.228 RPS)
```

---

## F9. Scheduler Capacity Knee / Admission Decision

**Location**
- `scheduler-decision-output` ~624–637

Still placeholders.

Populate using:
- real 8K open-loop,
- real 128K open-loop,
- 1M closed-loop queue/TPOT,
- explicit SLO.

Do not combine them into one universal “max users” number.

---

# G. PROFILER TAB — EXACT FIXES

This remains the largest semantic-risk area.

---

## G1. Profiler identity card

**Location**
- beginning of Profiler tab ~654 onward

### Hardware name
Replace Ada → Blackwell.

### Completeness
Do not say:
```text
14 CAPTURED (100%)
```

Use:
```text
14 / 22 expected distributed profiles complete
11 Native + 3 capped-100G complete
```

---

## G2. `chart_prof_kernel_categories`

**Canvas:** `chart_prof_kernel_categories`  
**HTML card ~730s; JS ~4031–4063**

### Single-node TP4/TP8 data

Values such as:
```text
TP4 decode AllReduce 86.3%
TP8 decode AllReduce 89.1%
TP4 prefill AllReduce 46.0%
```
are legitimate as **aggregate GPU kernel-time shares for the exact captured profile**.

### Wrong semantic label
Current:
```text
percentage of GPU time
decode time
critical path
```

Use:
```text
aggregate GPU kernel-work composition
```

This is not exclusive request wall-clock.

### Distributed arrays need reproducible aggregation

Current:
```text
TP16/PP1 AllReduce 76.2%
TP4/PP4 AllReduce 40.0%
TP4/PP4 SendRecv/Other 8.3%
```

Raw per-rank TP16 128K AllReduce share is roughly:
```text
range ~76.3–79.4%
median ~77.65%
mean ~77.61%
```

Raw TP4/PP4 128K:
```text
AllReduce range ~22.8–41.7%
median ~32.65%
mean ~32.68%

SendRecv range ~8.0–21.9%
median ~9.6%
```

Therefore a topology-wide chart **cannot silently use one selected rank's percentage**.

Choose one:
```text
A) exact selected rank, with rank ID shown
B) median across ranks, with range/error bars
C) per-rank distribution
```

and state the aggregation rule.

---

## G3. `chart_prof_pytorch_operators`

**Canvas:** `chart_prof_pytorch_operators`  
**JS ~4065–4099**

### Strong raw result that can remain
Rank-0 PyTorch profiler:

```text
TP4 AllReduce Self CUDA:
251.529 ms
7040 calls

TP8:
583.866 ms
7040 calls

ratio ~2.32×
```

This is an excellent cross-tool measurement.

### Current problems

1. `TOTAL Interactive Turn = 623.1 / 875.8 ms`
   - this is not user request TPOT/turn latency;
   - it appears to be a sum of selected Self CUDA groups.
   - remove or call `sum of selected operator Self CUDA groups`.

2. Several grouped categories (`GEMV`, `MoE`, etc.) need an explicit grouping recipe if they are sums of multiple profiler rows.

3. `Smoking Gun`, `completely wipes out`, `completely obliterated` are too causal.
   Replace with:
   ```text
   wider-TP AllReduce cost is a cross-validated contributor and exceeds the
   observed grouped GEMV saving in this rank-local operator accounting.
   ```

4. Y-axis says:
   ```text
   Self CUDA Time (ms / interactive turn)
   ```
   Change to:
   ```text
   Rank-local aggregate Self CUDA time in captured profile (ms)
   ```

---

## G4. `chart_prof_cuda_api`

**Canvas:** `chart_prof_cuda_api`  
**JS ~4101–4128**

This chart is **numerically invalid beyond the first few entries**.

Raw `tp4_decode/cuda_api_sum.csv`:

```text
cudaEventSynchronize
time 3.638s
Time% 32.8
calls 512

cudaLaunchKernel
3.466s
31.2%
888,504 calls

cuLaunchKernelEx
1.530s
13.8%
389,896 calls

cudaMemcpyAsync
0.710s
6.4%
90,224 calls

cudaStreamWaitEvent
0.361s
3.2%
337,712 calls

cudaLaunchKernelExC...
0.359s
3.2%

cudaEventRecord
0.286s
2.6%
...
```

Current chart incorrectly shows:
```text
cudaStreamWaitEvent 1.82s / 16.4%
cudaEventRecord 0.68s / 6.1%
cudaSetDevice 0.42s / 3.8%
cudaEventCreate 0.21s / 1.9%
```

These do not map to the named raw rows.

### Also invalid visualization
Current chart puts:
- seconds
- percentages

on the same y-axis.

Split into:
```text
A. CUDA API total time
B. API time share %
C. call count / avg API duration
```

or use one metric per chart.

### Recommendation text
Remove:
```text
CUDA Graph capture removes host launch overhead completely
```

No CUDA Graph A/B experiment exists in this campaign.

Use:
```text
CUDA Graph capture is a candidate follow-up optimization to test.
```

---

## G5. `chart_prof_kernel_latency`

**Canvas:** `chart_prof_kernel_latency`  
**JS ~4130–4171**

### Rename
This is **not a roofline** in the conventional performance-model sense.

Use:
```text
Kernel Invocation Latency Distribution / Dispersion
```

### Provenance problem
It mixes kernels from different profiles/topologies without showing the source profile/rank.

For every kernel series, add:
```text
profile ID
topology
phase
rank or aggregation method
```

### “100% empirical” wording
Individual min/avg/max values can be empirical, but the mixed chart needs exact source provenance.

Do not imply one coherent profile generated all points.

---

## G6. Empirical Time Attribution & Critical Path Ledger

**Location**
- Profiler ~820 onward

P0 semantic blocker.

Current title:
```text
Empirical Time Attribution & Critical Path Ledger
```

Current table mixes:
- aggregate GPU kernel-work %
- CPU API time
- inferred runtime
- wall-clock-style durations

under one percentage ledger.

That is not valid.

`PROFILE_ANALYSIS.json` explicitly warns aggregate GPU work is not wall-clock critical path.

### Replace title
```text
Resource-Pressure / Aggregate Work Ledger
```

Or create two separate views:

```text
1. Resource pressure
   GPU kernel work
   CPU API work
   calls/bytes

2. Critical-path wall time
   only timeline-exclusive durations after overlap/rank reconciliation
```

### Remove
- residual=0 style claims
- “full attribution”
- percentages from incompatible denominators in one total.

---

## G7. Detailed Top 15 Traced GPU Kernels

**Location**
- Profiler ~900 onward

Current rows often combine:
```text
decode share / prefill share
```
while showing **one**:
- total time
- instance count
- avg
- median
- min/max

That is ambiguous because those numeric columns belong to one profile.

### Fix
Add a first-class:
```text
Profile / Phase / Topology
```
column and make each row represent **one exact raw profile row**.

If the same kernel appears in prefill and decode, use separate rows.

---

## G8. Distributed Profile Completeness table

**Location**
- Profiler ~1100–1140

P0.

Current card:
```text
Native Multi-Node Distributed Profile Completeness
14 / 14 VERIFIED
```

This is wrong.

### Correct campaign state

```text
22 expected
17 PROFILE_VALIDATION files present
14 complete

Native:
14 expected
11 complete
3 incomplete

configured-100G:
3 complete profile points in captured set

remaining expected capped points:
not captured / incomplete according to validation contract
```

### Native incomplete cases that must be visible

```text
TP8/PP2 decode c8:
Node0 missing

TP4/PP4 decode c8:
Node0 and Node1 missing

TP16/PP1 decode c8:
Node1 missing
```

The current table incorrectly marks these 100% complete.

### Required visual
Replace “14/14 verified” with the previously requested **22-cell profile matrix**:
- topology
- network mode
- workload
- Node0
- Node1
- COMPLETE / INCOMPLETE / NOT_CAPTURED

---

## G9. Invalid 61-layer statements

**Locations**
- Scale-Out finding ~379
- Profiler completeness description ~1127
- Profiler root-cause table ~1167

Delete all `61 layers / 61 layerwise AllReduce` statements.

Actual manifest:
```text
27 hidden layers
20 KDA
7 full attention
```

Physical NCCL call counts must come from profile traces, not layer count.

---

## G10. Profiler Root Cause → Production Deployment Rules

**Location**
- ~1150–1184

### Row 1 — TP4 decode vs TP8

Current:
```text
TP4 Decode beats TP8 (-7.2% TPOT)
```

Canonical matched 8K context baseline:
```text
TP4 4.475ms
TP8 6.350ms
TP4 ~29.5% lower
TP8 ~41.9% higher
```

Keep the PyTorch/NCCL cross-validation but correct the application delta.

---

### Row 2 — TP8 prefill

Current:
```text
TP8 Prefill beats TP4 (-22% TTFT)
```

Canonical:
```text
128K: TP8 is slower than TP4
512K: TP8 ~12.0% lower TTFT
1M: TP8 ~19.9% lower TTFT
```

Therefore scope the claim by context.

Also:
```text
FlashAttention is FLOP bound
```
is not proven by Nsight Systems duration alone.

Use:
```text
TP8 reduces the measured FlashAttention kernel duration in the captured profile;
whether the kernel is FLOP-bound requires NCU/roofline evidence.
```

---

### Row 3 — TP4/PP4 vs TP16

Current:
```text
61 cross-node TCP AllReduce collectives/token
76.2% GPU time stuck in network sync
Always prefer PP over TP16
```

All three need correction.

Use:
```text
Measured: TP4/PP4 has lower TTFT and much lower cap sensitivity in this tested campaign.
Profiler: TP16 ranks show high aggregate AllReduce kernel-work share.
Decision: prefer PP-oriented candidate for these measured workloads/fabric conditions,
subject to workload/SLO; do not universalize.
```

---

### Row 4 — max_num_seqs

Current:
```text
zero effect because hardware is 100% prefill-compute bound
```

Measured:
```text
TTFT is flat across max_num_seqs 4/8/16
peak_running never approaches those configured ceilings
```

Conclusion:
```text
max_num_seqs is non-binding in this tested state.
```

Exact bottleneck cause is not proven by the A/B itself.

---

### Row 5 — CUDA Graphs

Current:
```text
Enable CUDA Graphs
```

Treat as **future hypothesis / A/B experiment**, not campaign finding.

---

# H. EVIDENCE TAB — EXACT FIXES

## H1. Status Contract stale

**Location**
- ~1198

Current:
```text
Native-only campaign
capped modes removed
sensitivity unresolved/deferred
```

Wrong.

Replace with the actual primary/auxiliary evidence contract.

---

## H2. Scope filter bug

**Location**
- Evidence filter ~1212
- JS matching ~3283–3304

Actual Evidence data-scope values:
```text
SINGLE_V6_BASE
SINGLE_V8_1M_EXT
MULTI_V8
OPEN_LOOP_GENERATED
```

Current option:
```text
SCALEOUT_V8
```

does **not** match `MULTI_V8`.

Fix option values to exact canonical scope labels.

---

## H3. Reliability filter is invalid

**Location**
- `ev-filter-rel` ~1215
- Evidence row badges

Current:
```text
High-N (p95/p99 Valid)
```

This collapses two different reliability flags.

Canonical completed rows:
```text
93 rows: p95=false, p99=false
19 rows: p95=true, p99=false
7 rows:  p95=true, p99=true
```

Therefore **19 rows are currently green/high-N while p99 is not reliable**.

Affected Evidence IDs:

```text
EV-002
EV-006
EV-022
EV-023
EV-037
EV-038
EV-039
EV-043
EV-044
EV-061
EV-063
EV-112
EV-119
EV-120
EV-121
EV-122
EV-123
EV-124
EV-125
```

### Required implementation
Do not infer from a frontend N threshold.

Render exact canonical booleans:
```text
p95_reliable
p99_reliable
```

Use two badges:
```text
p95 VALID / NOT VALID
p99 VALID / NOT VALID
```

---

## H4. One-click chart→Evidence mapping is not exact

**Location**
- `jumpToEvidence` ~3219–3263
- chart query functions throughout JS

The function does a simple contiguous substring search.

Many chart queries cannot match the actual `data-search`.

### Examples that currently fail

```text
query: tp4_pp4 128k
actual case: tp4_pp4_dist

query: tp4_1m_concurrency 1m_c1
actual: tp4_1m_concurrency_extension

query: tp4_1m_chunk4096
actual: tp4_chunk4k

query: tp4_prefix_128k
actual: tp4_prefix128k
```

`tp4_openloop_8192` matches **seven rows**, so every point can jump to the wrong first row.

### Required design
Every chart datum should store:
```text
evidence_id
```
or exact:
```text
case + bench + network_provenance
```

Then jump by ID, not fuzzy substring.

This is required to make the UI statement:
```text
Click any chart point -> exact Evidence row
```
true.

---

## H5. Decision Claim Registry is stale

**Location**
- `decision-claim-registry` ~3145–3160

### Row: interactive candidate
Numerical TPOT observation okay.
Change NCCL `86.3%` wording to:
```text
86.3% aggregate GPU kernel-work share in the exact TP4 decode profile
```

### Row: long-prefill candidate
Current:
```text
27.80s
22%
```
Replace:
```text
TP8 28.089s vs TP4 31.916s @512K
~12.0% lower TTFT
```

### Row: native scale-out
Observation correct.
Change “PP avoids barrier” to interpretation.

### Row: 1M admission
Entire row is wrong:
```text
queue 1.45s
c1-c2 zero queue
max_concurrent=2-3
```

Replace with canonical c2/c4 queue/TPOT and SLO-driven admission wording.

### Row: runtime knobs
Flat max_num_seqs is valid.
`chunk_size=8192 balanced` is not proven by fairness/jitter data.
State only:
```text
16K lowest c1 TTFT among tested chunk budgets.
```

---

## H6. Runtime Dashboard Acceptance list

**Location**
- ~3142

Current:
```text
GCP_NATIVE only measured
```
Wrong.

Update.

---

## H7. Post-Run Decision Intelligence sources

**Location**
- ~3138

Current planned artifact:
```text
NETWORK_SENSITIVITY_GAP.md
explicitly records deferred cap sweep
```

Stale.

Use real network-coverage / measured sensitivity output, e.g.:
```text
SCALEOUT_NETWORK_COVERAGE.md
```
or a newly generated normalized sensitivity artifact.

Label generated deployment artifacts as **derived build outputs**, not authoritative raw sources.

---

# I. CROSS-CUTTING UI / DATA-CONTRACT FIXES

## I1. Hard-coded numerical arrays remain

Even though the Evidence tab says:
```text
Frontend hard-coded arrays are never source of truth
```
the JS still contains many manually typed arrays and `scaleoutMetricsData`.

This is exactly why the 128K open-loop / prefix / TP4PP2-KV regressions appeared.

### Required architecture

Generate one normalized dashboard object from:

```text
FINAL_VALIDATION.json
coverage.json
combined_vllm_runs.json
hardware_processed/summary.json
hardware_processed/iperf.csv
hardware_processed/nccl_points.csv
NCCL_POLICY_AUDIT.json
SCALEOUT_TELEMETRY_AUDIT.json
PROFILE_VALIDATION.json
profile-specific CSV only for profiler panels
```

Then render the charts from that object.

---

## I2. Config selectors that do not actually filter

Some chips visually look like filters but have no dataset update implementation.

Review:
- Scale-Up context/config chips
- Long Context topology chips
- Scheduler config chips
- Profiler scenario chips

Profiler chips currently mostly change active style/show a toast; they do not actually rebuild the charts/ledger.

Either:
- implement real filtering, or
- render them as labels, not interactive controls.

---

## I3. Do not use `s-failed` for “slow”

`FAILED` should mean execution failure.

For completed but poor-performance runs:
```text
execution_status = COMPLETED
sensitivity = HIGH
SLO_status = FAIL only when an SLO exists
```

---

## I4. Model-manifest guardrail

Any architectural formula/claim must use:

```text
Kimi-Linear-48B-A3B-Instruct
hidden_size = 2304
num_hidden_layers = 27
KDA layers = 20
full-attention layers = 7
num_experts = 256
experts/token = 8
dtype = BF16
revision = e1df551a...
```

Do not import K3's 93-layer/7168-wide model dimensions.

---

# 4. COMPLETE 27-CHART STATUS TABLE

| # | Tab | Canvas | Numerical status | Required action |
|---:|---|---|---|---|
| 1 | Executive | `chart_exec_ttft` | ✅ Good | fix distributed Evidence mapping; remove unrelated concurrency analysis |
| 2 | Executive | `chart_exec_tpot` | ✅ Good | fix mapping; scope mechanism |
| 3 | Executive | `chart_exec_capacity` | 🟡 data mostly good | remove 1240 claim; label lineages; fix TP4 click IDs |
| 4 | Scale-Up | `chart_scaleup_ttft` | ✅ Good | populate analysis |
| 5 | Scale-Up | `chart_scaleup_tpot` | ✅ Good | populate analysis |
| 6 | Scale-Up | `chart_scaleup_tps` | 🟡 mixed lineage | rebuild from one matched lineage; exact click IDs |
| 7 | Scale-Up | `chart_scaleup_concurrency` | 🟡 values real | title says TTFT/TPOT but graph is Output TPS; fix title/mapping |
| 8 | Scale-Up | `chart_scaleup_nccl` | ✅ exact message sizes | clarify BusBW / PCIe-NUMA provenance |
| 9 | Scale-Out | `chart_scaleout_comparison` | 🟡 core TTFT good | TP4/PP2 KV wrong when metric changes; dynamic verdict hard-coded |
| 10 | Scale-Out | `chart_scaleout_context_scaling` | 🟡 core TTFT good | same dynamic-data/verdict issues |
| 11 | Long | `chart_long_concurrency` | ✅ TTFT correct | exact Evidence mapping |
| 12 | Long | `chart_long_scheduler` | ✅ correct | keep scoped |
| 13 | Long | `chart_long_chunk` | ✅ TTFT correct | remove fairness label; fix case IDs |
| 14 | Long | `chart_long_fp8` | 🟡 status valid | total VRAM mislabeled as KV comparison; prefer status card |
| 15 | Long | `chart_long_prefix` | ❌ wrong semantic/data | replace with first/repeat fields + true hit/query ratio |
| 16 | Long | `chart_long_offload` | ❌ hidden stale data | remove quantitative dataset; NOT_RUN only |
| 17 | Scheduler | `chart_sched_kv` | ✅ correct | keep |
| 18 | Scheduler | `chart_sched_running_waiting` | ✅ correct peak state | keep “Peak” semantics |
| 19 | Scheduler | `chart_sched_queue_mean` | ✅ correct | fix click mapping |
| 20 | Scheduler | `chart_sched_preemptions` | ✅ correct | keep |
| 21 | Scheduler | `chart_sched_max_seqs` | ✅ correct | keep scoped |
| 22 | Scheduler | `chart_sched_open_loop_8k` | ✅ data correct | knee is DERIVED/SLO-dependent; offered vs achieved RPS |
| 23 | Scheduler | `chart_sched_open_loop_128k` | ❌ incorrect | replace x-axis, TTFT and queue with canonical rows |
| 24 | Profiler | `chart_prof_kernel_categories` | 🟡 single-node real, distributed aggregation unclear | rename aggregate work; rank/median provenance |
| 25 | Profiler | `chart_prof_pytorch_operators` | 🟡 key AR values real | remove fake “turn” total; document grouping; soften causality |
| 26 | Profiler | `chart_prof_cuda_api` | ❌ partially fabricated/misassigned | rebuild directly from `cuda_api_sum.csv`; split units |
| 27 | Profiler | `chart_prof_kernel_latency` | 🟡 individual values may be real | rename from roofline; exact profile/rank provenance |

---

# 5. STATIC STALE-VALUE / PHRASE SWEEP — MUST BE ZERO BEFORE SIGN-OFF

The following stale/problematic strings are still present in the 9pm HTML and should be eliminated or corrected.

## Incorrect/stale numeric phrases

```text
7.84ms vs 8.41ms
TP8 22% faster at 512K
27.80s @ 512K
1.45s queue
1,240 tok/s
29.8 GB VRAM
45.2 GB VRAM
0.902s / 16.866s / 48.349s called warm hit
99.4% / 96.8% / 94.2% prefix hit ratio
```

## Wrong hardware/model phrases

```text
RTX PRO 6000 Ada
NVLINK
61 layers
61 layerwise AllReduce
```

## Stale campaign-scope phrases

```text
native-only
bandwidth-cap sensitivity deferred
bandwidth sensitivity unresolved
GCP_NATIVE only measured
NETWORK_SENSITIVITY_GAP ... deferred cap sweep
```

## Overclaim phrases to remove/soften

```text
fully absorb rate limits
avoid collective stalls
100% prefill-compute bound
FLOP bound              [unless NCU/roofline proved]
memory bandwidth bound  [unless measured roofline proved]
completely wipes out
completely obliterated
CUDA Graph removes overhead completely
always prefer
production viable       [without explicit SLO]
strict cap              [without explicit SLO]
optimal                  [without objective]
```

## Placeholder phrase

`post-run`

There are still numerous `post-run` placeholders in:
- Executive Configuration Guidance
- Executive Deployment Recipe
- Scale-Up analysis strips
- Scale-Up Decision Output
- Long Context Serving Decision
- Scheduler Capacity Knee card

Populate or remove all of them before publication.

---

# 6. ITEMS THAT ARE NOW CLOSED AND SHOULD NOT BE REGRESSED

These improvements from the 9pm build are valid and should be preserved:

### Campaign status
- E2E matrix no longer presented as full-suite PASS
- NCCL policy shown incomplete
- 80/87 fixed serving
- 12 Native topology×context scale-out rows
- Blackwell SKU in main page title/topbar
- 95 Native +24 capped +7 NOT_RUN campaign banner

### Scale-Up
- matched context TTFT values corrected
- matched context TPOT values corrected
- 1M output TPS unit corrected
- c48/c64 removed from closed-loop chart
- exact NCCL message-size points used

### Scale-Out
- Native TTFT topology curves correct
- application configured-100G / configured-20G data exposed
- configured cap vs achieved iperf mostly exposed
- topology sensitivity heatmap concept is strong

### Long/Scheduler
- 1M TTFT c1/c2/c4 correct
- queue chart corrected
- max_num_seqs chart corrected
- CPU offload shown NOT_RUN rather than numeric zero
- scheduler KV chart rebuilt
- total GPU memory separated from KV% in the scheduler ledger
- preemptions = 0 retained
- 8K open-loop chart values retained

### Evidence
- 126 coverage rows
- 119 completed / 7 NOT_RUN
- primary vs auxiliary evidence class
- artifact-relative paths
- much richer runtime/network identity columns
- row-level TTFT/TPOT/KV/queue numerically reconciled to canonical data

---

# 7. P0 FIX ORDER FOR THE TEAM

Do these before any new Top-10 Executive characterization work is merged:

1. **Long / SLO Waterfall:** replace TPOT c2/c4 and KV values.
2. **Long / Prefix:** replace mixed means with first/repeat metrics and real hit/query ratios.
3. **Scheduler / 128K open-loop:** rebuild all x-axis/TTFT/queue points.
4. **Profiler / CUDA API:** rebuild directly from raw `cuda_api_sum.csv`.
5. **Profiler / semantic model:** remove critical-path claims from aggregate kernel work.
6. **Profiler / completeness:** replace 14/14 with 14/22 and show incomplete nodes.
7. **Model contamination:** remove every `61 layers` claim.
8. **Hardware contamination:** remove Ada/NVLink.
9. **Executive Decision Map:** fix 8K/128K memory + KV.
10. **Scale-Out:** fix NCCL SendRecv bandwidth and TP4/PP2 KV values.
11. **Evidence reliability:** split canonical p95/p99 flags.
12. **Decision Claim Registry:** replace stale queue/TPOT/prefill claims.
13. **Chart→Evidence:** use exact Evidence IDs rather than substring queries.
14. **Campaign scope:** remove all native-only/deferred-cap contradictions.
15. **Placeholders:** populate/remove all remaining `post-run` sections.

---

# 8. P1 FIX ORDER

1. Replace generic `RECOMMENDED/VIABLE` with metric/SLO-scoped language.
2. Remove “production viable / strict cap / optimal” unless SLO/objective is defined.
3. Clarify offered vs achieved RPS on open-loop charts.
4. Use exact memory units and source telemetry.
5. Separate execution success from SLO/sensitivity verdict.
6. Make profiler distributed percentages rank-aware or aggregated transparently.
7. Remove unsupported compute-bound / bandwidth-bound classifications.
8. Correct scale-up throughput lineage.
9. Implement real selector behavior or make selectors non-interactive.
10. Replace proposed post-run artifacts with actual generated analysis objects or mark them PROPOSED.

---

# 9. P2 / ARCHITECTURE HARDENING

The recurring root cause is still hand-maintained frontend data.

Recommended final architecture:

```text
raw results
   ↓
FINAL_VALIDATION + coverage + combined_vllm_runs
   ↓
hardware/profile normalized joins
   ↓
DASHBOARD_CANONICAL_DATA.json
   ↓
derived analysis functions
   ↓
EXECUTIVE_DISCOVERIES.json
   ↓
UI
```

Every chart datum should contain:

```text
evidence_id
case
bench
network_provenance
TP
PP
context/load
metric
unit
value
sample_count
p95_reliable
p99_reliable
evidence_class
artifact_path
```

This will remove the failure mode where the chart is updated but its:
- annotation,
- table,
- click-through,
- confidence badge,
- or recommendation

still uses an older number.

---

# 10. Final sign-off gate

Do **not** call the 9pm HTML data-signoff ready until all of the following are true:

- [ ] no wrong TPOT/KV values in 1M SLO waterfall
- [ ] 128K open-loop exactly matches canonical rows
- [ ] prefix card uses hit-conditioned repeat latency/counters
- [ ] no aggregate kernel share called critical-path wall time
- [ ] no 14/14 profiler completeness
- [ ] no Ada / NVLink / 61-layer contamination
- [ ] no stale 1.45s / 1240 tok/s / 7.84-8.41 / 27.80-22% claims
- [ ] no 21.84 GB/s generic NCCL SendRecv claim
- [ ] Executive memory values match `gpu_node_stats_json`
- [ ] TP4/PP2 Scale-Out KV matches canonical rows
- [ ] p95/p99 reliability rendered independently from canonical flags
- [ ] chart clicks resolve to the exact Evidence row
- [ ] no native-only/deferred-cap contradiction
- [ ] no universal recommendation without workload/SLO scope
- [ ] no unresolved `post-run` placeholder in a publication-facing decision card
- [ ] Evidence row numeric reconciliation remains intact
- [ ] all new Top-10 characterization cards are added **only after** these base-layer corrections

---

# Bottom line

The team has successfully repaired most of the original **core E2E charts**, which is significant.

The remaining risk is now concentrated in:

1. **new derived presentation layers** (waterfall, prefix, open-loop),
2. **profiler semantics and profiler completeness**,
3. **stale/static recommendation text**,
4. **evidence wiring and reliability labels**.

The raw campaign itself is strong enough to close these items. **No new benchmark campaign is required for the fixes in this document.** Most are frontend data-binding, provenance, terminology or evidence-class corrections.

Once these are closed, the dashboard is in a much stronger position to receive the separate Top-10 deep-characterization Executive layer.
