# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_pp2_dist_load | 8k_c8 | 8192 | 8 | 1.48 | 1541.48 | 15.10 | 379.42 | 0.005 | 4 | 0 | CAPTURED |
| tp4_pp2_dist_load | 128k_c2 | 131072 | 2 | 0.34 | 4058.58 | 29.91 | 21.52 | 0.016 | 1 | 0 | CAPTURED |
| tp4_pp2_dist_load | 128k_c4 | 131072 | 4 | 0.36 | 6571.97 | 69.75 | 23.31 | 0.031 | 3 | 0 | CAPTURED |
| tp4_pp2_dist_load | 128k_c8 | 131072 | 8 | 0.38 | 8350.02 | 200.41 | 24.35 | 0.063 | 7 | 0 | CAPTURED |
| tp4_pp2_dist_load | 1m_c2 | 1000000 | 2 | 0.02 | 79420.07 | 281.35 | 0.61 | 0.090 | 1 | 0 | CAPTURED |
| tp4_pp2_dist_load | 1m_c4 | 1000000 | 4 | 0.02 | 131438.77 | 417.16 | 0.61 | 0.090 | 3 | 0 | CAPTURED |
| tp8_pp2_dist_load | 8k_c8 | 8192 | 8 | 1.32 | 1212.62 | 19.02 | 337.42 | 0.004 | 4 | 0 | CAPTURED |
| tp8_pp2_dist_load | 128k_c2 | 131072 | 2 | 0.27 | 5110.74 | 38.49 | 16.97 | 0.016 | 1 | 0 | CAPTURED |
| tp8_pp2_dist_load | 128k_c4 | 131072 | 4 | 0.29 | 8231.69 | 85.97 | 18.73 | 0.031 | 3 | 0 | CAPTURED |
| tp8_pp2_dist_load | 128k_c8 | 131072 | 8 | 0.31 | 9754.23 | 258.04 | 19.64 | 0.062 | 7 | 0 | CAPTURED |
| tp8_pp2_dist_load | 1m_c2 | 1000000 | 2 | 0.02 | 70038.22 | 282.71 | 0.69 | 0.089 | 1 | 0 | CAPTURED |
| tp8_pp2_dist_load | 1m_c4 | 1000000 | 4 | 0.02 | 115716.92 | 417.21 | 0.69 | 0.090 | 3 | 0 | CAPTURED |
| tp4_pp4_dist_load | 8k_c8 | 8192 | 8 | 1.18 | 760.67 | 23.51 | 302.82 | 0.002 | 0 | 0 | CAPTURED |
| tp4_pp4_dist_load | 128k_c2 | 131072 | 2 | 0.51 | 2566.54 | 21.40 | 32.67 | 0.007 | 1 | 0 | CAPTURED |
| tp4_pp4_dist_load | 128k_c4 | 131072 | 4 | 0.58 | 4015.37 | 46.28 | 36.88 | 0.015 | 3 | 0 | CAPTURED |
| tp4_pp4_dist_load | 128k_c8 | 131072 | 8 | 0.62 | 6984.49 | 93.73 | 39.64 | 0.029 | 6 | 0 | CAPTURED |
| tp4_pp4_dist_load | 1m_c2 | 1000000 | 2 | 0.03 | 43347.15 | 453.33 | 1.11 | 0.055 | 1 | 0 | CAPTURED |
| tp4_pp4_dist_load | 1m_c4 | 1000000 | 4 | 0.04 | 71194.29 | 677.17 | 1.13 | 0.056 | 3 | 0 | CAPTURED |
| tp16_pp1_dist_load | 8k_c8 | 8192 | 8 | 1.17 | 1465.78 | 21.04 | 299.27 | 0.009 | 6 | 0 | CAPTURED |
| tp16_pp1_dist_load | 128k_c2 | 131072 | 2 | 0.15 | 9629.25 | 63.09 | 9.40 | 0.032 | 1 | 0 | CAPTURED |
| tp16_pp1_dist_load | 128k_c4 | 131072 | 4 | 0.15 | 12040.25 | 226.23 | 9.71 | 0.064 | 3 | 0 | CAPTURED |
| tp16_pp1_dist_load | 128k_c8 | 131072 | 8 | 0.16 | 26334.74 | 372.01 | 10.06 | 0.080 | 7 | 0 | CAPTURED |
| tp16_pp1_dist_load | 1m_c2 | 1000000 | 2 | 0.01 | 105294.58 | 217.31 | 0.46 | 0.152 | 1 | 0 | CAPTURED |
| tp16_pp1_dist_load | 1m_c4 | 1000000 | 4 | 0.01 | 170076.95 | 328.98 | 0.47 | 0.152 | 3 | 0 | CAPTURED |
