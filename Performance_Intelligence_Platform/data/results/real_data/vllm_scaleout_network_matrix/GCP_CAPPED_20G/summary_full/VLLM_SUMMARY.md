# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_pp2_dist | 128k_c1 | 131072 | 1 | 0.31 | 2859.20 | 5.52 | 19.95 | 0.008 | 0 | 0 | CAPTURED |
| tp4_pp2_dist | 512k_c1 | 524288 | 1 | 0.05 | 18371.56 | 7.94 | 1.72 | 0.031 | 0 | 0 | CAPTURED |
| tp4_pp2_dist | 1m_c1 | 1000000 | 1 | 0.02 | 53127.08 | 10.55 | 0.60 | 0.059 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 128k_c1 | 131072 | 1 | 0.30 | 2810.19 | 7.59 | 19.46 | 0.008 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 512k_c1 | 524288 | 1 | 0.06 | 15545.56 | 9.92 | 2.02 | 0.031 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 1m_c1 | 1000000 | 1 | 0.02 | 41471.62 | 12.51 | 0.76 | 0.059 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 128k_c1 | 131072 | 1 | 0.43 | 1960.87 | 5.65 | 27.62 | 0.004 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 512k_c1 | 524288 | 1 | 0.09 | 11134.24 | 8.10 | 2.81 | 0.014 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 1m_c1 | 1000000 | 1 | 0.03 | 29683.66 | 10.71 | 1.07 | 0.027 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 128k_c1 | 131072 | 1 | 0.03 | 31053.11 | 15.37 | 2.00 | 0.016 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 512k_c1 | 524288 | 1 | 0.01 | 128275.46 | 17.72 | 0.25 | 0.064 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 1m_c1 | 1000000 | 1 | 0.00 | 256889.47 | 20.57 | 0.12 | 0.121 | 0 | 0 | CAPTURED |
