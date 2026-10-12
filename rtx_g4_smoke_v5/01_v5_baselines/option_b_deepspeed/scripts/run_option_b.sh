#!/bin/bash
set -euo pipefail
# Run Option B: Nsys CUDA Kernel Profiling (8K & 128K context)
OUT_DIR="${1:-$HOME/v5_profiling/option_b_results}"
mkdir -p "$OUT_DIR"
echo "=== Running 8K Nsys Probe ==="
PROFILE_ROOT="$OUT_DIR/option_b_8k" INPUT_LEN=8192 OUTPUT_LEN=32 bash 14_run_vllm_nsys_profile.sh
echo "=== Running 128K Nsys Probe ==="
PROFILE_ROOT="$OUT_DIR/option_b_128k" INPUT_LEN=131072 OUTPUT_LEN=32 bash 14_run_vllm_nsys_profile.sh
python3 16_analyze_vllm_profiles.py --profile-root "$OUT_DIR"
echo "Option B complete. Results in $OUT_DIR"
