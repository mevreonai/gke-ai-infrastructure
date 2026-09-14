# Moonshot AI Kimi-K3 (24× RTX 6000 Pro) Multi-Node Live Demo Runbook

This runbook provides complete, copy-pasteable commands to execute a live demonstration or build from scratch **Moonshot AI Kimi-K3** across **3 nodes (24 GPUs, 2.3 TB VRAM)** using **Ray + vLLM**.

---

## 📋 Architecture & Parallelism Specifications

| Parameter | Configuration | Technical Explanation |
| :--- | :--- | :--- |
| **Model** | `moonshotai/Kimi-K3` | 1,453 GB weights, 96 safetensor shards, MoE architecture |
| **Cluster Topology** | 3 VMs (`g4-standard-384`) | 8× NVIDIA RTX 6000 Pro (96GB VRAM) per node = **24 GPUs total (2.3 TB VRAM)** |
| **Tensor Parallel (TP)** | **`8`** | Intra-node tensor sharding across 8 GPUs on the local PCIe/NVLink bus |
| **Pipeline Parallel (PP)**| **`3`** | Inter-node pipeline stages across 3 VMs (Node 0 → Node 1 → Node 2) |
| **Expert Parallel (EP)** | **`1`** | MoE expert layers partitioned across the 8 TP ranks on each node |
| **Storage** | **6,000 GB Total** | 2,000 GB local NVMe per node (`/data`). Local read throughput: 2.7 GB/s |
| **Inference Endpoint** | `http://<NODE_0_IP>:8000/v1` | Head node exposes OpenAI-compatible HTTP API server |

---

## ⚡ Quickstart: One-Click Master Control

Background `systemd` startup services are installed on all 3 nodes (`kimi-vllm.service` on Node 0, `kimi-ray.service` on Nodes 1 & 2). 
Ray and vLLM **boot up automatically whenever the VMs power on**.

Use the master scripts from this directory:
* **Windows PowerShell:** `.\cluster.ps1 <command>`
* **Linux / macOS / Cloud Shell:** `./cluster.sh <command>`

### 4 Essential Commands:

```powershell
# 1. Power ON all 3 nodes (Ray & vLLM start automatically on boot!)
.\cluster.ps1 start

# 2. Watch real-time model loading logs (Ctrl+C to exit):
.\cluster.ps1 logs

# 3. Test the live 24-GPU model with a sample prompt:
.\cluster.ps1 query

# 4. Power OFF all 3 nodes after demo to pause GPU billing:
.\cluster.ps1 stop
```

Run `.\cluster.ps1 status` at any time to verify cluster health and port 8000 readiness.

---

## 🚀 Part 1: Step-by-Step Manual Demo on Existing VMs

If you prefer to run commands manually inside SSH terminals, follow these steps:

### Step 1.1: Power On the 3 Nodes

Run from your local workstation:
```bash
gcloud compute instances start kimi-node-0 --zone=us-central1-b --project=mevreon
gcloud compute instances start kimi-node-1 --zone=us-central1-b --project=mevreon
gcloud compute instances start kimi-node-2 --zone=us-west1-a --project=mevreon
```

*Verify all 3 nodes report `RUNNING`:*
```bash
gcloud compute instances list --filter="name ~ kimi-node" --project=mevreon
```

---

### Step 1.2: Check Internal IP of Node 0 (Head Node)

SSH into `kimi-node-0`:
```bash
gcloud compute ssh kimi-node-0 --zone=us-central1-b --project=mevreon
```
Check internal IP (default is `10.128.0.39`):
```bash
hostname -I | awk '{print $1}'
```

---

### Step 1.3: Start Ray Cluster Across All 3 Nodes

#### On `kimi-node-0` (Ray Head):
```bash
docker rm -f ray-head 2>/dev/null || true

docker run -d --name ray-head \
  --net=host \
  --ipc=host \
  --gpus all \
  --ulimit nofile=1048576:1048576 \
  -v /data/models/kimi-k3:/models/kimi-k3 \
  --entrypoint /bin/bash \
  vllm-ray:latest \
  -c "ray start --head --port=6379 --num-gpus=8 --block"
```

#### On `kimi-node-1` (Ray Worker 1):
```bash
docker rm -f ray-worker-1 2>/dev/null || true

docker run -d --name ray-worker-1 \
  --net=host \
  --ipc=host \
  --gpus all \
  --ulimit nofile=1048576:1048576 \
  -v /data/models/kimi-k3:/models/kimi-k3 \
  --entrypoint /bin/bash \
  vllm-ray:latest \
  -c "ray start --address=10.128.0.39:6379 --num-gpus=8 --block"
```

#### On `kimi-node-2` (Ray Worker 2):
```bash
docker rm -f ray-worker-2 2>/dev/null || true

docker run -d --name ray-worker-2 \
  --net=host \
  --ipc=host \
  --gpus all \
  --ulimit nofile=1048576:1048576 \
  -v /data/models/kimi-k3:/models/kimi-k3 \
  --entrypoint /bin/bash \
  vllm-ray:latest \
  -c "ray start --address=10.128.0.39:6379 --num-gpus=8 --block"
```

---

### Step 1.4: Verify 24-GPU Cluster Health

Back on `kimi-node-0`, verify the Ray cluster topology:
```bash
docker exec ray-head ray status
```

**Expected Output:**
```text
======== Ray Cluster Status ========
Healthy:
 1 Node '10.128.0.39' (Head)
 1 Node '10.128.0.40'
 1 Node '10.138.0.3'
------------------------------------
Resources:
 Total GPUs: 24.0 / 24.0
 Total CPUs: 1152.0 / 1152.0
 Total RAM: 3.6 TB
```

