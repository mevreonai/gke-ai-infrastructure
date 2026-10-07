# 01. Preflight Diagnostics & Hardware Qualification Suite

## 🎯 Purpose & Scope
This directory contains the operational tools required to qualify accelerator nodes, PCIe bus bandwidth, NUMA topology, memory channels, and distributed Ray/NCCL readiness **before** launching LLM benchmarks.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `run_quickstart.sh`
* **Purpose:** Rapid 2-minute pre-execution sanity check.
* **Checks:** GPU driver detection, CUDA device count (8 GPUs per node), VRAM allocation verification, host memory capacity (>1.5 TB DDR5), and Python virtualenv availability.
* **Usage:**
  ```bash
  ./run_quickstart.sh
  ```

### 2. `22_readiness.py`
* **Purpose:** Validates vLLM worker process initialization, tensor parallel rank spawning, and Ray head/worker connectivity.
* **Usage:**
  ```bash
  python3 22_readiness.py --head-ip 10.128.0.10 --worker-ip 10.128.0.11 --num-gpus 16
  ```

### 3. `20_ray_nccl_env_audit.py`
* **Purpose:** Performs a live audit of Linux environment variables across all Ray actor nodes, ensuring matching `NCCL_SOCKET_IFNAME`, `NCCL_BUFFSIZE`, and `NCCL_NET=Socket` settings.
* **Usage:**
  ```bash
  python3 20_ray_nccl_env_audit.py
  ```

### 4. `01_prepare_node.sh` & `02_run_node_local.sh`
* **Purpose:** Sets host CPU governors to `performance`, sets GPU clocks to maximum persistence mode (`nvidia-smi -pm 1`), clears page caches, and runs local PCIe bidirectional bandwidth checks.
* **Usage:**
  ```bash
  sudo ./01_prepare_node.sh
  ./02_run_node_local.sh
  ```

### 5. `03_run_network_sweep.sh`
* **Purpose:** Measures point-to-point TCP bandwidth and latency across cluster interfaces using `iperf3` and sockperf under standard MTU 1460 and Jumbo MTU 9000 frames.

---

## 📋 Pass/Fail Exit Criteria
- GPU Count: 8 devices per node detected.
- PCIe Gen5 Bandwidth: $\ge 58.0\text{ GB/s}$ bidirectional.
- Inter-Node TCP Bandwidth: $\ge 94.5\text{ Gbps}$ on 100G GCP Andromeda VPC.
- Ray Cluster Status: Active with 16 available GPUs.
