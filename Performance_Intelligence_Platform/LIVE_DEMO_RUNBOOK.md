# Multi-Node Distributed GPU Cluster: Operational Execution Runbook

**Cluster Architecture:** Dual-Node GPU Supercomputing Cluster  
**Hardware Accelerators:** 2× GCP G4 Instances × 8× NVIDIA RTX PRO 6000 Blackwell GPUs (16 GPUs Total, 1.5 TB GDDR7 VRAM)  
**Host Platform:** AMD EPYC 9654 (384 vCPUs, 1.44 TB RAM per node)  
**Network Fabric:** Google Cloud VPC (120 Gbps aggregate throughput, 0.075 ms latency)  
**Software Stack:** Rocky Linux 10, NVIDIA Driver 580.173, CUDA 12.8 / 13.0, PyTorch 2.12 (sm_120), Ray Core 2.59, vLLM  

---

## 🖥️ Terminal Setup (3 Windows)

Open 3 terminal windows side-by-side:

* **Terminal 1 (`[LOCAL]`):** Local workstation terminal (`c:\Users\ayu23\OneDrive\Desktop\tpu\Performance_Intelligence_Platform\demo`)
* **Terminal 2 (`[NODE 0]`):** SSH session for Node 0 (Head Node / Master Orchestrator)
* **Terminal 3 (`[NODE 1]`):** SSH session for Node 1 (Worker Node)

---

## 📋 Concrete Example Reference Table

Throughout this runbook, concrete example values are shown so you can see the exact syntax:

| Parameter | Example Value | Where Used |
| :--- | :--- | :--- |
| **Project ID** | `mevreon` | Local GCP CLI |
| **Zone** | `us-central1-b` | Local GCP CLI |
| **Node 0 Name** | `rtx-demo-node-0` | Provisioning & SSH |
| **Node 1 Name** | `rtx-demo-node-1` | Provisioning & SSH |
| **Node 0 External IP** | `34.70.242.214` | Local SSH to Node 0 |
| **Node 1 External IP** | `35.225.118.110` | Local SSH to Node 1 |
| **Node 0 Internal IP** | `10.128.0.41` | Ray cluster join (`--worker`) & VPC traffic |
| **Node 1 Internal IP** | `10.128.0.42` | VPC inter-node traffic |
| **SSH Key Path** | `~/.ssh/google_compute_engine` | SSH authentication |
| **SSH Username** | `ayu23` | Remote Linux account |

---

## ⚡ Step-by-Step Technical Instructions

---

### STEP 1: Provision the 2 VMs from Scratch

* **Location:** 👉 **Terminal 1 (`[LOCAL]`)**
* **Working Directory:** `Performance_Intelligence_Platform/demo`

#### Command:
```bash
cd Performance_Intelligence_Platform/demo
bash 01_provision_cluster.sh
```

*(Optional: To use custom instance names, pass them as arguments: `bash 01_provision_cluster.sh my-node-0 my-node-1`)*

#### Expected Output:
```text
Created [https://www.googleapis.com/compute/v1/projects/mevreon/zones/us-central1-b/instances/rtx-demo-node-0].
Created [https://www.googleapis.com/compute/v1/projects/mevreon/zones/us-central1-b/instances/rtx-demo-node-1].

NAME              ZONE          STATUS   INTERNAL_IP  EXTERNAL_IP
rtx-demo-node-0   us-central1-b RUNNING  10.128.0.41  34.70.242.214
rtx-demo-node-1   us-central1-b RUNNING  10.128.0.42  35.225.118.110
```

> **Action:** Copy down the two **EXTERNAL_IP** addresses and the **INTERNAL_IP** of Node 0 from the table output.

---

### STEP 2: Connect via SSH to Both Nodes

#### 2.1 Connect to Node 0 (Terminal 2)
* **Location:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Syntax:** `ssh -i ~/.ssh/google_compute_engine ayu23@<NODE0_EXTERNAL_IP>`
* **Exact Command Example:**
```bash
ssh -i ~/.ssh/google_compute_engine ayu23@34.70.242.214
```

