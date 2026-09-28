# V8-FULL Key Finds — Single-Page SIGNAL Implementation Specification V4

**Target:** `#keyfinds` only in `MASTER_CHARACTERIZATION_DASHBOARD_V4_26thSept_1amIST(2).html`  
**UI branch:** **single-page all-10 findings view**  
**Primary empirical source:** `results_V8_runs(4).zip`  
**Previous architecture review:** `V8_KEY_FINDS_CHIEF_LLM_PERFORMANCE_ARCHITECT_DEEP_REVIEW_V3.md`  
**Previous implementation reference:** `V8_EXECUTIVE_TOP10_DEEP_CHARACTERIZATION_IMPLEMENTATION_V2(2).md`  
**Visual reference:** the latest dark single-page “Key Deployment Findings” mockup supplied in this review session  
**Status:** implementation-ready specification for the team

---

# 0. Decision for this implementation branch

This specification is the **single-page SIGNAL version** of Key Finds.

The immediate implementation goal is:

> **One Key Finds tab, one scrollable page, all ten findings, clear context/topology coverage, real campaign data only, with engineering evidence preserved through exact drill-down.**

Do **not** implement ten separate pages as part of this change.

Do **not** implement a second full ENGINEER page or a third full FORENSICS page yet. Those will be decided after offline review.

The existing in-place evidence drawer / popup can and should remain the deep evidence path. The single-page view is therefore:

```text
KEY FINDS / SIGNAL PAGE
        ↓
10 concise evidence-backed findings
        ↓ click card / metric / evidence action
EXISTING IN-PLACE EVIDENCE POPUP
        ↓
exact telemetry / formula / profiler / provenance
```

If a top-right mode selector remains visually present during this branch:

```text
SIGNAL      active
ENGINEER    disabled / future
FORENSICS   disabled / future
```

Do **not** make disabled buttons appear interactive.

---

# 1. Architectural principle

The page must not standardize around TP4/PP1, and it must not show every topology in every finding.

Use this rule:

> **For each finding, show the minimum controlled configuration set that isolates the phenomenon, then add an independent matched configuration only when it materially increases confidence.**

This produces three finding types.

## Type A — topology findings

Multiple TP/PP configurations are part of the finding itself.

```text
#1  Fabric Exposure
#6  Parallelism Directional Elasticity
#9  Busy GPU != Efficient Serving
#10 KV Headroom != VRAM Headroom
```

## Type B — controlled perturbation findings

Keep topology fixed so the runtime/workload perturbation is interpretable.

```text
#4 Prefix Reuse
#5 Prompt-Token Admission
#8 Runtime Knobs
```

## Type C — mechanism + replication findings

Use one clean controlled comparison plus an independent replication/corroboration where available.

```text
#2 Concurrency
#7 TP Decode Communication
```

## Type D — matched profiler scaling finding

Keep profiler topology and profile methodology fixed.

```text
#3 Long-Context Resource-Pressure Shift
```

---

# 2. Non-negotiable evidence contract

Every number visible in the Key Finds single-page view must resolve to:

```text
MEASURED
CROSS-VALIDATED
DERIVED
MODELED
UNRESOLVED
```

Rules:

1. Never label a derived ratio as directly measured.
2. Never infer a missing context or topology.
3. Never render missing evidence as zero.
4. Never call a small delta “noise” without replicate variance / CI.
5. Never turn aggregate profiler GPU work into exclusive request wall-clock critical path.
6. Never mix PyTorch Profiler percentages with Nsight aggregate-work percentages under one denominator.
7. Never turn a workload-scoped observation into a universal topology recommendation.
8. Every visible topology label must be explicit `TPx/PPy`; never show only `TP4` or `TP8`.
9. Every visible finding must expose context coverage.
10. Every card must say what was **not measured** when that omission could change interpretation.

---

# 3. Source-of-truth hierarchy

Use this hierarchy for the new Key Finds renderer:

```text
1. RAW CAMPAIGN
   results/real_data/final_validation/FINAL_VALIDATION.json
   results/real_data/final_validation/coverage.json
   results/real_data/final_validation/combined_vllm_runs.csv
   results/real_data/final_validation/combined_vllm_runs.json
   exact run JSON / manifests
   hardware_processed/*
   exact profile artifacts

2. VERSIONED DERIVATION FUNCTIONS
   network deltas
   concurrency multipliers
   queue closure
   prompt-token normalization
   scaling exponents
   elasticity
   GPU-second proxy
   memory headroom arithmetic

3. GENERATED KEY-FINDS DATA OBJECT
   EXECUTIVE_DISCOVERIES_V4_SINGLE_PAGE.json

4. HTML / JS RENDERER

5. README / prose
   descriptive only; never overrides raw evidence
```

The HTML must not be the source of truth.

Do not maintain one set of values in visible markup and a second set in `window.EXECUTIVE_DISCOVERIES`.

---

# 4. Campaign identity strip — exact content

The page header must use campaign truth, not design-mockup placeholders.

## Model