---

### Step 1.5: Launch vLLM Serving Engine

On `kimi-node-0`, trigger distributed serving inside the Ray Head container:

```bash
docker exec -d ray-head vllm serve /models/kimi-k3 \
  --served-model-name moonshotai/Kimi-K3 \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 3 \
  --distributed-executor-backend ray \
  --gpu-memory-utilization 0.90 \
  --max-model-len 8192 \
  --trust-remote-code \
  --port 8000
```

*Watch real-time model loading into the 24 GPUs:*
```bash
docker exec ray-head bash -c 'tail -f $(ls -S /tmp/ray/session_latest/logs/worker-*.err | head -n 1)'
```
*Wait for shards to finish loading and Uvicorn to start:*
```text
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### Step 1.6: Run Live Demo Inferences

#### Test 1: Standard Chat Completion (Run on `kimi-node-0`)
```bash
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-K3",
    "messages": [
      {"role": "system", "content": "You are Kimi-K3 running on a distributed 24-GPU cluster."},
      {"role": "user", "content": "Explain the architecture of Kimi-K3 and why tensor parallelism is paired with pipeline parallelism."}
    ],
    "max_tokens": 150,
    "temperature": 0.6
  }' | jq
```

#### Test 2: Real-Time Token Streaming Client
```bash
python3 05_test_chat.py --host localhost --port 8000
```

---

### Step 1.7: Post-Demo Teardown (Stop Billing)

After the presentation, power off the VMs to stop compute billing:
```bash
gcloud compute instances stop kimi-node-0 --zone=us-central1-b --project=mevreon
gcloud compute instances stop kimi-node-1 --zone=us-central1-b --project=mevreon
gcloud compute instances stop kimi-node-2 --zone=us-west1-a --project=mevreon
```

---

## 🛠️ Part 2: Building from Scratch (Infrastructure Setup)

To recreate the entire cluster from zero:

### 2.1 Firewall Configuration
```bash
gcloud compute firewall-rules create allow-ray-vllm-internal \
  --project=mevreon \
  --network=default \
  --allow=tcp:6379,tcp:8000,tcp:8265,tcp:10000-10100,udp:10000-10100 \
  --source-ranges=10.128.0.0/9,10.138.0.0/16 \
  --description="Allow Ray cluster and vLLM inter-node communication"
```

### 2.2 VM Creation
```bash
# Node 0 (Head)
gcloud compute instances create kimi-node-0 \
  --project=mevreon \
  --zone=us-central1-b \
  --machine-type=g4-standard-384 \
  --accelerator=count=8,type=nvidia-rtx-pro-6000 \
  --maintenance-policy=TERMINATE \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-balanced \
  --image-family=common-cu124-debian-11 \
  --image-project=ml-images \
  --create-disk=name=kimi-node-0-data,size=2000GB,type=hyperdisk-balanced,auto-delete=no

# Node 1 (Worker 1)
gcloud compute instances create kimi-node-1 \
  --project=mevreon \
  --zone=us-central1-b \
  --machine-type=g4-standard-384 \
  --accelerator=count=8,type=nvidia-rtx-pro-6000 \
  --maintenance-policy=TERMINATE \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-balanced \
  --image-family=common-cu124-debian-11 \
  --image-project=ml-images \
  --create-disk=name=kimi-node-1-data,size=2000GB,type=hyperdisk-balanced,auto-delete=no

# Node 2 (Worker 2)
gcloud compute instances create kimi-node-2 \
  --project=mevreon \
  --zone=us-west1-a \
  --machine-type=g4-standard-384 \
  --accelerator=count=8,type=nvidia-rtx-pro-6000 \
  --maintenance-policy=TERMINATE \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-balanced \
  --image-family=common-cu124-debian-11 \
  --image-project=ml-images \
  --create-disk=name=kimi-node-2-data,size=2000GB,type=hyperdisk-balanced,auto-delete=no
```

### 2.3 Disk Formatting (Run on all 3 nodes)
```bash
sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0 /dev/sdb
sudo mkdir -p /data
sudo mount -o discard,defaults /dev/sdb /data
sudo chmod -R 777 /data
echo "/dev/sdb /data ext4 discard,defaults,nofail 0 2" | sudo tee -a /etc/fstab
```

### 2.4 Model Download (Run on all 3 nodes)
```bash
pip install -q huggingface_hub[hf_transfer]
export HF_HUB_ENABLE_HF_TRANSFER=1

python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='moonshotai/Kimi-K3',
    local_dir='/data/models/kimi-k3',
    local_dir_use_symlinks=False,
    max_workers=16
)
"

# Verification: must output 96 shards
ls /data/models/kimi-k3/*.safetensors | wc -l
```

---

## 🔍 Critical Gotchas & Troubleshooting

1. **`errno 24 (Too many open files)` Crash:**
   Each node has 384 vCPUs. Ray creates hundreds of worker threads and file descriptors. You **MUST** pass `--ulimit nofile=1048576:1048576` to `docker run`.
2. **Network Mode:**
   You **MUST** pass `--net=host --ipc=host` so Ray nodes can communicate directly without Docker bridge NAT overhead or port blocking.
3. **Internal IP Resolution:**
   Always use GCP private internal IPs (`10.x.x.x`) for the `--address` argument in Ray workers. Never use external IPs.
4. **Log Inspection:**
   Shard progress bars output to `stderr` (`.err`), while Uvicorn HTTP server logs output to `stdout` (`.out`). To check shard download/loading:
   ```bash
   docker exec ray-head bash -c 'tail -f $(ls -S /tmp/ray/session_latest/logs/worker-*.err | head -n 1)'
   ```
