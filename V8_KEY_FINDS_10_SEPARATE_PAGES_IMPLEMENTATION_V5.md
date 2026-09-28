# V8-FULL Key Finds — 10 Separate Finding Pages Implementation Specification V5

**Implementation branch:** Multi-page / ten sub-pages under the existing **Key Finds** tab  
**Primary UI basis:** the ten attached 1536×1024 Key Finds concept pages supplied in this review session  
**Data authority:** `results_V8_runs(4).zip`  
**Current dashboard:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_26thSept_1amIST(2).html`  
**Single-page sibling spec:** `V8_KEY_FINDS_SINGLE_PAGE_SIGNAL_IMPLEMENTATION_V4.md`  
**Prior deep architecture review:** `V8_KEY_FINDS_CHIEF_LLM_PERFORMANCE_ARCHITECT_DEEP_REVIEW_V3.md`  
**Status:** implementation-ready comparison branch

---

# 0. Purpose

This document defines the **second UI branch** for Key Finds:

> **One Key Finds top-level tab containing ten separate finding pages, selected from a persistent left navigation rail.**

This branch must use the **same empirical contract, topology/context discipline, no-hallucination rules, and data corrections** as the single-page V4 specification.

The ten attached images are **layout references only**. They are **not data sources**.

No value, hardware label, network label, confidence score, topology, context, or claim may be copied from an image unless it resolves to the canonical V8 data or an explicitly validated profiler artifact.

---

# 1. Navigation contract

The global dashboard tabs remain unchanged.

When `Key Finds` is selected, render:

```text
LEFT SUB-NAV                         MAIN FINDING PAGE
──────────────────────               ─────────────────────────────
1  Fabric Exposure                   selected finding only
2  Concurrency
3  Long-context Pressure Shift
4  Prefix Reuse
5  Prompt-token Admission
6  Parallelism Frontier
7  TP Decode Communication
8  Runtime Knobs
9  Busy GPU ≠ Efficient Serving
10 KV Cache vs VRAM
```

Stable route/fragment IDs:

```text
#keyfinds/fabric-exposure
#keyfinds/concurrency
#keyfinds/long-context-pressure
#keyfinds/prefix-reuse
#keyfinds/prompt-token-admission
#keyfinds/parallelism-frontier
#keyfinds/tp-decode
#keyfinds/runtime-knobs
#keyfinds/busy-gpu
#keyfinds/kv-vram
```

Only one finding page is rendered as active at a time.

The left rail is persistent and must not reset scroll/state unnecessarily when moving between findings.

---

# 2. Shared page anatomy

Every one of the ten pages uses the same visual grammar.

```text
PAGE HEADER
# + finding title + category chip
one-line finding
optional Signal / Engineer / Forensics controls

ROW A
┌────────────────────┬───────────────────┬────────────────────┐
│ KEY FINDING        │ WHY IT MATTERS    │ CONFIDENCE         │
└────────────────────┴───────────────────┴────────────────────┘

ROW B
┌───────────────────────────────┬──────────────────────────────┐
│ SCOPE — WHAT'S MEASURED       │ QUICK COMPARISON             │
└───────────────────────────────┴──────────────────────────────┘

ROW C
┌───────────────────────────────┬──────────────────────────────┐
│ PRIMARY VISUAL                │ SECONDARY VISUAL / EVIDENCE  │
└───────────────────────────────┴──────────────────────────────┘

ROW D
┌───────────────────────────────┬──────────────────────────────┐
│ KEY TAKEAWAYS                 │ DECISION CHANGED             │
└───────────────────────────────┴──────────────────────────────┘
```

For Finding #7, Row C may become one full-width three-stage evidence chain.

---

# 3. Signal / Engineer / Forensics control

The attached concept images show three mode buttons.

For this implementation branch:

```text
SIGNAL
default page described in this spec

ENGINEER
do not invent a separate dataset or page
if an existing detailed implementation is already wired, it may be retained
otherwise hide or disable until specified