```text
Kimi-Linear 48B surrogate
BF16
max model length = 1,048,576
```

Full evidence identity in drawer:

```text
model        = moonshotai/Kimi-Linear-48B-A3B-Instruct
revision     = e1df551a447157d4658b573f9a695d57658590e9
dtype        = bfloat16
hidden size  = 2304
layers       = 27
KDA layers   = 20
full attn    = 7
experts      = 256
experts/tok  = 8
```

Guardrail:

> **Surrogate characterization — do not numerically transfer absolute performance to Kimi K3.**

## Hardware

```text
16 × NVIDIA RTX PRO 6000 Blackwell Server Edition
2 nodes × 8 GPUs/node
reported device memory = 97,887 MiB ≈ 95.59 GiB per GPU
```

Do not use `H100`, `SXM`, `Ada`, or `NVLink` labels in this Key Finds implementation.

## Campaign health

```text
119 / 126 application rows completed
7 guarded NOT_RUN
0 failed application rows
14 / 22 expected distributed profiles complete
E2E RUN MATRIX VALIDATED
STRICT SUITE SIGN-OFF INCOMPLETE
```

The strict-signoff warning is mandatory.

---

# 5. Single-page information architecture

Use the latest single-page mockup structure.

```text
┌──────────────────────────────────────────────────────────────┐
│ KEY DEPLOYMENT FINDINGS                                     │
│ model · hardware · run health · profile health · sign-off   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 60-SECOND FINDING MAP                                       │
│ # | finding | scope | measured surprise | decision          │
└──────────────────────────────────────────────────────────────┘

ARCHITECTURE & FABRIC
┌──────────────┬──────────────┬──────────────┐
│ #1 Fabric    │ #6 Parallel  │ #7 TP Decode │
└──────────────┴──────────────┴──────────────┘

WORKLOAD & ADMISSION
┌──────────────┬──────────────┬──────────────┐
│ #2 Conc.     │ #5 Admission │ #8 Knobs     │
└──────────────┴──────────────┴──────────────┘

LONG CONTEXT & REUSE
┌───────────────────────┬────────────────────┐
│ #3 Pressure Shift     │ #4 Prefix Reuse    │
└───────────────────────┴────────────────────┘

OPERATIONAL TRAPS & CAPACITY SEMANTICS
┌───────────────────────┬────────────────────┐
│ #9 Busy GPU           │ #10 KV vs VRAM     │
└───────────────────────┴────────────────────┘
```

This order is intentional. It groups by engineering question, not by discovery ID.

Stable Top IDs remain visible for lineage.

---

# 6. Page-density contract

This is a **SIGNAL page**, not a report.

Each card must expose:

```text
1. finding title
2. one-line finding
3. context-coverage rail
4. topology-coverage rail
5. one hero contrast or compact table
6. one microvisual / visual grammar
7. one Decision Changed box
8. Evidence confidence
9. Causal confidence
10. evidence drill-down affordance
```

Default visible prose target:

```text
50–100 words per card excluding table labels
```

Do not render:

- long quote blocks
- repeated WHAT/WHERE/WHY prose
- full formula blocks
- raw paths
- full boundary paragraphs
- raw profiler tables

Those remain in the evidence popup.

---

# 7. Coverage-rail semantics

Every card gets a compact context and topology rail.

## Context states

```text
●  directly measured for this finding
P  profiler evidence
R  independent matched replication
—  not measured for this finding
```

Never use an empty state to imply zero.

## Example — #2 Concurrency

```text
CONTEXT
8K ● | 128K ● | 512K ● | 1M ●

TOPOLOGY
TP4/PP1 ● PRIMARY
TP8/PP1 R @1M
TP4/PP2 —
TP8/PP2 —
TP4/PP4 —
TP16/PP1 —
```

## Example — #10 KV vs VRAM

```text
TOPOLOGY
TP4/PP1 ●
TP4/PP2 ●
TP4/PP4 ●
TP8/PP1 R
TP8/PP2 R
TP16/PP1 ● Engineer/evidence layer
```

The rail communicates breadth of evidence without cluttering the chart.

---

# 8. 60-second Finding Map — required copy and scope

The first table is navigation + mental model.

