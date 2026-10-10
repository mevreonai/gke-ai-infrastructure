#!/usr/bin/env bash
# ==============================================================================
# DEMO STEP 6: Serve Model via vLLM Distributed Engine
# ==============================================================================
# Architecture: Tensor Parallelism (TP=8) across 8x NVIDIA RTX PRO 6000 GPUs
# Memory Breakdown:
#   - Total Node VRAM : 760 GB (8x 95 GB GDDR7)
#   - Model Footprint : ~96 GB total in BF16 (~12 GB per GPU)
#   - KV-Cache Pool   : ~83 GB per GPU for massive context & concurrency
# ==============================================================================
set -euo pipefail

VENV_BIN="$HOME/vllm_env/bin"
export PATH="$VENV_BIN:$PATH"

MODEL_ID="${MODEL:-${MODEL_ID:-moonshotai/Kimi-Linear-48B-A3B-Instruct}}"
TP_SIZE="${TP_SIZE:-8}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
PORT="${PORT:-8000}"
ENFORCE_EAGER="${ENFORCE_EAGER:-0}"

export CUDA_DEVICE_ORDER="PCI_BUS_ID"
export VLLM_MOE_BACKEND="triton"
export VLLM_FLASHINFER_AUTOTUNE="1"
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"

EXTRA_ARGS=()
if [[ "$ENFORCE_EAGER" == "1" ]]; then
  EXTRA_ARGS+=(--enforce-eager)
fi

echo "======================================================================"
echo " [DEMO] Launching vLLM Engine with Target Model"
echo "======================================================================"
echo " Model Target        : $MODEL_ID"
echo " Tensor Parallelism  : TP=$TP_SIZE (Across all 8 GPUs)"
echo " Max Context Length  : $MAX_MODEL_LEN Tokens"
echo " API Port            : $PORT"
echo " Engine Acceleration : FlashInfer + PagedAttention + CUDA Graphs"
echo "======================================================================"

exec "$VENV_BIN/vllm" serve "$MODEL_ID" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --tensor-parallel-size "$TP_SIZE" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization 0.90 \
    --trust-remote-code \
    --disable-log-requests \
    "${EXTRA_ARGS[@]}"
