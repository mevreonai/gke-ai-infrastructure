# Kimi-K3 24-GPU Cluster — End-to-End Replication Runbook

This runbook outlines every command and operational detail required to build, configure, and serve **Moonshot AI Kimi-K3 (1.45 TB MoE)** across **24 NVIDIA RTX Pro 6000 GPUs** on Google Cloud Platform.

---

## ⏱️ Estimated Time per Phase

| Stage | Operation | Expected Time |
| :--- | :--- | :--- |
| **Phase 1** | Node Provisioning & Firewall Configuration | ~3–5 minutes |
| **Phase 2** | Disk Formatting & Mounting (2 TB per node) | ~2 minutes |
| **Phase 3** | Docker Environment & vLLM Container Setup | ~5 minutes |
| **Phase 4** | Weight Ingestion (96 Shards / 1.45 TB per node) | ~20–30 minutes (via high-speed HF transfer) |
| **Phase 5** | Multi-Node Ray Cluster Formation (24 GPUs) | ~1–2 minutes |
| **Phase 6** | vLLM Weight Sharding & GPU Loading | ~25–28 minutes |
| **Phase 7** | Inference Validation & Health Checks | ~1 minute |

---

## 🚀 Phase-by-Phase Instructions

### Phase 1: Provisioning the Compute Engine Instances

Run `01_provision_nodes.sh` on your local workstation with authenticated `gcloud`:

```bash
chmod +x 01_provision_nodes.sh
./01_provision_nodes.sh
```

**What this performs:**
1. Configures VPC firewall rules for ports `6379` (Ray GCS), `8265` (Ray Dashboard), `8000` (vLLM API), and `10000-19999` (Worker ports).
2. Deploys 3x `g4-standard-384` SPOT instances with 8x NVIDIA RTX Pro 6000 GPUs each and 2 TB Hyperdisk Balanced attached.

**Node Topology:**
- `kimi-node-0`: `us-central1-b` (Internal IP: `10.128.0.39`) — Head Node
- `kimi-node-1`: `us-central1-b` (Internal IP: `10.128.0.40`) — Worker Node 1
- `kimi-node-2`: `us-west1-a` (Internal IP: `10.138.0.3`) — Worker Node 2

---

### Phase 2: Disk Preparation & Mount

On each of the 3 nodes (`kimi-node-0`, `kimi-node-1`, `kimi-node-2`), SSH in and format/mount the 2 TB data disk to `/data`:

```bash
# Format disk if not formatted
sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb

# Mount to /data
sudo mkdir -p /data
sudo mount -o discard,defaults /dev/sdb /data
sudo chown -R $USER:$USER /data

# Add to /etc/fstab for persistent mount across reboots
echo "/dev/sdb /data ext4 discard,defaults,nofail 0 2" | sudo tee -a /etc/fstab
```

---

### Phase 3: Docker & vLLM Container Setup

On each node, prepare the Docker image containing Ray and vLLM:

```bash
# Verify NVIDIA GPU runtime in Docker
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi

# Pull or build the vLLM Ray image
docker tag vllm/vllm-openai:latest vllm-ray:latest
```

---

### Phase 4: Download Model Weights (1.45 TB / 96 Shards)

Execute `02_download_weights.sh` on each node to download the complete safetensors repository:

```bash
chmod +x 02_download_weights.sh
./02_download_weights.sh huggingface
```

*(Alternatively, if weights are staged in Google Cloud Storage: `./02_download_weights.sh gcs gs://<YOUR_BUCKET>/moonshotai/Kimi-K3`)*

**Verification:**
```bash
ls -1 /data/models/kimi-k3/*.safetensors | wc -l
# Expected output: 96
```

---

### Phase 5: Form the Distributed Ray Cluster

#### On `kimi-node-0` (Head Node):
```bash
chmod +x 03_setup_ray.sh
./03_setup_ray.sh head
```

#### On `kimi-node-1` (Worker Node 1):
```bash
./03_setup_ray.sh worker 10.128.0.39
```

#### On `kimi-node-2` (Worker Node 2):
```bash
./03_setup_ray.sh worker 10.128.0.39
```

#### Verify 24-GPU Cluster Health:
On `kimi-node-0`:
```bash
./03_setup_ray.sh status
```
*Verify that `Resources` shows `24.0/24.0 GPU` and 3 active nodes.*

---

### Phase 6: Launch Distributed vLLM Server

On `kimi-node-0`, launch the vLLM OpenAI-compatible server using Tensor Parallelism = 8 and Pipeline Parallelism = 3:

```bash
chmod +x 04_launch_vllm.sh
./04_launch_vllm.sh
```

**Monitor Weight Loading:**
```bash
docker exec ray-head bash -c 'tail -f $(ls -S /tmp/ray/session_latest/logs/worker-*.err | head -n 1)'
```

Loading 96 shards across 24 GPUs takes approximately **27–28 minutes**. Once complete, Uvicorn will output:
```
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### Phase 7: Test Inference Endpoint

From your workstation or on `kimi-node-0`, execute the verification script:

```bash
python3 05_test_chat.py --host <KIMI_NODE_0_EXTERNAL_IP> --port 8000
```

**Or test via `curl`:**
```bash
curl -X POST http://<KIMI_NODE_0_EXTERNAL_IP>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-K3",
    "messages": [
      {"role": "system", "content": "You are Kimi-K3 running on 24 GPUs."},
      {"role": "user", "content": "Explain tensor vs pipeline parallelism in 2 sentences."}
    ],
    "max_tokens": 100,
    "temperature": 0.6
  }'
```

---

## 🔧 Troubleshooting Reference

1. **Docker Container Entrypoint Error:**
   - *Symptom:* `Unknown command: ray start`
   - *Fix:* Ensure `docker run` includes `--entrypoint /bin/bash` before image name.

2. **Ray Worker Port Exhaustion:**
   - *Symptom:* `RuntimeError: Failed to bind to worker port`
   - *Fix:* Increase system file descriptor limit with `--ulimit nofile=1048576:1048576` on all Ray containers.

3. **VRAM Allocation Failures:**
   - *Symptom:* `CUDA out of memory during initialization`
   - *Fix:* Set `--gpu-memory-utilization 0.90` (leaving ~10% for PyTorch activation overhead).
