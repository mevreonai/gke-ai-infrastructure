# RUNBOOK: FRESH VM PROVISIONING & BENCHMARK SUITE EXECUTION
## Complete Step-by-Step Operations Guide from Clean GCP VM to Validated Telemetry

This runbook provides copy-pasteable commands to provision a clean GPU VM (or 2-node cluster) on Google Cloud Platform, install the required AI software stack, run the automated smoke test, and execute the benchmark suite.

---

## 📋 Architecture & Prerequisites Overview

* **GPU Accelerators:** NVIDIA RTX PRO 6000 Ada (8x per node) or NVIDIA Blackwell B200 / Hopper H100.
* **Host OS:** Ubuntu 22.04 LTS (Deep Learning VM or clean server image).
* **Network:** Google Cloud Andromeda VPC with Tier 1 Networking enabled (100 Gbps line rate).
* **Storage:** $\ge 500\text{ GB}$ NVMe / Hyperdisk Balanced per node for model weights and traces.
* **Target Model:** `moonshotai/Kimi-Linear-48B-A3B-Instruct` (or any custom HF MoE / Dense model).

---

## STEP 1: Provisioning GPU Instances on Google Cloud

Run these commands from your local machine (with `gcloud` authenticated) or Cloud Shell:

### 1.1 Set GCP Project & Compute Region
```bash
export PROJECT_ID="mevreon"
export ZONE="us-central1-b"
export SUBNET="default"
gcloud config set project "$PROJECT_ID"
gcloud config set compute/zone "$ZONE"
```

### 1.2 Create Node 0 (Primary Orchestrator & Worker)
```bash
gcloud compute instances create kimi-node-0 \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --machine-type="a3-highgpu-8g" \
  --network-interface="network-tier=PREMIUM,subnet=$SUBNET,nic-type=GVNIC" \
  --maintenance-policy="TERMINATE" \
  --service-account="$(gcloud config get-value account)" \
  --scopes="https://www.googleapis.com/auth/cloud-platform" \
  --image-family="common-cu124-ubuntu-2204" \
  --image-project="deeplearning-platform-release" \
  --boot-disk-size="600GB" \
  --boot-disk-type="pd-ssd" \
  --boot-disk-device-name="kimi-node-0" \
  --metadata="install-nvidia-driver=True"
```

> [!NOTE]
> If using custom GPU shapes (e.g. 8x NVIDIA RTX PRO 6000 Ada or L40S), specify:
> `--accelerator="type=nvidia-rtx-pro-6000,count=8" --machine-type="n1-standard-96"`

### 1.3 Create Node 1 (Secondary Worker for Dual-Node Scale-Out)
```bash
gcloud compute instances create kimi-node-1 \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --machine-type="a3-highgpu-8g" \
  --network-interface="network-tier=PREMIUM,subnet=$SUBNET,nic-type=GVNIC" \
  --maintenance-policy="TERMINATE" \
  --service-account="$(gcloud config get-value account)" \
  --scopes="https://www.googleapis.com/auth/cloud-platform" \
  --image-family="common-cu124-ubuntu-2204" \
  --image-project="deeplearning-platform-release" \
  --boot-disk-size="600GB" \
  --boot-disk-type="pd-ssd" \
  --boot-disk-device-name="kimi-node-1" \
  --metadata="install-nvidia-driver=True"
```

### 1.4 Retrieve Internal Cluster IPs
```bash
NODE0_IP=$(gcloud compute instances describe kimi-node-0 --zone="$ZONE" --format='get(networkInterfaces[0].networkIP)')
NODE1_IP=$(gcloud compute instances describe kimi-node-1 --zone="$ZONE" --format='get(networkInterfaces[0].networkIP)')

echo "Node 0 Internal IP: $NODE0_IP"
echo "Node 1 Internal IP: $NODE1_IP"
```

---

## STEP 2: Host Environment & Driver Setup

SSH into `kimi-node-0`:
```bash
gcloud compute ssh kimi-node-0 --zone="$ZONE"
```

### 2.1 Verify GPU Driver & CUDA Version
```bash
nvidia-smi
# Expected: 8 GPUs detected, Driver version >= 550.54, CUDA Version >= 12.4
```

### 2.2 Install Required System Tooling & Linux Network Utilities
```bash
sudo apt-get update && sudo apt-get install -y \
  git git-lfs build-essential iproute2 iputils-ping numactl \
  libnuma-dev linux-tools-common linux-tools-generic \
  python3-pip python3-venv jq
```

