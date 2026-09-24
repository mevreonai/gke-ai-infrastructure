# 03 — Chart map: which rows feed which chart

Purpose: stop the implementing agent from guessing. Every figure in the report is listed with its exact data source. Row IDs use the format `case::bench` and resolve to `02_evidence_rows.csv`.

> **Rule that prevents silent errors: key on `case`, not on (TP, context, concurrency).**
> 11 (TP, input, concurrency) cells appear under more than one case, sometimes with different configs. Example, TP4 / 128K / c1 TTFT (ms):
> `tp4_qualification` 4534.1 · `tp4_context_baseline` 4540.8 · `tp4_prefill_focus` 4542.1 · `tp4_chunk4k` 5235.5 · `tp4_chunk8k` 4544.5 · `tp4_chunk16k` 4366.5 · `tp4_closedloop_128k` 4538.8.
> Each chart below names its source case. Never average across cases and never pick "whichever row matches first."

---

## A. Charts that exist in the report (Figures 1–11)

| Fig | Title | Plots | Source rows | Values (from CSV) | Problem in current UI | Required fix |
|---|---|---|---|---|---|---|
| 1 | Case coverage | Horizontal bars, configured vs present, by test group | **Case manifest not in this package.** Group counts in `02b_chart_only_values.csv` (pixel-measured) | Long context 33/39; KV dtype 0/3; Offload 0/3; all other groups fully present | Group taxonomy overlaps and does not partition 59/64; "Concurrency" reads 17 in the figure but 15 by case-name prefix | **UNRESOLVED.** Rebuild from the real case manifest (`10_vllm_surrogate_cases.json`) and state the taxonomy. |
| 2 | Baseline TTFT vs context (log-log) | x = input tokens (K), y = TTFT (s), two lines TP4/TP8 | `tp4_context_baseline::{8k_c1,128k_c1,512k_c1,1m_c1}` and `tp8_context_baseline::{same}` | TP4: 0.222, 4.541, 31.979, 93.385 s · TP8: 0.268, 4.824, 28.167, 74.850 s | Invented 32K/64K/256K markers; "~350K crossover" | Only 4 measured points per line. Crossover = "observed bracket 128K–512K"; any fitted crossover is DERIVED and dashed. |
| 3 | Baseline TPOT vs context | Same axes, y = TPOT (ms/token) | Same 8 rows as Fig 2 | TP4: 4.45, 5.10, 7.56, 10.24 · TP8: 6.33, 7.05, 9.44, 12.07 | — | TP4 lower TPOT, TP8 lower TTFT at 512K/1M: state as prefill-vs-decode trade-off, not a winner. |
| 4 | 8K TP4 throughput: Evidence vs UI JS | Grouped bars c1/c4/c8/c16/c32 | `tp4_closedloop_8k::{c1,c4,c8,c16,c32}` | Evidence: 187.6, 415.3, 559.7, 673.2, 774.4 tok/s · UI JS (approx, pixel-measured): 188, 483, 553, 838, 1118 | UI overstates c4 by ~16%, c16 by ~24%, c32 by ~44% | Delete the embedded array; bind to the 5 rows. Tooltip: N, output length, "closed-loop". |
| 5 | 128K capacity knee | Dual axis: output tok/s (solid) and TPOT (dashed) vs concurrency | `tp4_closedloop_128k::{c1,c4,c8,c16}` | tok/s: 24.7, 27.2, 28.0, 28.2 · TPOT: 5.11, 64.37, 186.98, 242.85 ms | Reads like scaling | Annotate as latency-throughput trade-off, not scaling and not "max users." |
| 6 | Long-context TPOT under concurrency | x = concurrency (1,2,4), y = TPOT, lines 512K and 1M | `tp4_closedloop_512k::{c1,c2,c4}` and `tp4_closedloop_1m::{c1,c2,c4}` | 512K: 7.56, 367.40, 433.95 · 1M: 10.20, 239.25, 267.69 ms | Not headline | Place above the fold on Long Context and Scheduler & KV. Throughput is flat (512K = 2.0, 1M = 0.3 tok/s). |
| 7 | 1M TP4 c1 chunk sweep | Bars: 4K, 8K, 16K TTFT | `tp4_chunk4k::1m_c1`, `tp4_chunk8k::1m_c1`, `tp4_chunk16k::1m_c1` | 122.10, 93.38, 89.16 s | "8,192 sweet spot" claim | Finding = "16K lowest 1M c1 TTFT among 4K/8K/16K" plus workload/SLO caveat (no concurrent-decode evidence). |
| 8 | 1M TP4 closed-loop | Dual axis: TTFT (s, solid) and TPOT (ms, dashed) vs c1/c2/c4 | `tp4_closedloop_1m::{c1,c2,c4}` | TTFT: 93.46, 150.65, 231.50 s · TPOT: 10.20, 239.25, 267.69 ms · KV: 12.3, 15.5, 15.5% | c4 shown as 49.2% KV elsewhere | Headline Long Context chart. KV = 15.5% at c4. |
| 9 | Scale-out 128K TTFT | Bars: TP4/PP4, Forced TP4/PP2, TP8/PP2, TP16/PP1 | **None in the 59 rows.** Approx values in `02b_chart_only_values.csv` | ~1722, ~2642, ~2813, ~6028 ms (pixel-measured, ±12) | Values are "current UI values pending raw production validation" | Keep that label until each bar links to run manifest, rank placement, network fingerprint, source JSON. Badge MEASURED-48B once validated. |
| 10 | Scale-out throughput | Same 4 bars, output tok/s | **None in the 59 rows** | ~30.8, ~21.4, ~19.5, ~9.4 tok/s (pixel-measured, ±0.1) | "PP masks network latency" causal claim | Observation + medium-confidence interpretation + trace requirement. Do not infer masking from throughput alone. |
| 11 | 128K KV utilization: Evidence vs UI JS | Grouped bars c1/c4/c8/c16 | `tp4_closedloop_128k::{c1,c4,c8,c16}` `kv_peak_pct` | Evidence: 1.6, 6.5, 13.1, 14.6% · UI JS: ~1.9, ~7.4, ~14.7, **29.44** | UI scales values synthetically | Use exact `kv_peak_pct`. No multiplication or extrapolation. |