#### 2.2 Verify Node 0 Hardware & GPU Discovery
Run on **Terminal 2**:
```bash
nvidia-smi
```
**Expected Output:** Displays 8× NVIDIA RTX PRO 6000 Blackwell GPUs, 97887 MiB VRAM each, Driver 580.173, CUDA 13.0.

```bash
nvidia-smi topo -m
```
**Expected Output:** Displays the dual-NUMA host bridge PCIe topology (GPUs 0–3 on NUMA 0 with PIX links, GPUs 4–7 on NUMA 1 with PIX links).

#### 2.3 Connect to Node 1 (Terminal 3)
* **Location:** 👉 **Terminal 3 (`[NODE 1]`)**
* **Syntax:** `ssh -i ~/.ssh/google_compute_engine ayu23@<NODE1_EXTERNAL_IP>`
* **Exact Command Example:**
```bash
ssh -i ~/.ssh/google_compute_engine ayu23@35.225.118.110
```

---

### STEP 3: Copy the Platform & Demo Suite to Both Nodes

* **Location:** 👉 **Terminal 1 (`[LOCAL]`)**

#### Command Syntax:
* **On PowerShell (Windows):**
  * `.\copy_scripts_to_nodes.ps1 <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>`
* **On Bash (Linux / macOS):**
  * `./copy_scripts_to_nodes.sh <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>`

#### Exact Command Example:

**PowerShell:**
```powershell
.\copy_scripts_to_nodes.ps1 34.70.242.214 35.225.118.110
```

**Bash:**
```bash
./copy_scripts_to_nodes.sh 34.70.242.214 35.225.118.110
```

#### Expected Output:
```text
--> Deploying Performance_Intelligence_Platform to Node 0 (34.70.242.214)...
--> Deploying Performance_Intelligence_Platform to Node 1 (35.225.118.110)...
--> SUCCESS: Full suite deployed to ~/Performance_Intelligence_Platform and symlinked to ~/demo
```

---

### STEP 4: Install System Dependencies, PyTorch, vLLM & Ray

Run this command **simultaneously** in both remote SSH sessions:

#### On Node 0:
* **Location:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Exact Command:**
```bash
cd ~/demo
./02_install_stack.sh
```

#### On Node 1:
* **Location:** 👉 **Terminal 3 (`[NODE 1]`)**
* **Exact Command:**
```bash
cd ~/demo
./02_install_stack.sh
```

#### What this executes:
1. Installs `iperf3`, `git`, and `pciutils` via `dnf`.
2. Installs `uv` package manager into `~/.local/bin/`.
3. Creates virtual environment at `~/vllm_env`.
4. Installs PyTorch nightly with CUDA 12.8 and native `sm_120` Blackwell kernel support.
5. Installs `vllm`, `ray[default]`, `triton`, `transformers`, `huggingface-hub`, and `fastapi`.
6. Executes internal self-test verifying all 8 GPUs.

#### Expected Output (on both nodes):
```text
[DEMO] Verification & Self-Test
 Python Version : 3.12.14
 PyTorch Version: 2.12.0.dev20260408+cu128
 CUDA Runtime   : 12.8
 CUDA Available : True
 GPU Count      : 8 GPUs detected
   -> GPU 0: NVIDIA RTX PRO 6000 (sm_120) | 95.0 GB GDDR7
   ...
   -> GPU 7: NVIDIA RTX PRO 6000 (sm_120) | 95.0 GB GDDR7
 STATUS: Ready for Multi-Node Ray Cluster & vLLM Serving!
```

---

### STEP 5: Form the Multi-Node 16-GPU Ray Cluster

#### 5.1 Start Ray Head on Node 0
* **Location:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Exact Command:**
```bash
cd ~/demo
./03_start_ray_cluster.sh --head
```

**Expected Output:**
```text
[DEMO] Initializing Ray Cluster HEAD on Node 0...
--> Ray HEAD is running on 10.128.0.41:6379
--> Ray Dashboard: http://10.128.0.41:8265
======================================================================
NOW RUN ON NODE 1:
    ./03_start_ray_cluster.sh --worker 10.128.0.41
======================================================================
```

