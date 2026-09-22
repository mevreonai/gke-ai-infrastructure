# V8-FULL Dashboard Decision-Intelligence Specification — Native-Only Campaign — UI V4 Full Configuration Identity

## Purpose

This document is the post-run dashboard interpretation contract for the V8-FULL campaign. It converts raw benchmarking, hardware, telemetry, network and profiler data into deployment guidance.

The dashboard must answer: **for this workload, which deployment configuration is appropriate, what limits it, what changes when context/load/network/topology changes, and what evidence supports the conclusion?**

No V8 result should be presented as measured until the V8-FULL run has completed and the corresponding evidence row passes validation.

### V8-FULL execution-scope update — Native network only

The lab execution was narrowed because of limited lab availability. **All V8-FULL network-dependent hardware, scale-out vLLM, and distributed profiler runs in this campaign use `GCP_NATIVE` only.** The previously planned `GCP_CAPPED_100G`, `GCP_CAPPED_50G`, `GCP_CAPPED_20G`, and `GCP_CAPPED_10G` sensitivity points were **not executed in this campaign**.

This is a scope reduction, not permission to weaken the dashboard. The UI must still preserve `network_provenance` as a first-class dimension so future capped or local-fabric runs can be added without redesign. For this run:

- `GCP_NATIVE` = measured when evidence exists.
- capped modes = **not part of the executed campaign**; do not synthesize, interpolate, or project them.
- bandwidth-sensitivity conclusions = `UNRESOLVED` / future validation.
- native topology, long-context, scheduler/KV, compute, NCCL, telemetry, and profiler evidence must still be fully surfaced.
- missing cap sweeps must never cause real native data to be omitted or the UI to become less informative.

### Validation-scope rule

The **collector/validation configuration must agree with the executed native-only campaign**. The dashboard must not hide a validation failure caused by a stale validator that still expects capped runs. If `FINAL_VALIDATION.json` still requires 100G/50G/20G/10G cases that were deliberately removed from the campaign, fix or annotate the campaign validation scope before publishing the dashboard. The UI must report the validator truth; it must not locally override a failed run into a pass.



## UI V4 amendment — full configuration identity is mandatory

UI V4 makes **configuration identity part of every measurement**, not merely a tooltip or Evidence-only field.

### Visible naming rule

Every chart, legend, decision table, profile row, and recommendation must show at least the complete logical parallelism identity:

```text
TPx/PPy
```

Examples used by the executed V8 campaign:

```text
Single-node:
  TP4/PP1
  TP8/PP1

Scale-out / distributed:
  TP4/PP2
  TP8/PP2
  TP4/PP4
  TP16/PP1
```

Do **not** label a measured series only `TP4` or `TP8` when the intended configuration is `TP4/PP1` or `TP8/PP1`.

### Full evidence identity

The complete measurement key must retain, where available:

```text
model_id
model_revision
TP
PP
DP
EP
rank -> node -> GPU UUID -> PCI bus -> NUMA/socket
context / requested input tokens
output tokens
client concurrency or offered RPS
max_num_seqs
max_num_batched_tokens
KV-cache dtype
prefix caching
offload configuration
attention / MoE / runtime backend
network_provenance
run_id / case_id / profile_id
```

A compact `config_id` may be derived from these fields, but the source fields must remain available.

### Manifest-binding rule

If the V8 design does not explicitly fix a configuration field for a specific sensitivity case, the dashboard must bind that field from the actual case/profile manifest or evidence row.

**Never infer or assume an unspecified TP/PP, DP/EP, scheduler, KV, prefix, offload, or backend setting.**

### Per-tab identity contract

