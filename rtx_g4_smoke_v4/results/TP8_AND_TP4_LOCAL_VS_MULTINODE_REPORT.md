# Distributed Network Sweeps: TP-8 & TP-4 Local vs. Multi-Node

**Hardware Platform:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)
**Cluster:** `kimi-node-0` (10.128.0.39) & `kimi-node-1` (10.128.0.40) on GCP VPC (us-central1-b)
**Configurations Covered:**
- **TP-8 Local (Single-Node Dual-Socket PCIe Gen5)** vs. **TP-8 Multi-Node (4 ranks/node across 2 nodes)**
- **TP-4 Local (Single-Node Single-NUMA Socket-Local)** vs. **TP-4 Multi-Node (2 ranks/node across 2 nodes)**
- **Network Rates:** 175G Native (173.6 Gbps), 100G, 50G, 20G, 10G Egress Caps

## 1. Executive Summary: 256 MiB Large Prefill Across All Topologies & Rates

| Topology | Collective | Local Baseline | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TP=8** | AllReduce | **18.006 ms** | **52.552 ms** | 39.523 ms | 79.439 ms | 196.873 ms | **393.861 ms** | **2.92x** | **21.87x** |
| **TP=8** | AllGather | **9.85 ms** | **28.532 ms** | 30.794 ms | 40.394 ms | 98.364 ms | **196.738 ms** | **2.90x** | **19.97x** |
| **TP=8** | ReduceScatter | **9.934 ms** | **28.447 ms** | 29.457 ms | 40.581 ms | 98.488 ms | **196.736 ms** | **2.86x** | **19.80x** |
| **TP=4** | AllReduce | **15.382 ms** | **41.384 ms** | 41.775 ms | 67.601 ms | 168.829 ms | **337.761 ms** | **2.69x** | **21.96x** |
| **TP=4** | AllGather | **8.44 ms** | **23.725 ms** | 25.603 ms | 35.225 ms | 84.451 ms | **168.966 ms** | **2.81x** | **20.02x** |
| **TP=4** | ReduceScatter | **8.48 ms** | **23.818 ms** | 25.877 ms | 35.172 ms | 84.464 ms | **169.582 ms** | **2.81x** | **20.00x** |

---

## 2. Detailed Breakdown: TP=8 Multi-Node vs. TP=8 Local (Node-Local Dual-Socket PCIe Gen5)

### AllReduce (TP=8)

