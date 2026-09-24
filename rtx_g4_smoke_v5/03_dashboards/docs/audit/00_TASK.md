# TASK: Remediate the V6 vLLM Characterization Dashboard

You are modifying `MASTER_CHARACTERIZATION_DASHBOARD.html` (2,523 lines, 7 tabs: Executive, Scale-Up, Scale-Out, Long Context, Scheduler & KV, Profiler, Evidence). An engineering audit found that it presents hard-coded, interpolated, or illustrative values as measured data. Your job is to fix the UI to the audit spec **without inventing any data**.

Hardware target: NVIDIA RTX PRO 6000 Blackwell Server Edition, 96GB GDDR7, PCIe Gen5. Model: Kimi-Linear-48B-A3B-Instruct (a 48B surrogate).

## Files (in `docs/audit/`, read in this order)

1. `README.md`: what each file is.
2. `01_spec.md`: **authoritative requirements.** Every P0/P1 item, table, and rule.
3. `02_evidence_rows.csv` / `.json`: **single source of truth for numbers** (59 rows).
4. `02b_chart_only_values.csv`: values that exist only inside chart images (approximate; NOT authoritative).
5. `03_chart_map.md`: which rows feed which chart, and which required charts are buildable vs blocked.
6. `04_acceptance_checklist.md`: the pass/fail gate you report against after every phase.
7. `figures/`: the report's 11 figures. **Visual reference only.** If a figure and the CSV disagree, the CSV wins.
8. `original.pdf`: fallback if any Markdown looks wrong.

Before doing anything else, reply with a 10-line summary in your own words of: the non-negotiable rules, the 7 tabs, the evidence-class taxonomy, and what "BLOCKED" means. If anything in the files is contradictory or unclear, list it. Do not guess.

## Non-negotiable rules

1. **No number on any chart unless it resolves to a `row_id` in the evidence data**, or to an explicit DERIVED formula drawn dashed and badged DERIVED.
2. **Missing data is shown as `NOT RUN` or `NOT CAPTURED`. Never 0, never interpolated, never "plausible filler."**
3. **Never invent or estimate a value.** If a number you need is not in the files or the HTML, stop and add it to an UNRESOLVED list.
4. **Key chart data on `case`, not on (TP, context, concurrency).** Multiple cases share those cells with different configs (see `03_chart_map.md`). Never average across cases.
5. Hardware label everywhere = RTX PRO 6000 Blackwell Server Edition / 96GB GDDR7 / PCIe Gen5. Remove all Ada / 48GB / Gen4 text.
6. Closed-loop concurrency is **never** "users" or "max users."
7. Do not use "best", "proves", "recommended", "superiority", "sweet spot" without an explicit workload + objective. Prefer measured, scoped phrasing.
8. Every chart gets this annotation: **Observation → Interpretation [High/Med/Low] → Decision (workload-scoped) → Next evidence → Evidence (class + row_ids + N).**
9. Evidence classes: `MEASURED-48B` (model/vLLM), `MEASURED-GCP-HW` (hardware/fabric/NCCL primitive), `DERIVED`, `LOCAL-REAL`, `UNRESOLVED`. Never mix `MEASURED-48B` with `MODELED-K3`.
10. Only the 8 qualification rows are raw-validated. Every other value stays labeled **"current UI value pending raw re-validation"**. Scale-out and profiler numbers especially.
11. Keep the 7-tab structure. Do not redesign the whole UI.
12. Profiler: keep the equation `T = A_GPU + B_TP + C_PP + D_PCIe/offload + E_vLLM + F_CPU/launch + G_other − O_overlap`, remove all precise percentages, show an unresolved ledger. PP = N/A on any PP1 profile.

## Phases: do them in order and STOP at the end of each

**Phase 0 (audit only, NO code changes).**
- Inventory the HTML: every hard-coded data array, every hardware string, every claim listed in Spec Appendix A. Produce a findings table: `location (line) → problem → spec item → planned fix`.
- Extract the real embedded Evidence rows from the HTML and **diff them against `02_evidence_rows.csv`**. Report every mismatch. Confirm or refute: 59 rows, the 8K TP4 throughput divergence (Fig 4), the 29.44% KV value (Fig 11).
- Extract the real scale-out values (Figs 9–10) from the HTML and compare with `02b_chart_only_values.csv`. Report the exact numbers.
- List everything the spec requires that the workspace has no data for (use `03_chart_map.md` §B as the starting point).
- Wait for my "go".

**Phase 1: Global P0.** Hardware identity; single evidence data layer (`data/evidence.json` or equivalent) that every chart loads from; badge taxonomy; header shows latest-run timestamp + build time and "Live" only when polling; revision-drift fields (suite_version / git SHA / manifest hash → NOT CAPTURED if absent).
**Phase 2: Executive.** Spec §5.
**Phase 3: Scale-Up.** Spec §6–7 (measured-only points, crossover bracket, Pareto, capacity knee).
**Phase 4: Long Context (1M).** Spec §8 (headline closed-loop chart, chunk finding, KV in %, missing coverage).
**Phase 5: Scale-Out.** Spec §9 (correct TP16/PP1 and forced TP4/PP2 diagrams, remove universal verdict and network causality, NOT RUN for 512K).
**Phase 6: Scheduler & KV.** Spec §10 (exact KV values, max_num_seqs chart, percentile gates, NOT CAPTURED for scheduler overhead / fragmentation).
**Phase 7: Profiler.** Spec §11.
**Phase 8: Evidence tab.** Spec §12 (coverage by group, provenance columns, revision drift, click-through from chart points).
**Then P1 items,** only after all P0 items pass.

## End-of-phase report (required, in this format)

```
PHASE N: <name>
Files changed: ...
Spec items completed: <ids>
Spec items NOT completed and why (BLOCKED = data absent; do not fill in): ...
Checklist (04_acceptance_checklist.md): PASS/FAIL/BLOCKED/N-A-YET per row, one line of evidence each
New UNRESOLVED items: ...
Screenshots: <one per affected tab>
```

## Verification

- After each phase, load the page in a browser and screenshot each affected tab. Compare against the relevant `figures/` image: shape and ordering should match; numbers must come from the CSV.
- Add a check (script or test) that fails if any chart data is a literal array in `<script>` rather than loaded from the evidence data.
- If the spec and the data conflict, **stop and ask**. Do not resolve it silently.
