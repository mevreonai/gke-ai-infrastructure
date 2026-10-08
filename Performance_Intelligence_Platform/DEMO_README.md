# Multi-Node Distributed AI Inference Cluster: Complete Execution Runbook

**Cluster Architecture:** Dual-Node GPU Cluster  
**Hardware Accelerators:** 2× GCP G4 Instances × 8× NVIDIA RTX PRO 6000 Blackwell GPUs (16 GPUs Total, 1.5 TB High-Bandwidth GDDR7 VRAM)  
**Host Platform:** AMD EPYC 9654 (384 vCPUs, 1.44 TB RAM per node)  
**Network Fabric:** Google Cloud Virtual Private Cloud (120 Gbps aggregate throughput, 0.075 ms latency)  
**Software Stack:** Rocky Linux 10, NVIDIA Driver 580.173, CUDA 12.8 / 13.0, PyTorch 2.12 (sm_120), Ray Core 2.59, vLLM  

---

## 🖥️ Terminal Window Setup

Open **3 Terminal Windows side-by-side** on your screen:

| Terminal Window | Label | Role | Host |
| :--- | :--- | :--- | :--- |
| **Terminal 1** | `[LOCAL]` | Cluster Provisioning, SCP Deployment & Teardown | Local Workstation |
| **Terminal 2** | `[NODE 0]` | Primary Head Node: Ray Master, Model Ingestion & Benchmark | Remote SSH (`ayu23@<NODE0_IP>`) |
| **Terminal 3** | `[NODE 1]` | Secondary Worker Node: Ray Distributed Worker Pool | Remote SSH (`ayu23@<NODE1_IP>`) |

---

## 📋 Complete Step-by-Step Execution Sequence

### STEP 1: Provision the Dual-Node Infrastructure
* **Where:** 👉 **Terminal 1 (`[LOCAL]`)**
* **Command:**
```bash
cd Performance_Intelligence_Platform/demo
bash 01_provision_cluster.sh
```
*(To use custom instance names, pass them as arguments: `bash 01_provision_cluster.sh <NODE0_NAME> <NODE1_NAME>`)*

* **What it does:**
  * Calls GCP Compute API to provision two `g4-standard-384` spot instances with 8× NVIDIA RTX PRO 6000 GPUs each in `us-central1-b`.
  * Attaches 1000GB NVMe `hyperdisk-balanced` boot volumes.
  * Configures network tags `kimi-ray-node` and permissions.
* **Duration:** ~90 seconds.
* **Output:** Prints a table with instance names, internal IPs, and external IPs. Note down the **External IPs**.

---

### STEP 2: Connect via SSH to Both Nodes

#### 2.1 Connect to Node 0:
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Command:**
```bash
ssh -i ~/.ssh/google_compute_engine ayu23@<NODE0_EXTERNAL_IP>
```

#### 2.2 Verify Hardware & Topology on Node 0:
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Command:**
```bash
nvidia-smi
nvidia-smi topo -m
```
* **Verification:** Confirms 8× NVIDIA RTX PRO 6000 Blackwell GPUs (96 GB GDDR7 VRAM each, 760 GB total per node, Driver 580.173, CUDA 13.0) and dual-NUMA host bridge architecture with PCIe PIX links.

#### 2.3 Connect to Node 1:
* **Where:** 👉 **Terminal 3 (`[NODE 1]`)**
* **Command:**
```bash
ssh -i ~/.ssh/google_compute_engine ayu23@<NODE1_EXTERNAL_IP>
```

---

### STEP 3: Deploy the Platform & Demo Suite to Remote Nodes
* **Where:** 👉 **Terminal 1 (`[LOCAL]`)**
* **Command:**

**On Windows PowerShell:**
```powershell
.\copy_scripts_to_nodes.ps1 <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
```

**On Bash / Linux / macOS:**
```bash
./copy_scripts_to_nodes.sh <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
```