| Payload Size | Milestone Description | TP=8 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16 KiB** | Batch-1 Token Decode | **0.028 ms** | **0.204 ms** | 0.208 ms | 0.21 ms | 0.207 ms | **0.202 ms** | 7.27x | 7.20x |
| **32 KiB** | 32 KiB | **0.03 ms** | **0.21 ms** | 0.211 ms | 0.214 ms | 0.21 ms | **0.216 ms** | 6.99x | 7.19x |
| **64 KiB** | 64 KiB | **0.035 ms** | **0.248 ms** | 0.294 ms | 0.25 ms | 0.259 ms | **0.255 ms** | 7.04x | 7.26x |
| **128 KiB** | Small Activation | **0.05 ms** | **0.241 ms** | 0.286 ms | 0.256 ms | 0.255 ms | **0.398 ms** | 4.81x | 7.95x |
| **256 KiB** | 256 KiB | **0.087 ms** | **0.272 ms** | 0.299 ms | 0.295 ms | 0.385 ms | **0.771 ms** | 3.12x | 8.83x |
| **512 KiB** | 512 KiB | **0.162 ms** | **0.477 ms** | 0.466 ms | 0.751 ms | 0.786 ms | **1.54 ms** | 2.94x | 9.50x |
| **1 MiB** | 1 MiB Tensor | **0.138 ms** | **0.432 ms** | 0.469 ms | 0.558 ms | 0.789 ms | **1.542 ms** | 3.12x | 11.13x |
| **2 MiB** | 2 MiB | **0.231 ms** | **0.582 ms** | 0.628 ms | 0.735 ms | 1.551 ms | **3.076 ms** | 2.52x | 13.31x |
| **4 MiB** | 4 MiB | **0.355 ms** | **0.935 ms** | 1.007 ms | 1.389 ms | 3.075 ms | **6.152 ms** | 2.64x | 17.35x |
| **8 MiB** | 8 MiB | **0.656 ms** | **1.715 ms** | 1.431 ms | 2.473 ms | 6.147 ms | **12.3 ms** | 2.61x | 18.75x |
| **16 MiB** | 16 MiB Activation | **1.217 ms** | **3.306 ms** | 2.577 ms | 4.919 ms | 12.316 ms | **24.581 ms** | 2.72x | 20.20x |
| **32 MiB** | 32 MiB | **2.378 ms** | **6.711 ms** | 4.967 ms | 9.837 ms | 24.575 ms | **49.191 ms** | 2.82x | 20.68x |
| **64 MiB** | 64 MiB Chunk | **4.64 ms** | **13.169 ms** | 9.866 ms | 19.672 ms | 49.2 ms | **98.433 ms** | 2.84x | 21.21x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **9.021 ms** | **26.222 ms** | 19.719 ms | 39.378 ms | 98.43 ms | **196.921 ms** | 2.91x | 21.83x |
| **256 MiB** | Large Prefill (256 MiB) | **18.006 ms** | **52.552 ms** | 39.523 ms | 79.439 ms | 196.873 ms | **393.861 ms** | 2.92x | 21.87x |

### AllGather (TP=8)

| Payload Size | Milestone Description | TP=8 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8 KiB** | Min Size Floor | **0.018 ms** | **0.176 ms** | 0.193 ms | 0.163 ms | 0.144 ms | **0.235 ms** | 9.81x | 13.08x |
| **16 KiB** | Batch-1 Token Decode | **0.017 ms** | **0.166 ms** | 0.149 ms | 0.121 ms | 0.124 ms | **0.279 ms** | 9.75x | 16.37x |
| **32 KiB** | 32 KiB | **0.019 ms** | **0.149 ms** | 0.12 ms | 0.128 ms | 0.136 ms | **0.156 ms** | 7.65x | 8.04x |
| **64 KiB** | 64 KiB | **0.02 ms** | **1.522 ms** | 0.319 ms | 0.255 ms | 0.197 ms | **0.29 ms** | 75.48x | 14.38x |
| **128 KiB** | Small Activation | **0.029 ms** | **0.251 ms** | 0.298 ms | 0.266 ms | 0.217 ms | **1.004 ms** | 8.58x | 34.25x |
| **256 KiB** | 256 KiB | **0.047 ms** | **0.275 ms** | 0.34 ms | 0.272 ms | 0.27 ms | **0.408 ms** | 5.79x | 8.59x |
| **512 KiB** | 512 KiB | **0.084 ms** | **0.3 ms** | 0.394 ms | 0.43 ms | 0.267 ms | **0.415 ms** | 3.59x | 4.95x |
| **1 MiB** | 1 MiB Tensor | **0.076 ms** | **0.436 ms** | 0.531 ms | 0.524 ms | 0.474 ms | **0.784 ms** | 5.71x | 10.28x |
| **2 MiB** | 2 MiB | **0.118 ms** | **0.621 ms** | 0.757 ms | 0.8 ms | 0.787 ms | **1.566 ms** | 5.27x | 13.31x |
| **4 MiB** | 4 MiB | **0.182 ms** | **1.035 ms** | 1.175 ms | 1.152 ms | 1.54 ms | **3.09 ms** | 5.70x | 17.02x |
| **8 MiB** | 8 MiB | **0.334 ms** | **3.269 ms** | 1.962 ms | 1.85 ms | 3.071 ms | **6.131 ms** | 9.80x | 18.38x |
| **16 MiB** | 16 MiB Activation | **0.634 ms** | **3.721 ms** | 4.031 ms | 3.393 ms | 6.137 ms | **12.374 ms** | 5.87x | 19.53x |
| **32 MiB** | 32 MiB | **1.238 ms** | **5.478 ms** | 4.404 ms | 7.353 ms | 12.294 ms | **24.562 ms** | 4.43x | 19.84x |
| **64 MiB** | 64 MiB Chunk | **2.464 ms** | **8.489 ms** | 10.716 ms | 13.994 ms | 24.562 ms | **49.122 ms** | 3.44x | 19.93x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.928 ms** | **14.373 ms** | 16.076 ms | 19.929 ms | 49.178 ms | **98.32 ms** | 2.92x | 19.95x |
| **256 MiB** | Large Prefill (256 MiB) | **9.85 ms** | **28.532 ms** | 30.794 ms | 40.394 ms | 98.364 ms | **196.738 ms** | 2.90x | 19.97x |

