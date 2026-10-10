# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_8k_chunk_control_8192 | 8k_c4 | 8192 | 4 | 1.52 | 653.10 | 7.72 | 390.12 | 0.005 | 1 | 0 | CAPTURED |
| tp4_8k_chunk_control_8192 | 8k_c32 | 8192 | 32 | 2.94 | 1678.90 | 35.96 | 752.34 | 0.040 | 27 | 0 | CAPTURED |
| tp4_8k_chunk_fix_8448 | 8k_c4 | 8192 | 4 | 1.15 | 562.33 | 11.44 | 294.13 | 0.005 | 0 | 0 | CAPTURED |
| tp4_8k_chunk_fix_8448 | 8k_c32 | 8192 | 32 | 2.87 | 1605.18 | 37.22 | 735.66 | 0.040 | 27 | 0 | CAPTURED |
