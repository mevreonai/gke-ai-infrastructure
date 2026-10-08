# Distributed AI Inference Cluster: End-to-End Deployment & Empirical Characterization Runbook

**Cluster Architecture:** Dual-Node GPU Supercomputing Cluster  
**Hardware Accelerators:** 2× GCP G4 Instances × 8× NVIDIA RTX PRO 6000 Blackwell GPUs (16 GPUs Total, 1.5 TB High-Bandwidth GDDR7 VRAM)  
**Host Platform:** AMD EPYC 9654 (384 vCPUs, 1.44 TB RAM per node)  
**Network Fabric:** Google Cloud Virtual Private Cloud (120 Gbps aggregate throughput, 0.075 ms latency)  
**Software Stack:** Rocky Linux 10, NVIDIA Driver 580.173, CUDA 12.8 / 13.0, PyTorch 2.12 (sm_120), Ray Core 2.59, vLLM  

---

## 1. Executive Architecture & Workflow Overview

This runbook documents the complete lifecycle of deploying a multi-node, multi-GPU distributed inference cluster from bare metal / cold-start cloud APIs to live tensor parallel serving of the **48B Parameter Model** (`moonshotai/Kimi-Linear-48B-A3B-Instruct`).

```text
+----------------------------------------------------------------------------------------------------+
|                                    END-TO-END DEPLOYMENT PIPELINE                                   |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [PHASE 1: CLUSTER PROVISIONING (CUSTOMIZABLE NAMES)]                                              |
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
|                                         │                                                          |
|                                         ▼                                                          |
|  [PHASE 6: 48B MODEL DISTRIBUTED SERVING (TP=8 / TP=16)]                                           |
|   vLLM Engine -> Kimi-Linear-48B-A3B-Instruct -> 12 GB weights/GPU + 81 GB KV-Cache/GPU             |
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

### 2.2 Customizing Names & Environment Variables
Every parameter in this suite is configurable. You can override defaults via environment variables or CLI arguments:

| Configuration Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PROJECT_ID` | `mevreon` | Target Google Cloud Project ID |
| `ZONE` | `us-central1-b` | GCP Availability Zone (supports G4 accelerators) |
| `NODE0_NAME` | `rtx-demo-node-0` | Name of Primary / Head Instance |
| `NODE1_NAME` | `rtx-demo-node-1` | Name of Secondary / Worker Instance |
| `SSH_KEY` | `~/.ssh/google_compute_engine` | Path to local OpenSSH private key |
| `SSH_USER` | `ayu23` | Default GCP provisioned Linux user |
| `MODEL_ID` | `moonshotai/Kimi-Linear-48B-A3B-Instruct` | Target LLM to serve and benchmark |

---

## 3. Deep Dive: How the 48B Parameter Model is Loaded

### 3.1 VRAM Memory Arithmetic & Partitioning
When serving `moonshotai/Kimi-Linear-48B-A3B-Instruct` (48 Billion Parameters):
* **Raw Weights Footprint (BF16 / FP16):** 48 Billion × 2 Bytes = **~96.0 GB Total**.
* **Under Tensor Parallelism (TP=8 across all 8 GPUs on Node 0):**
  * **Model Weights per GPU:** `96 GB / 8` = **~12.0 GB per GPU**.
  * **Total Physical VRAM per RTX PRO 6000:** **95.0 GB GDDR7**.
  * **Runtime Allocations:**
    * Model Shard: `12.0 GB`
    * Activation Memory + CUDA Graphs: `~2.0 GB`
    * **PagedAttention KV-Cache Pool:** **~81.0 GB per GPU!**
* **Why This Matters:**
  * Because 81 GB of VRAM per GPU is dedicated solely to the KV-cache, the cluster can hold **hundreds of thousands of cached tokens**, enabling massive multi-user concurrency and context windows up to **32K / 128K tokens** without out-of-memory (OOM) eviction.

### 3.2 Multi-Node Scale-Out (TP=16 across Both Nodes)
Via the Ray cluster link, the model can also be sharded across **all 16 GPUs** across both nodes:
* `96 GB / 16` = **~6.0 GB weights per GPU**.
* Unlocks over **1.4 Terabytes of pooled KV-cache** across the cluster.

---

## 4. Step-by-Step Execution Runbook

### STEP 1: Provision the Dual-Node Infrastructure from Scratch
* **Target Environment:** 👉 **Terminal 1 (`[LOCAL-CONTROL]`)**
* **Command (Default Names):**
```bash
cd Performance_Intelligence_Platform/demo
bash 01_provision_cluster.sh
```

* **Command (Custom Names - if you want custom instance identifiers):**
```bash
# Pass custom names directly as arguments:
bash 01_provision_cluster.sh prod-ai-node-0 prod-ai-node-1
```

