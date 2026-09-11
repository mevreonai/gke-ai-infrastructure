# 🚀 Interactive Testing & Benchmark Guide: TPU & GPU Serving on GKE

This guide walks through deploying, benchmarking, and interacting with frontier LLMs (**Google Gemma-2-27B-IT**, **Qwen2.5**, etc.) on **Google Cloud TPUs** and **NVIDIA GPUs** using GKE, vLLM, and the Gateway API with **automatic cost protection**.

---

## 🎯 Architecture Summary

| Feature | Single-Host TPU (`single_host/`) | Multi-Host TPU (`multi_host/`) | GKE Inference Gateway (`inference_gateway_tpu/` & `_gpu/`) |
| :--- | :--- | :--- | :--- |
| **Hardware** | **TPU v6e Trillium** (`ct6e-standard-4t`, 4 chips) | **TPU v5e Pod Slice** (2 VMs x `ct5lp-hightpu-4t`, `2x4`) | **TPU v6e** or **NVIDIA L4 / A100 GPU** |
| **Serving Framework** | **vLLM** (Kubernetes Deployment) | **Ray Serve + vLLM** (KubeRay Operator) | **vLLM + llm-d Endpoint Picker (EPP)** |
| **Routing / LB** | Standard ClusterIP / Ingress | Ray Serve Head Proxy | **Kubernetes Gateway API + Inference Extension** |
| **Model Streaming** | Cloud Storage FUSE CSI Driver | Cloud Storage FUSE CSI Driver | Cloud Storage FUSE CSI Driver |
| **Cost Protection** | **Automated Multi-Region Cleanup on exit** | **Automated Multi-Region Cleanup on exit** | **Automated Multi-Region Cleanup on exit** |

---

## 🎬 Hands-On Testing Steps

### Option 1: Single-Host TPU v6e Trillium (GKE + vLLM)

#### Step 1: Launch Deployment
```powershell
cd single_host
.\run.ps1
```
> **Tip for unattended testing:** Add `-AutoTestAndTeardown` (e.g. `.\run.ps1 -AutoTestAndTeardown`) to automatically deploy, run live model validation benchmarks, and trigger multi-region cost cleanup upon completion without requiring manual keypresses.

#### Step 2: Live Telemetry
The script streams live progress directly on your terminal:
```text
[LIVE TELEMETRY] Nodes: 2 | Gradio: Running | vLLM Pod: Running | Hardware: TPU Slice Queue: SUCCEEDED
```
Once live, port-forwarding starts and **automatically opens the Gradio chat UI in your browser** at `http://localhost:8080`.

#### Step 3: Test Inference
1. **In Browser:** Chat live with the model at `http://localhost:8080`.
2. **In Terminal:** Press **`T`** to execute an instant benchmark test (prints latency, tokens, and response).
3. **In Terminal:** Press **`L`** to stream live vLLM inference logs.

#### Step 4: Clean Teardown
* Press **`[ENTER]`** (or `Ctrl+C`).
* The teardown trap deletes the GKE cluster and verifies **0 active compute/TPU VMs remain**.

---

### Option 2: Multi-Host TPU Serving (Ray Serve + KubeRay + 8 TPU Chips)

#### Step 1: Launch
```powershell
cd multi_host
.\run.ps1 -SkipBuild
```

#### Step 2: Interactive Testing
* Automatically deploys the RayService manifest spanning worker hosts with tensor parallelism.
* Opens `http://localhost:8080` for live chat.
* Press **`T`** for inference test or **`S`** for Ray Serve distributed cluster status.

#### Step 3: Exit and Clean Up
* Press **`[ENTER]`** to delete all clusters and VMs automatically.

---

### Option 3: GKE Inference Gateway (`llm-d`) on TPU or GPU

#### Launch TPU Edition:
```powershell
cd inference_gateway_tpu
.\run.ps1
```

#### Launch GPU Edition:
```powershell
cd inference_gateway_gpu
.\run.ps1
```

#### Verify Latency & Throughput:
```powershell
python client/test_inference.py
```

---

## 🛑 Universal Emergency Teardown
To force-delete all clusters and verify all VMs are stopped across all regions:

```powershell
# From root or any directory:
.\cleanup.ps1
```
Or in Bash:
```bash
./cleanup.sh
```