### ReduceScatter (TP=8)

| Payload Size | Milestone Description | TP=8 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8 KiB** | Min Size Floor | **0.02 ms** | **0.19 ms** | 0.774 ms | 0.133 ms | 0.134 ms | **0.132 ms** | 9.56x | 6.63x |
| **16 KiB** | Batch-1 Token Decode | **0.018 ms** | **0.191 ms** | 0.123 ms | 0.126 ms | 0.135 ms | **0.192 ms** | 10.54x | 10.56x |
| **32 KiB** | 32 KiB | **0.019 ms** | **0.118 ms** | 0.127 ms | 0.131 ms | 0.131 ms | **0.223 ms** | 6.20x | 11.67x |
| **64 KiB** | 64 KiB | **0.02 ms** | **0.198 ms** | 0.198 ms | 0.197 ms | 0.211 ms | **0.321 ms** | 10.05x | 16.27x |
| **128 KiB** | Small Activation | **0.03 ms** | **0.224 ms** | 0.211 ms | 0.215 ms | 0.234 ms | **0.421 ms** | 7.51x | 14.12x |
| **256 KiB** | 256 KiB | **0.051 ms** | **0.305 ms** | 0.228 ms | 0.235 ms | 0.275 ms | **0.539 ms** | 6.02x | 10.65x |
| **512 KiB** | 512 KiB | **0.091 ms** | **0.279 ms** | 0.263 ms | 0.243 ms | 0.275 ms | **0.456 ms** | 3.07x | 5.01x |
| **1 MiB** | 1 MiB Tensor | **0.076 ms** | **0.421 ms** | 0.412 ms | 0.42 ms | 0.441 ms | **0.931 ms** | 5.54x | 12.26x |
| **2 MiB** | 2 MiB | **0.125 ms** | **0.639 ms** | 0.651 ms | 0.79 ms | 0.791 ms | **1.57 ms** | 5.11x | 12.56x |
| **4 MiB** | 4 MiB | **0.187 ms** | **1.028 ms** | 1.048 ms | 1.229 ms | 1.61 ms | **3.117 ms** | 5.50x | 16.67x |
| **8 MiB** | 8 MiB | **0.349 ms** | **1.678 ms** | 1.785 ms | 1.931 ms | 3.095 ms | **6.499 ms** | 4.80x | 18.60x |
| **16 MiB** | 16 MiB Activation | **0.641 ms** | **2.534 ms** | 3.302 ms | 3.808 ms | 6.193 ms | **12.282 ms** | 3.95x | 19.16x |
| **32 MiB** | 32 MiB | **1.247 ms** | **4.77 ms** | 4.771 ms | 11.3 ms | 12.281 ms | **24.614 ms** | 3.83x | 19.74x |
| **64 MiB** | 64 MiB Chunk | **2.484 ms** | **8.079 ms** | 9.574 ms | 13.07 ms | 24.64 ms | **49.124 ms** | 3.25x | 19.78x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.967 ms** | **15.575 ms** | 16.912 ms | 19.896 ms | 49.25 ms | **98.358 ms** | 3.14x | 19.80x |
| **256 MiB** | Large Prefill (256 MiB) | **9.934 ms** | **28.447 ms** | 29.457 ms | 40.581 ms | 98.488 ms | **196.736 ms** | 2.86x | 19.80x |

