# V8-FULL Team Handoff Prompt — Native-Only Campaign Dashboard Migration — UI V4 Full Configuration Identity

**Audience:** the engineering team that previously ran the RTX PRO 6000 GCP hardware/smoke suite (V4 lineage), ran the V6 vLLM characterization suite, and built the existing hardware + vLLM dashboards.

**Primary goal:** after the V8-FULL run finishes, update the existing dashboards so that every number, chart, status, and conclusion is driven from the V8-FULL result tree and can be traced back to raw evidence.

**Important:** do not redesign the measurements. V8-FULL deliberately preserves the working V6 execution path where possible and adds hardware/fabric, deeper 1M, distributed profiling, provenance, and validation around it. The dashboard work is mainly a **data-contract + UI migration**, not a new benchmark design.

### Campaign-scope update: `GCP_NATIVE` only

Because the available lab window was limited, the V8-FULL execution was narrowed to **native network only** for all network-dependent hardware, scale-out vLLM, and distributed profiler work. The originally planned 100G/50G/20G/10G capped sensitivity runs were not executed.

This must **not** reduce dashboard quality or omit any measured V8 evidence. Keep `network_provenance` as a first-class schema field, but for this campaign the only measured network state is `GCP_NATIVE`. Capped modes are a future extension / unresolved sensitivity question, not data to synthesize.

---

# 0. Read this first — non-negotiable rules

1. **Do not hard-code benchmark values into the HTML/JS.** Every plotted point must come from the V8-FULL output files.
2. **Do not reuse V4/V6 dashboard numbers unless they are explicitly shown as historical reference.** A V8 chart must read the V8 run.
3. **Missing is never zero.** Render `FAILED`, `SAFETY_SKIPPED`, `NOT_RUN`, `NOT_CAPTURED`, or `UNRESOLVED` as a status, not as numeric 0.
4. **Separate measurement from interpretation.** Under every important graph use:
   - **Observation:** literal measured result.
   - **Interpretation:** plausible mechanism, with confidence (`High` / `Medium` / `Low`).
   - **Decision / implication:** only scoped to the tested workload.
   - **Next evidence:** trace/test required to prove the mechanism if not already proven.
5. **Do not infer a network mode from folder names alone.** Use `network_provenance`, run/campaign configuration, native network validation, and final validation data.
6. **Do not invent capped-network results.** This campaign measured `GCP_NATIVE` only. 100G/50G/20G/10G sensitivity remains `NOT RUN` / `UNRESOLVED` unless a later supplemental campaign adds evidence.
7. **Do not mix legacy forced-transport NCCL numbers with native V8 NCCL.** The older V4-era run used forced `NCCL_P2P_DISABLE=1` / `NCCL_SHM_DISABLE=1` for some local TP tests. V8 native local NCCL clears all `NCCL_*` overrides first. Forced P2P is retained only as an explicitly labeled `SENSITIVITY_ONLY` experiment.
8. **Do not call CUTLASS FP16 reference GEMMs “Kimi K3 MXFP4 performance.”** CUTLASS is a reference compute roof only. Actual vLLM kernels come from Nsight/PyTorch profiling.
9. **Do not aggregate per-rank GPU kernel durations and present the sum as wall-clock TTFT/TPOT.** Distributed GPU work overlaps. Use critical-path/timeline attribution or report component activity without pretending it is additive wall time.
10. **Do not show “full run complete” unless `final_validation/FINAL_VALIDATION.json` says `full_suite_valid: true`.**
    - The validator itself must be configured for the executed **native-only campaign scope**.
    - If a stale collector still expects capped modes, do not hide that mismatch in the UI. Correct/annotate the validation scope first; the dashboard must not locally turn a failed validation into a pass.
11. **Use the actual completed/near-complete V8 result tree as the only V8 measurement source.** If a planned capped-network case was not executed, show the campaign scope honestly; do not backfill it from V4/V6 or models.

12. **Configuration identity is mandatory in every tab.**
    - Visible chart/legend identity must show at least `TPx/PPy`.
    - Do not abbreviate `TP4/PP1` to `TP4`, or `TP8/PP1` to `TP8`, in a way that hides PP.
    - Scheduler/KV and profiler views must retain the same topology identity as Scale-Up/Scale-Out/Long Context.
    - Full evidence identity must preserve TP/PP, DP/EP, placement, workload, scheduler/KV modifiers, backend, and network provenance.
    - If a field is not explicitly fixed by this handoff, bind it from the case/profile manifest; do not assume it.


---

# 1. What changed conceptually: V4 → V6 → V8-FULL

| Area | V4 / smoke lineage | V6 | V8-FULL executed campaign |
|---|---|---|---|
| Primary purpose | Hardware/fabric primitives | vLLM runtime characterization | One auditable end-to-end characterization suite |
| Hardware local tests | Yes | Mostly external to V6 | **Integrated; native network/fabric path only for this run** |
| Network sweep | Earlier lineage included multiple caps | Distributed provenance, not a full model sensitivity matrix | **`GCP_NATIVE` only in this campaign** |
| Single-node vLLM | No | TP4/TP8 full matrix | **Full original V6 matrix rerun; single-node topology labels are `TP4/PP1` and `TP8/PP1`** |
| 1M single-node | Limited but meaningful | Baselines/chunking/concurrency/offload etc. | V6 1M + **new `TP4/PP1` and `TP8/PP1` c1/c2/c4, TP4/PP1 max_num_seqs, FP8-KV, prefix** |
| Scale-out | Hardware proxies | 128K/512K subset | **TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 × 128K/512K/1M × `GCP_NATIVE`** |
| vLLM network sensitivity | No | No systematic matrix | **Not measured in this campaign; schema remains future-ready** |
| Profiler | Hardware logs | Single-node Nsight/Torch; distributed coverage limited | **Single-node + native distributed Nsight** |
| Both-node telemetry | Hardware per node | Added for multi-node | **Required and validated where captured** |
| NCCL P2P/SHM policy | Historical forced sensitivity existed | Successful V6 vLLM did not force P2P/SHM | **Explicitly audited; native results must remain uncontaminated** |
| Final evidence database | Separate V4 summaries | Per-suite summaries | **Unified `final_validation/` contract** |
| Missing result semantics | Ad hoc | Improved | **Explicit status + coverage; absent capped modes are not zero** |

