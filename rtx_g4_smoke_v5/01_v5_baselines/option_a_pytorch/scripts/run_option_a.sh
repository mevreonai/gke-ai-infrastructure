#!/bin/bash
set -euo pipefail
# Run Option A: vLLM Single-Node Surrogate Suite on Blackwell RTX PRO 6000
OUT_DIR="${1:-$HOME/v5_profiling/option_a_results}"
mkdir -p "$OUT_DIR"
python3 11_run_vllm_surrogate.py --out "$OUT_DIR"
python3 15_summarize_vllm.py --dir "$OUT_DIR"
echo "Option A complete. Results in $OUT_DIR"
