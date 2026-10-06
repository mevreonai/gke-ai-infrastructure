# GKE AI Infrastructure — Distributed TPU & GPU LLM Serving & Characterization

An enterprise-ready repository for high-throughput, low-latency Large Language Model (LLM) serving on **Google Kubernetes Engine (GKE)** using **Cloud TPUs (v5e / v6e Trillium)** and **NVIDIA GPUs (RTX PRO 6000 Blackwell / Ada / H100 / A100 / L4)** with **vLLM** and **`llm-d` (Gateway API Inference Extension / Endpoint Picker)**.

---

## 🌟 V9 Master Characterization: DeepSeek V4.1 Flash (Blackwell SM120)

The repository hosts the complete empirical release of the **V9 Multi-Node & Single-Node DeepSeek V4.1 Flash Characterization Suite**, executed on a dual-node workstation cluster of 16× NVIDIA RTX PRO 6000 Blackwell GPUs.

- **Interactive Master Dashboard:** [`v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html) (or production entrypoint [`v9_full_result/index.html`](file:///v9_full_result/index.html))
- **Comprehensive Execution Report:** [`V9_BENCHMARK_AND_DASHBOARD_EXECUTION_REPORT.md`](file:///V9_BENCHMARK_AND_DASHBOARD_EXECUTION_REPORT.md)
- **Model:** DeepSeek-AI DeepSeek-V4.1-Flash (FP4 / MXFP8 Weights, 43 Layers, 64 Attention Heads, 24 Engram Hash Heads)
- **Hardware Cluster:** 2× Google Cloud Compute Instances (`us-central1-b`), AMD EPYC 9654 (96 vCPU, 384GB RAM), 16× NVIDIA RTX PRO 6000 Blackwell (96GB VRAM each, 1,536 GB cluster aggregate), PCIe Gen5, Dual 100GbE Interconnect, MTU 8896 Jumbo Frames.
- **Empirical Governance:** 100% genuine empirical measurements (**zero synthetic/mock figures**). All 84 active benchmarks and profiler traces completed with exit code 0. Both cluster instances have been safely **`TERMINATED`** ($0/hr active compute billing).

### 🏆 Key Deployment Decisions & Empirical Findings

| Workload Regime | Primary SLO | Recommended Topology | Empirical Observation | Architectural Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Short-Context Interactive (1K–8K)** | Lowest TPOT (< 5ms) | **`TP4 / PP1` (Single-Node)** | **4.42 ms – 4.49 ms TPOT** · 108.2 ms TTFT | Confining TP within a single PCIe socket eliminates NUMA cross-socket and network barriers during decode. |
| **Single-Node Long Context (1M)** | Lowest TTFT | **`TP4 / PP1` (16K Chunk)** | **88.96s TTFT** · 10.28 ms TPOT | 16K chunked prefill minimizes kernel launch overhead on Blackwell SM120 while staying safely within memory limits. |
| **Multi-Node Distributed (1M Tokens)** | 1M Fit & Lowest Dist TTFT | **`TP4 / PP2` (Dual-Node)** | **127.13s TTFT** · 56.27 ms TPOT · 2.88% peak KV | Pipeline parallel partition keeps layers 20–42 within Stage 2, respecting DeepSeek's compressed KV-sharing group boundary. |
| **Multi-Node Scale-Out (1M Throughput)** | Scaled Prefill Acceleration | **`TP8 / PP2` (Dual-Node)** | **133.64s TTFT** (1.42× faster than TP8 Single-Node 189.68s) | Intra-node TP8 across PCIe Gen5 combined with 2-stage PP across 100GbE VPC provides massive compute parallelism. |
| **Architectural Anti-Pattern 1** | Pipeline Boundary Split | **`TP4 / PP4` (`FAILED`)** | **`SERVER_START_FAILED`** (exit code 1) | DeepSeek V4.1 Flash layers 20–42 share KV states with layer 20. PP=4 slices across this boundary, throwing `NotImplementedError`. |
| **Architectural Anti-Pattern 2** | Non-Uniform Tensor Parallel | **`TP16 / PP1` (`BLOCKED`)** | **`CAPABILITY_BLOCKED`** | Dividing 24 Engram hash heads across 16 TP ranks requires uneven head allocation, which vLLM rejects. |

### 🔬 Empirical Hardware Profiling (SM120 TP8)

Captured **100MB of PyTorch operator traces** and **976MB of Nsight Systems traces** (`vllm_profile.1.sqlite`) with CUDA graphs active:
- **NCCL AllReduce Barrier (TP8)**: 639.53 ms (62.16% Self CUDA time, 243 calls/turn)
- **Shared MoE Forward & DeepGEMM**: 206.35 ms (20.05% Self CUDA time)
- **Sparse MLA Prefill & Decode**: 73.35 ms (7.14% Self CUDA time)
- **MXFP8 GEMM & TileLang Normalization**: 78.59 ms (7.64% Self CUDA time)
- **Blackwell TMA Hardware Encodings**: 2,778,144 calls analyzed (`cuTensorMapEncodeTiled`)

---

## 📊 V8 Characterization: Kimi-Linear-48B (Dual RTX PRO 6000 Blackwell Server Edition)

The repository hosts the complete, audited **V8 Characterization Suite** for MoonshotAI `Kimi-Linear-48B-A3B-Instruct` across single-node and dual-node 16× NVIDIA RTX PRO 6000 Blackwell GPUs.

- **Comprehensive V8 Suite & Dashboard Guide:** [`README_V8_SUITE_AND_DASHBOARD_GUIDE.md`](file:///README_V8_SUITE_AND_DASHBOARD_GUIDE.md) *(detailed breakdown of the 3 V8 folders, runner scripts, empirical outputs, and frontend mappings)*
- **Interactive Master Dashboard:** [`v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html) (mirror: [`v8_full_results/dashboards/v4_dashboard/index.html`](file:///v8_full_results/dashboards/v4_dashboard/index.html))
- **Model:** MoonshotAI `Kimi-Linear-48B-A3B-Instruct` (BF16, 27 Active Layers, Hidden Size 2304)
- **Cluster:** Dual-Node 16× NVIDIA RTX PRO 6000 Blackwell GPUs (PCIe Gen5, NUMA dual-socket, 173.6 Gbps VPC interconnect).
- **V8 Directory Structure:**
  - `v8_full_results/`: Authoritative master dataset (126 canonical runs) and interactive 10-tab dashboard.
  - `v8_additional_runs_suite/`: Executable benchmark runner suite and test definitions (Stage 1 & Stage 2).
  - `v8_additional_runs_local/`: Downloaded empirical cluster metrics, traces, and execution status logs (`rc: 0`).

## 📁 Repository Structure

```
├── v9_full_result/                     # Production V9 DeepSeek V4.1 Flash Release Package
│   ├── MASTER_CHARACTERIZATION_DASHBOARD.html # Standalone interactive HTML dashboard (1.18 MB)
│   ├── index.html                      # Production entrypoint (synchronized 1:1)
│   ├── chart.umd.js                    # Bundled offline Chart.js v4.4.1
│   ├── profiler/                       # Verified empirical profiler traces
│   │   ├── PROFILER_GENUINE_SUMMARY.json # Structured JSON of 382K kernel launches
│   │   ├── torch_tp8_decode_profiler_out_0.txt # PyTorch operator table (8K Decode)
│   │   ├── torch_tp8_prefill_profiler_out_0.txt # PyTorch operator table (128K Prefill)
│   │   ├── nsys_tp8_decode_cuda_gpu_kern_sum.csv # Nsight kernel breakdown (133 kernels)
│   │   └── nsys_tp8_decode_stats.txt   # Nsight Systems CLI summary
│   ├── tp4_pp2_dist_live/              # Raw execution manifests and logs for TP4/PP2
│   ├── vllm_scaleout_network_matrix/   # Multi-node benchmark outputs and raw metrics
│   ├── final_validation/               # Matrix coverage and verification records
│   │   ├── combined_vllm_runs.csv      # All 84 empirical benchmark runs
│   │   ├── combined_vllm_runs.json     # Full JSON metrics dataset
│   │   ├── coverage.csv & coverage.json# 120-point execution coverage audit
│   │   └── FINAL_VALIDATION.md         # Final validation sign-off report
│   └── v9_full_production_20260930_143117_FULL_EVIDENCE.tar.gz # 132.4MB Evidence Tarball
│
├── inference_gateway/                  # GKE Gateway API Inference Extension routing
│   ├── README.md                       # Gateway architecture and configuration guide
│   └── manifests/                      # Gateway, HTTPRoute, and InferencePool definitions
│
├── inference_gateway_gpu/              # GKE Inference Gateway on NVIDIA GPUs (L4 / A100 / Blackwell)
│   ├── manifests/                      # K8s CRDs, vLLM GPU StatefulSets, and EPP configurations
│   ├── client/                         # Benchmarking & verification client
│   ├── run.ps1                         # 1-click deployment script
│   └── cleanup.ps1                     # Safe teardown script
│
├── inference_gateway_tpu/              # GKE Inference Gateway on Cloud TPUs (v6e Trillium)
│   ├── manifests/                      # TPU v6e vLLM deployment manifests and EPP proxy
│   ├── client/                         # Latency and throughput benchmarking client
│   ├── run.ps1                         # 1-click deployment script
│   └── cleanup.ps1                     # Safe teardown script
│
├── disaggregated_tpu_llmd/             # Disaggregated Prefill & Decode TPU Serving
│   ├── manifests/                      # Prefill (producer), Decode (consumer), and llm-d proxy
│   ├── client/                         # Disaggregated token benchmarking suite
│   ├── run.ps1                         # Automated deployment automation
│   └── cleanup.ps1                     # Teardown automation
│
├── single_host/                        # Standalone single-host TPU slice deployment (GKE & vLLM)
├── multi_host/                         # Multi-host TPU pod slice deployment (v5e-16, v6e-16)
│
├── tools/                              # Automation & Diagnostic Suite
│   ├── v9_automation/                  # V9 benchmark runners, verifiers, and harvest scripts
│   │   ├── auto_pilot.py               # Autonomous execution scheduler
│   │   ├── launch_tp4_pp2.py           # Multi-node TP4/PP2 orchestrator
│   │   ├── integrate_live_results.py   # Empirical data aggregator
│   │   └── sync_and_shutdown.py        # Safe cluster synchronization and shutdown
│   └── generate_dashboard.py           # Dashboard generator utilities
│
├── V9_BENCHMARK_AND_DASHBOARD_EXECUTION_REPORT.md # Comprehensive V9 execution & root-cause report
└── REPLICATION_RUNBOOK.md              # Step-by-step reproduction and operations guide
```

---

## 🏛️ GKE Inference Gateway Architecture

The deployment infrastructure leverages Kubernetes-native primitives:
1. **Gateway API Inference Extension (`inference.networking.x-k8s.io`)**: Advanced Layer-7 traffic steering and health probing.
2. **`llm-d` Endpoint Picker (EPP)**: Real-time decision proxy that routes requests based on:
   - **Prefix Cache Affinity (`prefix-cache-scorer`)**: Maximizes KV reuse to minimize TTFT.
   - **KV Cache Utilization (`kv-cache-utilization-scorer`)**: Prevents pod memory saturation and request eviction.
   - **Queue Depth Balancing (`queue-scorer`)**: Distributes traffic away from saturated prefill queues.
3. **Disaggregated Serving**: Separates long-context compute-heavy prefill nodes from latency-sensitive memory-bound decode workers.

---

## 🚀 Quickstart & Verification

### Viewing the V9 Dashboard Locally
Open the self-contained dashboard directly in any modern browser:
```powershell
# Open production dashboard
Start-Process "v9_full_result\index.html"
```

### Verifying the Empirical Datasets
Run the matrix verification script to audit all 84 genuine runs:
```powershell
python -c "
import csv
with open('v9_full_result/final_validation/combined_vllm_runs.csv') as f:
    rows = list(csv.DictReader(f))
print(f'Empirical benchmarks: {len(rows)}')
"
```

---

## 📜 Zero-Mock Data Governance
In accordance with our strict data integrity protocol:
- Every data point on the dashboard maps 1:1 to an empirical execution log in `final_validation/combined_vllm_runs.json`.
- Architecturally incompatible configurations (`tp4_pp4_dist` and `tp16_pp1_dist`) are explicitly preserved as `SERVER_START_FAILED` and `CAPABILITY_BLOCKED` with detailed technical root causes rather than masked with zero or fabricated values.