| Tab | Minimum visible configuration identity |
|---|---|
| Executive | Candidate configuration must show `TPx/PPy`; workload/SLO remains explicit |
| Scale-Up | `TP4/PP1` vs `TP8/PP1` for the current single-node V8 matrix |
| Scale-Out | `TP4/PP2`, `TP8/PP2`, `TP4/PP4`, `TP16/PP1` + `GCP_NATIVE` |
| Long Context | Single-node `TP4/PP1` / `TP8/PP1`; distributed 1M uses all four scale-out topologies |
| Scheduler & KV | Every series carries exact `TPx/PPy` before scheduler/KV modifiers |
| Profiler | Every trace/profile row carries the exact `TPx/PPy` captured |
| Evidence | Full configuration key; `TPx/PPy` is mandatory and all additional dimensions remain drill-down accessible |

This amendment changes **presentation, provenance, and decision traceability only**. It does not redesign or add benchmark runs.


## 1. Dashboard objectives

The UI should help engineers answer:

- Can the model fit at the required context?
- Can it meet the TTFT/TPOT SLO?
- What concurrency/request rate can be admitted before latency collapses?
- Which TP/PP topology fits the workload?
- What does the topology do on the measured native fabric, and what network-bandwidth sensitivity remains unresolved because capped sweeps were not executed?
- Is the bottleneck compute, memory, PCIe/NUMA, NCCL, network, scheduler/KV, CPU launch, or runtime/framework overhead?
- Which knobs materially change performance?
- Which knobs show low sensitivity and should not consume engineering time?
- Which conclusions are measured, timeline-attributed, derived, or unresolved?
- What still needs to be validated on the production/local cluster?

## 2. Keep the seven-tab architecture

1. Executive
2. Scale-Up
3. Scale-Out
4. Long Context
5. Scheduler & KV
6. Profiler
7. Evidence

V8-FULL should enrich these views rather than replace them.

## 3. Executive: Deployment Decision Map

Create a workload-oriented map:

| Workload regime | Primary SLO | Candidate configuration (TP/PP) | Observed bottleneck | Native fabric / sensitivity status | Memory/KV state | Confidence |
|---|---|---|---|---|---|---|
| Short-context interactive | TPOT | post-run | post-run | Native measured / N/A single-node | measured | Direct/Timeline |
| Long prompt, c1 | TTFT | post-run | post-run | Native measured / N/A single-node | measured | Direct/Timeline |
| 512K serving | TTFT + TPOT | post-run | post-run | Native measured / N/A single-node | measured | Direct/Timeline |
| 1M c1 | feasibility + TTFT | post-run | post-run | Native measured / N/A single-node | measured | Direct/Timeline |
| 1M concurrent | TTFT/TPOT + queue | post-run | post-run | Native measured / N/A single-node | measured | Direct/Timeline |
| Multi-node native fabric | latency + throughput | post-run | post-run | Native measured; cap sensitivity unresolved | measured | Direct/Timeline |

Do not populate candidate configuration or bottleneck without supporting evidence.

## 4. Topology is workload-dependent

Required charts:

- TTFT vs context: matched `TP4/PP1` vs `TP8/PP1` and distributed topology points.
- TPOT vs context.
- Prefill-vs-decode topology trade-off matrix.
- Throughput-vs-latency Pareto.

Never use a universal "best topology" badge. Use workload-scoped wording such as:

> Lowest TTFT among matched configurations for this workload.

## 5. Long-context / 1M deployment playbook

The Long Context tab must separately answer:

### Can it fit?
Use GPU memory, KV utilization/capacity, offload, admission and explicit OOM evidence.

### Can it finish?
Use completion/failure/timeout/preemption/engine status and safety-gate status.

### Is latency usable?
Use TTFT, TPOT/ITL, E2E latency and output throughput.

### Can it serve concurrent requests?
Use c1/c2/c4, queue, scheduler state, throughput, preemption and open-loop load where available.

A headline saying only "1M supported" is insufficient.

## 6. Required V8 1M matrix

### Single node

- `TP4/PP1` c1/c2/c4
- `TP8/PP1` c1/c2/c4
- `TP4/PP1` max_num_seqs sweep
- FP8-KV 1M — exact TP/PP must bind from the matched evidence row
- prefix-reuse 1M — exact TP/PP must bind from the case manifest
- applicable preserved V6 1M cases — preserve their exact TP/PP lineage