| # | Finding | Scope shown in map | Measured surprise / pattern | Decision |
|---:|---|---|---|---|
| 1 | Fabric Exposure | `128K→1M · TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 · Native/100G/20G` | `1M/20G: TP16/PP1 +276.7% TTFT vs TP4/PP4 +3.9%` | topology determines exposed fabric risk |
| 2 | Concurrency | `TP4/PP1 · 8K→1M · c1→c4; TP8/PP1 @1M replication` | throughput dividend collapses with context; `1M +1.52% TPS / 26.15× TPOT` | admission from latency/queue SLO, not memory fit |
| 3 | Long-context pressure | `TP4/PP4 profiler · 128K→512K` | attention work `~15.7×`; NCCL `~2.18×`; KDA/MoE `~4×` | re-evaluate optimization target as context grows |
| 4 | Prefix reuse | `TP4/PP1 only · ~128K/~512K/1M` | `1M 94.23s → 2.614s repeat-hit median` | repeated-prefix traffic is a distinct workload class |
| 5 | Prompt-token admission | `TP4/PP1 · open-loop · 8K + 128K only` | `~18.2× req/s gap → ~1.14× input-token/s gap` | normalize prefill demand in tokens/s |
| 6 | Parallelism | `TP4/PP1↔TP8/PP1 8K→1M; TP4 PP frontier 128K→1M` | TP8 worse at 8K/128K, better at 512K/1M | choose parallelism dimension from measured workload elasticity |
| 7 | TP decode | `TP4/PP1↔TP8/PP1 · 8K profiler; 8K→1M E2E` | same 7040 AR calls; TP8 Self CUDA `~2.32×`; 8K TPOT `+41.9%` | validate wider TP for interactive decode |
| 8 | Runtime knobs | `TP4/PP1 · chunk 128K→1M; max_num_seqs 512K/1M` | chunk leverage grows; max_num_seqs stays nearly flat | tune knobs by measured derivative |
| 9 | Busy GPU | `TP4/PP4↔TP16/PP1 · 128K/512K/1M` | `1M: 80.6% util` topology is `2.39×` slower TTFT | utilization is not a topology selector |
| 10 | KV vs VRAM | `TP4 PP1→PP2→PP4 @1M + TP8 replication; TP4/PP1 baseline 8K→1M` | KV `12.29→5.91→2.75%` while memory stays `~88–89 GiB` | KV pressure and VRAM headroom are different metrics |

Rows should be clickable and scroll/focus the relevant finding card.

---

# 9. FINDING #1 — Fabric Exposure Fingerprint

## Finding type

```text
TYPE A — TOPOLOGY FINDING
```

## Primary question

> How much of a measured fabric constraint becomes user-visible TTFT under each topology?

## Signal scope

```text
Contexts:
8K  —
128K ●
512K ●
1M   ●

Topologies:
TP4/PP2  ●
TP8/PP2  ●
TP4/PP4  ●
TP16/PP1 ●

Network:
GCP_NATIVE
GCP_CAPPED_100G
GCP_CAPPED_20G
```

8K must be visibly marked not measured for the application cap sweep.

## Hero statement

> **The same measured fabric constraint produces radically different TTFT damage by topology.**

## Primary 20G-vs-Native heatmap

| Topology | 128K | 512K | 1M |
|---|---:|---:|---:|
| TP4/PP2 | +8.01% | +2.37% | +1.14% |
| TP8/PP2 | +0.81% | -0.19% | -0.10% |
| TP4/PP4 | +14.67% | +8.93% | +3.91% |
| TP16/PP1 | +383.66% | +333.01% | +276.69% |

Hero callout:

```text
1M configured-20G:
TP16/PP1  +276.69% TTFT
TP4/PP4     +3.91% TTFT
```

## Optional secondary inset

Show absolute TP16/PP1 20G latency tax:

```text
128K  +24.63 s
512K  +98.65 s
1M    +188.69 s
```

This is operationally easier to absorb than percentage alone.

## Transport provenance strip

```text
Configured state
      ↓
Measured iperf
Native    173.58 Gb/s
100G      56.84 Gb/s
20G       16.48 Gb/s
      ↓
Measured NCCL SendRecv primitive
      ↓
Application TTFT response
```

Do not label the achieved 100G/20G values as literal achieved cap values.

## Decision Changed

> **Size and choose scale-out topology from measured application exposure to transport degradation, not from NIC/iperf capability alone.**

## Confidence

```text
Evidence: HIGH
Cause:    MEDIUM-HIGH
```

## Boundary

- no 8K application cap sweep
- no 50G/10G application inference
- fitted communication coefficient is DERIVED and not a literal transfer count
- small signed TP8/PP2 changes must not be called “noise” without replicate variance

---

# 10. FINDING #2 — Concurrency Value Destruction

## Finding type

```text
TYPE C — PRIMARY CONTROLLED EXPERIMENT + REPLICATION
```

## Primary scope

```text
PRIMARY
TP4/PP1
closed-loop
c1 → c4
8K / 128K / 512K / 1M

REPLICATION
TP8/PP1
1M
c1 / c2 / c4
```

Do not add TP4/PP2, TP8/PP2, TP4/PP4, or TP16/PP1 to this Signal card because they do not have the matched concurrency sweep.

## Hero statement

> **The concurrency dividend collapses as context grows.**

## Context sweep

| Context | Output TPS gain c1→c4 | TTFT multiplier | TPOT multiplier | c4 queue |
|---|---:|---:|---:|---:|
| 8K | +120.82% | 2.74× | 1.63× | 0.027s |
| 128K | +10.27% | 2.28× | 12.96× | 5.11s |
| 512K | +2.19% | 2.74× | 57.36× | 53.66s |
| 1M | +1.52% | 2.48× | 26.15× | 134.43s |

The single-page visual should make the collapse obvious:

