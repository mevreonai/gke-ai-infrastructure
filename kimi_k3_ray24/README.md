# Moonshot AI Kimi-K3: 24-GPU Distributed Cluster (Ray + vLLM)

This directory contains the production-grade automation suite, distributed architecture specifications, and live demo controllers for **Moonshot AI Kimi-K3** deployed across **24 NVIDIA RTX 6000 Pro GPUs (2.3 TB VRAM)** on Google Cloud Platform.

---

## 🏗️ Architecture & Topology

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 VPC Internal Network                   │
                  │             (10.128.0.0/9 / 10.138.0.0/20)             │
                  └───────┬────────────────────────┬───────────────┬───────┘
                          │                        │               │
            Pipeline Stage 0 (PP=0)  Pipeline Stage 1 (PP=1) Pipeline Stage 2 (PP=2)
                          │                        │               │
        ┌─────────────────▼─────────┐    ┌─────────▼────────┐    ┌─▼────────────────┐
        │       kimi-node-0         │    │   kimi-node-1    │    │   kimi-node-2    │
        │      (Ray Head Node)      │    │  (Ray Worker 1)  │    │  (Ray Worker 2)  │
        ├───────────────────────────┤    ├──────────────────┤    ├──────────────────┤
        │ Zone: us-central1-b       │    │ Zone: us-cent-1b │    │ Zone: us-west1-a │
        │ Internal IP: 10.128.0.39  │    │ IP: 10.128.0.40  │    │ IP: 10.138.0.3   │
        │ 8x RTX 6000 (96GB each)   │    │ 8x RTX 6000 (96G)│    │ 8x RTX 6000 (96G)│
        │ Local NVMe: 2,000 GB      │    │ Local NVMe: 2TB  │    │ Local NVMe: 2TB  │
        │ vLLM API Server: :8000    │    │                  │    │                  │
        └───────────────────────────┘    └──────────────────┘    └──────────────────┘
```

### Cluster Specifications

| Parameter | Specification | Technical Details |
| :--- | :--- | :--- |
| **Model** | `moonshotai/Kimi-K3` | 1,453 GB weights, 96 safetensor shards, MoE architecture |
| **Compute Topology** | 3× `g4-standard-384` | 8× NVIDIA RTX 6000 Pro (96GB VRAM) per node = **24 GPUs total (2.3 TB VRAM)** |
| **vCPU & Host RAM** | 1,152 vCPUs, 3.6 TB RAM | 384 vCPUs and 1.2 TB RAM per physical node |
| **Tensor Parallelism (TP)** | **`8`** | Intra-node tensor sharding across 8 GPUs on local PCIe/NVLink bus |
| **Pipeline Parallelism (PP)** | **`3`** | Inter-node pipeline stages partitioned across the 3 VMs |
| **Storage Infrastructure** | **6,000 GB NVMe** | 2,000 GB local Hyperdisk Balanced per node (`/data`) @ 2.7 GB/s read |
| **Inference Endpoint** | `http://<HEAD_EXTERNAL_IP>:8000/v1` | OpenAI-compatible HTTP API server exposed on Head node |

---

## 🧭 Choose Your Workflow

Depending on your objective, follow either **Path A** or **Path B**:

* [🟢 **Path A: One-Click Live Demo (Using Existing Pre-Configured Cluster)**](#-path-a-one-click-live-demo) — Best for running live inference demonstrations, checking health, and streaming responses with pre-installed background services.
* [🛠️ **Path B: Build & Replicate from Scratch**](#️-path-b-build--replicate-from-scratch) — Best for provisioning a brand-new 24-GPU cluster on any GCP project, downloading weights, and setting up Ray + vLLM from zero.

---

## 🟢 Path A: One-Click Live Demo

On pre-configured environments, background `systemd` services (`kimi-vllm.service` on Node 0, `kimi-ray.service` on Nodes 1 & 2) launch the 24-GPU Ray cluster and vLLM automatically whenever the VMs power on.

Use the unified workstation lifecycle scripts:
* **Windows PowerShell:** `.\cluster.ps1 <command>`
* **Linux / macOS / Cloud Shell:** `./cluster.sh <command>`

### 1. Power On All 3 Nodes
```powershell
.\cluster.ps1 start
```
*Powers on all 3 instances with automated retry logic to bypass transient zone capacity locks. Ray and vLLM launch automatically in the background upon boot.*

### 2. Inspect Cluster Health
```powershell
.\cluster.ps1 status
```
*Verifies all 3 VMs are `RUNNING`, confirms all `24.0/24.0 GPUs` are registered in Ray, and checks if port 8000 is open.*

### 3. Stream Shard Loading Logs (First Boot)
```powershell
.\cluster.ps1 logs
```
*Streams the live shard ingestion progress bar directly from GPU workers (`XX/96 Completed`). Press `Ctrl+C` to cleanly detach from logs at any time.*

### 4. Execute a Live Inference Query
```powershell
.\cluster.ps1 query
```
*Sends a sample prompt to Kimi-K3 via port 8000 and prints the formatted response:*
```json
{
  "id": "chatcmpl-8c78d39495e190b3",
  "object": "chat.completion",
  "model": "moonshotai/Kimi-K3",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Quantum computing leverages superposition and entanglement to perform calculations exponentially faster than classical bits. For a 1.45 TB Mixture-of-Experts model, 24 GPUs provide the aggregate 2.3 TB VRAM and memory bandwidth required to distribute model parameters via hybrid tensor and pipeline parallelism."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 142,
    "completion_tokens": 120,
    "total_tokens": 262
  }
}
```

### 5. Interactive Streaming Chat (Python Benchmark)
```bash
python 05_test_chat.py --host <HEAD_EXTERNAL_IP> --port 8000
```
*Streams tokens in real time to your terminal and calculates Time-to-First-Token (TTFT) and throughput metrics.*

### 6. Power Off to Stop Billing
```powershell
.\cluster.ps1 stop
```
*Shuts down all 3 instances. GPU compute billing halts immediately ($0.00/hr) while persistent model disks remain preserved for your next demo.*

---

## 🛠️ Path B: Build & Replicate from Scratch

If you are setting up this architecture on a new GCP project or bare-metal environment, follow these modular scripts:

### Step 1: Provision Multi-Node Infrastructure
```bash
chmod +x 01_provision_nodes.sh
./01_provision_nodes.sh
```
*Creates firewall rules for Ray (6379, 8265, 10000–19999) and vLLM (8000), and provisions 3x `g4-standard-384` SPOT instances with 8x NVIDIA RTX 6000 Pro GPUs and 2 TB NVMe disks across `us-central1-b` and `us-west1-a`.*

### Step 2: Download Model Weights (1.45 TB, 96 Shards)
Run on all 3 nodes (via SSH):
```bash
chmod +x 02_download_weights.sh

# Option 1: Direct Hugging Face high-speed download via HF Transfer
./02_download_weights.sh huggingface

# Option 2: Fast sync from internal GCS bucket
./02_download_weights.sh gcs gs://your-bucket-name/moonshotai/Kimi-K3
```

### Step 3: Form the 24-GPU Distributed Ray Cluster
#### On `kimi-node-0` (Ray Head):
```bash
chmod +x 03_setup_ray.sh
./03_setup_ray.sh head
```
#### On `kimi-node-1` and `kimi-node-2` (Ray Workers):
```bash
chmod +x 03_setup_ray.sh
./03_setup_ray.sh worker 10.128.0.39
```
#### Verify Cluster Topology:
```bash
./03_setup_ray.sh status
```

### Step 4: Launch Distributed vLLM Serving
Run on `kimi-node-0`:
```bash
chmod +x 04_launch_vllm.sh
./04_launch_vllm.sh
```

### Step 5: Test and Benchmark
```bash
python3 05_test_chat.py --host localhost --port 8000
```

---

## 📁 File Manifest

| File | Purpose |
| :--- | :--- |
| **[`cluster.ps1`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/cluster.ps1)** | Master Windows PowerShell lifecycle script (`start`, `status`, `logs`, `query`, `stop`). |
| **[`cluster.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/cluster.sh)** | Master Linux/macOS/Cloud Shell lifecycle script (`start`, `status`, `logs`, `query`, `stop`). |
| **[`RUNBOOK.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/RUNBOOK.md)** | Comprehensive step-by-step reproduction runbook with manual copy-paste commands. |
| **[`01_provision_nodes.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/01_provision_nodes.sh)** | Infrastructure automation: VPC firewall, 3x VMs, and NVMe disk attachments. |
| **[`02_download_weights.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/02_download_weights.sh)** | High-speed parallel weight downloader supporting Hugging Face Hub and GCS. |
| **[`03_setup_ray.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/03_setup_ray.sh)** | Containerized Ray Head and Worker orchestrator with explicit ulimits and entrypoint. |
| **[`04_launch_vllm.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/04_launch_vllm.sh)** | Distributed vLLM serving launcher (`TP=8, PP=3`). |
| **[`05_test_chat.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/05_test_chat.py)** | Streaming chat completion test client with latency & TTFT benchmarking. |

---

## 🔬 Distributed Parallelism Breakdown

### Why Hybrid TP=8 × PP=3?
Cross-node Tensor Parallelism over standard cloud networking incurs severe latency due to frequent All-Reduce synchronizations on every transformer layer. 

To maximize throughput:
1. **Intra-Node Tensor Parallelism (`TP=8`):** Restricts the latency-sensitive matrix multiplications to the 8 GPUs on the same physical motherboard via local PCIe/NVLink buses.
2. **Inter-Node Pipeline Parallelism (`PP=3`):** Divides the 1.45 TB model into 3 sequential pipeline stages:
   - **Node 0 (GPUs 0–7):** First 1/3 of layers (Embedding & initial attention layers)
   - **Node 1 (GPUs 8–15):** Middle 1/3 of layers (Deep representation extraction)
   - **Node 2 (GPUs 16–23):** Final 1/3 of layers (Output logit projection & token sampling)
3. **VPC Activation Passing:** Only small activation tensors pass between physical machines over the internal VPC network (`10.128.0.0/9` to `10.138.0.0/20`), preserving low latency and high generation throughput.

---

## 🛡️ Critical Operational Rules & Gotchas

1. **File Descriptor Limits:**
   Because each node contains 384 vCPUs (1,152 vCPUs cluster total), Ray spawns hundreds of internal socket threads. Containers must be launched with `--ulimit nofile=1048576:1048576` to prevent `errno 24 (Too many open files)` failures.
2. **Network Mode:**
   Containers must use `--net=host --ipc=host` for zero-copy shared memory communication and native private VPC IP routing.
3. **Explicit Container Entrypoint:**
   Docker run commands must explicitly specify `--entrypoint /bin/bash` when invoking containerized Ray workers to avoid default image entrypoint overrides.
4. **VRAM Memory Headroom:**
   The model weights occupy ~63.6 GiB per GPU across all 24 GPUs. This leaves **~34.4 GiB free VRAM per GPU** (>820 GB aggregate cluster memory) dedicated to KV cache for massive context windows.