### Scale-out — executed campaign

For each topology:

- TP4/PP2
- TP8/PP2
- TP4/PP4
- TP16/PP1

under the **only executed network mode**:

- `GCP_NATIVE`

at:

- 128K
- 512K
- 1M

This gives **4 required distributed 1M cells** and **12 fixed native scale-out operating points** across all three contexts.

The data model must still carry `network_provenance`, but the dashboard must not fabricate empty 100G/50G/20G/10G measurements. If the UI keeps future network columns for design continuity, render them as `NOT EXECUTED IN THIS CAMPAIGN` / `NOT_RUN`, visually distinct from failures.

Every executed cell must show one of:

`COMPLETED | FAILED | SAFETY_SKIPPED | NOT_RUN`

Never render missing data as zero.

## 7. Capacity-cliff / SLO envelope

For each context, visualize:

- x-axis: concurrency or offered RPS
- y-axis: achieved throughput
- overlays or companion charts: TTFT and TPOT
- markers: queue time, KV%, preemption

Identify the **capacity knee**: where throughput gain flattens while TTFT/TPOT/queue increases sharply.

Do not call this "max users."

The deployment output is an SLO-compatible admission-control envelope.

## 8. Network requirement / sensitivity

## Native fabric characterization and deferred network sensitivity

This V8-FULL campaign contains **native-network evidence only**.

For each matched topology/context, compare performance on `GCP_NATIVE` and correlate it with the native hardware/fabric measurements that were actually captured:

- native iperf forward/reverse where available;
- RTT / interface / MTU provenance where available;
- native NCCL SendRecv;
- native cross-node TP2 / TP8 / TP16 collectives;
- vLLM TTFT / TPOT / throughput / queue / KV;
- distributed Nsight and both-node telemetry.

### Required native scale-out table

| Topology | Context | Native TTFT | Native TPOT | Native output TPS | Native fabric evidence | Status |
|---|---:|---:|---:|---:|---|---|
| TP4/PP2 | 128K/512K/1M | measured | measured | measured | linked | status |
| TP8/PP2 | 128K/512K/1M | measured | measured | measured | linked | status |
| TP4/PP4 | 128K/512K/1M | measured | measured | measured | linked | status |
| TP16/PP1 | 128K/512K/1M | measured | measured | measured | linked | status |

### What the dashboard may conclude

It may describe:
- native-fabric performance;
- topology ordering for a matched workload on the native fabric;
- native NCCL / SendRecv / profiler behavior;
- evidence-backed communication or idle behavior from timelines.

### What it must not conclude

It must **not** derive:
- 100G / 50G / 20G / 10G degradation curves;
- minimum required network bandwidth;
- crossover bandwidth;
- equivalence to a local 2×10GbE deployment;
- a network-sizing recommendation that requires bandwidth-sensitivity measurements.

Show these as:

> **Bandwidth sensitivity: UNRESOLVED in this V8 campaign — capped sweeps deferred because of lab-window constraints.**

Preserve the network dimension in the schema so a future supplemental cap sweep can be merged without changing the UI architecture.

## 9. Hardware ceiling vs application achieved

Connect:

- BabelStream -> practical GPU memory bandwidth
- NVBandwidth -> H2D/D2H/D2D/P2P
- P2P latency
- NCCL AR/AG/RS
- NCCL SendRecv
- cross-node TP2/TP8/TP16
- iperf/ping
- CUTLASS/GEMM reference

to:

- vLLM TTFT/TPOT/throughput
- GPU/node telemetry
- network/NCCL primitives
- profiler traces
- raw artifacts

The UI should answer:

> Is the application slow because the hardware/fabric is slow, or because the runtime is not exploiting the available capability?

## 10. Topology / NUMA / placement

Every relevant result should carry:

`rank -> node -> GPU UUID -> PCI bus -> NUMA/socket`

Scale-out diagrams must reflect real communication:

- TP16/PP1: cross-node TP collectives.
- TP8/PP2: TP8 stage per node; remote PP boundary.
- TP4/PP4: two TP4 stages per node; remote PP boundary between node groups.
- TP4/PP2: one TP4 stage per node; remote PP boundary.

TP/PP numbers without physical placement are insufficient deployment evidence.


### Scheduler / KV configuration identity

Scheduler and cache conclusions are configuration-specific.

For every Scheduler & KV chart:

- show exact `TPx/PPy` in the series/legend;
- keep context and concurrency/RPS separate from scheduler settings;
- show `max_num_seqs`, `max_num_batched_tokens`, KV dtype, prefix/offload only when they are actual case fields;
- never merge queue/KV/preemption data from unmatched TP/PP configurations.

For the planned V8 1M `max_num_seqs` extension, the visible identity is:

```text
TP4/PP1 · 1M · c4 · max_num_seqs = 4 / 8 / 16
```

If the preserved 512K max_num_seqs lineage is surfaced, label it separately with its own exact configuration.

For generated open-loop cases, bind TP/PP from the generated case manifest rather than assuming it.


## 11. Profiler: Where did the time go?

Use critical-path accounting:

`T_workload = A_GPU + B_TP + C_PP + D_PCIe/offload + E_runtime + F_CPU/launch + G_other - O_overlap`

Do not force this into percentages unless the timeline supports them.

Required table:

| Component | Prefill | Decode | Evidence source | Confidence |
|---|---:|---:|---|---|
| GPU kernels | timeline | timeline | Nsight | High/Med |
| TP NCCL | timeline | timeline | Nsight/NCCL | High/Med |
| PP Send/Recv + idle | timeline | timeline | distributed Nsight | High/Med |
| CPU/CUDA launch gaps | timeline | timeline | CUDA API | High/Med |
| vLLM scheduler/runtime | measured/derived | measured/derived | Prometheus/runtime | Med |
| PCIe/offload | measured/timeline | measured/timeline | telemetry/Nsight | Med |
| overlap | timeline | timeline | Nsight | High/Med |
| residual | derived | derived | E2E-attributed | Derived |

Never sum kernel time across ranks and call it wall-clock latency.


### Profiler configuration identity

A profiler trace is evidence only for the exact topology and workload it captured.

The UI must expose:

```text
profile_id
TP/PP
context
prefill/decode mode
concurrency
network_provenance
ranks expected/captured
node0/node1 trace presence
PROFILE_VALIDATION status
```

For the planned native distributed profiler matrix, show topology names explicitly rather than the phrase "four topologies":

```text
TP4/PP2
TP8/PP2
TP4/PP4
TP16/PP1
```

for:
- 128K prefill;
- 8K decode c1;
- 8K decode c8;

plus heavy 512K prefill:
- `TP4/PP4`;
- `TP16/PP1`.

If the executed profiler manifest differs, the manifest wins.

Do not transfer a mechanism observed in one topology to another topology without independent trace evidence.


## 12. What each tool should tell the user

- **vLLM benchmarks**: TTFT, TPOT, throughput, load, failures/admission.
- **vLLM/Prometheus**: queue, running/waiting, KV, preemption, scheduler/runtime state.
- **Nsight Systems**: critical path, CPU/GPU timeline, NCCL overlap, PP bubble/idle, launch gaps.
- **PyTorch Profiler**: framework/operator attribution and CPU overhead.
- **Nsight Compute** if used later: why a selected kernel is inefficient.
- **NCCL Tests**: available collective performance independent of model/runtime.
- **NVBandwidth/P2P**: PCIe/NUMA/data-movement capability.
- **BabelStream**: practical memory-bandwidth ceiling.
- **CUTLASS/GEMM**: representative compute reference.
- **iperf/network tools**: network capability independent of NCCL/model.