```text
TPS dividend:
+120.8% → +10.3% → +2.2% → +1.5%

Queue:
0.027s → 5.11s → 53.66s → 134.43s
```

## 1M independent replication badge

Queue-accounting closure:

```text
TP4/PP1 c2  96.4%
TP4/PP1 c4  97.5%

TP8/PP1 c2  95.7%
TP8/PP1 c4  97.2%
```

This replication should be visible as a small green badge, not another full chart.

## Primary visual

Use two aligned microvisuals:

1. `TPS gain vs context`
2. `c4 queue vs context`

Optional overlay:
- TTFT multiplier
- TPOT multiplier

Do not overload a single y-axis with incompatible units unless explicitly separated.

## Decision Changed

> **Drive admission from TTFT/TPOT/queue SLOs; “fits in KV” is not production capacity.**

## Confidence

```text
Evidence: HIGH
Cause: HIGH for added-TTFT queue closure
Cause: MEDIUM for exclusive TPOT root mechanism
```

## Boundary

Do not state a universal `c=1 production cap`. The admission threshold depends on product SLO.

---

# 11. FINDING #3 — Long-Context Resource-Pressure Shift

## Finding type

```text
TYPE D — MATCHED PROFILER SCALING
```

## Signal scope

```text
TP4/PP4
matched distributed prefill profile
128K P
512K P

8K —
1M — for profiler evidence in this specific finding
```

The 1M E2E point may appear only as contextual corroboration, not as a profiled endpoint.

## Hero statement

> **As context grows, full-attention aggregate GPU work accelerates much faster than KDA, MoE, or NCCL in the matched profile pair.**

## Validated growth summary

| Component | 128K→512K growth | Resource-pressure exponent |
|---|---:|---:|
| Full attention | ~15.7× | ~1.99 |
| GEMM family | ~5.25× | ~1.20 |
| KDA | ~3.9× | ~0.99 |
| MoE | ~3.8× | ~0.96 |
| NCCL | ~2.18× | ~0.56 |

## Visual

Use horizontal growth bars on the single page.

Do not attempt to show a “measured critical-path crossover”.

Footer:

> **Aggregate GPU work ≠ exclusive request wall-clock critical path.**

## Decision Changed

> **Re-profile the optimization target as context grows; one 128K profile is not enough for long-context deployment decisions.**

## Confidence

```text
Evidence: HIGH for valid endpoint profile data
Cause: MEDIUM for user-visible bottleneck interpretation
```

## P0 implementation correction

For this finding, derive the displayed growth from the exact matched TP4/PP4 128K and 512K profile artifacts using the versioned grouping function.

Do **not** use a TP16/PP1 profile record as a substitute for the TP4/PP4 matched pair.

---

# 12. FINDING #4 — Prefix Reuse Changes the Curve

## Finding type

```text
TYPE B — CONTROLLED PERTURBATION
```

## Signal scope

```text
Topology:
TP4/PP1 ONLY

Contexts:
8K     —
~128K  ●
~512K  ●
1M     ●

Other topologies:
NOT PREFIX-SWEPT
```

Keep the friendly context labels, but preserve exact requested input lengths in evidence:

```text
~128K case requested input = 131,328
~512K case requested input = 524,544
1M case requested input    = 1,000,000
```

## Exact hit-conditioned comparison

| Context | First/cold TTFT | Repeat-hit median | Speedup | Runtime prefix hit/query counter ratio |
|---|---:|---:|---:|---:|
| ~128K | 4.8965s | 0.3307s | 14.8× | 87.33% |
| ~512K | 32.5762s | 1.1679s | 27.9× | 49.98% |
| 1M | 94.2272s | 2.6140s | 36.0× | 49.97% |

Hero:

```text
1M:
94.2272s first/cold
→
2.6140s repeat-hit median
≈36.0×
```

## Visual

Primary:
- three context columns
- first/cold vs repeat-hit median

Optional:
- speedup line/bar

Do not label the mixed mean as warm-hit latency.

Do not call the workload `100% prefix hit`.

## Decision Changed

> **Route and capacity-plan repeated-prefix traffic as a distinct workload class; keep topology sensitivity explicitly unmeasured.**

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH
```

## Boundary

No prefix experiment exists here for:
- TP4/PP2
- TP8/PP2
- TP4/PP4
- TP16/PP1

Do not infer prefix benefit by topology.

---

# 13. FINDING #5 — Prompt-Token Admission Fingerprint

## Finding type

```text
TYPE B — CONTROLLED OPEN-LOOP PERTURBATION
```

## Signal scope

```text
TP4/PP1 ONLY
open-loop arrival

8K   ●
128K ●
512K —
1M   —
```

## Method

Use the median achieved request throughput across:

```text
1.00× offered load
1.10× offered load
1.25× offered load
```

Do not use a single arbitrary point as “maximum stable”.

## Canonical normalized values

```text
8K:
median achieved request rate = 3.358605 req/s
input-token rate             = 27.51K tok/s

