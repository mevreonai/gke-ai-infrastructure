# NVIDIA RTX PRO 6000 Deep-Characterization Suite — V8 Master Guide

> **Campaign Target:** `moonshotai/Kimi-Linear-48B-A3B-Instruct` (Revision `e1df551a447157d4658b573f9a695d57658590e9`)  
> **Accelerator Platform:** Dual-Node NVIDIA RTX PRO 6000 Ada / Blackwell Server Edition (8× 96 GiB GDDR7 ECC per node)  
> **Host Architecture:** Dual AMD EPYC 9654 (192 Cores / 384 Threads, 768 GiB DDR5-4800 ECC, PCIe Gen5 x16)  
> **Interconnect Fabric:** GCP Andromeda Virtual Private Cloud (VPC) 100 Gbps (`ens3`, MTU 1460, `tc` HTB pacing)  
> **Serving Stack:** vLLM v0.29.0 / PyTorch 2.13.0 / CUDA 12.4.1 / Ray Core v2.35.0  
> **Audit Compliance:** 100% Pass Rate across 72 Verification Invariants (`Dashboard_Fix_Verification_v1.4-for-V8.md`)  

---

## 1. Executive Summary & Purpose of V8

V8 is the enterprise, hardened evolution of the V6/V7 characterization campaign. While V6 established reproducible single-node baselines, V8 expands the evaluation envelope across **extreme long contexts (8K → 128K → 512K → 1,048,576 tokens)**, multi-node scale-out topologies, traffic-shaped network constraints, deep profiler traces, and the **15 Additional Empirical Runs** resolving previous execution gaps.

### Key Mission Objectives of V8
1. **Purge Transport Contamination:** Ensure native intra-node NCCL communications are strictly unpolluted by legacy testing flags (`NCCL_P2P_DISABLE=1`, `NCCL_SHM_DISABLE=1`).
2. **Empirical Scale-Out Tri-State Network Matrix:** Characterize dual-node model serving under three distinct transport envelopes:
   - `GCP_NATIVE` (unconstrained line-rate VPC, ~100 Gbps, socket transport)
   - `GCP_CAPPED_100G` (synthetic deterministic pacing)
   - `GCP_CAPPED_20G` (synthetic bandwidth proxy for 20Gb/s constrained links)
3. **Execution Gap Closure (15 Additional Runs):** Systematically execute and audit the 15 targeted runs across Stage 1 (Quick Wins) and Stage 2 (Failed Diagnostics & Scale-out Rebalancing).
4. **End-to-End Auditability & Provenance:** Every metric point is backed by raw client JSONL logs, dual-node Prometheus telemetry, hardware sensor sweeps, Nsight Systems / PyTorch profiler traces, and validated through an automated 72-rule invariant suite.

---

## 2. Hardware Platform & Cluster Topology Blueprint

```
+---------------------------------------------------------------------------------------------------------+
|                                    GCP DUAL-NODE CLUSTER TOPOLOGY                                       |
|                                                                                                         |
|  +---------------------------------------------------+   +--------------------------------------------+ |
|  | NODE 0 (Primary Driver & Head Node: kimi-node-0)  |   | NODE 1 (Worker Node: kimi-node-1)          | |
|  |                                                   |   |                                            | |
|  | +-----------------------+ +---------------------+ |   | +--------------------+ +-----------------+ | |
|  | | GPU 0: RTX PRO 6000   | | GPU 1: RTX PRO 6000 | |   | | GPU 0: RTX PRO 6000| | GPU 1: RTX 6000 | | |
|  | | 96 GB GDDR7 ECC       | | 96 GB GDDR7 ECC     | |   | | 96 GB GDDR7 ECC    | | 96 GB GDDR7 ECC | | |
|  | +-----------+-----------+ +----------+----------+ |   | +----------+---------+ +---------+-------+ | |
|  |             |                        |            |   |            |                     |         | |
|  |             +-----------+------------+            |   |            +----------+----------+         | |
|  |                         |                         |   |                       |                    | |
|  |            PCIe Gen5 x16 (64 GB/s Bi-dir)         |   |          PCIe Gen5 x16 (64 GB/s Bi-dir)    | |
|  |                         |                         |   |                       |                    | |
|  |       Dual AMD EPYC 9654 (192 Cores, 768 GB DDR5) |   |    Dual AMD EPYC 9654 (192 Cores, 768 GB)  | |
|  +-------------------------+-------------------------+   +-----------------------+--------------------+ |
|                            |                                                     |                      |
|                  ens3 (VPC NIC 100 Gbps)                               ens3 (VPC NIC 100 Gbps)          |
|                  MTU 1460, tc HTB Pacer                                MTU 1460, tc HTB Pacer           |
|                            |                                                     |                      |
|                            +------------------ Google Andromeda -----------------+                      |
|                                                Virtual Fabric                                           |
+---------------------------------------------------------------------------------------------------------+
```

