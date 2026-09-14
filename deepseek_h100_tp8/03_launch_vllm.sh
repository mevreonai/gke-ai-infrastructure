#!/usr/bin/env bash
# ==============================================================================
# 03_launch_vllm.sh
# Launch DeepSeek-V4.1-Flash with vLLM in Docker (Tensor Parallel = 8)
# Run inside the 8x H100 VM.
# ==============================================================================

CONTAINER_NAME="vllm-deepseek"
IMAGE_TAG="vllm/vllm-openai:deepseekv41-flash-0909"
MODEL_DIR="/data/models/deepseek-v4.1-flash"
PORT=8000

# Remove any existing container
sudo docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "=== Launching vLLM on 8x NVIDIA H100 GPUs ==="
sudo docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --gpus all \
    --ipc=host \
    --net=host \
    -v "$MODEL_DIR":/models/deepseek-ai/DeepSeek-V4.1-Flash:ro \
    "$IMAGE_TAG" \
    --model /models/deepseek-ai/DeepSeek-V4.1-Flash \
    --tensor-parallel-size 8 \
    --tokenizer-mode deepseek_v41 \
    --language-model-only \
    --gpu-memory-utilization 0.92 \
    --served-model-name deepseek-ai/DeepSeek-V4.1-Flash \
    --trust-remote-code \
    --port "$PORT" \
    --host 0.0.0.0

echo "Container launched."
echo "Follow logs using: sudo docker logs -f $CONTAINER_NAME"
