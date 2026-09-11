# 🚀 Executive Demo & Replication Guide: GKE Inference Gateway (TPU vs GPU)

This guide provides the exact replication commands and links to present both the **Cloud TPU v6e Trillium** and **NVIDIA GPU** editions of the **GKE Inference Gateway (llm-d)** to your boss with zero hiccups.

---

## 🟢 Part 1: Live Demo Happening RIGHT NOW (Zero Setup Needed)

Your TPU deployment is already active and serving in Google Cloud right now. You can open and show this immediately:

| Demo Feature | Live Endpoint / Command | What to Explain to Your Boss |
| :--- | :--- | :--- |
| **Interactive Chat Web UI** | 👉 **[http://34.90.83.99:8080/](http://34.90.83.99:8080/)** | *"This is Google's Gemma-2-27B frontier model running on 4 Cloud TPU v6e Trillium chips with vLLM OpenXLA. Notice the instant sub-second response streaming."* |
| **GKE Inference Gateway IP** | `http://35.214.179.58:80` | *"This is Google Cloud's Regional Application Load Balancer controlled by the Kubernetes Gateway API."* |
| **List Models API** | `curl.exe http://35.214.179.58/v1/models` | *"Standard OpenAI-compatible API showing the loaded model checkpoint streamed via Cloud Storage FUSE."* |

---

## 🛠️ Part 2: Exact Commands to Replicate TPU in Front of Your Boss

If you want to demonstrate deploying the Cloud TPU edition from scratch:

```powershell
# Step 1: Open PowerShell and navigate to the TPU directory
cd c:\Users\ayu23\OneDrive\Desktop\tpu\inference_gateway_tpu

# Step 2: Run the 1-Click deployment script
.\run.ps1
```

### What `run.ps1` does automatically:
1. Provisions the GKE cluster with Gateway API standard and Cloud Storage FUSE CSI driver.
2. Creates the regional proxy-only subnet (`10.125.0.0/24`) and Envoy routing firewall rules.
3. Requests a 4-chip Cloud TPU v6e Trillium slice (`ct6e-standard-4t`, 2x2 mesh).
4. Streams 50.71 GB Gemma-2-27B-IT weights from `gs://mevreon-tpu-model-weights`.
5. Starts the `llm-d` Endpoint Picker (EPP) scheduling extension (`v1.5.0`).
6. Deploys the Gradio Web UI with a public LoadBalancer external IP.

### Verification Command:
```powershell
python client/test_inference.py
```

### Teardown (Stop Billing):
```powershell
.\cleanup.ps1
```

---

## 🎮 Part 3: Exact Commands to Replicate NVIDIA GPU in Front of Your Boss

To run and demonstrate the official NVIDIA GPU edition:

```powershell
# Step 1: Open PowerShell and navigate to the GPU directory
cd c:\Users\ayu23\OneDrive\Desktop\tpu\inference_gateway_gpu

# Step 2: Run the 1-Click GPU deployment script
.\run.ps1
```

### What the GPU script does automatically:
1. Connects to the cluster and provisions an NVIDIA L4 GPU node pool (`g2-standard-4`).
2. Automatically installs NVIDIA GPU drivers.
3. Deploys the official `vllm/vllm-openai:latest` container with `--accelerator=nvidia.com/gpu: 1`.
4. Connects the GPU InferencePool to the `llm-d` EPP scheduler on port 9090.
5. Exposes the GPU Gradio Web UI on port 8080.

### Verification Command:
```powershell
python client/test_inference.py
```

### Teardown (Stop GPU Billing):
```powershell
.\cleanup.ps1
```

---

## 📊 Executive Talking Points for Your Presentation

1. **Why GKE Inference Gateway?**
   - Traditional Kubernetes load balancers only inspect L4/L7 HTTP headers and round-robin blindly.
   - GKE Inference Gateway with `llm-d` inspects real-time model telemetry (KV cache utilization, prefix caching hits, queue depth) to route requests to the best accelerator.
2. **TPU v6e (Trillium) Advantage:**
   - 4x cost-performance compared to prior generation TPUs.
   - Ideal for large multi-billion parameter models (e.g. 27B) with fast OpenXLA compilation and huge HBM bandwidth.
3. **GPU Flexibility:**
   - Runs standard CUDA / NVIDIA containers (`vllm-openai`) with zero code modifications.
   - Both TPU and GPU workloads can be managed uniformly using the exact same Kubernetes Gateway API Inference Extension CRDs (`InferencePool`, `InferenceObjective`).
