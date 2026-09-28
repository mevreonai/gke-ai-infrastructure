# V8 Key Discoveries — Hybrid SIGNAL + Engineer Explorer
## Validated Implementation Specification V6

**Target HTML:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_2amIST.html`  
**Primary empirical source:** `results_V8_runs(4).zip`  
**Target tab:** `Key Discoveries`  
**Implementation model:** **single-page SIGNAL view first + 10 detailed Engineer finding pages + in-place forensic evidence viewer**  
**Status:** data-audited implementation specification

---

# 0. Executive implementation decision

Keep the hybrid solution.

The product hierarchy should be:

```text
KEY DISCOVERIES
    │
    ├── 1. SIGNAL / CAMPAIGN VIEW
    │      60-second Finding Map
    │      10 concise evidence-backed cards
    │
    ├── 2. DETAILED FINDING / ENGINEER VIEW
    │      one of 10 finding pages
    │      persistent finding navigation
    │
    └── 3. INSPECT EVIDENCE / FORENSICS
           exact run / profiler / derivation / raw provenance
```

This is the preferred architecture because it preserves the system-level story while still giving an LLM performance engineer enough depth to challenge any finding.

Do **not** maintain a fourth, fully duplicated detailed representation.

The current full-detail modal should either:

1. be removed, or
2. be reduced to a lightweight **Quick Preview** that consumes the exact same canonical discovery object as the embedded Engineer explorer.

The embedded 10-page explorer remains the authoritative detailed view.

---

# 1. Validation statement

All numeric values explicitly marked **VALIDATED** in this document were recomputed or checked against the actual V8 real-run evidence package:

```text
results/real_data/final_validation/combined_vllm_runs.csv
results/real_data/final_validation/FINAL_VALIDATION.json
results/logs/preflight_node0/preflight.json
hardware_processed/*
profiles_torch_single_node/*
profiles_multi_node_native/*
```

The current HTML was also inspected for:

- stale duplicated values
- mismatched finding numbering
- evidence-ID drift
- scope drift
- causal overclaims
- duplicate interaction layers

Generated UI mockups are **not** treated as data sources.

---

# 2. Campaign truth that must appear in Key Discoveries

## Model

```text
moonshotai/Kimi-Linear-48B-A3B-Instruct
BF16 surrogate characterization
max model length = 1,048,576
```

## Hardware

```text
16 × NVIDIA RTX PRO 6000 Blackwell Server Edition
2 nodes × 8 GPUs/node
raw reported memory = 97,887 MiB ≈ 95.59 GiB / GPU
```

## Real-run coverage

```text
Application rows completed       119 / 126
NOT_RUN                          7
FAILED                           0
Distributed profiles complete   14 / 22
profiles_all_complete            false
serving_matrix_complete          false
nccl_policy_ok                   false
strict_full_coverage             false
full_suite_valid                 false
```

## Measured transport

```text
GCP_NATIVE          173.58 Gb/s
GCP_CAPPED_100G     56.84 Gb/s
GCP_CAPPED_20G      16.48 Gb/s
```

### Required trust-strip wording

Replace:

```text
E2E RUN MATRIX VALIDATED
```

with:

```text
119/126 COMPLETED E2E ROWS VALIDATED
```

Retain:

```text
STRICT SUITE SIGN-OFF INCOMPLETE
```

Reason: the completed application evidence is valid, but the serving matrix and full strict suite are not complete.

---

# 3. Stable finding IDs — P0

Use this numbering everywhere:

| ID | Finding |
|---:|---|
| 1 | Fabric Exposure |
| 2 | Concurrency |
| 3 | Long-context Resource-Pressure Shift |
| 4 | Prefix Reuse |
| 5 | Prompt-token Admission |
| 6 | Parallelism Frontier |
| 7 | TP Decode Communication |
| 8 | Runtime Knobs |
| 9 | Busy GPU ≠ Efficient Serving |
| 10 | KV Cache vs VRAM |

The current Signal cards have 5/6 and 7/8 visually swapped relative to the detailed-page IDs. This must be eliminated.

The following must all consume the same stable ID:

```text
Finding Map row
Signal card number
Signal card action
Engineer left-nav number
Engineer page object
route / slug
modal preview
evidence drill-down
```

---

# 4. One-source architecture — P0

The largest current implementation risk is duplicated literals.

Build:

```text
RAW RESULTS + PROFILE ARTIFACTS
            ↓
VERSIONED DERIVATION FUNCTIONS
            ↓
KD_DISCOVERIES_V6.json
            ↓
 ┌──────────────────┬──────────────────┬────────────────────┐
 │ 60-sec map       │ Signal cards     │ Engineer pages     │
 └──────────────────┴──────────────────┴────────────────────┘
            ↓
EVIDENCE / FORENSICS VIEWER
```

Do **not** maintain independent numeric copies in:

```text
HTML map markup
Signal-card markup
KD_PAGES_DATA
Chart.js arrays
legacy EXECUTIVE_DISCOVERIES
modal-specific payloads
```

Recommended canonical object:

```json
{
  "stable_id": 2,
  "slug": "concurrency",
  "finding_type": "MECHANISM_REPLICATION",
  "headline": "...",
  "scope": {},
  "signal_metrics": [],
  "engineer_tables": [],
  "visuals": [],
  "decision_changed": "...",
  "evidence_confidence": "...",
  "causal_confidence": "...",
  "boundaries": [],
  "evidence_locators": []
}
```

Evidence locators should be generated from:

```text
case
bench
network_provenance
metric
```

not handwritten `EV-xxx` strings.

The build must fail when a locator resolves to zero or more than one canonical row.

---

# 5. Evidence-ID integrity — P0

The current detailed-page dataset contains numerous stale evidence IDs.

Examples of required corrections:

```text
Fabric TP4/PP2 1M:
Native = EV-078
100G   = EV-090
20G    = EV-102

Concurrency 1M TP4:
c1 = EV-065
c4 = EV-067

Parallelism baseline:
8K    = EV-009 / EV-013
128K  = EV-010 / EV-014
512K  = EV-011 / EV-015
1M    = EV-012 / EV-016

Runtime 1M chunk:
4K  = EV-027
16K = EV-035

KV 1M:
TP4/PP1 = EV-012
TP4/PP2 = EV-078
TP4/PP4 = EV-084
TP8/PP1 = EV-016
TP8/PP2 = EV-081
```

For a comparison derived from multiple rows, show all supporting IDs or a derivation ID that records all input IDs.

A single evidence ID must never be presented as support for a three-network comparison.

---

# 6. Signal-card coverage rail — mandatory

Every Signal card gets one compact scope line.

Legend:

```text
● = directly measured for this finding
P = profiler endpoint
R = independent matched replication
— = not measured
```

Examples:

```text
Concurrency
CTX 8K● 128K● 512K● 1M● · TP4/PP1 PRIMARY · TP8/PP1 R@1M

Prefix
CTX 8K— ~128K● ~512K● 1M● · TP4/PP1 ONLY

Prompt Admission
CTX 8K● 128K● 512K— 1M— · TP4/PP1 OPEN-LOOP

TP Decode
8K P+E2E · 128K/512K/1M E2E · TP4/PP1 ↔ TP8/PP1

Long Context
CTX 8K— 128K P 512K P 1M— · TP4/PP4 matched profile
```

This is a trust feature, not decoration.

---

# 7. 60-second Finding Map — corrected content

Add a **Scope** column.

| # | Finding | Scope | Measured surprise / pattern | Decision |
|---:|---|---|---|---|
| 1 | Fabric Exposure | `128K→1M · 4 distributed topologies · Native/100G/20G` | `1M/20G: TP16/PP1 +276.69% vs TP4/PP4 +3.91% TTFT` | topology determines exposed fabric risk |
| 2 | Concurrency | `TP4/PP1 8K→1M c1→c4 · TP8/PP1 @1M replication` | `1M: +1.52% TPS · 2.48× TTFT · 26.15× TPOT · 134.43s queue` | admit from latency/queue SLO |
| 3 | Long Context | `TP4/PP4 profiler 128K→512K` | `attention ~15.7× vs NCCL ~2.18× grouped GPU work` | re-profile optimization target with context |
| 4 | Prefix Reuse | `TP4/PP1 only · ~128K/~512K/1M` | `1M: 94.227s cold → 2.614s repeat-hit median` | treat repeat-prefix traffic as separate workload class |
| 5 | Prompt-token Admission | `TP4/PP1 open-loop · 8K + 128K only` | `~18.20× req/s gap → ~1.14× input-token/s gap` | normalize prefill demand in tokens/s |
| 6 | Parallelism Frontier | `TP4↔TP8 8K→1M · TP4 PP frontier 128K→1M` | TP8 is slower at 8K/128K, faster at 512K/1M | choose parallelism dimension from workload elasticity |
| 7 | TP Decode | `8K profiler · 8K→1M E2E · TP4/PP1↔TP8/PP1` | same 7040 AllReduce calls; 8K TPOT +41.9% | validate collective cost before wider TP |
| 8 | Runtime Knobs | `TP4/PP1 · chunk 128K→1M · maxseq 512K/1M` | chunk leverage rises; maxseq remains nearly flat | tune knobs by measured derivative |
| 9 | Busy GPU | `TP4/PP4↔TP16/PP1 · 128K/512K/1M Native` | higher GPU activity coexists with far worse TTFT | utilization is not a topology selector |
| 10 | KV vs VRAM | `TP4 PP sweep @1M + TP8 replication · TP4 baseline 8K→1M` | KV falls sharply with PP while device memory remains high | separate cache pressure from physical headroom |

Map row action:

```text
View Detailed Finding ↓
```

Do not say “open full 10-page explorer” if the click opens a modal.

---

# 8. Finding 1 — Fabric Exposure

## Signal headline

> **The same measured fabric constraint produces radically different user-visible TTFT damage depending on topology.**

## Scope

```text
8K —
128K ●
512K ●
1M ●

TP4/PP2 ●
TP8/PP2 ●
TP4/PP4 ●
TP16/PP1 ●

GCP_NATIVE
GCP_CAPPED_100G
GCP_CAPPED_20G
```

## VALIDATED 20G delta heatmap

| Topology | 128K | 512K | 1M |
|---|---|---|---|
| TP4/PP2 | +8.01% | +2.37% | +1.14% |
| TP8/PP2 | +0.81% | -0.19% | -0.10% |
| TP4/PP4 | +14.67% | +8.93% | +3.91% |
| TP16/PP1 | +383.66% | +333.01% | +276.69% |

## VALIDATED 100G delta heatmap

| Topology | 128K | 512K | 1M |
|---|---|---|---|
| TP4/PP2 | +0.66% | +0.20% | +0.13% |
| TP8/PP2 | +1.36% | -0.18% | -0.13% |
| TP4/PP4 | +2.97% | +1.64% | +1.04% |
| TP16/PP1 | +51.64% | +45.47% | +36.36% |

Small negative TP8/PP2 deltas are signed observations. Do not call them noise without replicate variance.

## VALIDATED 1M exact comparison

| Topology | Native | 100G | Δ100G vs Native | 20G | Δ20G vs Native | Evidence IDs |
|---|---|---|---|---|---|---|
| TP4/PP2 | 52.526s | 52.597s | +0.13% | 53.127s | +1.14% | EV-078 / EV-090 / EV-102 |
| TP8/PP2 | 41.515s | 41.462s | -0.13% | 41.472s | -0.10% | EV-081 / EV-093 / EV-105 |
| TP4/PP4 | 28.568s | 28.866s | +1.04% | 29.684s | +3.91% | EV-084 / EV-096 / EV-108 |
| TP16/PP1 | 68.197s | 92.992s | +36.36% | 256.889s | +276.69% | EV-087 / EV-099 / EV-111 |

## Absolute TP16/PP1 20G tax

```text
128K  +24.63s
512K  +98.65s
1M    +188.69s
```

## Current HTML correction

The detailed 20G line chart currently contains stale absolute values for several topologies.

Use the exact values from the table above.

## Decision Changed

> **Choose and size scale-out topology from measured application exposure to transport degradation, not NIC/iperf capability alone.**

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM-HIGH
```

## Boundary

- no 8K application cap sweep
- no 50G/10G application claim
- configured network label != measured achieved bandwidth
- no universal topology winner

---

# 9. Finding 2 — Concurrency

## Signal headline

> **The concurrency dividend collapses as context grows.**

## Primary scope

```text
TP4/PP1 · c1→c4 · 8K/128K/512K/1M
TP8/PP1 · 1M c1/c2/c4 replication
```

## VALIDATED context sweep

| Context | Output TPS gain c1→c4 | TTFT multiplier | TPOT multiplier | c4 queue | Evidence IDs |
|---|---|---|---|---|---|
| 8K | +120.82% | 2.74× | 1.63× | 0.027s | EV-036 / EV-037 |
| 128K | +10.27% | 2.28× | 12.96× | 5.11s | EV-041 / EV-042 |
| 512K | +2.19% | 2.74× | 57.36× | 53.66s | EV-045 / EV-047 |
| 1M | +1.52% | 2.48× | 26.15× | 134.43s | EV-065 / EV-067 |

## VALIDATED 1M detailed values

```text
Output throughput
c1 0.34147 tok/s
c4 0.34666 tok/s
gain +1.52%

TTFT
93.395s → 231.268s
2.48×

TPOT
10.228ms → 267.411ms
26.15×

Queue c4
134.428s

Peak KV c4
15.51%

Preemptions c4
0
```

## Queue closure replication

```text
TP4/PP1 c2  96.4%
TP4/PP1 c4  97.5%
TP8/PP1 c2  95.7%
TP8/PP1 c4  97.2%
```

## Current HTML correction

The detailed page currently contains stale hero numbers such as:

```text
7.90 → 8.02 tok/s
11.2 → 293.7ms TPOT
```

Do not use them.

Use the validated values above.

## Decision Changed

> **Drive admission from TTFT/TPOT/queue SLOs; “fits in KV” is not production capacity.**

## Confidence

```text
Evidence: HIGH
Cause — added TTFT queue closure: HIGH
Cause — exclusive TPOT mechanism: MEDIUM
```

## Boundary

Do not create a universal `c=1` production cap without an explicit product SLO.

---

# 10. Finding 3 — Long-context Resource-Pressure Shift

## Headline

> **As context grows, full-attention grouped GPU work accelerates much faster than KDA, MoE, or NCCL in the matched TP4/PP4 profile pair.**

## Scope

```text
TP4/PP4 matched distributed prefill profiles
128K P
512K P

8K —
1M —
```

## Derived profiler result to regenerate from raw profile artifacts

```text
Full attention   ~15.7×   empirical p≈1.99
GEMM family       ~5.25×  empirical p≈1.20
KDA               ~3.95×  empirical p≈0.99
MoE               ~3.80×  empirical p≈0.96
NCCL              ~2.18×  empirical p≈0.56
```

Source artifacts:

```text
profiles_multi_node_native/tp4_pp4_dist/prefill_128k/
profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/
```

The build should regenerate these grouped values from those artifacts rather than hard-code them.

## Required wording correction

Do not write:

```text
Full Attention (O(N²))
```

as a campaign-proven complexity claim.

Use:

```text
Full-attention grouped GPU work · empirical p≈1.99 over measured 128K→512K range
```

Do not write:

```text
attention becomes the exclusive bottleneck
```

Use:

> **Subsystem resource pressure changes sharply with context.**

Mandatory footer:

> **Aggregate GPU work ≠ exclusive request wall-clock critical path.**

## Decision Changed

> **Re-profile the optimization target as context grows; one 128K profile is not sufficient for long-context deployment tuning.**

## Confidence

```text
Evidence: HIGH for matched profiler endpoints
Cause: MEDIUM for user-visible bottleneck interpretation
```

---

# 11. Finding 4 — Prefix Reuse

## Headline

> **Prefix reuse moves the measured TTFT curve into a dramatically lower, near-linear hit-conditioned regime.**

## Scope

```text
TP4/PP1 ONLY
8K —
~128K ●
~512K ●
1M ●
```

## VALIDATED comparison

| Context label | Exact requested tokens | First/cold TTFT | Repeat-hit median | Speedup | Runtime hit/query counter ratio | Evidence |
|---|---|---|---|---|---|---|
| ~128K | 131,328 | 4.8965s | 0.3307s | 14.8× | 87.33% | EV-053 |
| ~512K | 524,544 | 32.5762s | 1.1679s | 27.9× | 49.98% | EV-054 |
| 1M | 1,000,000 | 94.2272s | 2.6140s | 36.0× | 49.97% | EV-075 |

## VALIDATED empirical fit over only these measured endpoints

```text
Cold / first TTFT:
p = 1.4427
R² = 0.9979

Repeat-hit median:
p = 1.0013
R² = 0.9935
```

## Required wording correction

Do not say:

```text
quadratic → near-constant
```

The measured fit supports:

```text
super-linear cold curve (~p=1.44) → near-linear repeat-hit median (~p=1.00)
```

Do not use “100% prefix hit”.

## Decision Changed

> **Route and capacity-plan repeated-prefix traffic as a distinct workload class; topology sensitivity remains unmeasured.**

---

# 12. Finding 5 — Prompt-token Admission

## Headline

> **Requests/s exaggerates the capacity gap between different prompt lengths; input-token normalization reveals much closer accepted prefill work.**

## Scope

```text
TP4/PP1
open-loop

8K ●
128K ●
512K —
1M —
```

## VALIDATED high-load median method

Use the median achieved request throughput across:

```text
rps_1.00x
rps_1.10x
rps_1.25x
```

Results:

```text
8K
median achieved rate  = 3.358605 req/s
normalized input rate = 27.51K tok/s

128K
median achieved rate  = 0.184567 req/s
normalized input rate = 24.19K tok/s

raw request-rate gap  = 18.20×
input-token-rate gap  = 1.14×
```

Correct supporting evidence:

```text
8K high-load rows:
EV-116 / EV-117 / EV-118

128K high-load rows:
EV-123 / EV-124 / EV-125
```

## Current HTML correction

The detailed page currently cites chunk-size evidence IDs for this finding.

Remove those stale IDs.

## Decision Changed

> **Normalize prefill-heavy demand into prompt tokens/s before comparing capacity across prompt lengths.**

## Boundary

This is a two-context empirical fingerprint, not a universal admission law.

---

# 13. Finding 6 — Parallelism Frontier

## Headline

> **The useful direction for adding GPUs changes with context.**

## VALIDATED TP-width comparison

| Context | TP4/PP1 TTFT | TP8/PP1 TTFT | TP8 effect | Evidence IDs |
|---|---|---|---|---|
| 8K | 0.222s | 0.263s | +18.5% | EV-009 / EV-013 |
| 128K | 4.532s | 4.810s | +6.1% | EV-010 / EV-014 |
| 512K | 31.916s | 28.089s | -12.0% | EV-011 / EV-015 |
| 1M | 93.248s | 74.688s | -19.9% | EV-012 / EV-016 |

Interpretation:

```text
8K    TP8 slower
128K  TP8 slower
512K  TP8 faster
1M    TP8 faster
```

## VALIDATED 1M TTFT/resource plane

| Topology | TTFT | GPUs | GPU-s/request proxy | Evidence |
|---|---|---|---|---|
| TP4/PP1 | 93.248s | 4 | 372.99 | EV-012 |
| TP4/PP2 | 52.526s | 8 | 420.21 | EV-078 |
| TP4/PP4 | 28.568s | 16 | 457.09 | EV-084 |
| TP8/PP1 | 74.688s | 8 | 597.50 | EV-016 |
| TP8/PP2 | 41.515s | 16 | 664.24 | EV-081 |
| TP16/PP1 | 68.197s | 16 | 1091.15 | EV-087 |

Measured TP4-family lower-left progression:

```text
TP4/PP1 → TP4/PP2 → TP4/PP4
```

Label it:

```text
workload-specific measured frontier
```

## Current HTML corrections

1. Current Signal card shows TP8/PP2 near `767 GPU-s`; correct value is **664.24 GPU-s**.
2. The detailed page must not omit TP8/PP2 from the full measured-point scatter.
3. Never render TP8/PP4; it was not a measured topology.
4. Use canonical baseline evidence IDs shown above, not stale IDs.

## Decision Changed

> **Add GPUs along the parallelism dimension with positive measured latency elasticity for the target workload/SLO, while exposing the resource-occupancy trade-off.**

## Boundary

No universal “best topology”.

---

# 14. Finding 7 — TP Decode Communication

## Headline

> **Wider TP increases the measured short-decode synchronization cost; the E2E TPOT penalty persists across the context baselines.**

## Scope

```text
TP4/PP1 ↔ TP8/PP1

8K:
profiler mechanism + E2E

128K / 512K / 1M:
E2E corroboration only
```

## Validated profiler anchor @8K

```text
TP4/PP1 PyTorch AllReduce Self CUDA = 251.529 ms
TP8/PP1 PyTorch AllReduce Self CUDA = 583.866 ms
AllReduce calls                      = 7040 in both
ratio                                ≈2.32×
```

Source artifacts:

```text
profiles_torch_single_node/tp4_8k_decode/pytorch_profiler.json
profiles_torch_single_node/tp8_8k_decode/pytorch_profiler.json
```

## VALIDATED E2E TPOT table

| Context | TP4/PP1 TPOT | TP8/PP1 TPOT | TP8 penalty | Evidence IDs |
|---|---|---|---|---|
| 8K | 4.475ms | 6.350ms | +41.9% | EV-009 / EV-013 |
| 128K | 5.106ms | 7.098ms | +39.0% | EV-010 / EV-014 |
| 512K | 7.565ms | 9.455ms | +25.0% | EV-011 / EV-015 |
| 1M | 10.267ms | 12.102ms | +17.9% | EV-012 / EV-016 |

## Current HTML correction

The detailed page currently has stale absolute TPOT values at 128K/512K/1M even though the displayed percentage penalties are approximately correct.

Use the exact table above.

## Instrument rule

Do not combine:

```text
PyTorch Self CUDA %
Nsight aggregate GPU-work %
```

into one percentage.

Always label instrument + denominator.

## Decision Changed

> **Validate small-collective synchronization cost before assuming wider TP improves interactive decode.**

## Boundary

The causal profiler evidence is strongest at 8K; do not claim the same profiler fraction at 1M.

---

# 15. Finding 8 — Runtime Knobs

## Headline

> **Some runtime knobs have a material matched derivative; others are non-binding in the measured occupancy state.**

## Scope

```text
TP4/PP1 FIXED

Chunk:
128K ●
512K ●
1M ●

max_num_seqs:
512K ●
1M ●
```

## VALIDATED chunk comparison

| Context | chunk=4K TTFT | chunk=16K TTFT | Reduction | Evidence IDs |
|---|---|---|---|---|
| 128K | 5.228s | 4.364s | 16.5% | EV-024 / EV-032 |
| 512K | 40.271s | 30.455s | 24.4% | EV-026 / EV-034 |
| 1M | 122.049s | 88.951s | 27.1% | EV-027 / EV-035 |

## VALIDATED max_num_seqs

```text
512K c4
maxseq 4   87.973s
maxseq 8   87.931s
maxseq 16  87.932s
spread     0.047%
evidence   EV-050 / EV-051 / EV-052

1M c4
maxseq 4   232.342s
maxseq 8   232.364s
maxseq 16  232.250s
spread     0.049%
evidence   EV-071 / EV-072 / EV-073
```

## Current HTML corrections

1. `233.364s` is a typo. Correct value is **232.364s**.
2. Do not say the flat max_num_seqs result is **because memory constrained it**.
3. Supported statement:

> **The configured max_num_seqs ceiling was not reached in these runs; therefore the knob is non-binding in the measured state.**

The exact lower-level reason is not established by this sweep alone.

## Decision Changed

> **Tune only knobs with a material matched A/B derivative in the measured state.**

---

# 16. Finding 9 — Busy GPU ≠ Efficient Serving

## Headline

> **Higher GPU activity does not identify the better serving topology.**

## Scope

```text
GCP_NATIVE
TP4/PP4 ↔ TP16/PP1

128K ●
512K ●
1M ●
```

## VALIDATED comparison

| Context | TP4/PP4 util | TP4/PP4 TTFT | TP16/PP1 util | TP16/PP1 TTFT | TP16/PP1 latency ratio | Evidence IDs |
|---|---|---|---|---|---|---|
| 128K | 35.2% | 1.710s | 63.2% | 6.420s | 3.75× | EV-082 / EV-085 |
| 512K | 55.3% | 10.222s | 67.8% | 29.624s | 2.90× | EV-083 / EV-086 |
| 1M | 62.8% | 28.568s | 80.6% | 68.197s | 2.39× | EV-084 / EV-087 |

## Required wording corrections

Do not write:

```text
SM activity measures barrier stall, not user work
```

Use:

> **GPU utilization measures device activity, which can include communication kernels; it is not a direct measure of useful-token efficiency.**

Do not write:

```text
>76% of TP16 execution is collective AllReduce
```

unless the denominator is explicitly the aggregate GPU-kernel-work denominator from the exact captured profile.

Preferred phrasing:

> **The captured TP16 profile contains a large aggregate GPU-kernel-work share attributed to AllReduce; this must not be interpreted as an exclusive wall-clock critical-path percentage.**

## Decision Changed

> **Pair utilization with TTFT, TPOT, throughput and profiler composition; never use utilization alone to choose topology.**

## Confidence

```text
Evidence: HIGH
Cause: MEDIUM
```

---

# 17. Finding 10 — KV Cache vs VRAM

## Headline

> **Reported KV-cache pressure and physical device-memory occupancy are different capacity signals.**

## Scope

```text
Primary controlled PP sweep @1M:
TP4/PP1
TP4/PP2
TP4/PP4

Replication:
TP8/PP1
TP8/PP2

Additional:
TP16/PP1

TP4/PP1 context baseline:
8K / 128K / 512K / 1M
```

## VALIDATED 1M topology table

| Topology | Peak KV | Peak GPU memory | Evidence |
|---|---|---|---|
| TP4/PP1 | 12.29% | 88.39 GiB | EV-012 |
| TP4/PP2 | 5.91% | 88.69 GiB | EV-078 |
| TP4/PP4 | 2.75% | 88.83 GiB | EV-084 |
| TP8/PP1 | 12.18% | 87.27 GiB | EV-016 |
| TP8/PP2 | 5.88% | 87.51 GiB | EV-081 |
| TP16/PP1 | 12.13% | 86.71 GiB | EV-087 |

## VALIDATED TP4/PP1 context baseline

| Context | Peak KV | Peak GPU memory | Evidence |
|---|---|---|---|
| 8K | 0.13% | 86.67 GiB | EV-009 |
| 128K | 1.63% | 88.39 GiB | EV-010 |
| 512K | 6.46% | 88.39 GiB | EV-011 |
| 1M | 12.29% | 88.39 GiB | EV-012 |

Raw reported device capacity:

```text
97,887 MiB ≈ 95.59 GiB
```

## P0 removals

Remove the current:

```text
Global Model KV Check
~11.82% (2×5.91%)
~11.00% (4×2.75%)
~11.76% (2×5.88%)
```

Those arithmetic reconstructions imply an allocator/denominator law that is not established.

Also replace:

```text
93% saturated!
```

with:

> **88.83 GiB peak telemetry on a raw-reported ~95.59 GiB device**

Replace:

```text
Usable VRAM Headroom
```

with:

```text
Raw reported capacity − peak telemetry
```

unless allocator-reserved/usable memory semantics are separately proven.

## Current HTML numeric correction

Actual TP8 memory telemetry:

```text
TP8/PP1  87.27 GiB
TP8/PP2  87.51 GiB
```

Do not use the current ~88.65/~88.70 GiB values.

## Decision Changed

> **Use KV% for cache pressure and physical device-memory telemetry for OOM/headroom analysis; never substitute one for the other.**

## Confidence

```text
Evidence: HIGH
Cause: LOW-MEDIUM for exact allocator/sharding interpretation
```

---

# 18. Hybrid UX corrections

## 18.1 Signal remains default

Opening Key Discoveries should show the Signal campaign view at the top.

The user should not have to choose a mode before seeing the campaign story.

## 18.2 Card action

Rename Signal-card:

```text
Inspect Evidence ↓
```

to:

```text
View Detailed Finding ↓
```

because the current action scrolls to the Engineer explorer.

## 18.3 Engineer action

Inside the detailed page, provide:

```text
Inspect Evidence →
```

which opens the actual forensic evidence viewer.

## 18.4 Finding-map action

A map row should either:

```text
scroll to Engineer explorer + select finding
```

or:

```text
open Quick Preview
```

but the label must state which.

Do not label a modal action “open full explorer”.

## 18.5 Preserve scroll state

When returning from Engineer to Signal:

```text
restore previous Signal scroll position
```

This makes cross-finding investigation much faster.

---

# 19. Retire the legacy `Key Finds` tab after validation

During development, keeping both is useful for A/B inspection.

For production:

```text
Key Discoveries = canonical replacement
```

Hide/remove the old `Key Finds` tab after the new tab passes the automated parity tests.

Two public top-level tabs containing substantially the same findings create:

- user ambiguity
- duplicated maintenance
- evidence drift
- inconsistent conclusions

---

# 20. Forensic evidence viewer contract

Do not create another evidence system.

Reuse the in-place viewer.

Required tabs:

```text
1. Finding
2. Measured Telemetry
3. Cross-Evidence / Profiler
4. Derivation
5. Raw Provenance
6. Boundary / Follow-up
```

For every primitive row:

```text
evidence_id
case
bench
TP/PP
context tokens
load semantics/value
network provenance
metric
unit
value
sample count
p95 reliable
p99 reliable
artifact path
```

Profiler evidence additionally:

```text
instrument
node
rank
phase
aggregation rule
denominator semantics
profile completeness
artifact path
```

---

# 21. Automated build-time parity tests — mandatory

The Key Discoveries build should fail when any of these fail.

```text
A. stable IDs
map.id == signal.id == engineer.id == route.id

B. hero parity
signal.hero_metric == engineer.hero_metric

C. raw-value parity
every displayed primitive value == canonical source value

D. derivation parity
every displayed derived value == versioned derivation output

E. evidence resolution
each evidence locator resolves uniquely

F. comparison completeness
a comparison requiring N rows contains all N input evidence IDs

G. scope parity
contexts/topologies shown in Signal == canonical scope

H. missing evidence
missing/NOT_RUN is never rendered as zero

I. artifact path
every displayed raw/profile path exists

J. profiler semantics
instrument + denominator are explicit

K. trust state
strict suite badge follows FINAL_VALIDATION.json

L. forbidden claims
no universal winner / 100% prefix hit / allocator law / profiler=critical-path
```

Recommended CI output:

```text
KEY_DISCOVERIES_VALIDATION.json
KEY_DISCOVERIES_VALIDATION.md
```

---

# 22. P0 implementation checklist

Before this version is presented as validated:

- [ ] Fix stable numbering 1–10 everywhere.
- [ ] Generate all map/card/detail content from one canonical discovery object.
- [ ] Replace stale handwritten evidence IDs with generated locators.
- [ ] Correct stale Fabric detailed absolute TTFT values.
- [ ] Correct detailed Concurrency hero TPS/TPOT values.
- [ ] Correct Parallelism TP8/PP2 GPU-s value.
- [ ] Include TP8/PP2 as a measured scatter point.
- [ ] Correct detailed TP Decode absolute TPOT values.
- [ ] Correct Runtime `233.364s` typo to `232.364s`.
- [ ] Correct TP8/PP1 and TP8/PP2 physical memory values.
- [ ] Remove KV “Global Model KV Check”.
- [ ] Remove “93% saturated!” wording.
- [ ] Replace E2E matrix trust badge with completed-row wording.
- [ ] Add context/topology coverage rail to every Signal card.
- [ ] Change card action from “Inspect Evidence” to “View Detailed Finding”.
- [ ] Route Engineer “Inspect Evidence” to forensic viewer.
- [ ] Remove or downgrade duplicate full-detail modal.
- [ ] Tighten Long Context complexity wording.
- [ ] Tighten Prefix scaling wording.
- [ ] Remove unsupported max_num_seqs memory-causality claim.
- [ ] Remove unsupported Busy-GPU barrier/spin-wait claims.
- [ ] Hide legacy Key Finds tab after parity validation.

---

# 23. P1 presentation improvements

After P0 data integrity is complete:

1. Keep Signal cards visually short.
2. Use one dominant contrast per card.
3. Keep Decision Changed to one sentence.
4. Keep confidence categorical.
5. Use `MEASURED`, `DERIVED`, `CROSS-VALIDATED`, `MODELED`, `UNRESOLVED`.
6. Use context chips consistently across all cards.
7. Show independent replication as a small badge, not another full chart.
8. Keep full tables in Engineer view.
9. Put formulas only in Derivation/Forensics.
10. Make all exact chart points clickable.

---

# 24. Desired final user journey

An experienced LLM inference engineer should be able to answer:

## In 60 seconds

```text
What are the 10 most consequential findings?
Which are long-context-specific?
Which are topology-specific?
Which have independent replication?
What architecture decision changes?
```

## In 5 minutes

```text
What exact contexts/topologies support the finding?
What are the exact measurements?
Is the result measured or derived?
What are the reliability limits?
```

## In forensic review

```text
Which exact run/profile supports this point?
Which node/rank/instrument?
What was the aggregation?
What raw artifact can I inspect?
```

That is the standard the hybrid tab should meet.

---

# 25. Final Chief Architect implementation mandate

> **Key Discoveries must be a decision surface built from one canonical evidence graph—not ten manually synchronized stories. Keep the Signal view compact enough to expose system-level regime changes, keep the Engineer pages deep enough to challenge each finding, and make every material claim traceable to real V8 run or profiler evidence. Impact should come from measured contrast and decision consequence, never from stronger wording than the evidence supports.**

---

# Appendix A — Current high-risk stale items

These are known examples and should be explicitly regression-tested:

```text
Finding 1:
stale absolute 20G chart values

Finding 2:
stale detailed TPS / TPOT hero values

Finding 5:
wrong open-loop evidence IDs

Finding 6:
wrong/stale baseline evidence IDs
wrong TP8/PP2 GPU-s value
TP8/PP2 omitted from full scatter

Finding 7:
stale 128K/512K/1M absolute TPOT values
wrong longer-context evidence IDs

Finding 8:
233.364 typo
wrong chunk/maxseq evidence IDs
unsupported memory-causality wording

Finding 9:
wrong evidence pairs
over-strong communication/wait wording

Finding 10:
wrong evidence IDs
wrong TP8 VRAM values
unsupported Global Model KV reconstruction
unsupported “saturated” wording
```

---

# Appendix B — Validated key numbers for regression tests

## Fabric

```text
1M Native / 100G / 20G
TP4/PP2   52.526419 / 52.596877 / 53.127085s
TP8/PP2   41.514880 / 41.462069 / 41.471619s
TP4/PP4   28.567955 / 28.865661 / 29.683658s
TP16/PP1  68.196792 / 92.991995 / 256.889474s
```

## Concurrency 1M TP4

```text
TPS     0.341470915 → 0.346655992
TTFT    93.394898 → 231.267511s
TPOT    10.227508 → 267.410621ms
queue   134.427672s
```

## Prefix

```text
~128K 4.896505 → 0.330738s
~512K 32.576217 → 1.167912s
1M    94.227243 → 2.613997s
```

## Admission

```text
8K    3.358605009 req/s  27513.692 input tok/s
128K  0.184567076 req/s  24191.576 input tok/s
```

## TP decode E2E

```text
8K    4.474753 / 6.350044 ms
128K  5.105683 / 7.098200 ms
512K  7.565417 / 9.455463 ms
1M    10.266643 / 12.101510 ms
```

## KV/VRAM @1M

```text
TP4/PP1  KV 12.289626%  VRAM 88.391602 GiB
TP4/PP2  KV 5.910601%  VRAM 88.686523 GiB
TP4/PP4  KV 2.748287%  VRAM 88.834961 GiB
TP8/PP1  KV 12.177271%  VRAM 87.274414 GiB
TP8/PP2  KV 5.881557%  VRAM 87.514648 GiB
TP16/PP1 KV 12.128736%  VRAM 86.713867 GiB
```