128K:
median achieved request rate = 0.184567 req/s
input-token rate             = 24.19K tok/s
```

Comparison:

```text
requests/s gap      ≈ 18.20×
input-token/s gap   ≈ 1.14×
```

## Visual

Two aligned panels:

```text
BEFORE NORMALIZATION
Achieved req/s
8K vs 128K
~18.2× gap

AFTER NORMALIZATION
Achieved input tok/s
8K vs 128K
~1.14× gap
```

This finding is a **fingerprint**, not a universal law.

## Decision Changed

> **Normalize prefill-heavy demand into prompt tokens/s before comparing capacity across prompt lengths.**

## Confidence

```text
Evidence: MEDIUM-HIGH for two measured contexts
Cause: LOW-MEDIUM for any general invariant claim
```

## Boundary

No open-loop 512K/1M evidence in this campaign.

No matched open-loop data for the distributed TP/PP topologies.

---

# 14. FINDING #6 — Parallelism Directional Elasticity + Frontier

## Finding type

```text
TYPE A — TOPOLOGY FINDING
```

This card has two controlled views.

## Part A — hold PP=1, vary TP

```text
TP4/PP1 ↔ TP8/PP1
8K / 128K / 512K / 1M
```

| Context | TP4/PP1 TTFT | TP8/PP1 TTFT | TP8 effect |
|---|---:|---:|---:|
| 8K | 0.222s | 0.263s | +18.5% |
| 128K | 4.532s | 4.810s | +6.1% |
| 512K | 31.916s | 28.089s | -12.0% |
| 1M | 93.248s | 74.688s | -19.9% |

Signal message:

```text
8K / 128K: TP8 is slower
512K / 1M: TP8 becomes faster
```

Do not simplify this to “TP8 is better” or “TP4 is better”.

## Part B — hold TP=4, increase PP

Measured Native frontier:

### 128K

| Topology | TTFT | GPUs | GPU-s/request proxy |
|---|---:|---:|---:|
| TP4/PP1 | 4.532s | 4 | 18.1 |
| TP4/PP2 | 2.647s | 8 | 21.2 |
| TP4/PP4 | 1.710s | 16 | 27.4 |

### 512K

| Topology | TTFT | GPUs | GPU-s/request proxy |
|---|---:|---:|---:|
| TP4/PP1 | 31.916s | 4 | 127.7 |
| TP4/PP2 | 17.945s | 8 | 143.6 |
| TP4/PP4 | 10.222s | 16 | 163.5 |

### 1M

| Topology | TTFT | GPUs | GPU-s/request proxy |
|---|---:|---:|---:|
| TP4/PP1 | 93.248s | 4 | 373.0 |
| TP4/PP2 | 52.526s | 8 | 420.2 |
| TP4/PP4 | 28.568s | 16 | 457.1 |

On the single-page Signal card, show the 1M frontier line:

```text
TP4/PP1 → TP4/PP2 → TP4/PP4
```

with a small label:

```text
workload-specific measured TTFT / GPU-second frontier
```

The 128K/512K variants stay in evidence / tooltip / drawer.

## Decision Changed

> **Add GPUs along the parallelism dimension with positive measured latency elasticity for the target workload/SLO; expose the resource-occupancy trade-off instead of declaring a universal winner.**

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM
```

---

# 15. FINDING #7 — TP Decode Communication

## Finding type

```text
TYPE C — MECHANISM + CROSS-TOOL EVIDENCE
```

## Signal scope

```text
CONTROLLED TP-WIDTH COMPARISON
TP4/PP1 ↔ TP8/PP1

Profiler mechanism:
8K P

E2E TPOT:
8K ●
128K ●
512K ●
1M ●
```

Do not put TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 into the Signal mechanism chart.

They may be exposed in the evidence/Engineer drill-down as distributed decode-profile corroboration, with instrument/denominator identity visible.

## Evidence chain

### Layer A — NCCL small-message primitive

Representative processed points show TP8/TP4 latency ratio roughly:

```text
~1.9–2.2×
```

### Layer B — PyTorch Profiler @ 8K decode

```text
TP4/PP1:
AllReduce Self CUDA = 251.529 ms
calls = 7040

TP8/PP1:
AllReduce Self CUDA = 583.866 ms
calls = 7040

ratio ≈ 2.32×
```

### Layer C — E2E TPOT

| Context | TP8 vs TP4 TPOT penalty |
|---|---:|
| 8K | +41.9% |
| 128K | +39.0% |
| 512K | +25.0% |
| 1M | +17.9% |

The causal chain is strongest at 8K. The 128K–1M data is E2E persistence/corroboration, not proof that the 8K profiler fraction remains identical.

## Visual

Horizontal three-step chain:

```text
NCCL primitive
  ↓
PyTorch profiler @8K
  ↓
E2E TPOT 8K→1M
```

Keep Nsight and PyTorch denominators separate if both are shown in the drawer.

## Decision Changed

