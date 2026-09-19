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
| 8192 | 1 | 1.215 | 1.429 | 0.717 |
| 8192 | 8 | 1.101 | 1.320 | 0.792 |
| 131072 | 1 | 1.070 | 1.378 | 0.902 |
| 524288 | 1 | 0.888 | 1.254 | 1.119 |

## Closed-loop concurrency frontier

This is a backlog/saturation test, not a production user-arrival model. Generate open-loop cases with `13_generate_load_cases.py` before claiming a capacity knee.
