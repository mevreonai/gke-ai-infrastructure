#!/bin/bash
set -e
export PATH="/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
source /home/ayu23/vllm_env/bin/activate

cd /data/models/deepseek-v4.1-flash/inference

echo "=== Running DeepSeek V4.1 Flash on 8x RTX PRO 6000 GPUs ==="
torchrun --nproc-per-node 8 generate.py \
    --ckpt-path /data/models/deepseek-v4.1-flash-tp8 \
    --config config.json \
    --input-file /data/models/user_prompt.txt \
    --max-new-tokens 512 \
    --temperature 0.0