The dashboard should connect tools to deployment questions, not simply list test outputs.

## 13. Knobs that matter / knobs that do not

Create a tuning-sensitivity table:

| Knob | Tested range | Workload | Metric delta | Sensitivity | Deployment implication | Evidence |
|---|---|---|---:|---|---|---|
| TP width | ... | ... | ... | high/med/low | ... | run IDs |
| chunk size | ... | ... | ... | ... | ... | ... |
| max_num_seqs | ... | ... | ... | ... | ... | ... |
| KV dtype | ... | ... | ... | ... | ... | ... |
| prefix cache | ... | ... | ... | ... | ... | ... |
| network mode | Native only in this campaign | scale-out | sensitivity not measurable | UNRESOLVED | supplemental cap sweep if needed | campaign scope + native evidence |

The activity should tell engineers both where to spend optimization effort and where not to.

## 14. Bottleneck regime map

Create:

| Context | Load | Phase | Supporting evidence | Bottleneck classification | Confidence |
|---|---|---|---|---|---|

Evidence types:
`DIRECT_MEASURED | TIMELINE_ATTRIBUTED | DERIVED | UNRESOLVED`

Do not assign a bottleneck without evidence.

## 15. Deployment recipe cards

After V8 validation, generate workload-specific cards containing:

- workload context/output/load/SLO
- measured phase: prefill/decode/mixed
- candidate topology or candidates
- native-fabric behavior and explicit bandwidth-sensitivity gap
- primary limiter
- memory/KV state
- runtime settings that matter
- settings with low measured sensitivity
- production validation still needed
- run/profile evidence IDs

Never turn this into a universal topology recommendation.

## 16. "What not to do" panel

Potential lessons, only promoted when evidence supports them:

- Do not choose topology from peak tokens/sec alone.
- Do not call admission success production capacity.
- Do not assume "fits in VRAM" means usable latency.
- Do not assume TP4/TP8 ordering is identical for prefill and decode.
- Do not extrapolate 128K behavior linearly to 1M.
- Do not infer network-bandwidth sensitivity or local-fabric equivalence from a native-only campaign.
- Do not infer NCCL/PP causality from E2E latency alone.
- Do not compare unmatched workloads.
- Do not use profiler-instrumented latency as benchmark latency.
- Do not treat CUTLASS numbers as model-kernel efficiency.
- Do not tune scheduler knobs blindly when compute/communication dominates.
- Do not render NOT_RUN/NOT_CAPTURED as zero.
- Do not use "best" without an explicit workload objective/SLO.

## 17. Mandatory annotation under important charts

**Observation** — literal measured fact.

**Interpretation [High/Medium/Low]** — plausible mechanism.

**Deployment implication** — what an engineer should consider.

**Next evidence / production validation** — what remains to be proven.

**Evidence** — run IDs, source class, N, profile ID.

This is required to keep facts separate from interpretation.

## 18. Post-run machine-readable analysis layer

Do not make frontend JavaScript re-derive important conclusions.

Add a post-processing layer such as:

```text
final_validation/dashboard_intelligence/
  DEPLOYMENT_FINDINGS.json
  DEPLOYMENT_FINDINGS.md
  BOTTLENECK_REGIME_MAP.csv
  TUNING_SENSITIVITY.csv
  SLO_CAPACITY_ENVELOPE.csv
  SCALEOUT_NATIVE_FABRIC.csv
  NETWORK_SENSITIVITY_GAP.md
  TOPOLOGY_WORKLOAD_MATRIX.csv
  DASHBOARD_DATA_CONTRACT.json
```

These should be generated only from validated V8 evidence.

## 19. Finding schema

Each finding should carry:

- finding_id
- status: MEASURED/TIMELINE_ATTRIBUTED/DERIVED/UNRESOLVED
- workload scope
- topology
- network provenance
- observation
- interpretation
- confidence
- deployment implication
- next validation
- metrics
- run IDs
- profile IDs
- raw artifact paths
- sample count

