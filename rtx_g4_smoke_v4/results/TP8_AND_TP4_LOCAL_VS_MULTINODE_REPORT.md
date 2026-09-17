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
| **TP=8** | AllGather | **9.743 ms** | **20.692 ms** | 26.884 ms | 39.358 ms | 98.473 ms | **196.952 ms** | **2.12x** | **20.21x** |
| **TP=8** | ReduceScatter | **9.444 ms** | **26.688 ms** | 22.919 ms | 39.363 ms | 98.437 ms | **197.068 ms** | **2.83x** | **20.87x** |
| **TP=4** | AllReduce | **15.382 ms** | **41.384 ms** | 41.775 ms | 67.601 ms | 168.829 ms | **337.761 ms** | **2.69x** | **21.96x** |
| **TP=4** | AllGather | **8.435 ms** | **20.047 ms** | 20.063 ms | 33.764 ms | 84.439 ms | **168.974 ms** | **2.38x** | **20.03x** |
| **TP=4** | ReduceScatter | **8.479 ms** | **20.978 ms** | 18.952 ms | 33.786 ms | 84.503 ms | **168.884 ms** | **2.47x** | **19.92x** |

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
| **16 KiB** | Batch-1 Token Decode | **0.016 ms** | **0.102 ms** | 0.099 ms | 0.111 ms | 0.11 ms | **0.1 ms** | 6.16x | 6.05x |
| **32 KiB** | 32 KiB | **0.019 ms** | **0.102 ms** | 0.102 ms | 0.117 ms | 0.111 ms | **0.103 ms** | 5.44x | 5.46x |
| **64 KiB** | 64 KiB | **0.02 ms** | **0.124 ms** | 0.121 ms | 0.135 ms | 0.141 ms | **0.116 ms** | 6.31x | 5.94x |
| **128 KiB** | Small Activation | **0.031 ms** | **0.127 ms** | 0.127 ms | 0.139 ms | 0.141 ms | **0.193 ms** | 4.15x | 6.31x |
| **256 KiB** | 256 KiB | **0.047 ms** | **0.143 ms** | 0.142 ms | 0.162 ms | 0.196 ms | **0.384 ms** | 3.02x | 8.13x |
| **512 KiB** | 512 KiB | **0.083 ms** | **0.165 ms** | 0.165 ms | 0.18 ms | 0.194 ms | **0.385 ms** | 1.98x | 4.62x |
| **1 MiB** | 1 MiB Tensor | **0.075 ms** | **0.225 ms** | 0.234 ms | 0.258 ms | 0.387 ms | **0.769 ms** | 2.98x | 10.19x |
| **2 MiB** | 2 MiB | **0.118 ms** | **0.311 ms** | 0.309 ms | 0.33 ms | 0.767 ms | **1.536 ms** | 2.65x | 13.06x |
| **4 MiB** | 4 MiB | **0.181 ms** | **0.516 ms** | 0.556 ms | 0.614 ms | 1.534 ms | **3.069 ms** | 2.85x | 16.97x |
| **8 MiB** | 8 MiB | **0.334 ms** | **0.853 ms** | 1.017 ms | 1.23 ms | 3.074 ms | **6.216 ms** | 2.56x | 18.64x |
| **16 MiB** | 16 MiB Activation | **0.634 ms** | **1.381 ms** | 1.736 ms | 2.458 ms | 6.151 ms | **12.277 ms** | 2.18x | 19.35x |
| **32 MiB** | 32 MiB | **1.24 ms** | **2.691 ms** | 3.823 ms | 4.908 ms | 12.283 ms | **24.596 ms** | 2.17x | 19.84x |
| **64 MiB** | 64 MiB Chunk | **2.461 ms** | **5.258 ms** | 6.763 ms | 9.848 ms | 24.596 ms | **49.312 ms** | 2.14x | 20.04x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.896 ms** | **10.604 ms** | 13.511 ms | 19.679 ms | 49.21 ms | **98.482 ms** | 2.17x | 20.12x |
| **256 MiB** | Large Prefill (256 MiB) | **9.743 ms** | **20.692 ms** | 26.884 ms | 39.358 ms | 98.473 ms | **196.952 ms** | 2.12x | 20.21x |

### ReduceScatter (TP=8)

