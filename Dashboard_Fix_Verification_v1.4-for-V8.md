# Dashboard fix verification — 5 Oct build checked against verification v1.2

*v1.4 (6 Oct 2026). v1.3 re-audited claim by claim against the build's HTML and code and against the archive; §8 lists what changed. The check itself: the 5 Oct 4am build against every item in `Dashboard_Fix_Verification_v1.2.md` — §1 (28 fix-list items), §2 (24 tab items), §3 (five contradictions), §5 (short list), §6 (layout additions and scope labels) and §7 (time-budget charts) — tab by tab, section by section and chart by chart, and records what the build newly gets wrong. v1.2 and v1.3 are kept as they were; §6 below corrects six things v1.2 itself got wrong.*

**Build checked:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_5thOct_4amIST_V8_KIMI48B.html` (1.16 MB), compared with the 4 Oct 2am build v1.2 was written against.
**How it was checked:** rendered in headless Chromium with Chart.js 4.5.1 beside the file (the page loads `chart.umd.js` and falls back to the CDN). Every tab clicked; every canvas read through `Chart.getChart` (labels, data, axes); all ten Key Discoveries explorer pages opened with their charts and their "Inspect Evidence" pop-ups; all seven profiler drawers (PR-001…PR-007) opened; all 21 Scale-Out selector states (3 networks × 7 metrics) rendered; the four new time-budget views toggled. Page text diffed against the 4 Oct build tab by tab; `KD_PAGES_DATA`, `PROFILER_REGISTRY` and the three discovery maps diffed field by field. Every number the build adds or changes was recomputed from the archive: `combined_vllm_runs.csv`, the per-rank `cuda_gpu_kern_sum.csv` exports, the case manifests, `logs/readiness_node*/V8_READINESS.json`, `FINAL_VALIDATION.json`, `V8_FULL_RELEASE.json`, the nvbandwidth and nccl-tests raw files, and the time-budget CSVs.
**Console:** no script errors. Four failed resource loads — the four time-budget PNGs (§2.8).
**Screenshots** (in `v13_evidence/`): the Evidence readiness panel above the misaligned ledger, the Profiler time-budget panel as shipped, and the Scale-Out heatmap labels.
**Audit of this document:** every quotation below was matched verbatim, by script, against its source: for the dashboard, the HTML, the rendered text of each tab, the ten Key Discoveries pages and the seven drawers; otherwise v1.2, the master review v1.2 or the pilot code. 155 scripted checks re-ran the numeric and structural claims against the HTML, the dashboard code and the archive; all pass. Two behaviours were checked by clicking in the browser: the composition-chart bars and the KD "Inspect Evidence" buttons. One figure comes from an earlier review and was not recomputed here; it is marked where it is used (the TP8 decode split in N10).

## 0. Verdict

The short list from v1.2 mostly landed where it was aimed. One TP8 ratio (3.10×) now runs through the hero, the narrative, the definitions box and the discovery maps. The NUMA cause is rewritten on the Executive, Scale-Up, Key Finds, Profiler and Evidence tabs and in the drawer. The deployment rule, the claim registry and PR-002/003 no longer argue from the eager decode capture (PR-002/003 now put an "eager" label on a number that is not eager — N21). "~0.1ms RTT" no longer appears anywhere. The regime-map 8K row, the K3 pool-in-tokens sentence, the knee label, the six-layout composition table, the PP2 check, the KD#7 cross-node pointer and the scope labels on the two loaded panels are all in. The Profiler tab has the four-view time-budget panel in the right place, with both findings, and nothing was removed to make room.

Three things keep this build from being shared:

1. **The Evidence tab now states things the archive contradicts.** The new readiness panel lists a software stack the cluster did not run: vLLM 0.6.2, PyTorch 2.4, CUDA 12.4, driver 550, NCCL 2.20 "AWS-OFI". The archive and the same tab's own audit matrix say vLLM 0.29.0, PyTorch 2.13.0, NCCL 2.29.7, driver 580.173.02 and CUDA 13.0. The panel also gives an invented validator defect and invented reasons for the 7 NOT_RUN runs and the 5 missing profiles. Of the ledger's two new columns, one holds a single constant ("w=1 · 32 req") that is wrong on all 23 rows it appears on, and the other is empty. No row lines up with the 16 headers any more — the 23 rows with a value are one cell short, the other 103 two — and a fragment of HTML prints above the table.
2. **The four time-budget charts do not show.** They are `<img>` links to PNG files that are not inside the HTML, so in the file as shared they are broken images.
3. **Part of the Key Discoveries work never reaches the screen.**
   * Three fixes went into `confidence_note` / `scope_note` fields that the page renderer never reads: KD#2's scope note, KD#6's corrected confidence line and KD#9's telemetry source. So KD#6 still shows "6 scale-out topologies at 1M" and KD#9 still shows "Prometheus GPU SM utilization telemetry".
   * The Key Finds tab was hidden in the 4 Oct build and is a visible tab now. It still carries the old text for seven of the ten findings.

The fixes also brought in new wrong statements:

* "Stages 1–3 wait 17–22 %" — only stage 3 does.
* KD#6's energy line uses TP16's 128K number as its 1M number and labels TP8/PP2's row as TP4/PP2, which reverses the comparison.
* KD#1 says "PP point-to-point boundaries operate without penalty down to 20G cap", but TP4/PP4 is +14.7 % at 128K.
* The PP2 check credits the 0.75 ratio to "the 6 vs 8 full-attention layer distribution"; the split is 3 vs 4 of 7.
* The heatmap prints a rule that its own cells break.

**Status counts.**

| List | Closed | Partly | Open | Regressed |
|---|---|---|---|---|
| v1.2 §1 fix list (28) | 24 | 2 (items 3, 15) | 0 | 2 (items 10, 24) |
| v1.2 §2 tab items (24) | 13 | 9 | 1 | 1 |
| v1.2 §3 contradictions (5) | 4 | 0 | 1 (KD#3, now inside one page) | 0 |

Beyond the v1.2 lists:

* 22 new errors in this build (N1–N22, §4).
* 17 older defects found in the deeper passes (P1–P17, §5).
* 6 corrections to v1.2 itself (C1–C6, §6).

"Closed" means the ask is visible where v1.2 asked for it; errors the fix itself introduced are counted separately in §4.

## 1. What blocks sharing this build — fix these first

| # | Problem | Where | Fix (archive value) |
|---|---|---|---|
| B1 | **Software stack invented.** The panel shows vLLM 0.6.2 · PyTorch 2.4.0+cu124 · CUDA 12.4 (driver 550.54.15) · NCCL 2.20.5 "AWS-OFI-NCCL / GCP VPC tuned" · Ray 2.37.0, badged "AUDIT VERIFIED". | Evidence → Cluster, Stack & Campaign Readiness Audit | `V8_READINESS.json` (both nodes), actual versions: vLLM 0.29.0 · Ray 2.58.0 · PyTorch 2.13.0 · Triton 3.7.1 · FlashInfer 0.6.18 · nvidia-nccl-cu13 2.29.7. Driver 580.173.02 and CUDA 13.0 come from the nvbandwidth headers (`CUDA Runtime Version 13000`), and the same tab's Reviewer Audit matrix already shows them. Transport: `NCCL_NET=Socket` on ens3, GCP NCCL net plugin disabled (`libnccl-net.so → /dev/null`). There is no AWS-OFI plugin. |
| B2 | **Validator defect 2 invented.** The panel lists "FINAL_VALIDATION Duplicate Keys … reconciled against raw JSON logs". | same panel | The real second defect: `FINAL_VALIDATION.json` was computed off the cluster (`result_root: C:\Users\…\v8_full_results\20260921_195656`). Its `ray_nccl_scaleout_audits: 0` sits beside 12 audit files that pass. |
| B3 | **NOT_RUN and NOT_CAPTURED reasons invented.** Wordings: "7 runs marked GUARDED_NOT_RUN (safety-gated configurations not executed)"; "workload horizons where per-worker nsys daemon was skipped"; "7 Safety-Guarded NOT_RUN" in the global banner; "Excluded from execution scope" on the offload card; "FP8 KV-cache was not executed". | Evidence panel; global header banner (every tab); Scheduler offload card; Long Context FP8 card | The 7 runs were attempted. Each case manifest records `error: RuntimeError('server exited rc=1')`: the server stopped 126 s (offload), 132 s (FP8) and 134 s (FP8 1M) after start, and no server log was kept. `FINAL_VALIDATION`: `safety_skipped_count 0`; `coverage.json` gives the 7 entries `has_gate: false` and no `gate_reason`. Say "attempted; server failed to start (rc=1); cause not logged". For the 5 missing profiles no reason is recorded (§2.8). |
| B4 | **Ledger columns wrong and misaligned.** "Warmup / Prompts" appears on 23 of 126 rows, always "w=1 · 32 req", and is wrong on all 23. Examples: tp4_qualification 8k_c1 is 2 warm-ups · 12 prompts; 512k_c1 is 0 · 2; the seven 128K open-loop rows are 0 · 24. "Cold Load" has a header and no cells. The 23 rows with a value have 15 cells and the other 103 have 14, under 16 headers. On the 15-cell rows the reliability badges sit under Cold Load, TTFT under Sample Reliability and the artifact path under KV/Queue; on the 14-cell rows the network badge sits under Warmup / Prompts and every later cell moves one or two columns left. The text `id="perf-evidence-table-container">` prints on screen because the readiness panel was pasted over the ledger card's opening tag. | Evidence → Comprehensive Audited Evidence Ledger | Restore `<div class="card mb8" id="perf-evidence-table-container">`. Fill Warmup/Prompts on all 126 rows from `warmups` / `prompts_requested` (0/1/2 warm-ups on 77/26/16 runs; 1–318 prompts). Fill Cold Load from the start-up table or drop the column. Emit one `<td>` per header. |
| B5 | **Time-budget charts are broken images.** `<img src="wall_time_budget_*.png">` with no image in the file; the CSV links point at `time_budget/…` while the images point at the HTML's own folder. | Profiler → End-to-End Wall-Time Budget | Embed the four PNGs as data URIs (2.0 MB of PNG, about 2.7 MB as base64), or better, draw them with Chart.js from the four CSVs inlined as JSON, so they match the dark theme and get tooltips like every other chart. |
| B6 | **Key Discoveries fixes the reader cannot see.** `renderFindingHtmlClient` reads `confidence.notes` and `scope.*`, never `confidence_note` or `scope_note`. Ten `confidence_note` fields (one per page) and four `scope_note` fields (KD#2, #4, #5, #8) are dead data. Most repeat something the page already shows: KD#3's takeaway says "nsys only, eager mode", and KD#4 and KD#8 say single-node in their boundary lines. Three were meant to add or replace visible text and so change nothing on screen: KD#2's scope note ("Distributed layouts (TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1) were run at c=1 only; concurrency not yet measured"), KD#6's confidence line ("HIGH across the 4 scale-out + 2 scale-up topologies evaluated at 1M") and KD#9's telemetry source ("Telemetry sourced from nvidia-smi background sampler"). So KD#6 still shows "6 scale-out topologies at 1M" and KD#9 still shows "Prometheus GPU SM utilization telemetry". | Key Discoveries explorer pages | Render the two fields, or move their text into `confidence.notes` and the scope rail. Then remove the old sentences they were meant to replace. |
| B7 | **Key Finds tab exposed with old text.** The 4 Oct build had the Key Finds button commented out; the 5 Oct build shows it. TOP 2/3/4/5/8/9/10 still have the pre-fix text, e.g. TOP 10 "Causal: LOW-MED … does not establish the allocator's exact sharding rule" against KD#10's HIGH. | Key Finds tab | Port the KD explorer fixes card by card (§2.2), or hide the tab again until they are ported. |
| B8 | **Four new wrong statements.** | Profiler, KD#6, KD#1, Scale-Out | N5, N6, N7, N8 in §4. |

## 2. Tab by tab

Status: **CLOSED** · **PARTLY** · **OPEN** · **REGRESSED** · **NEW ERROR** (introduced by this build) · **OLD DEFECT** (present before 5 Oct, found in this pass). "On screen" says whether the change actually reaches the reader.

### 2.0 Global header and navigation

| Section | Ref | Status | On screen | Evidence / what remains |
|---|---|---|---|---|
| Tab bar | — | changed | yes | Key Finds tab button is now live (it was commented out on 4 Oct). See §2.2: the tab brings its old text with it. |
| Campaign banner | C2 | OLD DEFECT | yes | "7 Safety-Guarded NOT_RUN" on every tab. No safety gate exists in the archive (B3). |
| Fabric line | v1.2 §2 Executive | CLOSED | yes | "173.58 Gb/s fwd / 173.59 rev via iperf3 16 streams, MTU 1460"; HTB burst note. Nit: the 16-stream reverse run reads 173.58 Gb/s; 173.59 is the 32-stream hardware run. |

### 2.1 Executive

| Section / chart | Ref | Status | On screen | Evidence / what remains |
|---|---|---|---|---|
| Method & Metric Definitions box | item 26, §3.1 | CLOSED | yes | TP8 row: dashboard "3.10× (Decode-only per call, 18.9 → 58.7 µs)", brief "3.10× (Both agree on decode-only)", note "…old 2.32× metric was contaminated by the single 8K prefill step's 55 large AllReduces." |
| Wall-Time Budget tile | item 27, §7 | CLOSED | yes | Kept; the 4 Oct build showed it twice, this build once. Small label point: "1M decode is 54 % KV read" is the whole memory floor (KV ≈ 45 % + weights ≈ 9 %) — P13. |
| Run Validation / Fixed Serving tiles | item 10 | REGRESSED (wording) | yes | "7 guarded NOT_RUN" — see B3. |
| Distributed Profile Coverage tile | item 3 | PARTLY | yes | "14 / 22 CAPTURED" over "7 with usable exports (all prefill); decode deferred · 8 missing". The "7" is v1.2's counting error; it is **8** (C1). |
| NCCL Policy tile | item 8 | CLOSED | yes | 12/12 CLEAN. |
| Deployment Decision Map · TP4 row | item 6 | CLOSED, one tag left | yes | Text now "the 8-GPU ring is 2× longer (14 vs 6 steps: +17 µs/call measured) and socket crossing adds ≤ 0.4 µs". Still tagged "[MEDIUM / CROSS-VALIDATED]"; v1.2 asked to drop "cross-validated" for this cause. The ring explains 17 of the 40 µs; say so and add "the other ~22 µs appears only in serving; pinning test pending". |
| Decision Map · network cells | item 7 | CLOSED | yes | "173.58 Gbps VPC (MTU 1460, ens3)" in all four cells. |
| Campaign Scope / Gaps | — | OLD DEFECT | yes | Listed under "Not established / Unresolved": "decode profiles in graphs-on mode (captured in eager mode only; serving operates with CUDA Graphs ON)". Single-node graphs-on decode profiles exist (the torch budget the Profiler uses). What is missing is two-node decode — P11. |
| Configuration Guidance Matrix | item 4, §2 | CLOSED | yes | TP4 row reworded; c8/c16 row with p95; chunk 8192. |
| Knobs That Matter · chunk row | item 23 | CLOSED, overstated | yes | "16K chunk size Pareto-dominates 8K … HIGH (Pareto Resolved)". The row's own numbers say otherwise: at 128K c4 TTFT is 11.34 → 10.66 → 10.88 s, so 16K is 2 % slower than 8K. This came from v1.2's §4.14 — C3. |
| Knobs · network cap row | §2 | CLOSED | yes | "PP boundaries were fine down to 20G (-0.1% to +3.9% at 1M)" — correct because it is scoped to 1M. |
| Bottleneck Regime Map · 8K row | §2 regime map | CLOSED | yes | "kernel-time + collectives (46 % of memory BW)". |
| Prefill Communication Share (§4.4) | — | OLD DEFECT (nit) | yes | 8K row "≈ 50 %" is 0.12 / 0.222 = 54 % (the tile says 54 %). "intra-node TP prefill spends 14–50 %" — the §4.17 table gives 16–57 % for TP4/TP8, and 14 % is a two-node row — P12. |
| Recipe card / What Not To Do | §2 | CLOSED | yes | — |
| Chart · TTFT vs Context (`chart_exec_ttft`) | — | unchanged | yes | 4 series × 3 contexts. Renders. |
| Chart · TPOT vs Context (`chart_exec_tpot`) | item 6 | CLOSED | yes | Card interpretation reworded to the ring explanation. |
| Chart · Capacity / SLO Envelope (`chart_exec_capacity`) | item 11 | CLOSED | yes | "784.1 output tok/s (at 34.5 ms mean TPOT, 38.0 ms p95)". |

### 2.2 Key Finds (a visible tab from this build on)

The Top-10 cards are a second copy of the ten findings. Only TOP 1 (KD#3) and TOP 7 (KD#7) received fixes. Now that the tab is visible, every un-ported card contradicts its own Key Discoveries page.

| Card / chart | KD page | Status | Evidence / what remains |
|---|---|---|---|
| Hero #1 · TOP 2 Fabric Exposure + `chart_top10_fabric_exposure` | KD#1 | OPEN on this card | No noise-floor sentence and no transport boundary (both now on KD#1). Numbers are correct: 20G deltas +1.14 / −0.10 / +3.91 / +276.7 % at 1M; SendRecv 7.11 / 5.54 / 2.04 GB/s. |
| Hero #2 · TOP 3 Concurrency + waterfall chart | KD#2 | OPEN on this card | WHY still says "the detailed service-time/scheduler mechanism behind the queue buildup is not fully decomposed". KD#2 now gives the mechanism: prefills one full prefill apart, first tokens at 93.5 / 185.4 / 277.3 / 368.9 s, `max_num_partial_prefills=1`. Copy it. |
| Hero #3 · TOP 1 Long-Context table + `chart_top10_hybrid_regime` | KD#3 | PARTLY | The NCCL row's cells now read "NCCL (SendRecv / AR)", "SendRecv + AR", "nsys eager", "SendRecv 4.5× · AR 2.7×", "excluding start-up broadcast": the 128K and 512K work cells hold labels, not times. Put in the 16-rank sums: SendRecv 4.31 → 19.29 s, AllReduce 12.44 → 33.75 s. The chart mixes two set-ups. Its 128K point (FlashAttention 21.5 %, MoE 11.6 %, KDA 2.7 %) carries the TP4/PP4 run's evidence ID (EV-082) but holds the single-node TP4/PP1 128K capture's shares (the Profiler's top-15 table and ledger: 21.5 %, 11.6 %, 2.7 %). Its 512K point (44.8 %) is one TP4/PP4 stage-1 rank (P4). |
| TOP 4 Prefix Reuse | KD#4 | OPEN on this card | Only the counter ratios (87.33 / 49.98 / 49.97 %). The miss counts are on KD#4 ("1M: 2 of 3 hit … 2nd request missed"). |
| TOP 5 Prompt-Token Admission | KD#5 | OPEN on this card | No SLO-conditioned 1.8× and no client-cap boundary (both on KD#5). |
| TOP 6 Elasticity + `chart_top10_parallelism_elasticity` | KD#6 | CLOSED | GPU-s boundary sentence present. η values unchanged. |
| TOP 7 TP Decode Chain | KD#7 | CLOSED, two leftovers | 3.10× and the ring wording are in. Layer A still reads "19.0 μs", "37.0 μs", "1.95× barrier latency", where the α-β table says 37.6 µs, so 1.98× (P10). Layer C "Nsight … NCCL AllReduce dominant" is the eager capture; graphs-on it is 23 % on TP4. Label it eager or use 1.04 / 3.23 ms. |
| TOP 8 Runtime Knobs | KD#8 | OPEN on this card | Boundary still "impact on decode jitter … remains unresolved". The c4 runs measure it: TPOT 141.3 / 119.3 / 105.1 ms, p95 161 / 212 / 207 ms. Mixed short + long traffic is the part never run. |
| TOP 9 Busy GPU | KD#9 | OPEN on this card | No telemetry source and no power. KD#9's power sentence: TP16 225 W at 80.6 % vs TP4/PP4 310 W at 62.8 %. |
| TOP 10 KV Headroom | KD#10 | OPEN on this card | "Causal: LOW-MED"; WHY and DECISION both say "does not establish the allocator's exact sharding rule". KD#10 now says HIGH, with pool sizes 8.14 / 16.9 / 36.4 M tokens. |

### 2.3 Key Discoveries

**Signal view and 60-second map**

| Section | Ref | Status | Evidence |
|---|---|---|---|
| Header chip "PROFILE EVIDENCE: 14/22 DISTRIBUTED PROFILES COMPLETE" | item 3, §2 | OPEN | Unchanged. Use "14/22 captured · 8 with usable exports (all prefill)". |
| 60-second map · #3 row | item 15 | CLOSED | "…GEMM 5.2×; SendRecv 4.5×" (nit: "~15.6×" here, 15.7× elsewhere). |
| 60-second map · #7 row | item 5 | CLOSED | "18.9 µs vs 58.7 µs/call (3.10×…)". |
| Signal card #3 bars | item 15 | CLOSED | "SendRecv 4.5× · AllReduce 2.7×". |
| Signal card #4 / #5 | items 9, 16 | OPEN | Ratio only / 18.20× → 1.14× only. |
| Signal card #7 | item 5 | CLOSED, label nit | "Exact 7040 calls" sits next to decode-only numbers from 6,985 calls. |
| Two SVG charts (signal cards) | — | unchanged | Render. |

**Explorer pages** (rendered with `openFindingSubPage(1…10)`; all 19 page charts have live Chart.js instances)

| Page | Status | On screen now | What remains |
|---|---|---|---|
| KD#1 Fabric Exposure | PARTLY · NEW ERROR | Takeaways: noise floor ✓ (v1.2 item 21), mechanism added, transport boundary added. | (a) The mechanism sentence fuses three separate measurements: "SendRecv ceiling drops 7.11 → 2.04 GB/s with 16 KiB latency rising to 227–290 µs across 37.7 MB per call". The 20G cap moves SendRecv bandwidth; 227–290 µs is native cross-node AllReduce latency; 37.7 MB is the prefill message. Split them. (b) "NCCL_NET Transport Boundary: PP point-to-point boundaries operate without penalty down to 20G cap; cross-node TP should not be deployed across VPC without NVLink" is wrong (N7). The ask was the transport fact: NCCL over plain TCP sockets, `NCCL_NET=Socket`, provider plugin disabled. (c) "Inspect Evidence" opens EV-030 (tp4_chunk8k 512k_c1); it should open EV-111 (P1). Charts: TTFT at 20G by topology, 1M delta bars — correct. |
| KD#2 Concurrency | CLOSED (one label) | Ladder takeaway ✓ ("first tokens arrive sequentially at 93.5s, 185.4s, 277.3s, 368.9s (peak_running = 2, peak_waiting = 3)"); stall footnote ✓. | The footnote "stall budget card confirms 25% → 57% → 71% stall share under load" uses 8K load points (c8, c32, open loop 1.0×) inside a 1M sentence; add "(8K)". The scope note ("Distributed layouts … were run at c=1 only; concurrency not yet measured") sits in the unrendered `scope_note` (B6). Confidence line "MEDIUM for exclusive TPOT mechanism" can stay: the TPOT mechanism is not decomposed. "Inspect Evidence" → EV-034 (tp4_chunk16k 512k_c1), should be EV-067. |
| KD#3 Long-Context | PARTLY — §3.4 contradiction now on one page | Takeaway ✓ ("SendRecv grows 4.5× … AllReduce grows 2.7× (neither is sub-linear)"). | Hero card ("2.18×", "NCCL Transport Work", "empirical p≈0.56 (sub-linear)"), table row ("NCCL Transport (Send/Recv)", "8.3%", "5.2%", "~2.18×", "p ≈ 0.56") and the primary chart's first bar (2.18) are all unchanged. The takeaway now says "nsys only, eager mode, start-up broadcast excluded" ✓, but the confidence line still says "Direct PyTorch/Nsight kernel breakdown" (the PyTorch profiles are single-node decode; this page is nsys only). The share columns and secondary chart (22.8 → 44.8 % FA, 40 → 35.6 % "Intra TP", 8.3 → 5.2 % P2P) are single ranks from different stages and do not match any per-rank export (P4). Use the §6.1 16-rank aggregates (128K → 512K: FA 14.7 → 43.8 %, AllReduce 43.1 → 22.4 %, SendRecv 14.9 → 12.8 %). "Inspect Evidence" → PR-007 (N12). |
| KD#4 Prefix Reuse | CLOSED | Miss counts in takeaways. | "Inspect Evidence" → EV-038 (8K c8); should be EV-075. |
| KD#5 Prompt-token Admission | CLOSED (wording) | 1.8× row and client-cap boundary in takeaways. | "usable capacity is 1.8×" does not say of what. Write "the 8K-vs-128K gap in usable throughput is 1.8×: 24,977 vs 13,967 tok/s (prompt + output) at the highest load that keeps p95 TPOT ≤ 100 ms with ≥ 90 % of the offered rate served — 8K at 0.75×, 128K at 0.50×". Prompt tokens alone give 24,220 vs 13,940 tok/s (1.7×). "Inspect Evidence" → EV-040 (8K c32); should be EV-116. |
| KD#6 Parallelism Frontier | PARTLY · NEW ERROR | GPU-s definition ✓; "4 scale-out + 2 scale-up" in a takeaway. | Confidence line on screen still "6 scale-out topologies at 1M"; the fix is in the dead field, so the page contradicts itself. Energy takeaway is wrong (N6). "Inspect Evidence" → EV-044 (128K c16); should be EV-081. |
| KD#7 TP Decode | CLOSED (two nits) | Hero, chain, graphs-on budget, 1M KV floor, cross-node/pipeline pointer. | The pointer takeaway is printed twice (N13). Confidence says "Exact 7040 AllReduce calls"; the decode-only figure is 6,985. "Inspect Evidence" → PR-003 (correct target; see N10/N11). |
| KD#8 Runtime Knobs | PARTLY | Binding-constraint sentence ✓, two-step wording ✓, peak_running = 2 ✓. | "16K chunk size Pareto-dominates 8K and 4K under concurrency (TTFT drops −27.1% …)": −27.1 % is 1M c1, not concurrency. At 128K c4, 16K is 2 % slower on TTFT than 8K (C3). The c4 rows are not in the page table. "Inspect Evidence" → EV-048 (1M c1 closed loop); should be EV-027 / EV-035. |
| KD#9 Busy GPU | PARTLY | Power takeaway ✓, eager label on takeaway 5 ✓. | Confidence line on screen: "Direct comparison of Prometheus GPU SM utilization telemetry…" (fix in dead field). Chart y-axis "Reported GPU SM Util (%)": the archive field is `gpu_util_mean_pct`, which the pilot's `09_metrics_sampler.py` takes from nvidia-smi `utilization.gpu` (share of time a kernel was running), not SM occupancy (P14). The dead note's "1 Hz" is also wrong: the pilot's case files set `metrics_interval_s` 0.5 (1.0 only on the minimal-observer case), the per-GPU sample counts in `gpu_node_stats_json` against each run's duration give a median of 0.46 s (middle half 0.39–0.52 s), and the energy panel's "0.5s interval" is right. "Inspect Evidence" → EV-050 (512K maxseq4); should be EV-084 / EV-087. |
| KD#10 KV vs VRAM | CLOSED | Confidence HIGH; pool sizes; MLA replicated; 10 % reserve (`--gpu-memory-utilization 0.9` in 43 of 44 case manifests and 60 of 61 `SERVER_COMMAND.txt` files; the exception is the offload case, which fixed the pool with `--kv-cache-memory-bytes` and failed to start). | "Inspect Evidence" → EV-054 (prefix 512K); should be EV-084. |

### 2.4 Scale-Up

| Section / chart | Ref | Status | Evidence |
|---|---|---|---|
| TTFT card · TPOT card · decision table | item 6, §2 | CLOSED | "Single-NUMA 4-GPU ring avoids 14-step ring AllReduce latency (+17 µs ring; socket crossing adds ≤ 0.4 µs; thread pinning pending diagnostic)". The leading "Single-NUMA" is a leftover label but no longer a causal claim. |
| Crossover, 16 KiB / 64 MiB points, TPOT with throughput | §2 | CLOSED | Unchanged from 4 Oct. |
| Charts: TTFT, TPOT, TPS, 8K concurrency, NCCL busbw (5) | — | unchanged | All render; data identical to 4 Oct. |

### 2.5 Scale-Out

| Section / chart | Ref | Status | On screen | Evidence / what remains |
|---|---|---|---|---|
| Network selector | item 1 | CLOSED | yes | Three options: Native, 100G (HTB, burst 2400 B), 20G. |
| Charts · topology comparison and context scaling (`chart_scaleout_comparison`, `chart_scaleout_context_scaling`) | item 25 | CLOSED | yes | Rendered in all 21 states (3 networks × 7 metrics); data and axis titles follow the selector. The metric dropdown and chart axes do not say "c1", but one line above the matrix now does ("All metrics measured under c=1"). |
| Context card ratios | §2 | CLOSED | yes | "4.6–6.8× (128K→512K) and 2.3–2.9× (512K→1M)". |
| Decision Matrix · verdict rules | item 25, §5.7 | PARTLY | partly | A rule line was added: "RECOMMENDED = lowest measured latency / highest TPS; VIABLE = …; HIGH CAP SENSITIVITY = >50 % TTFT penalty". The rendered table never shows "RECOMMENDED": the script replaces it with "lowest measured TTFT among tested cells". "HIGH CAP SENSITIVITY" is hard-coded to TP16 at 20G, so TP16 at 100G and 128K (+51.6 %) shows "VIABLE" against the printed rule (N9). Column headers now "Output TPS (c1)", "Req TPS (c1)", "Queue (c1)" ✓. |
| Decision Matrix · queue units | item 25, K6 | CLOSED | yes | ms, with the right values (0.012 / 0.016 / 0.020 ms on TP4/PP4; 0.038 ms on TP8/PP2 1M). |
| §4.7 per-stage PP panel | item 18 | CLOSED | yes | Stage table, cost model, the 8,7,6,6 note and the 15,12 prediction, all as on 4 Oct. |
| §4.7 · PP2 check line (new) | §6.2 | CLOSED · NEW ERROR | yes | Ratios correct (stage 0 / stage 1 flash time 0.766 on TP4/PP2 and 0.773 on TP8/PP2). "exactly corroborating the 0.75 ratio expected from the 6 vs 8 full-attention layer distribution" is wrong: the panel directly above lists the 7 full-attention layers (#3, #7, #11 | #15, #19, #23, #26), so the 14/13 split puts 3 against 4. 0.77 vs 0.75 is "within 3 %", not "exactly" (N8). |
| α-β model, verification table, placement | items 19, 20, 25 | CLOSED | yes | Unchanged from 4 Oct. |
| Repeatability noise floor paragraph | item 21 | CLOSED · OLD DEFECT | yes | The band is right. Two of its examples are mislabelled: "Deltas of ±0.10% (e.g. 100G cap at 128K)" — no 128K delta is that small (+0.66 / +1.36 / +2.97 / +51.6 % at 100G); the deltas near ±0.1 % are TP8/PP2 at 1M (−0.13 / −0.10 %) and TP4/PP2 at 1M under 100G (+0.13 %). "+3.91% (TP4/PP4 at 20G, 128K)" — +3.91 % is 1M; 128K is +14.67 % (P6). |
| Topology × Network Sensitivity heatmap | §5.7 | PARTLY · NEW ERROR | yes | Rule printed: "HIGH NETWORK RESILIENCE = <15% TTFT delta on 20G cap vs native; MODERATE = 15–50% delta; HIGH CAP SENSITIVITY / EXPOSED = >50% delta". The cells use six labels, and three of them break the rule: TP4/PP2 (+8.0 / +2.4 / +1.1 %) is "MODERATE NETWORK SENSITIVITY" while TP4/PP4 (+14.7 / +8.9 %) is "HIGH NETWORK RESILIENCE"; TP4/PP4 1M (+3.91 %) is "LOWEST DELTA ON 20G CAP" while TP8/PP2 (−0.10 %) and TP4/PP2 (+1.14 %) are lower; TP8/PP2 cells use "INSENSITIVE TO EGRESS CAP" and "LOW APPLICATION TTFT SENSITIVITY…", which are not rule labels (N9). Deltas recomputed from `combined_vllm_runs.csv`: 23 of 24 match as shown; TP8/PP2 128K at 100G is +1.36 % (shown +1.37 %). 21 of the 36 TTFT cells sit 0.7–3.3 ms off the archive means (P17). |
| Network Architecture table | item 7 | CLOSED | yes | No RTT. 50G/10G iperf rows (33.0 / 9.0 Gb/s, "HW QUALIFIED / RUNS DEFERRED") were already there on 4 Oct (C5). |
| Energy per Token panel (§4.6) | item 17 | CLOSED | yes | Every row as v1.2 recomputed. Insight text "Lower per-GPU draw from NUMA/network stalls" (TP8/PP2) is a guess; drop "NUMA". |

### 2.6 Long Context

| Section / chart | Ref | Status | On screen | Evidence / what remains |
|---|---|---|---|---|
| Scope label on "TP4/PP1 vs TP8/PP1 — 1M Concurrency" (new) | §6 | CLOSED | yes | "Distributed layouts … were run at c=1 only; concurrency / multi-request load not yet measured". Right card. |
| Readiness tiles, waterfall, serving-decision table, prefix 1M | L1–L6 | CLOSED | yes | Unchanged from 4 Oct. |
| FP8 KV card | item 10 | REGRESSED (fact) | yes | "NOT_RUN (no gate reason recorded) … FP8 KV-cache was not executed". It was attempted: the server exited rc=1 after 132 s and 134 s (B3, C2). |
| Host ↔ GPU tiering card | item 20 | CLOSED · OLD DEFECT (wording) | yes | Numbers right (8.1 GB per rank, 0.14 s at 56.9 GB/s). "While offload was disabled … the physical bounds are mathematically certain" — offload was not disabled, its runs failed to start, and 0.14 s is a bandwidth estimate to be tested (plan B9). Nit: D2H is 452.37 GB/s over 8 GPUs = 56.5 GB/s, not 56.6 (P8). |
| Charts: concurrency, scheduler, chunk, prefix (4) + FP8 placeholder | — | unchanged | yes | Render; FP8 canvas intentionally empty. |

### 2.7 Scheduler & KV

| Section / chart | Ref | Status | On screen | Evidence / what remains |
|---|---|---|---|---|
| End-to-End Wall-Time Budget tables (§4.17) | item 27 | CLOSED | yes | First card on this tab (v1.2 said Long Context — C4). 24 + 24 rows with †. |
| Finding card · "Chunk-Size / Prompt Budget Finding (8K at c4)" (new) | §7 finding 1 | CLOSED · overstated | yes | Numbers right: own prefill 0.21 → 0.42 s, queue 27 ms, prompt = `max_num_batched_tokens`. "Expanding batch token headroom to 8,448 … eliminates this 211 ms penalty" states an untested prediction as a result. Write "should save ~211 ms; plan A1 (10 min) checks it" (N16). |
| Finding card · "MoE Decode Batching & Expert Expansion" (new) | §7 finding 2 | CLOSED · overstated | yes | "Under load, MoE decode step expands from 4.5 ms (c1, 8 active experts) to 15.8 ms (c32, 163 of 256 experts) and 22.9 ms at full load (222 experts)". The expert counts are modelled (uniform routing, an upper estimate) but are written as observed. Add "expected under uniform routing; a router counter would measure it". v1.2's other half — the kernels above the floor stay at 2.5–4.8 ms (2.46–4.75 ms in the CSV) — is missing (N16). |
| Stall budget card (§4.5) | item 23, §3.5 | CLOSED | yes | Scope label added ✓; "At full load (1.00×), 71% … (Knee occurs at 0.75× SLO / 0.90× slope)" ✓. |
| K1 capacity knee · K2 · K4 · K5 · K8 | §2 | CLOSED | yes | Unchanged. K7: "TPOT 10.82ms" still has no p95 beside it (13.3 ms) — minor, as in v1.2. |
| Peak KV chart (`chart_sched_kv`) · K9 | item 14 | PARTLY | yes | The subtitle now carries the token pools ("TP4/PP1 8.14M, PP2 16.9M, PP4 36.4M tokens · 10% vLLM reserve"); the axis is still %. A tokens axis, or token labels on the points, closes it. |
| Scale-out ledger · K3 | item 14 | CLOSED | yes | "is verified by empirical token pool scaling: TP4/PP1 8.14M … TP4/PP4 36.4M tokens (… headroom = 10% vLLM reserve)". |
| Scale-out ledger · queue column · K6 | K6 | CLOSED (units) · NEW ERROR (values) | yes | The units are now ms, but the values are pattern-filled: 0.012 ms on every 128K row and 0.020 ms on every 512K/1M row. Archive (`queue_mean_s_from_hist`): TP4/PP4 512K 0.016, TP4/PP2 512K 0.023, TP8/PP2 1M 0.038, TP16 128K 0.019 ms. The Scale-Out matrix shows the right values for the same runs (N17). |
| Offload card | item 10 | REGRESSED (fact) | yes | "NOT_RUN / Excluded from execution scope" — attempted, server exited rc=1 after 126 s (B3). |
| Charts (7): KV, running/waiting, queue mean, preemptions, max_num_seqs, 8K and 128K open loop | — | unchanged | yes | All render. |

### 2.8 Profiler

Order on the page: banner → provenance table → scenario chips → hero tiles (Wall-Time Budget, AR, FA, GV, CP) → **new four-view time-budget panel** → kernel-composition card → **new six-layout table** → PyTorch operator card → CUDA API card → kernel latency card → resource-pressure ledger → top-15 kernel table → coverage matrix → deployment rules. That is the order §7 of v1.2 asked for, and nothing was removed.

| Section / chart | Ref | Status | On screen | Evidence / what remains |
|---|---|---|---|---|
| Eager-mode banner | item 2 | CLOSED | yes | Unchanged. |
| Provenance table · distributed row | item 3 | PARTLY | yes | "14 / 22 CAPTURED" over "7 usable exports (all prefill); decode deferred · 8 missing" — 8, not 7 (C1). |
| Provenance table · capped row | — | OLD DEFECT | yes | "3 Prefill sweeps captured at 100G; decode points deferred …". No capped decode points were planned. `V8_FULL_RELEASE.json` plans 8 capped points, all 128K prefill (`capped_100g_20g_prefill128k: 8`): 3 captured at 100G; TP16 at 100G and all four layouts at 20G not taken (P2). |
| Scenario chips | §6.1 | NEW ERROR | yes | TP4/PP2 and TP8/PP2 chips were added **twice** (11 chips). The kernel table they filter has rows only for `tp4_prefill` (8) and `tp4_decode` (6), so the PP2 chips (and the older TP8, TP4/PP4 and TP16 chips) show zero rows (N14). |
| Hero tiles (AR, FA, GV, CP, Wall-Time) | items 4, 28 | CLOSED | yes | 18.9 → 58.7 µs; 6.24 → 4.26 ms with "no TTFT gain at 128K"; 171.2 → 126.5 ms; CP eager caption. |
| **Time-budget panel — four views** (new) | §7 | CLOSED on the page · **NOT VISIBLE in the file** | **no** | Placement, four-way toggle (single-request first token / decode token, under-load first token / decode token), captions E2E·A–D, † note, measured-vs-modelled note, the 0.4 % engine/client closure, the additive-scope note and the two waves clarifications are all present. The four images are `<img src="wall_time_budget_*.png">` and are not in the file; the console shows four `ERR_FILE_NOT_FOUND`. With the PNGs beside the HTML they render correctly (checked); in the uploaded file they are broken icons (N18). The CSV links point to `time_budget/*.csv`, a different folder from the images. |
| Panel captions | §7 | CLOSED (one overstatement) | yes | E2E·D: "at high concurrency prefill-chunk contention causes 86–98 % stall waits". That holds for the closed-loop 128K–1M rows (86–98 %: c ≥ 4 at 128K, c ≥ 2 at 512K and 1M); the 128K open-loop rows are 76 % (0.50×) and 90 % (1.0×), and at 8K waiting is 13–63 %. Say "for ≥128K prompts under load". |
| Finding 1 (8K tail chunk) | §7 | CLOSED · overstated | yes | "Per-request trace proves it: wave arrivals land at 0.23, 0.65, 0.87, 0.88s … saves 211 ms at c4". Those times are first tokens, not arrivals. The saving is the prediction plan A1 tests. "A 256-token headroom expansion (budget 8,448 or 8,000 prompt tokens)" mixes two alternatives (N16). |
| Finding 2 (MoE experts) | §7 | CLOSED · overstated | yes | "Concurrency forces uniform routing to touch 163 of 256 experts". Uniform routing is the model's assumption, not something concurrency does: "a batch of 32 is expected to touch ~163 of 256 experts under uniform routing (upper estimate)" (N16). |
| Kernel composition card · Decode Budget box | item 2 | CLOSED | yes | 23 % / 51 %; GEMV 24 %, MoE 19 %, Attention 19 %; 0.79 TB/s = 46 %. |
| Kernel composition card · 1M KV box, prefill contrast, cross-node line | items 28, P6 | CLOSED | yes | "TP16/PP1 spends 76.2% of GPU work (Node 0 Rank 0; all-rank mean 77.6%)". |
| Kernel composition card · pipeline line | P6 | CLOSED | yes | "8.3% of captured stage work (Stage 0)". |
| Chart · `chart_prof_kernel_categories` | §6.1 | CLOSED · NEW ERROR | yes | Three PP datasets added, and their values sum to the §6.1 table (the table's "other" is split into "Norms & Elementwise" 3.5 / 3.0 / 4.6 %, which is not in the source table and cannot be checked). Errors: (a) the TP4/PP4 legend says "Stage 0: 40.0% AR, 8.3% P2P; Stages 1-3 P2P wait 17-22%". On that rank 40.0 % is the start-up Broadcast and its AllReduce is 32.8 %; and only stage 3 waits 17–22 % (N5, P4). (b) The click map `prMap` has 5 entries for 7 datasets. Clicked in the browser: the TP4/PP2 bar opens PR-005 (a TP4/PP4 entry), and the TP8/PP2 and TP4/PP4 bars open EV-001, the single-node TP4 8K qualification run the pop-up falls back to. The two eager decode datasets (AllReduce 86.3 % / 89.1 %) open PR-002/003, which this build turned into graphs-on drawers (23 % / 51 %) (N15). (c) The TP16 legend's "All-Rank Range 75.1–78.9%" disagrees with PR-004's "range 74.8% - 79.5%"; the 12 usable ranks give 76.3–79.5 %, mean 77.6 % (P9). (d) The card subtitle says "across 112,640 traced kernels"; 112,640 is the TP4 eager decode capture's AllReduce call count (P16). |
| Six-layout composition table (new) | §6.1 | CLOSED | yes | All 56 cells (ranks and seven shares on seven rows) equal `prefill_composition_128k_by_layout.csv`; reading sentence and eager caption included. |
| PyTorch operator card · chart | items 4, 6 | CLOSED · OLD DEFECT | yes | Chart data right (GEMV 171.2 vs 126.5 ms). The Operator Accounting line "TP8 decode-only AllReduce penalty (+277.6 ms) exceeds GEMV savings (+39.8 µs/call over 6,985 decode steps)" has its parts swapped: the GEMV saving is 44.6 ms, 39.8 µs per call is the AllReduce penalty, and 6,985 are calls (127 steps). The chart tooltip still says "TP8 decode GEMV is 66.9ms faster", which is the pair item 4 corrected (P7). |
| Resource-pressure ledger | P8 (v1.2) | OPEN | yes | The row "Host CPU Launch & Event Sync" (6.1 % / 3.0 %) is still inside a GPU-share ledger. The AllReduce row now says "+39.8 µs per decode AllReduce (14-step vs 6-step ring + host serving skew)": the ring explains 17 µs, and "host skew" is the untested half. |
| Top-15 kernel table | P9 (v1.2), P13 | PARTLY / OPEN | yes | Still no mode column (the mode appears only in the drawer); no torch chip. |
| Coverage matrix · status column | item 3 | PARTLY | yes | Two rows changed to "DECODE DEFERRED" (TP4/PP4 2/16, TP8/PP2 0/16). Four rows with 0–2 usable ranks still say COMPLETE: TP4/PP2 decode 2/8, TP4/PP2 batched 0/4, TP16 decode 0/9, TP16 512K 1/12. |
| Coverage matrix · TP4/PP4 128K row | P6, §1.3 | NEW ERROR | yes | "SendRecv P2P handoff is 8.3% of Stage 0 work (Stages 1–3 wait 17–22%)". Per-rank exports (share of all kernel time): stage 0 8.0–9.9 %, stage 1 8.8–10.2 %, stage 2 9.0–11.2 %, stage 3 17.2–21.9 % (N5). |
| Coverage matrix · capped rows and node counts | — | OLD DEFECT | yes | Four rows (`tp4_pp4_decode_capped100g`, `tp8_pp2_decode_capped100g`, `tp4_pp2_decode_capped100g`, `tp16_pp1_decode_capped100g`: CAPPED_100G · 8K Decode · NOT_CAPTURED) describe points that were never planned, and the four missing 20G prefill points are absent; the reason "Deferred in favor of empirical E2E…" is not recorded anywhere (P2). TP4/PP2 rows show "8 / 8" in both node-capture columns where each node has 4 ranks, and capped TP4/PP2 says "Complete 16-rank dual-node capture under configured 100G bandwidth cap" (it has 8 ranks); capped TP8/PP2 says the same with 15 of 16 usable (P3). |
| Deployment rules · row 1 | items 2, 6 | CLOSED | yes | Graphs-on: "58.7 µs vs 18.9 µs on TP4 (3.23 ms vs 1.04 ms collective budget; +17 µs from longer ring, socket crossing adds ≤ 0.4 µs)"; prescription points to the pinning test; source `profiles_torch_single_node/`. |
| Drawers PR-001…PR-007 | §2 drawer row | PARTLY · NEW ERRORS | yes | `mode` added to all seven, but the badge prints twice in every drawer (N11). PR-002's "GEMV/MoE Compute" row reads "51% (1.94 ms)" — 1.94 ms is 43 % of 4.47 ms. PR-003's reads "49%", which is all non-AllReduce time; GEMV + MoE ≈ 0.78 + 0.85 = 1.63 ms = 26 %. Its "Weight Streaming" row reads "46% BW", TP4's figure; TP8 is ≈ 27 % by the same method (N10). PR-002/003 also call their 251.5 / 583.9 ms totals an "Eager Nsight baseline"; those are the graphs-on torch totals for the whole capture (N21), and their `artifact_path` names a file that does not exist (N22). PR-005 has the stage-wait error (N5). PR-007 joins stage 0's FlashAttention (22 %) to another rank's AllReduce 35.6 % and SendRecv 5.2 %; at 512K stage 0's SendRecv is 25.6–26.0 % (N12). PR-006 (TP16 512K) shows the TP4/PP4 growth factors 15.7× / 3.9× / 3.8× and does not say only 1 of 12 ranks exported (P5). PR-002/003 observations still count the eager "Nsight decode kernel work" as layer 3 of the chain. PR-001, PR-004, PR-005 and PR-006 point to files that are not in the archive, and so do 26 of the 28 paths in the drawers' "Raw Artifact Paths" lists (P15). |
| Charts (4): composition, PyTorch operators, CUDA API, kernel latency | — | render | yes | Only the composition chart changed. |

### 2.9 Evidence

| Section | Ref | Status | On screen | Evidence / what remains |
|---|---|---|---|---|
| Cluster, Stack & Campaign Readiness Audit (new) | item 24 (readiness block) | REGRESSED | yes | Software stack invented (B1, N1). Validator defect 2 invented (B2, N2). NOT_RUN reason invented (B3, N3). NOT_CAPTURED counts right (5 not captured, 3 native incomplete, 14 captured) but the reason is invented, and "7 with usable rank exports" should be 8 (C1). |
| Stray `id="perf-evidence-table-container">` text | — | NEW ERROR | yes | The readiness panel overwrote the ledger card's opening tag; the ledger lost its card wrapper (N4). |
| Ledger · new columns | item 24 | REGRESSED | yes | B4, N4. |
| Ledger · NOT_CAPTURED row | E1 | CLOSED | yes | The ledger now holds 119 COMPLETED + 7 NOT_RUN and no profile rows; the reconciliation note explains the profiler counts (fix its wording per B3). |
| Ledger · network cells | item 7 | CLOSED | yes | "173.6 Gbps (MTU 1460)" in all 12 native cells. |
| Startup table, campaign summary, source hierarchy | items 22, 24 | CLOSED | yes | Unchanged. |
| Reviewer Audit matrix | item 6 | CLOSED | yes | TP8 row now "14-step ring latency identified as contributor (+17 µs ring; socket crossing adds ≤ 0.4 µs; thread pinning pending diagnostic)". This matrix lists the right stack (vLLM 0.29.0 … CUDA 13.0) — so the tab now contradicts itself (B1). |
| Decision Claim Registry · row 1 | item 2 | CLOSED | yes | "graphs-on budget confirms 23% AR collective share (1.04 of 4.47 ms; weights stream at 46% mem BW; eager nsys capture 86.3% noted as reference)"; source `tp4_8192_c1 + torch_graphs_profile`. |

## 3. The v1.2 lists, item by item

### 3.1 v1.2 §1 — the 28-item fix list

| # | Item | v1.2 (4 Oct) | 5 Oct | What decides it (section above) |
|---|---|---|---|---|
| 1 | 50G/10G not rendered as data | FIXED | **CLOSED** | §2.5. The 50G/10G iperf rows were already on the network table (C5). |
| 2 | Eager disclosure; graphs-on budget | PARTLY | **CLOSED** (new defects inside the fix) | Rules row 1, claim registry row 1 and PR-002/003 now graphs-on. Inside the fix: wrong derived shares (N10), badge printed twice (N11), the torch totals labelled eager (N21), a dead artifact path (N22). Leftovers: Key Finds TOP 7 Layer C and the PR-002/003 observations still lean on the eager capture. |
| 3 | Coverage status from usable exports; qualify 14/22 | PARTLY | **PARTLY** | 2 of 6 low-export rows changed; four still COMPLETE; the KD header chip still says COMPLETE; "7 usable" should be 8 (C1); TP4/PP4 row now wrong (N5). |
| 4 | Five wrong on-screen numbers | FIXED | **CLOSED** | All five still right. Same family, missed by v1.2: GEMV tooltip 66.9 ms and the Operator Accounting card (P7). |
| 5 | KD#7 hero 3.10× | PARTLY | **CLOSED** | Narrative and definitions box now 3.10×. Nits: "Exact 7040 calls" label; duplicate pointer (N13). |
| 6 | NUMA cause reworded everywhere | PARTLY | **CLOSED** (one tag) | Every causal NUMA sentence rewritten. One "[MEDIUM / CROSS-VALIDATED]" tag left on the Executive TP4 row; the unexplained ~22 µs is not mentioned. |
| 7 | Network facts; no RTT | PARTLY | **CLOSED** | 0 occurrences of RTT. |
| 8 | NCCL policy tile | FIXED | **CLOSED** | — |
| 9 | Prefix miss counts | PARTLY | **CLOSED** on KD#4 | Key Finds TOP 4 and signal card #4 still ratio-only (§2.2). |
| 10 | NOT_RUN, no invented reason | FIXED | **REGRESSED** | New invented reasons (B3, N3). v1.2's "no reason recorded" was itself incomplete: the manifests record rc=1 (C2). |
| 11 | SLO and p95 | FIXED | **CLOSED** | — |
| 12 | Open-loop client cap | FIXED | **CLOSED** | Now also on KD#5. |
| 13 | Serial prefill; partial-prefill limit | PARTLY | **CLOSED** | Ladder on KD#2; KD#8 binding constraint. Key Finds TOP 3 still says "not fully decomposed" (§2.2). |
| 14 | Pool in tokens; drop the allocator hedge | PARTLY | **CLOSED** on K3 and KD#10 | K9 only as a subtitle; Key Finds TOP 10 keeps the hedge (§2.2). |
| 15 | KD#3 NCCL 2.18× | NOT FIXED | **PARTLY** | Takeaway, 60-second map, signal card and discovery maps fixed. KD#3 hero, table and chart still 2.18× (p ≈ 0.56, "sub-linear") (§2.3). |
| 16 | KD#5 1.8× | PARTLY | **CLOSED** on KD#5 | Say what the 1.8× is of (§2.3). |
| 17 | Energy | FIXED | **CLOSED** | Panel right. New KD#6 energy line wrong (N6). |
| 18 | Per-stage PP view | FIXED | **CLOSED** | PP2 check added, with an error (N8). |
| 19 | α-β; TP16 bound | FIXED | **CLOSED** | — |
| 20 | Host↔GPU, tiering | FIXED | **CLOSED** | Wording and D2H nit (P8). |
| 21 | Repeatability band | FIXED | **CLOSED** | Now used on KD#1. Two mislabelled examples (P6). |
| 22 | Start-up | FIXED | **CLOSED** | — |
| 23 | Stall budget; chunk Pareto | FIXED | **CLOSED** | Knee label fixed. "Pareto" overstated (C3); Key Finds TOP 8 still says "unresolved". |
| 24 | Evidence tab columns, NOT_CAPTURED, defects, readiness | PARTLY | **REGRESSED** | B1–B4 (N1–N4). |
| 25 | Placement; c1 labels | PARTLY | **CLOSED** | Matrix headers and a rule line say c1. |
| 26 | Definitions box | PARTLY | **CLOSED** | — |
| 27 | Where the time goes | FIXED | **CLOSED** | Tables on Scheduler & KV (C4); charts §3.6. |
| 28 | TP16 11–16 ms; §4.3 scope | FIXED | **CLOSED** | — |

### 3.2 v1.2 §2 — the 24 tab items

| Tab · item | v1.2 | 5 Oct | Note |
|---|---|---|---|
| Executive · header, validation tiles | FIXED | CLOSED | — |
| Executive · regime map 8K row | NOT FIXED | **CLOSED** | "kernel-time + collectives (46 % of memory BW)". |
| Executive · decision map, guidance, knobs, recipe | FIXED | CLOSED | Pareto wording (C3). |
| Executive · What Not To Do | FIXED | CLOSED | — |
| KD signal view · "14/22 … COMPLETE" | PARTLY | **OPEN** | Unchanged. |
| KD#1 · mechanism, replicate variance, transport boundary | NOT FIXED | **PARTLY** | Variance closed. Mechanism sentence fuses three measurements. Boundary sentence wrong and does not state the transport (N7). |
| KD#2 · label, ladder, 8K footnote | PARTLY | **CLOSED** | Footnote needs "(8K)". |
| KD#3 · grouping, denominator, Broadcast, 2.18×, nsys/eager | NOT FIXED | **PARTLY** | §2.3. |
| KD#4 · miss counts | PARTLY | **CLOSED** | — |
| KD#5 · 1.8×, client cap | PARTLY | **CLOSED** | Wording. |
| KD#6 · 4 + 2, GPU-s label, energy | NOT FIXED | **PARTLY** | "6 scale-out" still on screen (dead field); energy line wrong (N6). |
| KD#7 · hero, budget, PCIe label, boundary | FIXED | CLOSED | Pointer duplicated. |
| KD#8 · binding limit, c4 rows, two-step wording | PARTLY | **PARTLY** | Binding limit and two-step closed; the c4 rows appear only inside the wrong "under concurrency" sentence (C3). |
| KD#9 · telemetry source, power, eager label | NOT FIXED | **PARTLY** | Power and eager label closed; "Prometheus GPU SM" still on screen (dead field) and on the chart axis (P14). |
| KD#10 · law, decision, headroom | PARTLY | **CLOSED** | — |
| Evidence drawer · mode and rank set | NOT FIXED | **PARTLY** | Mode added (twice); PR-004 rank set fixed; PR-005, PR-007 wrong; PR-006 untouched (N5, N11, N12, P5). |
| Scale-Up · NUMA, crossover, TPOT, break-even, NCCL sizes | FIXED except NUMA | **CLOSED** | — |
| Scale-Out · ratios, labels, VERDICT, verification, placement, heatmap, transport | PARTLY | **PARTLY** | Rules printed; cells and rendered labels do not follow them (N9). |
| Long Context · L1–L6 | FIXED | CLOSED | Scope label added. FP8 card fact (B3). |
| Scheduler · K1, K2, K4, K5, K7, K8 | FIXED | CLOSED | K7 p95 nit unchanged. |
| Scheduler · K3, K6, K9 | NOT FIXED | **PARTLY** | K3 closed; K6 units right but values pattern-filled (N17); K9 subtitle only. |
| Profiler · P1–P5, P7, P11 rows 2/5, P12 | FIXED | CLOSED | — |
| Profiler · P6, P8, P9, P13, rules row 1 | PARTLY | **PARTLY** | P6 and rules row 1 closed; P8 and P13 open; P9 only in the drawer. |
| Evidence · E1–E4 | PARTLY | **REGRESSED** | E1 counts reconciled, reasons invented; E2–E3 B1–B4. |

### 3.3 v1.2 §3 — the five self-contradictions

| # | Contradiction | 5 Oct |
|---|---|---|
| 1 | TP8 AllReduce ratio 2.32× vs 3.10× | **CLOSED** — 3.10× everywhere; 2.32× appears only as "old … contaminated". |
| 2 | NUMA cause vs "socket crossing ≤ 0.4 µs" | **CLOSED** — one "CROSS-VALIDATED" tag on the Executive TP4 row left. |
| 3 | Eager decode numbers used as evidence | **CLOSED** in the three named places — PR-002/003 now carry wrong graphs-on shares (N10) and call graphs-on totals "eager" (N21). |
| 4 | KD#3 NCCL 2.18× vs SendRecv 4.5× | **OPEN** — the contradiction moved inside the KD#3 page: takeaway 4.5× / 2.7×, hero card, table and chart 2.18×. |
| 5 | Knee at 0.75× / 0.90× vs "the 8K knee" at 1.00× | **CLOSED** |

New contradictions this build creates (each also in §4):

* Two different software stacks on the Evidence tab (B1).
* Three different NOT_RUN stories ("NOT_RUN (no reason recorded)" / "safety-gated configurations not executed" / "Excluded from execution scope") against an archive that records rc=1 (B3).
* KD#6 confidence "6 scale-out topologies" against its own takeaway "4 scale-out + 2 scale-up".
* KD#9 "Prometheus" on screen against the dead note "not Prometheus".
* TP16 at 1M drawing 150 W (KD#6) against 225 W (KD#9 and the energy panel).
* "the 6 vs 8 full-attention layer distribution" (PP2 check) against "the 7 full-attention layers sit at #3, #7, #11, #15, #19, #23, #26" (the panel above it).
* The heatmap rule against the heatmap cells.
* Scheduler queue values against Scale-Out queue values for the same runs.

### 3.4 v1.2 §5 — the short list

| # | Ask | 5 Oct |
|---|---|---|
| 1 | 2.32× → 3.10× in the narrative and definitions box | **Done.** |
| 2 | Rewrite the six NUMA sentences; drop "cross-validated" | **Done**, except one tag. |
| 3 | Eager numbers out of rules row 1, claim registry row 1; update PR-002/003/004/005/007 with a mode field | **Done, with new errors**: N5, N10, N11, N12, N21, N22. |
| 4 | KD#3: replace 2.18×, publish the grouping and denominator | **Partly**: hero, table and chart still 2.18×; times and denominator missing. |
| 5 | Port fixes to KD pages 1, 2, 4, 5, 6, 8, 9, 10 | **Partly**: takeaways ported; three fixes in unrendered fields (B6); new errors on KD#1, #6, #8; the Key Finds copies not ported (B7). |
| 6 | Coverage status from usable exports; qualify the 14/22 tiles | **Partly**: tiles qualified (with v1.2's 7 → 8, C1); 4 rows and the KD header chip still say COMPLETE. |
| 7 | Remove RTT; define VERDICT; print the heatmap rule; label c1 views | **Partly**: RTT gone; c1 labelled; rules printed but not applied (N9). |
| 8 | K3; K6; K9; regime-map 8K row | **Mostly**: K3 and regime map done; K6 values wrong (N17); K9 subtitle only. |
| 9 | Evidence ledger columns | **Regressed** (B4). |

### 3.5 v1.2 §6 — layout coverage additions and scope labels

| Ask | 5 Oct | Note |
|---|---|---|
| 1. TP4/PP2 and TP8/PP2 in the kernel-composition card | **Done** (table + chart datasets) | Table exact. Chart: TP4/PP4 legend wrong, click map broken (N15). Chips duplicated and empty (N14). |
| 2. One line on the §4.7 panel for the PP2 check | **Done, with an error** | "6 vs 8" → 3 vs 4 (N8). |
| 3. KD#7 pointer to cross-node and pipeline decode | **Done** | Printed twice (N13). Text right: 208–290 µs per call, 11–16 ms of 14.9–20.1 ms TPOT, +0.3–0.5 ms per PP hop. |
| Scope labels: Long Context waterfall, stall budget, KD#2, #4, #5, #8 | **Partly** | Long Context 1M concurrency card and the stall budget card carry it; the Profiler panel carries an additive-scope note. KD#2/#4/#5/#8 labels sit in the unrendered `scope_note` (B6). KD#4 and #8 still say "single-node only" in their visible boundary line; KD#2 and #5 do not. |

### 3.6 v1.2 §7 — the four time-budget charts

| Ask | 5 Oct | Note |
|---|---|---|
| Four charts on the Profiler tab, under the hero row, above the kernel-composition card | **Placed correctly; not visible** | The panel, toggle and captions are there; the images are not in the file (B5, N18). |
| Single-request pair first, under-load pair behind a toggle | Done | Four-way toggle. |
| Captions: totals measured on every row; splits measured or modelled (†) | Done | "Totals are measured on every row …"; "† indicates modelled rows". |
| The two findings as notes on Profiler and Scheduler | Done, overstated | Both tabs carry both notes. Each states a prediction as a result (N16). |
| Additive — nothing removed | **Done** | Executive tile kept (de-duplicated), Long Context tile and Scheduler tables kept, kernel-composition card, torch panel and eager captures unchanged. |
| Optional: say "scheduling" cannot be split yet | Not done | Optional; one sentence in the measurement note would cover it. |

## 4. New errors in the 5 Oct build

| # | Error | Where | Archive / correct value |
|---|---|---|---|
| N1 | Software stack invented (vLLM 0.6.2, PyTorch 2.4.0+cu124, CUDA 12.4, driver 550.54.15, NCCL 2.20.5 "AWS-OFI-NCCL", Ray 2.37.0) | Evidence readiness panel | `V8_READINESS.json` actual versions: vLLM 0.29.0, Ray 2.58.0, PyTorch 2.13.0, Triton 3.7.1, FlashInfer 0.6.18, nvidia-nccl-cu13 2.29.7; driver 580.173.02; CUDA 13.0. `NCCL_NET=Socket`, GCP net plugin disabled. Worth stating next to it: the two-node Ray workers ran with `LD_LIBRARY_PATH=/tmp/clean_nccl_libs` (all 12 Ray audits). That directory holds `libnccl.so.2.31.2`, the version nccl-tests reports (`nccl_version 23102`). So the panel should show both the pip package (2.29.7) and the library on the two-node path (2.31.2). |
| N2 | "FINAL_VALIDATION Duplicate Keys" defect | same | Not in the archive. Real defects: `result_root` on a Windows path, and the Ray audit count of 0 / 12. |
| N3 | "safety-gated configurations not executed"; "per-worker nsys daemon was skipped" | same | Manifests: `RuntimeError('server exited rc=1')` after 126 / 132 / 134 s. `FINAL_VALIDATION`: `safety_skipped_count 0`. `coverage.json`: the 7 entries have `has_gate: false` and no `gate_reason`. No reason recorded for the 5 missing capped profiles. |
| N4 | Ledger: constant "w=1 · 32 req" on 23 rows (all wrong); empty "Cold Load" column; all 126 rows one cell short; stray tag text; card wrapper lost | Evidence ledger | The 23 rows: EV-001…008, 041…044, 061…064, 119…125. Archive: qualification 8K c1 2 · 12, 8K c8 2 · 32, 128K c1 1 · 5, 512K c1 0 · 2; closed-loop 128K c1/c4/c8/c16: 1 · 6, 1 · 12, 1 · 24, 0 · 32; observer rows 2 · 32 and 1 · 12; open-loop 128K 0 · 24. |
| N5 | "Stages 1–3 wait 17–22 %" | Coverage row, PR-005, composition-chart legend | TP4/PP4 128K SendRecv share of kernel time per rank: stage 0 8.0–9.9 %, stage 1 8.8–10.2 %, stage 2 9.0–11.2 %, **stage 3 17.2–21.9 %**. |
| N6 | KD#6: "TP4/PP4 consumes 143.1 J/1K tokens (310 W) vs TP16 134.8 J/1K tokens (150 W) and TP4/PP2 179.7 J/1K tokens (268 W)" | KD#6 takeaway | 1M c1 rows of the energy panel, each recomputed from `gpu_node_stats_json`: TP4/PP4 143.1 J, 310 W; TP4/PP2 160.2 J, 379 W; TP8/PP2 179.7 J, 268 W; TP16 **247.2 J, 225 W**. 134.8 J / 150 W is TP16 at 128K. As written, TP16 looks the cheapest at 1M; it is the most expensive. |
| N7 | KD#1: "PP point-to-point boundaries operate without penalty down to 20G cap; cross-node TP should not be deployed across VPC without NVLink"; plus the fused mechanism sentence | KD#1 takeaways | 20G deltas: TP4/PP4 +14.7 % (128K), +8.9 % (512K), +3.9 % (1M); TP4/PP2 +8.0 / +2.4 / +1.1 %; TP8/PP2 +0.8 / −0.2 / −0.1 %. There is no NVLink option between these nodes. The asked-for fact: cross-node NCCL ran over plain TCP sockets (`NCCL_NET=Socket`, provider plugin disabled). |
| N8 | "0.75 ratio expected from the 6 vs 8 full-attention layer distribution", "exactly corroborating" | Scale-Out §4.7 PP2 line | 7 full-attention layers; 14/13 split = 3 vs 4; measured 0.766 / 0.773 vs 0.75 (within 3 %). |
| N9 | Rules printed but not applied: heatmap labels, "RECOMMENDED" never rendered, TP16 at 100G +51.6 % not flagged | Scale-Out | Under the printed rule every TP4/PP2, TP8/PP2 and TP4/PP4 cell is "resilient" (< 15 %) and every TP16 cell "exposed"; TP16 at 100G 128K is +51.6 %. |
| N10 | PR-002 row "GEMV/MoE Compute" = "51% (1.94 ms)"; PR-003 rows "GEMV/MoE Compute" = "49%" and "Weight Streaming" = "46% BW" | Drawers | TP4: 1.94 ms is 43 % of 4.47 ms. TP8 (split and weight size taken from the graphs-on budget in Master review v1.2 §4.3, not recomputed here): GEMV ≈ 0.78 + MoE ≈ 0.85 = 1.63 ms = 26 % of 6.35 ms; 6.1 GB of active weights over 8 GPUs ≈ 0.76 GB per GPU in 1.63 ms ≈ 0.47 TB/s ≈ 27 % of the 1.71–1.72 TB/s BabelStream copy rate. |
| N11 | Mode badge printed twice | All seven drawers | Remove the duplicated line in the badge builder. |
| N12 | PR-007 "Pipeline Stage 0 / Rank 0: 22% FlashAttention, 35.6% intra-node TP AllReduce, 6.2% Fused MoE, 5.2% P2P SendRecv" | Drawer PR-007 (also KD#3's "Inspect Evidence") | TP4/PP4 512K stage 0 (4 ranks): SendRecv 25.6–26.0 %, FlashAttention 22.2–22.6 %, AllReduce 20.7–21.9 %, start-up Broadcast ~15 %. Stages 1–3 FlashAttention 44.4–50.0 %. |
| N13 | KD#7 pointer takeaway twice | KD#7 page | Delete one. |
| N14 | TP4/PP2 and TP8/PP2 chips duplicated; every distributed chip filters to 0 rows | Profiler | Remove duplicates; add rows per scenario, or let the chips filter the composition chart instead. |
| N15 | Composition chart: TP4/PP4 legend "Stage 0: 40.0% AR, 8.3% P2P; Stages 1-3 P2P wait 17-22%". `prMap` has 5 entries for 7 datasets: the TP4/PP2 bar opens PR-005, the TP8/PP2 and TP4/PP4 bars open EV-001 (clicked in the browser), and the two eager decode datasets (86.3 % / 89.1 % AllReduce) open PR-002/003, which now show graphs-on 23 % / 51 % | Profiler | That rank's AllReduce is 32.8 % (40.0 % is its start-up Broadcast). Give each of the 7 datasets its own drawer, in the same mode as the bar. |
| N16 | Findings stated as results: "proves", "eliminates this 211 ms penalty", "saves 211 ms", "wave arrivals", "forces uniform routing to touch 163 of 256 experts" | Profiler and Scheduler notes | 211 ms is a prediction (plan A1, 10 min). 0.23 / 0.65 / 0.87 / 0.88 s are first-token times. The expert counts are an upper estimate under assumed uniform routing (the PNG footnote says so; the notes do not). |
| N17 | Queue column pattern-filled (0.012 / 0.020 ms) | Scheduler scale-out ledger | TP4/PP4 512K 0.016; TP4/PP2 512K 0.023, 1M 0.021; TP8/PP2 512K 0.020, 1M 0.038; TP16 128K 0.019, 512K 0.021, 1M 0.021 ms. |
| N18 | Four time-budget charts are external PNGs | Profiler | Embed or redraw (B5). |
| N19 | Fixes written to fields the renderer never reads | KD pages | `confidence_note` × 10, `scope_note` × 4 (B6). |
| N20 | Key Finds tab exposed with pre-fix text on 7 of 10 cards | Key Finds | B7, §2.2. |
| N21 | PR-002/003 call their 251.5 / 583.9 ms totals eager: badge "eager capture 251.5 ms shown for reference", rule "Eager Nsight baseline: 251.5 ms across 7,040 calls", row "Eager Nsight AR (Ref)" (583.9 ms on PR-003) | Drawers PR-002, PR-003 | They are the graphs-on torch profile's AllReduce totals for the whole capture (`profiles_torch_single_node/tp{4,8}_8k_decode/torch/profiler_out_0.txt`; the pilot's torch run has no `--enforce-eager`): 55 calls in the prefill step (119.2 / 174.0 ms) + 6,985 decode calls (132.3 / 409.9 ms). The eager Nsight decode capture is 41.62 s over 112,640 calls on TP4 (86.3 %, 369.5 µs per call) and 100.60 s over 225,280 calls on TP8 (89.1 %, 446.5 µs). Label them "graphs-on torch, whole capture incl. the prefill step" or drop them. v1.2 called them eager (C6). |
| N22 | PR-002/003 `artifact_path` changed to `results_real_data/profiles_torch_single_node/tp{4,8}_8k_decode/torch_profile.json` | Drawers PR-002, PR-003 (Raw Artifacts tab) | No `torch_profile.json` exists in the archive. The files are `torch/profiler_out_<rank>.txt` (4 for TP4, 8 for TP8); rank 0 is `profiler_out_0.txt`. |

## 5. Older defects found in this pass (present on 4 Oct, not in v1.2)

| # | Defect | Where | Correct value / fix |
|---|---|---|---|
| P1 | 8 of 10 "Inspect Evidence" buttons on the KD pages open unrelated runs. The ID map in `openEvidenceForFinding` predates a renumbering: its own comments name the intended evidence ("TP16/PP1 20G TTFT 256.889s"), but EV-030 is now tp4_chunk8k 512k_c1. | KD explorer | KD#1 → EV-111, KD#2 → EV-067, KD#4 → EV-075, KD#5 → EV-116, KD#6 → EV-081, KD#8 → EV-027 / EV-035, KD#9 → EV-084 / EV-087, KD#10 → EV-084. KD#3 → PR-007 and KD#7 → PR-003 are the right targets. |
| P2 | Capped profiles described as "decode deferred" (tiles) and "decode points deferred" (provenance row); four rows `tp{4_pp4,8_pp2,4_pp2,16_pp1}_decode_capped100g` (CAPPED_100G · 8K Decode · NOT_CAPTURED); reason "Deferred in favor of empirical E2E benchmark runs and iperf3 validation" | Profiler provenance table and coverage matrix | Planned: 8 capped points, all 128K prefill (`V8_FULL_RELEASE.json`: `capped_100g_20g_prefill128k: 8`; the runner `21_run_vllm_capped_profiles.sh` says "capped modes capture only the matched 128K prefill point for all four topologies" and loops over 100g and 20g). Captured: TP4/PP2, TP8/PP2, TP4/PP4 at 100G. Missing: TP16 at 100G; all four at 20G (the archive has no 20G profile folder). No reason recorded. These are plan B10. |
| P3 | "8 / 8" in both node-capture columns on the TP4/PP2 rows; capped TP4/PP2 and capped TP8/PP2 both say "Complete 16-rank dual-node capture under configured 100G bandwidth cap" | Coverage matrix | TP4/PP2 is 4 + 4 ranks (capped: 8 of 8 usable). Capped TP8/PP2 has 15 of 16 usable. |
| P4 | PR-005's 128K stage-0 composition (AllReduce 40.0 %, FlashAttention 22.8 %, MoE 13.2 %) matches no per-rank export; KD#3's share columns and secondary chart reuse it; its 512K column is a stage-1 rank | Drawer PR-005; KD#3 page; Key Finds hero #3 chart | Stage-0 ranks at 128K: AllReduce 24.5–32.8 %, FlashAttention 5.4–6.0 %, MoE 5.2–5.8 %, start-up Broadcast 40.0–44.6 %. Use the §6.1 16-rank aggregates. |
| P5 | PR-006 (TP16 512K) shows TP4/PP4's growth factors (15.7× / 3.9× / 3.8×) and not its 1-of-12 usable ranks | Drawer PR-006 | Say "1 of 12 rank exports usable; no composition claimed". |
| P6 | Repeatability examples mislabelled: "Deltas of ±0.10% (e.g. 100G cap at 128K)"; "+3.91% (TP4/PP4 at 20G, 128K)" | Scale-Out | The deltas closest to ±0.1 % are TP8/PP2 at 1M (−0.13 / −0.10 %) and TP4/PP2 at 1M under 100G (+0.13 %); at 128K the 100G deltas run from +0.66 to +51.6 %. +3.91 % is TP4/PP4 at 1M (128K is +14.67 %). |
| P7 | "exceeds GEMV savings (+39.8 µs/call over 6,985 decode steps)"; tooltip "TP8 decode GEMV is 66.9ms faster" | Profiler operator card and chart tooltip | GEMV 171.2 → 126.5 ms (−44.6 ms). AllReduce decode-only 132.3 → 409.9 ms: +277.5 ms (277.6 from the rounded totals), i.e. 18.9 → 58.7 µs per call over 6,985 calls in 127 steps. |
| P8 | "While offload was disabled … mathematically certain"; offload card "Excluded from execution scope"; D2H 56.6 GB/s | Long Context, Scheduler | Offload runs failed to start (rc=1). 0.14 s is a bandwidth estimate (plan B9). D2H 452.37 GB/s / 8 = 56.5 GB/s. |
| P9 | TP16 AllReduce share range 74.8–79.5 % (PR-004) vs 75.1–78.9 % (chart) | Profiler | 12 usable ranks: 76.3–79.5 %, mean 77.6 %. |
| P10 | "19 μs vs 37 μs … 1.95×" (KD#7 Layer A, PR-002/003 observations) vs 37.6 µs elsewhere | Key Finds, drawers | nccl-tests 16 KiB TP8 rows: 37.03 / 37.61 / 37.61 µs; TP4 19.66 / 19.04 / 19.04 µs. Use 37.6 vs 19.0 µs = 1.98×. |
| P11 | Under "Not established / Unresolved": "decode profiles in graphs-on mode (captured in eager mode only; serving operates with CUDA Graphs ON)" | Executive Campaign Scope | Single-node graphs-on decode profiles exist (`profiles_torch_single_node/`, TP4 and TP8 at 8K); two-node decode is what's missing. |
| P12 | §4.4 table "≈ 50 %" at 8K; "intra-node TP prefill spends 14–50 %" | Executive | 0.12 / 0.222 = 54 %; single-node TP range in §4.17 is 16–57 %. |
| P13 | "1M decode is 54 % KV read" | Executive, Long Context, Profiler tiles | That is the memory floor: 5.59 of 10.27 ms in the time-budget row, KV ≈ 45 % + weights ≈ 9 %. Say "54 % memory-speed floor, mostly KV read". |
| P14 | "Reported GPU SM Util (%)" axis; "Prometheus GPU SM utilization telemetry" | KD#9 | `gpu_util_mean_pct` comes from the pilot's `09_metrics_sampler.py`, which polls nvidia-smi `utilization.gpu` every 0.5 s: the share of time a kernel was running, not SM occupancy. |
| P15 | Artifact paths that are not in the archive. Drawer `artifact_path`: PR-001 `results_V8_runs(3)/hardware_processed/nsight_tp4_prefill/cuda_gpu_kern_sum.csv`; PR-004/005/006 `results_V8_runs(3)/hardware_processed/distributed_profiles/…/PROFILE_VALIDATION.json`. The "Raw Artifact Paths" lists that drawers linked to a finding show (from the discovery maps): 26 of the 28 distinct paths, e.g. `vllm_single_node_v6_matrix/tp4_qualification/tp4_qualification_8k_c1.json`, `profiles_torch_single_node/tp4_8k_decode/pytorch_profiler.json`, `scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_128k_c1_native.json` | Drawers (Measured Telemetry and Raw Artifacts tabs) | `hardware_processed/` holds eight summary files and no subfolders; the captures are in `profiles_single_node/tp4_prefill/` and `profiles_multi_node_native/<layout>_dist/<point>/`. Run files sit at `<matrix>/<case>/<bench>/<bench>.json` (e.g. `vllm_single_node_v6_matrix/tp4_qualification/8k_c1/8k_c1.json`; scale-out runs under `vllm_scaleout_network_matrix/<network>/results/<layout>/<layout>/<bench>/`). Of the paths a reader can follow, only PR-007's, `hardware_processed/nccl_points.csv` and `final_validation/SCALEOUT_TELEMETRY_AUDIT.json` resolve; the case-manifest paths on the 119 completed EV runs do. |
| P16 | "across 112,640 traced kernels" (composition-card subtitle; PR-001's rule, which adds "validated with torch.profiler") | Profiler, drawer PR-001 | 112,640 is the TP4 eager decode capture's AllReduce call count. The TP4 128K prefill capture behind PR-001 has 84,456 kernel launches (5,060 AllReduce), and there is no torch profile of prefill: the torch captures are 8K decode only. |
| P17 | Topology × Network Sensitivity heatmap TTFT cells | Scale-Out | 21 of the 36 TTFT cells (all TP4/PP2 and TP8/PP2 cells, three TP16 cells) differ from `combined_vllm_runs.csv` by 0.7–3.3 ms, e.g. TP8/PP2 128K native 2.791 s against 2.788 s. One delta follows: TP8/PP2 128K at 100G is +1.36 % (shown +1.37 %). Small (≤ 0.12 %), but these cells do not trace to the archive; regenerate them from the CSV. |

## 6. Corrections to v1.2

| # | v1.2 said | Correct |
|---|---|---|
| C1 | The qualifier "7 with usable exports (all prefill)" (item 3) — the build copied the 7 | **8**. Native: TP4/PP2 128K 8/8, TP8/PP2 128K 15/16, TP4/PP4 128K 16/16, TP4/PP4 512K 16/16, TP16 128K 12/16. Capped 100G: TP4/PP2 8/8, TP8/PP2 15/16, TP4/PP4 16/16. Plus TP16 512K with one rank. v1.2's own §6 table listed TP8/PP2 at 15/16, and the magnifying-glass note's D7 100G check uses the three capped captures. |
| C2 | NOT_RUN → "no reason recorded" | The case manifests do record a reason: `RuntimeError('server exited rc=1')`, 126–134 s after start, with no server log kept. Use "attempted; server failed to start (rc=1); cause not logged" for all 7. |
| C3 | Item 23, from §4.14 of the master review v1.2: "16K wins both axes at these points" (a Pareto) | At 128K c4, 16K has the lowest mean TPOT (105.1 vs 119.3 ms) but a 2 % higher TTFT than 8K (10.88 vs 10.66 s) and about the same p95 TPOT (207 vs 212 ms; 4K: 161 ms). It cuts stalls > 100 ms from 313 to 141 but makes each one longer (median 270 → 537 ms). Write "16K is the better default for ≥128K prompts: lowest c1 TTFT at 128K–1M and lowest c4 mean TPOT; not dominant on every axis". |
| C4 | The §4.17 tables are "on the Long Context & 1M tab" | They are the first card of the Scheduler & KV tab, in both builds. |
| C5 | "the hardware-only 50G/10G facts (…) are now nowhere on the Scale-Out tab" | The iperf rows (33.0 / 9.0 Gb/s, "HW QUALIFIED / RUNS DEFERRED") are on the network table. What is absent is SendRecv 4.09 / 1.11 GB/s and cross-node AllReduce 223–319 µs at those caps. |
| C6 | Item 2 listed PR-002/003's "251.5 / 583.9 ms" among the "Eager decode numbers still presented as evidence" | They are not eager. They are the graphs-on torch profile's AllReduce totals for the whole capture: 7,040 calls = 55 in the prefill step + 6,985 decode calls (TP4 119.2 + 132.3 ms, TP8 174.0 + 409.9 ms). What was wrong with them was the prefill step's 55 large calls mixed into a decode figure, not the mode. The 5 Oct build took v1.2's word and labels them eager (N21). |

## 7. What closes it, in order

1. **Evidence tab (B1–B4).**
   * Replace the readiness panel's stack, defect 2, and NOT_RUN / NOT_CAPTURED reasons with the archive values above.
   * Restore the ledger card tag, fill Warmup/Prompts on all 126 rows from the CSV, and fill or drop Cold Load.
   * Apply the same NOT_RUN wording to the global banner, the Executive tiles, the Long Context FP8 card and the Scheduler offload card.
2. **Time-budget charts (B5).** Embed or redraw the four charts, and make the CSV paths match.
3. **Key Discoveries renderer (B6).** Render `confidence_note` and `scope_note`, or fold them into `confidence.notes` and the scope rail. Then remove what they replace: KD#6 "6 scale-out topologies", KD#9 "Prometheus GPU SM utilization" (and the chart axis).
4. **KD#3.** Change the hero card, table row and primary chart to SendRecv 4.5× / AllReduce 2.7× with times (4.31 → 19.29 s, 12.44 → 33.75 s; 16-rank sums; start-up Broadcast excluded; nsys, eager). Replace the share columns and secondary chart with the §6.1 aggregates.
5. **The new wrong statements.**
   * Stage waits (N5), on all three surfaces.
   * KD#6 energy (N6).
   * KD#1 boundary and mechanism (N7).
   * PP2 layers (N8).
   * Heatmap and verdict labels (N9).
   * PR-002/003/007 numbers, the "eager" label on the torch totals and the dead artifact path (N10, N12, N21, N22).
   * The "Pareto" wording on the Executive knobs row and KD#8 (C3).
6. **Key Finds tab (B7).** Port the explorer text into TOP 2/3/4/5/8/9/10, or hide the tab until it is ported.
7. **Coverage matrix.**
   * Status from usable exports on the four remaining rows.
   * Capped rows rewritten to the planned 20G prefill points (P2) and node counts fixed (P3).
   * "14/22 … COMPLETE" chip → "14/22 captured · 8 with usable exports".
8. **Findings wording (N16).** "Predicted; plan A1 checks it." "First tokens at 0.23 / 0.65 / 0.87 / 0.88 s." "Expected under uniform routing (upper estimate)."
9. **Clicks and duplicates.**
   * The KD "Inspect Evidence" map (P1).
   * `prMap` (N15).
   * Chips (N14).
   * Duplicate mode badge (N11) and duplicate KD#7 pointer (N13).
10. **Small numbers.** Queue values (N17); 37.6 µs / 1.98× (P10); GEMV 44.6 ms (P7); heatmap TTFT cells (P17); artifact paths (P15); "112,640 traced kernels" (P16); TP16 range (P9); repeatability examples (P6); §4.4 54 % (P12); D2H 56.5 (P8); the floor label (P13); Executive scope line (P11); "Exact 7040" → "6,985 decode calls"; the Executive TP4 row's "CROSS-VALIDATED" tag; K9 tokens axis; K7 p95; Profiler P8, P9 and P13 from v1.2.

Items 1–3 are what make the build safe to share; 4–6 make the ten findings agree with each other on every tab; the rest is finish.

*Method: as at the top. Numbers recomputed with the same scripts and classification as v1.2:*

* *Kernel shares: `cuda_gpu_kern_sum.csv` per rank, usable = header plus at least one row. Stages are assigned by AllReduce instance count (TP4/PP4: 423 / 395 / 395 / 339 at 128K; 1,143 / 1,067 / 1,067 / 915 at 512K).*
* *Queue: `queue_mean_s_from_hist`. Energy: `gpu_node_stats_json`. Versions: `logs/readiness_node0/V8_READINESS.json` (node 1 identical).*
* *NOT_RUN: the three `case_manifest.json` files. Capped plan: `V8_FULL_RELEASE.json` `profile_breakdown`.*
* *Rendering: Chromium via Playwright, viewport 1600 px, Chart.js 4.5.1.*
* *Composition shares: kernel names grouped as flash → full attention; moe / topk / expert → MoE; kda / gated_delta / causal_conv1d / recurrent → KDA; gemm / gemv / cutlass → GEMM; start-up Broadcast left out of the denominator. This regenerates all 56 cells of the six-layout table.*
* *Torch totals: `profiles_torch_single_node/tp{4,8}_8k_decode/torch/profiler_out_0.txt` (rank 0); the prefill step is the `vllm::all_reduce` row.*
* *Energy: J per 1K tokens = summed GPU power × duration ÷ (total-token throughput × duration ÷ 1,000); every row of the §4.6 panel reproduces.*

## 8. What changed from v1.3

v1.3 was re-checked claim by claim against the HTML, the dashboard code and the archive. The verdict, the eight blockers and the status counts stand. These v1.3 statements were wrong or loose, and are corrected above:

| Where | v1.3 said | v1.4 says |
|---|---|---|
| §2.8 composition chart, N15 | The TP8/PP2 and TP4/PP4 bars open nothing | They open EV-001, the pop-up's fallback (clicked in the browser). The two eager decode bars open PR-002/003, now graphs-on drawers |
| §0, B6, §3.4 | Four fixes sit in fields the renderer never reads | Three of them would change the screen (KD#2 scope note, KD#6 confidence, KD#9 telemetry); the other dead fields repeat visible text. KD#3's "nsys only, eager mode" is visible in its takeaway |
| §0, B4 | Every row is one column out of line | The 23 rows with a value are one cell short, the other 103 two |
| B5 | ~2 MB | 2.0 MB of PNG, about 2.7 MB as base64 |
| §2.2 hero #3 | The FlashAttention line is single-rank | Its 128K point is from another set-up: the single-node TP4/PP1 capture, filed under the TP4/PP4 evidence ID |
| §2.3 KD#5 | 24,977 vs 13,967 are usable prompt tokens/s | They are prompt + output tokens; prompt tokens alone give 24,220 vs 13,940 (1.7×) |
| §2.3 KD#9 | Samples come every ~0.4–0.55 s | The case files set 0.5 s; sample counts give a median of 0.46 s |
| §2.3 KD#10 | 0.9 on all 19 server commands checked | 43 of 44 case manifests and 60 of 61 `SERVER_COMMAND.txt` files; the offload case is the exception |
| §2.5 repeatability, P6 | The ±0.1 % deltas are TP8/PP2 at 512K and 1M; TP8/PP2 128K at 100G is +1.37 % | TP8/PP2 at 1M and TP4/PP2 at 1M under 100G (512K is −0.18 / −0.19 %); +1.36 % |
| §2.5 heatmap | All 24 deltas match | 23 of 24; 21 TTFT cells are 0.7–3.3 ms off (P17) |
| §2.7, N17 | TP4/PP2 512K queue 0.024 ms | 0.023 ms (0.0235; the Scale-Out matrix shows 0.023) |
| §2.8 six-layout table | 49 cells | 56 cells, all re-derived from the rank exports |
| §2.8 E2E·D caption | 86–98 % at c ≥ 4 / c ≥ 2 | Closed-loop rows only; the 128K open-loop rows are 76 % and 90 % |
| §2.8 operator card, P7 | GEMV saving 44.7 ms; +39.8 µs × 6,985 calls = +277.6 ms | 44.6 ms; +277.5 ms = 39.7 µs × 6,985 (44.7, 277.6 and 39.8 come from rounded inputs) |
| §2.1, P13 | KV ≈ 46 % of the 1M token | ≈ 45 % (4.66 of 10.27 ms) |
| B3, N3 | `coverage.json` has_gate False | True of the 7 NOT_RUN entries; 22 completed entries are gated |
| N10 | TP8 GEMV / MoE split given without a source | Marked as taken from Master review v1.2 §4.3 |
| Throughout | Several dashboard quotes paraphrased | All quotes verbatim |

Added in v1.4: N21 and N22 (new errors in this build), P15–P17 (older defects), C6 (v1.2 called the torch totals eager), and the 16-stream iperf nit on the fabric line.