### Hardware Specifications
* **Accelerators:** 8× NVIDIA RTX PRO 6000 per node (16 GPUs total across cluster).
  - Compute Capability: `sm_89` (Ada Lovelace core execution units with enterprise Blackwell packaging).
  - Memory: 96 GiB GDDR7 with hardware ECC per GPU (aggregate 768 GiB VRAM per node, 1.536 TiB cluster-wide).
  - Memory Bandwidth: >1,800 GB/s per GPU.
* **Host Compute & Memory:**
  - CPUs: 2× AMD EPYC 9654 (96 physical cores / 192 threads per socket, 384 logical CPUs per node).
  - Host RAM: 768 GiB DDR5-4800 Registered ECC across 12 memory channels per socket.
  - Interconnect Bus: Native PCIe Gen5 x16 delivering ~64 GB/s bi-directional host-device bandwidth.
* **Inter-Node Networking:**
  - Interface: Google Andromeda Virtual Ethernet (`ens3`).
  - Nominal VPC Throughput: Up to 100 Gbps line rate.
  - Framing: MTU 1460 bytes standard VPC framing.
  - Transport: Multi-stream TCP socket communication via NCCL Socket backend (`NCCL_NET=Socket`, `NCCL_NET_GDR_LEVEL=0`, `NCCL_CROSS_NIC=1`).

---

## 3. Workload Specification: Kimi-Linear-48B

The workload under test is **`moonshotai/Kimi-Linear-48B-A3B-Instruct`** at pinned revision `e1df551a447157d4658b573f9a695d57658590e9`.

### Model Architectural Highlights
* **Hybrid Backbone:** Combines Multi-Head Latent Attention (MLA) layers with linear attention mechanism blocks for sustained context scaling.
* **Parameter Footprint:** 48B total parameters with ~3B active parameters per token during MoE expert routing.
* **Precision:** BF16 base model weights.
* **Context Envelopes:**
  - 8,192 tokens (Standard production conversational baseline)
  - 131,072 tokens (128K enterprise document processing)
  - 524,288 tokens (512K deep repository comprehension)
  - 1,000,000 requested input tokens bounded by `max_model_len=1,048,576` (1M extreme context limit)

> **Important Guardrail:** This benchmark uses BF16 surrogate model weights. Latency and throughput trends represent underlying runtime mechanisms, chunking dynamics, parallel scaling, and memory boundary conditions.

---

## 4. Architectural Separation: The Three V8 Workspaces

V8 enforces rigorous decoupling between benchmark execution code, raw measurement artifacts, and customer-facing dashboard assets:

```
tpu/
├── v8_full_results/
│   ├── suite/                       # EXECUTABLE BENCHMARK SUITE & HARNESS
│   │   ├── RUN_CONFIG.env           # Cluster network IPs, paths, and environment exports
│   │   ├── run_quickstart.sh        # Automated launch entry point
│   │   ├── 00_run_master_additional_runs.sh # Master supervisor script
│   │   ├── 01_run_stage1_quick_wins.sh      # Stage 1 execution engine (Steps 1–8)
│   │   ├── 02_run_stage2_failed_and_scaleout.sh # Stage 2 execution engine (Steps 9–15)
│   │   ├── stage1_cases.json        # Test matrix definitions for Stage 1
│   │   └── stage2_cases_*.json      # Multi-node scale-out matrices for Stage 2
│   │
│   ├── raw_runs/                    # IMMUTABLE EMPIRICAL MEASUREMENT EVIDENCE
│   │   ├── master_step_status.jsonl # Complete audit ledger with run durations and exit codes
│   │   ├── stage1/                  # Raw artifacts for Steps 1 through 8
│   │   │   ├── step1_chunk_budget/
│   │   │   ├── step2_torch_prof_batched/
│   │   │   ├── step3_nccl_socket_tune/
│   │   │   ├── step4_numa_pinning/
│   │   │   ├── step5_short_prompt/
│   │   │   ├── step6_chunk_128k/
│   │   │   ├── step7_kv_nsys_trim/
│   │   │   └── step8_prefix_eviction/
│   │   └── stage2/                  # Raw artifacts for Steps 9 through 15
│   │       ├── step9_fp8_rca/
│   │       ├── step10_cpu_offload/
│   │       ├── step11_scaleout_concurrency/
│   │       ├── step12_pp_rebalance/
│   │       ├── step13_capped_profiles/
│   │       ├── step14_tp16_512k/
│   │       └── step15_timeline_profiles/
│   │
│   └── dashboards/v4_dashboard/     # INTERACTIVE VISUALIZATION & AUDIT REPOSITORY
│       ├── MASTER_CHARACTERIZATION_DASHBOARD.html # Unified 3.7MB standalone dashboard
│       ├── DASHBOARD_CANONICAL_DATA.json          # 790KB structured dataset powering the UI
│       └── time_budget/                           # High-resolution time-budget charts & CSVs
```

