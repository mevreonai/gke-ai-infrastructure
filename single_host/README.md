# Single-Host TPU Serving on GKE Standard (vLLM)

This directory implements single-host LLM serving on **Google Kubernetes Engine (GKE) Standard** using **standalone vLLM** (based on the official Google Cloud GKE vLLM TPU architecture guide).

---

## 🏗️ Architecture: Why Single-Host Doesn't Need Ray

In single-host serving:
- All TPU chips (e.g. 4 chips on `ct5lp-hightpu-4t` / `ct6e-standard-4t`, or 8 chips on `ct6e-standard-8t`) reside directly inside a **single VM (Host)**.
- Standard **vLLM** spawns local tensor-parallel workers (`--tensor-parallel-size=4` or `8`) on that single machine.
- No Ray Actor Cluster or KubeRay Operator is required.
- Standard Kubernetes `Deployment` + `Service` manages the workload.

---

## 🚀 Quickstart: Run with Automatic Billing Protection

### On Windows (PowerShell):
```powershell
.\run.ps1 -ProjectId "mevreon" -HfToken "your_huggingface_token"
```

### On Linux / Cloud Shell (Bash):
```bash
./run.sh
```

*When you press `[Enter]` or `Ctrl+C`, the script immediately deletes the GKE cluster and TPU node pool to prevent any accumulating charges.*

---

## 🛑 Manual / Emergency Teardown
```powershell
.\cleanup.ps1 -ProjectId "mevreon"
```
Or in Bash:
```bash
./cleanup.sh
```