The executed fixed serving matrix is expected to contain:

- **64** original V6 single-node benchmark points
- **11** V8 1M-extension points
- **12** native scale-out points = 4 topologies × 3 contexts × 1 network mode
- **87 fixed serving points total**, plus dynamically generated open-loop points where executed

Treat these as **configured-scope expectations only**. Do not hard-code `87` as completed. Final completed/failed/skipped/not-run counts must come from the actual V8 `coverage.json` / `FINAL_VALIDATION.json`.

If the final run manifest differs from these planned counts, **the manifest wins**.

# 2. Frozen V8-FULL matrices the dashboard must understand

## 2.1 Executed network scope

The executed campaign uses:

```text
GCP_NATIVE
```

for:
- hardware/network primitives;
- native SendRecv / cross-node collectives;
- scale-out vLLM;
- distributed Nsight profiling.

The previously planned capped modes are **not part of this executed run**:

```text
GCP_CAPPED_100G
GCP_CAPPED_50G
GCP_CAPPED_20G
GCP_CAPPED_10G
```

Do not delete network provenance from the data contract. Keep the UI/schema future-ready, but do not manufacture those series.

## 2.2 Scale-out topologies

```text
tp4_pp2_dist   = TP4 / PP2
tp8_pp2_dist   = TP8 / PP2
tp4_pp4_dist   = TP4 / PP4
tp16_pp1_dist  = TP16 / PP1
```

Critical topology semantics:

- `TP16/PP1` is **one TP16 group spanning both nodes**. Its TP collectives cross the network.
- `TP8/PP2` is one TP8 stage per node with a remote PP boundary.
- `TP4/PP4` uses four TP4 pipeline stages across two nodes. Use actual placement evidence; do not assume every logical PP boundary is remote.
- `TP4/PP2` is one TP4 stage per node and a remote PP boundary. **It is not a split cross-node TP ring.**

## 2.3 Scale-out contexts

For every topology under `GCP_NATIVE`:

```text
128K c1
512K c1
1,000,000 c1
```

This gives 12 planned native scale-out points.

1M remains safety-gated if the execution package uses prerequisite gates. A gate skip is a valid status; it is not zero and must not be silently discarded.

## 2.4 Dashboard treatment of deferred cap sweeps

The dashboard may keep a future-ready network control, but for this campaign use one of these designs:

- show `GCP_NATIVE` as the only enabled value and label sensitivity `NOT MEASURED`; or
- hide the selector and show a prominent `GCP_NATIVE` provenance badge, while retaining the network field in the data model.

Do **not** show empty 100G/50G/20G/10G charts as if they were failed V8 tests if they were removed from the final campaign scope.

# 3. V8-FULL output directory — this replaces assumptions from the V4/V6 layouts

The run root is:

```text
~/v8_full_results/<RUN_ID>/
```

Expected structure:

```text
<RUN_ID>/
├── logs/
├── .done/                              # resume/completion markers
├── step_status.jsonl
├── STATIC_VALIDATION.json
├── RUN_CONFIG.env
├── SUITE_SOURCE_SHA256SUMS.txt
├── V8_FULL_RELEASE.json
│
├── preflight_node0/
├── preflight_node1/
├── readiness_node0/
├── readiness_node1/
├── model_validation.json
│
├── hardware_prepare/
│   ├── node0/
│   └── node1/
│
├── hardware_raw/
│   ├── node0/
│   ├── node1/
│   └── network_node0/
│
├── hardware_processed/
│   ├── nccl_points.csv
│   ├── iperf.csv
│   ├── nvbandwidth_metrics.csv
│   ├── babelstream.csv
│   ├── cutlass.csv
│   ├── summary.json
│   ├── SUMMARY.md
│   └── validation_hw.json
│
├── vllm_single_node_v6_matrix/
│   ├── <V6 case>/...
│   └── summary_v8full/
│       ├── vllm_runs.json
│       ├── vllm_runs.csv
│       └── ...
│
├── vllm_single_node_v8_1m_extensions/
│   ├── <V8 1M case>/...
│   └── summary_v8full/
│
├── 10c_v8_generated_load_cases.json
├── vllm_open_loop/
│   └── summary_v8full/
│
├── vllm_scaleout_network_matrix/
│   └── GCP_NATIVE/
│       ├── network_validation/            # exact contents depend on executed native suite
│       ├── results/
│       └── summary_v8full/
│
├── profiles_single_node/
├── profiles_torch_single_node/
├── profiles_multi_node_native/
# No capped-profile directory is required for this native-only campaign.
│
└── final_validation/
    ├── combined_vllm_runs.json
    ├── combined_vllm_runs.csv
    ├── coverage.json
    ├── coverage.csv
    ├── ONE_MILLION_COVERAGE.md
    ├── SCALEOUT_NETWORK_COVERAGE.md
    ├── NCCL_POLICY_AUDIT.json
    ├── SCALEOUT_TELEMETRY_AUDIT.json
    ├── artifact_index.json
    ├── FINAL_VALIDATION.json
    ├── FINAL_VALIDATION.md
    └── FILE_LIST.tsv
```

The final evidence archive is:

```text
<RUN_ID>_FULL_EVIDENCE.tar.gz
<RUN_ID>_FULL_EVIDENCE.tar.gz.sha256
```

---

# 4. Which files are the source of truth for the dashboards

## 4.1 First read these files

For a dashboard build, ingest in this order:

1. `final_validation/FINAL_VALIDATION.json`
2. `final_validation/coverage.json`
3. `final_validation/combined_vllm_runs.json`
4. `hardware_processed/summary.json`
5. `hardware_processed/validation_hw.json`
6. `final_validation/NCCL_POLICY_AUDIT.json`
7. `final_validation/SCALEOUT_TELEMETRY_AUDIT.json`
8. profiler `PROFILE_VALIDATION.json` files

### Why two vLLM files are necessary

- `coverage.json` answers: **Was this configured point completed, failed, skipped, or not run?**
- `combined_vllm_runs.json` answers: **What metrics were measured for the completed/summarized point?**

Do not infer completion from the existence of a chart metric. Join the two layers.

Recommended fixed-row identity:

```text
(scope, network_provenance, case, bench)
```

For analytics, also carry:

```text
tp
pp
requested_input_tokens
requested_output_tokens
concurrency
max_num_seqs
max_num_batched_tokens
kv_cache_dtype
prefix_caching
offload_gib_total
network_mode
configured_network_cap_gbps
nccl_transport_provenance
```

## 4.2 Status contract

The UI must visibly distinguish:

```text
COMPLETED
FAILED
SAFETY_SKIPPED
NOT_RUN
UNKNOWN
NOT_CAPTURED
UNRESOLVED
```

Never coerce these to 0.

## 4.3 Top-level validation banner

Read `final_validation/FINAL_VALIDATION.json` and show a run-integrity banner.

At minimum expose:

```text
full_suite_valid
strict_full_coverage
serving_matrix_complete
profiles_all_complete
hardware_required_ok
network_evidence_ok
scaleout_telemetry_ok
nccl_policy_ok
scaleout_1m_native_completed  # derive from coverage if the collector still exposes only a legacy all-networks field
coverage_counts
failed_count
not_run_count
safety_skipped_count
```

Recommended UI states:

```text
GREEN   = full_suite_valid == true
AMBER   = data exists but one or more completeness conditions are false
RED     = NCCL policy/readiness/evidence validation failure
GRAY    = run not collected yet
```

Do not label a partial run “Validated” just because individual rows completed.

---

# 5. V8 vLLM row schema — fields the V6 dashboard should now use

The V8 summarizer exposes, among others:

### Identity / configuration

```text
case
groups
purpose
tp
pp
network_provenance
network_mode
configured_network_cap_gbps
nccl_transport_provenance
physical_gpu_indices
max_num_batched_tokens
max_num_seqs
max_num_active_seqs
kv_cache_dtype
kv_cache_memory_bytes
offload_gib_total
prefix_caching
observability_profile
bench
status
```

### Workload

```text
requested_input_tokens
requested_output_tokens
concurrency
prompts_requested
warmups
request_rate
burstiness
probe_request_rate
actual_input_min
actual_input_max
actual_input_mean
actual_output_min
actual_output_max
actual_output_mean
input_len_exact_match
```

### End-to-end performance

```text
duration
request_throughput
output_throughput
total_token_throughput
mean_ttft_ms
p50_ttft_ms
p95_ttft_ms
p99_ttft_ms
mean_tpot_ms
p50_tpot_ms
p95_tpot_ms
p99_tpot_ms
mean_itl_ms
mean_e2el_ms
```

### Scheduler / KV / runtime

```text
peak_kv_usage
peak_running
peak_waiting
mean_running
mean_waiting
preemptions_delta
prefix_hits_delta
prefix_queries_delta
offload_bytes_delta
offload_time_delta_s
queue_mean_s_from_hist
prefill_mean_s_from_hist
decode_mean_s_from_hist
inference_mean_s_from_hist
metric_samples
metrics_capture_status
gpu_node_stats_json
```

### Prefix-specific

```text
prefix_first_ttft_ms
prefix_repeat_ttft_median_ms
```

### Percentile reliability

Keep the V6 reliability rule:

- p95 is trustworthy only when completed sample count is at least 20.
- p99 is trustworthy only when completed sample count is at least 100.

Raw percentile values may exist, but the dashboard must not promote low-N p95/p99 as reliable SLO statistics.

---

# 6. Hardware / V4-smoke dashboard migration

Treat the existing V4-style smoke dashboard as the **hardware/fabric dashboard**, but rewire it to V8 paths and provenance.

## 6.1 Machine-readable inputs

Use whatever native-run outputs are actually present, especially:

```text
hardware_processed/nccl_points.csv
hardware_processed/iperf.csv
hardware_processed/nvbandwidth_metrics.csv
hardware_processed/babelstream.csv
hardware_processed/cutlass.csv
hardware_processed/summary.json
hardware_processed/validation_hw.json
```

Use `hardware_raw/` for drill-down/evidence and debugging.

Do not fail the dashboard because a multi-cap file/row is absent if the executed campaign scope is native-only.

## 6.2 Recommended hardware dashboard tabs

### Tab A — System & Topology

Show:
- node0/node1 GPU count and exact model
- CPU/NUMA topology
- PCIe topology
- GPU↔CPU affinity
- detected network interface
- CUDA/NCCL/tool versions
- run ID / timestamps
- hardware validation status

Do not display legacy RTX 6000 Ada / 48GB / PCIe Gen4 labels.

### Tab B — Local Memory / PCIe

Charts:
1. H2D bandwidth by GPU/node
2. D2H bandwidth by GPU/node
3. D2D bandwidth matrix or same-NUMA vs cross-NUMA grouping
4. D2D latency
5. BabelStream Copy/Add/Triad/Dot

Each chart must link to raw evidence.

### Tab C — Local NCCL / TP4 vs TP8

Charts:
1. Native TP4 AllReduce latency vs message size
2. Native TP8 AllReduce latency vs message size
3. Native TP4/TP8 AllGather
4. Native TP4/TP8 ReduceScatter
5. Algorithm/bus bandwidth where parsed

Primary native charts must exclude forced-transport sensitivity rows.

If a forced-P2P sensitivity test exists, place it in a separate clearly labeled panel. Do not merge it with native.

### Tab D — Native Network/Fabric

Show the native evidence that actually exists:
- iperf forward/reverse if captured
- RTT/ping if captured
- interface + MTU
- NCCL SendRecv latency/bandwidth
- native network validation status

Add a visible note:

> Controlled 100G/50G/20G/10G sensitivity was not executed in this campaign.

Do not derive a cap curve.

### Tab E — Native Cross-node Collectives

For available TP2 / TP8 / TP16:
- native AllReduce latency vs message size
- native AllReduce bandwidth vs message size
- topology/group-size comparison

This is still highly valuable for explaining native scale-out behavior.

### Tab F — Compute Reference

CUTLASS:
- 8192³ reference GEMM
- Kimi-width `N=K=7168` reference shapes
- runtime / GFLOP/s where parsed

Label:

> **FP16 tensor-core reference compute roof. Not Kimi K3 MXFP4 model performance.**

### Tab G — Evidence

Searchable table with:
- node
- kind
- TP/group size
- `network_provenance`
- size
- time
- algbw/busbw
- raw file
- validation status

