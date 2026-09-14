# Kimi-K3 24-GPU Cluster — From-Scratch Replication Guide

This directory contains modular infrastructure scripts and step-by-step documentation for replicating the distributed deployment of **Moonshot AI Kimi-K3 (1.45 TB MoE)** across **3 GCP Compute Engine nodes (24x NVIDIA RTX Pro 6000 GPUs / 2.3 TB VRAM)** from scratch.

---

## 🏗️ Hardware & Cluster Architecture

| Parameter | Specification | Purpose |
| :--- | :--- | :--- |
| **Model** | `moonshotai/Kimi-K3` (1.45 TB, 96 Shards) | FP8-quantized Mixture of Experts (MoE) |
| **Total GPUs** | 24x NVIDIA RTX Pro 6000 (96 GB GDDR7 each) | **2.30 TB aggregate GPU VRAM** |
| **Node Topology** | 3x `g4-standard-384` (8 GPUs / 384 vCPUs / 1.2 TB RAM per node) | 24 GPUs distributed across 3 instances |
| **Zone Allocation** | 2 Nodes in `us-central1-b`, 1 Node in `us-west1-a` | Maximizes regional GPU spot quota |
| **Parallelism** | **Tensor Parallel = 8 (TP=8)** $\times$ **Pipeline Parallel = 3 (PP=3)** | TP within each 8-GPU node; PP across the 3 nodes |
| **VRAM Consumption** | **~63.6 GiB per GPU** (1.52 TB total model footprint in VRAM) | Leaves ~32 GiB per GPU for KV cache & activations |

---

## 📁 Replication Pipeline Scripts

| Script | Purpose | Where to Run |
| :--- | :--- | :--- |
| **`01_provision_nodes.sh`** | Provisions 3x 8-GPU VMs and creates 2 TB persistent disks | Local Machine / Cloud Shell |
| **`02_download_weights.sh`** | Downloads the 96 safetensors shards (1.45 TB) to `/data` | Run on all 3 nodes |
| **`03_setup_ray.sh`** | Launches Ray head on Node 0 and joins Nodes 1 & 2 | Node 0 (`head`), Nodes 1 & 2 (`worker`) |
| **`04_launch_vllm.sh`** | Initializes distributed vLLM server (`TP=8`, `PP=3`, port 8000) | Run on Node 0 |
| **`05_test_chat.py`** | Sends streaming chat completions and evaluates TTFT | Local Machine or Node 0 |

---

## ⚡ Quick Replication Flow

```bash
# 1. Provision 3 multi-GPU nodes in GCP
./01_provision_nodes.sh

# 2. Download weights on each node (or sync from GCS)
./02_download_weights.sh huggingface

# 3. Form the Ray Cluster across the 3 nodes
# On Node 0:
./03_setup_ray.sh head

# On Node 1 & Node 2:
./03_setup_ray.sh worker <NODE0_INTERNAL_IP>

# 4. Launch distributed vLLM server on Node 0
./04_launch_vllm.sh

# 5. Verify live generation
python3 05_test_chat.py --host <NODE0_EXTERNAL_IP>
```

For the complete in-depth walkthrough, troubleshooting steps, and exact commands, refer to [`REPLICATION_RUNBOOK.md`](./REPLICATION_RUNBOOK.md).
