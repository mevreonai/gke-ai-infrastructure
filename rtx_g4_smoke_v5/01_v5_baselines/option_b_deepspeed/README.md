# Option B: Nsys CUDA Kernel Profiling Suite

This suite contains surgical profiling scripts and verified kernel breakdown artifacts for Kimi-Linear 48B running on NVIDIA Blackwell GPUs (`g4-standard-384`).

- **`scripts/14_run_vllm_nsys_profile.sh`**: Launch vLLM under Nsys with layerwise NVTX tracing.
- **`scripts/16_analyze_vllm_profiles.py`**: Parse exported SQLite/CSV reports to extract kernel-level metrics.
- **`scripts/run_option_b.sh`**: One-click execution for 8K and 128K context probes.
- **`results/option_b_8k/`**: Verified 8K probe results and kernel summaries.
- **`results/option_b_128k/`**: Verified 128K probe results and kernel summaries.
