# V8 Dashboard 26 Sept 1am — Deterministic Closure Re-Audit

**Latest dashboard reviewed:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_26thSept_1amIST.html`  
**Frozen review baseline:** `V8_V4_25SEP_7AM_FINAL_DETERMINISTIC_CLOSURE_REAUDIT(1).md`  
**Scope:** closure verification of the existing review comments only, plus separately labelled objective integrity regressions found by machine-checking the same HTML. No new optimization requirements are introduced.

## 0. Anti-hallucination / impact-preservation method

This review follows the same frozen contract as the prior re-audit:

1. A previous comment is not reopened because wording could be nicer.
2. Valid measured values are never removed to close a messaging comment.
3. `FIXED` requires the visible UI **and** the backing discovery/evidence path to agree.
4. Provenance checks are performed against the embedded `CANONICAL_DASHBOARD_DATA.evidence_registry`, `EXECUTIVE_DISCOVERIES`, `PROFILER_REGISTRY`, chart click handlers, and `exactMap`.
5. Any newly detected issue is listed separately as an **objective integrity regression** and is not silently mixed into the prior-comment closure score.

### Impact scale

| Impact label | Meaning |
|---|---|
| **↑ High positive** | Fix prevents wrong evidence, wrong arithmetic, or a claim that could invalidate the finding. |
| **↑ Medium positive** | Fix strengthens defensibility while keeping the headline result intact. |
| **↔ Neutral to headline** | Label/messaging/provenance cleanup only; measured result remains unchanged. |
| **No change needed** | Prior comment is closed; reopening it would add review drift without evidence. |

> **Rule for the team:** preserve the headline measurements. Change only incorrect provenance, inconsistent derived arithmetic, or wording stronger than the evidence.

# 1. Overall status

The 26 Sept 1am build is materially better than the 25 Sept 7am build. The previous broad evidence-mapping failure is almost entirely repaired, Scheduler/KV decision criteria are now explicit, the Executive Deployment Recipe is corrected, Scale-Up long-prefill wording is corrected, and the Profiler now has a first-class artifact registry.

However, **not all comments are closed yet**. The deterministic alias check improved from 1/26 in the prior build to **91/93 exactMap aliases correct** in the latest build. The two remaining failures are both prefix-reuse mappings.

| Tab / area | 26 Sept 1am status | Impact assessment |
|---|---|---|
| Global / campaign identity | ✅ **FIXED** | No further change helps; do not reopen. |
| Executive | ✅ **FIXED for prior Executive comments** | The prior recipe/mechanism comments are closed without reducing impact. |
| Key Finds / Top 10 | 🟡 **PARTIAL** | Visible cards improved strongly, but several backing discovery objects/profiler links remain inconsistent. |
| Scale-Up | 🟡 **PARTIAL** | C6 is fixed; C2 still has one deterministic NUMA sentence in the decision table. |
| Scale-Out | ✅ **FIXED for prior comments** | No further change required from this audit. |
| Long Context | 🟡 **PARTIAL** | Main lineage is fixed; prefix evidence IDs are wrong; FP8 remains quantitative-looking despite NOT_RUN. |
| Scheduler & KV | ✅ **FIXED for prior comments** | Heuristic knee and allocator-boundary wording are now explicit. |
| Profiler | 🟡 **PARTIAL** | Major semantics/provenance improved; backing profiler registry still contains stronger causal language and Top #1 profile mismatch. |
| Evidence | 🟡 **PARTIAL / localized P0** | 91/93 aliases correct; prefix128K/512K still map to wrong EV rows. |
| Cross-cutting data contract | ❌ **NOT CLOSED** | Manual chart data arrays remain and are still a drift source. |

# 2. Global / Cross-Tab

| ID | Prior comment | Status now | Impact of current change |
|---|---|---|---|
| G-01 | Remove native-only title semantics | ✅ FIXED | No change needed. |
| G-02 | Distinguish Native primary vs capped auxiliary sweeps | ✅ FIXED | No change needed; preserves network-sensitivity impact. |
| G-03 | 119/126 + 7 NOT_RUN, not full sign-off | ✅ FIXED | No change needed. |
| G-04 | Profiler denominator 14/22, 11 Native + 3 capped-100G | ✅ FIXED | No change needed. |
| G-05 | Blackwell identity, not Ada | ✅ FIXED | No change needed. |
| G-06 | Remove native-only footer semantics | ✅ FIXED | No change needed. |
| G-07 | Remove unsupported `no fabricated values` assertion | ✅ FIXED | No change needed. |

# 3. Executive Tab

| Item | Prior comment | Status now | What changed / deterministic check | Impact perspective |
|---|---|---|---|---|
| E-01 | 14/22 distributed profile KPI | ✅ FIXED | Still correct. | No change needed. |
| E-02 | Correct 8K KV/memory | ✅ FIXED | Still correct. | No change needed. |
| E-03 | Correct TP4/PP4 128K memory | ✅ FIXED | Still correct. | No change needed. |
| E-04 | Finish MiB/GiB cleanup | ✅ FIXED | `88.8GB VRAM` no longer appears. | ↑ Medium positive; unit ambiguity removed. |
| E-05 | Soften 1M c1 mechanism | ✅ FIXED | Measured vs interpretation boundary retained. | No impact loss. |
| E-06 | No universal strict c=1 cap | ✅ FIXED | SLO-dependent wording retained. | No impact loss. |
| E-07 | Scale-out causal overclaim | ✅ FIXED | Observation and interpretation remain separated. | No impact loss. |
| E-08 | Campaign scope/gaps explicit | ✅ FIXED | Native/100G/20G vs unmeasured 50G/10G application scope remains clear. | No impact loss. |
| E-09 | Populate guidance | ✅ FIXED | Guidance remains populated. | Positive. |
| E-10 | Network sensitivity measured | ✅ FIXED | Retained. | Positive. |
| Exec TTFT values | Canonical values | ✅ FIXED | Values remain correct. | No change needed. |
| Exec TTFT mapping | Exact evidence identity | ✅ FIXED | Chart click handler now uses direct EV-010/011/012, EV-014/015/016, EV-082/083/084, EV-085/086/087. | ↑ High positive; auditability fixed without touching values. |
| Exec TPOT value | TP16 512K = 17.413 ms | ✅ FIXED | 17.413 retained. | No change needed. |
| Exec TPOT mapping | Exact evidence identity | ✅ FIXED | Direct EV grid is used. | ↑ High positive. |
| Exec capacity | 784.1 tok/s c32, no universal optimum | ✅ FIXED | Direct EV IDs retained. | No change needed. |
| E-11 | BabelStream semantics | ✅ FIXED | No prior regression found. | No change needed. |
| E-12 | Profiler work != critical path | ✅ FIXED | Boundary retained. | No impact loss. |
| E-13 | TP width values | ✅ FIXED | Canonical values retained. | No change needed. |
| E-14 | Chunk fairness unresolved | ✅ FIXED | Still scoped. | No impact loss. |
| E-15 | max_num_seqs non-binding state | ✅ FIXED | Still scoped. | Positive operational value. |
| E-16 | FP8-KV guarded NOT_RUN | ✅ FIXED in Executive | Still guarded. | No fake delta. |
| E-17 | Prefix first/repeat semantics | ✅ FIXED in visible Executive | Values retained. | Impact preserved; separate prefix click issue tracked in Long/Evidence. |
| E-18 | Network sensitivity measured | ✅ FIXED | Retained. | Positive. |
| E-19 | Correct 8K TPOT | ✅ FIXED | Retained. | No change needed. |
| E-20 | Remove c64 extrapolation | ✅ FIXED | Scope remains c1→c32. | No impact loss. |
| E-21 | No 128K compute-bound claim | ✅ FIXED | No unqualified roofline claim. | ↑ Medium positive. |
| E-22 | No 512K compute/VRAM-bound claim | ✅ FIXED | Removed. | ↑ Medium positive. |
| E-23 | Correct queue values | ✅ FIXED | 134.43s / 107.01s retained. | Strong measured impact preserved. |
| Deployment Recipe | Remove FLOP/pipeline-dominated and deterministic primary-limiter wording | ✅ FIXED | Latest recipe says `Measured regime` and `Candidate mechanism / next evidence`; NCU/timeline verification is explicitly pending. | ↑ Medium positive; makes the card stronger, not weaker. |
| What Not To Do | Keep guardrails | ✅ FIXED | Retained. | No change needed. |

# 4. Scale-Up Tab

| ID | Prior comment | Status now | Current issue | Impact perspective |
|---|---|---|---|---|
| C1 | Canonical TTFT + DERIVED crossover | ✅ FIXED | No issue. | No change needed. |
| C2 | NUMA mechanism must be qualified as contributor, not exclusive cause | 🟡 PARTIAL | Chart interpretation now says `cross-validated contributor ... timeline corroboration pending`, but the Decision Output row still says `Single-NUMA ring avoids dual-NUMA bridge AllReduce penalty` without the qualifier. | ↔ Neutral to headline. Keep 4.475 vs 6.350 ms; only align the table wording with the already-correct chart wording. |
| C3 | TPS matched lineage | ✅ FIXED | No issue. | No change needed. |
| C4 | Concurrency title/lineage | ✅ FIXED | No issue. | No change needed. |
| C5 | NCCL exact sizes/BusBW/PCIe, no NVLink | ✅ FIXED | No issue. | No change needed. |
| C6 | Remove unproven FLOP-scaling explanation | ✅ FIXED | Latest row says TP8 lowers measured TTFT and exact compute vs collective balance requires NCU/timeline confirmation. | ↑ Medium positive; measured TP8 advantage remains fully intact. |

# 5. Scale-Out Tab

All D1–D10 comments from the frozen audit remain closed.

| ID | Status now | Impact |
|---|---|---|
| D1 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D2 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D3 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D4 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D5 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D6 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D7 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D8 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D9 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |
| D10 | ✅ FIXED | No change needed; do not reopen without new contradictory data. |

The Scale-Out tab therefore remains one of the strongest sections of the current build. Its measured topology/network sensitivity impact is not diluted by the review.

# 6. Long Context Tab

| Item | Prior comment | Status now | Current issue | Impact perspective |
|---|---|---|---|---|
| E1 TPOT/KV/c2 lineage | Use one extension c1/c2/c4 lineage | ✅ FIXED | 139.37s / 44.34s extension story remains consistent. | No change needed. |
| E2 Prefix values | Use first/cold + repeat-hit median | ✅ FIXED numerically | 14.8× / 27.9× / 36× values remain. | Headline impact preserved. |
| E3 Long concurrency mapping | Exact evidence click | ✅ FIXED | Direct EV-065..070 grid now used. | ↑ High positive. |
| E4 Scheduler | Correct 4/8/16 sweep | ✅ FIXED | Direct EV-071/072/073. | No change needed. |
| E5 Chunk | Correct values/no fairness claim | ✅ FIXED | Direct EV-027/031/035. | No change needed. |
| E6 FP8 | Do not imply a quantitative FP8 comparison when FP8 is NOT_RUN | 🟡 PARTIAL | The chart still plots BF16 88.7 GiB against `FP8 KV: NOT_RUN`; its dataset/axis still uses `Peak VRAM (GB)` / `VRAM Usage (GB)`. | ↔ Neutral to headline. Replace chart with a NOT_RUN status card or clearly non-comparative BF16 baseline; no FP8 data is lost because none exists. |
| E7 CPU offload | NOT_RUN only | ✅ FIXED | No stale quantitative offload chart. | No change needed. |
| E8 KPI | c1 cleanest/SLO-driven | ✅ FIXED | Retained. | No change needed. |
| E9 distributed matrix | No unstated SLO label | ✅ FIXED | Retained. | No change needed. |
| E10 serving decision | No mixed lineage | ✅ FIXED | Retained. | No change needed. |
| NEW / H4-linked Prefix evidence mapping | Prefix 128K/512K must open their own evidence rows | 🔴 NOT FIXED / LOCAL P0 | `chart_long_prefix` uses EV-073/EV-074/EV-075. EV-073 is max_num_seqs16, EV-074 is FP8-KV NOT_RUN, and only EV-075 is prefix1M. Correct prefix rows are EV-053/EV-054/EV-075. | ↑ High positive. This is a provenance repair only; keep every prefix metric and speedup unchanged. |

# 7. Scheduler & KV Tab

| ID | Prior comment | Status now | Current check | Impact perspective |
|---|---|---|---|---|
| F1 | Exact KV chart mapping | ✅ FIXED | Direct EV grid is used for single-node and distributed series. | ↑ High positive. |
| F2 | Peak running/waiting semantics | ✅ FIXED | Retained. | No change needed. |
| F3 | Queue exact extension lineage | ✅ FIXED | Direct extension EV IDs are used. | ↑ High positive. |
| F4 | 0 preemptions observed, not `Zero Memory Thrashing` | ✅ FIXED | Correct label remains. | No impact loss. |
| F5 | max_num_seqs scoped/non-binding | ✅ FIXED | Retained. | Positive. |
| F6 numeric | Correct KV/queue/memory ledger | ✅ FIXED | Retained. | No change needed. |
| F6 interpretation | Allocator sharding must be `consistent with`, not asserted | ✅ FIXED | Latest takeaway explicitly says `consistent with distributing ... exact allocator sharding is not directly measured`. | ↑ Medium positive; KV impact stays. |
| F7 8K knee | Define criterion or call candidate heuristic | ✅ FIXED | Latest card says `Candidate Capacity Knee` and names the heuristic: slope inflection of TPOT / queue degradation. | ↑ Medium positive; makes the decision reproducible. |
| F8 128K open-loop | Canonical values | ✅ FIXED | Retained. | No change needed. |
| F9 admission | No undefined SLO-safe; define candidate threshold | ✅ FIXED | Latest decision uses `candidate admission limits`, `evaluate`, and explicit SLO dependence. | ↑ Medium positive; preserves cliff impact without inventing SLO. |

# 8. Profiler Tab

| ID | Prior comment | Status now | Current check | Impact perspective |
|---|---|---|---|---|
| G1 | Hardware identity / 14-of-22 completeness | ✅ FIXED | Retained. | No change needed. |
| G2 single-node | Kernel shares valid | ✅ FIXED | Rank-0 semantics retained. | No change needed. |
| G2 semantic denominator | Aggregate GPU work, not decode wall time | ✅ FIXED | Visible chart uses aggregate GPU kernel-work. | ↑ High positive. |
| G2 distributed aggregation | State exact rank OR reproducible aggregation | ✅ FIXED for visible profiler | TP16 is explicitly Node0 Rank0 with all-rank mean/range in PR-004; TP4/PP4 is explicitly Stage0/Rank0 in PR-005. | ↑ High positive; preserves raw percentages while removing topology-wide ambiguity. |
| G3 | Document PT operator grouping recipe | ✅ FIXED | Grouping recipe is now printed above the chart. | ↑ Medium positive. |
| G4 | Aggregate host API time, not wall-clock | ✅ FIXED | Chart label and axis now say `Aggregate Host API Time`. | ↑ Medium positive. |
| G5 | Remove roofline/100%-empirical; add exact provenance | ✅ FIXED | Bad labels are absent and kernel-latency clicks resolve to PR-001/002/005. | ↑ Medium positive. |
| G6 | Resource pressure != critical path; no unsupported FLOP/memory-bound labels | ✅ FIXED | Ledger language remains aggregate work/resource pressure; CUDA Graph is only a candidate experiment. | ↑ High positive. |
| G7/G8/G9 | Top15 identity, 22-point matrix, no 27-barrier/61-layer contamination | ✅ FIXED | No prior regression found. | No change needed. |
| G10 | Soften root-cause/prescriptive wording | 🟡 PARTIAL | Visible profiler is much better (`Cross-Node Synchronization`, `TP4 vs TP8 Trade-off`, candidate optimization). However PR-002/PR-003 backing entries still encode deterministic phrases such as `across 22 layers`, `barrier overhead`, and `due to cross-NUMA ... traversal` as if directly observed. | ↔ Neutral to headline. Keep 251.5/583.9ms and 7040 calls; make backing observation wording match the visible cross-validated/contributor language unless a raw trace explicitly proves the layer mapping. |

# 9. Evidence Tab / Drill-Down

## 9.1 Machine-checked exactMap status

- Aliases checked: **93**
- Correct: **91**
- Incorrect: **2**

| Alias | Current target | Actual current target | Correct target | Status |
|---|---:|---|---:|---|
| `tp4_prefix128k` | `EV-073` | `tp4_1m_maxseq16` / `1m_c4` | `EV-053` | ❌ |
| `tp4_prefix512k` | `EV-074` | `tp4_fp8_kv_1m` / `1m_c1` | `EV-054` | ❌ |

The two bad mappings are therefore not an assumption: they are direct contradictions between `exactMap` and the same HTML's canonical `evidence_registry`.

| ID | Prior comment | Status now | Impact perspective |
|---|---|---|---|
| H1 | Status contract | ✅ FIXED | No change needed. |
| H2 | Scope filter | ✅ FIXED | No change needed. |
| H3 | p95/p99 gating | ✅ FIXED | No change needed. |
| H4 | Exact chart→Evidence identity | 🟡 PARTIAL / localized P0 | ↑ High positive to finish. 91/93 aliases are fixed; prefix128K/512K remain wrong, and `chart_long_prefix` repeats those wrong IDs. |
| H5 | Claim registry must not reintroduce unsupported mechanism/SLO | 🟡 PARTIAL | ↑ Medium positive. Most rows are improved, but `Pipeline parallelism avoids cross-node AllReduce collective stalls` is still stated as a resolved interpretation rather than a measured sensitivity/contributor. |
| H6 | Runtime acceptance contract | ✅ FIXED | No change needed. |
| H7 | Current network coverage source | ✅ FIXED | No change needed. |

# 10. Cross-Cutting / Data Contract

| ID | Prior comment | Status now | Deterministic check | Impact perspective |
|---|---|---|---|---|
| I1 | Canonical data must drive charts; remove manually duplicated performance arrays | ❌ NOT FIXED | Latest HTML still contains 28 `safeInitChart(...)` initializations and 71 literal `data:[...]` arrays. | ↑ High positive engineering impact. This does not change current measurements; it prevents future drift. |
| I2 | Selectors functional or scope-only | 🟡 MOSTLY FIXED | Scale-Out is functional; profiler scenario chips still primarily filter the table rather than every profiler visualization. | Low impact; optional polish after evidence integrity. |
| I3 | Slow completed runs must not be failed | ✅ FIXED | No regression detected. | No change needed. |
| I4 | Manifest-bind model metadata/formulas | 🟡 PARTIAL | Correct 27/20/7 identity is used, but discovery/UI strings remain manually repeated. | ↑ Medium long-term; prevents future architecture drift without changing current result. |

# 11. Key Finds / Top 10 — Visible Card vs Backing Object

This section is deliberately strict: a visible card can be excellent while its Inspect-Evidence discovery object is stale. That is **not** a reason to weaken the card; it is a reason to align the backing object.

| Top | Status now | What is closed | What is still open | Impact of remaining fix |
|---:|---|---|---|---|
| 1 | ❌ NOT FIXED | Visible card keeps the 15.7× / 3.9× / 3.8× result, MEDIUM causal label, and critical-path boundary. | Visible decision still prescribes FlashAttention/chunk vs MoE/GEMM priorities. More seriously, backing inputs PR-004 and PR-006 are TP16/PP1 profiler records while the finding explicitly claims matched TP4/PP4 128K→512K profiles; the backing raw profile list still exposes only TP4/PP4 128K, not a first-class TP4/PP4 512K profile record. | ↑ High positive. Fix provenance and turn the prescriptive sentence into `candidate focus to validate`; do not change the measured scaling table. |
| 2 | 🟡 PARTIAL | Visible card is correctly workload-scoped; formula now says dimensionless hidden-width-equivalent coefficient. | Backing `decision_changed` still says `Disallow cross-node TP16 ... standardize on TP4/PP4`, which contradicts the visible no-universal-winner message. | ↑ Medium positive. Align backing decision to visible card; keep +276.7% vs +3.91% unchanged. |
| 3 | 🟡 PARTIAL | Lineage, queue closure, visible causal split, and EV-065..070 are correct. | Backing `decision_changed` still says `KV capacity remains ~84% free` and `latency SLOs are destroyed`, which conflicts with the dashboard's own KV%-vs-VRAM caution and undefined-SLO guardrail. | ↑ Medium positive. Replace with `reported KV utilization remains ~15.5% while TTFT/TPOT degrade sharply`; no metric changes. |
| 4 | ❌ NOT FIXED | Visible card now correctly makes sticky routing a candidate experiment. | Backing evidence IDs remain EV-073/074/075; correct prefix IDs are EV-053/054/075. Backing decision also still says `Deploy prefix caching...` unconditionally. | ↑ High positive. Fix IDs and align decision; preserve all 14.8×/27.9×/36× numbers. |
| 5 | ❌ NOT FIXED | Visible card wording and six high-load evidence IDs are corrected. | Backing confidence is still HIGH/HIGH rather than MED-HIGH / LOW-MED, and backing decision says ten 128K requests create `160×` the prompt stress of ten 8K requests; token count ratio for equal request count is 16×, not 160×. | ↑ High positive. Correct the backing arithmetic/confidence. The ~27.5K vs ~24.2K headline remains unchanged. |
| 6 | 🟡 PARTIAL | Visible WHY is now neutral; full canonical TP/PP evidence set is correctly linked. | Backing object still has causal confidence HIGH and a universal deployment instruction (`Deploy TP4... Scale out via PP4 rather than TP16`) instead of the visible elasticity/SLO-scoped decision. | ↑ Medium positive. Align object to visible decision; preserve all η and GPU-s values. |
| 7 | 🟡 PARTIAL | Visible card is now workload-scoped; E2E EV-009/013 and PR-002/003 are linked; raw NCCL path is listed. | Backing causal confidence remains HIGH vs visible MED-HIGH; there is still no first-class NCCL primitive evidence ID, only a raw path. PR-002 also states `7040 ... across 22 layers`, a layer mapping not established by the provided dashboard/audit. | ↑ Medium positive. Keep the 19→37μs / 251.5→583.9ms / +41.9% chain; tighten only provenance/claim strength. |
| 8 | 🟡 PARTIAL | Correct maxseq and chunk EV IDs are now linked; visible mechanism is scoped. | Backing causal confidence remains HIGH and decision says `focus ... entirely` on chunk/token budget; boundary adds OOM-risk language not demonstrated by this A/B result. | ↑ Medium positive. Match backing object to visible MED-HIGH/scoped language; no measured result changes. |
| 9 | 🟡 PARTIAL | Visible card is strong and correctly says utilization alone is insufficient; causal label MEDIUM. | Backing object still says causal HIGH, `Never use ...`, `Rely exclusively...`, and asserts >40% active spin-wait cycles—stronger than the visible evidence contract. | ↑ Medium positive. Align backing object; retain utilization/TTFT comparison. |
| 10 | ❌ NOT FIXED | Visible card is now correctly cautious and shows only measured KV% + GPU memory. | Backing object still contains causal HIGH, `96.00 GiB`, `7.86 GiB actual headroom`, and `8.19%` headroom. `96.00 - 88.83 = 7.17`, not 7.86; the object also attributes memory to weights/activations/runtime/NCCL without allocator instrumentation. | ↑ High positive. Remove unsupported headroom/decomposition or bind it to a normalized device-capacity source; preserve the measured KV% and 88.x-GiB telemetry. |

## 11.1 High-impact results that must remain

- Fabric: **+276.7% vs +3.91% TTFT** under configured-20G vs Native at 1M.
- 1M concurrency: **+1.52% output TPS, 2.48× TTFT, 26.15× TPOT, ~134.43s queue, 0 preemptions**.
- Resource-pressure scaling: **~15.7× attention vs ~3.9× KDA / ~3.8× MoE**.
- Prefix reuse: **14.8× / 27.9× / 36.0×** repeat-hit improvement.
- Prompt-token fingerprint: **~27.5K vs ~24.2K input tok/s**.
- Parallelism elasticity and all GPU-s/request proxy values.
- TP decode evidence chain: NCCL → PT Profiler → Nsight → E2E.
- Runtime-knob derivative: **<0.05% max_num_seqs spread vs ~27.1% chunk TTFT reduction**.
- GPU-utilization/TTFT divergence.
- KV% vs peak GPU-memory telemetry.

> None of the remaining fixes requires deleting these measurements.

# 12. Objective integrity regressions found in this latest build

These are separated from the frozen closure score to avoid moving the goalposts.

### N-01 — Prefix evidence-ID regression (P0 localized)

- `tp4_prefix128k` is mapped to EV-073, but EV-073 is `tp4_1m_maxseq16 / 1m_c4`; correct prefix128K is EV-053.
- `tp4_prefix512k` is mapped to EV-074, but EV-074 is `tp4_fp8_kv_1m / 1m_c1`; correct prefix512K is EV-054.
- `tp4_prefix1m` → EV-075 is correct.
- The same wrong EV trio is used by `chart_long_prefix` and Top #4 discovery inputs.

### N-02 — Top #1 profiler topology mismatch (P0 for discovery auditability)

Top #1 explicitly says the scaling result comes from **matched TP4/PP4 128K and 512K profiles**. Its backing inputs include PR-004 and PR-006; PR-004 is TP16/PP1 128K and PR-006 is TP16/PP1 512K. The latest first-class profiler registry therefore does not actually provide the TP4/PP4 128K+512K pair needed to support the card.

### N-03 — Backing discovery objects still carry stale/stronger claims

The visible Top-10 cards have been cleaned substantially, but several `EXECUTIVE_DISCOVERIES` entries still contain older universal recommendations, higher causal confidence, or unsupported derived quantities. Because Inspect Evidence reads these objects, this is a real UI consistency issue, not stylistic preference.

# 13. Recommended fix order

## P0

1. Fix prefix evidence identity everywhere: EV-053 / EV-054 / EV-075.
2. Create/use correct first-class TP4/PP4 128K and 512K profiler artifacts for Top #1, or remove profiler IDs that point to TP16.
3. Re-run an automated test: every chart/discovery datum's `evidence_id` must match its own case/bench/network/profile identity.

## P1

1. Align every Top-10 backing discovery object with the already-clean visible card (confidence, decision, boundary).
2. Fix Top #10 derived memory/headroom arithmetic by removing unsupported headroom until capacity units/source are normalized.
3. Align Scale-Up C2 Decision Output wording with its already-qualified chart interpretation.
4. Convert Long FP8 visualization into a NOT_RUN status treatment.
5. Finish Profiler backing-object wording (`due to`, `22 layers`, barrier attribution) unless exact raw trace mapping is available.
6. Soften the Evidence Decision Claim Registry row that says PP `avoids cross-node AllReduce collective stalls`; use measured sensitivity/communication-structure language.

## P2

1. Replace manual chart arrays with generated canonical chart data.
2. Generate card text, discovery object, confidence, click target, and artifact paths from one canonical discovery schema.
3. Manifest-bind architecture/formula values.

# 14. Final sign-off

**Status: DATA/EVIDENCE SIGN-OFF STILL PENDING, but very close.**

Most previous tab-level comments are now closed. The remaining issues are concentrated rather than broad:

- prefix evidence linkage,
- Top #1 profiler provenance,
- stale backing Top-10 discovery objects,
- one Scale-Up causal sentence,
- FP8 NOT_RUN presentation,
- manual data duplication.

From an impact perspective, the latest changes **helped**: they made the dashboard more defensible without removing the strongest results. The next pass should **not** add new findings or soften the headline measurements. It should finish object/provenance consistency so the visible impact and the evidence drawer tell exactly the same story.
