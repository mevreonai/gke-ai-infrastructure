# 04. Scale-Out Distributed Network Suite

## 🎯 Purpose & Scope
Evaluates multi-node distributed serving across dual 8-GPU nodes interconnected via Google Cloud Andromeda VPC (100 Gbps virtual ethernet). Investigates the communication bottlenecks of cross-node Tensor Parallelism (`TP16/PP1`) vs Pipeline Parallelism (`TP8/PP2`, `TP4/PP4`) and measures resilience under synthetic bandwidth throttling and packet loss.

---

## 🛠️ Tool Catalog & Execution Commands

### 1. `12_run_vllm_multi_node.sh` & `12_run_vllm_multi_node.py`
* **Purpose:** Core distributed runner executing multi-node test groups (`scaleout_load`, `pp2_split`, `r3_network_resilience`) across Ray and NCCL clusters.
* **Usage:**
  ```bash
  ./12_run_vllm_multi_node.sh --group scaleout_load
  ```

### 2. `20_run_vllm_network_matrix.sh`
* **Purpose:** Executes full distributed serving sweep comparing network topologies and traffic pacing.
* **Parameters Evaluated:**
  - Topologies: `TP16 / PP1` (monolithic cross-node All-Reduce) vs `TP8 / PP2` (pipelined inter-node boundary activations).
  - Traffic Control: Native 100G vs `tc` HTB pacing at 100G, 20G, and 0.05% loss + 0.2ms jitter.
* **Usage:**
  ```bash
  ./20_run_vllm_network_matrix.sh
  ```

### 3. `20_nccl_policy.sh`
* **Purpose:** Enforces kernel socket buffers and NCCL environment policies (`NCCL_BUFFSIZE=4194304`, `NCCL_NET=Socket`, `NCCL_ALGO`/`NCCL_PROTO` unset to prevent AllGather protocol mismatch).

### 4. `23_run_nccl_socket_tuning.sh`
* **Purpose:** Evaluates TCP socket performance using `nccl-tests` (AllReduce & SendRecv) over the VPC interconnect.

---

## 💡 Landmark Findings & Measured Deltas
1. **Topology Supremacy:** `TP16` across virtualized 100G VPC suffers severe packet serialization stalls, increasing decode latency to **88.4 ms/token**. `TP8+PP2` confines All-Reduce inside each node and transmits only boundary activations, cutting decode latency to **5.48 ms/token** (a **16.1× speedup**).
2. **Network Resilience:** Under 0.05% packet loss, `TP16` suffers a **3.8× slowdown**, whereas `TP8+PP2` and `TP4+PP4` degrade by **less than 5%**.
3. **Asymmetric 15/12 Layer Partition:** An asymmetric 15/12 layer split on 27-layer models provides an A/B benchmark evaluation against default symmetric splits.

## 🧊 Multi-Node Cold vs. Warm Cache Isolation
In multi-node runs, cold/warm cache isolation is orchestrated across both cluster nodes:
* **Coordinated Worker Termination:** Local and remote Ray actors and `vllm serve` processes are cleanly terminated via `ray stop` and targeted process-group shutdown.
* **Cluster VRAM Drain:** Both Node 0 and Node 1 verify complete VRAM allocation return to zero prior to the next concurrency point.
* **Cold Initial Measurements:** Initial requests at each concurrency tier evaluate pure cold performance without cross-request prefix caching.

---

## 📖 Reference Guides
- Master Run Coverage Matrix (Steps 00-20): [`RUN_COVERAGE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/RUN_COVERAGE.md)
- Full script execution parameters: [`SCRIPTS_AND_RESULTS_GUIDE.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/SCRIPTS_AND_RESULTS_GUIDE.md)
- Complete measured benchmarks: [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md)