#### 5.2 Join Ray Worker on Node 1
* **Location:** 👉 **Terminal 3 (`[NODE 1]`)**
* **Syntax:** `./03_start_ray_cluster.sh --worker <NODE0_INTERNAL_IP>`
* **Exact Command Example:**
```bash
cd ~/demo
./03_start_ray_cluster.sh --worker 10.128.0.41
```

#### 5.3 Verify Unified 16-GPU Pool
Check the output printed at the end of the script:
```text
====================== Ray Cluster Status ======================
Healthy:
 1 Node '10.128.0.41' (Head)
 1 Node '10.128.0.42' (Worker)
----------------------------------------------------------------
Resources:
  GPU: 16.0 / 16.0 GPUs
  CPU: 768.0 / 768.0 CPUs
  Memory: 2880.0 GiB Total System RAM
```
*(Confirms that all 16 GPUs across both VMs are pooled into a single distributed runtime).*

---

### STEP 6: Mount / Stream Model Checkpoints

* **Location:** 👉 **Terminal 2 (`[NODE 0]`)**

#### Method A: Instant Zero-Copy Cloud Storage FUSE Mount (Recommended: 2 Seconds)
* **Exact Command:**
```bash
cd ~/demo
./04_get_weights.sh fuse
```
* **Verify files are mounted:**
```bash
ls -lh /mnt/models/moonshotai/Kimi-K3/
```
*(Model checkpoint shards are mounted directly from GCS into filesystem with zero disk copy wait time).*

#### Method B: Direct VPC High-Speed Multi-Threaded Streaming
* **Syntax:** `./04_get_weights.sh download <GCS_BUCKET_URI>`
* **Exact Command Example:**
```bash
cd ~/demo
./04_get_weights.sh download gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash
```

---

### STEP 7: Run Live 8-GPU Compute & Interconnect Characterization

* **Location:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Exact Command:**
```bash
cd ~/demo
./05_run_smoke_benchmark.sh
```

#### Expected Benchmark Output:
```text
======================================================================
  NVIDIA RTX PRO 6000 BLACKWELL 8-GPU LIVE HARDWARE BENCHMARK
======================================================================
[1/3] Benchmarking FP16 GEMM Across All 8 GPUs (8192x8192 Matrix Multiply)...
  GPU 0 [NVIDIA RTX PRO 6000]: 294.7 TFLOPS | Latency: 3.73 ms
  GPU 1 [NVIDIA RTX PRO 6000]: 291.5 TFLOPS | Latency: 3.77 ms
  GPU 2 [NVIDIA RTX PRO 6000]: 298.1 TFLOPS | Latency: 3.69 ms
  GPU 3 [NVIDIA RTX PRO 6000]: 295.8 TFLOPS | Latency: 3.72 ms
  GPU 4 [NVIDIA RTX PRO 6000]: 294.5 TFLOPS | Latency: 3.73 ms
  GPU 5 [NVIDIA RTX PRO 6000]: 297.7 TFLOPS | Latency: 3.69 ms
  GPU 6 [NVIDIA RTX PRO 6000]: 292.4 TFLOPS | Latency: 3.76 ms
  GPU 7 [NVIDIA RTX PRO 6000]: 297.0 TFLOPS | Latency: 3.70 ms

[2/3] Peer-to-Peer Access Matrix:
     G00  G01  G02  G03  G04  G05  G06  G07
G00: SELF  P2P  P2P  P2P  P2P  P2P  P2P  P2P
G01:  P2P SELF  P2P  P2P  P2P  P2P  P2P  P2P
... (100% P2P across all 8 devices)

[3/3] GDDR7 Memory Copy Bandwidth...
  GPU 0 GDDR7 Memory Copy Bandwidth: 816.1 GB/s
======================================================================
  ALL 8 BLACKWELL GPUS VALIDATED: 100% HEALTHY & DEMO-READY!
======================================================================
```

---

### STEP 8: Run the Master Benchmark Suite

* **Location:** 👉 **Terminal 2 (`[NODE 0]`)**

