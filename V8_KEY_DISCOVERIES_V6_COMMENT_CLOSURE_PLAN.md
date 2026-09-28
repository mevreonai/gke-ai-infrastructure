# V8 Key Discoveries V6 — Comment Closure Plan
## Final implementation actions before technical sign-off

**Target HTML:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html`  
**Primary empirical source:** `results_V8_runs(4).zip`  
**Reference review:** `V8_KEY_DISCOVERIES_HYBRID_VALIDATED_IMPLEMENTATION_V6.md`  
**Purpose:** close the remaining Key Discoveries comments without reintroducing stale data, unsupported causal claims, or duplicated representations.

---

# 0. Current sign-off status

The current Key Discoveries implementation is **substantially improved but not yet sign-off ready**.

The measured Top-10 findings remain valid. The remaining work is primarily:

1. stale hard-coded values in one detailed chart,
2. source-of-truth duplication,
3. forensic routing,
4. duplicate modal/UI depth,
5. several residual wording issues,
6. legacy Key Finds / legacy evidence-object contamination risk,
7. missing explicit profile-completeness status in the Key Discoveries trust strip.

Do **not** mark Key Discoveries `FINAL / VALIDATED` until all P0 items and all release acceptance tests in this document pass.

---

# 1. Already closed — do not regress

These review comments are considered closed in the 27 Sept 7pm HTML and must remain closed.

| Item | Required state |
|---|---|
| Stable finding numbering | `1 Fabric, 2 Concurrency, 3 Long Context, 4 Prefix, 5 Admission, 6 Parallelism, 7 TP Decode, 8 Runtime, 9 Busy GPU, 10 KV/VRAM` |
| Concurrency 1M numbers | canonical real-run values |
| TP8/PP2 GPU-s | ~664.24, not ~767 |
| TP8/PP2 measured scatter point | included |
| TP Decode absolute TPOT | corrected at 8K/128K/512K/1M |
| Runtime maxseq typo | 232.364s, not 233.364s |
| TP8 physical memory telemetry | ~87.27 / ~87.51 GiB |
| Global Model KV arithmetic reconstruction | removed from displayed finding |
| `93% saturated!` | removed as a claim |
| Trust badge | `119/126 COMPLETED E2E ROWS VALIDATED` |
| Signal scope rails | present |
| Signal action | `View Detailed Finding ↓` |
| max_num_seqs causality | framed as non-binding, not “memory constrained” |

Validated 1M concurrency regression values:

```text
Output TPS    0.341470915 → 0.346655992
TTFT          93.394898s → 231.267511s
TPOT          10.227508ms → 267.410621ms
Queue @c4     134.427672s
```

Validated 1M max_num_seqs regression values:

```text
4  → 232.342s
8  → 232.364s
16 → 232.250s
```

---

# 2. P0-1 — Fix the remaining stale Fabric chart

## Current problem

The detailed Fabric table is corrected, but the detailed Chart.js 20G line chart still contains stale absolute TTFT literals.

Search the HTML for:

```text
2.926
18.860
2.510
15.650
```

These must not remain in the Key Discoveries detailed Fabric chart.

## Canonical 20G TTFT values

| Topology | 128K | 512K | 1M |
|---|---:|---:|---:|
| TP4/PP2 | 2.859s | 18.372s | 53.127s |
| TP8/PP2 | 2.810s | 15.546s | 41.472s |
| TP4/PP4 | 1.961s | 11.134s | 29.684s |
| TP16/PP1 | 31.053s | 128.275s | 256.889s |

## Required code state

The chart series must be generated from the same canonical values used by the Fabric Engineer table.

Do not maintain a second hand-written array.

### Closure test

```text
PASS when:
chart TP4/PP2 == table TP4/PP2 for all three contexts
chart TP8/PP2 == table TP8/PP2 for all three contexts
chart TP4/PP4 == table TP4/PP4 for all three contexts
chart TP16/PP1 == table TP16/PP1 for all three contexts
```

---

# 3. P0-2 — Eliminate independent literals: one canonical discovery object

## Current problem

The current HTML still contains separate content/value copies across:

```text
Finding Map
Signal cards
KD_PAGES_DATA
Chart.js arrays
legacy EXECUTIVE_DISCOVERIES / DISCOVERY_MAP
modal rendering
```

The stale Fabric chart proves that manual synchronization is not safe.

## Required architecture

Build one canonical object:

```text
RAW V8 RESULTS / PROFILE ARTIFACTS
             ↓