Preserve schema fields for future capped measurements, but do not render absent caps as measured.

# 7. Latest V6 dashboard migration — keep the 7-tab structure, change the data model

Use the existing `MASTER_CHARACTERIZATION_DASHBOARD.html` as a UI/reference baseline, but the V8 implementation must stop using hard-coded arrays or synthetic interpolation as measured evidence.

Keep these seven top-level tabs:

```text
Executive
Scale-Up
Scale-Out
Long Context
Scheduler & KV
Profiler
Evidence
```

Do **not** add a separate top-level Network tab unless the UI becomes too crowded. Network mode fits naturally as a first-class selector inside Scale-Out and Profiler.

---


# 7A. UI V4 global configuration-identity convention

UI V4 treats configuration identity as part of every measurement.

## 7A.1 Visible label convention

At minimum, every plotted/compared series must show:

```text
TPx/PPy
```

Current V8 examples:

```text
Single-node:
  TP4/PP1
  TP8/PP1

Distributed:
  TP4/PP2
  TP8/PP2
  TP4/PP4
  TP16/PP1
```

Do not use a naked `TP4` or `TP8` label when the actual configuration is `TP4/PP1` or `TP8/PP1`.

For scheduler and long-context sensitivity charts, extend the label as needed:

```text
TP4/PP1 · 1M · c4 · maxseq=8
TP8/PP1 · 1M · c2
TP4/PP4 · 512K prefill · GCP_NATIVE
```

## 7A.2 Full configuration key

Evidence and drill-down must retain:

```text
model_id / revision
TP / PP / DP / EP
rank -> node -> GPU UUID -> PCI bus -> NUMA/socket
context / input / output
concurrency or request rate
max_num_seqs
max_num_batched_tokens
KV-cache dtype
prefix caching
offload configuration
attention / MoE / runtime backend
network_provenance
run_id / case_id / profile_id
```

If the benchmark specification does not fix a field, read it from the manifest / evidence row.

## 7A.3 Per-tab minimum

| Tab | UI V4 minimum visible identity |
|---|---|
| Executive | Candidate configuration shows `TPx/PPy` |
| Scale-Up | `TP4/PP1` vs `TP8/PP1` |
| Scale-Out | all four distributed TP/PP topologies + `GCP_NATIVE` |
| Long Context | exact single-node or distributed TP/PP for every 1M panel |
| Scheduler & KV | exact TP/PP per queue/KV/scheduler series |
| Profiler | exact TP/PP per trace/profile row |
| Evidence | full configuration key |

This is a dashboard/data-contract change only. Do not invent new benchmark runs.


# 8. Executive tab — V8 requirements

The Executive page should answer four questions only:

1. Did the run complete and validate?
2. What was measured?
3. What are the strongest literal observations?
4. What remains unresolved?

Required cards:

```text
Run validation: full / partial / failed
Fixed serving coverage: completed / configured
1M scale-out coverage: completed / required
Profiler coverage: complete / expected
Hardware validation: pass/fail
NCCL policy: pass/fail
Native network evidence: pass/fail
Both-node telemetry: pass/fail
```

Do not put invented runtime-share percentages such as “GPU 48%, TP 22%, PP 8%, vLLM 14%” on Executive unless the profiler analysis actually produced a validated critical-path attribution.

Keep observations workload-scoped. Example wording:

> “At 128K c1 on GCP_NATIVE, topology X had the lowest measured TTFT among the four tested topologies.”

Not:

> “Topology X is the best architecture.”

---

# 9. Scale-Up tab — V8 requirements

Scale-Up is **single-node only**.

Primary dimensions:

```text
TP/PP = `TP4/PP1` / `TP8/PP1`
context
concurrency
chunk size
scheduler settings
KV dtype
```

Required charts:

1. `TP4/PP1` vs `TP8/PP1` TTFT at measured context points
2. `TP4/PP1` vs `TP8/PP1` TPOT at measured context points
3. output throughput at matched workload
4. TTFT / TPOT vs concurrency for contexts where the matrix actually exists
5. local `TP4/PP1` vs `TP8/PP1` NCCL correlation panel using V8 hardware data


### UI V4 naming rule for Scale-Up

Scale-Up is single-node only for this V8 matrix.

Use:

```text
TP4/PP1
TP8/PP1
```

Do **not** show `TP4/PP2` in Scale-Up unless a future run actually adds a single-node PP2 evidence row. `TP4/PP2` is part of the current Scale-Out topology set.


### Critical chart rule

Do not plot 32K/64K/256K as “measured” unless V8 actually has rows at those contexts.

Use:

- solid marker = measured
- dashed line = derived/interpolated, only if the product needs it
- no marker / `NOT RUN` = absent

If you fit an estimated crossover, label it `DERIVED`, not `MEASURED`.

---

# 10. Scale-Out tab — this is the biggest V8 dashboard change

V8 still introduces a much richer **topology × context** dataset, but this campaign has one measured network provenance: `GCP_NATIVE`.

## 10.1 Required selectors

```text
Network provenance:
  GCP_NATIVE    # measured campaign state

Context:
  128K
  512K
  1M

Metric:
  TTFT
  TPOT
  request throughput
  output throughput
  queue
  KV usage
  preemptions
```

You may keep a disabled/future network selector in the UI architecture, but do not show 100G/50G/20G/10G as measured options.

## 10.2 Required scale-out charts

### Chart 1 — Topology comparison at selected context on native fabric

Compare:
- TP4/PP2
- TP8/PP2
- TP4/PP4
- TP16/PP1

### Chart 2 — Context scaling by topology

Plot:

```text
128K → 512K → 1M
```

for each topology on `GCP_NATIVE`.

### Chart 3 — Native topology × metric decision matrix

For the selected context, show TTFT / TPOT / throughput / queue / KV with status.

### Chart 4 — Native 1M scale-out matrix

| Topology | GCP_NATIVE |
|---|---:|
| TP4/PP2 | status + metric |
| TP8/PP2 | status + metric |
| TP4/PP4 | status + metric |
| TP16/PP1 | status + metric |

Every cell must show status. A safety-skipped or failed cell must not look like zero latency.

## 10.3 Native network verification panel

