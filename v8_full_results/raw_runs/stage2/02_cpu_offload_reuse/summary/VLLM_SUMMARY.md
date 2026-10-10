# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_native_offload_reuse_test | 128k_c1 | 131072 | 1 | 0.19 | 4900.80 | 5.91 | 12.14 | 0.138 | 0 | 0 | CAPTURED |
| tp4_native_offload_reuse_test | 512k_c1 | 524288 | 1 | 0.03 | 32988.18 | 8.53 | 1.91 | 0.551 | 0 | 0 | CAPTURED |
| tp4_native_offload_reuse_test | 1m_c1 | 1000000 | 1 | 0.01 | 181171.96 | 10.84 | 0.18 | 0.998 | 0 | 2 | CAPTURED |
| tp4_native_offload_reuse_test | offload_revisit_a | 600256 | 1 | 0.02 | 41422.82 | 8.71 | 0.77 | 0.633 | 0 | 0 | CAPTURED |
