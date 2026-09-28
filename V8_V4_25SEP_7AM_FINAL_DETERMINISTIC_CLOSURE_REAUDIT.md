# V8 Dashboard 25 Sept 7am — Final Deterministic Closure Re-Audit

**Reviewed dashboard:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_25thSept_7amIST.html`  
**Prior closure baseline:** `V8_V4_24SEP_3PM_DEEP_CLOSURE_REAUDIT(2).md`  
**Top-10 baseline:** `V8_EXECUTIVE_TOP10_DEEP_CHARACTERIZATION_IMPLEMENTATION_V2.md` + the immediately preceding Top-10 review comments in the team thread.  
**Review scope:** closure verification only. This pass does **not** invent new optimization requirements.

## 0. How this review avoids hallucinated feedback / review drift

This pass uses a frozen review contract:

1. **No new comment is added just because wording could be prettier.** A status is checked only against an already-written audit/Top-10 requirement, or against an objective regression that violates that same requirement.
2. **Measured data is never weakened to fix messaging.** If a number/table is valid, it stays. A wording change only separates `MEASURED` observation from `DERIVED/CROSS-VALIDATED` interpretation or from an untested deployment prescription.
3. **A comment is called `FIXED` only when both the visible UI and the backing evidence object/click-through satisfy it.** A visually corrected card with a stale/wrong backing object is `PARTIAL`.
4. **Provenance comments are machine-checked.** The embedded `evidence_registry`, `EXECUTIVE_DISCOVERIES`, chart queries, and `exactMap` were parsed directly from the 7am HTML.
5. **No external knowledge is used to override campaign truth.** The canonical run registry embedded in this HTML and the attached audit are the basis of this closure review.

### Status legend

| Status | Meaning |
|---|---|
| ✅ **FIXED** | The exact prior comment is closed in visible UI and backing evidence/provenance. |
| 🟡 **PARTIAL** | Some part is fixed, but the original risk remains in another UI/object/provenance path. |
| ❌ **NOT FIXED** | The original problematic statement/behavior is still present. |
| 🔴 **REGRESSION / P0** | A change now produces objectively incorrect evidence linkage or mixes/points to the wrong canonical record. |

### Impact-preservation rule

> **Do not delete strong measurements to satisfy this audit.** Keep the measured numbers and high-impact discovery. Change only (a) unsupported causal wording, (b) untested prescription, (c) incorrect provenance, or (d) inconsistent derived arithmetic.

This is particularly important for the Top 10: most remaining comments do **not** ask the team to weaken the findings. They ask the UI to preserve the strong observation while making the evidence chain defensible.

# 1. Executive closure summary

The 7am build closes the two major numerical regressions that blocked the 3pm build:

- TP4 1M c2 extension story now uses **139.37 s TTFT / 44.34 s queue** rather than splicing the older 150.54 s / 55.40 s row.
- Executive TP16/PP1 512K TPOT is now **17.413 ms**, replacing 16.892 ms.

The largest remaining blocker is no longer a benchmark value. It is **evidence identity**: the new `exactMap` claims deterministic mapping, but most of its hard-coded EV IDs point to different cases than the query label.

Machine check: among **26 case-specific aliases**, only **1** currently points to the canonical evidence row implied by its alias.

| Area | 7am status | Main reason |
|---|---|---|
| Global / campaign identity | ✅ FIXED | Original scope/status comments closed. |
| Executive | 🟡 PARTIAL | Deployment Recipe still overstates FLOP/primary-limiter mechanisms; evidence click mapping is wrong. |
| Key Finds / Top 10 | 🟡 PARTIAL | Core measured discoveries remain strong; several remaining issues are messaging-only, but #5/#6/#7/#8/#10 have real provenance/object problems. |
| Scale-Up | 🟡 PARTIAL | Long-prefill FLOP mechanism and deterministic NUMA wording remain. |
| Scale-Out | ✅ FIXED for the attached audit comments | D1–D10 closure items are resolved in visible UI. |
| Long Context | 🟡 PARTIAL | Main c2 lineage fixed; FP8 still shown as a quantitative-looking chart; click mapping is affected by global evidence-map regression. |
| Scheduler & KV | 🟡 PARTIAL | Knee criteria and exact KV-stage mechanism remain too strong; evidence mapping affected globally. |
| Profiler | 🟡 PARTIAL | Distributed aggregation, grouping provenance, and CUDA API wording are not fully closed. |
| Evidence | 🔴 REGRESSION / P0 | `exactMap` is deterministic but largely maps to the wrong EV rows. |
| Cross-cutting data contract | ❌ NOT CLOSED | Hard-coded chart arrays remain; canonical registry and UI wiring can drift. |

# 2. Global / Cross-Tab

| ID | Prior comment | 7am status | Deterministic check | Why the comment matters / impact |
|---|---|---|---|---|
| G-01 | Remove native-only title semantics | ✅ FIXED | Header no longer says native-only. | Prevents false scope limitation; no data change. |
| G-02 | Distinguish primary Native from auxiliary 100G/20G | ✅ FIXED | Banner/header explicitly separate Native primary and capped sweeps. | Preserves network-sensitivity impact while keeping provenance clear. |
| G-03 | Do not imply 119/119 full sign-off | ✅ FIXED | Executive shows 119/126 + 7 guarded NOT_RUN + strict sign-off incomplete. | Avoids overstating campaign completeness. |
| G-04 | Profiler denominator must be 14/22, 11 Native + 3 capped-100G | ✅ FIXED | Executive KPI shows 14/22 and composition. | Keeps profiler completeness honest. |
| G-05 | Remove Ada identity | ✅ FIXED | Rendered identity is RTX PRO 6000 Blackwell Server Edition. | Hardware identity is part of reproducibility. |
| G-06 | Remove native-only footer semantics | ✅ FIXED | No rendered native-only campaign statement remains. | No impact loss. |
| G-07 | Remove unsupported 'no fabricated values' assertion | ✅ FIXED | Claim removed. | Evidence quality should be shown by provenance, not asserted. |

# 3. Executive Tab

| Item | Prior comment | 7am status | Current problem / evidence | Why change is needed | Impact of fix |
|---|---|---|---|---|---|
| E-01 | Distributed profile KPI = 14/22, 11 Native + 3 capped-100G | ✅ FIXED | Correct KPI shown. | Completeness truth. | No measured data changes. |
| E-02 | Correct 8K KV / memory | ✅ FIXED | ~0.126% KV and ~86.69 GiB retained. | Avoids memory-unit/value drift. | No impact loss. |
| E-03 | Correct TP4/PP4 128K memory | ✅ FIXED | ~88.84 GiB shown. | Avoids stale memory values. | No impact loss. |
| E-04 | Finish MiB/GiB cleanup; profiler still had `88.8GB VRAM` | ❌ NOT FIXED | `88.8GB VRAM` still appears in profiler completeness row (latest HTML L2696). | GB vs GiB is a real unit mismatch. | Label-only fix; no data removed. |
| E-05 | Soften 1M c1 causal confidence | ✅ FIXED | Executive distinguishes measured observation from MEDIUM interpretation. | Prevents E2E observation becoming unproven root cause. | Keeps measured TTFT/KV/queue impact intact. |
| E-06 | Do not impose universal strict c=1 cap without SLO | ✅ FIXED | c1 described as cleanest measured; production cap SLO-dependent. | Admission is product/SLO dependent. | Keeps concurrency cliff finding. |
| E-07 | Scale-out causal overclaim | ✅ FIXED | Decision Map uses observation + MEDIUM/CROSS-VALIDATED interpretation. | Protects strong topology data from causal overreach. | No data removed. |
| E-08 | Campaign scope/gaps explicit | ✅ FIXED | Native/100G/20G E2E vs 50G/10G HW-only is clear. | Stops extrapolation into unmeasured app regimes. | Preserves measured cap-sweep impact. |
| E-09 | Populate guidance rows | ✅ FIXED | Guidance matrix populated. | Makes measurements actionable. | Positive impact. |
| E-10 | Network sensitivity no longer unresolved | ✅ FIXED | Sensitivity surfaced. | Reflects completed campaign work. | Positive impact. |
| Exec TTFT values | Use canonical values | ✅ FIXED | Visible chart values are canonical. | Data integrity. | No impact loss. |
| Exec TTFT evidence mapping | Every point must resolve to exact evidence ID / case+bench+network | 🔴 REGRESSION / P0 | Chart queries enter a hard-coded `exactMap`; many aliases point to unrelated EV rows (Appendix A). | A correct plotted value opening the wrong raw record invalidates auditability. | Fix strengthens—not weakens—the finding. |
| Exec TPOT value | TP16/PP1 512K must be 17.413 ms | ✅ FIXED | Latest chart uses 17.413. | Numerical blocker closed. | Restores correct impact. |
| Exec TPOT evidence mapping | Exact evidence linkage | 🔴 REGRESSION / P0 | Same `exactMap` issue. | Traceability is a core V2 contract. | No data change. |
| Exec capacity | Use 784.1 tok/s c32 lineage; no 'optimal' claim | ✅ FIXED | Capacity card remains scoped. | Avoids unsupported optimization winner. | Impact preserved. |
| E-11 | Correct BabelStream labels/values | ✅ FIXED | No stale bandwidth semantics found in reviewed Executive path. | Hardware roof context remains valid. | No impact loss. |
| E-12 | Nsight/PT aggregate work != critical path | ✅ FIXED at Executive level | Executive keeps timeline attribution boundary. | Avoids invalid time accounting. | Keeps profiler corroboration. |
| E-13 | Correct TP width values | ✅ FIXED | 4.475/6.350 ms and long-context values retained. | Data integrity. | No impact loss. |
| E-14 | Do not claim chunk fairness without evidence | ✅ FIXED | Fairness/decode interaction remains unresolved. | Prevents untested benefit claim. | Chunk TTFT gain remains. |
| E-15 | `max_num_seqs` non-binding, not a universal setting | ✅ FIXED | Flat measured state is correctly scoped. | Turns knob result into a measured derivative. | Impact preserved. |
| E-16 | FP8-KV cause unsupported; guarded NOT_RUN | ✅ FIXED in Executive table | Guarded NOT_RUN wording retained. | No fake FP8 performance delta. | Honest scope. |
| E-17 | Prefix use first/repeat-hit fields | ✅ FIXED | 1M 94.23s → 2.61s repeat result retained. | Prevents mixed-mean distortion. | Impact preserved. |
| E-18 | Network sensitivity is measured | ✅ FIXED | Measured cap response shown. | Reflects actual campaign. | Positive. |
| E-19 | Correct stale 8K TPOT | ✅ FIXED | Canonical values retained. | Data integrity. | No impact loss. |
| E-20 | Remove unsupported c64 | ✅ FIXED | c1→c32 scope. | Avoids fabricated range. | No impact loss. |
| E-21 | Do not label 128K compute-bound without NCU | ✅ FIXED in main Executive cards | No 'compute bound' label in main regime row. | Causal boundary. | Observation remains. |
| E-22 | Do not label 512K 'compute & VRAM bound' | ✅ FIXED | Rephrased around measured prefill behavior. | Causal boundary. | Observation remains. |
| E-23 | Replace stale 1.45s queue | ✅ FIXED | Correct 134.43s / 107.01s queue values used. | Major numerical integrity. | Strengthens result. |
| Deployment Recipe | Remove `FLOP/pipeline dominated` and deterministic `Primary limiter` statements without NCU/timeline proof | ❌ NOT FIXED | Latest HTML L1103 still says `prefill (FLOP/pipeline dominated)` and `Primary limiter: ... Prefill: head compute / pipeline bubbles`. | These phrases elevate a hypothesis to a proven bottleneck. The rest of the dashboard correctly says NCU/timeline evidence is still needed. | Text-only correction. Keep all measurements; change to `observed regime` + `candidate mechanism / next evidence`. |
| What Not To Do | Keep measured-range guardrails | ✅ FIXED | Guardrail list remains. | Prevents over-extrapolation. | No impact loss. |

# 4. Scale-Up Tab

| ID | Prior comment | 7am status | Current problem | Why / impact |
|---|---|---|---|---|
| C1 | TTFT baseline values; crossover must be DERIVED | ✅ FIXED | Values and derived crossover are retained. | Good: measured scaling story remains strong. |
| C2 | TPOT values correct; deterministic NUMA mechanism should be qualified | 🟡 PARTIAL | Latest text still says `Single-NUMA 4-GPU ring avoids dual-NUMA bridge traversal`. | Keep the TP4<TP8 TPOT result; label mechanism CROSS-VALIDATED/contributor rather than exclusive cause. |
| C3 | TPS must use one matched lineage | ✅ FIXED | Matched baseline chart retained. | Prevents apples-to-oranges throughput. |
| C4 | Concurrency title/lineage | ✅ FIXED | Correct 8K scope/series. | No impact loss. |
| C5 | NCCL exact sizes/BusBW/PCIe; no NVLink | ✅ FIXED | No NVLink claim in reviewed chart. | Preserves hardware evidence. |
| C6 | Remove `8-GPU prefill compute FLOP scaling outweighs...` unless NCU/roofline proves it | ❌ NOT FIXED | Latest HTML L1822 still uses that exact sentence; same row also says `High single-stream compute saturation`. | The measured result is enough: TP8 lowers 512K/1M TTFT. Fixing mechanism wording makes the result harder to challenge, not weaker. |

# 5. Scale-Out Tab

| ID | Prior comment | 7am status | Deterministic result / impact |
|---|---|---|---|
| D1 | Fix TP4/PP2 KV dynamic bug | ✅ FIXED | Correct KV values are used. |
| D2 | Remove hard-coded TP4/PP4 universal winner | ✅ FIXED | Leader is workload/metric scoped. |
| D3 | Slow completed run must not be labelled failed | ✅ FIXED | TP16 capped rows remain completed/high-sensitivity. |
| D4 | Network heatmap deltas must match raw | ✅ FIXED | Measured sensitivity presentation retained. |
| D5 | Remove NVLink | ✅ FIXED | No stale NVLink claim. |
| D6 | Remove invented `27 layerwise AllReduce barriers/token` | ✅ FIXED | Phrase is absent; model metadata now says 27 layers (20 KDA, 7 full attention) without converting layer count into collective count. |
| D7 | Use neutral `NATIVE BASELINE`, separate configured vs achieved | ✅ FIXED | Latest HTML uses `NATIVE BASELINE` (L1953). |
| D8 | Replace stale 21.84 GB/s SendRecv | ✅ FIXED | Message-size-specific transport numbers retained. |
| D9 | Do not call cross-node TP16 local | ✅ FIXED | Topology identity separated. |
| D10 | Remove unstated `SLO BOTTLENECK` | ✅ FIXED | `SLO BOTTLENECK` is absent; current table uses neutral measured ordering such as highest TTFT. |

**Scale-Out closure note:** the visible Scale-Out comments from the attached audit are closed. The global Evidence click-through problem still applies to its chart points and is tracked under H4; it is not a new Scale-Out performance comment.

# 6. Long Context Tab

| Item | Prior comment | 7am status | Current check | Why / impact |
|---|---|---|---|---|
| E1 TPOT | Use extension TPOT values | ✅ FIXED | 181.97/267.41 (TP4) and corresponding TP8 values retained. | Closes mixed-lineage numerical risk. |
| E1 KV | Use correct c1/c2/c4 KV | ✅ FIXED | Values vary correctly by load. | Preserves memory context. |
| E1 TP4 c2 lineage | Use 139.37s / 44.34s, not 150.54/55.40 | ✅ FIXED in visible Long Context | Chart/table use 139.37s / 44.33s. | Major P0 numerical fix closed. |
| E1 queue narrative | Use same lineage as table | ✅ FIXED | Queue story is now consistent with extension row. | Prevents mixed legitimate runs. |
| E2 Prefix | Use first/cold and repeat-hit fields | ✅ FIXED | Prefix result remains intact. | Strong impact retained. |
| E3 long concurrency chart | Correct value + exact click provenance | 🟡 PARTIAL | Visible value is fixed to 139.37s, but click query is routed through the broken `exactMap`. | No chart value change needed; only evidence wiring. |
| E4 Scheduler | Correct 4/8/16 sweep | ✅ FIXED | Measured flat response remains. | Impact retained. |
| E5 Chunk | Correct values and no fairness claim | ✅ FIXED | Chunk TTFT curve retained. | Impact retained. |
| E6 FP8 | No quantitative FP8 comparison exists; prefer NOT_RUN status card | 🟡 PARTIAL | Latest HTML still initializes `chart_long_fp8` with `BF16 KV (Measured: 88.7 GB)` vs `FP8 KV: NOT_RUN` (L5726+). | The issue is presentation, not loss of data. A status card avoids visually implying a measured FP8 delta. |
| E7 CPU offload | NOT_RUN only | ✅ FIXED | No stale quantitative offload chart. | Honest scope. |
| E8 Long KPI | Use c1-cleanest / SLO-driven wording | ✅ FIXED | No universal cap in reviewed Long cards. | Impact retained. |
| E9 Distributed 1M matrix | Remove unstated SLO label | ✅ FIXED | Neutral measured ordering used. | No data loss. |
| E10 1M serving decision | Use one c1/c2/c4 lineage | ✅ FIXED | Visible decision uses extension values consistently. | P0 lineage issue closed. |

# 7. Scheduler & KV Tab

| ID | Prior comment | 7am status | Current problem / evidence | Why change is needed / impact |
|---|---|---|---|---|
| F1 | KV chart values correct but exact distributed mapping required | 🟡 PARTIAL | Visible data is correct; click queries use aliases affected by H4 exactMap regression. | Traceability only; keep all KV values. |
| F2 | Running/waiting must use peak semantics | ✅ FIXED | Peak labels retained. | No impact loss. |
| F3 | Queue chart must use exact extension lineage | 🟡 PARTIAL | Displayed queue values are correct; click IDs resolve incorrectly through exactMap. | Provenance fix only. |
| F4 | `Zero Memory Thrashing` is too strong; say 0 preemptions observed | ✅ FIXED | Chart label says `0 Scheduler Preemptions Observed`. | Preserves exact measurement. |
| F5 | max_num_seqs result scoped/non-binding | ✅ FIXED | Flat 4/8/16 result retained. | Good operational finding. |
| F6 numeric | Correct KV/queue/memory ledger | ✅ FIXED | Visible numbers corrected. | Data integrity. |
| F6 interpretation | Do not assert exact allocator mechanism / unstated SLOs | 🟡 PARTIAL | SLO-compliant labels are gone, but L2148 still says `4-way pipeline stage KV distribution`; takeaway says PP `divides` active KV allocation across 4 stages. | Observed PP×KV pattern supports `consistent with distribution`; exact allocator sharding is not measured. Wording-only change; KV data stays. |
| F7 8K open-loop | Knee must have explicit criterion | 🟡 PARTIAL | Card still labels a derived 0.90x `Capacity Knee` without defining the rule that makes 0.90x the knee. | Keep all sweep data; define the heuristic (e.g., queue/TPOT slope or explicit SLO) or call it `candidate knee`. |
| F8 128K open-loop | Correct canonical data | ✅ FIXED | Cliff data retained. | Impact preserved. |
| F9 admission card | No `SLO-safe` without SLO; correct c2; define knee criterion | 🟡 PARTIAL | Wrong c2 is fixed and SLO-safe label removed, but 128K 0.75x is still prescribed as throttle point without an explicit selection rule; 8K c≤8 likewise depends on target TPOT. | This is a decision-rule transparency issue, not a request to delete the capacity findings. |

# 8. Profiler Tab

| ID | Prior comment | 7am status | Current problem / evidence | Why / impact |
|---|---|---|---|---|
| G1 identity | Blackwell identity | ✅ FIXED | Correct hardware identity shown. | Reproducibility. |
| G1 completeness | 14/22, 11 Native + 3 capped | ✅ FIXED | Correct denominator retained. | Completeness truth. |
| G2 single-node values | Single-node kernel shares are real | ✅ FIXED / VALID | TP4/TP8 rank-0 aggregate work is still shown. | Strong evidence retained. |
| G2 semantics | Use aggregate GPU kernel work, not decode wall time | ✅ FIXED | Latest visible text says aggregate GPU kernel work. | Correct denominator semantics. |
| G2 distributed aggregation | Distributed topology percentages need one exact rank or reproducible median/range | ❌ NOT FIXED | Chart still plots TP16 76.2% while label mentions multi-rank mean 77.6%; TP4/PP4 uses 40.0/8.3 selected-stage values without a topology-wide aggregation rule. | This is not dilution: keep the raw selected-rank/stage values, but label them as such OR render median+range. It prevents one rank being presented as topology-wide behavior. |
| G3 PT operators | Document grouping recipe for selected operator groups | 🟡 PARTIAL | Chart honestly says `Sum of Selected Operator Groups`, but grouping definitions remain absent. | Reproducibility of the non-AllReduce bars. AllReduce 251.5/583.9ms result remains strong. |
| G4 CUDA API | Use `aggregate host API time`, not wall-clock when calls can overlap | 🟡 PARTIAL | Visible card subtitle says aggregate host API time, but Chart.js label/axis still says `Host API Wall-Clock Time` (L5974–L5988). | Text/denominator fix only; values 3.638/3.466/... stay. |
| G5 kernel latency | Remove roofline/100%-empirical overclaim; provide rank provenance | 🟡 PARTIAL | `KERNEL ROOFLINE` and `100% empirical evidence` are gone. Exact provenance for every P2P/kernel series is still not fully surfaced. | Preserve durations; improve traceability. |
| G6 title | Resource pressure != exclusive critical path | ✅ FIXED | Ledger title/subtitle correctly states resource pressure / aggregate work. | Strong semantic fix. |
| G6 content | Remove FLOP-bound, memory-bound, single-greatest, CUDA Graph as established fix | ✅ LARGELY FIXED | Disallowed phrases are absent; CUDA Graph is now a `candidate follow-up optimization to test`. | Keeps diagnostic value without fake causal proof. |
| G7 Top-15 | Add profile/phase/topology identity | ✅ FIXED structurally | Identity columns retained. | Reproducibility. |
| G8 matrix structure | 22 rows / correct status accounting | ✅ FIXED | Completeness structure retained. | No impact loss. |
| G8 narrative | Remove invented 27 barriers/token / avoids stalls | ✅ FIXED | Those exact claims are absent. | Prevents model-layer count being misused as collective count. |
| G9 61 layers | Remove contamination | ✅ FIXED | Current model metadata is 27 layers / 20 KDA / 7 attention. | Model integrity. |
| G10 root-cause table | Soften causal/prescriptive claims | 🟡 PARTIAL | Profiler still uses phrases such as `Multi-Node Stalling`, `barriers`, `Why TP4 beats TP8`, and `Pin TP4...` as stronger recommendations than the aggregate-work evidence alone establishes. | Keep all profiler numbers; change labels to `observed composition` / `cross-validated contributor` / workload-scoped candidate. |

# 9. Evidence Tab — P0 Closure Blocker

The prior H4 requirement was exact datum-level identity: `evidence_id` or exact `case + bench + network_provenance`, with separate profile-artifact identity for profiler-only evidence.

| ID | Prior comment | 7am status | Deterministic check | Why / impact |
|---|---|---|---|---|
| H1 | Status contract | ✅ FIXED | Primary/auxiliary/guarded states are represented. | Scope truth. |
| H2 | Scope filter | ✅ FIXED | Scope labels align with rendered rows. | No impact loss. |
| H3 | p95/p99 reliability gating | ✅ FIXED | Reliability flags remain separate. | Prevents low-N percentile overclaim. |
| H4 | Exact chart→Evidence mapping | 🔴 REGRESSION / P0 | `exactMap` has 26 case-specific aliases checked; only 1 maps to the canonical registry row implied by its label. | A correct chart point can open the wrong case. This directly defeats the evidence-backed claim of the dashboard. |
| H5 | Claim registry must not reintroduce unsupported mechanism/SLO/mixed lineage | 🟡 PARTIAL | Major c2/SLO regressions are improved, but some causal phrasing remains stronger than supporting evidence. | Messaging/provenance cleanup only; do not delete findings. |
| H6 | Runtime acceptance contract | ✅ FIXED | Network scope contract corrected. | No impact loss. |
| H7 | Use current network coverage source | ✅ FIXED | Current coverage source retained. | No impact loss. |

## 9.1 Why the `exactMap` issue is not a hallucinated review comment

This is a direct machine comparison between two objects inside the **same 7am HTML**:

- `exactMap`: query alias → EV ID
- `CANONICAL_DASHBOARD_DATA.evidence_registry`: EV ID → actual case/bench/network

Examples:

| Query alias in current `exactMap` | Current EV target | What that EV actually is | Canonical EV for the alias |
|---|---:|---|---:|
| `tp4_context_baseline 8k` | `EV-001` | `tp4_qualification` / `8k_c1` / `SINGLE_NODE_LOCAL` | `EV-009` |
| `tp4_context_baseline 128k` | `EV-007` | `tp8_qualification` / `128k_c1` / `SINGLE_NODE_LOCAL` | `EV-010` |
| `tp4_context_baseline 1m` | `EV-009` | `tp4_context_baseline` / `8k_c1` / `SINGLE_NODE_LOCAL` | `EV-012` |
| `tp4_pp4_dist 128k` | `EV-070` | `tp8_1m_concurrency_extension` / `1m_c4` / `SINGLE_NODE_LOCAL` | `EV-082` |
| `tp4_pp4_dist 1m` | `EV-072` | `tp4_1m_maxseq8` / `1m_c4` / `SINGLE_NODE_LOCAL` | `EV-084` |
| `tp16_pp1_dist 128k` | `EV-076` | `tp4_pp2_dist` / `128k_c1` / `GCP_NATIVE` | `EV-085` |
| `tp16_pp1_dist 512k` | `EV-086` | `tp16_pp1_dist` / `512k_c1` / `GCP_NATIVE` | `EV-086` |
| `tp4_1m_concurrency_extension 1m_c2` | `EV-013` | `tp8_context_baseline` / `8k_c1` / `SINGLE_NODE_LOCAL` | `EV-066` |
| `tp8_1m_concurrency_extension 1m_c4` | `EV-028` | `tp4_chunk8k` / `128k_c1` / `SINGLE_NODE_LOCAL` | `EV-070` |

**Required fix:** do not maintain a hand-written alias→EV-number table. Bind the canonical `evidence_id` to each chart datum at data-generation time. Generic profiler queries such as `tp4_prefill`, `tp4_decode`, `tp8_decode` should resolve to profile-artifact IDs, not ordinary E2E benchmark EV rows.

# 10. Cross-Cutting / Data Contract

| ID | Prior comment | 7am status | Current check | Why / impact |
|---|---|---|---|---|
| I1 | Remove manually maintained performance arrays; canonical data must drive UI | ❌ NOT FIXED | The file contains 26 `safeInitChart(...)` chart initializations and dozens of literal numeric `data: [...]` arrays. | This is the structural reason visible data, discovery objects and evidence IDs can drift. Fixing it reduces future regressions without changing current results. |
| I2 | Decorative selectors should be functional or rendered as scope labels | 🟡 MOSTLY FIXED | Scale-Out controls are functional; other tabs mostly use scope labels; profiler filters do not drive every chart. | Usability/consistency, not data impact. |
| I3 | Do not mark slow completed runs failed | ✅ FIXED | No reviewed slow completed row uses failure semantics. | Preserves valid data. |
| I4 | Bind model metadata/formulas to one manifest-backed object | 🟡 PARTIAL | Correct 27/20/7 metadata appears, but architecture/formula strings are still repeated/hard-coded in UI/discovery text. | Reduces future K3/Kimi-Linear or formula drift; no need to remove the architecture finding. |

# 11. Key Finds / Top 10 — Impact-Preserving Review

## Important answer to the team's concern

**No, the remaining Top-10 feedback is not all text/messaging.** It splits into two classes:

- **Messaging / causal-boundary only:** keep the data exactly as-is; soften or reclassify only the unsupported sentence.
- **Provenance / derived-object integrity:** the visible number may be right, but the evidence IDs, raw-profile linkage, or derived arithmetic is wrong/incomplete. These must be fixed because they directly affect auditability.

The table below explicitly states whether a change touches measured data.

| Top | 7am status | Type of remaining comment | Current problem | Why change is justified | Impact-preserving fix | Does measured data change? |
|---:|---|---|---|---|---|---|
| 1 | 🟡 PARTIAL | Messaging + profile provenance | Visible card correctly says MEASURED+DERIVED and MEDIUM causal confidence, but still prescribes `Prioritize FlashAttention & chunk budget for ≥512K; prioritize MoE routing and GEMMs for ≤128K`. Backing raw paths name a 128K profile summary but do not expose an equally explicit 512K profile artifact/ID for the matched scaling calculation. | The measured evidence establishes relative aggregate-work growth; it does not contain an intervention/A-B test proving those optimization priorities. | Keep the full 15.7×/3.9×/3.8× table and exponents. Replace the prescription with `candidate optimization focus to validate`. Add explicit 128K+512K profile artifact IDs/paths. | NO |
| 2 | 🟡 PARTIAL (minor) | Object/text consistency | Visible card is now well scoped and no longer bans TP16 or standardizes TP4/PP4. But backing `formula_derivation` still labels the normalized quantity as `≈116 bytes/token` while the card/boundary correctly calls it hidden-width-equivalent exposure. | The dimensionless/normalized coefficient should not look like literal transferred bytes. This is already acknowledged by the visible boundary. | Keep all network/TTFT data and fit. Make formula wording match the visible `hidden-width-equivalent exposure coefficient`. | NO |
| 3 | ✅ FIXED | Data lineage + messaging | The extension c1/c2/c4 values, queue closure, causal split, and evidence IDs EV-065..070 are now consistent. | This was the previous P0 mixed-lineage problem and is now closed. | No change required. | NO |
| 4 | 🟡 PARTIAL | Messaging only | All prefix numbers and mechanism wording are strong. The card still says `Route multi-turn chat and RAG to cache-warm replicas with sticky sessions`. | Sticky routing/cache-warm replica architecture was not directly tested; the card's own boundary says production value depends on residency/eviction/workload mix. | Keep the 14.8×/27.9×/36× speedups. Move sticky-session routing to `candidate deployment experiment` / follow-up. | NO |
| 5 | ❌ NOT FIXED | Messaging + provenance | Visible text says RPS `diverges by 18.2× due to prompt length discrepancy` although prompt length differs 16×; `~14% spread confirms prompt-token saturation`; WHY says saturation is fundamentally governed by token compute. More importantly, discovery drilldown/input IDs are EV-058/059/060/074/075/076, which are unrelated offload/FP8/prefix/scale-out rows, not the high-load open-loop points. | V2 explicitly defines this as a two-context empirical fingerprint with LOW-MED causal confidence and says to derive it from 1.00×/1.10×/1.25× high-load points. | Keep ~27.5K vs ~24.2K result. Say `18.2× lower accepted RPS while prompt length is 16× larger`; change `confirms` to `yields a tighter measured band`. Bind source IDs to 8K EV-116/117/118 and 128K EV-123/124/125 or a first-class derived record containing those six IDs. | NO measured values; YES provenance |
| 6 | ❌ NOT FIXED | Causal wording + provenance | Visible WHY still says short prompts are `memory-bandwidth ... bound` and long prompts `compute-heavy`. Discovery input/drilldown IDs contain stale/mismatched EV rows rather than the canonical context baselines and Native PP rows. | Elasticity measures scaling direction; it does not prove roofline class. V2 explicitly set causal confidence MEDIUM. | Keep every elasticity and GPU-s value. Use `measured TP return changes sign with context; exact compute/communication balance unresolved`. Bind TP baseline to EV-009..016; PP Native to EV-076..084; add EV-079..081 and EV-085..087 where GPU-s frontier points use them. | NO measured values; YES provenance |
| 7 | ❌ NOT FIXED | Causal/prescriptive wording + profiler provenance | The 4-layer numerical chain is excellent, but card still says `doubling synchronization barrier overhead` and `Enforce TP=4; avoid TP=8`. Backing drilldown has only EV-001/EV-005 (E2E qualification rows), not first-class NCCL/PT/Nsight artifact IDs. | The chain supports wider-TP synchronization as a contributor. It does not prove a universal policy or exclusive critical-path fraction. V2 explicitly requires each layer to drill to exact raw artifacts. | Keep 19→37µs, 251.5→583.9ms, same 7040 calls, and +41.9% TPOT. Use workload-scoped decision wording. Use E2E baseline EV-009/EV-013 plus separate profile/NCCL artifact IDs. | NO measured values; YES provenance |
| 8 | 🟡 PARTIAL | Provenance only (visible message mostly fixed) | Visible mechanism is now properly scoped. But backing drilldown/input IDs EV-052/053/054/046/047/048 do not represent the 1M max_num_seqs 4/8/16 plus 1M chunk 4K/8K/16K comparison. | A derivative card is only reproducible if its matched A/B source rows are exact. | Keep all numbers. Use maxseq EV-071/072/073 and 1M chunk EV-027/031/035 (or include all context-matched chunk rows if the drawer shows them). | NO measured values; YES provenance |
| 9 | 🟡 PARTIAL | Backing-object semantics | Visible card is now well scoped: MEDIUM causal, no absolute autoscaling prohibition. Backing object still defines an `Effective compute efficiency` formula not required by V2 and not directly measured as useful work. | The insight only needs measured utilization + TTFT and the semantic point that communication kernels count as activity. | Keep 80.6%/68.2s vs 62.8%/28.57s. Remove or clearly label the efficiency formula as a heuristic if retained. | NO |
| 10 | 🟡 PARTIAL | Backing-object arithmetic/provenance | Visible card is corrected and no longer shows derived headroom. Backing object still says `Actual Physical VRAM Headroom = 7.86 GiB` while its own formula says `96.00 - 88.83 = 7.17 GiB`; it also calls `PP×KV%` a `True Total Model KV Footprint`. Drilldown omits TP16 although visible table includes it. | These are internal inconsistencies, not stylistic opinions. The core discovery only needs KV% vs measured GPU memory. | Keep 12.29/5.91/2.75% and 88.39/88.69/88.83 GiB. Remove derived headroom until total capacity/unit source is normalized; say PP×KV is `consistency check`, not true footprint; include EV-087 if TP16 remains in table. | NO core measured values; YES backing derivation |

## 11.1 Top-10 impact protection — what must **not** be lost

The following high-impact results should remain exactly visible after cleanup:

- **Fabric:** TP16/PP1 +276.7% vs TP4/PP4 +3.91% TTFT under configured-20G vs Native at 1M.
- **Concurrency:** TP4 1M c1→c4 = +1.52% output TPS, 2.48× TTFT, 26.15× TPOT, ~134.43s queue, 0 preemptions.
- **Resource-pressure scaling:** ~15.7× attention vs ~3.9× KDA / ~3.8× MoE between matched 128K and 512K profiles, with aggregate-work boundary.
- **Prefix reuse:** 14.8× / 27.9× / 36.0× repeat-hit TTFT improvement for the measured prefix cases.
- **Prompt-token normalization:** ~27.5K vs ~24.2K input tok/s for measured 8K/128K high-load regions.
- **Elasticity / GPU-s:** retain η and all measured GPU-s/request proxy values.
- **TP decode chain:** retain NCCL → PT Profiler → Nsight → E2E numeric chain.
- **Runtime knobs:** retain <0.05% max_num_seqs spread vs ~27.1% chunk-budget TTFT improvement.
- **GPU-utilization caution:** retain utilization/TTFT comparison.
- **KV vs VRAM:** retain measured KV% and peak GPU-memory telemetry side-by-side.

> The cleanup should make these findings **more credible**, not less impactful.

# 12. Appendix A — Deterministic `exactMap` Reconciliation

This table is generated by parsing the 7am HTML, not by manual interpretation.

| Alias | Current target | Current target actually represents | Expected canonical target | Status |
|---|---:|---|---:|---|
| `tp4_context_baseline 8k` | `EV-001` | `tp4_qualification` / `8k_c1` / `SINGLE_NODE_LOCAL` | `EV-009` | ❌ |
| `tp4_context_baseline 128k` | `EV-007` | `tp8_qualification` / `128k_c1` / `SINGLE_NODE_LOCAL` | `EV-010` | ❌ |
| `tp4_context_baseline 512k` | `EV-008` | `tp8_qualification` / `512k_c1` / `SINGLE_NODE_LOCAL` | `EV-011` | ❌ |
| `tp4_context_baseline 1m` | `EV-009` | `tp4_context_baseline` / `8k_c1` / `SINGLE_NODE_LOCAL` | `EV-012` | ❌ |
| `tp8_context_baseline 8k` | `EV-015` | `tp8_context_baseline` / `512k_c1` / `SINGLE_NODE_LOCAL` | `EV-013` | ❌ |
| `tp8_context_baseline 128k` | `EV-021` | `tp4_decode_focus` / `8k_decode_c1` / `SINGLE_NODE_LOCAL` | `EV-014` | ❌ |
| `tp8_context_baseline 512k` | `EV-022` | `tp4_decode_focus` / `8k_decode_c8` / `SINGLE_NODE_LOCAL` | `EV-015` | ❌ |
| `tp8_context_baseline 1m` | `EV-023` | `tp4_decode_focus` / `8k_decode_c16` / `SINGLE_NODE_LOCAL` | `EV-016` | ❌ |
| `tp4_pp4_dist 128k` | `EV-070` | `tp8_1m_concurrency_extension` / `1m_c4` / `SINGLE_NODE_LOCAL` | `EV-082` | ❌ |
| `tp4_pp4_dist 512k` | `EV-071` | `tp4_1m_maxseq4` / `1m_c4` / `SINGLE_NODE_LOCAL` | `EV-083` | ❌ |
| `tp4_pp4_dist 1m` | `EV-072` | `tp4_1m_maxseq8` / `1m_c4` / `SINGLE_NODE_LOCAL` | `EV-084` | ❌ |
| `tp16_pp1_dist 128k` | `EV-076` | `tp4_pp2_dist` / `128k_c1` / `GCP_NATIVE` | `EV-085` | ❌ |
| `tp16_pp1_dist 512k` | `EV-086` | `tp16_pp1_dist` / `512k_c1` / `GCP_NATIVE` | `EV-086` | ✅ |
| `tp16_pp1_dist 1m` | `EV-078` | `tp4_pp2_dist` / `1m_c1` / `GCP_NATIVE` | `EV-087` | ❌ |
| `tp4_pp2_dist 128k` | `EV-067` | `tp4_1m_concurrency_extension` / `1m_c4` / `SINGLE_NODE_LOCAL` | `EV-076` | ❌ |
| `tp4_pp2_dist 512k` | `EV-068` | `tp8_1m_concurrency_extension` / `1m_c1` / `SINGLE_NODE_LOCAL` | `EV-077` | ❌ |
| `tp4_pp2_dist 1m` | `EV-069` | `tp8_1m_concurrency_extension` / `1m_c2` / `SINGLE_NODE_LOCAL` | `EV-078` | ❌ |
| `tp8_pp2_dist 128k` | `EV-073` | `tp4_1m_maxseq16` / `1m_c4` / `SINGLE_NODE_LOCAL` | `EV-079` | ❌ |
| `tp8_pp2_dist 512k` | `EV-074` | `tp4_fp8_kv_1m` / `1m_c1` / `SINGLE_NODE_LOCAL` | `EV-080` | ❌ |
| `tp8_pp2_dist 1m` | `EV-075` | `tp4_prefix1m` / `prefix1m` / `SINGLE_NODE_LOCAL` | `EV-081` | ❌ |
| `tp4_1m_concurrency_extension 1m_c1` | `EV-012` | `tp4_context_baseline` / `1m_c1` / `SINGLE_NODE_LOCAL` | `EV-065` | ❌ |
| `tp4_1m_concurrency_extension 1m_c2` | `EV-013` | `tp8_context_baseline` / `8k_c1` / `SINGLE_NODE_LOCAL` | `EV-066` | ❌ |
| `tp4_1m_concurrency_extension 1m_c4` | `EV-014` | `tp8_context_baseline` / `128k_c1` / `SINGLE_NODE_LOCAL` | `EV-067` | ❌ |
| `tp8_1m_concurrency_extension 1m_c1` | `EV-026` | `tp4_chunk4k` / `512k_c1` / `SINGLE_NODE_LOCAL` | `EV-068` | ❌ |
| `tp8_1m_concurrency_extension 1m_c2` | `EV-027` | `tp4_chunk4k` / `1m_c1` / `SINGLE_NODE_LOCAL` | `EV-069` | ❌ |
| `tp8_1m_concurrency_extension 1m_c4` | `EV-028` | `tp4_chunk8k` / `128k_c1` / `SINGLE_NODE_LOCAL` | `EV-070` | ❌ |

Generic aliases `tp4_prefill`, `tp4_decode`, `tp8_decode`, `tp16_pp1_dist`, `tp4_pp4_dist` should not be repaired by pointing them to arbitrary E2E EV rows. Profiler-only evidence needs its own `profile_id / node / rank / phase / raw artifact` identity.

# 13. Final Team Fix List

## P0 — must close before claiming deterministic evidence drill-down

1. **Delete or regenerate the hard-coded `exactMap` from the canonical registry.** Prefer carrying `evidence_id` directly on every chart datum.
2. **Repair Top #5 / #6 / #7 / #8 evidence inputs** as specified above; Top #7 requires first-class profiler/NCCL artifact identities.
3. **Re-run an automated chart-point → expected case/bench/network test** after the fix. The acceptance criterion should be 100% match for all E2E chart datums.

## P1 — semantic/provenance cleanup that preserves impact

1. Executive Deployment Recipe: remove FLOP/pipeline-bound and deterministic primary-limiter wording.
2. Scale-Up C2/C6: keep measured TP4/TP8 result; reclassify mechanism as cross-validated/contributor pending NCU/timeline.
3. Scheduler: define the knee criterion or label it candidate/heuristic; change exact PP/KV sharding language to `consistent with`.
4. Profiler: distributed composition must be exact rank or median+range; document PT operator grouping; use aggregate host API time consistently.
5. Top #1/#4/#9/#10: make visible card and backing discovery object say the same thing.
6. Top #10: remove inconsistent derived VRAM headroom until device capacity/unit basis is explicit.

## P2 — architecture hardening

1. Replace manually maintained chart arrays with generated canonical chart data.
2. Generate discovery objects, chart datums, confidence, and evidence links from one source.
3. Add CI assertions: every chart datum's `evidence_id` must resolve to the same case/bench/network carried by the datum.
4. Add profiler artifact registry separate from E2E evidence registry.

# 14. Final Sign-Off Assessment

### What is genuinely closed and should not be reopened without new evidence

- Campaign scope / hardware identity / completion accounting
- TP4 1M c2 mixed-lineage P0 in visible Long/Key-Finds data
- TP16 512K TPOT value regression
- Scale-Out D1–D10 comments from the attached audit
- Prefix first/repeat values
- max_num_seqs measured non-binding result
- removal of 27-barriers/token, SLO BOTTLENECK, Zero Memory Thrashing, KERNEL ROOFLINE, and 100%-empirical wording

### What still blocks full data/evidence sign-off

- Wrong deterministic evidence-ID mapping (`exactMap`)
- Several Top-10 discovery input/drilldown IDs do not correspond to the measurements used in the visible discovery
- Distributed profiler composition lacks one reproducible topology-level aggregation rule
- Remaining causal/prescriptive statements that are stronger than the evidence contract
- Manually duplicated chart arrays / discovery data create drift risk

### Bottom line

**Do not dilute the Top-10 measured findings.** The remaining work is mostly about making the evidence chain and causal boundary as strong as the measurements already are. The only comments that should alter numbers are objective corrections to provenance/derived arithmetic; none of the remaining messaging comments require deleting a valid measured result.

For the next review, the team should treat this document as a **frozen closure checklist**. A future reviewer should not add new stylistic or optimization comments into the closure score unless a new objective data/provenance regression is found. New ideas should go into a separate `Future Improvements / Experiments` list.