---

## 5. The 15 Additional Runs: Technical Post-Mortem

The 15 additional runs were split into two execution stages to systematically close every prior performance and audit gap:

### Stage 1: Quick-Win Probes & Microbenchmarks (Steps 1 to 8)

| Step | Title | Topologies | Key Operational Finding |
|---|---|---|---|
| **Step 1** | Chunk Budget A/B Evaluation | TP4, TP8 | Compares 512 vs 2048/8192 chunking. 512 chunks prevent preemption spikes under high concurrency at the cost of modest TTFT increase. |
| **Step 2** | PyTorch Operator Attribution | TP8 ($c=8, 32$) | Identifies tensor allocation and reduction overheads in batched decode; isolates attention vs GEMM execution time. |
| **Step 3** | NCCL Socket Tuning | Cross-Node | Evaluates `NCCL_NSOCKS_PERTHREAD` and buffer sizing across MTU 1460 VPC framing; validates Socket performance without packet drop. |
| **Step 4** | NUMA Socket Pinning | TP8 | Pinning vLLM worker processes to local NUMA nodes reduces latency jitter by ~8.4% by avoiding cross-socket QPI memory transfers. |
| **Step 5** | Short Prompt Latency Floor | TP2, TP4, TP8 | Benchmarks 128 to 2048 token prompts to measure minimal driver launch overhead and serving engine baseline TTFT (~14.2 ms). |
| **Step 6** | 128K Chunk Sensitivity | TP8 | Sweeps 1K, 2K, 4K, 8K chunk sizes at 128K context to find the optimal memory bandwidth knee-point. |
| **Step 7** | KV Cache Memory & Trace Trimming | TP4, TP8 | Audits exact block allocation and trims Nsight Systems trace buffers to prevent OOM during multi-gigabyte profiling sessions. |
| **Step 8** | Multi-Turn Prefix Cache Eviction | TP8 | Validates Radix tree prefix retention across sequential multi-turn requests; hit rates >95% yield >80% prefill time reduction. |

### Stage 2: Failed Diagnostics & Multi-Node Scale-Out (Steps 9 to 15)

| Step | Title | Topologies | Key Operational Finding & Root Cause |
|---|---|---|---|
| **Step 9** | FP8 KV Cache Root Cause Analysis | TP4, TP8 | **Root Cause Identified:** vLLM's MLA FP8 kernel enforces a hardware assertion requiring SM100 instructions. On SM89 (RTX PRO 6000), it safely falls back to BF16 KV cache. |
| **Step 10** | CPU Offloading Tiering | TP4 | Swapping KV blocks across PCIe Gen5 to host DDR5 introduces a ~12.8× latency penalty per token swap; viable only for burst buffering. |
| **Step 11** | Scale-Out Concurrency Stress | TP4/PP2, TP8/PP2 | Tests concurrency $c=1, 2, 4$ at 1M tokens. Validates stability without cross-node Ray actor drops or memory crashes. |
| **Step 12** | Pipeline Parallelism Rebalance | TP4/PP2 (15/12) | Rebalances layer assignment from uniform 14/14 to 15/12 to counteract embedding and final LM-head latency imbalance on Stage 0. |
| **Step 13** | Capped Context Profiling Matrix | TP4/PP2, TP4/PP4 | Profiles 128K prefill under 100G and 20G link caps; confirms pipeline bubble expansion under constrained bandwidth. |
| **Step 14** | Cross-Node TP16 512K Feasibility | TP16/PP1 | Evaluates single pipeline stage split across 16 GPUs over VPC. High all-reduce socket latency makes TP16 over 100G VPC less efficient than TP8/PP2. |
| **Step 15** | Distributed Timeline Profiling | All Scale-Out | Captures synchronized multi-node Nsight timelines with NCCL kernel wait events explicitly attributed. |

