# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_pp4_dist | 1k_c1 | 1024 | 1 | 0.77 | 74.99 | 9.67 | 98.19 | 0.000 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 1k_c8 | 1024 | 8 | 2.20 | 216.12 | 26.97 | 281.06 | 0.001 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 1k_c32 | 1024 | 32 | 2.97 | 7610.38 | 19.50 | 380.73 | 0.001 | 24 | 0 | CAPTURED |
| tp4_pp4_dist | 8k_c1 | 8192 | 1 | 0.46 | 297.24 | 7.43 | 116.81 | 0.000 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 8k_c8 | 8192 | 8 | 0.92 | 720.68 | 31.39 | 234.43 | 0.002 | 2 | 0 | CAPTURED |
| tp4_pp4_dist | 8k_c32 | 8192 | 32 | 0.93 | 23054.50 | 31.96 | 237.57 | 0.002 | 24 | 0 | CAPTURED |
| tp4_pp4_dist | 128k_c1 | 131072 | 1 | 0.35 | 2060.12 | 13.25 | 22.10 | 0.004 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 128k_c2 | 131072 | 2 | 0.28 | 3742.35 | 52.25 | 18.17 | 0.007 | 1 | 0 | CAPTURED |
| tp4_pp4_dist | 128k_c4 | 131072 | 4 | 0.40 | 5435.43 | 71.28 | 25.75 | 0.015 | 3 | 0 | CAPTURED |
| tp4_pp4_dist | 128k_c8 | 131072 | 8 | 0.39 | 7470.87 | 206.64 | 24.89 | 0.029 | 7 | 0 | CAPTURED |
| tp4_pp4_dist | 512k_c1 | 524288 | 1 | 0.07 | 13537.22 | 22.95 | 2.25 | 0.014 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 512k_c2 | 524288 | 2 | 0.08 | 19326.08 | 221.06 | 2.43 | 0.029 | 1 | 0 | CAPTURED |
| tp4_pp4_dist | 512k_c4 | 524288 | 4 | 0.09 | 25872.54 | 538.07 | 2.89 | 0.043 | 3 | 0 | CAPTURED |
| tp4_pp4_dist | 1m_c1 | 1000000 | 1 | 0.03 | 30669.42 | 14.48 | 1.03 | 0.028 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 1m_c2 | 1000000 | 2 | 0.03 | 45048.41 | 489.07 | 1.05 | 0.055 | 1 | 0 | CAPTURED |
| tp4_pp4_dist | 1m_c4 | 1000000 | 4 | 0.03 | 78026.23 | 752.03 | 1.02 | 0.056 | 3 | 0 | CAPTURED |
