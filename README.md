# GKE Inference Gateway — Distributed TPU & GPU LLM Serving

An enterprise-ready repository for high-throughput, low-latency Large Language Model (LLM) serving on **Google Kubernetes Engine (GKE)** using **Cloud TPUs (v5e / v6e Trillium)** and **NVIDIA GPUs (L4 / A100 / H100)** with **vLLM** and **`llm-d` (Gateway API Inference Extension / Endpoint Picker)**.

---

## 📊 V8-FULL Characterization Dashboard (Native VPC & RTX 6000 Ada)

The repository includes the production **V8-FULL vLLM Empirical Characterization Dashboard** ([`MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///MASTER_CHARACTERIZATION_DASHBOARD.html)), built directly from the UI V4 specification with 100% 1:1 structural fidelity, 81 analysis cards, 26 interactive Chart.js graphs, and 126 verified evidence rows.

- **Dashboard File:** [`MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///MASTER_CHARACTERIZATION_DASHBOARD.html) (Stand-alone, interactive HTML/JS)
- **Empirical Dataset:** [`v8_native_dashboard_data.json`](file:///v8_native_dashboard_data.json) (119 completed empirical runs, 7 safety-guarded runs, paired node socket telemetry, hardware primitives)
- **Model:** `Kimi-Linear-48B-A3B` (Linear RNN / MLA architecture)
- **Infrastructure:** Dual-Node GCP Compute Instances (`g4-standard-96`), 16x NVIDIA RTX 6000 Ada Generation (96 GB VRAM each, 1,536 GB total cluster VRAM), PCIe Gen4 × 16, intra-node NVLink bridges (25.95 GB/s bus bandwidth).
- **Fabric Provenance:** Google Cloud Native VPC (`GCP_NATIVE`) over `ens4` with MTU 8896 (Jumbo frames). Forward throughput: `173.58 Gbps`, Reverse: `173.42 Gbps`, Round-Trip Time: `0.05 ms`, 0 packet drops.

### 🏆 Key Deployment Decisions & Empirical Findings

| Workload Regime | Primary SLO | Recommended Topology | Empirical Observation | Rationale & Architectural Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Short-Context Interactive (8K)** | Lowest TPOT (&lt; 10ms) | **`TP4 / PP1`** | **7.84 ms TPOT** (vs 8.41 ms on TP8) | 4-GPU barrier synchronization latency is 7.2% faster than 8-GPU all-reduce. Lower communication overhead dominates decode. |
| **Short-Context Throughput (8K c=8)** | Batch Output TPS | **`TP8 / PP1`** | **479.5 tok/s** (vs 438.2 tok/s on TP4) | 8 memory channels and doubled aggregate FLOPS amortize collective sync on saturated batch decode. |
| **Single-Node Long Prefill (512K)** | Lowest TTFT | **`TP8 / PP1`** | **27.8s TTFT** (vs 35.8s on TP4) | 22% prefill speedup single-node. Large GEMM compute dominates over NVLink collective sync. |
| **2-Node Extreme Context (1M Tokens)** | 1M Fit, Finish, Latency | **`TP4 / PP4`** | **28.56s TTFT (35,014 tok/s)** · 88.7 GB Peak VRAM | **Decisive Winner:** Confines high-frequency tensor all-reduces within NVLink nodes; cross-node communication is strictly P2P activations. Leaves 7.24 GB safety headroom with 0 OOMs. |
| **1M Concurrency Admission** | Queue Wait &amp; Preemption | **`TP4 / PP4` (c ≤ 2)** | **0 preemptions** · queue mean 0.0s at c=1 &amp; c=2 | Concurrency knee occurs at c=4 where compute saturation causes 1.45s queue buildup. Service rate: 1.82 tok/s per stream. |
| **Cross-Node Anti-Pattern** | Latency Failure | **`TP16 / PP1` (AVOID)** | **68.20s TTFT (2.4x slowdown)** | Forcing tensor parallel all-reduces across TCP VPC creates massive barrier synchronization stalls (42.8% GPU idle time). |

### 📑 7 Dashboard View Tabs
1. **Executive (`#executive`)**: Executive KPI banners, Deployment Decision Map, Configuration Guidance Matrix, and authorative source hierarchy.
2. **Single-Node Scale-Up (`#scaleup`)**: TTFT vs Context (8K–1M), TPOT vs Context, Output Throughput curves, concurrency sweeps, and intra-node NVLink audit.
3. **Scale-Out (`#scaleout`)**: Native VPC verification (173.58 Gbps iperf, 0.05ms RTT, MTU 8896), Topology comparison (`TP4/PP2`, `TP8/PP2`, `TP4/PP4`, `TP16/PP1`), and context scaling curves.
4. **Long Context & 1M (`#long`)**: 1M fit/finish/usability ledger, concurrency scaling (`c1`, `c2`, `c4`), scheduler sensitivity (`chunk_size=4096` vs `8192`), and KV dtype contracts.
5. **Scheduler & KV (`#sched`)**: Peak KV cache utilization (1.25% at 8K to 88.7 GB at 1M), running vs waiting sequences, queue mean latency, and zero-preemption verification.
6. **Profiler (`#profiler`)**: Nsight Systems wall-time breakdown, CUDA kernel categories (`linear_kda_forward`, `attn_gemm`), and native NCCL vs idle stalls.
7. **Evidence & Audit Backbone (`#evidence`)**: 126 interactive rows filterable by scope, topology, context, and status (`119 COMPLETED`, `7 GUARDED NOT_RUN`). Zero synthetic figures.

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
├── disaggregated_tpu_llmd/     # Disaggregated TPU Serving (Prefill & Decode decoupled via llm-d)
│   ├── manifests/              # Manifests (Prefill kv_producer, Decode kv_consumer, llm-d proxy)
│   ├── client/                 # Disaggregated TTFT and throughput benchmark
│   ├── run.ps1                 # Automated 1-click deployment script
│   └── cleanup.ps1             # Cost-protection teardown script
│
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
