#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/var/log/deploy_deepseek.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=================================================="
echo "Deploying DeepSeek-V4.1-Flash on 8x A100 (TP=8)"
echo "Timestamp: $(date -u)"
echo "=================================================="

# 1. Install gcsfuse
echo "[1/5] Installing Cloud Storage FUSE..."
if ! command -v gcsfuse &> /dev/null; then
    export GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s)
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt $GCSFUSE_REPO main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor --yes -o /usr/share/keyrings/cloud.google.gpg
    sudo apt-get update
    sudo apt-get install -y gcsfuse
fi

# 2. Mount GCS Model Bucket
echo "[2/5] Mounting gs://mevreon-deepseek-models to /mnt/models..."
sudo mkdir -p /mnt/models
if ! mountpoint -q /mnt/models; then
    sudo gcsfuse --implicit-dirs -o ro --file-mode=777 --dir-mode=777 mevreon-deepseek-models /mnt/models
    echo "Cloud Storage mounted successfully at /mnt/models."
fi

# Quick verification of model files
ls -lh /mnt/models/deepseek-ai/DeepSeek-V4.1-Flash/config.json

# 3. Start NVIDIA DCGM GPU Exporter (Port 9400)
echo "[3/5] Starting NVIDIA DCGM GPU Exporter on :9400..."
sudo docker rm -f dcgm-exporter || true
sudo docker run -d --name dcgm-exporter \
    --restart unless-stopped \
    --gpus all \
    --net host \
    --cap-add SYS_ADMIN \
    nvcr.io/nvidia/k8s/dcgm-exporter:3.3.5-3.4.1-ubuntu22.04

# 4. Start Prometheus Scraper (Port 9090)
echo "[4/5] Starting Prometheus Container on :9090..."
sudo mkdir -p /etc/prometheus
cat << 'EOF' | sudo tee /etc/prometheus/prometheus.yml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: 'vllm'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'dcgm-gpu'
    static_configs:
      - targets: ['localhost:9400']
    metrics_path: '/metrics'
EOF

sudo docker rm -f prometheus || true
sudo docker run -d --name prometheus \
    --restart unless-stopped \
    --net host \
    -v /etc/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
    prom/prometheus:latest \
    --config.file=/etc/prometheus/prometheus.yml \
    --web.listen-address=0.0.0.0:9090

# 5. Start Gradio Chat UI on :7860
echo "[5/6] Starting Gradio UI Container on :7860..."
sudo docker rm -f gradio-ui || true
sudo docker run -d --name gradio-ui \
    --restart unless-stopped \
    --net host \
    -e HOST="http://localhost:8000" \
    -e MODEL_ID="deepseek-ai/DeepSeek-V4.1-Flash" \
    -e CONTEXT_PATH="/v1/chat/completions" \
    -e LLM_ENGINE="openai-chat" \
    -e DISABLE_SYSTEM_MESSAGE="true" \
    us-docker.pkg.dev/google-samples/containers/gke/gradio-app:v1.0.7

# 6. Launch vLLM with deepseekv41-flash-0909 image
echo "[6/6] Launching vLLM Engine (TP=8, MXFP4/FP8, NVLink) on :8000..."
sudo docker rm -f vllm-deepseek || true
sudo docker run -d --name vllm-deepseek \
    --restart unless-stopped \
    --gpus all \
    --ipc host \
    --net host \
    -v /mnt/models:/models:ro \
    -e VLLM_ENGINE_READY_TIMEOUT_S=3600 \
    vllm/vllm-openai:deepseekv41-flash-0909 \
    --model /models/deepseek-ai/DeepSeek-V4.1-Flash \
    --tensor-parallel-size 8 \
    --tokenizer-mode deepseek_v41 \
    --language-model-only \
    --gpu-memory-utilization 0.95 \
    --served-model-name /models/deepseek-ai/DeepSeek-V4.1-Flash deepseek-ai/DeepSeek-V4.1-Flash \
    --trust-remote-code \
    --port 8000 \
    --host 0.0.0.0

echo "=================================================="
echo "Deployment initiated successfully!"
echo "vLLM container is running and loading weights."
echo "=================================================="
