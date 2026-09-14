# Moonshot AI Kimi-K3: 24-GPU Distributed Cluster (Ray + vLLM)

This directory provides the complete, production-grade automation suite, distributed architecture specifications, and live demo controllers for **Moonshot AI Kimi-K3** deployed across **24 NVIDIA RTX 6000 Pro GPUs (2.3 TB VRAM)** on Google Cloud Platform.

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

| Parameter | Specification | Engineering Details |
| :--- | :--- | :--- |
| **Model** | `moonshotai/Kimi-K3` | 1,453 GB weights, 96 safetensor shards, MoE architecture |
| **Compute Topology** | 3× `g4-standard-384` | 8× NVIDIA RTX 6000 Pro (96GB VRAM) per node = **24 GPUs total (2.3 TB VRAM)** |
| **vCPU & Host RAM** | 1,152 vCPUs, 3.6 TB RAM | 384 vCPUs and 1.2 TB RAM per physical node |
| **Tensor Parallelism (TP)** | **`8`** | Intra-node tensor sharding across 8 GPUs on local PCIe/NVLink bus |
| **Pipeline Parallelism (PP)** | **`3`** | Inter-node pipeline stages partitioned across the 3 VMs |
| **Storage Infrastructure** | **6,000 GB NVMe** | 2,000 GB local Hyperdisk Balanced per node (`/data`) @ 2.7 GB/s read |
| **API Endpoint** | `http://<HEAD_EXTERNAL_IP>:8000/v1` | OpenAI-compatible HTTP API server exposed on Head node |

---

## ⚡ Live Demo Walkthrough (1-Click Automation)

All 3 cluster instances are configured with background `systemd` services (`kimi-vllm.service` on the head node, `kimi-ray.service` on the worker nodes). When the instances power on, the Ray 24-GPU cluster forms and the vLLM distributed inference engine launches automatically.

Use the unified controller from your workstation:
* **Windows PowerShell:** `.\cluster.ps1 <command>` or `.\demo_cluster.ps1 <command>`
* **Linux / macOS / Cloud Shell:** `./cluster.sh <command>`

### 1. Power On the Cluster
```powershell
.\cluster.ps1 start
```
* **What it does:** Powers on all 3 VMs with automated retry logic to bypass transient cloud capacity locks. The Ray head and workers auto-connect, and vLLM begins loading the 96 safetensor shards into GPU memory upon boot.

### 2. Check Cluster Health & Readiness
```powershell
.\cluster.ps1 status
```
* **Expected Output:**
  - 3 instances reporting `RUNNING` with their respective internal and external IP addresses.
  - Ray status showing `24.0/24.0 GPU` active.
  - vLLM status indicating whether weights are loading or the endpoint is ready.

### 3. Monitor Real-Time Loading Progress
```powershell
.\cluster.ps1 logs
```
* **Expected Output:** Live streaming shard loading bar directly from the GPU workers:
  ```text
  Loading safetensors checkpoint shards:  48%|████████      | 46/96 [07:15<07:54, 9.48s/it]
  ```
  *(Press `Ctrl+C` to cleanly detach from log streaming at any time).*

### 4. Execute a Live Inference Query
```powershell
.\cluster.ps1 query
```
* **What it does:** Sends a test completion request through port 8000 and prints the formatted JSON response:
  ```json
  {
    "id": "chat-xxxxxxxxxxxx",
    "object": "chat.completion",
    "model": "moonshotai/Kimi-K3",
    "choices": [
      {
        "message": {
          "role": "assistant",
          "content": "Quantum computing harnesses superposition and entanglement to process complex computations exponentially faster than classical machines. For 1.45 TB Mixture-of-Experts (MoE) models, 24 GPUs provide the aggregate 2.3 TB VRAM and memory bandwidth required to distribute model parameters via hybrid tensor and pipeline parallelism."
        }
      }
    ]
  }
  ```

### 5. Interactive Streaming Chat (Python Benchmark)
```bash
python 05_test_chat.py --host <HEAD_EXTERNAL_IP> --port 8000
```
* **What it does:** Streams tokens in real time, displays output as it generates, and calculates Time-to-First-Token (TTFT) and throughput metrics.

### 6. Power Off to Stop Billing
```powershell
.\cluster.ps1 stop
```
* **What it does:** Shuts down all 3 instances cleanly. GPU compute billing drops to $0.00 while the 2,000 GB NVMe model disks remain preserved for the next session.

---

## 📁 Repository Structure

```
kimi_k3_ray24/
├── README.md               # Complete architecture documentation & demo guide
├── RUNBOOK.md              # Detailed step-by-step reproduction runbook
├── cluster.ps1             # Master Windows PowerShell lifecycle controller
├── cluster.sh              # Master Linux/macOS lifecycle controller
├── 01_provision_nodes.sh   # Provisions 3x g4-standard-384 nodes across zones
├── 02_download_weights.sh  # Parallel downloads Kimi-K3 96 shards (1.45 TB)
├── 03_setup_ray.sh         # Starts containerized Ray Head and Worker daemons
├── 04_launch_vllm.sh       # Launches distributed vLLM server (TP=8, PP=3)
└── 05_test_chat.py         # Python streaming chat & latency benchmark client
```

---

## 🔬 Distributed Parallelism Breakdown

### Why Hybrid TP=8 × PP=3?

Cross-node Tensor Parallelism over standard cloud networking incurs severe latency due to frequent all-reduce communications on every attention layer. 

To maximize generation speed and throughput:
1. **Intra-Node Tensor Parallelism (`TP=8`):** Restricts the latency-sensitive matrix multiplications to the 8 GPUs residing on the same physical motherboard via local PCIe/NVLink buses.
2. **Inter-Node Pipeline Parallelism (`PP=3`):** Divides the 1.45 TB model into 3 sequential pipeline stages:
   - **Node 0 (GPUs 0–7):** Stage 0 — Prompt token embedding and first 1/3 of transformer layers.
   - **Node 1 (GPUs 8–15):** Stage 1 — Intermediate 1/3 of transformer layers.
   - **Node 2 (GPUs 16–23):** Stage 2 — Final 1/3 of layers, output norm, and vocabulary projection.
3. **VPC Activation Passing:** Only small activation tensors pass between nodes over internal GCP VPC networking (`10.128.0.0/9`), preserving low latency and high token throughput.

---

## 🛡️ Critical Operational Rules

1. **File Descriptor Limits:**
   With 384 vCPUs per node, Ray spawns hundreds of internal socket threads. Docker containers must be started with `--ulimit nofile=1048576:1048576` to avoid `errno 24 (Too many open files)` failures.
2. **Network Mode:**
   Containers must use `--net=host --ipc=host` for zero-copy shared memory communication and native private VPC IP routing.
3. **Independent Storage Volumes:**
   High-performance NVMe disks (Hyperdisk Balanced) cannot be attached in Read-Write mode to multiple VMs simultaneously. Each node maintains its own independent 2,000 GB local NVMe volume mounted at `/data` to sustain 2.7 GB/s local weight read throughput.
4. **VRAM Headroom:**
   The model weights consume ~63.6 GiB per GPU across the 24 GPUs. This leaves ~34.4 GiB of free VRAM per GPU (>820 GB aggregate cluster memory) dedicated to KV cache for massive context lengths.
