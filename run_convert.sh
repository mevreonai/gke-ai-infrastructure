#!/bin/bash
set -e
export PATH="/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
source /home/ayu23/vllm_env/bin/activate

mkdir -p /data/models/deepseek-v4.1-flash-tp8

echo "Starting convert.py..."
cd /data/models/deepseek-v4.1-flash/inference
python3 convert.py \
  --hf-ckpt-path /data/models/deepseek-v4.1-flash \
  --save-path /data/models/deepseek-v4.1-flash-tp8 \
  --model-parallel 8 \
  --expert-dtype fp4 \
  --tokenizer-path /data/models/deepseek-v4.1-flash

cp /data/models/deepseek-v4.1-flash/config.json /data/models/deepseek-v4.1-flash-tp8/
echo "Conversion complete!"
ls -lh /data/models/deepseek-v4.1-flash-tp8/
