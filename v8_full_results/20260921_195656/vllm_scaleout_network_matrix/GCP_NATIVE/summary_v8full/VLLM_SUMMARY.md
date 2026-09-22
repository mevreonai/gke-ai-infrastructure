# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_pp2_dist | 128k_c1 | 131072 | 1 | 0.33 | 2647.23 | 5.51 | 21.37 | 0.008 | 0 | 0 | CAPTURED |
| tp4_pp2_dist | 512k_c1 | 524288 | 1 | 0.05 | 17945.46 | 7.86 | 1.76 | 0.031 | 0 | 0 | CAPTURED |
| tp4_pp2_dist | 1m_c1 | 1000000 | 1 | 0.02 | 52526.42 | 10.54 | 0.61 | 0.059 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 128k_c1 | 131072 | 1 | 0.31 | 2787.75 | 7.54 | 19.61 | 0.008 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 512k_c1 | 524288 | 1 | 0.06 | 15575.73 | 9.88 | 2.01 | 0.031 | 0 | 0 | CAPTURED |
| tp8_pp2_dist | 1m_c1 | 1000000 | 1 | 0.02 | 41514.88 | 12.47 | 0.76 | 0.059 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 128k_c1 | 131072 | 1 | 0.48 | 1709.97 | 5.63 | 30.99 | 0.004 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 512k_c1 | 524288 | 1 | 0.10 | 10221.76 | 8.03 | 3.06 | 0.014 | 0 | 0 | CAPTURED |
| tp4_pp4_dist | 1m_c1 | 1000000 | 1 | 0.03 | 28567.95 | 10.64 | 1.11 | 0.027 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 128k_c1 | 131072 | 1 | 0.14 | 6420.44 | 14.94 | 8.69 | 0.016 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 512k_c1 | 524288 | 1 | 0.03 | 29624.08 | 17.41 | 1.06 | 0.064 | 0 | 0 | CAPTURED |
| tp16_pp1_dist | 1m_c1 | 1000000 | 1 | 0.01 | 68196.79 | 20.08 | 0.46 | 0.121 | 0 | 0 | CAPTURED |