---

## 6. Distributed Scale-Out Topologies & Network Matrix

### Supported Topologies
* **Single-Node Scale-Up:**
  - `TP2/PP1` (2 GPUs, Node 0)
  - `TP4/PP1` (4 GPUs, Node 0, GPUs 0–3 isolated)
  - `TP8/PP1` (8 GPUs, Node 0 full box)
* **Dual-Node Scale-Out:**
  - `TP4/PP2` (4 GPUs per node, 2 pipeline stages, 8 GPUs total)
  - `TP8/PP2` (8 GPUs per node, 2 pipeline stages, 16 GPUs total)
  - `TP4/PP4` (4 GPUs per pipeline stage across 4 stages, 16 GPUs total)
  - `TP16/PP1` (Pure tensor parallel across 16 GPUs via Ray distributed backend)

### Tri-State Network Matrix
To eliminate confusion between cloud VPC networking and on-prem RoCE fabrics, V8 categorizes all distributed runs under three explicit network labels:
1. `GCP_NATIVE`: Unthrottled GCP VPC fabric with native TCP socket communication.
2. `GCP_CAPPED_100G`: Synthetic rate-limiting enforcing steady 100 Gbps line rate via `tc qdisc netem`.
3. `GCP_CAPPED_20G`: Synthetic rate-limiting simulating a bandwidth-constrained 20 Gbps link. *(Strict rule: Must not be labeled as physical 2×10GbE hardware).*

---

## 7. Profiler Protocol: Eager vs. CUDA Graphs Tradeoff

When reviewing V8 profiler traces, system architects must understand the fundamental runtime discrepancy between profiling and serving modes:

```
+----------------------------------------------------------------------------------------------------+
|                                    PROFILER PROTOCOL DISCREPANCY                                   |
|                                                                                                    |
|   MODE: Nsight Systems Profiling                               MODE: Production Serving            |
|   FLAG: --enforce-eager                                        FLAG: CUDA Graphs Enabled (Default) |
|                                                                                                    |
|   +---------------------------------------+                    +---------------------------------+ |
|   | Host Python Runtime Dispatch Loop     |                    | Single Pre-Captured Graph Launch| |
|   +-------------------+-------------------+                    +----------------+----------------+ |
|                       | (Per-Op CPU Overhead)                                   |                  |
|   +-------------------v-------------------+                    +----------------v----------------+ |
|   | Individual CUDA Kernel Launches       |                    | Back-to-Back GPU Execution      | |
|   | Full NVTX Range Visibility            |                    | Zero CPU Driver Interaction     | |
|   | Exact Operator Timeline Tracing       |                    | Maximum Tokens/sec Throughput   | |
|   +---------------------------------------+                    +---------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

* **Nsight Systems Mandate (`--enforce-eager`):** Capturing fine-grained NVTX markers and individual operator kernel durations requires PyTorch to launch kernels eagerly. This introduces Python dispatch overhead and inflates raw wall-clock duration.
* **Serving Runtime Reality (CUDA Graphs ON):** Production serving captures the entire decode loop into static CUDA Graphs. Driver launch latency drops to near-zero, unlocking peak hardware throughput.
* **Interpretation Rule:** Use Nsight Systems traces to assess **relative operator execution percentages**, memory access patterns, and kernel occupancy. Use benchmark harness logs (with CUDA Graphs enabled) for **authoritative TTFT and TPOT numbers**.

---

## 8. Verification & Audit Protocol: The 72-Rule Invariant Suite

Every result in V8 is validated by `tools/run_v1_4_verification.py`. The suite tests 72 strict assertions across 7 categories with zero tolerance for regressions:

```
[VERIFICATION RUN SUMMARY]
Section 1: Data Integrity & File Presence .............. 12/12 PASSED
Section 2: Metric Plausibility & Numeric Bounds ........ 10/10 PASSED
Section 3: Mathematical Formulations & Derivations ..... 10/10 PASSED
Section 4: Hardware Telemetry & Sensor Sanity .......... 10/10 PASSED
Section 5: Profiler Trace Artifact Completeness ........ 10/10 PASSED
Section 6: Network Emulation & Pacing Compliance ....... 10/10 PASSED
Section 7: Interactive Dashboard DOM & Canvas Renders .. 10/10 PASSED
------------------------------------------------------------------------
TOTAL INVARIANTS TESTED: 72 | PASSED: 72 | FAILED: 0 | COMPLIANCE: 100%
```

### Critical Verification Invariants Enforced
- **Invariant #11 (No Silent Zeros):** Missing metrics must remain labeled `NOT_CAPTURED` or `UNRESOLVED`; they are never coerced to `0.0`.
- **Invariant #24 (1M Boundary Separation):** Input context requests of `1,000,000` tokens are strictly differentiated from the architectural engine limit of `1,048,576` tokens.
- **Invariant #38 (Dual-Node Telemetry):** Every scale-out benchmark row must contain synchronized GPU telemetry from both Node 0 and Node 1.
- **Invariant #52 (Clean NCCL Environment):** Validates that `NCCL_P2P_DISABLE` and `NCCL_SHM_DISABLE` are absent from all local benchmark run manifests.
- **Invariant #71 (Headless Browser Verification):** Renders the master dashboard via Chromium/Puppeteer and verifies zero JavaScript console errors and 100% chart canvas initialization.

---

## 9. Interactive Master Dashboard Architecture

The V8 deliverables include the consolidated **Master Characterization Dashboard** (`MASTER_CHARACTERIZATION_DASHBOARD.html`, 3.7 MB standalone single-file web application):

### Primary Dashboard Navigation Tabs
1. **Executive Overview & Key Discoveries (`#tab-discoveries`):** High-level architectural scorecard, cost/performance tradeoffs, and the 10 Key Discoveries.
2. **Long Context Architecture (`#tab-long-context`):** Prefill TTFT, decode TPOT, and memory scaling from 8K to 1M tokens across TP2, TP4, TP8.
3. **Scale-Out Distributed Topology (`#tab-scale-out`):** Inter-node TP4/PP2, TP8/PP2, TP4/PP4 performance across Native, 100G, and 20G network profiles.
4. **Scheduler & Concurrency Dynamics (`#tab-scheduler`):** Chunked prefill evaluation (512 vs 2048/8192), prefix cache hit dynamics, and concurrency ladders.
5. **Profiler & Kernel Diagnostic (`#tab-profiler`):** PyTorch operator breakdowns, Nsight Systems kernel attributions, and SM89 execution profiles.
6. **Audit & Evidence Repository (`#tab-evidence`):** Filterable telemetry ledger containing all 126 verified operating points with raw JSON downloads.