#### Option A: Quick Characterization Run (Step 1: Chunked Prefill Sizing)
* **Exact Command:**
```bash
cd ~/demo
./08_run_full_master_benchmark.sh --step 1
```
* **What this executes:**
  * Runs the automated test case from `master_benchmark_cases.json`.
  * Measures prompt prefill latency, decode throughput, and concurrency scaling.
  * Streams real-time tokens/sec and P95 latency metrics directly to stdout.

#### Option B: Launch Full 15-Step Master Campaign
* **Exact Command:**
```bash
cd ~/demo
./08_run_full_master_benchmark.sh --all
```
* **To monitor progress in real time:**
```bash
tail -f ~/platform_benchmark_runs/*/logs/MASTER_BENCHMARK_RUN.log
```

---

### STEP 9: Serve the 48B Model Live & Execute Queries

#### 9.1 Start vLLM Serving Engine with TP=8
* **Location:** 👉 **Terminal 2 (`[NODE 0]`)**
* **Exact Command:**
```bash
cd ~/demo
./06_serve_48b_model.sh
```
* **Memory Architecture:**
  * 48B Parameter Model Footprint: `~96 GB` in BF16.
  * Sharded across 8 GPUs: **12 GB weights per GPU**.
  * Remaining VRAM: **~81 GB per GPU** dedicated to PagedAttention KV-Cache (>640 GB cluster pool).
  * API Endpoint: `http://0.0.0.0:8000/v1`

#### 9.2 Execute Test Query
Open a new terminal tab or run from background:
* **Exact Command:**
```bash
cd ~/demo
./07_test_inference_query.sh
```

**Or run direct curl:**
```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-Linear-48B-A3B-Instruct",
    "messages": [{"role": "user", "content": "Explain tensor parallelism in 2 sentences."}],
    "max_tokens": 64
  }' | jq .
```

---

### STEP 10: Cluster Teardown (Post-Presentation)

* **Location:** 👉 **Terminal 1 (`[LOCAL]`)**

#### Stop Instances (Halts billing, preserves persistent disks):
```bash
gcloud compute instances stop rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b
```

#### Delete Instances Completely:
```bash
gcloud compute instances delete rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b --quiet
```

---

## 📁 Summary Reference of All Commands

| Step | Action | Environment | Exact Command Example |
| :---: | :--- | :--- | :--- |
| **1** | Provision 2 VMs | Terminal 1 (`Local`) | `bash 01_provision_cluster.sh` |
| **2** | SSH Node 0 | Terminal 2 (`Node 0`) | `ssh -i ~/.ssh/google_compute_engine ayu23@34.70.242.214` |
| **2** | SSH Node 1 | Terminal 3 (`Node 1`) | `ssh -i ~/.ssh/google_compute_engine ayu23@35.225.118.110` |
| **3** | Copy Demo Suite | Terminal 1 (`Local`) | `.\copy_scripts_to_nodes.ps1 34.70.242.214 35.225.118.110` |
| **4** | Install Runtime | Terminals 2 & 3 | `cd ~/demo && ./02_install_stack.sh` |
| **5** | Start Ray Head | Terminal 2 (`Node 0`) | `cd ~/demo && ./03_start_ray_cluster.sh --head` |
| **5** | Join Ray Worker | Terminal 3 (`Node 1`) | `cd ~/demo && ./03_start_ray_cluster.sh --worker 10.128.0.41` |
| **6** | Mount Model Weights | Terminal 2 (`Node 0`) | `cd ~/demo && ./04_get_weights.sh fuse` |
| **7** | Hardware Benchmark | Terminal 2 (`Node 0`) | `cd ~/demo && ./05_run_smoke_benchmark.sh` |
| **8** | Master Benchmark | Terminal 2 (`Node 0`) | `cd ~/demo && ./08_run_full_master_benchmark.sh --step 1` |
| **9** | Serve 48B Model | Terminal 2 (`Node 0`) | `cd ~/demo && ./06_serve_48b_model.sh` |
| **9** | Test Query | Terminal 2 (`Node 0`) | `cd ~/demo && ./07_test_inference_query.sh` |
| **10** | Teardown Cluster | Terminal 1 (`Local`) | `gcloud compute instances delete rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b --quiet` |
