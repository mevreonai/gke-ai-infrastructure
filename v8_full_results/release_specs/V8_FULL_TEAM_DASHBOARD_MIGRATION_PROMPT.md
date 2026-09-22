# V8-FULL Team Handoff Prompt — Migrate the V4 Smoke + V6 vLLM Dashboards to V8-FULL

**Audience:** the engineering team that previously ran the RTX PRO 6000 GCP hardware/smoke suite (V4 lineage), ran the V6 vLLM characterization suite, and built the existing hardware + vLLM dashboards.

**Primary goal:** after the V8-FULL run finishes, update the existing dashboards so that every number, chart, status, and conclusion is driven from the V8-FULL result tree and can be traced back to raw evidence.

**Important:** do not redesign the measurements. V8-FULL deliberately preserves the working V6 execution path where possible and adds hardware/fabric, deeper 1M, network sensitivity, distributed profiling, provenance, and validation around it. The dashboard work is mainly a **data-contract + UI migration**, not a new benchmark design.

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
5. **Do not infer a network mode from folder names alone.** Use `network_provenance`, `configured_network_cap_gbps`, `NETWORK_MODE.json`, and final validation data.
6. **Do not call GCP-capped 20G a local dual-10G measurement.** It is `GCP_CAPPED_20G`, a bandwidth-sensitivity proxy only.
7. **Do not mix legacy forced-transport NCCL numbers with native V8 NCCL.** The older V4-era run used forced `NCCL_P2P_DISABLE=1` / `NCCL_SHM_DISABLE=1` for some local TP tests. V8 native local NCCL clears all `NCCL_*` overrides first. Forced P2P is retained only as an explicitly labeled `SENSITIVITY_ONLY` experiment.
8. **Do not call CUTLASS FP16 reference GEMMs “Kimi K3 MXFP4 performance.”** CUTLASS is a reference compute roof only. Actual vLLM kernels come from Nsight/PyTorch profiling.
9. **Do not aggregate per-rank GPU kernel durations and present the sum as wall-clock TTFT/TPOT.** Distributed GPU work overlaps. Use critical-path/timeline attribution or report component activity without pretending it is additive wall time.
10. **Do not show “full run complete” unless `final_validation/FINAL_VALIDATION.json` says `full_suite_valid: true`.**
11. **The V8 release package itself has been statically/synthetically validated, but the real GCP run has not happened yet.** Until the actual run is complete, dashboard templates must show `NOT RUN` / placeholder state rather than synthetic numbers.

---

# 1. What changed conceptually: V4 → V6 → V8-FULL

| Area | V4 / smoke lineage | V6 | V8-FULL |
|---|---|---|---|
| Primary purpose | Hardware/fabric primitives | vLLM runtime characterization | One auditable end-to-end characterization suite |
| Hardware local tests | Yes | Mostly external to V6 | **Integrated** |
| Network sweep | Native/100/50/20/10G | Distributed provenance, not full model sensitivity matrix | **Hardware:** Native/100/50/20/10G; **vLLM:** Native/100/20G |
| Single-node vLLM | No | TP4/TP8 full matrix | **Full original V6 matrix rerun** |
| 1M single-node | Limited but meaningful | Baselines/chunking/concurrency/offload etc. | V6 1M + **new TP4/TP8 c1/c2/c4, max_num_seqs, FP8-KV, prefix** |
| Scale-out | Hardware proxies | 128K/512K subset | **TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 × 128K/512K/1M × Native/100G/20G** |
| vLLM model network sensitivity | No | No systematic matrix | **36 fixed scale-out points** |
| Profiler | Hardware logs | Single-node Nsight/Torch; distributed coverage limited | **Single-node + distributed Nsight; capped 100G/20G matched prefill profiles** |
| Both-node telemetry | Hardware per node | Added for multi-node | **Required and validated** |
| NCCL P2P/SHM policy | Historical forced sensitivity existed | Successful V6 vLLM did not force P2P/SHM | **Explicitly audited and fail-closed** |
| Final evidence database | Separate V4 summaries | Per-suite summaries | **Unified `final_validation/` contract** |
| Missing result semantics | Ad hoc | Improved | **Explicit status + strict coverage** |

The exact V8-FULL fixed serving matrix before dynamically generated open-loop cases is:

- **64** original V6 single-node benchmark points
- **11** V8 1M-extension points
- **36** scale-out points = 4 topologies × 3 contexts × 3 vLLM network modes
- **111 fixed serving points total**, plus dynamically generated open-loop points

Do **not** hard-code `111` as “completed.” It is the configured fixed matrix. Completed/failed/skipped counts must come from `coverage.json` / `FINAL_VALIDATION.json`.

