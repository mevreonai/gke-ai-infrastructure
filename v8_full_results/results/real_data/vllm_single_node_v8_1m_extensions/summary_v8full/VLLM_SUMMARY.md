# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_1m_concurrency_extension | 1m_c1 | 1000000 | 1 | 0.01 | 93394.90 | 10.23 | 0.34 | 0.123 | 0 | 0 | CAPTURED |
| tp4_1m_concurrency_extension | 1m_c2 | 1000000 | 2 | 0.01 | 139373.63 | 181.97 | 0.34 | 0.155 | 1 | 0 | CAPTURED |
| tp4_1m_concurrency_extension | 1m_c4 | 1000000 | 4 | 0.01 | 231267.51 | 267.41 | 0.35 | 0.155 | 3 | 0 | CAPTURED |
| tp8_1m_concurrency_extension | 1m_c1 | 1000000 | 1 | 0.01 | 74886.08 | 12.05 | 0.43 | 0.122 | 0 | 0 | CAPTURED |
| tp8_1m_concurrency_extension | 1m_c2 | 1000000 | 2 | 0.01 | 111744.26 | 177.21 | 0.43 | 0.153 | 1 | 0 | CAPTURED |
| tp8_1m_concurrency_extension | 1m_c4 | 1000000 | 4 | 0.01 | 184879.44 | 259.50 | 0.43 | 0.154 | 3 | 0 | CAPTURED |
| tp4_1m_maxseq4 | 1m_c4 | 1000000 | 4 | 0.01 | 232342.11 | 267.53 | 0.35 | 0.155 | 3 | 0 | CAPTURED |
| tp4_1m_maxseq8 | 1m_c4 | 1000000 | 4 | 0.01 | 232363.69 | 267.45 | 0.35 | 0.155 | 3 | 0 | CAPTURED |
| tp4_1m_maxseq16 | 1m_c4 | 1000000 | 4 | 0.01 | 232249.97 | 267.48 | 0.35 | 0.155 | 3 | 0 | CAPTURED |
| tp4_prefix1m | prefix1m | 1000000 | 1 | 0.02 | 48349.47 | 10.33 | 0.66 | 0.146 | 0 | 0 | CAPTURED |
