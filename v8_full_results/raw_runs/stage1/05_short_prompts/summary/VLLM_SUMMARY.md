# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_short_prompts | 1k_c1 | 1024 | 1 | 1.47 | 48.90 | 4.95 | 188.80 | 0.000 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 1k_c8 | 1024 | 8 | 6.35 | 213.13 | 8.24 | 812.17 | 0.003 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 1k_c32 | 1024 | 32 | 11.17 | 459.61 | 18.89 | 1430.01 | 0.012 | 3 | 0 | CAPTURED |
| tp4_short_prompts | 2k_c1 | 2048 | 1 | 1.42 | 73.67 | 4.97 | 181.51 | 0.001 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 2k_c8 | 2048 | 8 | 5.45 | 287.12 | 9.26 | 697.53 | 0.004 | 0 | 0 | CAPTURED |
| tp4_short_prompts | 2k_c32 | 2048 | 32 | 8.73 | 657.29 | 23.62 | 1117.13 | 0.016 | 19 | 0 | CAPTURED |
