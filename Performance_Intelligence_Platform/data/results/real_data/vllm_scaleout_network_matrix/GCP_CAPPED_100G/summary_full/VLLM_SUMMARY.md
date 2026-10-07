# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_pp2_dist | 128k_c1 | 131072 | 1 | 0.33 | 2664.67 | 5.53 | 21.24 | 0.008 | 0 | 0 | CAPTURED |
| tp4_pp2_dist | 512k_c1 | 524288 | 1 | 0.05 | 17982.06 | 7.90 | 1.76 | 0.031 | 0 | 0 | CAPTURED |
| tp4_pp2_dist | 1m_c1 | 1000000 | 1 | 0.02 | 52596.88 | 10.57 | 0.60 | 0.059 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 128k_c1 | 131072 | 1 | 0.30 | 2825.80 | 7.58 | 19.37 | 0.008 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 512k_c1 | 524288 | 1 | 0.06 | 15548.37 | 9.93 | 2.02 | 0.031 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 1m_c1 | 1000000 | 1 | 0.02 | 41462.07 | 12.51 | 0.76 | 0.059 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 128k_c1 | 131072 | 1 | 0.47 | 1760.71 | 5.67 | 30.22 | 0.004 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 512k_c1 | 524288 | 1 | 0.09 | 10389.33 | 8.09 | 3.01 | 0.014 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 1m_c1 | 1000000 | 1 | 0.03 | 28865.66 | 10.68 | 1.10 | 0.027 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 128k_c1 | 131072 | 1 | 0.09 | 9735.83 | 15.62 | 5.97 | 0.016 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 512k_c1 | 524288 | 1 | 0.02 | 43094.92 | 17.86 | 0.73 | 0.064 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 1m_c1 | 1000000 | 1 | 0.01 | 92991.99 | 20.58 | 0.34 | 0.121 | 0 | 0 | CAPTURED |