**Other numeric panels in the report (not figures):**

| Panel | Source rows |
|---|---|
| §8 1M table (9 rows) | `tp4_context_baseline::1m_c1`, `tp8_context_baseline::1m_c1`, `tp4_prefill_focus::1m_prefill`, `tp4_chunk{4k,8k,16k}::1m_c1`, `tp4_closedloop_1m::{c1,c2,c4}` |
| §10 max_num_seqs sweep | `tp4_512k_maxseq4::512k_c4`, `tp4_512k_maxseq8::512k_c4`, `tp4_512k_maxseq16::512k_c4` |
| §10.1 prefix cache | `tp4_prefix128k::prefix128k`, `tp4_prefix512k::prefix512k` |
| §10.1 observer overhead | `tp4_observer_{minimal,full}::{8k_c8,128k_c4}` |

---

## B. Charts the report *requires* — can they be built from the data in this package?

> *This table is the package author's derivation from data availability, not a statement from the report. Verify in Phase 0.*

| Required chart / panel | Spec § | Status | What decides it |
|---|---|---|---|
| Throughput-vs-TPOT Pareto scatter | 6 (P1) | **BUILDABLE** | `output_tok_s` vs `tpot_ms` for all closed-loop rows. Long-context tok/s is 0.3–2.0, so use per-context panels or a log axis. |
| Capacity knee markers | 6 (P1) | **BUILDABLE** | 8K (`closedloop_8k`), 128K, 512K, 1M closed-loop sweeps. Mark where throughput gain flattens while TPOT/TTFT rises. Never label "max users." |
| Capacity heatmap (context × concurrency) | 10 (P1) | **BUILDABLE** (TP4 only) | Cells only where a row exists; **gray = NOT RUN**. Must declare which case feeds each cell (see duplicate-cell rule above). |
| `max_num_seqs` 4/8/16 dedicated chart | 10 (P1) | **BUILDABLE** | 3 rows. Finding: nearly identical TTFT/TPOT/KV, so `max_num_seqs` was not the limiter in this range. |
| Observer-overhead delta panel | 10.1 | **PARTIAL** | Percentage deltas can be computed (DERIVED). **N and run-to-run variance are NOT CAPTURED** in the data, so no blanket correction may be applied. |
| Coverage strip / Evidence coverage KPIs | 5, 12 | **PARTIAL** | Known: 64 configured, 59 present, 6 absent (3 FP8-KV + 3 native-offload), 1 extra (`tp4_closedloop_1m::c4`), all 59 status COMPLETED. **Failed / safety-skipped / gated / started counts are NOT in the report → NOT CAPTURED.** |
| Data-freshness card | 5 | **PARTIAL** | Not in package: last-run timestamp, suite_version, git SHA, case-manifest hash, model revision, run's vLLM version, profiler status. Render NOT CAPTURED for each. |
| Prefix cold-vs-hit chart | 10.1 | **BLOCKED** | Only 2 aggregate rows exist. Need first/cold vs repeat requests, reused/computed token counts, hit mechanism. |
| Percentile (P95/P99) charts | 10 | **BLOCKED** | Rows carry one unspecified statistic per metric, no p50/p95/p99, no N. Gate: P95 needs N≥20, P99 needs N≥100. |
| Regime-change panel (per-chunk iteration time vs accumulated context) | 8 (P1) | **BLOCKED** | Needs per-prefill-chunk iteration timing, GPU util, scheduler time, offload bytes/time, NCCL contribution. |
| Open-loop request-rate page | 10 (P1) | **BLOCKED** | No RPS runs exist. Render NOT RUN placeholder only. |
| AllReduce / NCCL primitive graph | 6 | **BLOCKED** | Requires V4/NCCL or Nsight data (not attached). Badge MEASURED-GCP-HW; separate time / algbw / busbw. |
| Scale-out: 512K selector, TP16/PP1 512K | 9 (P1) | **BLOCKED** | Show **NOT RUN** unless executed. Only 4 topologies at 128K c1 are known, and only approximately. |
| Scale-out: placement audit, per-node balance, network fingerprint | 9 (P1) | **BLOCKED** | Needs multi-node manifests (rank→node→GPU UUID→PCI→NUMA), per-GPU util/mem/power, zone/interface/MTU/RTT/iperf/NCCL transport. |
| Profiler timeline, attribution, trace completeness | 11 | **BLOCKED** | No trace data attached. Render the equation and an *unresolved ledger*; **no percentages**. PP = N/A on PP1. |
| 1M offload (native), FP8-KV | 8, 12 | **NOT RUN / NOT SURFACED** | The 6 absent configured cases. Report does not say whether they were run; treat that as UNRESOLVED. |
| 1M multi-node | 8 | **NOT CONFIGURED** | Not part of the multi-node case matrix. |

---

## C. Annotation template (must sit under every chart)

```
Observation:        <literal measured result, with numbers>
Interpretation [High|Medium|Low]: <plausible mechanism>
Decision:           <workload-scoped implication - name the context/concurrency/objective>
Next evidence:      <trace/test needed to confirm causality>
Evidence:           <evidence_class> · <run IDs / row_ids> · N=<sample_count or NOT CAPTURED>
```

**Worked example, Fig 5:**
```
Observation:        At 128K, closed-loop c1→c16 raises output throughput from 24.7 to 28.2 tok/s (+14%)
                    while TPOT rises from 5.11 to 242.85 ms/token (~47x).
Interpretation [Medium]: Throughput is saturating while per-request decode latency degrades - consistent
                    with queuing/contention at high concurrency; mechanism not yet isolated.
Decision:           For 128K workloads with a TPOT SLO, the useful operating point is well below c16.
                    This is not a "max users" figure.
Next evidence:      Scheduler running/waiting queue traces and preemption counts at c4/c8/c16;
                    open-loop RPS run.
Evidence:           MEASURED-48B (pending raw re-validation) · tp4_closedloop_128k::{c1,c4,c8,c16} · N=NOT CAPTURED
```