### 2.3 Configure Inter-Node Passwordless SSH (From Node 0 to Node 1)
```bash
# Generate key if not already present
[[ -f ~/.ssh/id_rsa ]] || ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa

# Add public key to authorized_keys on Node 1
PUBKEY=$(cat ~/.ssh/id_rsa.pub)
gcloud compute ssh kimi-node-1 --zone="$ZONE" --command="echo '$PUBKEY' >> ~/.ssh/authorized_keys"

# Test passwordless connectivity from Node 0:
ssh -o StrictHostKeyChecking=no "$NODE1_IP" "nvidia-smi --query-gpu=name --format=csv,noheader"
```

---

## STEP 3: Python Virtual Environment & AI Serving Stack

On `kimi-node-0` (and repeat on `kimi-node-1`):

### 3.1 Create and Activate Virtual Environment
```bash
python3 -m venv ~/vllm_env
source ~/vllm_env/bin/activate
pip install --upgrade pip setuptools wheel
```

### 3.2 Install PyTorch (CUDA 12.4)
```bash
pip install torch==2.5.1 torchvision --index-url https://download.pytorch.org/whl/cu124
```

### 3.3 Install vLLM, FlashInfer, and Distributed Ray
```bash
# Install vLLM
pip install "vllm>=0.6.3" ray[default] packaging psutil aiohttp requests tabulate pandas

# Install FlashInfer for Triton & Cutlass acceleration
pip install flashinfer -i https://flashinfer.ai/whl/cu124/torch2.5/
```

### 3.4 Verify AI Stack Installation
```bash
python3 -c "import torch, vllm, ray; print('PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available(), '| vLLM:', vllm.__version__)"
```

---

## STEP 4: Deploying Platform Code & Setting Cluster Config

### 4.1 Sync Performance Intelligence Platform to Node 0
Upload the suite from your local machine to `kimi-node-0`:
```bash
gcloud compute scp --recurse ~/Performance_Intelligence_Platform kimi-node-0:~/ --zone="$ZONE"
```

### 4.2 Configure `RUN_CONFIG.env` on Node 0
On `kimi-node-0`:
```bash
cd ~/Performance_Intelligence_Platform/scripts
cp RUN_CONFIG.env.example RUN_CONFIG.env

# Update internal IPs
sed -i "s/export NODE0_IP=\".*\"/export NODE0_IP=\"$NODE0_IP\"/" RUN_CONFIG.env
sed -i "s/export NODE1_IP=\".*\"/export NODE1_IP=\"$NODE1_IP\"/" RUN_CONFIG.env
```

---

## STEP 5: Running the Automated Sanity Smoke Test

Before executing heavy multi-hour benchmarks, verify all scripts, kernel flags, schema files, and tooling with the automated smoke test (~3 to 5 minutes):

```bash
cd ~/Performance_Intelligence_Platform/scripts
bash run_smoke_test.sh
```

### What the Smoke Test Validates (Up to 11 Automated Checks):
1. **Host Environment:** Python 3.10+, NVIDIA GPU drivers, and system dependencies.
2. **AI Framework Stack:** PyTorch CUDA availability and vLLM module initialization.
3. **MoE Kernel Invariants:** Checks `CUDA_DEVICE_ORDER=PCI_BUS_ID`, `VLLM_MOE_BACKEND=triton`, `VLLM_FLASHINFER_AUTOTUNE=1`, and `VLLM_PP_LAYER_PARTITION=15,12`.
4. **Cases Schema:** Validates `master_benchmark_cases.json` integrity across all 20 steps (27 cases).
5. **Linux Systems Utilities:** Qualifies `taskset`, `ip`, `tc`, and `numactl`.
6. **Dual-Node 16-GPU Interconnect Probe:** (When `NODE1_IP` is configured) Tests SSH connectivity, remote GPU detection, and inter-node readiness.
7. **Wave Trimming Engine:** Mathematically tests pilot wave outlier removal.
8. **Micro-Benchmark Pipeline:** Emulates telemetry generation and validates JSON schema.
9. **Master Runner Dry-Run:** Executes `run_master_benchmark.sh --dry-run` to prove zero syntax errors across steps 00–20.
10. **Wave & Stall Engine Verification:** Verifies decode pause and stall algorithms.
11. **Report Emission:** Generates a unified JSON verdict in `SMOKE_TEST_REPORT.json`.

