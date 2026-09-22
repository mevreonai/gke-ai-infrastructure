# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_openloop_8192 | rps_0.25x | 8192 | 64 | 1.03 | 305.07 | 8.97 | 262.80 | 0.016 | 1 | 0 | CAPTURED |
| tp4_openloop_8192 | rps_0.50x | 8192 | 64 | 2.04 | 348.53 | 16.58 | 521.14 | 0.029 | 1 | 0 | CAPTURED |
| tp4_openloop_8192 | rps_0.75x | 8192 | 64 | 2.96 | 599.02 | 40.52 | 756.86 | 0.081 | 3 | 0 | CAPTURED |
| tp4_openloop_8192 | rps_0.90x | 8192 | 64 | 3.30 | 935.90 | 60.86 | 845.21 | 0.081 | 8 | 0 | CAPTURED |
| tp4_openloop_8192 | rps_1.00x | 8192 | 64 | 3.36 | 979.06 | 62.41 | 859.80 | 0.081 | 10 | 0 | CAPTURED |
| tp4_openloop_8192 | rps_1.10x | 8192 | 64 | 3.35 | 783.52 | 63.13 | 856.76 | 0.081 | 9 | 0 | CAPTURED |
| tp4_openloop_8192 | rps_1.25x | 8192 | 64 | 3.42 | 825.71 | 64.01 | 875.99 | 0.081 | 5 | 0 | CAPTURED |
| tp4_openloop_131072 | rps_0.25x | 131072 | 32 | 0.06 | 5105.16 | 12.71 | 14.40 | 0.049 | 2 | 0 | CAPTURED |
| tp4_openloop_131072 | rps_0.50x | 131072 | 32 | 0.11 | 7510.66 | 36.74 | 27.23 | 0.115 | 4 | 0 | CAPTURED |
| tp4_openloop_131072 | rps_0.75x | 131072 | 32 | 0.16 | 6935.76 | 50.57 | 42.05 | 0.164 | 3 | 0 | CAPTURED |
| tp4_openloop_131072 | rps_0.90x | 131072 | 32 | 0.19 | 10008.60 | 131.55 | 49.06 | 0.277 | 3 | 0 | CAPTURED |
| tp4_openloop_131072 | rps_1.00x | 131072 | 32 | 0.18 | 21107.23 | 178.51 | 47.29 | 0.278 | 9 | 0 | CAPTURED |
| tp4_openloop_131072 | rps_1.10x | 131072 | 32 | 0.18 | 21470.52 | 166.73 | 46.76 | 0.278 | 7 | 0 | CAPTURED |
| tp4_openloop_131072 | rps_1.25x | 131072 | 32 | 0.18 | 21550.56 | 184.86 | 47.25 | 0.278 | 8 | 0 | CAPTURED |
| tp4_512k_interference_probe | 512k_main_plus_probe | 524288 | 16 | 0.02 | 44106.70 | 219.36 | 0.51 | 0.097 | 2 | 0 | CAPTURED |
