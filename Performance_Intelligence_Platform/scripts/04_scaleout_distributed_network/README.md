# 04. Scale-Out Distributed Network Suite

## 🎯 Purpose & Scope
Evaluates multi-node distributed serving across two 8-GPU nodes interconnected via Google Cloud Andromeda VPC (100 Gbps virtual ethernet). Investigates the communication bottlenecks of Tensor Parallelism (TP16) vs Pipeline Parallelism (TP8 + PP2).

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `20_run_vllm_network_matrix.sh`
* **Purpose:** Executes full distributed serving sweep comparing network topologies and traffic pacing.
* **Parameters Evaluated:**
  - Topologies: `TP16 / PP1` (monolithic cross-node All-Reduce) vs `TP8 / PP2` (pipelined inter-node boundary activations).
  - Network MTU: Standard MTU `1460` bytes vs Jumbo Frames MTU `9000` bytes.
  - Traffic Control: Native 100G vs `tc` HTB pacing at 10G, 20G, and 50G.
* **Usage:**
  ```bash
  ./20_run_vllm_network_matrix.sh
  ```

### 2. `20_nccl_policy.sh`
* **Purpose:** Configures kernel socket buffers and NCCL environment policies (`NCCL_BUFFSIZE=16777216`, `NCCL_NET=Socket`).

### 3. `23_run_nccl_socket_tuning.sh`
* **Purpose:** Evaluates TCP window auto-tuning parameters (`net.ipv4.tcp_rmem`, `net.ipv4.tcp_wmem`) on cross-node All-Reduce efficiency.

---

## 💡 Landmark Finding
`TP16` across virtualized 100G VPC suffers severe packet serialization stalls, increasing decode latency to **88.4 ms/token**. `TP8+PP2` confines All-Reduce inside each node and transmits only boundary activations, cutting decode latency to **5.5 ms/token** (a **16.1× speedup**).
