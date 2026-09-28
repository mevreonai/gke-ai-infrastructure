#!/bin/bash
set -e
export PATH="/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
source /home/ayu23/vllm_env/bin/activate
echo "PATH=$PATH"
echo "nvcc=$(which nvcc)"
echo "python=$(which python3)"
cd /data/models/deepseek-v4.1-flash/inference
python3 model.py