| Payload Size | Milestone Description | TP=8 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16 KiB** | Batch-1 Token Decode | **0.018 ms** | **0.101 ms** | 0.1 ms | 0.102 ms | 0.102 ms | **0.101 ms** | 5.75x | 5.72x |
| **32 KiB** | 32 KiB | **0.037 ms** | **0.106 ms** | 0.103 ms | 0.101 ms | 0.101 ms | **0.103 ms** | 2.86x | 2.78x |
| **64 KiB** | 64 KiB | **0.019 ms** | **0.138 ms** | 0.129 ms | 0.127 ms | 0.12 ms | **0.129 ms** | 7.12x | 6.63x |
| **128 KiB** | Small Activation | **0.029 ms** | **0.125 ms** | 0.154 ms | 0.128 ms | 0.125 ms | **0.193 ms** | 4.27x | 6.59x |
| **256 KiB** | 256 KiB | **0.05 ms** | **0.161 ms** | 0.161 ms | 0.139 ms | 0.192 ms | **0.389 ms** | 3.24x | 7.83x |
| **512 KiB** | 512 KiB | **0.09 ms** | **0.174 ms** | 0.17 ms | 0.172 ms | 0.192 ms | **0.385 ms** | 1.92x | 4.26x |
| **1 MiB** | 1 MiB Tensor | **0.075 ms** | **0.263 ms** | 0.228 ms | 0.215 ms | 0.384 ms | **0.769 ms** | 3.51x | 10.25x |
| **2 MiB** | 2 MiB | **0.124 ms** | **0.362 ms** | 0.327 ms | 0.336 ms | 0.767 ms | **1.534 ms** | 2.91x | 12.33x |
| **4 MiB** | 4 MiB | **0.187 ms** | **0.573 ms** | 0.555 ms | 0.649 ms | 1.535 ms | **3.072 ms** | 3.07x | 16.44x |
| **8 MiB** | 8 MiB | **0.349 ms** | **1.008 ms** | 1.002 ms | 1.249 ms | 3.073 ms | **6.161 ms** | 2.89x | 17.65x |
| **16 MiB** | 16 MiB Activation | **0.637 ms** | **1.84 ms** | 1.672 ms | 2.457 ms | 6.146 ms | **12.299 ms** | 2.89x | 19.32x |
| **32 MiB** | 32 MiB | **1.251 ms** | **3.479 ms** | 2.872 ms | 4.914 ms | 12.28 ms | **24.569 ms** | 2.78x | 19.65x |
| **64 MiB** | 64 MiB Chunk | **2.465 ms** | **7.016 ms** | 5.602 ms | 9.834 ms | 24.594 ms | **49.294 ms** | 2.85x | 20.00x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.845 ms** | **13.985 ms** | 11.44 ms | 19.678 ms | 49.202 ms | **98.46 ms** | 2.89x | 20.32x |
| **256 MiB** | Large Prefill (256 MiB) | **9.444 ms** | **26.688 ms** | 22.919 ms | 39.363 ms | 98.437 ms | **197.068 ms** | 2.83x | 20.87x |

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
| **16 KiB** | Batch-1 Token Decode | **0.011 ms** | **0.078 ms** | 0.122 ms | 0.08 ms | 0.083 ms | **0.086 ms** | 7.03x | 7.72x |
| **32 KiB** | 32 KiB | **0.012 ms** | **0.086 ms** | 0.087 ms | 0.088 ms | 0.09 ms | **0.088 ms** | 7.29x | 7.48x |
| **64 KiB** | 64 KiB | **0.012 ms** | **0.09 ms** | 0.091 ms | 0.092 ms | 0.091 ms | **0.088 ms** | 7.24x | 7.09x |
| **128 KiB** | Small Activation | **0.017 ms** | **0.098 ms** | 0.098 ms | 0.096 ms | 0.1 ms | **0.164 ms** | 5.76x | 9.63x |
| **256 KiB** | 256 KiB | **0.027 ms** | **0.153 ms** | 0.161 ms | 0.161 ms | 0.168 ms | **0.33 ms** | 5.77x | 12.44x |
| **512 KiB** | 512 KiB | **0.044 ms** | **0.141 ms** | 0.138 ms | 0.135 ms | 0.167 ms | **0.33 ms** | 3.22x | 7.51x |
| **1 MiB** | 1 MiB Tensor | **0.054 ms** | **0.21 ms** | 0.221 ms | 0.219 ms | 0.33 ms | **0.659 ms** | 3.92x | 12.31x |
| **2 MiB** | 2 MiB | **0.082 ms** | **0.259 ms** | 0.283 ms | 0.266 ms | 0.658 ms | **1.316 ms** | 3.18x | 16.14x |
| **4 MiB** | 4 MiB | **0.138 ms** | **0.389 ms** | 0.413 ms | 0.527 ms | 1.317 ms | **2.636 ms** | 2.82x | 19.13x |
| **8 MiB** | 8 MiB | **0.278 ms** | **0.693 ms** | 0.706 ms | 1.075 ms | 2.635 ms | **5.268 ms** | 2.49x | 18.95x |
| **16 MiB** | 16 MiB Activation | **0.542 ms** | **1.329 ms** | 1.331 ms | 2.109 ms | 5.266 ms | **10.534 ms** | 2.45x | 19.45x |
| **32 MiB** | 32 MiB | **1.069 ms** | **2.606 ms** | 2.594 ms | 4.223 ms | 10.553 ms | **21.092 ms** | 2.44x | 19.74x |
| **64 MiB** | 64 MiB Chunk | **2.124 ms** | **5.088 ms** | 5.041 ms | 8.458 ms | 21.096 ms | **42.199 ms** | 2.40x | 19.87x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.236 ms** | **10.126 ms** | 10.07 ms | 16.882 ms | 42.441 ms | **84.413 ms** | 2.39x | 19.93x |
| **256 MiB** | Large Prefill (256 MiB) | **8.435 ms** | **20.047 ms** | 20.063 ms | 33.764 ms | 84.439 ms | **168.974 ms** | 2.38x | 20.03x |

