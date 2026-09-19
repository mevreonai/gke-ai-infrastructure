# V5 RTX PRO 6000 Serving Analysis (V6 Qualification Run)

> **Evidence Guardrail:** MEASURED-48B surrogate (`moonshotai/Kimi-Linear-48B-A3B-Instruct` at `e1df551a447157d4658b573f9a695d57658590e9`). No absolute K3 extrapolation.

## What this analysis answers
- TP4 vs TP8 matched runtime deltas
- Context scaling from 8K to 512K tokens
- Concurrency scaling (c=1 vs c=8)
- Memory and queueing behavior under warm serving

## TP4 vs TP8 Matched Comparison Points

| Input Tokens | Concurrency | TTFT Ratio (TP8 / TP4) | TPOT Ratio (TP8 / TP4) | Throughput Ratio (TP8 / TP4) | Architectural Reason |
|---:|---:|---:|---:|---:|:---|
| **8,192** | 1 | 1.215 | 1.429 | 0.717 | TP4 avoids cross-socket UPI traffic; 4 GPUs in single NUMA node faster for decode |
| **8,192** | 8 | 1.101 | 1.320 | 0.792 | TP4 retains throughput advantage under moderate concurrency |
| **131,072** | 1 | 1.070 | 1.378 | 0.902 | TP4 decode remains ~38% faster (5.10 ms vs 7.02 ms) |
| **524,288** | 1 | **0.888** | 1.254 | **1.119** | **Prefill flip point**: 8 GPUs deliver 11.2% faster prefill on 512K tokens due to raw compute |

## Closed-Loop Concurrency Frontier

| Configuration | Context | Concurrency | Req/s | Output tok/s | TTFT ms | TPOT ms | Waiting Peak | Peak KV Usage | Preemptions |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **TP4** | 8K | 1 | 0.73 | 187.34 | 223.33 | 4.48 | 0 | 0.1% | 0 |
| **TP4** | 8K | 8 | 2.18 | 558.84 | 951.85 | 10.62 | 5 | 1.0% | 0 |
| **TP4** | 128K | 1 | 0.19 | 24.71 | 4,533.15 | 5.10 | 0 | 1.6% | 0 |
| **TP4** | 512K | 1 | 0.03 | 1.97 | 31,954.16 | 7.60 | 0 | 6.5% | 0 |
| **TP8** | 8K | 1 | 0.52 | 134.38 | 271.26 | 6.41 | 0 | 0.1% | 0 |
| **TP8** | 8K | 8 | 1.73 | 442.55 | 1,047.63 | 14.01 | 6 | 0.9% | 0 |
| **TP8** | 128K | 1 | 0.17 | 22.29 | 4,850.44 | 7.02 | 0 | 1.6% | 0 |
| **TP8** | 512K | 1 | 0.03 | 2.21 | 28,387.09 | 9.53 | 0 | 6.4% | 0 |