FORENSICS
do not invent a new page
use the existing in-place evidence popup / provenance workflow where possible
```

Do not ship a clickable control whose behavior has not been implemented.

---

# 4. Campaign identity — mandatory correction to all ten mockups

The attached concept pages display mockup-only platform text such as `8xH100 (SXM)`.

That must **not** enter implementation.

Use:

```text
Results: V8
Platform: 16× NVIDIA RTX PRO 6000 Blackwell Server Edition
Topology envelope: 2 nodes × 8 GPUs/node
Model: Kimi-Linear 48B surrogate
Precision: BF16
Max model length: 1,048,576
```

Raw reported memory:

```text
97,887 MiB ≈ 95.59 GiB / GPU
```

Do not use:

```text
H100
SXM
RTX 6000 Ada
NVLink
InfiniBand
```

unless a separate exact artifact proves that label for a specific result. It is not the campaign identity used here.

---

# 5. Campaign health strip

If campaign health is shown globally or inside Key Finds, use:

```text
Application rows        119 / 126 completed
Guarded NOT_RUN         7
Failed rows             0
Distributed profiles    14 / 22
E2E matrix              VALIDATED
Strict suite sign-off   INCOMPLETE
```

Never show an unqualified `FULLY VALIDATED` state while strict suite status remains incomplete.

---

# 6. Evidence confidence UI — correction to concept images

The concept images use segmented blue bars beside labels such as High / Medium.

Those segmented bars visually imply a numeric score that the campaign does not define.

**Do not implement numeric-looking confidence bars.**

Use categorical badges only:

```text
Evidence: HIGH
Cause: MEDIUM-HIGH
```

When confidence has mixed semantics, state it explicitly.

Example for concurrency:

```text
Evidence: HIGH
Cause — added TTFT queue closure: HIGH
Cause — exclusive TPOT mechanism: MEDIUM
```

---

# 7. Global no-hallucination / no-assumption rules

These rules apply to all ten pages.

1. **Every visible metric must resolve to an exact evidence row or versioned derivation.**
2. **Every topology must use explicit TP/PP identity.**
3. **Every finding must expose measured context coverage.**
4. **Unmeasured context/topology is shown as `— NOT MEASURED`, never blank and never zero.**
5. **Do not add arbitrary topologies to make a page look richer.**
6. **Do not call a single signed delta `noise` without replicate variability.**
7. **Do not call aggregate GPU work exclusive wall-clock critical path.**
8. **Do not merge PyTorch Profiler and Nsight percentages under a common denominator.**
9. **Do not use a generated visual as numerical truth.**
10. **Do not create universal topology winners.**
11. **Do not create a production concurrency cap without a stated SLO.**
12. **Do not extrapolate 50G/10G application behavior from hardware-only points.**
13. **Do not claim 100% prefix hits.**
14. **Do not claim exact allocator memory decomposition without allocator traces.**
15. **Do not turn two measured prompt lengths into a universal capacity law.**

---

# 8. Finding classification

Use the minimum controlled configuration set needed to establish each claim.

| Finding | Experimental type | Signal topology policy |
|---|---|---|
| #1 Fabric | Topology finding | multi-topology required |
| #2 Concurrency | Mechanism + replication | TP4/PP1 primary + TP8/PP1 @1M replication |
| #3 Long-context | matched profiler scaling | TP4/PP4 matched 128K→512K |
| #4 Prefix | controlled perturbation | TP4/PP1 only |
| #5 Prompt admission | controlled perturbation | TP4/PP1 only |
| #6 Parallelism | topology finding | TP comparison + PP frontier |
| #7 TP decode | mechanism + cross-tool | TP4/PP1 vs TP8/PP1 primary |
| #8 Runtime knobs | controlled perturbation | TP4/PP1 fixed |
| #9 Busy GPU | topology finding | TP4/PP4 vs TP16/PP1 |
| #10 KV vs VRAM | topology/memory semantics | TP4 PP sweep + TP8 replication |

---

# 9. PAGE 1 — Fabric Exposure

## Route

```text
#keyfinds/fabric-exposure
```

## Header

```text
1  Fabric Exposure
Category: Topology Dependent
```

Use this one-line finding:

> **The same measured fabric constraint produces radically different user-visible TTFT damage depending on topology.**

Do not use “multi-node is more exposed than single-node” as the primary sentence because all four application points on this page are distributed topologies; the important measured contrast is topology-specific fabric exposure.

## Row A — Key Finding

Hero:

```text
1M · configured-20G vs GCP_NATIVE

TP16/PP1   +276.69% TTFT
TP4/PP4      +3.91% TTFT
```

**P0 correction to attached image:**  
`+276.7%` and `+3.9%` are **20G vs Native** deltas, not `20G vs 100G`.

Do not label these hero values “20G vs 100G”.

For reference, actual 20G-vs-100G TP16/PP1 delta is a different derived number.

## Row A — Why It Matters

Use:

> Fabric capability alone does not determine serving impact. The topology determines how much transport degradation is exposed to application TTFT. Scale-out design therefore needs both measured fabric capability and measured application sensitivity.

## Row A — Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH
```

No numeric bar.

## Row B — Scope

```text
Contexts:
8K     — NOT MEASURED in application cap sweep
128K   ●
512K   ●
1M     ●

Topologies:
TP4/PP2  ●
TP8/PP2  ●
TP4/PP4  ●
TP16/PP1 ●

Network provenance:
GCP_NATIVE
GCP_CAPPED_100G
GCP_CAPPED_20G
```

**P0 correction to attached image:** replace `Native (InfiniBand)` with `GCP Native Fabric`.

Measured forward iperf:

```text
Native   173.58 Gb/s
100G     56.84 Gb/s
20G      16.48 Gb/s
```

Configured label and achieved throughput are separate fields.

## Row B — Quick Comparison @ 1M