Show the network evidence actually captured for the run:
- interface / MTU
- native iperf forward/reverse if available
- RTT/ping if available
- native NCCL/SendRecv
- `network_provenance`
- validation state

Do not imply that native bandwidth alone establishes the minimum network requirement.

## 10.4 Preserve future network-sensitivity compatibility

Keep `network_provenance` and related schema fields in joins/filters. The UI should be able to accept a later supplemental capped run without redesign.

For this campaign explicitly show:

> **Bandwidth-cap sensitivity: NOT MEASURED / UNRESOLVED — native network only due lab availability.**

## 10.5 Causal-language rule

Do not automatically say:
- “Pipeline Parallelism Superiority”
- “TP16 saturates the network”
- “PP masks transport latency”
- “X is universally recommended / Y should be avoided”

Use:

**Observation → Interpretation + confidence → workload-scoped implication → next evidence.**

Native distributed Nsight/NCCL evidence may support communication mechanisms; bandwidth sensitivity still remains unresolved without capped runs.

# 11. Long Context tab — V8 must make 1M a first-class dataset

This tab is no longer just “did 1M run?” It must expose the different 1M regimes.

## 11.1 Single-node 1M sections

Required V8 views:

### TP4 vs TP8 1M concurrency

```text
TP4/PP1: c1 → c2 → c4
TP8/PP1: c1 → c2 → c4
```

Plot:

- TTFT
- TPOT
- output throughput
- queue/waiting requests
- peak KV usage
- preemptions

### TP4/PP1 1M scheduler sensitivity

```text
TP4/PP1 · 1M · c4 · max_num_seqs = 4 / 8 / 16
```

### 1M chunked prefill

Keep V6 4K / 8K / 16K 1M cases and show the actual measured trade-off.

Do not call a chunk size “sweet spot” unless the selected objective is defined and the measured data supports it.

### FP8-KV 1M

Compare only against an otherwise matched baseline. Do not conflate KV dtype with model weight precision.

### Prefix cache 1M

Show:

- first/cold TTFT
- repeated-prefix median TTFT
- prefix hit/query metrics

Do not project a 1M prefix-cache speedup from 128K/512K now that V8 has an actual 1M prefix-reuse case.

### CPU offload 1M

Use the preserved V6 native offload-pressure case and correlate:

- offload bytes/time
- TTFT/TPOT
- queueing
- GPU telemetry

Do not say “memory is the bottleneck” without actual memory/offload evidence.


### UI V4 configuration identity for Long Context

Every long-context panel must expose the exact configuration:

| View | Configuration identity |
|---|---|
| 1M concurrency | `TP4/PP1` and `TP8/PP1` |
| 1M max_num_seqs | `TP4/PP1` |
| 1M chunking | preserve exact V6 topology lineage; current lineage is `TP4/PP1` where supported by evidence |
| FP8-KV 1M | bind exact TP/PP from matched evidence rows |
| Prefix reuse 1M | bind exact TP/PP from case manifest |
| CPU/offload 1M | bind exact TP/PP from preserved case manifest |
| Distributed 1M | `TP4/PP2`, `TP8/PP2`, `TP4/PP4`, `TP16/PP1` |

Do not hide TP/PP when the x-axis is concurrency, chunk size, scheduler setting, or KV dtype.


## 11.2 Distributed 1M

Add a dedicated panel sourced from:

```text
final_validation/ONE_MILLION_COVERAGE.md
final_validation/coverage.json
final_validation/combined_vllm_runs.json
```

Show all **4 executed distributed 1M cells**:

```text
4 topologies × GCP_NATIVE
```

If the UI retains future cap columns, label them `NOT EXECUTED IN THIS CAMPAIGN`; do not count them as V8 failures.

## 11.3 Token-length wording

Always distinguish:

```text
requested input = 1,000,000 tokens
max_model_len = 1,048,576
```

Do not label a 1,000,000-token request as “exact architectural maximum context.”

---

# 12. Scheduler & KV tab — fix the old unit and synthetic-data risks

Use actual V8 row fields.

Required charts:

1. peak KV usage vs context/concurrency
2. running vs waiting sequences
3. queue mean from Prometheus histogram
4. preemptions
5. `max_num_seqs` sensitivity
6. offload bytes/time where enabled
7. open-loop RPS → queue → TTFT/TPOT capacity envelope


## 12.1 UI V4 scheduler/KV configuration identity

Every Scheduler & KV chart must carry the exact `TPx/PPy` for each series.

Required examples:

```text
TP4/PP1 · 1M · c4 · max_num_seqs=4
TP4/PP1 · 1M · c4 · max_num_seqs=8
TP4/PP1 · 1M · c4 · max_num_seqs=16
```

For:
- peak KV usage;
- running/waiting;
- queue;
- preemptions;
- offload;
- open-loop capacity;

bind TP/PP from the matching case manifest/evidence row.

Do not aggregate unmatched TP/PP configurations into one queue/KV curve.

If the preserved 512K max_num_seqs cases are shown, label them separately from the new 1M sweep.


### Unit rule

`peak_kv_usage` is a utilization metric. Do **not** relabel a percentage/fraction as GB.

Only show KV GB when actual byte capacity/usage is available from a byte field and the conversion is explicit.

### Capacity semantics

Keep these concepts distinct:

```text
client concurrency
arrival RPS
running sequences
waiting sequences
max_num_seqs
max_num_batched_tokens
active decode batch
```

They are not interchangeable.

---

# 13. Profiler tab — V8 expands this materially

This native-only campaign has three profile evidence classes:

```text
single-node Nsight
single-node PyTorch profiler
native distributed Nsight
```

Capped distributed Nsight was not executed in this campaign.

## 13.1 Default distributed profiler matrix

Native:

- all four topologies × 128K prefill
- all four × 8K decode
- all four × 8K c8 batched decode
- TP4/PP4 512K prefill (heavy default)
- TP16/PP1 512K prefill (heavy default)

There is no capped distributed profile set in this campaign.

If the planned native profile matrix completed as originally defined, the expected native distributed validations are **14**:
- 4 × 128K prefill
- 4 × 8K decode
- 4 × 8K c8 batched decode
- 2 × heavy 512K prefill

The **actual profiler manifest / validation files win** if the final executed count differs.


## 13.1A UI V4 profiler configuration identity

Every profiler trace/profile row must show the exact `TPx/PPy`.

