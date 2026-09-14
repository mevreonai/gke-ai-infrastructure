# DeepSeek-V4.1-Flash on 8× NVIDIA H100 SXM5: Complete Architecture & Conversion Guide

This document explains each component of the deployment, how the weights were acquired, how the on-the-fly quantization/packing conversion happened, and exact step-by-step commands to spin up a new instance from scratch.

---

## 1. Component-by-Component Breakdown

### Component 1: Hardware & Compute Infrastructure
* **GCP Instance Type:** `a3-highgpu-8g` (Provisioned as SPOT / Preemptible).
* **GPUs:** 8× NVIDIA H100 80GB SXM5 (Hopper architecture, SM90 compute capability).
* **Interconnect:** 3.2 Tbps NVSwitch (NVLink 4.0 interconnecting all 8 GPUs at 900 GB/s bidirectional per card).
* **Host Compute:** 208 vCPUs (Intel Xeon Platinum 8480C), 1,872 GB (1.8 TB) System RAM.
* **Storage:** 1,000 GB Hyperdisk Balanced (attached as boot disk, preserving OS, container images, and model weights).

---

### Component 2: Storage & Weights Sourcing
* **HuggingFace Repository:** `deepseek-ai/DeepSeek-V4.1-Flash`
* **Raw Weights Format:** 48 Safetensors checkpoint shards (`model-00001-of-00048.safetensors` through `00048-of-00048.safetensors`), totaling **475.25 GiB**.
* **Storage Strategy:**
  * Rather than streaming weights across network buckets (GCS FUSE), the entire ~475 GB model was downloaded directly to a **1,000 GB local NVMe/hyperdisk** at `/data/models/deepseek-v4.1-flash/`.
  * Local disk read speed exceeds **800 MB/s**, enabling the 48 shards to be read into system RAM in **~2 minutes 18 seconds**.
  * To migrate between zones without re-downloading, GCP snapshots were used (`deepseek-weights-snapshot`). A new disk created from a snapshot takes under 4 minutes to restore 1,000 GB.

---

### Component 3: The Weight Conversion & Quantization Pipeline
DeepSeek-V4.1-Flash has **40 layers** with **384 routed MoE experts per layer** plus shared experts, resulting in **46,080 distinct expert weight matrices** (`w1`, `w2`, `w3` projections).

Here is how the conversion happened start to end:

```
[48 Safetensors Shards on Disk (475 GB)]
                   │  (Read into RAM: 2m 18s)
                   ▼
       [Host Memory Tensor Cache]
                   │
    ┌──────────────┴──────────────┐
    │  Tensor Parallel Sharding   │ (Shards weights across 8 ranks)
    └──────────────┬──────────────┘
                   │
    ┌──────────────┴──────────────┐
    │     MXFP4 / FP8 Decoding    │ (Unpacks Microscaling block format)
    └──────────────┬──────────────┘
                   │
    ┌──────────────┴──────────────┐
    │  Marlin Weight Repacking    │ (Transforms weights into 2:4/Marlin
    │                             │  gemm memory layout for Hopper)
    └──────────────┬──────────────┘
                   │
    ┌──────────────┴──────────────┐
    │ TileLang / TVM JIT Pipeline │ (Lowers CUDA pass pipeline for
    │                             │  FlashMLA and DeepGEMM on SM90)
    └──────────────┬──────────────┘
                   │
                   ▼
  [8x H100 VRAM: 51.5 GB allocated per GPU]
```

#### Detailed Stages:
1. **Sharding Across TP=8:**
   * When vLLM starts with `--tensor-parallel-size 8`, the 8 GPU worker processes (`Worker_TP0` through `Worker_TP7`) divide the expert layers across ranks.
2. **On-the-Fly MXFP4 Packing:**
   * DeepSeek-V4.1 uses `expert_dtype: fp4` with microscaling block scales (`ue8m0` format).
   * Inside `vllm/model_executor/layers/fused_moe/routed_experts.py` (`_load_w2`), vLLM loads each expert weight tensor, aligns the block scales to the refined grid, and converts the weights into the **Marlin MXFP4 GPU memory layout** (`MarlinMxfp8LinearKernel`).
   * This on-the-fly packing eliminates the need for any offline preprocessing scripts or pre-quantized weight conversions.
3. **TileLang / TVM JIT Compilation:**
   * DeepSeek-V4.1 utilizes custom FlashMLA attention and DeepGEMM kernels written in TileLang.
   * On Blackwell (RTX 6000), TileLang failed because TVM lacked SM120 target definitions.
   * On **H100 Hopper (SM90)**, TVM lowered the `CUDAPassPipelineBody` passes smoothly, generating native Hopper PTX/SASS kernels.
