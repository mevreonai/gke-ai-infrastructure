# Distributed AI Inference Cluster: End-to-End Deployment & Empirical Characterization Runbook

**Cluster Architecture:** Dual-Node GPU Supercomputing Cluster  
**Hardware Accelerators:** 2× GCP G4 Instances × 8× NVIDIA RTX PRO 6000 Blackwell GPUs (16 GPUs Total, 1.5 TB High-Bandwidth GDDR7 VRAM)  
**Host Platform:** AMD EPYC 9654 (384 vCPUs, 1.44 TB RAM per node)  
**Network Fabric:** Google Cloud Virtual Private Cloud (120 Gbps aggregate throughput, 0.075 ms latency)  
**Software Stack:** Rocky Linux 10, NVIDIA Driver 580.173, CUDA 12.8 / 13.0, PyTorch 2.12 (sm_120), Ray Core 2.59, vLLM  

---

## 1. Executive Architecture & Workflow Overview

This runbook documents the complete lifecycle of deploying a multi-node, multi-GPU distributed inference cluster from bare metal / cold-start cloud APIs to live tensor parallel serving and hardware qualification.

```text
+----------------------------------------------------------------------------------------------------+
|                                    END-TO-END DEPLOYMENT PIPELINE                                   |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [PHASE 1: CLUSTER PROVISIONING]                                                                   |
|   gcloud Compute API -> 2x g4-standard-384 instances -> 16x RTX PRO 6000 Ada/Blackwell GPUs        |
|                                         │                                                          |
|                                         ▼                                                          |
|  [PHASE 2: SECURE LINKAGE & REPOSITORY DISPATCH]                                                   |
|   OpenSSH terminal sessions -> Deploy deployment suite via high-throughput SCP                     |
|                                         │                                                          |
|                                         ▼                                                          |
|  [PHASE 3: SOFTWARE STACK BOOTSTRAP]                                                               |
|   Astral uv Package Manager -> Isolated virtualenv -> PyTorch CUDA 12.8 sm_120 -> Ray & vLLM       |
|                                         │                                                          |
|                                         ▼                                                          |
|  [PHASE 4: MULTI-NODE DISTRIBUTED CLUSTER LINKAGE]                                                 |
|   Node 0 Ray Head (Port 6379) <==== 120 Gbps VPC ====> Node 1 Ray Worker -> 16 GPU Unified Pool     |
|                                         │                                                          |
|                                         ▼                                                          |
|  [PHASE 5: ZERO-COPY WEIGHTS INGESTION & HARDWARE BENCHMARK]                                       |
|   GCS FUSE Mount -> Direct checkpoint access -> 8-GPU GEMM Benchmark (~295 TFLOPS/GPU, 816 GB/s)   |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Pre-Flight Preparation & Workspace Layout

### 2.1 Terminal Layout (Recommended: 3 Split Windows)
To maintain complete visibility and seamless execution during a live demonstration, arrange 3 terminal tabs side-by-side:

| Terminal Window | Identifier | Role & Execution Scope | Working Path |
| :--- | :--- | :--- | :--- |
| **Terminal 1** | `[LOCAL-CONTROL]` | Local Workstation: Infrastructure API calls & SCP dispatches | `Performance_Intelligence_Platform/demo/` |
| **Terminal 2** | `[NODE-0-HEAD]` | Primary Node 0: Head Node, Ray Master, Ingestion & Serving | Remote SSH Session (`ayu23@<NODE0_IP>`) |
| **Terminal 3** | `[NODE-1-WORKER]` | Secondary Node 1: Worker Node, Distributed Acceleration | Remote SSH Session (`ayu23@<NODE1_IP>`) |

### 2.2 Credentials & Pre-requisites Verification
Ensure Google Cloud authentication and SSH keys are active on your local machine:
```bash
gcloud auth list
# Expected: sudarshan@mevreon.ai (Active)
```

---

## 3. Step-by-Step Execution Runbook

### STEP 1: Provision the Dual-Node Infrastructure from Scratch
* **Target Environment:** 👉 **Terminal 1 (`[LOCAL-CONTROL]`)**
* **Command:**
```bash
cd Performance_Intelligence_Platform/demo
bash 01_provision_cluster.sh
```

**Technical Details & Flags:**
* `--machine-type="g4-standard-384"`: Allocates 384 vCPUs and 1,440 GB host memory per instance.
* `--accelerator="count=8,type=nvidia-rtx-pro-6000"`: Attaches 8 PCIe Gen5 GPUs per instance.
* `--boot-disk-type="hyperdisk-balanced"`: Provides high IOPS NVMe persistent storage for rapid checkpoint caching.
* `--image="rocky-linux-10-optimized-gcp-nvidia-580-v20260910"`: Enterprise Linux image with production NVIDIA 580 kernel drivers pre-compiled.
* `--provisioning-model=SPOT`: Utilizes spot capacity for cost efficiency while maintaining performance parity.

**Expected Output:**
```text
Created [rtx-demo-node-0].
Created [rtx-demo-node-1].

