# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_qualification | 8k_c1 | 8192 | 1 | 0.73 | 223.33 | 4.48 | 187.34 | 0.001 | 0 | 0 | CAPTURED |
| tp4_qualification | 8k_c8 | 8192 | 8 | 2.18 | 951.85 | 10.62 | 558.84 | 0.010 | 5 | 0 | CAPTURED |
| tp4_qualification | 128k_c1 | 131072 | 1 | 0.19 | 4533.15 | 5.10 | 24.71 | 0.016 | 0 | 0 | CAPTURED |
| tp4_qualification | 512k_c1 | 524288 | 1 | 0.03 | 31954.16 | 7.60 | 1.97 | 0.065 | 0 | 0 | CAPTURED |
| tp8_qualification | 8k_c1 | 8192 | 1 | 0.52 | 271.26 | 6.41 | 134.38 | 0.001 | 0 | 0 | CAPTURED |
| tp8_qualification | 8k_c8 | 8192 | 8 | 1.73 | 1047.63 | 14.01 | 442.55 | 0.009 | 6 | 0 | CAPTURED |
| tp8_qualification | 128k_c1 | 131072 | 1 | 0.17 | 4850.44 | 7.02 | 22.29 | 0.016 | 0 | 0 | CAPTURED |
| tp8_qualification | 512k_c1 | 524288 | 1 | 0.03 | 28387.09 | 9.53 | 2.21 | 0.064 | 0 | 0 | CAPTURED |