VERSIONED DERIVATIONS
             ↓
KD_DISCOVERIES_V6
             ↓
 ┌───────────────┬───────────────┬────────────────┐
 │ Finding Map   │ Signal Cards  │ Engineer Pages │
 └───────────────┴───────────────┴────────────────┘
             ↓
FORENSIC EVIDENCE VIEWER
```

At minimum, each discovery contains:

```json
{
  "stable_id": 1,
  "slug": "fabric-exposure",
  "headline": "...",
  "scope": {},
  "hero_metrics": [],
  "table_rows": [],
  "chart_series": [],
  "decision_changed": "...",
  "evidence_confidence": "HIGH",
  "causal_confidence": "MEDIUM-HIGH",
  "evidence_locators": [],
  "boundaries": []
}
```

## Mandatory rule

No chart may contain a manually typed value that already exists in the canonical object.

No Engineer table may contain a manually typed evidence ID if the row can be located by:

```text
case + bench + network_provenance
```

## Closure test

Build must fail if:

```text
Signal hero != Engineer hero
Chart point != canonical row / derivation
Scope rail != canonical scope
Evidence locator resolves to 0 rows
Evidence locator resolves to >1 row
```

---

# 4. P0-3 — Fix Forensics: “Inspect Evidence” must open exact evidence

## Current problem

The current Engineer pages display:

```text
Inspect Forensic Evidence →
```

but the action still calls `openFindingModal(...)`.

The transition bar also contains:

```text
Forensic Modal View →
```

and routes to the same duplicate finding modal.

This is not forensic inspection.

## Required behavior

Signal:

```text
View Detailed Finding ↓
```

Engineer:

```text
Inspect Evidence →
```

Forensics:

```text
open exact evidence popup
```

The Forensics action must call the actual in-place evidence viewer, e.g.:

```text
openEvidencePopup(...)
```

or an equivalent new V6 wrapper that resolves the exact evidence locator.

## Evidence view must identify

```text
evidence ID
case
bench
TP / PP
context
load / concurrency
network provenance
metric
value
unit
sample count
p95 reliable?
p99 reliable?
raw artifact path
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

## Important

Do not route the new Key Discoveries Forensics button into the legacy `EXECUTIVE_DISCOVERIES` object without first cleaning the stale legacy fields.

---

# 5. P0-4 — Remove the duplicate full-detail modal as a fourth information layer

The intended hierarchy is:

```text
SIGNAL
  ↓
ENGINEER
  ↓
FORENSICS
```

The current HTML also retains a full finding modal, producing:

```text
Signal
Engineer explorer
Full-detail modal
Forensic popup
```

This is redundant and increases drift risk.

## Required action

Preferred:

```text
Remove the full duplicate finding modal.
```

Alternative:

```text
Downgrade it to Quick Preview only.
```

If Quick Preview remains:

- it must consume `KD_DISCOVERIES_V6`,
- it must not contain independent numeric literals,
- it must not be labeled Forensic.

Remove/rename:

```text
Forensic Modal View →
```

---

# 6. P0-5 — Remove legacy stale-content contamination paths

The new Key Discoveries tab is cleaner, but the same HTML still contains older data/phrasing that can re-enter through legacy views.

## 6.1 Legacy Key Finds top-level tab

Current HTML still exposes:

```text
🎯 Key Finds
✨ Key Discoveries
```

For production:

```text
Key Discoveries = canonical Top-10 experience
```

After parity validation, hide/remove the legacy Key Finds tab.

During development only, it may remain behind a debug flag.

## 6.2 Legacy “noise” language

The HTML still contains:

```text
TP8/PP2 ... (noise)
```

for small signed Fabric deltas.

Remove `noise` unless replicate variance / CI supports that classification.

Use:

```text
small signed delta
```

or show only the measured signed percentage.

## 6.3 Legacy quadratic wording

The HTML still contains profiler text such as:

```text
driving quadratic prefill expansion
```

The validated Key Discoveries statement is narrower:

> Full-attention grouped GPU work shows empirical p≈1.99 over the matched 128K→512K profile interval.

If a legacy profiler record is surfaced by Forensics, replace the general “quadratic” conclusion with the measured-range empirical wording.

---

# 7. P0-6 — Restore profiler completeness to Key Discoveries trust strip

The Key Discoveries trust strip correctly shows:

```text
119/126 COMPLETED E2E ROWS VALIDATED
STRICT SUITE SIGN-OFF INCOMPLETE
```

Add:

```text
14/22 DISTRIBUTED PROFILES COMPLETE
```

Reason: this is one of the principal completeness limitations behind strict sign-off.

The trust strip should communicate three separate states:

```text
APPLICATION EVIDENCE: 119/126
PROFILE EVIDENCE: 14/22
STRICT SIGN-OFF: INCOMPLETE
```

Do not compress these into one generic “validated” badge.

---

# 8. P1 — Tighten remaining finding wording

These are not numeric blockers, but they are required for Chief-Architect-quality scientific language.

---

## 8.1 Finding 3 — Long-context Resource-Pressure Shift

Use:

> Full-attention grouped GPU work grew ~15.7× for a 4× context increase, corresponding to empirical p≈1.99 over the measured 128K→512K interval.

Use:

> KDA and MoE grouped GPU work grew ~3.8–4.0× over the same interval, consistent with approximately linear scaling over this measured range.

Do not use unqualified:

```text
O(N²)
scales linearly
becomes the exclusive bottleneck
ceases to dominate at extreme context
```

Mandatory guardrail:

> Aggregate GPU work ≠ exclusive request wall-clock critical path.

---

## 8.2 Finding 4 — Prefix Reuse

Use:

> Prefix reuse moves the measured TTFT curve from a super-linear cold regime toward a much lower near-linear repeat-hit regime over the tested range.

Do not say:

```text
bypasses the quadratic prefill curve
near-constant scaling
100% prefix hit
```

Routing/pool recommendation must remain an evaluation recommendation:

> Treat repeated-prefix traffic as a distinct workload class; evaluate routing or dedicated-pool strategies against actual reuse, residency and eviction behavior.

Do not claim the campaign proved a dedicated pool is always better.

---

## 8.3 Finding 6 — Parallelism Frontier

Validated 1M resource plane:

| Topology | TTFT | GPUs | GPU-s/request proxy |
|---|---:|---:|---:|
| TP4/PP1 | 93.248s | 4 | 372.99 |
| TP4/PP2 | 52.526s | 8 | 420.21 |
| TP4/PP4 | 28.568s | 16 | 457.09 |
| TP8/PP1 | 74.688s | 8 | 597.50 |
| TP8/PP2 | 41.515s | 16 | 664.24 |
| TP16/PP1 | 68.197s | 16 | 1091.15 |

Use short-context mechanism wording:

> At 8K/128K, the added TP synchronization cost is consistent with offsetting the compute benefit of wider TP.

Use long-context wording:

> At 512K/1M, measured E2E TTFT shows the compute-side benefit of wider TP outweighing the additional TP overhead in these runs.

Do not write universal:

```text
TP4 is better
TP8 is better
PP is the winner
```

---

## 8.4 Finding 7 — TP Decode Communication

Validated E2E TPOT:

| Context | TP4/PP1 | TP8/PP1 | TP8 penalty |
|---|---:|---:|---:|
| 8K | 4.475ms | 6.350ms | +41.9% |
| 128K | 5.106ms | 7.098ms | +39.0% |
| 512K | 7.565ms | 9.455ms | +25.0% |
| 1M | 10.267ms | 12.102ms | +17.9% |

Use:

> The 8K PyTorch-profiler AllReduce evidence contributes strongly to the observed short-context TPOT penalty.

Do not say:

```text
AllReduce causes the entire TPOT penalty
the same profiler fraction holds at 1M
```