* **What it does:**
  * Uses SCP to push the entire `Performance_Intelligence_Platform` directory to `~/Performance_Intelligence_Platform` on both nodes.
  * Creates a symlink `~/demo` pointing to `~/Performance_Intelligence_Platform/demo`.
  * Sets executable permissions on all shell scripts.

---

### STEP 4: Automated Software Stack Bootstrap (Both Nodes)
Run this command simultaneously on **Terminal 2** and **Terminal 3**:

* **Where:** 👉 **Terminal 2 (`[NODE 0]`)** AND **Terminal 3 (`[NODE 1]`)**
* **Command:**
```bash
cd ~/demo
./02_install_stack.sh
```

* **What it does:**
  * Installs system networking and PCIe diagnostics (`iperf3`, `git`, `pciutils`).
  * Installs `uv` (Rust-based ultra-fast package installer).
  * Creates isolated Python virtual environment at `~/vllm_env`.
  * Installs PyTorch nightly with native CUDA 12.8 / `sm_120` (Blackwell micro-architecture) support.
  * Installs `vLLM`, `Ray Core` (`ray[default]`), `triton`, `transformers`, `huggingface-hub`, and `fastapi`.
  * Executes automated self-test verifying all 8 GPUs recognized by PyTorch CUDA runtime.
* **Duration:** ~90 seconds.

---

### STEP 5: Coordinate Multi-Node Ray Cluster (16 GPUs Unified Pool)

#### 5.1 Initialize Head Node on Node 0:
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Command:**
```bash
cd ~/demo
./03_start_ray_cluster.sh --head
```
* **What it does:** Starts Ray Head on port `6379`, launches the Ray Dashboard on port `8265`, and allocates 8 local GPUs.
* **Note:** The terminal outputs Node 0's internal IP (e.g. `10.128.0.41`).

#### 5.2 Connect Worker Node on Node 1:
* **Where:** 👉 **Terminal 3 (`[NODE 1]`)**
* **Command:**
```bash
cd ~/demo
./03_start_ray_cluster.sh --worker <NODE0_INTERNAL_IP>
```
* **What it does:** Registers Node 1's 8 GPUs with the Ray Head on port `6379`.
* **Verification:** Automatically runs `ray status`. Verify the pooled resources:
```text
Healthy:
 1 Node '10.128.0.41' (Head)
 1 Node '10.128.0.42' (Worker)
Resources:
  GPU: 16.0 / 16.0 GPUs
  CPU: 768.0 / 768.0 CPUs
  Memory: 2880.0 GiB Total System RAM
```

---

### STEP 6: Ingest Model Weights (Zero-Copy GCS FUSE vs Streaming)

* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**

#### Method A: Instant Zero-Copy Cloud Storage FUSE Mount (Recommended)
```bash
cd ~/demo
./04_get_weights.sh fuse
```
* **What it does:** Mounts `gs://mevreon-kimi-k3-weights` directly to `/mnt/models` via kernel-level FUSE caching in 2 seconds without downloading hundreds of gigabytes over disk.
* **Inspect Mounted Files:**
```bash
ls -lh /mnt/models/moonshotai/Kimi-K3/
```

#### Method B: Direct VPC High-Speed Streaming Download (Alternative)
```bash
cd ~/demo
./04_get_weights.sh download gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash
```
* **What it does:** Streams checkpoint shards across internal Google VPC channels at 5–10 Gbps wire speeds directly to local NVMe storage.

---

### STEP 7: Run Live 8-GPU Compute & Interconnect Benchmark
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Command:**
```bash
cd ~/demo
./05_run_smoke_benchmark.sh
```

* **What it does:**
  * Runs FP16 GEMM 8192×8192 matrix multiplication benchmark across all 8 GPUs.
  * Measures GDDR7 memory copy throughput.
  * Validates full 8×8 peer-to-peer (P2P) access matrix across host bridges.
