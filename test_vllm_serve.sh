#!/bin/bash
set -e
export PATH="/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
source /home/ayu23/vllm_env/bin/activate
vllm serve /data/models/deepseek-v4.1-flash --trust-remote-code --tensor-parallel-size 8 --dry-run || true
