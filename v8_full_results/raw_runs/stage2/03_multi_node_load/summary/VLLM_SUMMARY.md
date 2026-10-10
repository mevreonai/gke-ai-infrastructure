# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_pp2_dist_load | 8k_c1 | 8192 | 1 | 0.40 | 258.48 | 8.88 | 101.48 | 0.001 | 0 | 0 | CAPTURED |
| tp4_pp2_dist_load | 8k_c8 | 8192 | 8 | 1.30 | 812.12 | 20.91 | 332.86 | 0.005 | 5 | 0 | CAPTURED |
| tp4_pp2_dist_load | 128k_c2 | 131072 | 2 | 0.30 | 4144.96 | 38.97 | 19.36 | 0.016 | 1 | 0 | CAPTURED |
| tp4_pp2_dist_load | 128k_c4 | 131072 | 4 | 0.35 | 6390.78 | 79.29 | 22.41 | 0.031 | 3 | 0 | CAPTURED |
| tp4_pp2_dist_load | 128k_c8 | 131072 | 8 | 0.37 | 8653.96 | 206.14 | 23.57 | 0.063 | 7 | 0 | CAPTURED |
| tp4_pp2_dist_load | 1m_c2 | 1000000 | 2 | 0.02 | 80388.49 | 294.86 | 0.60 | 0.090 | 1 | 0 | CAPTURED |
| tp4_pp2_dist_load | 1m_c4 | 1000000 | 4 | 0.02 | 132959.20 | 424.00 | 0.60 | 0.090 | 3 | 0 | CAPTURED |
| tp8_pp2_dist_load | 8k_c1 | 8192 | 1 | 0.15 | 303.16 | 24.56 | 38.99 | 0.001 | 0 | 0 | CAPTURED |
| tp8_pp2_dist_load | 8k_c8 | 8192 | 8 | 0.90 | 958.95 | 30.98 | 230.88 | 0.004 | 4 | 0 | CAPTURED |
| tp8_pp2_dist_load | 128k_c2 | 131072 | 2 | 0.27 | 4600.98 | 42.92 | 17.49 | 0.016 | 1 | 0 | CAPTURED |
| tp8_pp2_dist_load | 128k_c4 | 131072 | 4 | 0.31 | 6900.94 | 91.64 | 20.14 | 0.031 | 3 | 0 | CAPTURED |
| tp8_pp2_dist_load | 128k_c8 | 131072 | 8 | 0.33 | 7185.63 | 265.40 | 21.28 | 0.062 | 7 | 0 | CAPTURED |
| tp8_pp2_dist_load | 1m_c2 | 1000000 | 2 | 0.02 | 63487.16 | 251.97 | 0.76 | 0.089 | 1 | 0 | CAPTURED |
| tp8_pp2_dist_load | 1m_c4 | 1000000 | 4 | 0.02 | 105295.56 | 375.62 | 0.76 | 0.090 | 3 | 0 | CAPTURED |
| tp4_pp4_dist_load | 8k_c1 | 8192 | 1 | 0.43 | 259.95 | 8.14 | 109.54 | 0.000 | 0 | 0 | CAPTURED |
| tp4_pp4_dist_load | 8k_c8 | 8192 | 8 | 0.85 | 709.38 | 34.01 | 218.07 | 0.002 | 0 | 0 | CAPTURED |
| tp4_pp4_dist_load | 128k_c2 | 131072 | 2 | 0.47 | 2597.95 | 26.90 | 29.79 | 0.007 | 1 | 0 | CAPTURED |
| tp4_pp4_dist_load | 128k_c4 | 131072 | 4 | 0.54 | 4065.91 | 53.54 | 34.35 | 0.015 | 3 | 0 | CAPTURED |
| tp4_pp4_dist_load | 128k_c8 | 131072 | 8 | 0.61 | 6661.87 | 101.20 | 39.14 | 0.029 | 6 | 0 | CAPTURED |
| tp4_pp4_dist_load | 1m_c2 | 1000000 | 2 | 0.03 | 43799.36 | 460.98 | 1.10 | 0.055 | 1 | 0 | CAPTURED |
| tp4_pp4_dist_load | 1m_c4 | 1000000 | 4 | 0.03 | 71678.76 | 687.56 | 1.12 | 0.056 | 3 | 0 | CAPTURED |
| tp16_pp1_dist_load | 8k_c1 | 8192 | 1 | 0.14 | 887.73 | 24.21 | 36.25 | 0.001 | 0 | 0 | CAPTURED |
| tp16_pp1_dist_load | 8k_c8 | 8192 | 8 | 0.36 | 4950.98 | 68.56 | 91.17 | 0.009 | 6 | 0 | CAPTURED |
| tp16_pp1_dist_load | 128k_c2 | 131072 | 2 | 0.05 | 27295.56 | 261.01 | 2.92 | 0.032 | 1 | 0 | CAPTURED |
| tp16_pp1_dist_load | 128k_c4 | 131072 | 4 | 0.04 | 39592.40 | 846.37 | 2.75 | 0.064 | 3 | 0 | CAPTURED |
| tp16_pp1_dist_load | 128k_c8 | 131072 | 8 | 0.02 | 167323.58 | 2378.48 | 1.59 | 0.080 | 7 | 0 | CAPTURED |
| tp16_pp1_dist_load | 1m_c2 | 1000000 | 2 | 0.00 | 345814.54 | 474.54 | 0.16 | 0.153 | 1 | 0 | CAPTURED |
| tp16_pp1_dist_load | 1m_c4 | 1000000 | 4 | 0.00 | 443871.39 | 1433.95 | 0.15 | 0.153 | 3 | 0 | CAPTURED |
