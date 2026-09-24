# 04 — Acceptance checklist (Spec §16) with per-phase reporting

The agent must fill this in at the end of **every phase**, using only **PASS / FAIL / BLOCKED / N-A-YET** and one line of evidence (file + line, or screenshot name). "BLOCKED" means the data needed does not exist in the workspace; it is not a failure and must not be papered over.

| # | Criterion | Phase(s) that affect it | Status | Evidence |
|---|---|---|---|---|
| 1 | No chart contains a numeric point that cannot be resolved to an evidence row or an explicitly DERIVED formula | 1, 2, 3, 4, 5, 6 | | |
| 2 | No missing/not-run condition is rendered as zero | 1–8 | | |
| 3 | All 1M panels distinguish baseline c1, TP4 closed-loop c1/c2/c4, chunking, missing offload, and absent/not-configured scale-out coverage | 4 | | |
| 4 | TP16/PP1 and forced TP4/PP2 topology diagrams correctly reflect cross-node communication semantics (see Spec §9.1) | 5 | | |
| 5 | Every scale-out result shows rank placement and network provenance next to the performance result (BLOCKED if manifests absent; then show NOT CAPTURED) | 5 | | |
| 6 | Profiler page contains no precise decomposition percentage until trace-derived attribution is available | 7 | | |
| 7 | Hardware label is RTX PRO 6000 Blackwell Server Edition, 96GB GDDR7, PCIe Gen5; no Ada/48GB/Gen4 residue anywhere (grep the whole file) | 1, 7 | | |
| 8 | Percentile charts enforce N thresholds (P95 N≥20, P99 N≥100) and show N in tooltips | 6 | | |
| 9 | Every chart uses Observation / Interpretation / Decision / Next evidence language | 2–7 | | |
| 10 | Evidence tab displays suite revision and coverage counts by group | 8 | | |
| 11 | Clicking a chart point can navigate to its evidence row/raw source | 8 | | |
| 12 | Absolute 48B surrogate latency/tok/s is never presented as Kimi K3 performance | 1–8 | | |

## Extra mechanical checks the agent should automate (not in the report; added for verification)

- [ ] `grep -iE "ada|48 ?gb|gen ?4|6000 Ada"` on the HTML returns nothing relevant.
- [ ] `grep -iE "proves|superiority|best|recommended|sweet spot|100% passed"` returns only occurrences that are scoped by workload + objective, or none.
- [ ] No numeric array literal in `<script>` feeds a chart. All chart data is loaded from the evidence JSON.
- [ ] Row count in the Evidence tab = 59 (plus any multi-node rows, shown under a separate source selector).
- [ ] Every rendered chart point has a `row_id` reachable from its tooltip or click handler.
- [ ] Removed profiler percentages (74.2%, 21.8%, 11.2%, 14%, 12.6%, 8.2%, 48/22/8/14/8) are absent from the DOM.
- [ ] Removed claims (22.4GB/s, <0.04ms scheduler overhead, <1.8% fragmentation, 49.2% KV, 14.4s at 90% hit, ~350K crossover) are absent or re-stated as DERIVED / NOT CAPTURED.
