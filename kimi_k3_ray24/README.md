# Kimi-K3 Distributed Inference Infrastructure (24-GPU Cluster)

Production-grade deployment and operations suite for **Moonshot AI Kimi-K3 (1.45 TB MoE)** running across **3 GCP Compute Engine nodes with 24x NVIDIA RTX Pro 6000 GPUs (2.3 TB VRAM)** via Ray and vLLM.

---

## 📂 Repository Organization

The repository is structured into two dedicated operational paths:

```
kimi_k3_ray24/
│
├── quick_demo/                    # 🚀 FAST TRACK: For operating & demonstrating the existing 24-GPU cluster
│   ├── README.md                  # Quick start guide & demo parameters
│   ├── RUNBOOK.md                 # Live demo runbook with time benchmarks & exact outputs
│   ├── cluster.ps1                # 1-click PowerShell controller (start, status, logs, query, stop)
│   ├── cluster.sh                 # 1-click Bash controller for Linux/macOS
│   └── test_chat.py               # Streaming interactive test client & TTFT benchmark
│
└── from_scratch_replication/      # 🏗️ REPLICATION TRACK: For building the entire 24-GPU stack from zero
    ├── README.md                  # Hardware sizing, architecture design, and script map
    ├── REPLICATION_RUNBOOK.md     # Step-by-step reproduction runbook (VMs, storage, Ray, vLLM)
    ├── 01_provision_nodes.sh      # Provisions 3x 8-GPU nodes & attaches 2 TB disks
    ├── 02_download_weights.sh     # Downloads the 96 safetensors shards (1.45 TB) to NVMe/Hyperdisk
    ├── 03_setup_ray.sh            # Forms multi-node 24-GPU Ray cluster across zones
    ├── 04_launch_vllm.sh          # Launches distributed vLLM server (TP=8, PP=3, Port 8000)
    └── 05_test_chat.py            # End-to-end API test and validation script
```

---

## 🎯 Which Path Should You Choose?

### Option A: Running a Live Demo (`quick_demo/`)
If the 3 cluster nodes already exist in your GCP project and you want to power them on, monitor loading, and run live interactive completions:
👉 **[Go to Quick Demo Guide](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/quick_demo/README.md)** or follow **[Live Demo Runbook](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/quick_demo/RUNBOOK.md)**.

```powershell
cd quick_demo
.\cluster.ps1 start
.\cluster.ps1 status
.\cluster.ps1 logs
.\cluster.ps1 query
.\cluster.ps1 stop
```

---

### Option B: Deploying from Scratch (`from_scratch_replication/`)
If you want to provision new VMs, format persistent disks, download the 1.45 TB model weights, configure the Ray cluster, and deploy vLLM:
👉 **[Go to Replication Guide](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/from_scratch_replication/README.md)** or follow **[End-to-End Replication Runbook](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/kimi_k3_ray24/from_scratch_replication/REPLICATION_RUNBOOK.md)**.

```bash
cd from_scratch_replication
./01_provision_nodes.sh
./02_download_weights.sh
./03_setup_ray.sh head
./04_launch_vllm.sh
python3 05_test_chat.py
```

---

## ⚙️ Architecture & Cluster Specifications

| Component | Specification |
| :--- | :--- |
| **Model** | `moonshotai/Kimi-K3` (1.45 TB FP8 Mixture-of-Experts, 96 Shards) |
| **Total Accelerators** | **24x NVIDIA RTX Pro 6000** (96 GB GDDR7 per GPU = **2,304 GB Total VRAM**) |
| **Compute Nodes** | 3x `g4-standard-384` (8 GPUs, 384 vCPUs, 1,228 GB System RAM per node) |
| **Cluster Topology** | `kimi-node-0` (Head, `us-central1-b`), `kimi-node-1` (`us-central1-b`), `kimi-node-2` (`us-west1-a`) |
| **Distributed Engine** | Ray Distributed Runtime + vLLM Distributed Executor |
| **Parallelism Strategy** | **Tensor Parallel (TP) = 8** (Intra-Node NVLink) $\times$ **Pipeline Parallel (PP) = 3** (Inter-Node VPC) |
| **VRAM Footprint** | **63.6 GiB per GPU** (Leaving ~32 GiB per GPU headroom for KV cache and context) |
| **Serving API** | OpenAI-compatible HTTP REST endpoint on Port 8000 (`/v1/chat/completions`) |
