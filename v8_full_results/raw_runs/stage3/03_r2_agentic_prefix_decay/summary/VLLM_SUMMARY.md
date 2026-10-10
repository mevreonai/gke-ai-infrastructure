# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_r2_agentic_prefix_cache_decay | turn1_cold_1k | 1024 | 1 | 1.42 | 99.57 | 4.77 | 181.33 | 0.000 | 0 | 0 | CAPTURED |
| tp4_r2_agentic_prefix_cache_decay | turn2_cached_2k | 2048 | 1 | 1.47 | 72.98 | 4.79 | 187.93 | 0.001 | 0 | 0 | CAPTURED |
| tp4_r2_agentic_prefix_cache_decay | turn3_cached_3k | 3072 | 1 | 1.44 | 85.94 | 4.80 | 184.07 | 0.001 | 0 | 0 | CAPTURED |
| tp4_r2_agentic_prefix_cache_decay | turn4_cached_4k | 4096 | 1 | 1.40 | 102.76 | 4.80 | 179.74 | 0.001 | 0 | 0 | CAPTURED |
| tp4_r2_agentic_prefix_cache_decay | turn5_cached_5k | 5120 | 1 | 1.38 | 111.18 | 4.82 | 176.87 | 0.001 | 0 | 0 | CAPTURED |