| Topology | Native TTFT | 100G TTFT | 100G vs Native | 20G TTFT | 20G vs Native |
|---|---:|---:|---:|---:|---:|
| TP4/PP2 | 52.526s | 52.597s | +0.13% | 53.127s | +1.14% |
| TP8/PP2 | 41.515s | 41.462s | -0.13% | 41.472s | -0.10% |
| TP4/PP4 | 28.568s | 28.866s | +1.04% | 29.684s | +3.91% |
| TP16/PP1 | 68.197s | 92.992s | +36.36% | 256.889s | +276.69% |

Do not copy the generated-image quick-comparison numbers.

## Row C — Primary visual

Title:

```text
TTFT vs Context by Topology
```

Controls:

```text
Fabric: Native | configured-100G | configured-20G
```

X:
```text
128K · 512K · 1M
```

Series:
```text
TP4/PP2
TP8/PP2
TP4/PP4
TP16/PP1
```

Use log Y for TTFT if needed for readability.

## Row C — Secondary visual

Title:

```text
Fabric Impact vs Native
```

Default context:
```text
1M
```

Bar values:
```text
TP4/PP2   +1.14%
TP8/PP2   -0.10%
TP4/PP4   +3.91%
TP16/PP1  +276.69%
```

Context selector may switch 128K / 512K / 1M.

## Key Takeaways

- Fabric sensitivity varies dramatically by topology.
- TP16/PP1 is strongly exposed to the measured transport degradation.
- TP4/PP4 is far less sensitive in the same measured 1M cap condition.
- Do not provision from NIC/iperf capability alone.

## Decision Changed

> **Size and choose scale-out topology from measured application exposure to transport degradation, not NIC capability alone.**

## Boundary

- no 8K application cap sweep
- no 50G/10G application inference
- no universal topology winner
- small TP8/PP2 signed deltas are not called noise

---

# 10. PAGE 2 — Concurrency

## Route

```text
#keyfinds/concurrency
```

## Header

```text
2  Concurrency
Category: Admission / SLO Risk
```

Use:

> **The concurrency dividend collapses as context grows: additional concurrency buys progressively less output throughput while latency and queue residence rise sharply.**

This is stronger and more accurate than making the page sound 1M-only.

## Row A — Hero

Default stress example:

```text
1M · TP4/PP1 · c1 → c4

Output TPS    +1.52%
TTFT           2.48×
TPOT           26.15×
Queue c4       134.43s
```

## Why It Matters

> Capacity must be defined from TTFT, TPOT and queue SLOs, not only whether requests fit in KV memory. At long context, the same increase in concurrency can consume enormous latency for almost no useful throughput dividend.

## Confidence

```text
Evidence: HIGH
Cause — added TTFT queue closure: HIGH
Cause — exclusive TPOT root mechanism: MEDIUM
```

## Scope

Primary controlled sweep:

```text
TP4/PP1
c1 → c4
8K ●
128K ●
512K ●
1M ●
```

Independent replication:

```text
TP8/PP1
1M · c1 / c2 / c4
```

Do not add PP2/PP4/TP16 here.

## Quick Comparison

| Context | Output TPS gain c1→c4 | TTFT multiplier | TPOT multiplier | c4 queue |
|---|---:|---:|---:|---:|
| 8K | +120.82% | 2.74× | 1.63× | 0.027s |
| 128K | +10.27% | 2.28× | 12.96× | 5.11s |
| 512K | +2.19% | 2.74× | 57.36× | 53.66s |
| 1M | +1.52% | 2.48× | 26.15× | 134.43s |

## Primary visual

Title:

```text
Concurrency Dividend vs Context
```

Use:
- TPS gain on right axis
- TTFT multiplier
- TPOT multiplier

If the chart becomes visually ambiguous, split TPS into an inset rather than force all three onto one scale.

## Secondary visual

Title:

```text
Queue Increase at c4 vs Context
```

Use log Y because:

```text
8K    0.027s
128K  5.11s
512K  53.66s
1M    134.43s
```

## Replication box

Queue closure @1M:

```text
TP4/PP1 c4 ≈ 97.5%
TP8/PP1 c4 ≈ 97.2%
```

## Key Takeaways

- 8K still obtains a large useful throughput dividend from c1→c4.
- The dividend collapses rapidly as context increases.
- At 512K/1M, queue and TPOT costs dominate the small throughput gain.
- The 1M queue-accounting result reproduces on TP8/PP1.

## Decision Changed

> **Drive admission from TTFT/TPOT/queue SLOs; “fits in KV” is not production capacity.**

## Boundary

Do not write:
```text
c=1 is the production cap
```
without an explicit product SLO.

---

# 11. PAGE 3 — Long-Context Resource-Pressure Shift

## Route

```text
#keyfinds/long-context-pressure
```

## Header

```text
3  Long-context Resource-Pressure Shift
Category: Profiler / Resource Regime
```

## Hero

> **In the matched TP4/PP4 128K→512K profile pair, full-attention aggregate GPU work grows much faster than KDA, MoE, or NCCL.**

Hero values:

```text
Full attention  ~15.7×
GEMM family      ~5.25×
KDA              ~3.95×
MoE              ~3.80×
NCCL             ~2.18×
```

