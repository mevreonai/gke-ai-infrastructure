# DeepSeek-V4.1-Flash (FP8) on 8× NVIDIA A100 (80GB) Spot with Tensor Parallelism 8

This package provides a turnkey, production-grade deployment script for serving the **DeepSeek-V4.1-Flash (~510 GB native FP8)** model across **8× NVIDIA A100 (80GB)** GPUs on Google Cloud using **Tensor Parallelism 8 (TP=8)** and **Prometheus** monitoring.

---

## 🏛️ Architecture & Component Selection

```
                   ┌────────────────────────────────────────┐
                   │    Client / test_inference.py          │
                   └───────────────────┬────────────────────┘
                                       │ HTTP Port 8000
                                       ▼
                   ┌────────────────────────────────────────┐
                   │             vLLM Engine                │
                   │   --tensor-parallel-size 8             │
                   │   --distributed-executor-backend mp    │
                   │   --quantization fp8                   │
                   │   --gpu-memory-utilization 0.95        │
                   │                                        │
                   │  ┌──────────────┐    ┌──────────────┐  │
                   │  │  OpenAI API  │    │  Prometheus  │  │
                   │  │   Port 8000  │    │   Port 9090  │  │
                   │  └──────────────┘    └──────────────┘  │
                   └───────────────────┬────────────────────┘
                                       │ NCCL / NVLink (600 GB/s)
          ┌────────┬────────┬────────┬─┴──────┬────────┬────────┬────────┐
          ▼        ▼        ▼        ▼        ▼        ▼        ▼        ▼
        GPU 0    GPU 1    GPU 2    GPU 3    GPU 4    GPU 5    GPU 6    GPU 7
        (A100)   (A100)   (A100)   (A100)   (A100)   (A100)   (A100)   (A100)
        [ 80GB ] [ 80GB ] [ 80GB ] [ 80GB ] [ 80GB ] [ 80GB ] [ 80GB ] [ 80GB ]
        └───────────────────────── 640 GB VRAM ──────────────────────────┘
```

### Why NOT Ray?
On a single 8-GPU node (`a2-ultragpu-8g`), all 8 GPUs reside on the **same physical SXM4 NVLink mesh** (600 GB/s bandwidth). PyTorch's native multiprocessing (`mp`) backend communicates directly via hardware NCCL without daemon serialization, eliminating Ray cluster crashes, heartbeat timeouts, and unnecessary memory overhead.

### Why NOT llm-d?
`llm-d` is designed specifically for **Disaggregated Prefill/Decode (P/D)** architectures (routing prompts to a prefill cluster and streaming KV cache over high-speed networks to a decode cluster). Standard **Tensor Parallelism 8 (TP=8)** on a single model instance is simpler, faster, and avoids unneeded proxy sidecars and latency.

---

## 💰 Cost Protection: Spot vs. On-Demand

| VM Type | Provisioning Model | Approx. Hourly Rate | Savings |
| :--- | :--- | :--- | :--- |
| **`a2-ultragpu-8g` (8× A100 80GB)** | **SPOT** | **~$8.79 / hour** | **~70% OFF** |
| `a2-ultragpu-8g` (8× A100 80GB) | Standard On-Demand | ~$29.30 / hour | Standard |
| **Idle (Torn down via cleanup.ps1)** | **Deleted** | **$0.00 / hour** | **100% OFF** |

---

## 🚀 Quickstart Guide

### 1. Launch the Stack (When Ready to Test)
Run the automated launcher:
```powershell
.\run.ps1 -ProjectId mevreon -Zone us-central1-a
```
*(You can also use zones where you have quota, like `us-east4-c` or `europe-west4-a`)*.

The script will:
1. Open firewall ports `8000` (vLLM API), `9090` (Prometheus), and `9400` (DCGM).
2. Provision the Spot `a2-ultragpu-8g` instance with 500GB SSD.
3. Automatically install CUDA drivers, Docker, and NVIDIA Container Toolkit.
4. Mount `gs://mevreon-deepseek-models` via high-speed GCS FUSE.
5. Launch NVIDIA DCGM-exporter and Prometheus on port `9090`.
6. Launch vLLM with `TP=8` and `FP8` on port `8000`.

---

### 2. Run Inference & Validate Prometheus Metrics
Once the engine is ready, test streaming inference:
```powershell
python test_inference.py --host <VM_EXTERNAL_IP>
```
This will:
* Verify health on `/health`
* Scrape pre-inference VRAM cache metrics from `:8000/metrics`
* Stream tokens from DeepSeek-V4.1-Flash and measure **TTFT** and **tokens/sec**
* Display post-inference cache and request metrics

---

### 3. Immediate Cleanup (Stop Billing)
To guarantee zero unexpected billing charges, run the cleanup script as soon as you finish testing:
```powershell
.\cleanup.ps1 -Zone us-central1-a
```
This deletes the VM, frees the 8× A100 GPUs, and removes temporary firewall rules.
