# Blackwell RTX PRO 6000 Kimi-Linear 48B Profiling Suite (V5)

Comprehensive benchmark and kernel profiling suite for `moonshotai/Kimi-Linear-48B-A3B-Instruct` on NVIDIA Blackwell RTX PRO 6000 GPUs (`g4-standard-384`, `us-central1-b`).

## Repository Organization

```text
rtx_g4_smoke_v5/
├── README.md                           # Suite overview and hardware topology
├── kimi_linear_provenance.json         # Hugging Face checkpoint metadata & shard provenance
├── option_a/                           # Single-Node vLLM Surrogate Sweep
│   ├── README.md                       # Methodology and findings
│   ├── scripts/                        # Production runner, cases config, metrics sampler
│   │   ├── 08_validate_kimi_linear.py
│   │   ├── 09_metrics_sampler.py
│   │   ├── 10_vllm_surrogate_cases.json
│   │   ├── 11_run_vllm_surrogate.py
│   │   ├── 15_summarize_vllm.py
│   │   └── run_option_a.sh
│   └── results/                        # Measured benchmark telemetry & CSVs
│       ├── VLLM_SUMMARY.md
│       └── vllm_runs.csv
└── option_b/                           # Surgical Nsys CUDA Kernel Profiling
    ├── README.md                       # Profiling methodology & eager mode explanation
    ├── scripts/                        # Nsys profiler script and SQLite trace analyzer
    │   ├── 14_run_vllm_nsys_profile.sh
    │   ├── 16_analyze_vllm_profiles.py
    │   └── run_option_b.sh
    └── results/                        # Verified 8K and 128K kernel traces & summaries
        ├── OPTION_B_SUMMARY.md
        ├── option_b_8k/
        └── option_b_128k/
└── option_c/                           # 16-GPU Multi-Node Distributed Serving (Ray Cluster)
    ├── README.md                       # Multi-node scaling & TP8_PP2 vs TP16_PP1 analysis
    ├── scripts/                        # Ray multi-node runner & benchmark cases
    │   ├── 10b_vllm_multi_node_cases.json
    │   └── 12_run_vllm_multi_node.py
    └── results/                        # Telemetry & JSON outputs
        ├── tp8_pp2_dist/
        │   └── 128k_c1.json
        └── tp16_pp1_dist/
            └── 128k_c1.json
```

## Hardware Topology
- **Instance:** `g4-standard-384` (Google Compute Engine)
- **CPUs:** 384 vCPUs (Intel Xeon Platinum 8581C)
- **Memory:** 1.5 TB Host RAM
- **GPUs:** 8× NVIDIA RTX PRO 6000 Blackwell (96 GB GDDR7 per GPU, Compute Capability 12.0)
- **Interconnect:** PCIe Gen5 (no NVLink)

---

## 📊 Master Benchmark Comparison (Option A vs Option B vs Option C)

For complete technical notes and kernel breakdown, see [MASTER_BENCHMARK_SUMMARY.md](MASTER_BENCHMARK_SUMMARY.md).

| Metric | Option A (`tp8_cold_chunk8k`) | Option A (`tp4_chunk16k`) | Option B (Nsys Eager Profile) | Option C (`tp8_pp2_dist` 16-GPU) | Option C (`tp16_pp1_dist` 16-GPU) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Topology** | 1 Node (8 GPUs, TP8) | 1 Node (4 GPUs, TP4) | 1 Node (8 GPUs, Eager) | 2 Nodes (16 GPUs, TP8 PP2) | 2 Nodes (16 GPUs, TP16 PP1) |
| **Total VRAM** | 768 GB | 384 GB | 768 GB | 1,536 GB (1.536 TB) | 1,536 GB (1.536 TB) |
| **Test Context** | 8K input / 128 out | 128K input / 128 out | 128K input / 32 out | 128K input / 128 out | 128K input / 128 out |
| **TTFT (Cold)** | **278.45 ms** | **4,654.34 ms** | **4,970.15 ms** | **4,650.99 ms** | **8,216.91 ms** |
| **TTFT (Warmed)** | ~180 ms | ~2,750 ms | N/A (profiler overhead) | **2,810.45 ms** | 8,216.91 ms |
| **TPOT (Decode Latency)** | **6.88 ms / tok** | **5.71 ms / tok** | **31.46 ms / tok** (unbatched) | **7.49 ms / tok** | **11.57 ms / tok** |
| **Decode Throughput** | **145.3 tok/s** | **175.1 tok/s** | ~32 tok/s (overhead) | **133.4 tok/s** | **87.0 tok/s** |
| **Median ITL** | 6.85 ms | 5.69 ms | 31.26 ms | 7.48 ms | 11.55 ms |
| **E2E Latency** | 1,159 ms | 5,385 ms | 5,976 ms | 5,602.77 ms | 9,685.75 ms |

---

## 🎯 Key Architectural Findings
1. **Pipeline Parallelism across Nodes (`tp8_pp2_dist`) is 1.86× faster than single-node TP8 (7.49 ms vs 13.91 ms)**: Keeps All-Reduce within local PCIe Gen 5 and only sends activations across 10GbE VPC.
2. **Tensor Parallelism across Nodes (`tp16_pp1_dist`) suffers severe network latency degradation (11.57 ms decode, 8.2s TTFT)**: All-Reduce collectives stall across standard 10GbE network interfaces.
3. **Prefix Caching on Single-Node TP8 delivers 3.64× TTFT acceleration** (1,278 ms vs 4,654 ms) for multi-turn conversations.
4. **Kernel Verification confirms 80 model layers**: Exact $31 \times 80 = 2,480$ invocations of `fused_recurrent_kda_packed_decode_kernel` and `_causal_conv1d_update_kernel`.
