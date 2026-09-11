# GKE Inference Gateway — Distributed TPU & GPU LLM Serving

An enterprise-ready repository for high-throughput, low-latency Large Language Model (LLM) serving on **Google Kubernetes Engine (GKE)** using **Cloud TPUs (v5e / v6e Trillium)** and **NVIDIA GPUs (L4 / A100 / H100)** with **vLLM** and **`llm-d` (Gateway API Inference Extension / Endpoint Picker)**.

---

## 🏛️ Architecture Overview

This repository provides production infrastructure manifests and automated automation scripts for:
1. **GKE Inference Gateway (`gateway.networking.k8s.io`)**: Advanced layer-7 routing, load balancing, and health checking.
2. **`llm-d` Inference Extension Endpoint Picker (EPP)**: Intelligent cache-aware and queue-aware request dispatching using:
   - Prefix cache affinity (`prefix-cache-scorer`)
   - KV cache utilization scoring (`kv-cache-utilization-scorer`)
   - Queue depth balancing (`queue-scorer`)
3. **Hardware-Optimized Model Serving**:
   - **Google Cloud TPU (v6e Trillium & v5e)**: Optimized with XLA and GCS FUSE CSI driver for model weights loading.
   - **NVIDIA GPU (L4 / A100)**: Optimized with TensorRT / FlashAttention / vLLM CUDA kernels.
4. **Interactive UI & Validation**:
   - **Gradio Web Client**: Interactive chat testing connected directly to the GKE Inference Gateway.
   - **Automated Latency Benchmark**: TTFT (Time To First Token) and TPOT (Time Per Output Token) validation scripts.

---

## 📁 Repository Structure

```
├── inference_gateway_tpu/      # GKE Inference Gateway deployment on TPU v6e (Trillium)
│   ├── manifests/              # K8s manifests (CRDs, Gateway, vLLM TPU, EPP, HTTPRoute)
│   ├── client/                 # Python latency & token benchmarking scripts
│   ├── run.ps1                 # Automated 1-click deployment script
│   └── cleanup.ps1             # Cost-protection teardown script
│
├── inference_gateway_gpu/      # GKE Inference Gateway deployment on NVIDIA GPUs (L4 / A100)
│   ├── manifests/              # K8s manifests (CRDs, Gateway, vLLM GPU, EPP, HTTPRoute)
│   ├── client/                 # Benchmark & testing client
│   ├── run.ps1                 # Automated 1-click deployment script
│   └── cleanup.ps1             # Cost-protection teardown script
│
├── single_host/                # Standalone single-host TPU deployment (GKE & vLLM)
│   ├── manifests/              # Manifests for single TPU slice
│   ├── run.ps1                 # Deployment automation
│   └── cleanup.ps1             # Teardown automation
│
├── multi_host/                 # Multi-host TPU pod slice deployment (e.g., v5e-16, v6e-16)
│   ├── run.ps1                 # Deployment automation
│   └── cleanup.ps1             # Teardown automation
│
├── client/                     # Global client scripts and test harnesses
│   └── test_inference.py       # End-to-end OpenAI-compatible inference validator
│
├── transfer_deepseek.sh        # High-throughput model synchronization script (GCS bucket)
├── download_and_sync.py        # Hugging Face to GCS parallel download utility
└── REPLICATION_RUNBOOK.md      # Detailed engineering runbook & operations guide
```

---

## 🚀 Quickstart

### Prerequisites
- Google Cloud SDK (`gcloud`) authenticated (`gcloud auth login`)
- Kubernetes CLI (`kubectl`)
- Helm 3.x
- Active Google Cloud Project with TPU / GPU quota

### 1. Deploying on Google Cloud TPU (v6e)
```powershell
cd inference_gateway_tpu
.\run.ps1
```
*Creates the GKE cluster, enables GCS FUSE, installs Gateway API CRDs, deploys the vLLM TPU model server, starts the `llm-d` EPP, and opens the Gradio web UI.*

### 2. Deploying on NVIDIA GPU (L4 / A100)
```powershell
cd inference_gateway_gpu
.\run.ps1
```

### 3. Testing End-to-End Latency & Throughput
```powershell
python client\test_inference.py
```

### 4. Teardown & Cost Protection
```powershell
.\cleanup.ps1
```

---

## 🔒 Security & Best Practices
- Never commit `.env` files or service account keys.
- Model weights are streamed dynamically via GCS FUSE ephemeral caching or loaded from private Google Cloud Storage buckets (`gs://...`).
- Workload Identity Federation is configured for zero-secret cloud credential access.