NAME              ZONE          STATUS   INTERNAL_IP  EXTERNAL_IP
rtx-demo-node-0   us-central1-b RUNNING  10.128.0.41  34.70.242.214
rtx-demo-node-1   us-central1-b RUNNING  10.128.0.42  35.225.118.110
```
*(Record the external IPs printed for the subsequent steps).*

---

### STEP 2: Establish SSH Connectivity & Hardware Discovery

#### 2.1 Connect to Primary Node 0
* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**
* **Command:**
```bash
ssh -i ~/.ssh/google_compute_engine ayu23@<NODE0_EXTERNAL_IP>
```

#### 2.2 Inspect Topology & Device Health
On Node 0, run hardware qualification probes:
```bash
nvidia-smi
```
* **Verification:** Confirms 8× NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs (96 GB GDDR7 VRAM each, 760 GB total node VRAM, Driver 580.173, CUDA 13.0).

```bash
nvidia-smi topo -m
```
* **Verification:** Displays the dual-NUMA host bridge interconnect matrix:
  * NUMA Node 0: GPUs 0–3 (PCIe PIX/NODE affinity)
  * NUMA Node 1: GPUs 4–7 (PCIe PIX/NODE affinity)
  * Inter-NUMA: SYS bus links across the AMD EPYC SMP interconnect.

#### 2.3 Connect to Secondary Node 1
* **Target Environment:** 👉 **Terminal 3 (`[NODE-1-WORKER]`)**
* **Command:**
```bash
ssh -i ~/.ssh/google_compute_engine ayu23@<NODE1_EXTERNAL_IP>
```

---

### STEP 3: Dispatch Deployment Suite to Remote Nodes
* **Target Environment:** 👉 **Terminal 1 (`[LOCAL-CONTROL]`)**
* **Command:**

**Using PowerShell (Windows):**
```powershell
.\copy_scripts_to_nodes.ps1 <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
```

**Using Bash / Linux / macOS:**
```bash
./copy_scripts_to_nodes.sh <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
```

**Using direct OpenSSH / SCP:**
```bash
scp -i ~/.ssh/google_compute_engine -r . ayu23@<NODE0_EXTERNAL_IP>:~/demo/
scp -i ~/.ssh/google_compute_engine -r . ayu23@<NODE1_EXTERNAL_IP>:~/demo/
```
* **Verification:** Deploys the self-contained execution harness into `~/demo/` on both nodes and sets executable permissions (`chmod +x`).

---

### STEP 4: Automated Software Stack & Driver Runtime Bootstrap
Execute this step simultaneously across both active terminal sessions:

* **Target Environments:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)** and **Terminal 3 (`[NODE-1-WORKER]`)**
* **Command:**
```bash
cd ~/demo
./02_install_stack.sh
```

**What this script automates:**
1. Installs enterprise networking and PCIe diagnostic packages (`iperf3`, `git`, `pciutils`).
2. Installs `uv` (Rust-based ultra-fast package manager, resolving environments in seconds rather than minutes).
3. Creates a dedicated virtual environment at `~/vllm_env`.
4. Installs PyTorch nightly with native CUDA 12.8 / `sm_120` (Blackwell micro-architecture support).
5. Installs `vllm`, `ray[default]`, `triton`, `transformers`, `huggingface-hub`, and `fastapi`.
6. Executes an automated sanity test validating CUDA tensor allocation across all 8 devices.

**Expected Output:**
```text
[DEMO] Verification & Self-Test
 Python Version : 3.12.14
 PyTorch Version: 2.12.0.dev20260408+cu128
 CUDA Runtime   : 12.8
 CUDA Available : True
 GPU Count      : 8 GPUs detected
   -> GPU 0: NVIDIA RTX PRO 6000 (sm_120) | 95.0 GB GDDR7
   -> GPU 1: NVIDIA RTX PRO 6000 (sm_120) | 95.0 GB GDDR7
   ...
   -> GPU 7: NVIDIA RTX PRO 6000 (sm_120) | 95.0 GB GDDR7
 STATUS: Ready for Multi-Node Ray Cluster & vLLM Serving!
