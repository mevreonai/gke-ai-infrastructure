# V5 Kimi-Linear vLLM surrogate summary

> **Guardrail:** measured 48B surrogate data; absolute speed is not a K3 prediction.

| Case | Bench | Input | C | TTFT mean ms | TTFT P95 | TPOT mean ms | KV peak | Preempt Δ | Offload bytes Δ | GPU util mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tp4_cold_chunk8k | 8k_c1 | 8192 | 1 | 237.35 | 238.17 | 5.01 | 0.001 | 0 |  | 19.8 |
| tp8_cold_chunk8k | 8k_c1 | 8192 | 1 | 278.45 | 280.66 | 6.88 | 0.001 | 0 |  | 45.4 |
| tp4_chunk4k | 128k_c1 | 131072 | 1 | 5451.64 | 5604.11 | 5.70 | 0.019 | 0 |  | 32.6 |
| tp4_chunk16k | 128k_c1 | 131072 | 1 | 4654.34 | 4799.19 | 5.71 | 0.020 | 0 |  | 31.0 |
| tp4_prefix_chunk8k | prefix128k_seq | 131328 | 1 | 1278.92 | 4142.30 | 5.87 | 0.023 | 0 |  | 15.5 |
| tp4_concurrency_saturation | 8k_c1 | 8192 | 1 | 272.51 | 378.67 | 5.01 | 0.001 | 0 |  | 17.1 |
| tp4_pp2_dist | 128k_c1 | 131072 | 1 | 2832.61 | 3039.62 | 5.85 | 0.009 | 0 |  | 36.5 |
