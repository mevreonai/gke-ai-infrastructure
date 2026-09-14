# Kimi-K3 24-GPU Cluster — Quick Demo Guide

This directory provides automated tooling and controllers for operating and demonstrating the **Moonshot AI Kimi-K3 (1.45 TB MoE)** model running across a pre-provisioned **24x NVIDIA RTX Pro 6000 (2.3 TB VRAM)** distributed cluster.

---

## 🚀 Quick Start Overview

| Step | Action | Command | Typical Time |
| :--- | :--- | :--- | :--- |
| **1** | Power ON Cluster | `.\cluster.ps1 start` *(or `./cluster.sh start`)* | ~60s |
| **2** | Check Cluster Status | `.\cluster.ps1 status` *(or `./cluster.sh status`)* | Instant |
| **3** | Stream Weight Loading | `.\cluster.ps1 logs` *(or `./cluster.sh logs`)* | ~25–28m |
| **4** | Send Live Query | `.\cluster.ps1 query` *(or `./cluster.sh query`)* | ~3–5s |
| **5** | Power OFF Cluster | `.\cluster.ps1 stop` *(or `./cluster.sh stop`)* | ~15s |

---

## 📂 Included Tools

- **`cluster.ps1`**: Cross-platform PowerShell cluster manager (supports Windows, macOS, Linux with `pwsh`). Controls VM power states, auto-launches Ray/vLLM, streams logs, and executes live OpenAI-format queries directly.
- **`cluster.sh`**: Native POSIX Bash cluster manager with identical start, status, log streaming, querying, and shutdown capabilities.
- **`test_chat.py`**: Python OpenAI-compatible streaming client measuring Time To First Token (TTFT), total tokens, and tokens per second (TPS).
- **`RUNBOOK.md`**: Detailed step-by-step live demo walkthrough with terminal outputs, troubleshooting, and benchmarking procedures.

---

## 🛠️ Prerequisites

1. **Google Cloud SDK (`gcloud`)** installed and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project mevreon
   ```
2. **Cluster VMs Provisioned**:
   - `kimi-node-0` (`us-central1-b`) — Ray Head Node & vLLM API Host
   - `kimi-node-1` (`us-central1-b`) — Ray Worker Node 1
   - `kimi-node-2` (`us-west1-a`) — Ray Worker Node 2

---

## 💬 Live Inference Query Example

Once the endpoint is ready (Port 8000), query the cluster with `curl`, Python, or PowerShell:

### Using Python Streaming Client:
```bash
python test_chat.py --host <NODE0_EXTERNAL_IP> --port 8000 --prompt "Explain why MoE models require tensor and pipeline parallelism."
```

### Using Standard `curl`:
```bash
curl -X POST http://<NODE0_EXTERNAL_IP>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-K3",
    "messages": [
      {"role": "system", "content": "You are Kimi-K3 running on a 24-GPU cluster."},
      {"role": "user", "content": "What are the advantages of Kimi Delta Attention?"}
    ],
    "max_tokens": 150,
    "temperature": 0.6
  }'
```

---

## 💰 Cost Control Notice

When testing is complete, always shut down the VMs to avoid compute charges:
```powershell
.\cluster.ps1 stop
```
*(All 2 TB local SSD/Hyperdisk persistent disks remain intact with model weights pre-loaded for the next start.)*