* **Expected Output:**
  * **Compute:** **~295.2 TFLOPS per GPU** (8192×8192 GEMM in 3.7 ms)
  * **Memory Bandwidth:** **816.1 GB/s** GDDR7 copy throughput
  * **Interconnect:** Full **100% P2P** across all 8 devices

---

### STEP 8: Run the Master Benchmark Suite
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**

#### Option A: Run Fast Characterization Benchmark (2 Minutes)
```bash
cd ~/demo
./08_run_full_master_benchmark.sh --step 1
```
* **What it does:**
  * Executes Step 1 from `master_benchmark_cases.json` (Chunked Prefill Sizing under varying concurrency).
  * Evaluates chunk budgets (512 vs 2048 vs 8192 tokens).
  * Measures prompt tokens/sec, decode tokens/sec, and P95 latency in real time.

#### Option B: Launch Full 15-Step Master Campaign (Long-Running Background Sweep)
```bash
cd ~/demo
./08_run_full_master_benchmark.sh --all
```
* **What it does:** Executes all 15 stages sequentially (FP8 quantization, 128K context, 1M stress testing, PP rebalancing, Nsight traces).
* **Monitor Live Progress:**
```bash
tail -f ~/platform_benchmark_runs/*/logs/MASTER_BENCHMARK_RUN.log
```

---

### STEP 9: Serve the 48B Model Live & Execute Queries

#### 9.1 Start vLLM Serving Engine with Tensor Parallelism TP=8
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Command:**
```bash
cd ~/demo
./06_serve_48b_model.sh
```
* **Memory Architecture:**
  * 48B Parameter Model in BF16: `~96.0 GB Total`
  * Sharded across 8 GPUs: **~12.0 GB weights per GPU**
  * Remaining **~81.0 GB VRAM per GPU** allocated to PagedAttention KV-Cache Pool (**>640 GB cluster-wide KV-cache pool**).

#### 9.2 Execute Live Inference Query
In another terminal session or on Node 1:
* **Command:**
```bash
cd ~/demo
./07_test_inference_query.sh
```
* **Verification:** Returns live streaming chat completion response verifying active distributed serving.

---

### STEP 10: Resource Teardown & Cost Management
When finished, cleanly delete the cloud resources to avoid idle charges:

* **Where:** 👉 **Terminal 1 (`[LOCAL]`)**
* **Command:**
```bash
gcloud compute instances delete rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b --quiet
```

---

## 📁 Reference: Script Index (`Performance_Intelligence_Platform/demo/`)

| Script | Purpose | Where to Run |
| :--- | :--- | :--- |
| `01_provision_cluster.sh` | Provisions 2x G4 nodes (customizable names) | Terminal 1 (Local) |
| `02_install_stack.sh` | Installs uv, PyTorch sm_120, vLLM & Ray | Terminals 2 & 3 (Node 0 & 1) |
| `03_start_ray_cluster.sh` | Links nodes into unified 16-GPU Ray cluster | Terminals 2 & 3 (`--head` / `--worker`) |
| `04_get_weights.sh` | Ingests weights via GCS FUSE or VPC streaming | Terminal 2 (Node 0) |
| `05_run_smoke_benchmark.sh` | 8-GPU GEMM TFLOPS, GDDR7 & P2P bench | Terminal 2 (Node 0) |
| `06_serve_48b_model.sh` | Launches vLLM serving on 48B model (TP=8) | Terminal 2 (Node 0) |
| `07_test_inference_query.sh` | Sends live curl query to test inference latency | Terminal 2 (Node 0) |
| `08_run_full_master_benchmark.sh` | Launches master benchmark campaign (`--step 1` or `--all`) | Terminal 2 (Node 0) |
| `copy_scripts_to_nodes.ps1` | Deploys entire repo to both nodes (PowerShell) | Terminal 1 (Local) |
| `copy_scripts_to_nodes.sh` | Deploys entire repo to both nodes (Bash) | Terminal 1 (Local) |