Expected terminal output:
```text
================================================================================
  ✅ SMOKE TEST PASSED (11 / 11 CHECKS VERIFIED)
  Platform is 100% READY to execute full benchmark suites!
================================================================================
```

---

## STEP 6: Model Weights Configuration (GCS Buckets & HuggingFace)

The platform is model-agnostic. You can serve models directly from HuggingFace or from pre-staged Google Cloud Storage (GCS) buckets:

### 6.1 Kimi-Linear 48B (`moonshotai/Kimi-Linear-48B-A3B-Instruct`)
* **Option A: Direct HuggingFace:**
  ```bash
  export MODEL="moonshotai/Kimi-Linear-48B-A3B-Instruct"
  ```
* **Option B: Pre-staged GCS Bucket (Recommended for fast local loading):**
  ```bash
  # Sync weights from GCS bucket to high-speed NVMe:
  sudo mkdir -p /data/models/kimi-linear-48b
  sudo chown -R $USER:$USER /data/models
  gcloud storage rsync -r gs://mevreon-kimi-k3-weights/moonshotai/Kimi-K3 /data/models/kimi-linear-48b/
  
  export MODEL="/data/models/kimi-linear-48b"
  ```

### 6.2 DeepSeek V4.1 (`deepseek-ai/DeepSeek-V4.1-Flash`)
* **Pre-staged GCS Bucket:**
  ```bash
  # Sync weights from GCS bucket to high-speed NVMe:
  sudo mkdir -p /data/models/deepseek-v4.1-flash
  sudo chown -R $USER:$USER /data/models
  gcloud storage rsync -r gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash /data/models/deepseek-v4.1-flash/
  
  export MODEL="/data/models/deepseek-v4.1-flash"
  ```

---

## STEP 7: Executing the Benchmark Suite

### Profile-Based Execution

```bash
# 1. Quick Smoke Profile (~10 min): TP4 1k/8k c=1 sanity check on actual GPU weights
bash run_master_benchmark.sh --profile smoke --model "$MODEL"

# 2. Fast Dashboard Profile (~2h): Stages 1 & 2 (Minimum dataset for dashboard build)
bash run_master_benchmark.sh --profile fast-dashboard --model "$MODEL"

# 3. Default Full Campaign (~9h): Steps 00-17 across all topologies with cold/warm cache isolation
bash run_master_benchmark.sh --profile default --model "$MODEL"

# 4. Deep Profile Campaign (~14h): Steps 00-20 with Poisson sweeps, scheduler sweeps, and observer overhead
bash run_master_benchmark.sh --profile deep-profile --model "$MODEL"
```

### Targeted Custom Execution
```bash
# Filter by topology and stage:
bash run_master_benchmark.sh --model "$MODEL" --topologies tp4_pp1,tp8_pp1 --stage 1

# Filter by context and concurrency:
bash run_master_benchmark.sh --model "$MODEL" --contexts 1k,8k --concurrencies 1,8
```

---

## STEP 7: Monitoring & Real-Time Telemetry

While the benchmark runs, monitor progress in real time:

```bash
# Monitor live step transitions and exit codes:
tail -f ~/platform_benchmark_runs/latest_run_id.txt | xargs -I {} tail -f ~/platform_benchmark_runs/{}/master_step_status.jsonl

# Monitor overall campaign log:
tail -f ~/platform_benchmark_runs/latest_run_id.txt | xargs -I {} tail -f ~/platform_benchmark_runs/{}/logs/MASTER_BENCHMARK_RUN.log
```

---

## STEP 8: Retrieving Telemetry & Stopping Instances

### 8.1 Package and Download Results Archive
On `kimi-node-0`:
```bash
RUN_ID=$(cat ~/platform_benchmark_runs/latest_run_id.txt)
tar -czvf ~/benchmark_results_${RUN_ID}.tar.gz -C ~/platform_benchmark_runs "$RUN_ID"
```

From your local machine:
```bash
gcloud compute scp kimi-node-0:~/benchmark_results_*.tar.gz ./ --zone="$ZONE"
```

### 8.2 Stop VM Instances (Eliminates Compute Billing)
Once results are downloaded, stop instances immediately:
```bash
gcloud compute instances stop kimi-node-0 kimi-node-1 --zone="$ZONE"
```
Verify instances are terminated:
```bash
gcloud compute instances list --filter="name ~ kimi-node"
```
