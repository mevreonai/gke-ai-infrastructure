# V5 RTX PRO 6000 serving analysis

> MEASURED-48B surrogate. No absolute K3 extrapolation.

## What this analysis can answer
- TP4 vs TP8 matched runtime deltas
- chunk-size tradeoffs
- closed-loop batching frontier
- open-loop queueing/capacity behavior when generated-load tests are run
- prefix cold-vs-repeat behavior

## TP4 vs TP8 matched points

| Input | C | TTFT TP8/TP4 | TPOT TP8/TP4 | Throughput TP8/TP4 |
|---:|---:|---:|---:|---:|
| 8192 | 1 | 1.193 | 1.427 | 0.720 |
| 8192 | 8 | 1.083 | 1.302 | 0.803 |
| 131072 | 1 | 1.063 | 1.384 | 0.907 |
| 524288 | 1 | 0.883 | 1.250 | 1.126 |
| 8192 | 1 | 1.204 | 1.420 | 0.736 |
| 131072 | 1 | 1.062 | 1.383 | 0.907 |
| 524288 | 1 | 0.881 | 1.248 | 1.128 |
| 1000000 | 1 | 0.802 | 1.179 | 1.246 |

## Closed-loop concurrency frontier

This is a backlog/saturation test, not a production user-arrival model. Generate open-loop cases with `13_generate_load_cases.py` before claiming a capacity knee.

### Context 8192
| C | Req/s | Out tok/s | TTFT ms | TPOT ms | Wait peak | KV peak | Preempt |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.733 | 187.599 | 224.911 | 4.469 | 0.000 | 0.001 | 0.000 |
| 4 | 1.622 | 415.283 | 610.831 | 7.268 | 2.000 | 0.005 | 0.000 |
| 8 | 2.186 | 559.731 | 916.484 | 10.732 | 5.000 | 0.010 | 0.000 |
| 16 | 2.630 | 673.242 | 1155.821 | 19.268 | 13.000 | 0.020 | 0.000 |
| 32 | 3.025 | 774.404 | 1623.746 | 34.965 | 27.000 | 0.040 | 0.000 |

### Context 131072
| C | Req/s | Out tok/s | TTFT ms | TPOT ms | Wait peak | KV peak | Preempt |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.193 | 24.670 | 4538.780 | 5.114 | 0.000 | 0.016 | 0.000 |
| 4 | 0.212 | 27.200 | 10596.028 | 64.369 | 3.000 | 0.065 | 0.000 |
| 8 | 0.218 | 27.957 | 12722.521 | 186.978 | 7.000 | 0.131 | 0.000 |
| 16 | 0.221 | 28.236 | 37256.562 | 242.850 | 15.000 | 0.146 | 0.000 |

### Context 524288
| C | Req/s | Out tok/s | TTFT ms | TPOT ms | Wait peak | KV peak | Preempt |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.031 | 1.969 | 32028.529 | 7.559 | 0.000 | 0.065 | 0.000 |
| 2 | 0.031 | 2.006 | 40299.165 | 367.402 | 1.000 | 0.128 | 0.000 |
| 4 | 0.031 | 2.012 | 87703.848 | 433.953 | 3.000 | 0.129 | 0.000 |

### Context 1000000
| C | Req/s | Out tok/s | TTFT ms | TPOT ms | Wait peak | KV peak | Preempt |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.011 | 0.341 | 93460.375 | 10.201 | 0.000 | 0.123 | 0.000 |
| 2 | 0.011 | 0.346 | 150654.326 | 239.252 | 1.000 | 0.155 | 0.000 |
| 4 | 0.011 | 0.346 | 231503.504 | 267.686 | 3.000 | 0.155 | 0.000 |
