# RTX PRO 6000 GCP 2-Node Smoke Test Suite (V4)

Hardware, interconnect, and collective characterization suite for multi-node NVIDIA RTX PRO 6000 (Blackwell Server Edition) clusters on Google Cloud Platform (`g4-standard-384`).

---

## 🚀 Quick Replication Guide

To replicate this full benchmark suite on any 2-node cluster:

### Step 1: Prepare Environment on Both Nodes
```bash
# On Node 0 and Node 1:
chmod +x *.sh
sudo ./01_prepare_node.sh
```

### Step 2: Execute Single-Node Benchmarks
```bash
# Run on both Node 0 and Node 1:
./02_run_node_local.sh
```

### Step 3: Run Multi-Node Network & NCCL Sweep
```bash
# On Node 0 (ensure passwordless SSH is configured between nodes):
export NODE0_IP="<NODE_0_INTERNAL_IP>"
export NODE1_IP="<NODE_1_INTERNAL_IP>"
./03_run_network_sweep.sh
```

### Step 4: Summarize & Model Results
```bash
# Consolidate results from Node 1 to Node 0:
scp -r $NODE1_IP:~/rtx_g4_smoke/results/<RUN_ID>/node-1 ~/rtx_g4_smoke/results/<RUN_ID>/

# Generate summary & analytical model:
python3 04_summarize_results.py ~/rtx_g4_smoke/results/<RUN_ID> --out ~/rtx_g4_smoke/results/<RUN_ID>/summary
python3 05_analyze_model.py ~/rtx_g4_smoke/results/<RUN_ID>/summary/summary.json --out ~/rtx_g4_smoke/results/<RUN_ID>/summary/ANALYSIS.md
./06_package_results.sh ~/rtx_g4_smoke/results/<RUN_ID>
```

---

## 📊 Live Measured Results Summary

### 1. Host-to-Device & Interconnect
- **PCIe Gen 5 Host Transfer Rate**: **56.88 GB/s** per GPU (Aggregate **455.04 GB/s**).
- **VRAM Streaming Bandwidth (GDDR7)**: **1,280 GB/s** (~80% theoretical peak).
- **Intra-NUMA P2P (Same Socket)**: **52.1 GB/s**.
- **Cross-NUMA P2P (Cross Socket via UPI)**: **25.3 GB/s** (2.1x inter-socket penalty).

### 2. NCCL AllReduce Performance (TP4 vs TP8)
| Collective Size | TP4 Collective Time | TP4 AlgBW | TP8 Collective Time | TP8 AlgBW | TP4 vs TP8 Gain |
|---|---:|---:|---:|---:|---:|
| **16 KiB** (Decode Proxy) | **20.17 µs** | 0.81 GB/s | **38.24 µs** | 0.43 GB/s | **1.90x Lower Latency** |
| **128 KiB** | **20.73 µs** | 6.32 GB/s | **38.93 µs** | 3.37 GB/s | **1.88x Lower Latency** |
| **512 KiB** | **47.81 µs** | 10.97 GB/s | **61.39 µs** | 8.54 GB/s | **1.28x Lower Latency** |
| **64 MiB** | 2,599 µs | 25.81 GB/s | 2,961 µs | 22.66 GB/s | **1.14x Higher AlgBW** |
| **128 MiB** (Prefill Chunk) | 5,164 µs | **25.99 GB/s** | 5,891 µs | **22.78 GB/s** | **1.14x Higher AlgBW** |
| **256 MiB** | 10,258 µs | **26.17 GB/s** | 11,688 µs | **22.97 GB/s** | **1.14x Higher AlgBW** |

### 3. Multi-Node Network Sweep (`iperf3` Throughput)
- **GCP Native**: **173.58 Gbps** (21.70 GB/s)
- **100G Capped**: **58.75 Gbps** (7.34 GB/s)
- **50G Capped**: **33.77 Gbps** (4.22 GB/s)
- **20G Capped**: **16.80 Gbps** (2.10 GB/s)
- **10G Capped**: **9.02 Gbps** (1.13 GB/s)

---

## 🎯 Architecture Conclusions
- **TP4 / PP6** is the optimal topology for 24-GPU cluster deployments: keeping TP within a single 4-GPU NUMA domain eliminates cross-socket UPI penalties ($1.90\times$ faster decode latency) while keeping Pipeline Parallel transfers lightweight across the native GCP network.