> **Validate small-collective synchronization cost before assuming wider TP improves interactive decode.**

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH that wider-TP synchronization contributes
```

## Boundary

Do not call aggregate GPU work an exclusive critical-path fraction.

---

# 16. FINDING #8 — Runtime-Knob Derivative

## Finding type

```text
TYPE B — CONTROLLED RUNTIME PERTURBATION
```

## Signal scope

```text
TP4/PP1 FIXED

Chunk experiment:
128K ●
512K ●
1M ●

max_num_seqs experiment:
512K ●
1M ●
```

Do not add distributed topologies. Doing so would introduce topology as an uncontrolled variable.

## Chunk-size leverage

4K → 16K TTFT reduction:

| Context | 4K TTFT | 16K TTFT | Reduction |
|---|---:|---:|---:|
| 128K | 5.228s | 4.364s | 16.5% |
| 512K | 40.271s | 30.455s | 24.4% |
| 1M | 122.049s | 88.951s | 27.1% |

Signal message:

> **The measured chunk-budget derivative becomes larger as context increases over 128K→1M.**

Do not call 16K universally optimal.

## max_num_seqs — measured non-binding state

### 512K c4

```text
4   → 87.973s
8   → 87.931s
16  → 87.932s
spread ≈ 0.047%
```

### 1M c4

```text
4   → 232.342s
8   → 232.364s
16  → 232.250s
spread ≈ 0.049%

peak_running = 2
peak_waiting = 3
```

The configured ceiling is not reached in the measured state.

## Visual

Two compact panels:

```text
HIGHER DERIVATIVE
chunk 4K→16K vs context

NON-BINDING HERE
max_num_seqs 4→8→16
```

## Decision Changed

> **Tune only knobs with a material matched A/B derivative in the measured state.**

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH for max_num_seqs non-binding interpretation
```

---

# 17. FINDING #9 — Busy GPU != Efficient Serving

## Finding type

```text
TYPE A — TOPOLOGY / OBSERVABILITY FINDING
```

## Signal scope

```text
TP4/PP4 ↔ TP16/PP1
GCP_NATIVE

128K ●
512K ●
1M ●
```

## Exact measured comparison

| Context | TP4/PP4 util | TP4/PP4 TTFT | TP16/PP1 util | TP16/PP1 TTFT |
|---|---:|---:|---:|---:|
| 128K | 35.2% | 1.710s | 63.2% | 6.420s |
| 512K | 55.3% | 10.222s | 67.8% | 29.624s |
| 1M | 62.8% | 28.568s | 80.6% | 68.197s |

Hero:

```text
1M:
TP4/PP4  ~62.8% util · 28.568s TTFT
TP16/PP1 ~80.6% util · 68.197s TTFT

TP16/PP1 is 2.39× slower despite higher GPU utilization.
```

## Visual

Two aligned mini-panels by context:

1. GPU utilization
2. TTFT

Do not fit a causal regression.

Do not claim an exact “spin-wait percentage” without direct trace decomposition.

Safe interpretation:

> GPU utilization reflects device activity, which can include communication kernels; it is not a direct measure of useful-token efficiency.

## Decision Changed

> **Pair utilization with TTFT, TPOT, throughput and communication/profile composition; never use utilization alone to choose topology.**

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM
```

---

# 18. FINDING #10 — KV Headroom != VRAM Headroom

## Finding type

```text
TYPE A — CONTROLLED TOPOLOGY / MEMORY-SEMANTICS FINDING
```

This card should be deliberately multi-configuration.

## Primary Signal experiment — hold TP=4, increase PP

At 1M:

| Topology | Peak KV | Peak GPU memory |
|---|---:|---:|
| TP4/PP1 | 12.29% | 88.39 GiB |
| TP4/PP2 | 5.91% | 88.69 GiB |
| TP4/PP4 | 2.75% | 88.83 GiB |

Signal message:

```text
KV pressure:
12.29% → 5.91% → 2.75%

Peak per-GPU memory:
88.39 → 88.69 → 88.83 GiB
```

## Independent TP8 replication

At 1M:

```text
TP8/PP1 KV = 12.18%
TP8/PP2 KV = 5.88%
```

This replication should appear as a small badge:

> `TP8 replication: PP1 12.18% → PP2 5.88% KV`

## Baseline context sweep — TP4/PP1

| Context | Peak KV | Peak GPU memory |
|---|---:|---:|
| 8K | 0.13% | 86.67 GiB |
| 128K | 1.63% | 88.39 GiB |
| 512K | 6.46% | 88.39 GiB |
| 1M | 12.29% | 88.39 GiB |

Keep this in tooltip/evidence or as a small context badge if space is tight. The primary single-page chart remains the controlled PP sweep.

## Raw device capacity

```text
97,887 MiB ≈ 95.59 GiB per GPU
```

Do not use `96.00 GiB` as the arithmetic source.

## Visual

Two semantically separate scales:

```text
Peak KV utilization (%)
Peak GPU memory (GiB)
```

A dual-axis chart is acceptable only if axes are explicitly labeled and visually separated.

Preferred: aligned mini-panels.

## Decision Changed

> **Use KV% for cache pressure and device-memory telemetry for OOM/headroom decisions; never substitute one for the other.**

## Confidence

```text
Evidence: HIGH
Cause: LOW-MEDIUM for exact allocator/sharding interpretation
```

## Boundary

Do not claim:
- exact `1/PP` allocator law
- exact weight/activation/runtime/NCCL split
- “98% of memory is weights”
- exact OOM margin without accounting for telemetry semantics/reservation behavior

---

# 19. Single-page visual behavior

## 19.1 Finding cards

Cards must be clickable.

Click behavior:

```text
card title / hero metric / table row / chart point
        ↓