---

# 2. Frozen V8-FULL matrices the dashboard must understand

## 2.1 Hardware / smoke network modes

The hardware/fabric layer keeps the full curve:

```text
GCP_NATIVE
GCP_CAPPED_100G
GCP_CAPPED_50G
GCP_CAPPED_20G
GCP_CAPPED_10G
```

Use all five for:

- forward + reverse iperf
- NCCL SendRecv/PP proxy
- cross-node TP2 / TP8 / TP16 AllReduce
- hardware transport sensitivity

The hardware dashboard should therefore retain the **10G and 50G** points.

## 2.2 vLLM scale-out network modes

The expensive model runs intentionally use only:

```text
GCP_NATIVE
GCP_CAPPED_100G
GCP_CAPPED_20G
```

There is **no 10G vLLM model-run state in V8-FULL**.

## 2.3 Scale-out topologies

```text
tp4_pp2_dist   = TP4 / PP2
tp8_pp2_dist   = TP8 / PP2
tp4_pp4_dist   = TP4 / PP4
tp16_pp1_dist  = TP16 / PP1
```

Critical topology semantics:

- `TP16/PP1` is **one TP16 group spanning both nodes**. Its TP collectives cross the network.
- `TP8/PP2` is one TP8 stage per node with a remote PP boundary.
- `TP4/PP4` uses four TP4 pipeline stages across two nodes. Do not assume every logical PP boundary is remote; use actual placement evidence.
- `TP4/PP2` is one TP4 stage per node and a remote PP boundary. **It is not a split cross-node TP ring.**

## 2.4 Scale-out contexts

For every topology and every vLLM network mode:

```text
128K c1
512K c1
1,000,000 c1
```

1M remains safety-gated after the prerequisite long-context case. A gate skip is a valid status but does **not** count as complete full coverage.

---

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
│   ├── GCP_NATIVE/
│   │   ├── network_validation/
│   │   │   ├── NETWORK_MODE.json
│   │   │   ├── IPERF_VALIDATION.json
│   │   │   ├── iperf_forward.json
│   │   │   ├── iperf_reverse.json
│   │   │   ├── node0_qdisc.txt
│   │   │   ├── node0_class.txt
│   │   │   ├── node1_network_state.txt
│   │   │   └── NCCL_ENV.txt
│   │   ├── results/
│   │   └── summary_v8full/
│   ├── GCP_CAPPED_100G/
│   │   ├── network_validation/
│   │   ├── results/
│   │   └── summary_v8full/
│   └── GCP_CAPPED_20G/
│       ├── network_validation/
│       ├── results/
│       └── summary_v8full/
│
├── profiles_single_node/
├── profiles_torch_single_node/
├── profiles_multi_node_native/
├── profiles_multi_node_capped/
│   ├── GCP_CAPPED_100G/
│   └── GCP_CAPPED_20G/
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
scaleout_1m_all_networks_completed
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

Use:

```text
hardware_processed/nccl_points.csv
hardware_processed/iperf.csv
hardware_processed/nvbandwidth_metrics.csv
hardware_processed/babelstream.csv
hardware_processed/cutlass.csv
hardware_processed/summary.json
hardware_processed/validation_hw.json
```

Use `hardware_raw/` only for drill-down/evidence links and debugging.

## 6.2 Recommended top-level tabs for the smoke dashboard

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

Do not display legacy “RTX 6000 Ada”, “48 GB”, or “PCIe Gen4” labels. The V8 target is RTX PRO 6000 Blackwell Server Edition.

### Tab B — Local Memory / PCIe

Charts:

1. H2D bandwidth by GPU/node
2. D2H bandwidth by GPU/node
3. D2D bandwidth matrix or same-NUMA vs cross-NUMA grouping
4. D2D latency
5. BabelStream Copy/Add/Triad/Dot by representative GPU/NUMA island

Each chart must link to the underlying NVBandwidth/BabelStream raw file.

### Tab C — Local NCCL / TP4 vs TP8

Charts:

1. Native TP4 AllReduce latency vs message size
2. Native TP8 AllReduce latency vs message size
3. Native TP4/TP8 AllGather
4. Native TP4/TP8 ReduceScatter
5. Effective algorithm/bus bandwidth

**Primary native chart filter:** exclude any row tagged as forced transport / sensitivity.

Create a separate “Transport sensitivity” panel for:

```text
P2P SYS
P2P PHB
P2P disabled
```

Never merge those into the native series.

### Tab D — Network Sweep

For all five hardware network modes:

```text
Native / 100G / 50G / 20G / 10G
```

Charts:

1. iperf forward Gbps vs configured cap
2. iperf reverse Gbps vs configured cap
3. SendRecv latency vs message size, one series per network mode
4. SendRecv bandwidth vs message size
5. cap-validation status

Show the configured cap **and measured bandwidth**. A cap is not the measured throughput.

### Tab E — Cross-node Collectives

For TP2 / TP8 / TP16 and all hardware network modes:

- AllReduce latency vs message size
- AllReduce bandwidth vs message size
- sensitivity to bandwidth cap

This is where the team can see how wide TP becomes network-sensitive.

### Tab F — Compute Reference

CUTLASS charts:

- 8192³ reference GEMM
- Kimi-width `N=K=7168` reference shapes
- runtime / GFLOP/s when parsed

Label this clearly:

> **FP16 tensor-core reference compute roof. Not Kimi K3 MXFP4 model performance.**

### Tab G — Evidence

Searchable table with:

```text
node
kind
tp
network_provenance
cap_gbit
size_label
size_bytes
time_us
algbw_GBs
busbw_GBs
raw file
validation status
```

Include direct source path / evidence drill-down.

---

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
Network evidence: pass/fail
Both-node telemetry: pass/fail
```

Do not put invented runtime-share percentages such as “GPU 48%, TP 22%, PP 8%, vLLM 14%” on Executive unless the profiler analysis actually produced a validated critical-path attribution.

Keep observations workload-scoped. Example wording:

> “At 128K c1 on GCP_CAPPED_20G, topology X had the lowest measured TTFT among the four tested topologies.”

Not:

> “Topology X is the best architecture.”

---

# 9. Scale-Up tab — V8 requirements

Scale-Up is **single-node only**.

Primary dimensions:

```text
TP = 4 / 8
context
concurrency
chunk size
scheduler settings
KV dtype
```

Required charts:

1. TP4 vs TP8 TTFT at measured context points
2. TP4 vs TP8 TPOT at measured context points
3. output throughput at matched workload
4. TTFT / TPOT vs concurrency for contexts where the matrix actually exists
5. local TP4 vs TP8 NCCL correlation panel using V8 hardware data

### Critical chart rule

Do not plot 32K/64K/256K as “measured” unless V8 actually has rows at those contexts.

Use:

- solid marker = measured
- dashed line = derived/interpolated, only if the product needs it
- no marker / `NOT RUN` = absent

If you fit an estimated crossover, label it `DERIVED`, not `MEASURED`.

---

# 10. Scale-Out tab — this is the biggest V8 dashboard change

The V6 dashboard treated scale-out mostly as one topology comparison. V8 introduces a real **topology × context × network** cube.

## 10.1 Required selectors

```text
Network:
  GCP_NATIVE
  GCP_CAPPED_100G
  GCP_CAPPED_20G

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

## 10.2 Required scale-out charts

### Chart 1 — Topology comparison at selected network/context

Four bars/points:

```text
TP4/PP2
TP8/PP2
TP4/PP4
TP16/PP1
```

### Chart 2 — Network sensitivity by topology

For each topology plot:

```text
Native → 100G → 20G
```

for TTFT and/or throughput.

Do not include 10G in vLLM charts because V8 does not run vLLM at 10G.

### Chart 3 — Context scaling per topology

```text
128K → 512K → 1M
```

at the selected network mode.

### Chart 4 — 1M scale-out matrix

A 4 × 3 matrix/heatmap or grouped bars:

| Topology | Native | 100G | 20G |
|---|---:|---:|---:|
| TP4/PP2 | status + metric | status + metric | status + metric |
| TP8/PP2 | status + metric | status + metric | status + metric |
| TP4/PP4 | status + metric | status + metric | status + metric |
| TP16/PP1 | status + metric | status + metric | status + metric |

Every cell must display status. A safety-skipped cell must not look like zero latency.

## 10.3 Network verification panel

Next to each selected network mode show:

- configured cap
- measured forward iperf
- reverse iperf availability
- qdisc/cap validation
- network provenance

This prevents the dashboard from assuming “100G configured = exactly 100G measured.”

## 10.4 Remove/replace old causal claims

Do not automatically say:

- “Pipeline Parallelism Superiority”
- “TP16 saturates the network”
- “PP masks transport latency”
- “X is recommended / Y should be avoided”

unless profiler/network evidence directly supports the mechanism.

Use:

**Observation → Interpretation + confidence → workload-scoped implication → next evidence.**

---

# 11. Long Context tab — V8 must make 1M a first-class dataset

This tab is no longer just “did 1M run?” It must expose the different 1M regimes.

## 11.1 Single-node 1M sections

Required V8 views:

### TP4 vs TP8 1M concurrency