4. **CUDA Graph Capture & KV Cache Warmup:**
   * vLLM runs a dummy forward pass through all 40 layers, captures CUDA execution graphs for batch sizes 1 to 512, and reserves the remaining 228 GB of VRAM across the 8 GPUs for the dynamic KV cache.

---

### Component 4: Serving Engine & Runtime Parameters
* **Container Image:** `vllm/vllm-openai:deepseekv41-flash-0909`
* **Serving Framework:** vLLM v1 Engine (FastAPI + Uvicorn + zmq shm broadcast).
* **Command Parameters:**
  * `--tensor-parallel-size 8`: Distributes model across all 8 GPUs.
  * `--tokenizer-mode deepseek_v41`: Uses the specialized fast Rust tokenizer.
  * `--language-model-only`: Disables vision encoder modules for pure LLM serving.
  * `--gpu-memory-utilization 0.92`: Uses 92% of VRAM (~74 GB per card: 51.5 GB weights + 22.5 GB KV cache).
  * `--ipc=host --net=host`: Uses host shared memory and host network stack for zero-latency inter-GPU NCCL all-reduce.
  * Context Window: Native **1,048,576 tokens (1M)** using YaRN RoPE scaling.

---

## 2. Start-to-End Commands to Build from Scratch

If you ever need to reproduce this setup on a completely fresh GCP VM:

### Step 1: Create 1,000 GB Disk & Launch 8x H100 VM
```powershell
# Create fresh 1000GB disk (or use snapshot)
gcloud compute disks create deepseek-h100-disk `
    --project=mevreon `
    --zone=us-central1-a `
    --type=hyperdisk-balanced `
    --size=1000GB `
    --image-family=ubuntu-2204-lts `
    --image-project=ubuntu-os-cloud

# Launch Spot a3-highgpu-8g instance
gcloud compute instances create deepseek-h100 `
    --project=mevreon `
    --zone=us-central1-a `
    --machine-type=a3-highgpu-8g `
    --provisioning-model=SPOT `
    --instance-termination-action=STOP `
    --disk="name=deepseek-h100-disk,boot=yes,auto-delete=no" `
    --tags=deepseek-node,http-server `
    --maintenance-policy=TERMINATE `
    --scopes=cloud-platform
```

### Step 2: Install NVIDIA Drivers and Docker
SSH into the instance:
```powershell
gcloud compute ssh deepseek-h100 --zone=us-central1-a --project=mevreon
```
Inside the instance:
```bash
# Install NVIDIA Driver 580+ and CUDA 12.8 / 13.0
sudo apt-get update && sudo apt-get install -y nvidia-driver-580 nvidia-utils-580

# Install Docker & NVIDIA Container Toolkit
curl -fsSL https://get.docker.com | sh
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Step 3: Download Model Weights
```bash
sudo mkdir -p /data/models/deepseek-v4.1-flash
sudo chown -R $USER:$USER /data/models/deepseek-v4.1-flash

pip install huggingface_hub[hf_transfer]
export HF_HUB_ENABLE_HF_TRANSFER=1

huggingface-cli download deepseek-ai/DeepSeek-V4.1-Flash \
    --local-dir /data/models/deepseek-v4.1-flash \
    --local-dir-use-symlinks False
```

### Step 4: Run vLLM in Distributed Mode (TP=8)
```bash
sudo docker run -d \
    --name vllm-deepseek \
    --restart unless-stopped \
    --gpus all \
    --ipc=host \
    --net=host \
    -v /data/models/deepseek-v4.1-flash:/models/deepseek-ai/DeepSeek-V4.1-Flash:ro \
    vllm/vllm-openai:deepseekv41-flash-0909 \
    --model /models/deepseek-ai/DeepSeek-V4.1-Flash \
    --tensor-parallel-size 8 \
    --tokenizer-mode deepseek_v41 \
    --language-model-only \
    --gpu-memory-utilization 0.92 \
    --served-model-name deepseek-ai/DeepSeek-V4.1-Flash \
    --trust-remote-code \
    --port 8000 \
    --host 0.0.0.0
```

### Step 5: Test Inference
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-V4.1-Flash",
    "messages": [{"role": "user", "content": "Explain the architecture of DeepSeek V4 in 2 concise sentences."}],
    "max_tokens": 100
  }' | jq
```

### Step 6: Stop VM to Prevent Unwanted Charges
```powershell
gcloud compute instances stop deepseek-h100 --zone=us-central1-a --project=mevreon --discard-local-ssd=true
```
