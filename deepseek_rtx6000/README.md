# DeepSeek-V4.1-Flash on 8× NVIDIA RTX Pro 6000 (96 GB VRAM) Runbook

This guide provides the complete, production-grade architecture and manual step-by-step commands to deploy **DeepSeek-V4.1-Flash (FP8)** across **8× NVIDIA RTX Pro 6000 GPUs (768 GB aggregate VRAM)** using a dedicated **1,000 GB local hard disk** to eliminate cloud storage bottlenecks.

---

## 1. How the Components Fuse Together

```
+-----------------------------------------------------------------------------------+
|                        GCP Virtual Machine (1,000 GB Hard Disk)                   |
|                                                                                   |
|  [ Physical Hard Disk /dev/sda1 ]  -->  /data/models/deepseek-v4.1-flash/        |
|  (1,000 GB NVMe/SSD, >800 MB/s)         (475 GB raw safetensors weights)          |
|                                                     |                             |
|                                                     v (Local Docker Volume Mount) |
|  +-----------------------------------------------------------------------------+  |
|  | vLLM Distributed Engine Container (vllm/vllm-openai:deepseekv41-flash-0909) |  |
|  | - Tensor Parallelism: 8                                                    |  |
|  | - Model Arch: DeepseekV41ForCausalLM (--language-model-only)               |  |
|  | - Quantization: UE8M0 DeepGEMM FP8                                         |  |
|  | - Sharded Across: GPU 0, 1, 2, 3, 4, 5, 6, 7 (96 GB VRAM each)              |  |
|  +-----------------------------------------------------------------------------+  |
|          |                                              |                         |
|          v (:8000/v1/chat/completions)                  v (:8000/metrics)         |
|  +-----------------------------+               +-------------------------------+  |
|  | Gradio Chat Web UI (:7860)  |               | Prometheus Time-Series (:9090)|  |
|  | - Streaming response tokens |               | - Ingests engine throughput   |  |
|  | - Live 8-GPU telemetry box  |<--------------| - Ingests DCGM metrics        |  |
|  +-----------------------------+               +-------------------------------+  |
|                                                                 ^                 |
|                                                                 | (:9400/metrics) |
|                                                +-------------------------------+  |
|                                                | NVIDIA DCGM Exporter Container|  |
|                                                | - Live VRAM & GPU Core %      |  |
|                                                +-------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### The Component Pipeline:
1. **The 1,000 GB Boot Disk**: Eliminates GCS FUSE latency. By storing the 48 model shards directly on the local filesystem (`/data/models/`), vLLM reads directly from SSD at ~1 GB/s into GPU VRAM in under 6 minutes, preventing CPU I/O page faults (`Dl` hang).
2. **vLLM Distributed Model Server**: Loads the 475 GB model sharded across 8 GPUs using NCCL. Each GPU holds ~55 GB of weights, leaving ~41 GB of VRAM per card for high-speed KV cache.
3. **DCGM Exporter**: Queries the NVIDIA driver kernel directly to report exact per-GPU VRAM and compute load on port `9400`.
4. **Prometheus**: Scrapes metrics from both vLLM (`:8000`) and DCGM (`:9400`) every 5 seconds.
5. **Gradio Web Interface**: Fuses the chat window with real-time GPU statistics so you can interact with DeepSeek while watching all 8 cards operate in unison.

---

## 2. Step-by-Step Manual Commands

### Step 1: Provision the VM with 1,000 GB Hard Disk (GCP CLI or Console)
*If you already created the VM in the GCP Web Console with the 1,000 GB boot disk, skip to Step 2.*

```bash
gcloud compute instances create deepseek-rtx6000 \
    --project=mevreon \
    --zone=europe-west4-a \
    --machine-type=n1-standard-32 \
    --accelerator=type=nvidia-rtx-pro-6000-vws,count=8 \
    --boot-disk-size=1000GB \
    --boot-disk-type=pd-ssd \
    --image-family=common-cu128-ubuntu-2204-py311 \
    --image-project=deeplearning-platform-release \
    --maintenance-policy=TERMINATE
```
**Flag Explanations:**
- `--boot-disk-size=1000GB --boot-disk-type=pd-ssd`: Allocates 1 Terabyte of SSD storage to the primary disk.
- `--accelerator=type=nvidia-rtx-pro-6000-vws,count=8`: Attaches 8× RTX 6000 cards.
- `--image-family=common-cu128-ubuntu-2204-py311`: Official Google image with CUDA 12.8, Docker, and NVIDIA drivers pre-installed.

---

### Step 2: Open Firewall Ports for the Stack
Run from your local workstation:

```bash
gcloud compute firewall-rules create allow-deepseek-stack \
    --project=mevreon \
    --allow=tcp:7860,tcp:8000,tcp:9090,tcp:9400 \
    --target-tags=deepseek-instance \
    --description="Allow Gradio UI, vLLM API, Prometheus, and DCGM"
