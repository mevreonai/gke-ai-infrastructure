# 🚀 Executive Demo Guide: Multi-Host & Single-Host TPU Serving on GKE

This guide is designed for presenting a live, end-to-end demonstration of **LLM Serving on Google Cloud TPUs** using **Google Gemma-2-27B-IT**, comparing **Single-Host TPU v6e (Trillium)** and **Multi-Host TPU** architectures with **automatic cost protection**.

---

## 🎯 Architecture Summary (What to Explain to Your Boss)

| Feature | Single-Host TPU (`single_host/`) | Multi-Host TPU (`multi_host/`) |
| :--- | :--- | :--- |
| **Hardware** | **TPU v6e Trillium** (`ct6e-standard-4t`, 4 chips) | **TPU v5e Pod Slice** (2 VMs x `ct5lp-hightpu-4t`, `2x4`) |
| **Location** | Region-agnostic (default: `europe-west4-a`, quota active) | Region-agnostic (default: `europe-west4-a` / `us-east4-b`) |
| **Serving Framework** | **Standalone vLLM** (Standard Kubernetes Deployment) | **Ray Serve + vLLM** (KubeRay Operator) |
| **Why this architecture?** | Follows Google's official GKE reference architecture. Cleanest, no Ray overhead when model fits on 1 VM. | Scales across multiple physical hosts via Inter-Chip Interconnect (ICI). |
| **Model Streaming** | **Cloud Storage FUSE CSI Driver** (`gs://mevreon-tpu-model-weights`) | **Cloud Storage FUSE CSI Driver** (`gs://mevreon-tpu-model-weights`) |
| **Cost Protection** | **Comprehensive Multi-Region Auto-Teardown on exit** | **Comprehensive Multi-Region Auto-Teardown on exit** |

---

## 🎬 Live Presentation Steps (On Call)

### Option 1: Single-Host TPU v6e Trillium Demo (Official Google Standard GKE + vLLM)

#### Step 1: Open PowerShell and Launch
```powershell
cd c:\Users\ayu23\OneDrive\Desktop\tpu\single_host
.\run.ps1
```
> **Tip for unattended testing:** Add `-AutoTestAndTeardown` (e.g. `.\run.ps1 -AutoTestAndTeardown`) to automatically deploy, run live model validation benchmarks, and trigger multi-region cost cleanup upon completion without requiring manual keypresses.

#### Step 2: Live Telemetry & What to Point Out
* The script streams live progress directly on your terminal:
  ```text
  [LIVE TELEMETRY] Nodes: 2 | Gradio: Running | vLLM Pod: Running | Hardware: TPU Slice Queue: SUCCEEDED
  ```
* Once live, port-forwarding starts and **automatically opens the Gradio chat UI in your browser** at `http://localhost:8080`.

#### Step 3: Test Inference Live
1. **In Browser:** Chat live with **Gemma-2-27B** at `http://localhost:8080`.
2. **In Terminal:** Press **`T`** to execute an instant benchmark test (prints latency, tokens, and response).
3. **In Terminal:** Press **`L`** to stream live vLLM inference logs.

#### Step 4: Show Cost Protection
* Press **`[ENTER]`** (or `Ctrl+C`).
* The teardown trap deletes the GKE cluster and verifies **0 active compute/TPU VMs remain**.

---

### Option 2: Multi-Host TPU Serving Demo (Ray Serve + KubeRay + 8 TPU Chips)

#### Step 1: Open PowerShell and Launch with `-SkipBuild`
```powershell
cd c:\Users\ayu23\OneDrive\Desktop\tpu\multi_host
.\run.ps1 -SkipBuild
```
> **Tip for unattended testing:** Add `-AutoTestAndTeardown` (e.g. `.\run.ps1 -SkipBuild -AutoTestAndTeardown`) to automatically deploy, run live model validation benchmarks, and trigger multi-region cost cleanup upon completion without requiring manual keypresses.

#### Step 2: What Happens Automatically
* Uses the pre-built image in Artifact Registry (`-SkipBuild`).
* Deploys the RayService manifest spanning the 2 worker hosts with 8-way tensor parallelism.
* Opens `http://localhost:8080` for live chat.
* Press **`T`** for inference test or **`S`** for Ray Serve distributed status.

#### Step 3: Exit and Clean Up
* Press **`[ENTER]`** to delete all clusters and VMs across all regions automatically.

---

## 🛑 Universal Emergency Teardown
If you ever want to force-delete all clusters and check all VMs across all regions:

```powershell
# From root or any directory:
.\cleanup.ps1
```
Or in Bash:
```bash
./cleanup.sh
```