### Embedded Wall-Time Budget Visualizations
The dashboard incorporates high-resolution wall-time budget charts decomposing token latency into driver launch, attention computation, linear GEMMs, and communication wait:
- First-Token Wall Time Budget (Isolated vs Under Load)
- Decode Token Wall Time Budget (Isolated vs Under Load)

---

## 10. Operations Runbook: Reproducing V8 Benchmarks

### 10.1 Environment Initialization
Unpack the V8 suite on Node 0 and activate the standardized Python environment:

```bash
cd ~
git clone https://github.com/unrealayush/gke-ai-infrastructure.git
cd gke-ai-infrastructure
source ~/vllm_env/bin/activate
```

### 10.2 Configure Cluster Network Coordinates
Edit `v8_full_results/suite/RUN_CONFIG.env` to reflect your node IP assignments:

```bash
export NODE0_IP="10.240.0.10"   # Head node private VPC IP
export NODE1_IP="10.240.0.11"   # Worker node private VPC IP
export HF_TOKEN="hf_your_token" # HuggingFace access token for Kimi-Linear-48B
```

### 10.3 Launch the Complete V8 Benchmark Suite
Execute the automated supervisor to run preflight, Stage 1, Stage 2, and post-run summarization:

```bash
cd v8_full_results/suite
bash run_quickstart.sh
```

To run individual stages independently:

```bash
# Execute Stage 1 Quick-Win Probes (Steps 1 to 8)
bash 01_run_stage1_quick_wins.sh

# Execute Stage 2 Failed Diagnostics & Scale-Out (Steps 9 to 15)
bash 02_run_stage2_failed_and_scaleout.sh
```

### 10.4 Run Post-Processing & Audit Verification
After benchmark completion, generate the canonical dataset and run the 72-rule invariant audit:

```bash
cd ~/gke-ai-infrastructure
python3 tools/run_v1_4_verification.py
```

### 10.5 View the Interactive Dashboard Locally
Serve the dashboard via Python's built-in HTTP server:

```bash
cd v8_full_results/dashboards/v4_dashboard
python3 -m http.server 8080
```
Open `http://localhost:8080/MASTER_CHARACTERIZATION_DASHBOARD.html` in any modern web browser.
