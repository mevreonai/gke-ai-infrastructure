# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_short_prompts | 1k_c1 | 1024 | 1 | 1.46 | 48.98 | 4.99 | 187.39 | 0.000 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 1k_c8 | 1024 | 8 | 6.42 | 211.23 | 8.14 | 822.15 | 0.003 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 1k_c32 | 1024 | 32 | 11.29 | 457.72 | 18.67 | 1444.97 | 0.012 | 3 | 0 | CAPTURED |
| tp4_short_prompts | 2k_c1 | 2048 | 1 | 1.45 | 73.22 | 4.86 | 185.24 | 0.001 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 2k_c8 | 2048 | 8 | 5.45 | 286.23 | 9.27 | 697.63 | 0.004 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 2k_c32 | 2048 | 32 | 8.84 | 687.22 | 23.01 | 1131.24 | 0.016 | 15 | 0 | CAPTURED |