### ReduceScatter (TP=4)

| Payload Size | Milestone Description | TP=4 Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16 KiB** | Batch-1 Token Decode | **0.011 ms** | **0.077 ms** | 0.078 ms | 0.076 ms | 0.075 ms | **0.08 ms** | 7.19x | 7.53x |
| **32 KiB** | 32 KiB | **0.011 ms** | **0.088 ms** | 0.105 ms | 0.086 ms | 0.087 ms | **0.087 ms** | 7.70x | 7.59x |
| **64 KiB** | 64 KiB | **0.012 ms** | **0.089 ms** | 0.108 ms | 0.091 ms | 0.092 ms | **0.09 ms** | 7.15x | 7.22x |
| **128 KiB** | Small Activation | **0.018 ms** | **0.1 ms** | 0.114 ms | 0.098 ms | 0.099 ms | **0.164 ms** | 5.72x | 9.40x |
| **256 KiB** | 256 KiB | **0.028 ms** | **0.16 ms** | 0.194 ms | 0.16 ms | 0.165 ms | **0.33 ms** | 5.76x | 11.90x |
| **512 KiB** | 512 KiB | **0.048 ms** | **0.141 ms** | 0.163 ms | 0.14 ms | 0.165 ms | **0.329 ms** | 2.92x | 6.82x |
| **1 MiB** | 1 MiB Tensor | **0.054 ms** | **0.225 ms** | 0.253 ms | 0.221 ms | 0.342 ms | **0.677 ms** | 4.17x | 12.56x |
| **2 MiB** | 2 MiB | **0.088 ms** | **0.285 ms** | 0.277 ms | 0.33 ms | 0.668 ms | **1.318 ms** | 3.23x | 14.93x |
| **4 MiB** | 4 MiB | **0.144 ms** | **0.417 ms** | 0.398 ms | 0.534 ms | 1.318 ms | **2.638 ms** | 2.89x | 18.30x |
| **8 MiB** | 8 MiB | **0.288 ms** | **0.73 ms** | 0.67 ms | 1.074 ms | 2.631 ms | **5.271 ms** | 2.54x | 18.32x |
| **16 MiB** | 16 MiB Activation | **0.547 ms** | **1.393 ms** | 1.233 ms | 2.121 ms | 5.262 ms | **10.542 ms** | 2.55x | 19.26x |
| **32 MiB** | 32 MiB | **1.078 ms** | **2.64 ms** | 2.414 ms | 4.225 ms | 10.54 ms | **21.093 ms** | 2.45x | 19.57x |
| **64 MiB** | 64 MiB Chunk | **2.141 ms** | **5.335 ms** | 4.979 ms | 8.451 ms | 21.089 ms | **42.193 ms** | 2.49x | 19.71x |
| **128 MiB** | 8K Prefill Chunk (128 MiB) | **4.262 ms** | **10.688 ms** | 9.672 ms | 16.909 ms | 42.192 ms | **84.427 ms** | 2.51x | 19.81x |
| **256 MiB** | Large Prefill (256 MiB) | **8.479 ms** | **20.978 ms** | 18.952 ms | 33.786 ms | 84.503 ms | **168.884 ms** | 2.47x | 19.92x |

## 3. Key Architecture & Sizing Takeaways for Leadership

1. **Local NUMA / PCIe Scaling Efficiency**:
   - **TP-4 Local (Single-NUMA socket)** completes a 256 MiB AllReduce in **15.38 ms**, while **TP-8 Local (Dual-socket node)** completes it in **18.01 ms**. Both vastly outperform multi-node communication due to direct PCIe Gen5 x16 host interconnects without network packetization.
2. **Multi-Node Scaling Behavior (TP-8 & TP-4 Across Hosts)**:
   - When splitting TP-8 across two hosts (4 GPUs on Node 0 + 4 GPUs on Node 1), 256 MiB AllReduce takes **52.55 ms** on 175G Native VPC, scaling linearly with network throttling up to **393.86 ms** on a 10G link (~7.5x slower).
   - When splitting TP-4 across two hosts (2 GPUs on Node 0 + 2 GPUs on Node 1), 256 MiB AllReduce takes **41.38 ms** on 175G Native VPC, scaling to **337.76 ms** on a 10G link.
3. **Network Sensitivity Threshold**:
   - In both TP-8 and TP-4 multi-node distributed setups, bandwidth throttling below 50 Gbps causes an immediate linear degradation in throughput: dropping from 50G to 10G increases prefill allreduce latency by exactly **5.0x** (from ~67-79 ms to ~337-393 ms), directly bounding large-batch inference throughput.