128K/512K/1M are E2E persistence/corroboration, not repeated profiler proof.

---

## 8.5 Finding 9 — Busy GPU

Validated measured comparison:

| Context | TP4/PP4 util | TP4/PP4 TTFT | TP16/PP1 util | TP16/PP1 TTFT |
|---|---:|---:|---:|---:|
| 128K | 35.2% | 1.710s | 63.2% | 6.420s |
| 512K | 55.3% | 10.222s | 67.8% | 29.624s |
| 1M | 62.8% | 28.568s | 80.6% | 68.197s |

Search/remove these loaded chart labels:

```text
Erroneous High
Fast & Efficient
Up to 3.75× Slower!
```

Preferred chart labels:

```text
TP4/PP4 GPU activity
TP16/PP1 GPU activity

TP4/PP4 TTFT
TP16/PP1 TTFT
```

Use explanatory statement:

> GPU utilization reflects device activity, including communication kernels; it is not a direct measure of useful-token efficiency.

Do not infer exact spin-wait/barrier percentage.

---

## 8.6 Finding 10 — KV Cache vs VRAM

Validated 1M telemetry:

| Topology | Peak KV | Peak GPU memory telemetry |
|---|---:|---:|
| TP4/PP1 | 12.29% | 88.39 GiB |
| TP4/PP2 | 5.91% | 88.69 GiB |
| TP4/PP4 | 2.75% | 88.83 GiB |
| TP8/PP1 | 12.18% | 87.27 GiB |
| TP8/PP2 | 5.88% | 87.51 GiB |
| TP16/PP1 | 12.13% | 86.71 GiB |

Search/replace chart label:

```text
Peak Allocated Physical VRAM (GiB)
```

with:

```text
Peak GPU Memory Telemetry (GiB)
```

If showing capacity difference, label:

```text
Raw reported capacity − peak telemetry
```

not:

```text
Usable VRAM Headroom
```

unless allocator-reserved usable memory is separately established.

Remove all displayed arithmetic implying:

```text
PP × KV% = global model KV%
```

---

# 9. Evidence semantics — mandatory cleanup

Normalize displayed evidence classes to:

```text
MEASURED
CROSS-VALIDATED
DERIVED
MODELED
UNRESOLVED
```

Avoid exposing implementation-specific legacy labels such as:

```text
PRIMARY_NATIVE
PROFILER_DISTRIBUTED
```

as the reader-facing evidence class unless they are additionally mapped to the normalized class.

Keep:

```text
Evidence confidence
Causal confidence
```

separate.

Never attach causal confidence to a raw primitive datum.

---

# 10. Search-string cleanup before sign-off

The following strings should not remain in the production Key Discoveries path unless they appear only inside an explicit historical/dev comment:

```text
2.926
18.860
2.510
15.650

(noise)

Forensic Modal View

Erroneous High
Fast & Efficient

Peak Allocated Physical VRAM

Global Model KV Check
93% saturated

driving quadratic prefill expansion
```

Also verify the production top-level nav no longer exposes both:

```text
Key Finds
Key Discoveries
```

---

# 11. Mandatory automated parity validation

Before release, generate:

```text
KEY_DISCOVERIES_VALIDATION.json
KEY_DISCOVERIES_VALIDATION.md
```

Minimum tests:

```text
A. STABLE_ID_PARITY
map.id == signal.id == engineer.id == route.id

B. HERO_PARITY
signal.hero == engineer.hero

C. RAW_VALUE_PARITY
every primitive UI value == canonical run row

D. DERIVATION_PARITY
every derived UI value == versioned derivation

E. CHART_PARITY
chart point == canonical value used in table/card

F. EVIDENCE_UNIQUENESS
each evidence locator resolves to exactly one row

G. COMPARISON_COMPLETENESS
multi-row comparison records all input evidence IDs

H. SCOPE_PARITY
Signal scope rail == canonical measured scope

I. MISSING_DATA_RULE
missing / NOT_RUN never renders as zero

J. PROFILE_SEMANTICS
instrument + denominator explicit

K. ARTIFACT_EXISTENCE
all displayed raw/profile paths exist

L. TRUST_STATE
119/126, 14/22 and strict-signoff state match FINAL_VALIDATION

M. FORBIDDEN_CLAIMS
no universal winner
no 100% prefix-hit claim
no allocator law
no profiler-work == wall-clock critical path
no unsupported “noise” classification
```