## Why It Matters

> The optimization target changes with context length. A single 128K profile cannot represent the resource-pressure mix at 512K.

## Confidence

```text
Evidence: HIGH for the matched profile endpoints
Cause: MEDIUM for user-visible bottleneck interpretation
```

**Do not show “Cross-topology Consistency: Medium” on this Signal page.**  
This primary finding is a matched TP4/PP4 profile comparison, not a cross-topology consistency test.

## Scope

```text
TP4/PP4
matched prefill profiles

8K     — no matched profiler endpoint in this finding
128K   P
512K   P
1M     — no matched profiler endpoint in this finding
```

## Quick Comparison

| Component | Growth 128K→512K | Resource-pressure exponent |
|---|---:|---:|
| Full attention | ~15.7× | ~1.99 |
| GEMM family | ~5.25× | ~1.20 |
| KDA | ~3.95× | ~0.99 |
| MoE | ~3.80× | ~0.96 |
| NCCL | ~2.18× | ~0.56 |

## Primary visual

```text
GPU Work Growth — 128K → 512K
```

Horizontal or vertical bars.

## Secondary visual

```text
Component Growth Trend / Slope View
```

Normalize each component to 1 at 128K and show endpoint at 512K.

Footer:

> **Aggregate GPU work is not the same as exclusive wall-clock critical path.**

## Key Takeaways

- Re-profile at multiple long-context lengths.
- Full-attention work accelerates faster than KDA, MoE and NCCL in this matched pair.
- NCCL still grows, but more slowly than compute components over this range.

## Decision Changed

> **Re-evaluate the optimization target as context grows; one 128K profile is not enough.**

## Boundary

Do not:
- call this an exclusive wall-clock bottleneck crossover
- extend profiler growth to 1M without a matched 1M profile
- substitute a different topology profile into the TP4/PP4 matched pair

---

# 12. PAGE 4 — Prefix Reuse

## Route

```text
#keyfinds/prefix-reuse
```

## Header

```text
4  Prefix Reuse
Category: Optimization & Reuse
```

## Hero

```text
1M · TP4/PP1

first/cold TTFT       94.2272s
repeat-hit median     2.6140s
speedup               36.0×
```

Supporting:
```text
~128K  14.8×
~512K  27.9×
```

## Why It Matters

> Repeated-prefix traffic can occupy a radically different latency regime from cold long prompts and should be treated as a distinct workload class for routing and capacity planning.

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH
```

## Scope

```text
TP4/PP1 ONLY

8K      — not measured
~128K   ●
~512K   ●
1M      ●
```

Exact requested input lengths remain in evidence:

```text
~128K label = 131,328 requested input tokens
~512K label = 524,544 requested input tokens
1M label    = 1,000,000 requested input tokens
```

Explicit banner:

> **Only TP4/PP1 was prefix-swept. Do not infer topology sensitivity.**

## Quick Comparison

| Context | First/cold TTFT | Repeat-hit median | Speedup | Runtime hit/query counter ratio |
|---|---:|---:|---:|---:|
| ~128K | 4.8965s | 0.3307s | 14.8× | 87.33% |
| ~512K | 32.5762s | 1.1679s | 27.9× | 49.98% |
| 1M | 94.2272s | 2.6140s | 36.0× | 49.97% |

## Primary visual

First/cold vs repeat-hit median on log Y.

## Secondary visual

Speedup by context.

## Key Takeaways

- Repeated-prefix reuse substantially changes TTFT in the measured TP4/PP1 cases.
- The measured speedup increases over the three tested context horizons.
- Runtime hit/query counters are not 100%; do not label this a full-hit experiment.
- No topology comparison exists for prefix reuse.

## Decision Changed

> **Route and capacity-plan repeated-prefix traffic as a distinct workload class; keep topology boundary explicit.**

---

# 13. PAGE 5 — Prompt-Token Admission

## Route

```text
#keyfinds/prompt-token-admission
```

## Header

```text
5  Prompt-token Admission
Category: Open-loop Admission
```

## Hero

Before normalization:

```text
8K      3.35861 req/s
128K    0.18457 req/s
gap     ~18.20×
```

After normalization:

```text
8K      ~27.51K input tok/s
128K    ~24.19K input tok/s
gap     ~1.14×
```

## Method

Values are the **median achieved request throughput** over:

```text
rps_1.00x
rps_1.10x
rps_1.25x
```

Do not describe a single point as “maximum stable capacity”.

## Why It Matters

> Requests/s alone misstates prefill-heavy demand when prompt lengths differ. Input-token normalization exposes the actual accepted prefill work more fairly.

## Confidence

```text
Evidence: MEDIUM-HIGH for the two measured contexts
Cause/general invariant: LOW-MEDIUM
```

## Scope

```text
TP4/PP1
open-loop only

