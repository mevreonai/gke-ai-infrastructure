# Kimi-K3 Live Cluster Demonstration Runbook

This operational runbook provides exact terminal procedures, expected outputs, timing expectations, and verification steps for presenting or testing the **Moonshot AI Kimi-K3 24-GPU cluster**.

---

## ⏱️ Execution Timeline & Expected Latency

| Sequence | Action | Tool / Command | Expected Elapsed Time |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Instance Boot | `.\cluster.ps1 start` | **~60 seconds** |
| **Phase 2** | Ray Cluster Forming | Auto-triggered via systemd | **~30–45 seconds** |
| **Phase 3** | 96-Shard Model Loading | `.\cluster.ps1 logs` | **~25–28 minutes** (1.45 TB from disk to GPU) |
| **Phase 4** | Live Query & Inference | `.\cluster.ps1 query` / `python test_chat.py` | **~2–4 seconds** (Streaming output) |
| **Phase 5** | Cluster Shutdown | `.\cluster.ps1 stop` | **~15 seconds** |

---

## 📋 Step-by-Step Operator Procedure

### Step 1: Boot the 24-GPU Cluster

Run the start command from your terminal:

```powershell
.\cluster.ps1 start
```
*Or on Linux/macOS:*
```bash
./cluster.sh start
```

**Expected Console Output:**
```
========================================================
 Starting Kimi-K3 Distributed Cluster (24x RTX 6000 Pro)
========================================================
>> Starting kimi-node-0 (Head Node (vLLM API Port 8000)) in us-central1-b...
   [OK] kimi-node-0 is RUNNING!
>> Starting kimi-node-1 (Worker Node 1 (8 GPUs)) in us-central1-b...
   [OK] kimi-node-1 is RUNNING!
>> Starting kimi-node-2 (Worker Node 2 (8 GPUs)) in us-west1-a...
   [OK] kimi-node-2 is RUNNING!

========================================================
 Auto-Boot Sequence Initialized
 - Ray Cluster and vLLM are automatically launching via systemd.
 - To watch weight loading: .\cluster.ps1 logs
 - To test the endpoint:     .\cluster.ps1 query
========================================================
```

---

### Step 2: Verify Cluster & GPU Health

Check that all 3 instances are online and Ray sees all 24 GPUs:

```powershell
.\cluster.ps1 status
```

**Expected Ray Status Output:**
```
Node status
---------------------------------------------------------------
Active:
 1 node_596ac7551a87bbc1998280f076682ed71c15a5087112e8250900cf8a (kimi-node-0)
 1 node_99a011eea77cd2a02017888444967fae3c4c98dced162a76b54e6e10 (kimi-node-1)
 1 node_09db745a3a9fb963aee5bd31dd6fc578151127aecdb7240e85e91f92 (kimi-node-2)

Resources
---------------------------------------------------------------
Total Usage:
 0.0/1152.0 CPU
 24.0/24.0 GPU (24.0 used of 24.0 reserved in placement groups)
 0B/3.60TiB memory
```

---

### Step 3: Monitor Distributed Weight Loading

Stream the real-time weight loading across all 24 GPUs:

```powershell
.\cluster.ps1 logs
```

**Expected Output Progression:**
```
Loading safetensors checkpoint shards:   0% Completed | 0/96 [00:00<?, ?it/s]
Loading safetensors checkpoint shards:  25% Completed | 24/96 [06:55<20:45, 17.3s/it]
Loading safetensors checkpoint shards:  50% Completed | 48/96 [13:50<13:50, 17.3s/it]
Loading safetensors checkpoint shards:  75% Completed | 72/96 [20:45<06:55, 17.3s/it]
Loading safetensors checkpoint shards: 100% Completed | 96/96 [28:06<00:00, 17.5s/it]
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
*(Press `Ctrl+C` to exit log streaming once startup is complete.)*

---

### Step 4: Execute Live Interactive Demos

#### Option A: 1-Click PowerShell Query
```powershell
.\cluster.ps1 query
```

#### Option B: Live Streaming Python Client
```bash
python test_chat.py --host <NODE0_EXTERNAL_IP> --prompt "Explain the key architectural innovations of Kimi-K3."
```

#### Option C: Native HTTP API (`curl`)
```bash
curl -X POST http://<NODE0_EXTERNAL_IP>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-K3",
    "messages": [
      {"role": "system", "content": "You are Moonshot AI Kimi-K3 running on a 24-GPU cluster."},
      {"role": "user", "content": "Write a fast Python script demonstrating Ray actor parallelism."}
    ],
    "max_tokens": 200,
    "temperature": 0.6
  }'
```

---

### Step 5: Power Off Cluster to Pause Billing

```powershell
.\cluster.ps1 stop
```

**Expected Output:**
```
=== Stopping Cluster Nodes (Pausing Billing) ===
>> Powering off kimi-node-0...
>> Powering off kimi-node-1...
>> Powering off kimi-node-2...

All 3 nodes stopped. GPU billing paused. Model disks preserved.
```

---

## 🔍 Verification & Diagnostics

If port 8000 does not respond immediately after starting:

1. **Check Systemd Service on Head Node:**
   ```bash
   gcloud compute ssh kimi-node-0 --zone=us-central1-b --project=mevreon --command="sudo systemctl status kimi-vllm.service"
   ```
2. **Inspect Ray Container Logs:**
   ```bash
   gcloud compute ssh kimi-node-0 --zone=us-central1-b --project=mevreon --command="docker logs ray-head --tail 50"
   ```
3. **Check Worker Nodes:**
   ```bash
   gcloud compute ssh kimi-node-1 --zone=us-central1-b --project=mevreon --command="docker ps"
   gcloud compute ssh kimi-node-2 --zone=us-west1-a --project=mevreon --command="docker ps"
   ```
