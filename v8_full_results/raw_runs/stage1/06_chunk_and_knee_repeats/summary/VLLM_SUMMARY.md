# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_128k_chunk_sensitivity | 128k_c1 | 131072 | 1 | 0.20 | 4637.91 | 5.77 | 12.80 | 0.017 | 0 | 0 | CAPTURED |
| tp4_128k_chunk_sensitivity | 128k_c4 | 131072 | 4 | 0.22 | 11542.82 | 111.56 | 13.76 | 0.066 | 3 | 0 | CAPTURED |
| tp4_knee_repeats | 8k_knee_rep1 | 8192 | 16 | 2.50 | 1242.57 | 20.21 | 638.92 | 0.020 | 13 | 0 | CAPTURED |
| tp4_knee_repeats | 8k_knee_rep2 | 8192 | 16 | 2.50 | 1280.70 | 20.00 | 640.35 | 0.020 | 13 | 0 | CAPTURED |
| tp4_knee_repeats | 8k_knee_rep3 | 8192 | 16 | 2.50 | 1191.82 | 20.34 | 640.63 | 0.020 | 14 | 0 | CAPTURED |
| tp4_knee_repeats | 128k_knee_rep1 | 131072 | 4 | 0.20 | 10671.07 | 71.08 | 25.92 | 0.065 | 3 | 0 | CAPTURED |
| tp4_knee_repeats | 128k_knee_rep2 | 131072 | 4 | 0.20 | 10921.93 | 69.11 | 25.91 | 0.065 | 3 | 0 | CAPTURED |
| tp4_knee_repeats | 128k_knee_rep3 | 131072 | 4 | 0.20 | 10649.74 | 71.26 | 25.91 | 0.065 | 3 | 0 | CAPTURED |