Do not render a generic row named only "4 topologies."

The planned native distributed matrix is:

```text
128K prefill:
  TP4/PP2
  TP8/PP2
  TP4/PP4
  TP16/PP1

8K decode c1:
  TP4/PP2
  TP8/PP2
  TP4/PP4
  TP16/PP1

8K decode c8:
  TP4/PP2
  TP8/PP2
  TP4/PP4
  TP16/PP1

512K heavy prefill:
  TP4/PP4
  TP16/PP1
```

If fully completed as planned this is 14 native distributed profile validations.

For single-node Nsight and PyTorch profiles, read the exact TP/PP from `PROFILE_VALIDATION` / profile metadata.

A profiler mechanism is scoped to the topology that produced the trace. Do not use a TP16/PP1 NCCL observation as causal evidence for TP4/PP4 without an independent TP4/PP4 trace.


## 13.2 Profiler UI requirements

For each profile show:

```text
network provenance
topology
TP / PP
profile mode
context
concurrency
ranks expected / captured
node0 trace present
node1 trace present
Nsight version
NCCL trace/report availability
PROFILE_VALIDATION status
```

Then show actual parsed kernel/activity categories, for example where present:

```text
KDA / MLA attention
MoE / Triton kernels
GEMM
normalization / elementwise
NCCL AllReduce / AllGather / ReduceScatter
NCCL Send / Recv
CUDA API / CPU launch gaps
GPU idle intervals
NVTX phase/layer ranges
overlap
```

### Critical-path rule

Do not invent additive wall-time percentages from independent rank totals.

The conceptual decomposition is:

```text
T_workload = A_GPU + B_TP + C_PP + D_PCIe/offload + E_vLLM + F_CPU/launch + G_other - O_overlap
```

But a numeric stacked chart is allowed only when the attribution method is supported by the actual timeline and avoids double counting.

If not supported, show component activity and mark wall-time attribution `UNRESOLVED`.

### 1M profiler rule

1M end-to-end runs and telemetry are required. **1M Nsight is intentionally not a default V8 requirement.** Do not mark “profiler missing” for 1M as a failed benchmark; it is `NOT_CONFIGURED` for default profiling.

---

# 14. Evidence tab — make it the audit backbone

The V8 Evidence tab should be stronger than V6.

For vLLM rows include at least:

```text
scope
network_provenance
case
bench
status
config_id
tp
pp
dp
ep
rank_to_node_gpu
numa
input_tokens / requested_input_tokens
output_tokens
concurrency
configured_network_cap_gbps
max_num_seqs
max_num_batched_tokens
kv_cache_dtype
prefix_caching
offload_gib_total
completed
failed
input_len_exact_match
metric_samples
peak_kv_usage
preemptions_delta
manifest path
source_summary
```

Recommended `scope` categories from the final collector:

```text
SINGLE_V6_BASE
SINGLE_V8_1M_EXT
MULTI_V8
OPEN_LOOP_GENERATED
```


### UI V4 Evidence configuration key

Every chart point must resolve to an evidence row whose identity is sufficient to reproduce the point.

Use the conceptual key:

```text
model_revision
+ TP + PP + DP + EP
+ rank_placement
+ context
+ concurrency_or_RPS
+ max_num_seqs
+ max_num_batched_tokens
+ kv_cache_dtype
+ prefix_caching
+ offload
+ backend
+ network_provenance
```

The chart legend shows at least `TPx/PPy`; Evidence exposes the full configuration.

Missing identity remains `UNKNOWN` / `UNRESOLVED`, never inferred.


Add filters for:

- scope
- topology
- TP/PP
- context
- network provenance
- concurrency
- status
- KV dtype
- prefix cache
- offload

When the user clicks a chart point, jump to or highlight the backing Evidence row.

Also add links/paths to:

```text
case_manifest.json
benchmark result JSON
server.log
COMMAND.txt
metrics_gpu.jsonl or metrics_node0/node1.jsonl
metrics_raw.prom.log
network validation files
PROFILE_VALIDATION.json / .nsys-rep
```

---

# 15. Exact migration map from the team's old outputs

| Old concept/path | V8-FULL path / handling |
|---|---|
| V4 node-local raw results | `hardware_raw/node0/`, `hardware_raw/node1/` |
| V4 network sweep | `hardware_raw/network_node0/` |
| V4 summary CSV/JSON | `hardware_processed/` |
| V6 single-node result root | `vllm_single_node_v6_matrix/` |
| New 1M V8 cases | `vllm_single_node_v8_1m_extensions/` |
| V6 generated open-loop | `10c_v8_generated_load_cases.json` + `vllm_open_loop/` |
| V6 multi-node results | `vllm_scaleout_network_matrix/<NETWORK>/results/` |
| V6 multi-node summary | `vllm_scaleout_network_matrix/<NETWORK>/summary_v8full/` |
| V6 single-node profiler | `profiles_single_node/` |
| V6 Torch profiler | `profiles_torch_single_node/` |
| New native distributed profiles | `profiles_multi_node_native/` |
| Capped distributed profiles | **Not executed in this campaign**; reserve path/schema for a future supplemental run |
| V6 ad-hoc evidence ledger | `final_validation/coverage.json` + `combined_vllm_runs.json` |
| Manual completion checking | `FINAL_VALIDATION.json`, `ONE_MILLION_COVERAGE.md`, `SCALEOUT_NETWORK_COVERAGE.md` |

---

# 16. What to remove from the current V6 dashboard implementation

When migrating the existing master dashboard, remove or replace the following patterns:

1. **Hard-coded JS arrays** for benchmark charts.
2. Synthetic 32K/64K/256K values displayed as measured.
3. Legacy hardware labels such as RTX 6000 Ada / 48GB / PCIe Gen4.
4. A single “scale-out result” without network provenance.
5. TP16/PP1 described as “within nodes.”
6. TP4/PP2 described as split cross-node TP.
7. 1M prefix-cache projections when actual V8 1M prefix data exists.
8. KV “GB” values derived from a utilization percentage.
9. Unsupported exact profiler percentages.
10. Universal labels such as `BEST`, `RECOMMENDED`, `AVOID`, or “pipeline superiority” unless the UI is explicitly showing a narrowly defined measured objective and does not generalize beyond it.
11. “Live” timestamp if the dashboard is a static snapshot.
12. Percentile charts that ignore sample-count reliability.
13. Any missing run represented by numeric zero.