open existing in-place Evidence popup
```

Do not redirect to another tab or page.

## 19.2 Tooltip minimum

Every plotted datum should show:

```text
metric
value
TP/PP
context
load/concurrency
network provenance
evidence class
sample count
p95 reliable?
p99 reliable?
```

## 19.3 Context + topology identity

No visible chart legend may show:

```text
TP4
TP8
```

Use:

```text
TP4/PP1
TP8/PP1
TP4/PP2
TP8/PP2
TP4/PP4
TP16/PP1
```

When a modifier matters, append it:

```text
TP4/PP1 · 1M · c4
TP4/PP1 · 1M · chunk=16K
TP4/PP1 · 1M · max_num_seqs=8
```

---

# 20. Evidence popup — retain, do not duplicate

The current HTML already has an in-place evidence drawer/popup architecture.

For this single-page implementation:

- reuse it
- repair its data bindings
- do not create separate Engineer/Forensics pages yet

Required popup sections:

```text
Finding
Measured Telemetry
Cross-Evidence / Profiler
Derivation
Raw Provenance
Boundary / Follow-up
```

Profiler records require:

```text
instrument
metric
unit
denominator semantics
node
rank
aggregation rule
artifact path
```

Do not merge PyTorch and Nsight attribution into one percentage.

---

# 21. Key data-object update

Generate:

```text
results/real_data/final_validation/
EXECUTIVE_DISCOVERIES_V4_SINGLE_PAGE.json
```

Recommended discovery schema:

```json
{
  "id": "concurrency_value_destruction",
  "stable_discovery_id": "TOP_3_CONCURRENCY_VALUE_DESTRUCTION",
  "version": "4.0.0-single-page",
  "domain": "WORKLOAD_ADMISSION",
  "finding_type": "MECHANISM_REPLICATION",
  "headline": "The concurrency dividend collapses as context grows.",
  "signal_scope": {
    "contexts": ["8K","128K","512K","1M"],
    "primary_topologies": ["TP4/PP1"],
    "replication_topologies": ["TP8/PP1@1M"]
  },
  "signal_metrics": [],
  "visual_spec": {},
  "decision_changed": "...",
  "evidence_confidence": "HIGH",
  "causal_confidence": "HIGH_QUEUE_MEDIUM_TPOT",
  "boundaries": [],
  "evidence_ids": [],
  "derivation_ids": []
}
```

Primitive evidence rows must not carry an invented causal-confidence default.

---

# 22. P0 corrections that remain mandatory in this implementation

The single-page redesign does not waive the V3 trust issues.

- [ ] Visible cards and evidence popup must bind to one canonical object.
- [ ] Raw artifact paths must be generated from actual manifests / index.
- [ ] PyTorch Profiler and Nsight denominators must be separated.
- [ ] Fix stale parallelism 8K values in popup.
- [ ] Use raw `97,887 MiB` device capacity for memory arithmetic.
- [ ] Remove full/100%-prefix-hit wording.
- [ ] Prompt-token normalization must use the high-load median method in this spec.
- [ ] Remove unsupported GPU spin-wait percentage claims.
- [ ] Show strict suite sign-off incomplete.
- [ ] Remove universal topology-winner language.
- [ ] Normalize evidence classes.
- [ ] Do not call single-point signed deltas “noise”.
- [ ] Do not use stale `results_V8_runs(3)` artifact-path labels when the current package is V8 run set 4.
- [ ] Do not show `H100`, `SXM`, `Ada`, `NVLink`, or other mockup-only platform labels.

---

# 23. Implementation sequence

## Phase 0 — data trust repair

1. Rebuild the Key Finds data object from `results_V8_runs(4).zip`.
2. Validate model/hardware identity.
3. Repair evidence IDs and artifact paths.
4. Recompute all derived metrics from versioned code.
5. Separate profiler instruments.
6. Run numeric equality tests against canonical CSV/JSON.

## Phase 1 — page shell

1. Replace current Key Finds header with the campaign identity/trust strip.
2. Add 60-second Finding Map.
3. Add four domain sections.
4. Use the exact card grouping in this spec.

## Phase 2 — ten Signal cards

Implement in this order:

```text
#1 Fabric
#6 Parallelism
#7 TP Decode

#2 Concurrency
#5 Prompt Admission
#8 Runtime Knobs

#3 Long Context
#4 Prefix Reuse

