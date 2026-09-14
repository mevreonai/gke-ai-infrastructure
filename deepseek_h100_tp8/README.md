# DeepSeek-V4.1-Flash on 8× NVIDIA H100 (a3-highgpu-8g)

Production setup and replication scripts for deploying **DeepSeek-V4.1-Flash** on 8× NVIDIA H100 80GB SXM5 GPUs using **vLLM (TP=8)**.

---

## 📁 Repository Structure
```text
deepseek_h100_tp8/
├── 01_provision_vm.sh            # Provisions 1000GB disk & 8x H100 SPOT instance on GCP
├── 02_download_weights.sh        # Fast multi-stream download of 48 safetensors shards
├── 03_launch_vllm.sh             # Launches vLLM in Docker with TP=8 & Hopper SM90 flags
├── 04_test_chat.py               # Python test client with latency & throughput benchmarking
├── 05_manage_vm.sh               # Helper to start and safely stop the VM (freezes billing)
├── ARCHITECTURE_AND_CONVERSION.md # Complete component-wise architecture & conversion deep-dive
└── README.md                     # This file
```

---

## 🚀 Quickstart

### 1. Start Existing VM
```powershell
gcloud compute instances start deepseek-h100 --zone=us-central1-a --project=mevreon
```

### 2. Run Test Prompt
```powershell
python 04_test_chat.py 35.224.109.183
```

### 3. Stop VM (Avoid Billing)
```powershell
gcloud compute instances stop deepseek-h100 --zone=us-central1-a --project=mevreon --discard-local-ssd=true
```

For the complete technical breakdown of how the weights, MXFP4 Marlin conversion, TileLang JIT compilation, and vLLM serving work, see [ARCHITECTURE_AND_CONVERSION.md](ARCHITECTURE_AND_CONVERSION.md).
