# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_8k_chunk_control_8192 | 8k_c4 | 8192 | 4 | 1.27 | 938.59 | 8.68 | 324.57 | 0.005 | 0 | 0 | CAPTURED |
| tp4_8k_chunk_control_8192 | 8k_c32 | 8192 | 32 | 2.98 | 1618.06 | 35.55 | 763.94 | 0.040 | 26 | 0 | CAPTURED |
| tp4_8k_chunk_fix_8448 | 8k_c4 | 8192 | 4 | 1.60 | 544.03 | 7.66 | 409.59 | 0.005 | 1 | 0 | CAPTURED |
| tp4_8k_chunk_fix_8448 | 8k_c32 | 8192 | 32 | 3.06 | 1517.58 | 34.97 | 782.22 | 0.040 | 27 | 0 | CAPTURED |