#9 Busy GPU
#10 KV vs VRAM
```

## Phase 3 — evidence interaction

1. Bind every metric to exact evidence IDs.
2. Make table rows and chart points clickable.
3. Reuse the in-place evidence popup.
4. Add exact context/topology/network scope to popup header.

## Phase 4 — QA

Run all acceptance tests below before release.

---

# 24. Single-page acceptance tests

## 24.1 Page-level

- [ ] All ten findings are visible on one Key Finds scroll page.
- [ ] No separate finding page is required.
- [ ] 60-second map contains all ten findings.
- [ ] Domain grouping matches this spec.
- [ ] Campaign health strip shows `119/126` and `14/22`.
- [ ] Strict sign-off is visibly incomplete.
- [ ] No H100/SXM/Ada/NVLink wording appears.

## 24.2 Scope correctness

- [ ] #1 shows 128K/512K/1M and four distributed topologies; 8K shown as unmeasured.
- [ ] #2 shows TP4/PP1 across 8K→1M plus TP8/PP1 1M replication.
- [ ] #3 shows TP4/PP4 128K→512K profiler scope only.
- [ ] #4 shows TP4/PP1 only, ~128K/~512K/1M.
- [ ] #5 shows TP4/PP1 open-loop 8K + 128K only.
- [ ] #6 shows TP4/PP1↔TP8/PP1 8K→1M plus TP4 PP frontier 128K→1M.
- [ ] #7 shows TP4/PP1↔TP8/PP1 as primary Signal evidence.
- [ ] #8 shows TP4/PP1 fixed; context expanded instead of topology.
- [ ] #9 shows TP4/PP4↔TP16/PP1 at 128K/512K/1M.
- [ ] #10 shows TP4 PP1→PP2→PP4 primary and TP8 replication.

## 24.3 Numeric correctness

- [ ] Fabric heatmap deltas recompute from canonical Native vs 20G rows.
- [ ] Concurrency c1→c4 ratios recompute from matched rows.
- [ ] Queue closure recomputes from queue delta / added TTFT.
- [ ] Prefix uses first/cold and repeat-hit median fields.
- [ ] Prompt-token values use 1.00×/1.10×/1.25× median request throughput.
- [ ] TP4/TP8 TTFT and TPOT use canonical context-baseline rows.
- [ ] Runtime chunk reduction uses matched 4K vs 16K rows.
- [ ] max_num_seqs spread uses matched c4 rows.
- [ ] GPU-utilization comparison uses the same context and GCP_NATIVE topology rows.
- [ ] KV/VRAM uses measured KV% and measured peak memory telemetry.

## 24.4 Semantic correctness

- [ ] Derived values are marked derived.
- [ ] No missing value appears as zero.
- [ ] No “noise” without variance.
- [ ] No universal topology winner.
- [ ] No unconditional prefix-cache recommendation.
- [ ] No universal prompt-token law.
- [ ] No aggregate profiler work labeled wall-clock critical path.
- [ ] No exact allocator decomposition.
- [ ] Evidence confidence and causal confidence are separate.

## 24.5 Evidence linkage

- [ ] Every hero metric resolves to an evidence/derivation ID.
- [ ] Every chart point resolves to a canonical row or exact profile artifact.
- [ ] Every artifact path exists in the supplied result tree.
- [ ] Profiler evidence states instrument, node, rank, aggregation and denominator.

---

# 25. CSS / layout guidance

Use the existing dark V4 visual language.

Recommended desktop layout:

```css
.keyfinds-map      { grid-column: 1 / -1; }
.keyfinds-grid-3   { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
.keyfinds-grid-2   { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
```

At narrower widths, stack cleanly.

Do not shrink tables below legibility to preserve three columns.

Prefer a vertical page over unreadably compressed cards.

---

# 26. What should NOT be copied literally from concept images

The generated visual references are layout aids, not data sources.

Do not copy any mockup field unless it resolves to campaign evidence.

Specifically prohibit:

```text
8×H100 (SXM)
generic “Long-context LLM Inference” hardware identity
Infiniband labels
synthetic chart points
invented confidence bars
invented profiler percentages
invented topology coverage
invented throughput/cost values
```

The actual Key Finds data must come from the canonical V8 campaign sources.

---

# 27. Definition of done

The single-page Key Finds implementation is complete when an experienced inference architect can answer, without leaving the tab:

```text
WHAT did we learn?
WHERE / under which context/topology did it occur?
HOW broad is the evidence?
WHAT measured contrast makes it important?
WHAT decision changes?
WHAT is derived?
WHAT is not proven?
CAN I open the exact evidence?
```

The page should be understandable in ~60 seconds at SIGNAL depth, while the full engineering record remains available through exact evidence drill-down.

---

# 28. Final implementation statement

> **Do not optimize the Key Finds page by deleting evidence. Optimize it by controlling evidence depth. On the single page, show the cleanest controlled comparison, the context/topology coverage, the strongest measured contrast, and the decision consequence. Preserve the rest through exact evidence-linked drill-down.**

This is the implementation standard for the V4 single-page Key Finds branch.