## 2. Detailed Breakdown: TP=4 Multi-Node vs. TP=4 Local (Socket-Local Single-NUMA PCIe Gen5)

### AllReduce (TP=4)

| Payload Size | Milestone Description | TP=4 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16 KiB** | Batch-1 Token Decode | **0.016 ms** | **0.167 ms** | 0.155 ms | 0.162 ms | 0.161 ms | **0.166 ms** | 10.31x | 10.24x |
| **32 KiB** | 32 KiB | **0.017 ms** | **0.173 ms** | 0.173 ms | 0.175 ms | 0.207 ms | **0.175 ms** | 10.32x | 10.45x |
| **64 KiB** | 64 KiB | **0.018 ms** | **0.184 ms** | 0.178 ms | 0.187 ms | 0.201 ms | **0.178 ms** | 10.20x | 9.88x |
| **128 KiB** | Small Activation | **0.027 ms** | **0.192 ms** | 0.189 ms | 0.224 ms | 0.227 ms | **0.331 ms** | 7.23x | 12.42x |
| **256 KiB** | 256 KiB | **0.044 ms** | **0.34 ms** | 0.308 ms | 0.329 ms | 0.382 ms | **0.661 ms** | 7.72x | 15.02x |
| **512 KiB** | 512 KiB | **0.079 ms** | **0.318 ms** | 0.296 ms | 0.264 ms | 0.396 ms | **0.662 ms** | 4.03x | 8.39x |
| **1 MiB** | 1 MiB Tensor | **0.092 ms** | **0.473 ms** | 0.461 ms | 0.414 ms | 0.75 ms | **1.319 ms** | 5.13x | 14.33x |
| **2 MiB** | 2 MiB | **0.153 ms** | **0.551 ms** | 0.552 ms | 0.539 ms | 1.337 ms | **2.636 ms** | 3.60x | 17.20x |
| **4 MiB** | 4 MiB | **0.255 ms** | **0.806 ms** | 0.825 ms | 1.064 ms | 2.636 ms | **5.277 ms** | 3.16x | 20.72x |
| **8 MiB** | 8 MiB | **0.522 ms** | **1.353 ms** | 1.419 ms | 2.155 ms | 5.273 ms | **10.543 ms** | 2.59x | 20.19x |
| **16 MiB** | 16 MiB Activation | **1.006 ms** | **2.511 ms** | 2.665 ms | 4.227 ms | 10.544 ms | **21.082 ms** | 2.50x | 20.95x |
| **32 MiB** | 32 MiB | **2.008 ms** | **5.251 ms** | 5.024 ms | 8.448 ms | 21.094 ms | **42.207 ms** | 2.61x | 21.02x |
| **64 MiB** | 64 MiB Chunk | **3.989 ms** | **10.277 ms** | 10.03 ms | 16.899 ms | 42.342 ms | **84.395 ms** | 2.58x | 21.16x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **7.916 ms** | **20.525 ms** | 20.532 ms | 33.783 ms | 84.4 ms | **168.843 ms** | 2.59x | 21.33x |
| **256 MiB** | Large Prefill (256 MiB) | **15.382 ms** | **41.384 ms** | 41.775 ms | 67.601 ms | 168.829 ms | **337.761 ms** | 2.69x | 21.96x |

### AllGather (TP=4)

