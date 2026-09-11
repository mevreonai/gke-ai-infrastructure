# 🎮 GKE Inference Gateway (llm-d + NVIDIA GPU)

This directory contains the production-grade deployment of the **GKE Inference Gateway powered by `llm-d`** and the **Kubernetes Gateway API Inference Extension**, using **NVIDIA GPUs** (e.g. NVIDIA L4 / A100 / T4) and the official `vllm/vllm-openai:latest` GPU runtime.

---

## 🏛️ Architecture Map

```
                            [ Web Browser / Gradio / cURL ]
                                          │
                                          ▼ (HTTP Port 80)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Google Cloud Application Load Balancer (GKE Gateway API)                   │
│   • Gateway: [01-gateway.yaml] (gke-l7-regional-external-managed)           │
│   • Route: [05-http-route.yaml]                                             │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Intercepts via ext-proc gRPC
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ llm-d Endpoint Picker (EPP) Scheduler: [03-llmd-epp.yaml]                   │
│   • Image: registry.k8s.io/gateway-api-inference-extension/epp:v1.5.0     │
│   • Scheduling Policy: prefix-cache, kv-cache-utilization, queue-scorer     │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Dispatches Request
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ vLLM GPU Model Server: [02-vllm-gpu-modelserver.yaml]                       │
│   • Accelerator: 1x NVIDIA L4 (g2-standard-4) or T4/A100                    │
│   • Driver: Automated GKE GPU driver installation                           │
│   • Container: vllm/vllm-openai:latest                                      │
│   • Target Model: google/gemma-2-9b-it                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 How to Run

### 1. Launch GPU Inference Gateway (1-Click)
```powershell
cd c:\Users\ayu23\OneDrive\Desktop\tpu\inference_gateway_gpu

# If you have a Hugging Face token (required for gated Gemma 2 9B):
.\run.ps1 -HfToken "hf_xxxxxxxxxxxxxxxxxxxx"

# Or if already set in environment:
$env:HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxx"
.\run.ps1
```

### 2. Verify End-to-End Inference
```powershell
python client/test_inference.py
```

### 3. Teardown
```powershell
.\cleanup.ps1
```
