# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp8_r1_continuous_context_curve | 16k_c1 | 16384 | 1 | 1.05 | 531.46 | 6.74 | 66.95 | 0.002 | 0 | 0 | CAPTURED |
| tp8_r1_continuous_context_curve | 32k_c1 | 32768 | 1 | 0.67 | 1066.26 | 6.88 | 42.67 | 0.004 | 0 | 0 | CAPTURED |
| tp8_r1_continuous_context_curve | 64k_c1 | 65536 | 1 | 0.38 | 2203.83 | 7.01 | 24.19 | 0.008 | 0 | 0 | CAPTURED |
| tp8_r1_continuous_context_curve | 256k_c1 | 262144 | 1 | 0.09 | 10386.27 | 8.43 | 5.86 | 0.033 | 0 | 0 | CAPTURED |