No finding should exist without evidence pointers.

## 20. Data-source hierarchy

### Completeness/status
- `final_validation/FINAL_VALIDATION.json`
- `final_validation/coverage.json`

### vLLM measurements
- `final_validation/combined_vllm_runs.json`
- per-case benchmark JSON/manifest

### Hardware
- `hardware_processed/*`
- underlying `hardware_raw/*`

### Network
- native network validation / provenance
- raw native NCCL/iperf
- campaign-scope record showing capped sweeps were not executed

### Profiler
- profile manifests / PROFILE_VALIDATION
- `.nsys-rep`
- SQLite/CUDA/NVTX/NCCL summaries
- PyTorch traces

### Provenance
- `RUN_CONFIG.env`
- readiness/preflight
- release/source SHA
- NCCL policy audit

Frontend hard-coded arrays must never be the source of truth.

## 21. V6 vs V8 handling

V6 remains a prior baseline and source of lessons. V8 is the new end-to-end evidence set.

Never silently merge them.

Every row should carry:
- suite_version
- run_id
- model revision
- runtime version
- network provenance
- evidence class

Only compare V6 and V8 where the workload/model/runtime conditions are sufficiently matched and the comparison is explicitly labeled.

## 22. Post-run review workflow

1. Validate FINAL_VALIDATION.
2. Confirm completed/failed/safety-skipped matrix.
3. Validate both-node telemetry.
4. Validate NCCL policy/provenance.
5. Build hardware primitive summary.
6. Build matched TP4/TP8 comparisons.
7. Build 1M feasibility/capacity analysis.
8. Build topology × context × `GCP_NATIVE` matrix; keep network provenance in the schema.
9. Parse profiler traces for critical-path evidence.
10. Generate bottleneck regime map.
11. Generate tuning-sensitivity table.
12. Generate SLO/capacity envelope.
13. Generate deployment recipe cards.
14. Generate "what not to do" lessons only where evidence supports them.
15. Link every chart/decision to evidence.
16. Review conclusions with systems/runtime owners before publishing.

## 23. Native-only scope must not reduce dashboard quality

The native-only change affects **one experimental dimension only**: controlled network-bandwidth sensitivity.

It must not remove or weaken:

- all measured single-node TP4/TP8 data;
- all 1M single-node extensions;
- all four native scale-out topologies;
- all 128K / 512K / 1M native scale-out points;
- hardware smoke and native-fabric primitives actually captured;
- NCCL policy/provenance;
- rank/node/GPU/NUMA placement evidence;
- both-node telemetry;
- scheduler/KV/open-loop evidence;
- Nsight/PyTorch profiler evidence actually captured;
- raw-artifact drill-down;
- measured vs derived vs unresolved status;
- workload-scoped deployment implications;
- V6 historical comparison where conditions are matched.

The UI should therefore remain just as rich in **deployment reasoning**. The only conclusion class intentionally absent is measured **bandwidth-cap sensitivity**. The correct response is to expose that as an evidence gap, not to fill it with projections.

## 24. Definition of success

The dashboard is successful if a deployment engineer can ask:

> What configuration should I investigate for my workload on the measured native fabric, and what still requires network-sensitivity validation?

and immediately see:

- matched measured data
- latency/throughput trade-offs
- context/concurrency limits
- native-fabric behavior and explicit bandwidth-sensitivity gap
- topology/placement
- hardware ceiling
- bottleneck evidence
- tuning sensitivity
- unresolved risks
- raw evidence

The dashboard should make **wrong deployment choices harder to make**.


### Evidence configuration key

Every plotted point must be reproducible from an Evidence row.

Conceptually:

```text
config_id =
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

The dashboard legend must show at least `TPx/PPy`; the Evidence drill-down shows the complete key.

Missing identity fields remain `UNKNOWN` / `UNRESOLVED`; they are never inferred.

