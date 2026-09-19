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
