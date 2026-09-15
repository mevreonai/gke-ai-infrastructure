# RTX PRO 6000 smoke-test model analysis

This report converts the synthetic measurements into inputs for the separate **3-node Kimi K3 TP8/PP3 vs TP4/PP6 model**. It does not claim end-to-end Kimi performance.

## 1. TP4 vs TP8
- 16 KiB collective time: TP4 **20.170 us**, TP8 **38.240 us**; TP8/TP4 latency ratio = **1.90×**.
- 128M algbw: TP4 **25.99 GB/s**, TP8 **22.78 GB/s**; TP4/TP8 = **1.14×**.
- 256M algbw: TP4 **26.17 GB/s**, TP8 **22.97 GB/s**; TP4/TP8 = **1.14×**.
- **Decision gate:** TP4 large-message advantage = **14.1%**. TP topology matters, but model-level A/B is still required.

## 2. Network sweep
| Provenance | iperf Gb/s | SendRecv 16K us | 128M us | 256M us | 128M effective GB/s |
|---|---:|---:|---:|---:|---:|
| GCP_NATIVE | 173.58 | -1.000 | -1.000 | -1.000 |  |
| GCP_CAPPED_100G | 58.75 | -1.000 | -1.000 | -1.000 |  |
| GCP_CAPPED_50G | 33.77 | -1.000 | -1.000 | -1.000 |  |
| GCP_CAPPED_20G | 16.80 | -1.000 | -1.000 | -1.000 |  |
| GCP_CAPPED_10G | 9.02 | -1.000 | -1.000 | -1.000 |  |

### Large-message alpha–beta fits
| Provenance | alpha (ms) | fitted payload BW (GB/s) |
|---|---:|---:|

> The capped curves primarily characterize the **bandwidth/serialization term**. They do not reproduce the local lab NIC's physical latency, NUMA placement, queueing, offloads, switch behavior, or firmware.

## 3. PP-network proxy for the 3-node system
An 8K-token BF16 hidden-state proxy is **112.0 MiB**. The smoke suite measures nearby 128 MiB transfers and also fits the 64/128/256 MiB curve.

These are intentionally conservative *serialization proxies*. Real vLLM can overlap some PP communication with compute/pipeline execution.

## 4. TP communication sensitivity for K3
For the 93-layer model, if the runtime executes an effective **K** full-hidden-state collective equivalents per layer, a simple 8K-chunk proxy is:

`T_TP_chunk ≈ 93 × K × measured_AllReduce_time(128MiB)`

| TP | K=1 | K=1.5 | K=2 |
|---|---:|---:|---:|
| TP4 | 0.480 s | 0.721 s | 0.961 s |
| TP8 | 0.548 s | 0.822 s | 1.096 s |

> K is deliberately a sensitivity parameter; only a real vLLM/K3 trace can establish the exact collective count/fusion behavior.

## 5. Decode collective-latency proxy
Using the 16 KiB NCCL point as a batch-1-sized proxy:
- TP4: ~**1.88/2.81/3.75 ms/token** for K=1/1.5/2, before overlap/fusion.
- TP8: ~**3.56/5.33/7.11 ms/token** for K=1/1.5/2, before overlap/fusion.

## 7. What remains unresolved without Kimi/vLLM
- MXFP4 Kimi kernel efficiency
- actual KDA/MLA execution time
- exact collective count/fusion per K3 layer
- vLLM pipeline overlap and bubbles
- SimpleCPUOffloadConnector / LMCache lookup, eviction and restore behavior
- KV/cache residency at 512K and 1M
- scheduler/preemption effects

Therefore this report should be used to **prioritize** TP8/PP3 vs TP4/PP6 and network/offload experiments, not to claim final tokens/s.
