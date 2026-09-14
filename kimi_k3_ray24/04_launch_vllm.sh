#!/usr/bin/env bash
# ==============================================================================
# 04_launch_vllm.sh
# Launch vLLM OpenAI-Compatible API Server across 24 GPUs (TP=8, PP=3)
# Run on kimi-node-0 (Ray Head Node)
# ==============================================================================

set -euo pipefail

MODEL_PATH="/models/kimi-k3"
MODEL_NAME="moonshotai/Kimi-K3"
PORT=8000
MAX_MODEL_LEN=8192
GPU_UTIL=0.90

echo "======================================================================"
echo " Launching vLLM with Ray Distributed Executor"
echo " Model:             $MODEL_NAME ($MODEL_PATH)"
echo " Parallelism:       TP=8 (Intra-Node) x PP=3 (Inter-Node) = 24 GPUs"
echo " Max Context:       $MAX_MODEL_LEN tokens"
echo " GPU Utilization:   $GPU_UTIL"
echo " API Port:          $PORT"
echo "======================================================================"

docker exec -d ray-head vllm serve "$MODEL_PATH" \
    --served-model-name "$MODEL_NAME" \
    --distributed-executor-backend ray \
    --tensor-parallel-size 8 \
    --pipeline-parallel-size 3 \
    --gpu-memory-utilization "$GPU_UTIL" \
    --max-model-len "$MAX_MODEL_LEN" \
    --trust-remote-code \
    --port "$PORT"

echo "vLLM launched in background."
echo "Follow loading progress: docker exec ray-head bash -c 'tail -f \$(ls -S /tmp/ray/session_latest/logs/worker-*.err | head -n 1)'"