8K     ●
128K   ●
512K   — not measured
1M     — not measured
```

No other topologies were open-loop swept.

## Quick Comparison

| Metric | 8K | 128K | Interpretation |
|---|---:|---:|---|
| Median achieved request rate | 3.35861 req/s | 0.18457 req/s | ~18.20× gap |
| Normalized input-token rate | 27.51K tok/s | 24.19K tok/s | ~1.14× gap |

## Visuals

Left:
```text
Before Normalization — Achieved Request Rate
```

Right:
```text
After Normalization — Achieved Input-Token Rate
```

## Key Takeaways

- Request-rate comparison is misleading when prompt lengths differ materially.
- Prompt-token normalization compresses the apparent 8K-vs-128K capacity gap.
- This is a two-context fingerprint, not a universal law.

## Decision Changed

> **Normalize prefill-heavy demand into prompt tokens/s before comparing capacity across prompt lengths.**

---

# 14. PAGE 6 — Parallelism Frontier

## Route

```text
#keyfinds/parallelism-frontier
```

## Header

```text
6  Parallelism Frontier
Category: Architecture Trade-off
```

## Hero

> **The useful direction for adding GPUs changes with context. Short contexts penalize wider TP; deep contexts can benefit from it.**

Measured fixed-PP comparison:

| Context | TP4/PP1 TTFT | TP8/PP1 TTFT | TP8 effect |
|---|---:|---:|---:|
| 8K | 0.222s | 0.263s | +18.5% |
| 128K | 4.532s | 4.810s | +6.1% |
| 512K | 31.916s | 28.089s | -12.0% |
| 1M | 93.248s | 74.688s | -19.9% |

**P0 correction to attached image:** use the canonical 128K TP4 value shown above; do not copy `4.522s`.

## Why It Matters

> Parallelism choice should follow measured workload elasticity and the target SLO. More GPUs are not universally better; the useful parallelism dimension changes with context.

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM
```

## Scope

TP-width comparison:

```text
TP4/PP1 ↔ TP8/PP1
8K / 128K / 512K / 1M
```

PP frontier:

```text
TP4/PP1
TP4/PP2
TP4/PP4

128K / 512K / 1M
```

## Primary visual

```text
TTFT vs Context — TP4/PP1 vs TP8/PP1
```

Use log Y.

## Secondary visual

Default:

```text
1M TTFT vs GPU-seconds/request proxy
```

Actual 1M fixed-TP=4 points:

| Topology | TTFT | GPUs | GPU-s/request proxy |
|---|---:|---:|---:|
| TP4/PP1 | 93.248s | 4 | 373.0 |
| TP4/PP2 | 52.526s | 8 | 420.2 |
| TP4/PP4 | 28.568s | 16 | 457.1 |

Connect the non-dominated measured TP4 family points only.

**P0 correction to attached image:**  
Do not render `TP8/PP4`; it was not a measured configuration in this campaign.

Signal label:

```text
TP4/PP1 → TP4/PP2 → TP4/PP4
workload-specific measured frontier
```

128K and 512K frontier values may be exposed via context toggle or evidence drawer.

## Key Takeaways

- TP8/PP1 is slower at 8K and 128K.
- TP8/PP1 becomes faster at 512K and 1M.
- Fixed-TP=4 PP scaling creates a latency/resource trade-off.
- There is no universal parallelism winner.

## Decision Changed

> **Add GPUs along the parallelism dimension with positive measured latency elasticity for the target workload/SLO, and show the resource-occupancy trade-off.**

---

# 15. PAGE 7 — TP Decode Communication

## Route

```text
#keyfinds/tp-decode
```

## Header

```text
7  TP Decode Communication
Category: Cross-tool Evidence
```

## Hero

Profiler @8K:

```text
TP4/PP1 AllReduce Self CUDA   251.529 ms
TP8/PP1 AllReduce Self CUDA   583.866 ms
same calls                    7040
ratio                         ~2.32×
```

E2E:

```text
8K TP8-vs-TP4 TPOT penalty   +41.9%
```

## Why It Matters

> Wider TP can hurt interactive decode when small-collective synchronization cost rises with TP width, even though the collective count is unchanged.

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH that wider-TP synchronization contributes
```

## Scope

Controlled comparison:

```text
TP4/PP1 ↔ TP8/PP1
```

Profiler:

```text
8K only
```

E2E TPOT:

```text
8K ●
128K ●
512K ●
1M ●
```

Do not pretend the 8K profiler fraction is measured at all four contexts.

## Quick Comparison — E2E TPOT

| Context | TP8 vs TP4 TPOT penalty |
|---|---:|
| 8K | +41.9% |
| 128K | +39.0% |
| 512K | +25.0% |
| 1M | +17.9% |

## Primary visual — full-width evidence chain

```text
1. NCCL MICROBENCH
   small-message latency ratio ~1.9–2.2× where supported by processed points

        ↓

2. PYTORCH PROFILER @8K
   251.529ms → 583.866ms
   same 7040 AllReduce calls

        ↓

3. E2E TPOT
   +41.9% / +39.0% / +25.0% / +17.9%
