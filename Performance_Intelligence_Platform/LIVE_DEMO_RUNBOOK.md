# Multi-Node Distributed AI Inference Cluster: Master Presentation & Live Benchmark Runbook

**Target Architecture:** Dual-Node GPU Supercomputing Cluster  
**Hardware Accelerators:** 2× GCP G4 Instances × 8× NVIDIA RTX PRO 6000 Blackwell GPUs (16 GPUs Total, 1.5 TB High-Bandwidth GDDR7 VRAM)  
**Host Platform:** AMD EPYC 9654 (384 vCPUs, 1.44 TB RAM per node)  
**Network Fabric:** Google Cloud Virtual Private Cloud (120 Gbps aggregate throughput, 0.075 ms latency)  
**Software Stack:** Rocky Linux 10, NVIDIA Driver 580.173, CUDA 12.8 / 13.0, PyTorch 2.12 (sm_120), Ray Core 2.59, vLLM  

---

## 🎙️ Meeting Presentation Flow (What to Say & Do Chronologically)

When presenting in the meeting, follow this 4-act narrative structure:

```text
+----------------------------------------------------------------------------------------------------+
|                                    MEETING PRESENTATION STRUCTURE                                   |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [ACT 1: THE COLD START & PROVISIONING] (Minutes 00:00 - 02:00)                                    |
|   "We are spinning up a 16-GPU cluster with 1.5 TB GDDR7 memory from scratch in real time."        |
|                                         │                                                          |
|                                         ▼                                                          |
|  [ACT 2: TOPOLOGY & CLUSTER FABRIC] (Minutes 02:00 - 04:00)                                        |
|   "Notice our 8x8 P2P fabric and our inter-node 120 Gbps VPC interconnect running at 0.075 ms."     |
|                                         │                                                          |
|                                         ▼                                                          |
|  [ACT 3: RUNTIME BOOTSTRAP & DISTRIBUTED RAY LINKAGE] (Minutes 04:00 - 06:00)                      |
|   "Using uv, we bootstrap CUDA 12.8 with Blackwell sm_120 support and pool all 16 GPUs in Ray."     |
|                                         │                                                          |
|                                         ▼                                                          |
|  [ACT 4: 48B MODEL INGESTION & MASTER BENCHMARK RUN] (Minutes 06:00 - 10:00)                       |
|   "We mount our model via zero-copy FUSE and trigger our multi-phase benchmark suite live."         |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 🖥️ Screen & Terminal Workspace Layout

Before sharing your screen, arrange **3 Terminal Windows side-by-side**:

```text
+--------------------------+--------------------------+--------------------------+
|  TERMINAL 1: LOCAL       |   TERMINAL 2: NODE 0     |  TERMINAL 3: NODE 1      |
|                          |                          |                          |
|   Your laptop shell      |     Primary Head (SSH)   |    Secondary Worker (SSH)|
|  Provisioning & Copying  |     Master & Serving     |      Ray Worker Pool     |
+--------------------------+--------------------------+--------------------------+
```

---

## 🚀 Step-by-Step Execution Guide

### STEP 1: Provision the 2 VMs Live
* **Where:** 👉 **Terminal 1 (`[LOCAL]`)**
* **What to say:**  
  *"I'm initiating the cluster provisioning on Google Cloud G4. We are requesting two `g4-standard-384` instances with 8 NVIDIA RTX PRO 6000 Blackwell GPUs each, backed by high-throughput NVMe hyperdisks."*
* **Command:**
```bash
cd Performance_Intelligence_Platform/demo
bash 01_provision_cluster.sh
```
*(Takes ~90 seconds. Once completed, note down the External IPs printed in the summary table).*

---

### STEP 2: Connect via SSH & Verify Hardware Topology
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)** and **Terminal 3 (`[NODE 1]`)**
* **What to say:**  
  *"Both nodes are active. Let's inspect the hardware primitives and PCIe bus hierarchy."*
* **Commands:**
  * In **Terminal 2**:
    ```bash
    ssh -i ~/.ssh/google_compute_engine ayu23@<NODE0_EXTERNAL_IP>
    ```
  * In **Terminal 3**:
    ```bash
    ssh -i ~/.ssh/google_compute_engine ayu23@<NODE1_EXTERNAL_IP>
    ```
* **In Terminal 2, show the live hardware status:**
  ```bash
  nvidia-smi
  nvidia-smi topo -m
  ```
  👉 **Point out:**
  * All 8 GPUs recognized with **96 GB GDDR7 VRAM each** (760 GB total node capacity).
  * Direct dual-NUMA host bridge architecture with PCIe PIX links between adjacent accelerators.

---

### STEP 3: Deploy the Platform & Demo Suite
* **Where:** 👉 **Terminal 1 (`[LOCAL]`)**
* **What to say:**  
  *"We are now deploying our complete Performance Intelligence Platform repository and execution suite onto both nodes."*
* **Commands:**
  * **On Windows PowerShell:**
    ```powershell
    .\copy_scripts_to_nodes.ps1 <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
    ```
  * **On Bash / Linux / macOS:**
    ```bash
    ./copy_scripts_to_nodes.sh <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
    ```

---

### STEP 4: High-Speed Software Stack Bootstrap
Run this simultaneously on **both nodes**:
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)** and **Terminal 3 (`[NODE 1]`)**
* **What to say:**  
  *"Rather than a slow standard install, we use `uv` and pre-compiled wheels to install our isolated virtual environment, PyTorch with CUDA 12.8 Blackwell `sm_120` support, vLLM, and Ray in under 90 seconds."*
* **Command on Both Nodes:**
```bash
cd ~/demo
./02_install_stack.sh
```
👉 **Expected confirmation:** Outputs 8 GPUs detected with `sm_120` architecture, CUDA 12.8 runtime, and vLLM + Ray paths confirmed.

---

### STEP 5: Form the Multi-Node 16-GPU Ray Cluster
* **What to say:**  
  *"We now link Node 0 and Node 1 across the 120 Gbps VPC interconnect into a unified distributed computing mesh."*

#### 5.1 On Node 0 (Terminal 2):
```bash
cd ~/demo
./03_start_ray_cluster.sh --head
```
*(Notice Node 0's Internal IP printed on screen, e.g. `10.128.0.41`)*

#### 5.2 On Node 1 (Terminal 3):
```bash
cd ~/demo
./03_start_ray_cluster.sh --worker <NODE0_INTERNAL_IP>
```
👉 **Point out the Ray Status Output:**
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

### STEP 6: Mount the 48B Model Checkpoint (Zero-Copy)
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **What to say:**  
  *"For model weights ingestion, rather than waiting 20 minutes to copy a 100GB+ checkpoint over disk, we use Cloud Storage FUSE. The weights are mounted directly into kernel memory in 2 seconds."*
* **Command:**
```bash
cd ~/demo
./04_get_weights.sh fuse
```
* **Show the mounted files:**
```bash
ls -lh /mnt/models/moonshotai/Kimi-K3/
```

---

### STEP 7: Run Live Compute & P2P Hardware Characterization
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **What to say:**  
  *"Before launching model inference, we validate our hardware primitives: FP16 GEMM compute throughput, GDDR7 copy bandwidth, and P2P interconnect latency."*
* **Command:**
```bash
cd ~/demo
./05_run_smoke_benchmark.sh
```
👉 **Point out the Live Metrics:**
* **Compute:** **~295 TFLOPS per GPU** (8192×8192 GEMM in 3.7 ms).
* **Memory Bandwidth:** **816.1 GB/s** GDDR7 copy throughput.
* **Interconnect:** Full **100% P2P** across all 8 devices.

---

### STEP 8: Running the Master Benchmark Suite

There are two ways to showcase the benchmark suite depending on your meeting agenda:

#### Option A: Run the Live Characterization Benchmark (Best for 2-Minute Live Demos)
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **What to say:**  
  *"Now we trigger our automated characterization run for Step 1 (Chunked Prefill Sizing under varying concurrency). Watch the engine execute warmups and measure token throughput in real time."*
* **Command:**
```bash
cd ~/demo
./08_run_full_master_benchmark.sh --step 1
```
* **What happens:**
  * Runs the automated test case defined in `master_benchmark_cases.json`.
  * Evaluates chunk budgets (512 vs 2048 vs 8192 tokens).
  * Streams real-time prompt tokens/sec, decode tokens/sec, and P95 latency.

#### Option B: Launch the Complete 15-Step Master Campaign (Long-Running Sweep)
* **What to say:**  
  *"Our platform includes a unified 15-step master campaign covering FP8 root cause analysis, 128K ultra-long context, 1M concurrency stress testing, pipeline parallelism rebalancing, and Nsight tracing. I can launch the supervisor to run in the background."*
* **Command:**
```bash
cd ~/demo
./08_run_full_master_benchmark.sh --all
```
* To monitor in real time:
```bash
tail -f ~/platform_benchmark_runs/*/logs/MASTER_BENCHMARK_RUN.log
```

---

### STEP 9: Serve the 48B Model Live & Execute Queries
* **Where:** 👉 **Terminal 2 (`[NODE 0]`)**
* **What to say:**  
  *"Now let's launch the distributed vLLM serving engine on our 48B parameter model using Tensor Parallelism TP=8 across all 8 GPUs."*

#### 9.1 Start the Serving Engine:
```bash
cd ~/demo
./06_serve_48b_model.sh
```
* **Explain the memory partitioning:**
  * Total Model Footprint: `~96 GB` in BF16.
  * Sharded across 8 GPUs: **~12 GB per GPU**.
  * Remaining **~81 GB VRAM per GPU** is dedicated to PagedAttention KV-Cache, giving our cluster a combined **>640 GB KV-cache pool** for long context windows and massive concurrency.

#### 9.2 Execute Live Query:
In another tab or on Node 1:
```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-Linear-48B-A3B-Instruct",
    "messages": [{"role": "user", "content": "Explain tensor parallelism in 2 sentences."}],
    "max_tokens": 64
  }' | jq .
```
*(Or run `./07_test_inference_query.sh`)*

---

### STEP 10: Clean Resource Teardown
* **Where:** 👉 **Terminal 1 (`[LOCAL]`)**
* **What to say:**  
  *"To manage infrastructure costs, we cleanly tear down the spot instances via the GCP CLI."*
* **Command:**
```bash
gcloud compute instances delete rtx-demo-node-0 rtx-demo-node-1 --zone=us-central1-b --quiet
```

---

## 📁 Summary of Demo Scripts in `Performance_Intelligence_Platform/demo/`

| Script | Purpose | Where to Run |
| :--- | :--- | :--- |
| `01_provision_cluster.sh` | Provisions 2x G4 nodes (customizable names) | Terminal 1 (Local) |
| `02_install_stack.sh` | Installs uv, PyTorch sm_120, vLLM & Ray | Terminals 2 & 3 (Node 0 & 1) |
| `03_start_ray_cluster.sh` | Links nodes into unified 16-GPU Ray cluster | Terminals 2 & 3 (`--head` / `--worker`) |
| `04_get_weights.sh` | Mounts model weights via GCS FUSE | Terminal 2 (Node 0) |
| `05_run_smoke_benchmark.sh` | 8-GPU GEMM TFLOPS, GDDR7 & P2P bench | Terminal 2 (Node 0) |
| `06_serve_48b_model.sh` | Launches vLLM serving on 48B model (TP=8) | Terminal 2 (Node 0) |
| `07_test_inference_query.sh` | Sends live curl query to test inference | Terminal 2 (Node 0) |
| `08_run_full_master_benchmark.sh` | Launches master benchmark campaign (`--step 1` or `--all`) | Terminal 2 (Node 0) |
| `copy_scripts_to_nodes.ps1` | Deploys entire repo to both nodes (PowerShell) | Terminal 1 (Local) |
| `copy_scripts_to_nodes.sh` | Deploys entire repo to both nodes (Bash) | Terminal 1 (Local) |
