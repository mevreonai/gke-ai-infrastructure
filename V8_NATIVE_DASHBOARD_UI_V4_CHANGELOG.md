# V8 Native Dashboard UI V4 — Configuration Identity Changelog

## Why V4 exists

V2 added decision intelligence.  
V3 made Scale-Up and Long Context configuration naming explicit.  
V4 applies the same full configuration-identity convention consistently across **all seven tabs**, especially Scheduler & KV, Profiler, Executive, and Evidence.

## V4 changes

- Visible series/legend labels must show at least `TPx/PPy`.
- Single-node Scale-Up is explicitly `TP4/PP1` vs `TP8/PP1`.
- Scale-Out keeps `TP4/PP2`, `TP8/PP2`, `TP4/PP4`, `TP16/PP1`.
- Long Context carries exact TP/PP through concurrency/scheduler/KV/prefix/offload views.
- Scheduler & KV cannot merge unmatched topology series.
- Profiler identifies exact topology for every trace; planned distributed matrix is explicit at 14 cells.
- Evidence carries a full configuration key including TP/PP, DP/EP, placement, workload, scheduler/KV modifiers, backend, and network provenance.
- Unspecified fields are read from the manifest/evidence row; they are never assumed.
- No benchmark scope was added or changed by this UI revision.

## Campaign scope unchanged

- Network-dependent V8 measurements remain `GCP_NATIVE` only.
- Capped-network sensitivity remains `UNRESOLVED` / not executed.
- Missing data is never rendered as zero.
- All performance recommendations remain workload-scoped and evidence-backed.
