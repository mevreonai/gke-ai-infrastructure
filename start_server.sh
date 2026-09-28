#!/bin/bash
set -e
export PATH="/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
source /home/ayu23/vllm_env/bin/activate

cd /data/models/deepseek-v4.1-flash/inference

# Kill any lingering inference or vllm processes
pkill -f api_server.py 2>/dev/null || true
pkill -f torchrun 2>/dev/null || true
docker stop ray-head 2>/dev/null || true

echo "Starting DeepSeek V4.1 Flash OpenAI Server on port 8000 (8 GPUs)..."
exec torchrun --nproc-per-node 8 api_server.py