| Payload Size | Milestone Description | TP=4 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8 KiB** | Min Size Floor | **0.012 ms** | **0.092 ms** | 0.115 ms | 0.096 ms | 0.117 ms | **0.519 ms** | 7.65x | 43.11x |
| **16 KiB** | Batch-1 Token Decode | **0.012 ms** | **0.09 ms** | 0.096 ms | 0.104 ms | 0.098 ms | **0.091 ms** | 7.69x | 7.74x |
| **32 KiB** | 32 KiB | **0.012 ms** | **0.124 ms** | 0.191 ms | 0.157 ms | 0.15 ms | **2.422 ms** | 10.03x | 195.35x |
| **64 KiB** | 64 KiB | **0.013 ms** | **0.142 ms** | 0.195 ms | 0.145 ms | 0.159 ms | **0.14 ms** | 11.00x | 10.81x |
| **128 KiB** | Small Activation | **0.017 ms** | **0.164 ms** | 2.472 ms | 0.186 ms | 0.17 ms | **0.16 ms** | 9.52x | 9.31x |
| **256 KiB** | 256 KiB | **0.026 ms** | **0.261 ms** | 0.344 ms | 0.331 ms | 0.297 ms | **0.337 ms** | 9.85x | 12.75x |
| **512 KiB** | 512 KiB | **0.043 ms** | **0.269 ms** | 0.329 ms | 0.32 ms | 0.293 ms | **0.324 ms** | 6.21x | 7.48x |
| **1 MiB** | 1 MiB Tensor | **0.054 ms** | **0.432 ms** | 0.416 ms | 0.519 ms | 0.461 ms | **0.668 ms** | 8.03x | 12.43x |
| **2 MiB** | 2 MiB | **0.082 ms** | **0.62 ms** | 0.635 ms | 0.607 ms | 0.768 ms | **1.448 ms** | 7.57x | 17.67x |
| **4 MiB** | 4 MiB | **0.139 ms** | **0.918 ms** | 1.066 ms | 1.057 ms | 1.586 ms | **2.747 ms** | 6.63x | 19.83x |
| **8 MiB** | 8 MiB | **0.278 ms** | **1.388 ms** | 1.349 ms | 1.346 ms | 3.05 ms | **5.392 ms** | 5.00x | 19.41x |
| **16 MiB** | 16 MiB Activation | **0.542 ms** | **2.422 ms** | 2.159 ms | 2.198 ms | 5.835 ms | **10.863 ms** | 4.47x | 20.06x |
| **32 MiB** | 32 MiB | **1.066 ms** | **4.887 ms** | 3.573 ms | 6.796 ms | 10.748 ms | **21.144 ms** | 4.59x | 19.84x |
| **64 MiB** | 64 MiB Chunk | **2.12 ms** | **8.232 ms** | 7.265 ms | 8.767 ms | 21.258 ms | **42.246 ms** | 3.88x | 19.93x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.232 ms** | **12.112 ms** | 14.26 ms | 17.894 ms | 42.351 ms | **84.456 ms** | 2.86x | 19.96x |
| **256 MiB** | Large Prefill (256 MiB) | **8.44 ms** | **23.725 ms** | 25.603 ms | 35.225 ms | 84.451 ms | **168.966 ms** | 2.81x | 20.02x |

### ReduceScatter (TP=4)