```

Do not mix PyTorch Self CUDA % and Nsight aggregate-work %.

Distributed decode profiles for:
```text
TP4/PP2
TP8/PP2
TP4/PP4
TP16/PP1
```
belong in Engineer/evidence drill-down, not this Signal chain.

## Key Takeaways

- Wider TP raises the measured small-collective cost.
- Rank-local AllReduce Self CUDA time increases ~2.32× at 8K with the same call count.
- The E2E TPOT penalty persists across all four context baselines, although its magnitude decreases.
- Mechanism evidence is strongest at 8K.

## Decision Changed

> **Validate small-collective synchronization cost before assuming wider TP improves interactive decode.**

---

# 16. PAGE 8 — Runtime Knobs

## Route

```text
#keyfinds/runtime-knobs
```

## Header

```text
8  Runtime Knobs
Category: Tuning Derivative
```

## Hero

Chunk 4K→16K TTFT reduction:

```text
128K   16.5%
512K   24.4%
1M     27.1%
```

1M c4 max_num_seqs:

```text
4   → 232.342s
8   → 232.364s
16  → 232.250s

spread ≈ 0.049%
```

## Why It Matters

> Some runtime knobs have a material measured derivative while others are effectively inert under the current occupancy state. Tuning effort should follow matched A/B sensitivity, not knob folklore.

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH for the max_num_seqs non-binding interpretation
```

## Scope

```text
TP4/PP1 FIXED
```

Chunk:
```text
128K ●
512K ●
1M ●
```

max_num_seqs:
```text
512K ●
1M ●
```

Do not add unmatched scale-out topologies.

## Quick Comparison

### Chunk size

| Context | 4K TTFT | 16K TTFT | Reduction |
|---|---:|---:|---:|
| 128K | 5.228s | 4.364s | 16.5% |
| 512K | 40.271s | 30.455s | 24.4% |
| 1M | 122.049s | 88.951s | 27.1% |

### max_num_seqs

512K c4:
```text
87.973 / 87.931 / 87.932s
spread 0.047%
```

1M c4:
```text
232.342 / 232.364 / 232.250s
spread 0.049%
```

## Visuals

Left:
```text
Chunk Size Leverage vs Context
```

Right:
```text
max_num_seqs Impact
```

Default right panel may show 1M c4; 512K is selectable/evidence-linked.

## Key Takeaways

- The chunk-size derivative becomes larger across 128K→1M in the measured range.
- max_num_seqs is nearly flat at the measured long-context c4 states.
- The scheduler occupancy stays below the configured max_num_seqs ceiling in these runs.
- Do not declare 16K universally optimal.

## Decision Changed

> **Tune only knobs with a material matched A/B derivative in the measured state.**

---

# 17. PAGE 9 — Busy GPU ≠ Efficient Serving

## Route

```text
#keyfinds/busy-gpu
```

## Header

```text
9  Busy GPU ≠ Efficient Serving
Category: Operational Trap
```

## Hero — 1M

```text
TP4/PP4
GPU util   62.8%
TTFT       28.568s

TP16/PP1
GPU util   80.6%
TTFT       68.197s

TP16/PP1 is 2.39× slower despite higher utilization.
```

## Why It Matters

> GPU utilization measures device activity, not useful-token efficiency. Communication kernels and synchronization can keep the GPU active while user-visible latency becomes worse.

Do not claim an exact percentage of “spin-wait” without direct trace attribution.

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM
```

## Scope

```text
GCP_NATIVE

TP4/PP4 ↔ TP16/PP1

