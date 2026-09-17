# Empirical 3-Pair AllReduce Benchmark Report
Tested on 2x GCP G4 nodes (16x NVIDIA RTX PRO 6000 Ada Blackwell Server Edition GPUs).

## Pair 1: (TP=16, PP=1) vs (TP=8, PP=2) vs (TP=4, PP=4)
| Payload Size | TP=16, PP=1 Time (µs) | TP=16 AlgBW | TP=8, PP=2 Time (µs) | TP=8 AlgBW | TP=4, PP=4 Time (µs) | TP=4 AlgBW | Optimal Config |
|---|---:|---:|---:|---:|---:|---:|:---:|
| **16 KiB (Decode Proxy)** | 425.74 µs | 0.04 GB/s | 37.52 µs | 0.44 GB/s | 17.93 µs | 0.91 GB/s | **TP=4** |
| **128 KiB** | 1618.96 µs | 0.08 GB/s | 39.10 µs | 3.35 GB/s | 21.21 µs | 6.18 GB/s | **TP=4** |
| **512 KiB** | 1611.87 µs | 0.33 GB/s | 60.15 µs | 8.72 GB/s | 47.47 µs | 11.05 GB/s | **TP=4** |
| **64 MiB** | 2269.29 µs | 29.57 GB/s | 2964.52 µs | 22.64 GB/s | 2598.53 µs | 25.83 GB/s | **TP=8** |
| **128 MiB (8K Prefill Proxy)** | 2521.72 µs | 53.22 GB/s | 5890.50 µs | 22.79 GB/s | 5163.10 µs | 26.00 GB/s | **TP=8** |
| **256 MiB** | 5044.42 µs | 53.21 GB/s | 11721.90 µs | 22.90 GB/s | 10210.80 µs | 26.29 GB/s | **TP=8** |

## Pair 2: TP=8 vs TP=2 (Cross-Socket vs Single-Switch)
| Payload Size | TP=8 Time (µs) | TP=8 AlgBW | TP=2 Time (µs) | TP=2 AlgBW | TP=2 Speedup |
|---|---:|---:|---:|---:|---:|
| **16 KiB (Decode Proxy)** | 37.52 µs | 0.44 GB/s | 11.75 µs | 1.39 GB/s | **3.19x** |
| **128 KiB** | 39.10 µs | 3.35 GB/s | 12.94 µs | 10.13 GB/s | **3.02x** |
| **512 KiB** | 60.15 µs | 8.72 GB/s | 33.37 µs | 15.71 GB/s | **1.80x** |
| **64 MiB** | 2964.52 µs | 22.64 GB/s | 1892.73 µs | 35.46 GB/s | **1.57x** |
| **128 MiB (8K Prefill Proxy)** | 5890.50 µs | 22.79 GB/s | 3728.91 µs | 35.99 GB/s | **1.58x** |
| **256 MiB** | 11721.90 µs | 22.90 GB/s | 7360.78 µs | 36.47 GB/s | **1.59x** |

## Pair 3: TP=16 vs TP=1 (Network Scaling vs Zero-Comm Baseline)
| Payload Size | TP=16 Time (µs) | TP=16 AlgBW | TP=1 Time (µs) | TP=1 Overhead | Trade-off Description |
|---|---:|---:|---:|---:|---|
| **16 KiB (Decode Proxy)** | 425.74 µs | 0.04 GB/s | **0.00 µs** | 0 B | TP=1 eliminates 425.74 µs collective sync per layer. |
| **128 KiB** | 1618.96 µs | 0.08 GB/s | **0.00 µs** | 0 B | TP=1 eliminates 1618.96 µs collective sync per layer. |
| **512 KiB** | 1611.87 µs | 0.33 GB/s | **0.00 µs** | 0 B | TP=1 eliminates 1611.87 µs collective sync per layer. |
| **64 MiB** | 2269.29 µs | 29.57 GB/s | **0.00 µs** | 0 B | TP=1 eliminates 2269.29 µs collective sync per layer. |
| **128 MiB (8K Prefill Proxy)** | 2521.72 µs | 53.22 GB/s | **0.00 µs** | 0 B | TP=1 eliminates 2521.72 µs collective sync per layer. |
| **256 MiB** | 5044.42 µs | 53.21 GB/s | **0.00 µs** | 0 B | TP=1 eliminates 5044.42 µs collective sync per layer. |