| Payload Size | Milestone Description | TP=4 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8 KiB** | Min Size Floor | **0.012 ms** | **0.102 ms** | 0.1 ms | 0.094 ms | 0.124 ms | **0.112 ms** | 8.28x | 9.08x |
| **16 KiB** | Batch-1 Token Decode | **0.011 ms** | **0.17 ms** | 0.1 ms | 0.091 ms | 0.124 ms | **0.101 ms** | 15.13x | 8.97x |
| **32 KiB** | 32 KiB | **0.012 ms** | **0.204 ms** | 0.124 ms | 0.125 ms | 0.207 ms | **0.154 ms** | 16.88x | 12.76x |
| **64 KiB** | 64 KiB | **0.013 ms** | **0.135 ms** | 2.442 ms | 0.146 ms | 0.205 ms | **0.174 ms** | 10.57x | 13.66x |
| **128 KiB** | Small Activation | **0.018 ms** | **0.143 ms** | 0.154 ms | 0.162 ms | 0.195 ms | **0.204 ms** | 8.01x | 11.47x |
| **256 KiB** | 256 KiB | **0.028 ms** | **0.243 ms** | 0.249 ms | 0.255 ms | 0.265 ms | **0.343 ms** | 8.76x | 12.38x |
| **512 KiB** | 512 KiB | **0.048 ms** | **0.211 ms** | 0.231 ms | 0.259 ms | 0.299 ms | **0.333 ms** | 4.40x | 6.93x |
| **1 MiB** | 1 MiB Tensor | **0.054 ms** | **0.38 ms** | 0.369 ms | 0.422 ms | 0.41 ms | **0.699 ms** | 7.02x | 12.91x |
| **2 MiB** | 2 MiB | **0.088 ms** | **0.504 ms** | 0.582 ms | 0.572 ms | 0.749 ms | **1.367 ms** | 5.69x | 15.45x |
| **4 MiB** | 4 MiB | **0.143 ms** | **0.831 ms** | 0.927 ms | 1.108 ms | 1.768 ms | **2.761 ms** | 5.80x | 19.29x |
| **8 MiB** | 8 MiB | **0.286 ms** | **1.308 ms** | 1.442 ms | 1.789 ms | 2.93 ms | **5.386 ms** | 4.57x | 18.81x |
| **16 MiB** | 16 MiB Activation | **0.546 ms** | **4.241 ms** | 2.117 ms | 2.62 ms | 5.782 ms | **11.005 ms** | 7.77x | 20.17x |
| **32 MiB** | 32 MiB | **1.073 ms** | **3.618 ms** | 4.784 ms | 4.502 ms | 10.8 ms | **21.194 ms** | 3.37x | 19.76x |
| **64 MiB** | 64 MiB Chunk | **2.136 ms** | **6.263 ms** | 7.443 ms | 9.013 ms | 21.174 ms | **42.491 ms** | 2.93x | 19.89x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.262 ms** | **12.313 ms** | 13.274 ms | 19.072 ms | 42.476 ms | **84.508 ms** | 2.89x | 19.83x |
| **256 MiB** | Large Prefill (256 MiB) | **8.48 ms** | **23.818 ms** | 25.877 ms | 35.172 ms | 84.464 ms | **169.582 ms** | 2.81x | 20.00x |

## 3. Key Architecture & Sizing Takeaways for Leadership

1. **Local NUMA / PCIe Scaling Efficiency**:
   - **TP-4 Local (Single-NUMA socket)** completes a 256 MiB AllReduce in **15.38 ms**, while **TP-8 Local (Dual-socket node)** completes it in **18.01 ms**. Both vastly outperform multi-node communication due to direct PCIe Gen5 x16 host interconnects without network packetization.
2. **Multi-Node Scaling Behavior (TP-8 & TP-4 Across Hosts)**:
   - When splitting TP-8 across two hosts (4 GPUs on Node 0 + 4 GPUs on Node 1), 256 MiB AllReduce takes **52.55 ms** on 175G Native VPC, scaling linearly with network throttling up to **393.86 ms** on a 10G link (~7.5x slower).
   - When splitting TP-4 across two hosts (2 GPUs on Node 0 + 2 GPUs on Node 1), 256 MiB AllReduce takes **41.38 ms** on 175G Native VPC, scaling to **337.76 ms** on a 10G link.
3. **Network Sensitivity Threshold**:
   - In both TP-8 and TP-4 multi-node distributed setups, bandwidth throttling below 50 Gbps causes an immediate linear degradation in throughput: dropping from 50G to 10G increases prefill allreduce latency by exactly **5.0x** (from ~67-79 ms to ~337-393 ms), directly bounding large-batch inference throughput.
