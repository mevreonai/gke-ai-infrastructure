# 🌐 GKE Inference Gateway with llm-d & Custom TPU v6e Trillium Serving

This directory contains the production-ready implementation of **GKE Inference Gateway powered by `llm-d`** and the **Kubernetes Gateway API Inference Extension**, intelligently routing LLM requests to a **vLLM model server running on Google Cloud TPU v6e (Trillium)**.

---

## 🏛️ Architecture

```
                        [ Client / Web Browser / cURL ]
                                      │
                                      ▼ (HTTP Port 80)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Google Cloud Application Load Balancer (GKE Gateway Controller)            │
│   • Gateway Class: gke-l7-regional-external-managed                         │
│   • Subnet: Regional Managed Proxy-Only Subnet                              │
│   • HTTPRoute: Matches / and forwards to InferencePool                      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                         Routing Extension Intercept
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ llm-d Endpoint Picker (EPP) Scheduler                                       │
│   • Image: ghcr.io/llm-d/llm-d-inference-scheduler:v0.8.0                  │
│   • Evaluates:                                                              │
│       - prefix-cache-scorer (weight: 3) -> routes to warm KV caches         │
│       - kv-cache-utilization-scorer (weight: 2) -> avoids OOM thrashing     │
│       - queue-scorer (weight: 2) -> balances queue depth                    │
│       - no-hit-lru-scorer (weight: 2) -> assigns fresh requests evenly      │
│   • Protocol: Envoy ext-proc gRPC on port 9090                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Dispatches Request
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ InferencePool (inference.networking.k8s.io/v1)                              │
│   └── vLLM TPU v6e Model Server (ct6e-standard-4t, 4 Chips)                 │
│         • Accelerators: 4x TPU v6e Trillium (2x2 mesh topology)             │
│         • Model: Google Gemma-2-27B-IT (12 Safetensors shards, 50.7 GB)     │
│         • Cache: GCS FUSE CSI parallel prefetch buffer                      │
│         • Target Port: 8000 (OpenAI-compatible HTTP endpoint)               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
inference_gateway/
├── manifests/
│   ├── 00-crds.yaml                 # Gateway API Inference Extension CRDs
│   ├── 01-gateway.yaml              # Regional External Managed Gateway (Port 80)
│   ├── 02-vllm-tpu-modelserver.yaml # vLLM on TPU v6e Trillium (Gemma-2-27B-IT)
│   ├── 03-llmd-epp.yaml             # llm-d Endpoint Picker Deployment & Config
│   ├── 04-inference-pool.yaml       # InferencePool resource linking vLLM & EPP
│   ├── 05-http-route.yaml           # HTTPRoute mapping Gateway to InferencePool
│   ├── 06-inference-objective.yaml  # Serving priority custom resource
│   └── 07-gradio.yaml               # Interactive Chat Web UI
├── client/
│   └── test_inference.py            # Automated CLI test script for Gateway IP
├── run.ps1                          # 1-Click deployment and telemetry script
├── cleanup.ps1                      # 1-Click teardown and cost-protection script
└── README.md                        # Architectural and operation documentation
```

---

## 🚀 Quickstart

### 1. Launch Everything (1-Click)
Open PowerShell in this folder and run:
```powershell
cd c:\Users\ayu23\OneDrive\Desktop\tpu\inference_gateway
.\run.ps1
```

### 🧪 What happens automatically:
1. Validates `gcloud` credentials and creates the required Regional Proxy-Only subnet.
2. Provisions GKE cluster `inference-gateway-cluster` with `HttpLoadBalancing` & `GcsFuseCsiDriver`.
3. Carves out the TPU v6e Trillium slice (`ct6e-standard-4t`, 4 chips).
4. Installs the Gateway API Inference Extension CRDs (`InferencePool`, `InferenceObjective`).
5. Launches the `llm-d` Endpoint Picker (EPP) scheduler pod.
6. Deploys vLLM on TPU v6e with Gemma-2-27B-IT model weights streamed from Cloud Storage.
7. Allocates the external Gateway IP address and opens your browser to `http://localhost:8080`.

---

### 2. Verify with Benchmark Client
While `run.ps1` is running, open a terminal or press `T`:
```powershell
python client/test_inference.py
```

Sample output:
```
[TARGET] External Gateway IP: 34.141.x.x (Port 80)
[1/2] Testing /v1/models... Status: 200 OK
[2/2] Sending prompt via GKE Inference Gateway...

=================== MODEL RESPONSE ===================
• Prefix-Cache Routing: llm-d EPP inspects prompt tokens and dispatches to TPU nodes with primed KV caches.
• Hardware Acceleration: 4x TPU v6e Trillium chips deliver high-throughput matrix execution.
• Native Gateway Integration: Built into Google Cloud's Regional Application Load Balancer.
=======================================================
Latency:    2.85 seconds
Throughput: 54.2 tokens/sec
```

---

### 3. Stop & Teardown
Press **`ENTER`** in the `run.ps1` window, or run:
```powershell
.\cleanup.ps1
```
*(Deletes the cluster, load balancers, and TPU slices to ensure zero lingering cost).*
