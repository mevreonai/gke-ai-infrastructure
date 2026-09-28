#!/bin/bash
set -e
export PATH="/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
source /home/ayu23/vllm_env/bin/activate
python3 /tmp/test_vllm_load.py
