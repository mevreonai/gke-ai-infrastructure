#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/var/log/deepseek_startup.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=================================================="
echo "Starting DeepSeek-V4.1-Flash TP=8 Bootstrap"
echo "Timestamp: $(date -u)"
echo "=================================================="

# 1. Verify NVIDIA Driver & GPU topology
echo "[1/6] Verifying 8x NVIDIA A100 GPUs..."
until command -v nvidia-smi &> /dev/null; do
    echo "Waiting for NVIDIA driver installation to complete..."
    sleep 10
done

nvidia-smi
nvidia-smi topo -m

# 2. Install Docker & NVIDIA Container Toolkit if not already present
echo "[2/6] Configuring Container Runtime..."
if ! command -v docker &> /dev/null; then
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
fi

if ! dpkg -l | grep -q nvidia-container-toolkit; then
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    apt-get update
    apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi

# 3. Mount GCS Model Bucket using Cloud Storage FUSE
echo "[3/6] Mounting GCS Model Bucket (mevreon-deepseek-models)..."
if ! command -v gcsfuse &> /dev/null; then
    export GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s)
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
    apt-get update
    apt-get install -y gcsfuse
fi

mkdir -p /mnt/models
if ! mountpoint -q /mnt/models; then
    gcsfuse --implicit-dirs -o ro --file-mode=777 --dir-mode=777 mevreon-deepseek-models /mnt/models
    echo "Cloud Storage mounted successfully at /mnt/models."
fi

# 4. Start NVIDIA DCGM GPU Exporter (Port 9400)
echo "[4/6] Launching NVIDIA DCGM GPU Exporter for Prometheus on :9400..."
docker rm -f dcgm-exporter || true
docker run -d --name dcgm-exporter \
    --restart unless-stopped \
    --gpus all \
    --net host \
    --cap-add SYS_ADMIN \
    nvcr.io/nvidia/k8s/dcgm-exporter:3.3.5-3.4.1-ubuntu22.04

# 5. Start Prometheus Scraper (Port 9090)
echo "[5/6] Starting Prometheus Container on :9090..."
mkdir -p /etc/prometheus
cat << 'EOF' > /etc/prometheus/prometheus.yml
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

docker rm -f prometheus || true
docker run -d --name prometheus \
    --restart unless-stopped \
    --net host \
    -v /etc/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
    prom/prometheus:latest \
    --config.file=/etc/prometheus/prometheus.yml \
    --web.listen-address=0.0.0.0:9090

# 6. Launch vLLM Serving DeepSeek FP8 with TP=8
echo "[6/7] Launching vLLM Engine (TP=8, FP8, NVLink) on :8000..."
docker rm -f vllm-deepseek || true
docker run -d --name vllm-deepseek \
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


# 7. Launch Gradio Chat UI on :7860
echo "[7/7] Launching Gradio Chat UI container on :7860..."
docker rm -f gradio-ui || true
docker run -d --name gradio-ui \
    --restart unless-stopped \
    --net host \
    -e HOST="http://localhost:8000" \
    -e MODEL_ID="/models/deepseek-ai/DeepSeek-V4.1-Flash" \
    -e CONTEXT_PATH="/v1/chat/completions" \
    -e LLM_ENGINE="openai-chat" \
    -e DISABLE_SYSTEM_MESSAGE="true" \
    us-docker.pkg.dev/google-samples/containers/gke/gradio-app:v1.0.7

echo "=================================================="
echo "DeepSeek-V4.1-Flash TP=8 stack launched!"
echo "Gradio Chat UI: http://<EXTERNAL_IP>:7860"
echo "vLLM API:       http://<EXTERNAL_IP>:8000/v1"
echo "Prometheus:     http://<EXTERNAL_IP>:9090"
echo "Metrics:        http://<EXTERNAL_IP>:8000/metrics"
echo "DCGM Metrics:   http://<EXTERNAL_IP>:9400/metrics"
echo "=================================================="