Release should fail if any test fails.

---

# 12. Team closure matrix

| Priority | Comment | Required action | Closure evidence |
|---|---|---|---|
| P0 | Fabric stale detailed chart | generate chart from canonical Fabric object | screenshot + parity test |
| P0 | Duplicate numeric sources | create `KD_DISCOVERIES_V6` | code diff + no duplicate arrays |
| P0 | Forensics routes to finding modal | route exact evidence to evidence popup | click-through recording / test |
| P0 | Duplicate full-detail modal | remove or downgrade to Quick Preview | DOM check |
| P0 | Legacy Key Finds visible | hide after parity passes | production nav screenshot |
| P0 | Legacy noise/quadratic fields | clean/migrate forensic source objects | grep = 0 in production path |
| P0 | Missing 14/22 trust indicator | add profile completeness badge | screenshot |
| P1 | Long-context wording | measured-range empirical wording | text review |
| P1 | Prefix wording | super-linear → near-linear measured wording | text review |
| P1 | Parallelism mechanism | use “consistent with” | text review |
| P1 | TP Decode causality | use “contributes strongly” | text review |
| P1 | Busy GPU labels | neutral measured labels | chart screenshot |
| P1 | KV memory semantics | “telemetry”, not allocator claim | chart/table screenshot |

---

# 13. Final sign-off checklist

Do not sign off until every item is checked.

## Data integrity

- [ ] Fabric chart values equal canonical table values.
- [ ] Signal / Engineer / charts use one canonical object.
- [ ] No independent chart literals for measured values.
- [ ] Evidence locators resolve uniquely.
- [ ] Every multi-run comparison records all source rows.
- [ ] No missing/NOT_RUN value is rendered as zero.

## UX integrity

- [ ] Signal remains default.
- [ ] `View Detailed Finding` enters Engineer explorer.
- [ ] `Inspect Evidence` opens exact forensic evidence.
- [ ] No full duplicate modal masquerades as Forensics.
- [ ] Return to Signal preserves scroll position.
- [ ] Legacy Key Finds hidden in production.

## Trust strip

- [ ] `119/126 COMPLETED E2E ROWS VALIDATED`
- [ ] `14/22 DISTRIBUTED PROFILES COMPLETE`
- [ ] `STRICT SUITE SIGN-OFF INCOMPLETE`
- [ ] Native / 100G / 20G achieved bandwidth remains separate from configured network labels.

## Scientific wording

- [ ] No unsupported “noise”.
- [ ] No unqualified O(N²) campaign claim.
- [ ] No “near-constant” prefix scaling.
- [ ] No memory-causality assertion for max_num_seqs.
- [ ] No exact spin-wait/barrier attribution.
- [ ] No universal topology winner.
- [ ] No global-KV allocator reconstruction.
- [ ] No “usable VRAM” claim from simple arithmetic capacity difference.

## Forensics

- [ ] exact run identity visible.
- [ ] instrument visible.
- [ ] node/rank visible for profiler.
- [ ] denominator semantics visible.
- [ ] sample/reliability visible.
- [ ] artifact path exists.
- [ ] derivation inputs are traceable.

---

# 14. Definition of done

Key Discoveries is sign-off ready only when:

> **the same measured fact has one canonical value, one canonical scope, one canonical evidence chain, and consistent wording across Signal, Engineer, charts and Forensics.**

The final user journey must be:

```text
Campaign understanding
        ↓
Detailed engineering explanation
        ↓
Exact evidence
```

not:

```text
same finding copied into multiple independent representations
```

---

# 15. Chief Architect release criterion

> **Do not declare the Key Discoveries tab complete because the visuals look synchronized. Declare it complete only when synchronization is enforced by code. The dashboard should make strong findings visually obvious, but every claim must remain bounded by the exact context, topology, instrument and evidence available in the V8 campaign.**
