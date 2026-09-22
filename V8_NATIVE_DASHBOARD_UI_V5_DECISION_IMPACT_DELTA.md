# V8 Native Dashboard V5 — Decision-Impact Delta

## Objective

V5 preserves the V4 evidence discipline and seven-tab architecture, but changes the user experience from a benchmark/reporting dashboard into an operator-facing deployment decision system.

## V5 messaging changes

1. **Decision first, charts second.**
   - Executive opens with a 60-second deployment brief.
   - Every tab states the user question and the decision it should produce.

2. **No universal winner.**
   - Guidance is workload + SLO scoped.
   - Scale-Up explicitly separates prefill from decode.
   - Scale-Out makes topology ordering across 128K/512K/1M the central comparison.

3. **Long context becomes a readiness ladder.**
   - Fits → finishes → usable → concurrent → operational.
   - 1M admission success is not presented as production viability.

4. **Capacity becomes an admission decision.**
   - Scheduler explicitly defines a queue/latency/throughput knee.
   - Closed-loop concurrency is not called “users” or capacity.

5. **Profiler becomes causal decision support.**
   - Critical-path formula is explicit.
   - Every trace produces observation → mechanism/confidence → action → boundary.
   - Physical placement is surfaced beside topology.

6. **Evidence becomes clickable governance.**
   - Decision/chart → canonical row → manifest → metrics/telemetry/trace → raw artifacts.
   - DIRECT_MEASURED / TIMELINE_ATTRIBUTED / DERIVED / UNRESOLVED remain explicit.

7. **Precision messaging is corrected.**
   - Current V8 Kimi-Linear-48B surrogate is a BF16-weight baseline.
   - FP8-KV is a KV-cache sensitivity, not FP8 model weights.
   - MXFP4/NVFP4 weight-format comparisons are future supplemental evidence, not current V8 measurements.

8. **Native-only campaign boundary is more prominent.**
   - GCP_NATIVE is measured.
   - 10G/20G/50G/100G sensitivity, local 2×10GbE equivalence, and minimum network requirement remain unresolved.

## Highest-impact new UI elements

- 60-Second Deployment Brief
- Decision Funnel
- Decision Readiness / Evidence Health
- Prefill ↔ Decode Trade-off Map
- Scale-Out Topology × Context “Money Chart”
- Long-Context Readiness Ladder
- 512K → 1M Regime-Change Lens
- Explicit Capacity-Knee Decision Rule
- Profiler Critical-Path Ledger
- Rank/NUMA/Fabric Placement Lens
- Evidence Flow
- Safe-to-derive vs requires-new-evidence boundary
- Deployment Recipe Cards

## No new performance data

V5 introduces no fabricated benchmark values. All result fields remain `post-run`, `UNKNOWN`, `UNRESOLVED`, or manifest-bound until the validated V8 result tree is ingested.