---

# 17. What to add to the current V6 dashboard implementation

1. **Native network provenance control** on Scale-Out and Profiler:
   - `GCP_NATIVE` is the only measured state in this campaign.
   - keep the schema future-ready for later cap sweeps.
2. **1M scale-out grid** with all 4 executed native distributed cells.
3. **TP8 1M c1/c2/c4** alongside TP4.
4. **1M max_num_seqs** 4/8/16 panel.
5. **1M FP8-KV** panel.
6. **actual 1M prefix reuse** panel.
7. Validation banner driven by `FINAL_VALIDATION.json`.
8. Coverage counters driven by `coverage.json`.
9. Both-node telemetry completeness status.
10. NCCL transport policy status.
11. Hardware validation status and cross-links to hardware dashboard.
12. Per-point provenance badges.
13. Evidence drill-down links.
14. Profile completeness and trace-capture metadata.
15. Dynamic `COMPLETED / FAILED / SAFETY_SKIPPED / NOT_RUN` rendering.
16. A visible `NETWORK SENSITIVITY NOT MEASURED` note so users do not infer missing cap results.

---

# 18. Evidence/provenance badges to use consistently

Recommended badges:

```text
MEASURED-GCP-HW
MEASURED-48B
MEASURED-48B-PROFILE
GCP_NATIVE                # measured in this campaign
GCP_CAPPED_100G            # reserved for future supplemental runs
GCP_CAPPED_50G             # reserved for future supplemental runs
GCP_CAPPED_20G             # reserved for future supplemental runs
GCP_CAPPED_10G             # reserved for future supplemental runs
LOCAL_REAL                # reserve for later true local measurements
DERIVED
UNRESOLVED
SENSITIVITY_ONLY
```

For model results, continue to state that `moonshotai/Kimi-Linear-48B-A3B-Instruct` is a BF16-weight surrogate. Absolute TTFT/TPOT/tokens/s should **not** be scaled to Kimi K3. Use the surrogate to learn runtime mechanisms and relative effects.

---

# 19. Suggested dashboard loading logic

Pseudocode:

```python
root = Path(V8_RUN_ROOT)

final = json.load(open(root / "final_validation/FINAL_VALIDATION.json"))
coverage = json.load(open(root / "final_validation/coverage.json"))
runs = json.load(open(root / "final_validation/combined_vllm_runs.json"))
hardware = json.load(open(root / "hardware_processed/summary.json"))
hw_validation = json.load(open(root / "hardware_processed/validation_hw.json"))
nccl_policy = json.load(open(root / "final_validation/NCCL_POLICY_AUDIT.json"))
telemetry_audit = json.load(open(root / "final_validation/SCALEOUT_TELEMETRY_AUDIT.json"))
```

Then:

```python
# status index
status_by_key = {
    (r["scope"], r["network_provenance"], r["case"], r["bench"]): r
    for r in coverage
}

# metrics index — do not assume uniqueness without network provenance
metrics_by_key = {
    (infer_scope(r), r["network_provenance"], r["case"], r["bench"]): r
    for r in runs
}
```

If a configured point has no metric row:

- read its status from coverage
- render the status
- do not generate a fake metric

Before rendering a profile-derived numerical decomposition, require its `PROFILE_VALIDATION.json` to indicate complete/usable capture.

---

# 20. Dashboard-specific acceptance tests

## Hardware/smoke dashboard acceptance

- [ ] Uses `hardware_processed/*`, not old V4 hard-coded values.
- [ ] Shows all executed native hardware/network evidence; does not require unexecuted cap sweeps.
- [ ] Separates native NCCL from forced P2P sensitivity.
- [ ] Shows TP2/TP8/TP16 cross-node data.
- [ ] Labels CUTLASS as reference compute only.
- [ ] Has raw-evidence paths.
- [ ] Shows `validation_hw.json` state.

## V8 runtime dashboard acceptance

- [ ] Reads `FINAL_VALIDATION.json` first.
- [ ] Reads both `coverage.json` and `combined_vllm_runs.json`.
- [ ] Keeps the seven top-level V6 dashboard tabs.
- [ ] Scale-Out shows `GCP_NATIVE` as the only measured network state.
- [ ] No 100G/50G/20G/10G vLLM series is shown without actual evidence.
- [ ] Network-bandwidth sensitivity is explicitly marked unresolved/deferred.
- [ ] Scale-Out supports 128K/512K/1M.
- [ ] All four topologies are supported.
- [ ] TP16/PP1 semantics are correct.
- [ ] 1M has TP4 and TP8 c1/c2/c4 where completed.
- [ ] 1M max_num_seqs, FP8-KV, prefix reuse are visible.
- [ ] Missing/skipped/failed points are not zero.
- [ ] p95/p99 obey sample-count reliability.
- [ ] No unsupported profiler percentages.
- [ ] Both-node telemetry status is visible.
- [ ] NCCL policy audit is visible.
- [ ] Every chart point can be traced to evidence.

---

# 21. Recommended chart annotation format

Place this directly below important charts:

```text
Observation
  Literal measured result, including workload + topology + network mode.

Interpretation [High / Medium / Low confidence]
  Mechanism suggested by the data. Do not state correlation as proof.

Implication
  Scoped only to the tested workload/objective.

Next evidence
  Specific trace or test that would confirm/refute the mechanism.

Evidence
  Run ID, case, bench, source summary/raw path, sample count.
```

Example structure only — populate with actual V8 values after the run:

```text
Observation:
At 128K c1 under GCP_NATIVE, <topology> measured <TTFT> and <throughput>.

Interpretation [Medium]:
The result is consistent with <smaller/larger TP communication pressure or PP behavior>, but the endpoint metric alone does not prove the cause.

Implication:
For this exact 128K c1 / native-fabric workload, <topology> is the leading measured configuration for <metric>.

Next evidence:
Correlate per-rank NCCL time, PP Send/Recv, idle gaps, and Ray placement from the matched 128K native distributed profile.

Evidence:
GCP_NATIVE / <case> / 128k_c1 / N=<sample count> / <manifest path>
```

---