```

---

### STEP 5: Coordinate Multi-Node Ray Cluster

#### 5.1 Initialize Head Node on Node 0
* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**
* **Command:**
```bash
cd ~/demo
./03_start_ray_cluster.sh --head
```
* **Output:** Starts Ray Head on port `6379` and initializes the Ray Dashboard on port `8265`.
* *(Note the internal IP printed in the terminal, e.g., `10.128.0.41`).*

#### 5.2 Join Worker Node on Node 1
* **Target Environment:** 👉 **Terminal 3 (`[NODE-1-WORKER]`)**
* **Command:**
```bash
cd ~/demo
./03_start_ray_cluster.sh --worker <NODE0_INTERNAL_IP>
```

#### 5.3 Verify Unified 16-GPU Cluster Pool
The script automatically executes `ray status`. Verify the pooled hardware resources:
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
* **Significance:** 16 accelerators and 2.88 TB of RAM are now unified under a single distributed execution plane.

---

### STEP 6: Ingest Model Weights (Zero-Copy GCS FUSE vs Streaming)

* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**

#### Method A: Instant Zero-Copy Cloud Storage FUSE Mount (Recommended for live demonstrations)
```bash
cd ~/demo
./04_get_weights.sh fuse
```
* **How it works:** Mounts `gs://mevreon-kimi-k3-weights` directly to `/mnt/models` via kernel-level FUSE caching.
* **Advantage:** Eliminates download waiting time for multi-gigabyte/terabyte checkpoints. Models are served on-demand.
* **Inspect Mounted Files:**
```bash
ls -lh /mnt/models/moonshotai/Kimi-K3/
```

#### Method B: Direct VPC High-Speed Multi-Threaded Streaming
```bash
cd ~/demo
./04_get_weights.sh download gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash
```
* **How it works:** Streams checkpoint shards across internal Google VPC channels at 5–10 Gbps wire speeds directly to local NVMe storage.

---

### STEP 7: Run Live 8-GPU Compute & Interconnect Characterization

* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**
* **Command:**
```bash
cd ~/demo
./05_run_smoke_benchmark.sh
```

**Measured Empirical Benchmark Results:**

```text
======================================================================
  NVIDIA RTX PRO 6000 BLACKWELL 8-GPU LIVE HARDWARE BENCHMARK
======================================================================
PyTorch: 2.12.0.dev20260408+cu128 | CUDA: 12.8 | Devices: 8

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
G02:  P2P  P2P SELF  P2P  P2P  P2P  P2P  P2P
G03:  P2P  P2P  P2P SELF  P2P  P2P  P2P  P2P
G04:  P2P  P2P  P2P  P2P SELF  P2P  P2P  P2P
G05:  P2P  P2P  P2P  P2P  P2P SELF  P2P  P2P
G06:  P2P  P2P  P2P  P2P  P2P  P2P SELF  P2P
G07:  P2P  P2P  P2P  P2P  P2P  P2P  P2P SELF

[3/3] GDDR7 Memory Copy Bandwidth...
  GPU 0 GDDR7 Memory Copy Bandwidth: 816.1 GB/s
======================================================================
  ALL 8 BLACKWELL GPUS VALIDATED: 100% HEALTHY & DEMO-READY!
======================================================================
```

---

### STEP 8: Resource Teardown & Cost Management
Once the presentation is concluded, stop or delete the cluster to eliminate idle compute costs:

* **Target Environment:** 👉 **Terminal 1 (`[LOCAL-CONTROL]`)**

```bash
# Option A: Stop instances (Preserves disks, halts billing)
gcloud compute instances stop rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b

# Option B: Complete Deletion (Clean removal)
gcloud compute instances delete rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b --quiet
```

---

## 4. Script Index & File Reference

All deployment and benchmarking assets are located in [`Performance_Intelligence_Platform/demo/`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo):

| Script | Purpose | Host Execution Environment |
| :--- | :--- | :--- |
| [`01_provision_cluster.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/01_provision_cluster.sh) | Creates 2× G4 GPU nodes via GCP Compute API | Local Workstation (`Terminal 1`) |
| [`02_install_stack.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/02_install_stack.sh) | Fast bootstrap: `uv`, PyTorch `sm_120`, vLLM & Ray | Both Nodes (`~/demo/`) |
| [`03_start_ray_cluster.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/03_start_ray_cluster.sh) | Links Head and Worker into unified 16-GPU Ray pool | Node 0 (`--head`) & Node 1 (`--worker`) |
| [`04_get_weights.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/04_get_weights.sh) | Ingests weights via GCS FUSE or VPC parallel streaming | Node 0 (`~/demo/`) |
| [`05_run_smoke_benchmark.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/05_run_smoke_benchmark.sh) | Executes 8-GPU GEMM TFLOPS, GDDR7 and P2P benchmark | Node 0 (`~/demo/`) |
| [`copy_scripts_to_nodes.ps1`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/copy_scripts_to_nodes.ps1) | High-speed SCP deployment across both nodes (PowerShell) | Local Workstation (`Terminal 1`) |
| [`copy_scripts_to_nodes.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/copy_scripts_to_nodes.sh) | High-speed SCP deployment across both nodes (Bash) | Local Workstation (`Terminal 1`) |