128K ●
512K ●
1M ●
```

## Quick Comparison

| Context | TP4/PP4 util | TP4/PP4 TTFT | TP16/PP1 util | TP16/PP1 TTFT |
|---|---:|---:|---:|---:|
| 128K | 35.2% | 1.710s | 63.2% | 6.420s |
| 512K | 55.3% | 10.222s | 67.8% | 29.624s |
| 1M | 62.8% | 28.568s | 80.6% | 68.197s |

## Visuals

Left:
```text
GPU Utilization by Context
```

Right:
```text
TTFT by Context
```

Use log Y for TTFT if helpful.

Do not fit a regression or infer causality from correlation.

## Key Takeaways

- Higher utilization coexists with significantly worse TTFT in all three displayed contexts.
- Utilization includes communication/device activity, not only useful compute.
- End-to-end metrics must remain the deployment decision metrics.

## Decision Changed

> **Pair utilization with TTFT, TPOT, throughput and communication/profile composition; never use utilization alone to choose topology.**

---

# 18. PAGE 10 — KV Cache vs VRAM

## Route

```text
#keyfinds/kv-vram
```

## Header

```text
10  KV Cache vs VRAM
Category: Memory Semantics
```

## Hero — controlled TP4 PP sweep @1M

```text
TP4/PP1    KV 12.29%    peak memory 88.39 GiB
TP4/PP2    KV 5.91%    peak memory 88.69 GiB
TP4/PP4    KV 2.75%    peak memory 88.83 GiB
```

Replication:

```text
TP8/PP1 → TP8/PP2
KV 12.18% → 5.88%
```

## Why It Matters

> KV cache pressure and physical device-memory headroom are different metrics. Pipeline parallelism can strongly reduce reported KV pressure while total per-GPU memory telemetry remains high.

## Confidence

```text
Evidence: HIGH
Cause: LOW-MEDIUM for exact allocator/sharding interpretation
```

## Scope

Primary:
```text
TP4/PP1
TP4/PP2
TP4/PP4
1M
```

Replication:
```text
TP8/PP1
TP8/PP2
1M
```

Additional context baseline:
```text
TP4/PP1
8K ●
128K ●
512K ●
1M ●
```

**P0 correction to attached image:**  
Do not show `16K`, `32K`, or `64K` in the TP4/PP1 baseline rail; those context baselines are not present in the canonical V8 context-baseline matrix.

## Quick Comparison @1M

| Topology | Peak KV | Peak GPU memory |
|---|---:|---:|
| TP4/PP1 | 12.29% | 88.39 GiB |
| TP4/PP2 | 5.91% | 88.69 GiB |
| TP4/PP4 | 2.75% | 88.83 GiB |

TP4/PP1 context baseline:

| Context | Peak KV | Peak GPU memory |
|---|---:|---:|
| 8K | 0.13% | 86.67 GiB |
| 128K | 1.63% | 88.39 GiB |
| 512K | 6.46% | 88.39 GiB |
| 1M | 12.29% | 88.39 GiB |

Raw reported device capacity:

```text
97,887 MiB ≈ 95.59 GiB per GPU
```

## Primary visual

Title:

```text
KV Pressure vs Physical VRAM Reality
```

Preferred implementation:
- aligned two-panel chart

Acceptable:
- explicit dual-axis chart

If dual-axis:
```text
left Y  = Peak KV (%)
right Y = Peak GPU memory (GiB)
```

Do not put both metrics on one unlabeled percentage scale.

## Key Takeaways

- Reported KV pressure falls sharply as PP depth increases in the fixed-TP=4 sweep.
- Peak per-GPU memory telemetry remains high and nearly unchanged.
- TP8 PP1→PP2 independently reproduces the KV-pressure direction.
- KV% is not physical free-memory percentage.

## Decision Changed

> **Use KV% for cache pressure and device-memory telemetry for OOM/headroom decisions; never substitute one for the other.**

## Boundary

Do not infer:
- exact `1/PP` allocator law
- exact weights/activation/runtime/NCCL allocation split
- exact OOM margin from KV percentage
- 16K/32K/64K context baseline behavior

---

# 19. Evidence drill-down contract for all pages

Every page must make the following elements clickable where appropriate:

```text
hero metric
quick-comparison row
chart point
topology chip
context chip
replication badge
```

Click opens the existing in-place evidence experience.

Minimum evidence header:

```text
evidence ID
case
bench
TP/PP
context
load/concurrency
network provenance
metric
value
unit
sample count
p95 reliable
p99 reliable
```

Profiler evidence additionally requires:

```text
instrument
node
rank
phase
aggregation rule
denominator semantics
artifact path
```

---

# 20. Data object for the separate-page branch

Use one generated object to drive:

- page hero
- scope
- quick comparison
- charts
- takeaways
- decision
- evidence popup links

Recommended file:

```text
EXECUTIVE_DISCOVERIES_V5_SEPARATE_PAGES.json
```

Recommended fields:

```json
{
  "id": "runtime_knob_derivative",
  "route": "#keyfinds/runtime-knobs",
  "stable_discovery_id": "TOP_8_RUNTIME_KNOB_DERIVATIVE",
  "version": "5.0.0-separate-pages",
  "page_title": "Runtime Knobs",
  "category": "Tuning Derivative",
  "finding_type": "CONTROLLED_PERTURBATION",
  "signal_scope": {},
  "hero_metrics": [],
  "quick_comparison": {},
  "primary_visual": {},
  "secondary_visual": {},
  "takeaways": [],
  "decision_changed": "",
  "evidence_confidence": "",
  "causal_confidence": "",
  "boundaries": [],
  "evidence_ids": [],
  "derivation_ids": []
}
```

Do not hard-code a second copy of the values in HTML.

---

# 21. Explicit corrections to the ten attached visual references

The team must treat these as P0 before reproducing the screenshots.

| Visual issue | Required correction |
|---|---|
| Top bar says `8×H100 (SXM)` | use `16× RTX PRO 6000 Blackwell · 2×8` |
| Fabric page says `Native (Infiniband)` | use `GCP Native Fabric` |
| Fabric hero says `+276.7% / +3.9% 20G vs 100G` | label them `20G vs Native` |
| Fabric quick-comparison mockup numbers | regenerate from canonical rows |
| Confidence shown as arbitrary segmented bars | replace with categorical confidence badges |
| Long-context page shows cross-topology consistency bar | remove unless a matched cross-topology derivation is explicitly added |
| Parallelism quick-comparison title says `@1M` while listing four contexts | rename to `TP4/PP1 vs TP8/PP1 by Context` |
| Parallelism 128K TP4 value copied as 4.522s | use canonical 4.532s |
| Parallelism concept may show TP8/PP4 | do not render; no such measured campaign topology |
| KV page shows 8K→16K→32K→64K→128K→512K→1M baseline | use only canonical 8K→128K→512K→1M baseline |
| Prefix page can imply full-hit semantics | use first/cold + repeat-hit median + runtime hit/query counter ratio |
| Prompt admission can imply a stable maximum | use high-load median method |
| TP decode can mix profiler denominators | keep instrument semantics separate |
| Busy GPU can imply spin-wait percentage | do not claim without direct trace attribution |

---

# 22. CSS / responsive contract

The attached reference uses a persistent ~18% left rail and ~82% main content area at 1536×1024.

Do not force exact pixel reproduction if it harms readability.

Desktop target:

```text
left rail: 220–280px
main content: fluid
main rows: 3-column / 2-column / 2-column / 2-column
```

At narrower width:
- left rail may collapse to a dropdown / drawer
- Row A stacks to 1 column
- Row B/C/D stack cleanly
- never shrink tables to unreadable text

---

# 23. Acceptance tests — global

- [ ] Exactly ten Key Finds sub-pages exist.
- [ ] Left nav persists across all ten.
- [ ] Only selected page is visible.
- [ ] All page values come from the generated canonical object.
- [ ] No H100/SXM/Ada/NVLink/InfiniBand mockup identity leaks into production.
- [ ] Every topology is explicit TP/PP.
- [ ] Every page shows its measured context envelope.
- [ ] Unmeasured contexts are visible as unmeasured.
- [ ] Confidence is categorical, not invented numeric scoring.
- [ ] Decision Changed is workload-scoped.
- [ ] Every chart point can resolve to exact evidence.
- [ ] Existing evidence popup remains in-place; no redirect required.
- [ ] No generated-image number is accepted without data validation.

---

# 24. Acceptance tests — per page

## #1 Fabric
- [ ] Hero uses 20G vs Native deltas.
- [ ] 128K/512K/1M only.
- [ ] four distributed topologies.
- [ ] Native/100G/20G achieved transport provenance separate from configured label.

## #2 Concurrency
- [ ] TP4/PP1 8K→1M c1→c4.
- [ ] TP8/PP1 1M replication visible.
- [ ] no PP2/PP4/TP16 fake concurrency sweep.

## #3 Long-context
- [ ] TP4/PP4 matched 128K→512K.
- [ ] no 1M profiler endpoint implied.
- [ ] aggregate work not called critical path.

## #4 Prefix
- [ ] TP4/PP1 only.
- [ ] ~128K/~512K/1M.
- [ ] repeat-hit median, not mixed mean.
- [ ] no 100% hit language.

## #5 Admission
- [ ] TP4/PP1 open-loop only.
- [ ] 8K/128K only.
- [ ] high-load median normalization.

## #6 Parallelism
- [ ] TP4/PP1 vs TP8/PP1 across four contexts.
- [ ] TP4 PP1/PP2/PP4 frontier only.
- [ ] no TP8/PP4.
- [ ] no universal winner.

## #7 Decode
- [ ] TP4/PP1 vs TP8/PP1 primary.
- [ ] 8K profiler mechanism.
- [ ] 8K→1M E2E TPOT persistence.
- [ ] profiler denominators separate.

## #8 Runtime
- [ ] TP4/PP1 fixed.
- [ ] chunk 128K/512K/1M.
- [ ] maxseq 512K/1M.
- [ ] no unmatched topology overlay.

## #9 Busy GPU
- [ ] TP4/PP4 vs TP16/PP1.
- [ ] 128K/512K/1M.
- [ ] utilization not treated as useful-token efficiency.
- [ ] no invented spin-wait percentage.

## #10 KV vs VRAM
- [ ] TP4/PP1→PP2→PP4 primary.
- [ ] TP8/PP1→PP2 replication.
- [ ] context baseline only 8K/128K/512K/1M.
- [ ] 97,887 MiB raw capacity source.
- [ ] no allocator decomposition claim.

---

# 25. Definition of done

The ten-page Key Finds branch is ready for offline comparison with the single-page branch when:

1. Every page can be understood in <30 seconds at Signal depth.
2. A performance engineer can see context + topology coverage without opening evidence.
3. Each page contains only matched comparisons appropriate to the phenomenon.
4. Independent replication is shown when available and useful.
5. No page is visually enriched using unmatched configurations.
6. Every important number is evidence-linked.
7. All ten pages use the same design grammar, making cross-page navigation effortless.
8. No generated-image assumption survives into implementation.

---

# 26. Final implementation mandate

> **The separate-page design earns its extra screen space by making each finding clearer, not by adding more unsupported detail. Use the cleanest controlled experiment, expose context/topology coverage, show the strongest measured contrast, state the engineering decision, and preserve the full evidence chain one click away.**
