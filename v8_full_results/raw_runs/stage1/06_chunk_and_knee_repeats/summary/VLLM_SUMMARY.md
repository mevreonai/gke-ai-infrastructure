# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_128k_chunk_sensitivity | 128k_c1 | 131072 | 1 | 0.20 | 4607.86 | 5.65 | 12.89 | 0.017 | 0 | 0 | CAPTURED |
| tp4_128k_chunk_sensitivity | 128k_c4 | 131072 | 4 | 0.22 | 11536.87 | 111.27 | 13.78 | 0.066 | 3 | 0 | CAPTURED |
| tp4_knee_repeats | 8k_knee_rep1 | 8192 | 16 | 2.52 | 1229.88 | 20.01 | 645.26 | 0.020 | 12 | 0 | CAPTURED |
| tp4_knee_repeats | 8k_knee_rep2 | 8192 | 16 | 2.51 | 1229.87 | 20.12 | 642.43 | 0.020 | 12 | 0 | CAPTURED |
| tp4_knee_repeats | 8k_knee_rep3 | 8192 | 16 | 2.51 | 1228.06 | 20.10 | 643.13 | 0.020 | 14 | 0 | CAPTURED |
| tp4_knee_repeats | 128k_knee_rep1 | 131072 | 4 | 0.20 | 10770.48 | 69.86 | 25.99 | 0.065 | 3 | 0 | CAPTURED |
| tp4_knee_repeats | 128k_knee_rep2 | 131072 | 4 | 0.20 | 11027.19 | 68.02 | 25.96 | 0.065 | 3 | 0 | CAPTURED |
| tp4_knee_repeats | 128k_knee_rep3 | 131072 | 4 | 0.20 | 10852.90 | 69.23 | 25.99 | 0.065 | 3 | 0 | CAPTURED |