```text
TP4: c1 → c2 → c4
TP8: c1 → c2 → c4
```

Plot:

- TTFT
- TPOT
- output throughput
- queue/waiting requests
- peak KV usage
- preemptions

### TP4 1M scheduler sensitivity

```text
max_num_seqs = 4 / 8 / 16 at c4
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

## 11.2 Distributed 1M

Add a dedicated panel sourced from:

```text
final_validation/ONE_MILLION_COVERAGE.md
final_validation/coverage.json
final_validation/combined_vllm_runs.json
```

Show all 12 required distributed 1M cells:

```text
4 topologies × Native/100G/20G
```

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

V8 has four profile evidence classes:

```text
single-node Nsight
single-node PyTorch profiler
native distributed Nsight
capped distributed Nsight (100G / 20G, matched 128K prefill)
```

## 13.1 Default distributed profiler matrix

Native:

- all four topologies × 128K prefill
- all four × 8K decode
- all four × 8K c8 batched decode
- TP4/PP4 512K prefill (heavy default)
- TP16/PP1 512K prefill (heavy default)

Capped:

- all four topologies × 128K prefill @100G
- all four topologies × 128K prefill @20G

Expected distributed profile validations by default: **22**.

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
tp
pp
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
| New capped distributed profiles | `profiles_multi_node_capped/GCP_CAPPED_100G/`, `...20G/` |
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

1. **Network selector** on Scale-Out and Profiler:
   - Native
   - 100G
   - 20G
2. **1M scale-out grid** with all 12 required distributed cells.
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

---

# 18. Evidence/provenance badges to use consistently

Recommended badges:

```text
MEASURED-GCP-HW
MEASURED-48B
MEASURED-48B-PROFILE
GCP_NATIVE
GCP_CAPPED_100G
GCP_CAPPED_50G
GCP_CAPPED_20G
GCP_CAPPED_10G
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
- [ ] Shows all five hardware network modes.
- [ ] Separates native NCCL from forced P2P sensitivity.
- [ ] Shows TP2/TP8/TP16 cross-node data.
- [ ] Labels CUTLASS as reference compute only.
- [ ] Has raw-evidence paths.
- [ ] Shows `validation_hw.json` state.

## V8 runtime dashboard acceptance

- [ ] Reads `FINAL_VALIDATION.json` first.
- [ ] Reads both `coverage.json` and `combined_vllm_runs.json`.
- [ ] Keeps the seven top-level V6 dashboard tabs.
- [ ] Scale-Out has Native/100G/20G selector.
- [ ] No vLLM 10G series is shown.
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
At 128K c1 under GCP_CAPPED_20G, <topology> measured <TTFT> and <throughput>.

Interpretation [Medium]:
The result is consistent with <smaller/larger TP communication pressure or PP behavior>, but the endpoint metric alone does not prove the cause.

Implication:
For this exact 128K c1 / 20G workload, <topology> is the leading measured configuration for <metric>.

Next evidence:
Correlate per-rank NCCL time, PP Send/Recv, idle gaps, and Ray placement from the matched 128K capped profile.

Evidence:
GCP_CAPPED_20G / <case> / 128k_c1 / N=<sample count> / <manifest path>
```

---

# 22. Team workflow after the V8-FULL run finishes

Follow this order:

1. **Do not open the dashboard first.** Check `FINAL_VALIDATION.json`.
2. Confirm `hardware_required_ok`, `network_evidence_ok`, `nccl_policy_ok`, and `scaleout_telemetry_ok`.
3. Check `coverage_counts`, `failed_count`, `not_run_count`, and `safety_skipped_count`.
4. Check `ONE_MILLION_COVERAGE.md` and `SCALEOUT_NETWORK_COVERAGE.md`.
5. Confirm the 12 required distributed 1M cells have the expected status.
6. Confirm `combined_vllm_runs.json` contains measured rows for completed cases.
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

# 24. Final deliverables expected from the dashboard team

Please produce two updated artifacts after the V8 run:

## Deliverable A — V8 Hardware / Smoke Dashboard

Successor to the V4 hardware/fabric dashboard.

Must cover:

```text
System/topology
Local memory + PCIe
Native local NCCL
Transport sensitivity
Network Native/100/50/20/10G
Cross-node TP2/TP8/TP16
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
Native/100G/20G scale-out selector
128K/512K/1M topology matrix
all four distributed topologies
TP4 + TP8 1M c1/c2/c4
1M scheduler sweep
1M FP8-KV
actual 1M prefix reuse
both-node telemetry validation
NCCL-policy validation
distributed native + capped profiler evidence
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

# 25. Final instruction

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