# 22. Team workflow after the V8-FULL run finishes

Follow this order:

1. **Do not open the dashboard first.** Check `FINAL_VALIDATION.json`.
2. Confirm `hardware_required_ok`, `network_evidence_ok`, `nccl_policy_ok`, and `scaleout_telemetry_ok`.
3. Check `coverage_counts`, `failed_count`, `not_run_count`, and `safety_skipped_count`.
4. Check `ONE_MILLION_COVERAGE.md` and any scale-out coverage report generated by the native-only collector.
5. Confirm the 4 required native distributed 1M cells have the expected status.
6. Confirm `combined_vllm_runs.json` contains measured rows for completed native cases and no synthetic capped-network rows.
7. Confirm hardware CSV/JSON was parsed and `validation_hw.json` passes.
8. Confirm distributed `PROFILE_VALIDATION.json` files before exposing profile-derived claims.
9. Update/refresh the hardware dashboard.
10. Update/refresh the seven-tab runtime dashboard.
11. Manually review any high-level interpretation against raw evidence before publishing screenshots.
12. Archive the dashboard build with the exact V8 run ID and evidence archive SHA-256.

---

# 23. Files to keep beside this prompt while implementing

Use these as **reference**, not as V8 data sources:

```text
MASTER_CHARACTERIZATION_DASHBOARD.html
  Existing/latest V6 dashboard UI reference.

V6_vLLM_Dashboard_Deep_Audit_UI_Remediation.pdf
  Detailed review of what was wrong/missing in the latest V6 dashboard.

UI-scaleup-new.pdf
UI-scaleout-new.pdf
  Earlier hardware/topology UI references.

V8_FULL_README.md
V8_FULL_RELEASE_VALIDATION.md
V8_FULL_RELEASE.json
  V8 source-of-truth suite contract.
```

The actual numbers for the new dashboards must come from the **completed V8 run result directory**, not from these reference documents.

---

# 24. Native-only execution must not reduce dashboard quality

The lab-scope change removes only the controlled bandwidth-cap dimension. Do **not** simplify away the rest of the V8 data.

The final UI must still surface every captured dimension:

- system/topology inventory;
- exact hardware identity;
- H2D/D2H/D2D/P2P and memory-bandwidth evidence;
- native NCCL collectives and SendRecv;
- TP4/TP8 single-node matrix;
- full measured 1M extensions;
- open-loop load cases where executed;
- all four native scale-out topologies;
- 128K / 512K / 1M native scale-out data;
- scheduler/KV/queue/preemption metrics;
- both-node telemetry;
- rank/node/GPU/NUMA placement;
- native distributed Nsight;
- single-node Nsight and PyTorch profiler;
- profile completeness;
- raw-artifact drill-down;
- exact status semantics;
- measured / timeline-attributed / derived / unresolved separation;
- workload-scoped deployment implications;
- V6 comparison only where matched.

The UI should **retain network provenance in every relevant row** even though there is one value now. This preserves the original dashboard architecture and makes a later 100G/20G/etc. supplement a data append rather than a redesign.

The impact goal is unchanged: help an engineer understand what to deploy, why it behaves that way, where the bottleneck is, what to tune, and what remains unproven.

The only intentionally unavailable answer is:

> **How performance changes as network bandwidth is artificially constrained.**

Show that gap clearly rather than hiding it or estimating it.

# 25. Final deliverables expected from the dashboard team

Please produce two updated artifacts after the V8 run:

## Deliverable A — V8 Hardware / Smoke Dashboard

Successor to the V4 hardware/fabric dashboard.

Must cover:

```text
System/topology
Local memory + PCIe
Native local NCCL
Native transport evidence
Network: GCP_NATIVE only for this campaign
Cross-node TP2/TP8/TP16 where captured
CUTLASS reference compute
Evidence/raw drill-down
```

## Deliverable B — V8 vLLM Characterization Dashboard

Successor to `MASTER_CHARACTERIZATION_DASHBOARD.html`.

Keep:

```text
Executive
Scale-Up
Scale-Out
Long Context
Scheduler & KV
Profiler
Evidence
```

Major V8 additions:

```text
GCP_NATIVE scale-out provenance control
128K/512K/1M native topology matrix
all four distributed topologies
TP4 + TP8 1M c1/c2/c4
1M scheduler sweep
1M FP8-KV
actual 1M prefix reuse
both-node telemetry validation
NCCL-policy validation
distributed native profiler evidence
strict run-completeness banner
```

## Deliverable C — Data/validation note

A short Markdown file accompanying the dashboards with:

```text
V8 RUN_ID
result-root path
FULL_EVIDENCE archive SHA-256
FINAL_VALIDATION status
configured/completed/failed/skipped/not-run counts
hardware validation status
profile validation count
known unresolved items
```

---

# 26. Final instruction

The V8 dashboards should be **views over the measurement database**, not another layer of hand-entered conclusions.

If a value cannot be traced to:

```text
hardware_processed/*
final_validation/*
summary_v8full/*
case_manifest.json
benchmark JSON
metrics JSONL / Prometheus logs
network_validation/*
PROFILE_VALIDATION.json / Nsight raw trace
```

then it must not be shown as measured.

When data is absent, say **NOT RUN / NOT CAPTURED / UNRESOLVED**. When a mechanism is plausible but not proven, label it as an **interpretation with confidence**. This is the main change from the old static dashboards to the V8-FULL evidence-backed dashboard model.


---


## UI V4 configuration-identity acceptance checks

Before publishing:

- [ ] Executive candidate configurations show `TPx/PPy`.
- [ ] Scale-Up shows `TP4/PP1` and `TP8/PP1`, not naked TP4/TP8 labels.
- [ ] Scale-Out uses all four exact distributed topology names.
- [ ] Long Context exposes exact TP/PP for concurrency, scheduler, KV, prefix, offload, and distributed 1M panels.
- [ ] Scheduler & KV exposes exact TP/PP per series.
- [ ] Profiler exposes exact TP/PP per trace/profile row.
- [ ] The distributed profiler table lists the planned 14 topology/workload cells explicitly when configured.
- [ ] Evidence rows preserve full configuration identity.
- [ ] Any unspecified field is manifest-bound rather than assumed.
- [ ] No dashboard recommendation loses the configuration identity of the evidence that supports it.