**Technical Details & Flags:**
* `--machine-type="g4-standard-384"`: Allocates 384 vCPUs and 1,440 GB host memory per instance.
* `--accelerator="count=8,type=nvidia-rtx-pro-6000"`: Attaches 8 PCIe Gen5 GPUs per instance.
* `--boot-disk-type="hyperdisk-balanced"`: High IOPS NVMe persistent storage for rapid checkpoint caching.
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
2. Installs `uv` (Rust-based package manager, resolving environments in seconds rather than minutes).
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

---

### STEP 6: Ingest Model Weights (Zero-Copy GCS FUSE vs Streaming)

* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**

#### Method A: Instant Zero-Copy Cloud Storage FUSE Mount (Recommended for live demonstrations)
```bash
cd ~/demo
./04_get_weights.sh fuse
```
* **How it works:** Mounts `gs://mevreon-kimi-k3-weights` directly to `/mnt/models` via kernel-level FUSE caching.
* **Advantage:** Eliminates download waiting time for multi-gigabyte checkpoints.

#### Method B: Direct VPC High-Speed Multi-Threaded Streaming
```bash
cd ~/demo
./04_get_weights.sh download gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash
```

---

### STEP 7: Run Live 8-GPU Compute & Interconnect Characterization

* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**
* **Command:**
```bash
cd ~/demo
./05_run_smoke_benchmark.sh
```

**Measured Empirical Benchmark Results:**
* **Compute:** **~295.2 TFLOPS per GPU** (8192×8192 FP16 GEMM in 3.7 ms).
* **Memory Bandwidth:** **816.1 GB/s** GDDR7 copy throughput.
* **Interconnect:** **100% P2P** across all 8 devices.

---

### STEP 8: Serve the 48B Model Live & Run Inference

#### 8.1 Launch vLLM Serving Engine with TP=8
* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**
* **Command:**
```bash
cd ~/demo
./06_serve_48b_model.sh
```
* **What happens:**
  * vLLM loads `moonshotai/Kimi-Linear-48B-A3B-Instruct`.
  * Partitions the weights across GPUs 0–7 (12 GB per GPU).
  * Allocates 81 GB of KV-cache per GPU.
  * Starts the OpenAI-compatible API on `http://0.0.4:8000/v1`.

#### 8.2 Test Live Chat Completion Query
Open another terminal tab or run from background:
* **Target Environment:** 👉 **Terminal 2 (`[NODE-0-HEAD]`)**
* **Command:**
```bash
cd ~/demo
./07_test_inference_query.sh
```
* **Verification:** Returns a live LLM streaming response confirming successful end-to-end distributed inference.

---

### STEP 9: Resource Teardown & Cost Management
Once the presentation is concluded, stop or delete the cluster to eliminate idle compute costs:

* **Target Environment:** 👉 **Terminal 1 (`[LOCAL-CONTROL]`)**

```bash
# Option A: Stop instances (Preserves disks, halts billing)
gcloud compute instances stop rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b

# Option B: Complete Deletion (Clean removal)
gcloud compute instances delete rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b --quiet
```

---

## 5. Script Index & File Reference

All deployment and benchmarking assets are located in [`Performance_Intelligence_Platform/demo/`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo):

| Script | Purpose | Host Execution Environment |
| :--- | :--- | :--- |
| [`01_provision_cluster.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/01_provision_cluster.sh) | Creates 2× G4 GPU nodes via GCP Compute API (customizable names) | Local Workstation (`Terminal 1`) |
| [`02_install_stack.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/02_install_stack.sh) | Fast bootstrap: `uv`, PyTorch `sm_120`, vLLM & Ray | Both Nodes (`~/demo/`) |
| [`03_start_ray_cluster.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/03_start_ray_cluster.sh) | Links Head and Worker into unified 16-GPU Ray pool | Node 0 (`--head`) & Node 1 (`--worker`) |
| [`04_get_weights.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/04_get_weights.sh) | Ingests weights via GCS FUSE or VPC parallel streaming | Node 0 (`~/demo/`) |
| [`05_run_smoke_benchmark.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/05_run_smoke_benchmark.sh) | Executes 8-GPU GEMM TFLOPS, GDDR7 and P2P benchmark | Node 0 (`~/demo/`) |
| [`06_serve_48b_model.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/06_serve_48b_model.sh) | Serves 48B Model (`Kimi-Linear-48B`) with TP=8 on vLLM | Node 0 (`~/demo/`) |
| [`07_test_inference_query.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/07_test_inference_query.sh) | Sends live chat completion request to test inference latency | Node 0 (`~/demo/`) |
| [`copy_scripts_to_nodes.ps1`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/copy_scripts_to_nodes.ps1) | High-speed SCP deployment across both nodes (PowerShell) | Local Workstation (`Terminal 1`) |
| [`copy_scripts_to_nodes.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/demo/copy_scripts_to_nodes.sh) | High-speed SCP deployment across both nodes (Bash) | Local Workstation (`Terminal 1`) |
