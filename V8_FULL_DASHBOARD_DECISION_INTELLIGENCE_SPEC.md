# V8-FULL Dashboard Decision-Intelligence Specification

## Purpose

This document is the post-run dashboard interpretation contract for the V8-FULL campaign. It converts raw benchmarking, hardware, telemetry, network and profiler data into deployment guidance.

The dashboard must answer: **for this workload, which deployment configuration is appropriate, what limits it, what changes when context/load/network/topology changes, and what evidence supports the conclusion?**

No V8 result should be presented as measured until the V8-FULL run has completed and the corresponding evidence row passes validation.

## 1. Dashboard objectives

The UI should help engineers answer:

- Can the model fit at the required context?
- Can it meet the TTFT/TPOT SLO?
- What concurrency/request rate can be admitted before latency collapses?
- Which TP/PP topology fits the workload?
- How much network bandwidth does the topology need?
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

| Workload regime | Primary SLO | Candidate topology | Observed bottleneck | Network sensitivity | Memory/KV state | Confidence |
|---|---|---|---|---|---|---|
| Short-context interactive | TPOT | post-run | post-run | Low/Med/High | measured | Direct/Timeline |
| Long prompt, c1 | TTFT | post-run | post-run | Low/Med/High | measured | Direct/Timeline |
| 512K serving | TTFT + TPOT | post-run | post-run | Low/Med/High | measured | Direct/Timeline |
| 1M c1 | feasibility + TTFT | post-run | post-run | Low/Med/High | measured | Direct/Timeline |
| 1M concurrent | TTFT/TPOT + queue | post-run | post-run | Low/Med/High | measured | Direct/Timeline |
| Multi-node constrained network | latency + throughput | post-run | post-run | Low/Med/High | measured | Direct/Timeline |

Do not populate candidate topology or bottleneck without supporting evidence.

## 4. Topology is workload-dependent

Required charts:

- TTFT vs context: matched TP4/TP8 and distributed topology points.
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
- TP4 c1/c2/c4
- TP8 c1/c2/c4
- TP4 max_num_seqs sweep
- FP8-KV 1M
- prefix-reuse 1M
- applicable preserved V6 1M cases

### Scale-out
For each:
- TP4/PP2
- TP8/PP2
- TP4/PP4
- TP16/PP1

under:
- GCP_NATIVE
- GCP_CAPPED_100G
- GCP_CAPPED_20G

at:
- 128K
- 512K
- 1M

Every cell must show exactly one status:
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

For matched topology/context, compare:

- GCP_NATIVE
- GCP_CAPPED_100G
- GCP_CAPPED_20G

Derived metrics:

`delta_ttft_pct = (TTFT_cap - TTFT_native) / TTFT_native * 100`

`delta_tpot_pct = (TPOT_cap - TPOT_native) / TPOT_native * 100`

`delta_output_tps_pct = (TPS_cap - TPS_native) / TPS_native * 100`

Required table:

| Topology | Context | Native | 100G | 20G | Sensitivity |
|---|---:|---:|---:|---:|---|

Do not label GCP_CAPPED_20G as LOCAL_REAL_2x10G.

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
| network cap | ... | ... | ... | ... | ... | ... |

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
- network sensitivity
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
- Do not equate a GCP traffic cap to a physical local NIC.
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
  SCALEOUT_NETWORK_SENSITIVITY.csv
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
- per-mode network validation
- raw NCCL/iperf

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
8. Build topology × context × network matrix.
9. Parse profiler traces for critical-path evidence.
10. Generate bottleneck regime map.
11. Generate tuning-sensitivity table.
12. Generate SLO/capacity envelope.
13. Generate deployment recipe cards.
14. Generate "what not to do" lessons only where evidence supports them.
15. Link every chart/decision to evidence.
16. Review conclusions with systems/runtime owners before publishing.

## 23. Definition of success

The dashboard is successful if a deployment engineer can ask:

> What configuration should I investigate for my workload?

and immediately see:

- matched measured data
- latency/throughput trade-offs
- context/concurrency limits
- network sensitivity
- topology/placement
- hardware ceiling
- bottleneck evidence
- tuning sensitivity
- unresolved risks
- raw evidence

The dashboard should make **wrong deployment choices harder to make**.