```

---

### Step 3: Connect via SSH
```bash
gcloud compute ssh deepseek-rtx6000 --zone=europe-west4-a --project=mevreon
```

Once inside, verify the 1,000 GB hard disk and 8 GPUs:
```bash
# Verify hard disk size (should show ~980G on /dev/root)
df -h /

# Verify all 8 GPUs are present and show 96 GB VRAM each
nvidia-smi
```

---

### Step 4: Download Weights Directly to the 1,000 GB Hard Disk
```bash
# 1. Create a dedicated directory on the local hard disk
sudo mkdir -p /data/models/deepseek-v4.1-flash
sudo chown -R $USER:$USER /data/models

# 2. Download directly from Google Cloud Storage to local disk
gcloud storage cp -r "gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash/*" /data/models/deepseek-v4.1-flash/
```
**Why this matters:**
- `gcloud storage cp -r` utilizes multi-threaded parallel streaming directly into the local SSD.
- Once downloaded, files reside on the physical machine disk permanently. Zero network dependencies during inference.

---

### Step 5: Start the Telemetry Exporters

#### 5.1 Launch DCGM Exporter (Port 9400)
```bash
sudo docker run -d \
    --name dcgm-exporter \
    --restart unless-stopped \
    --gpus all \
    --net=host \
    -e DCGM_EXPORTER_PORT=9400 \
    nvidia/dcgm-exporter:latest
```

#### 5.2 Launch Prometheus (Port 9090)
Create `prometheus.yml` on the VM:
```bash
cat << 'EOF' > ~/prometheus.yml
global:
  scrape_interval: 5s
scrape_configs:
  - job_name: "vllm"
    static_configs:
      - targets: ["localhost:8000"]
  - job_name: "dcgm"
    static_configs:
      - targets: ["localhost:9400"]
EOF

sudo docker run -d \
    --name prometheus \
    --restart unless-stopped \
    --net=host \
    -v ~/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
    prom/prometheus:latest \
        --config.file=/etc/prometheus/prometheus.yml \
        --web.listen-address=0.0.0.0:9090
```

---

### Step 6: Start the vLLM Engine (Port 8000)
```bash
sudo docker run -d \
    --name vllm-deepseek \
    --restart unless-stopped \
    --gpus all \
    --ipc=host \
    --net=host \
    -v /data/models/deepseek-v4.1-flash:/models/deepseek-ai/DeepSeek-V4.1-Flash:ro \
    vllm/vllm-openai:deepseekv41-flash-0909 \
    vllm serve /models/deepseek-ai/DeepSeek-V4.1-Flash \
        --tensor-parallel-size 8 \
        --tokenizer-mode deepseek_v41 \
        --language-model-only \
        --block-size 64 \
        --gpu-memory-utilization 0.92 \
        --served-model-name deepseek-ai/DeepSeek-V4.1-Flash \
        --trust-remote-code \
        --port 8000 \
        --host 0.0.0.0
```
**Parameter Breakdown:**
- `--ipc=host`: Uses host shared memory for zero-latency inter-GPU communication across the 8 ranks.
- `-v /data/models/...:/models/...:ro`: Mounts the local 1,000 GB disk path into the container in read-only mode.
- `--tensor-parallel-size 8`: Divides the model layers across all 8 RTX 6000 cards.
- `--language-model-only`: Skips the 32-layer vision tower, optimizing VRAM and inference speed.
- `--gpu-memory-utilization 0.92`: Dedicates 92% of the 96 GB VRAM (~88 GB/GPU = ~706 GB total) to model weights and KV cache.

#### Monitor Startup Logs:
```bash
sudo docker logs -f vllm-deepseek
```
*Wait until you see:* `Application startup complete` or `Uvicorn running on http://0.0.0.0:8000`.

---

### Step 7: Launch the Gradio Chat Interface (Port 7860)
On the VM:
```bash
# Install dependencies
python3 -m pip install gradio openai requests

# Run the Gradio interface
python3 web_ui.py
```

Now open in your web browser:
- **Gradio Chat UI**: `http://<EXTERNAL_IP>:7860`
- **Prometheus Dashboard**: `http://<EXTERNAL_IP>:9090`
- **DCGM Metrics**: `http://<EXTERNAL_IP>:9400/metrics`

---

### Step 8: Command-Line Smoke Test
Test the API directly using `curl`:
```bash
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "deepseek-ai/DeepSeek-V4.1-Flash",
        "messages": [
            {"role": "user", "content": "What is 17 * 19? Return only the integer."}
        ],
        "temperature": 0.0
    }'
```
*Expected output: `{"content": "323"}`*
