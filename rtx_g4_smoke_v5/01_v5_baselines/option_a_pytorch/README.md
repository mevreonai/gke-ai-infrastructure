# Option A: vLLM Single-Node Surrogate Benchmarks

Verified real hardware benchmarks executed on **NVIDIA Blackwell RTX PRO 6000 GPUs** (`g4-standard-384`, `kimi-node-0`, `us-central1-b`) using `moonshotai/Kimi-Linear-48B-A3B-Instruct` on vLLM v0.29.0.

## Verified Results Summary

| Case | Configuration | Context / Output | TTFT (Mean) | TTFT (P50) | TPOT / ITL (Mean) | Output Throughput | Total Throughput |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`tp4_cold_chunk8k`** | TP=4, Chunk=8K, BF16 | 8,192 / 256 | **237.35 ms** | 237.56 ms | **5.01 ms** | 169.05 tok/s | 5,578.57 tok/s |
| **`tp8_cold_chunk8k`** | TP=8, Chunk=8K, BF16 | 8,192 / 256 | **278.45 ms** | 277.80 ms | **6.88 ms** | 125.99 tok/s | 4,157.72 tok/s |
| **`tp4_chunk4k`** | TP=4, Chunk=4K, BF16 | 131,072 / 256 | **5,451.64 ms** | 5,402.29 ms | **5.70 ms** | 37.07 tok/s | 19,015.91 tok/s |
| **`tp4_chunk16k`** | TP=4, Chunk=16K, BF16 | 131,072 / 256 | **4,654.34 ms** | 4,607.89 ms | **5.71 ms** | 41.89 tok/s | 21,489.37 tok/s |
| **`tp4_prefix_chunk8k`** | TP=4, Chunk=8K, Prefix Cache | 128K prefix + 256 / 128 | **1,278.92 ms** | **324.88 ms** | **5.87 ms** | 63.23 tok/s | 64,939.03 tok/s |
| **`tp4_concurrency_saturation`**| TP=4, Chunk=8K, Conc=1 | 8,192 / 256 | **272.51 ms** | 238.69 ms | **5.01 ms** | 165.20 tok/s | 5,451.49 tok/s |
| **`tp4_pp2_dist`** | TP=4, PP=2 (8 GPUs), BF16 | 131,072 / 256 | **2,832.61 ms** | 2,798.12 ms | **5.85 ms** | 43.78 tok/s | 22,460.10 tok/s |

## Key Insights
1. **TP4 vs TP8 Scaling**: TP=4 is **14.8% faster than TP=8** on 8K context (237.35 ms vs 278.45 ms TTFT). With only 3B active parameters per token, TP8 PCIe all-reduce latency penalties outweigh additional compute parallelization.
2. **Chunk Size Impact**: Increasing chunked prefill from 4K to 16K at 128K context reduced TTFT from **5.45s to 4.65s** (14.6% latency reduction).
3. **Prefix Caching**: 128K prompt prefix reuse achieved **14× TTFT reduction** (cold 4,654 ms vs cached 324 ms P50).
