# V9-FULL Characterization Suite: The 3 Tests, Step-by-Step Blueprint & Exact Execution Timings Guide

**Document Version:** 2.0.0  
**Target Suite:** V9-FULL Multi-Model Characterization Suite (`V9_FULL_vLLM_MULTI_MODEL_Characterization_RC2.zip`)  
**Target Workload:** DeepSeek-V4.1-Flash (Mixed MXFP4/FP8) & Kimi-Linear-48B (BF16)  
**Cluster Architecture:** 2-Node GPU Cluster (2 Nodes × 8 NVIDIA RTX PRO 6000 Ada / Blackwell / A100 / H100 = 16 GPUs total)  
**Distributed Engine:** vLLM v0.6+ with Ray Cluster Orchestration, NCCL, and Linux Traffic Control (`tc`)  

---

## Executive Overview: The Three Tests at a Glance

To achieve 100% production readiness and complete performance characterization without wasting compute time or risking mid-run cluster crashes, the testing strategy is structured into **Three Distinct Tests**:

| Test Tier | Test Name | Target Scope | Key Focus | Wall-Clock Timing | Recommended Timing |
|:---:|---|---|---|:---:|---|
| **TEST 1** | **2-Node Fast Cluster Smoke & Preflight Test** | Cluster Preflight, Network Sweeps, & 1 Distributed Topology (`tp4_pp2_dist`) | Validates SSH, Ray multi-node orchestration, NCCL bandwidth, `tc` traffic shaping, and vLLM distributed startup | **15 – 30 Minutes** | **Immediate First Step** (Before any long run) |
| **TEST 2** | **Core Characterization & Scale-Out Inference Suite (No Profilers)** | All 51 Single-Node Benchmarks + Open-Loop Queues + All 30 Scale-Out Runs | Full TTFT, TPOT, Context Elasticity (1K to 1M), and Network Sensitivity (Native, 100G, 20G) without trace overhead | **5.5 – 7.5 Hours** | **Daytime Operational Run** (Fast turnaround) |
| **TEST 3** | **Full Production Characterization & Deep Nsight/Torch Profiling** | The Complete 13-Phase Suite: Test 2 + 35 GPU Profiler Traces + Deep Kernel Metrics | Kernel execution breakdowns, SM occupancy, memory bandwidth saturation, and NCCL collective wait times | **12 – 16 Hours** | **Overnight Unattended Run** (Complete audit) |

---

## Prerequisites: From-Scratch Environment Setup (Common to All Tests)

Before executing any of the three tests, both nodes must be configured identically.

### 1. Cluster Identity & Host Resolution
- **Node 0 (Head Node)**: IP `10.0.0.10` (e.g., `gcp-node-0`)
- **Node 1 (Worker Node)**: IP `10.0.0.11` (e.g., `gcp-node-1`)
- Add host entries to `/etc/hosts` on both nodes:
  ```bash
  sudo bash -c 'cat <<EOF >> /etc/hosts
  10.0.0.10 node0
  10.0.0.11 node1
  EOF'
  ```

### 2. Passwordless Inter-Node SSH
Node 0 must be able to SSH into Node 1 (and loopback into Node 0) without any password prompt:
```bash
# On Node 0:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@node0
ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@node1

# Verify passwordless login (must output hostname without prompt):
ssh -o StrictHostKeyChecking=no ubuntu@node1 hostname
```

### 3. Passwordless `sudo tc` for Network Traffic Shaping
The V9 suite tests network degradation by capping fabric bandwidth to **100 Gbps** and **20 Gbps** using Linux `tc` (traffic control). The benchmark user must have passwordless `sudo` privileges for `tc`:
```bash
# On BOTH Node 0 and Node 1:
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/tc, /sbin/tc" | sudo tee /etc/sudoers.d/v9_tc_nopasswd
sudo chmod 0440 /etc/sudoers.d/v9_tc_nopasswd

# Verify on both nodes (must exit 0 with no password prompt):
sudo -n tc qdisc show
```

### 4. Shared Python Virtual Environment & CUDA Stack
Both nodes must have the same Python virtual environment path (e.g., `/home/ubuntu/vllm_env`):
```bash
# Packages required in venv:
# - python >= 3.10
# - torch >= 2.4.0 (CUDA 12.4+)
# - vllm >= 0.6.0
# - ray >= 2.35.0
# - flashinfer >= 0.1.6
# - iperf3, pyarrow, pandas, pydantic
source /home/ubuntu/vllm_env/bin/activate
python3 -c "import torch, vllm, ray; print('CUDA Available:', torch.cuda.is_available(), 'Devices:', torch.cuda.device_count())"
```

### 5. Cluster Configuration File (`configs/clusters/my_cluster.json`)
Create `V9_FULL/configs/clusters/my_cluster.json`:
```json
{
  "schema_version": 1,
  "provider": "local",
  "head_index": 0,
  "ssh_key": "/home/ubuntu/.ssh/id_rsa",
  "ssh_user": "ubuntu",
  "venv_dir": "/home/ubuntu/vllm_env",
  "bench_root": "/home/ubuntu/v9_bench",
  "expected_gpu_name_contains": "RTX",
  "nodes": [
    { "name": "node0", "host": "10.0.0.10", "gpus": 8, "interface": "auto" },
    { "name": "node1", "host": "10.0.0.11", "gpus": 8, "interface": "auto" }
  ],
  "ray_env": {
    "NCCL_DEBUG": "WARN",
    "NCCL_IB_DISABLE": "0",
    "NCCL_SOCKET_IFNAME": "eth0"
  }
}
```

---

## TEST 1: The 2-Node Fast Cluster Smoke & Preflight Test

### Purpose & Objective
- **Why run it first?** Never launch an 8-hour or 16-hour run without verifying basic infrastructure. If passwordless SSH fails, Ray ports are blocked by a firewall, NCCL cannot allocate cross-node sockets, or `tc` permissions fail, an overnight run will fail within minutes.
- **What it accomplishes:**
  1. Validates all 103 configuration, schema, and matrix rules in under 15 seconds.
  2. Confirms inter-node hardware communication, raw TCP throughput via multi-stream `iperf3`, and multi-node NCCL collective bandwidth across all 16 GPUs.
  3. Verifies distributed vLLM startup over Ray using the critical **`tp4_pp2_dist`** topology (4 GPUs per node, 2 nodes) on short context (1K/8K tokens).

### Points-Wise Breakdown of What Test 1 Executes
1. **Static Validation Phase (`Phase 01`)**:
   - Inspects `deepseek_v41_flash.json` (or `kimi_linear_48b.json`), `my_cluster.json`, and `suite_default.json`.
   - Validates that GPU counts match topology requirements ($4 \times 2 \le 16$, $8 \times 2 = 16$).
   - Confirms memory headroom bounds, context anchor lengths, and output token allocations.
2. **Cluster Readiness Preflight (`Phase 02`)**:
   - Probes Node 0 and Node 1 via SSH.
   - Confirms NVIDIA driver presence and 8 healthy GPUs per node.
   - Checks write permissions in `/home/ubuntu/v9_bench` and verifies `tc` privilege.
3. **Model Weights Probe (`Phase 03`)**:
   - Reads HuggingFace `config.json` without loading weights into GPU VRAM.
   - Verifies model architecture (`deepseek_v3` / `deepseek_v2` / `llama`), MoE routing dimensions, and quantization format.
4. **Hardware & Network Smoke Sweeps (`Phase 04`)**:
   - **Local P2P Sweep**: Measures intra-node PCIe/NVLink bandwidth across all pairs on Node 0.
   - **Multi-Stream `iperf3`**: Runs 16 parallel TCP streams across Node 0 and Node 1 to measure network line rate.
   - **Multi-Node NCCL AllReduce**: Sweeps message sizes from 8 bytes to 512 MB across all 16 GPUs.
   - **Multi-Node NCCL SendRecv / Ring**: Evaluates inter-node point-to-point bandwidth.
   - **Multi-Node NCCL AllToAll**: Simulates MoE cross-node token dispatch.
5. **Distributed vLLM Inference Smoke Run (`Phase 09 Subset`)**:
   - Starts Ray cluster on Node 0 and connects Node 1 worker.
   - Launches vLLM server with:
     - Model: `deepseek-ai/DeepSeek-V4.1-Flash`
     - Tensor Parallel (`TP`): 4 (intra-node)
     - Pipeline Parallel (`PP`): 2 (inter-node)
     - Max Model Len: 8,192
   - Sends 2 warmup requests + 5 evaluation prompts (`1024` input tokens, `256` output tokens).
   - Validates HTTP 200 OK, valid token streaming, and correct TTFT/TPOT logging.
   - Gracefully stops the vLLM server and tears down Ray.

### Exact Wall-Clock Timings for Test 1
| Step | Operation | Duration | Cumulative Time |
|:---:|---|:---:|:---:|
| 1 | Static Contract Validation (`21_static_validate_v9.py`) | 12 sec | 0:00:12 |
| 2 | Remote Cluster Readiness & Environment Checks | 45 sec | 0:00:57 |
| 3 | Model Probe & Matrix Generation | 30 sec | 0:01:27 |
| 4 | Local GPU P2P Bandwidth Matrix (Node 0) | 2 min 30 sec | 0:03:57 |
| 5 | Inter-Node TCP Bandwidth Sweep (`iperf3`) | 1 min 15 sec | 0:05:12 |
| 6 | Multi-Node NCCL AllReduce Sweep (16 GPUs) | 3 min 45 sec | 0:08:57 |
| 7 | Multi-Node NCCL AllToAll & SendRecv Sweeps | 3 min 15 sec | 0:12:12 |
| 8 | Ray Cluster Initialization across 2 Nodes | 45 sec | 0:12:57 |
| 9 | Distributed vLLM Server Weight Loading (`tp4_pp2_dist`) | 2 min 45 sec | 0:15:42 |
| 10 | KV Cache Allocation & CUDA Graph Warmup | 45 sec | 0:16:27 |
| 11 | Benchmark Prompt Inferences (1K Context, c1) | 35 sec | 0:17:02 |
| 12 | Server Tear Down & Log Harvest | 25 sec | 0:17:27 |
| **Total** | **Test 1 Complete Wall-Clock Time** | **~17 – 22 Minutes** | **Max 25 Mins** |

### Step-by-Step Command Line to Run Test 1
```bash
cd ~/v9_bench/V9_FULL

# Disable long model sweeps and profilers; run smoke preflight and network verification
RUN_HW_PREP=0 \
RUN_NODE_LOCAL_HW=1 \
RUN_NETWORK_SMOKE=1 \
RUN_SINGLE_NODE=0 \
RUN_OPEN_LOOP=0 \
RUN_SCALEOUT=0 \
RUN_PROFILES=0 \
RUN_HEAVY_PROFILE=0 \
./00_run_v9_full.sh \
  configs/models/deepseek_v41_flash.json \
  configs/clusters/my_cluster.json \
  configs/suite_default.json
```

### Verification & Success Criteria for Test 1
1. **Exit Code:** Command exits with `rc = 0`.
2. **Evidence Logs Check:**
   ```bash
   cat ~/v9_full_results/*/logs/phase_status.jsonl
   ```
   All executed phases (`static_validate`, `readiness`, `hardware_network_smoke`) must show `"rc": 0`.
3. **Network Throughput Sanity Check:**
   - Raw TCP bandwidth between nodes $\ge 90\text{ Gbps}$ (on 100G+ interfaces).
   - Multi-Node NCCL AllReduce bus bandwidth $> 15\text{ GB/s}$ at 512 MB buffer size.

---

## TEST 2: The Core Model Characterization & Scale-Out Inference Suite (No Profilers)

### Purpose & Objective
- **Why run it?** This is the **complete empirical application characterization run**. It executes every single inference server configuration and benchmark point across all context lengths (1K to 1M) and all network environments (Native, 100G, 20G) without the heavy overhead of GPU profiler tracing.
- **What it accomplishes:**
  1. Produces the complete TTFT (Time to First Token), TPOT (Time per Output Token), total latency, and throughput dataset for both single-node and multi-node deployments.
  2. Evaluates context length elasticity from interactive (1K/8K) to extreme long-context (128K, 512K, and 1,000,000 tokens).
  3. Quantifies concurrency scaling (`c1`, `c2`, `c4`, `c8`).
  4. Measures chunked prefill efficiency (4K vs 8K vs 16K chunk sizes).
  5. Measures prompt prefix-caching speedups on 128K, 512K, and 1M prompts.
  6. Quantifies scale-out network sensitivity across 3 explicit fabric conditions (**Native ~173 Gbps**, **Capped 100G**, **Capped 20G**).

### Points-Wise Breakdown of What Test 2 Executes

#### Part 1: Single-Node Characterization (17 Server Configurations / 51 Benchmark Cases)
Executed on Node 0 across TP=4 and TP=8:
1. **Context Elasticity Baseline (`tp4_context_baseline`, `tp8_context_baseline`)**:
   - Context anchors tested: `1,024`, `8,192`, `131,072`, `524,288`, `1,000,000` tokens.
   - Compares fixed TP=4 vs TP=8 memory footprint and execution curves.
2. **Prefill Focus Runs (`tp4_prefill_focus`)**:
   - Short output (4 tokens) with contexts up to 1M. Measures pure prefill compute rate ($T_{\text{prefill}}$) and eliminates decode overhead.
3. **Decode Focus Runs (`tp4_decode_focus`)**:
   - Long output (512 tokens) with 1K and 8K contexts at concurrency 1 and 8. Measures pure memory-bandwidth-bound token generation latency (TPOT).
4. **Closed-Loop Concurrency Scaling (`tp4_closedloop_*`)**:
   - Concurrency sweeps (`c1`, `c2`, `c4`, `c8`) across 1K, 8K, 128K, 512K, and 1M tokens.
   - Determines server saturation, batching efficiency, and queuing delay before out-of-memory.
5. **Chunked Prefill Chunk Size Derivatives (`tp4_chunk4096`, `tp4_chunk8192`, `tp4_chunk16384`)**:
   - Tests `max_num_batched_tokens` at 4,096, 8,192, and 16,384 on 128K, 512K, and 1M inputs.
   - Quantifies the trade-off between prefill latency and decode jitter.
6. **Automatic Prefix Caching Hit Speedups (`tp4_prefix_*`)**:
   - Tests 128K, 512K, and 1M prompts where 99.8% of the prefix is reused with a unique 256-token query suffix.
   - Quantifies cache-hit TTFT reduction (typically 85–95% latency reduction).
7. **Isolated Experimental Feature Probes (`tp4_kv_fp8_probe`, `tp8_ep_probe`)**:
   - Tests `--kv-cache-dtype fp8` to verify memory reduction without precision divergence.
   - Tests `--enable-expert-parallel` for DeepSeek MoE expert routing.

#### Part 2: Open-Loop Arrival Rate & Poisson Traffic Testing
- Measures admission gating, request queue latencies, and service-level objective (SLO) compliance under Poisson distributed arrival traffic.

#### Part 3: Multi-Node Distributed Scale-Out Matrix (5 Server Configurations / 30 Benchmark Cases)
Executed across Node 0 and Node 1 (16 GPUs total) under 3 network states (**Native**, **Capped 100G**, **Capped 20G**):
1. **`tp4_pp2_dist` (Clean Scale-Out Control)**:
   - 4 GPUs per node (TP4 local to each node via NVLink/PCIe), 2 pipeline stages across the 100G/20G Ethernet network.
   - Contexts: 1K, 8K, 128K, 512K, 1M.
   - Network modes: Native, 100G, 20G.
2. **`tp8_pp2_dist` (Saturated 16-GPU Setup)**:
   - 8 GPUs per node (TP8 local), 2 pipeline stages inter-node. Saturates all 16 GPUs across both nodes.
3. **`tp4_pp4_dist` (Deep Pipeline Scaling)**:
   - 4 pipeline stages total (2 stages per node). Tests inter-stage bubble overhead.
4. **`tp16_pp1_dist` (Global Cross-Node Tensor Parallelism)**:
   - 16 GPUs in a single TP group. AllReduce occurs across the inter-node Ethernet fabric on *every single transformer layer*.
   - Demonstrates the catastrophic impact of Ethernet latency on tensor parallelism compared to pipeline parallelism.
5. **`tp8_pp2_ep_dist` (Distributed MoE Expert Parallelism)**:
   - Evaluates cross-node MoE token routing efficiency on 8K and 128K contexts.

### Exact Wall-Clock Timings for Test 2
The timing depends on context token count and prompt processing:
- `1K Context` (input 1,024, output 256): ~2.5 sec / prompt
- `8K Context` (input 8,192, output 256): ~6.0 sec / prompt
- `128K Context` (input 131,072, output 128): ~35 sec / prompt
- `512K Context` (input 524,288, output 64): ~120 sec / prompt
- `1M Context` (input 1,000,000, output 32): ~240 sec / prompt

| Test Component | Server Launches | Total Prompts | Avg Time per Case | Wall-Clock Time |
|---|:---:|:---:|:---:|:---:|
| Hardware Preflight & Network Smoke | — | — | — | **~18 Mins** |
| Single-Node Baselines (1K to 1M) | 2 | 10 | ~25 mins | **~50 Mins** |
| Prefill & Decode Specializations | 2 | 8 | ~15 mins | **~30 Mins** |
| Closed-Loop Concurrency Sweeps (c1–c8) | 5 | 20 | ~22 mins | **~1 Hour 50 Mins** |
| Chunk Size Derivatives (4K, 8K, 16K) | 3 | 9 | ~18 mins | **~55 Mins** |
| Prefix Caching Hit Evaluations | 3 | 6 | ~12 mins | **~36 Mins** |
| Isolated Feature Probes (FP8 KV, EP) | 2 | 3 | ~10 mins | **~20 Mins** |
| Open-Loop Arrival Rate Testing | 1 | 150 (Poisson) | ~35 mins | **~35 Mins** |
| Multi-Node `tp4_pp2_dist` (Native, 100G, 20G) | 3 | 18 | ~15 mins | **~45 Mins** |
| Multi-Node `tp8_pp2_dist` (Native, 100G, 20G) | 3 | 18 | ~18 mins | **~54 Mins** |
| Multi-Node `tp4_pp4_dist` (Native, 100G, 20G) | 3 | 18 | ~15 mins | **~45 Mins** |
| Multi-Node `tp16_pp1_dist` (Cross-Node TP) | 3 | 18 | ~22 mins | **~1 Hour 05 Mins** |
| Multi-Node `tp8_pp2_ep_dist` (MoE Native) | 1 | 2 | ~12 mins | **~12 Mins** |
| Diagnostics & Evidence Processing | — | — | — | **~15 Mins** |
| **Total** | **28 Server Launches** | **81 Benchmark Runs** | | **~6.0 – 7.5 Hours** |

### Step-by-Step Command Line to Run Test 2
```bash
cd ~/v9_bench/V9_FULL

# Run all application inference benchmarks; skip heavy GPU kernel profiler captures
RUN_HW_PREP=0 \
RUN_NODE_LOCAL_HW=1 \
RUN_NETWORK_SMOKE=1 \
RUN_SINGLE_NODE=1 \
RUN_OPEN_LOOP=1 \
RUN_SCALEOUT=1 \
RUN_PROFILES=0 \
RUN_HEAVY_PROFILE=0 \
./00_run_v9_full.sh \
  configs/models/deepseek_v41_flash.json \
  configs/clusters/my_cluster.json \
  configs/suite_default.json
```

---

## TEST 3: The Full Production Characterization & Deep Nsight/Torch Profiling (Overnight Complete Run)

### Purpose & Objective
- **Why run it?** This is the **definitive gold-standard characterization suite**. It executes every single element of Test 2 PLUS **35 deep GPU kernel execution traces** using NVIDIA Nsight Systems (`nsys`) and PyTorch Profiler (`torch.profiler`).
- **What it accomplishes:**
  1. Captures deep hardware telemetry: exact SM utilization, Tensor Core activity, memory bandwidth saturation, and kernel execution times.
  2. Pinpoints NCCL collective latency: measures the exact microseconds spent in `ncclKernel_AllReduce`, `ncclKernel_AllToAll`, and P2P communication across the network under Native, 100G, and 20G conditions.
  3. Produces publication-grade evidence, timeline traces (`.nsys-rep`, `.json.gz`), and automated diagnostics required for complete architectural sign-off.

### Points-Wise Breakdown of What Test 3 Executes
Test 3 runs the **full 13-phase end-to-end pipeline**:
1. **Phases 01–06**: Static verification, hardware preparation, node-local benchmarks, multi-node network smoke sweeps, model probing, and benchmark matrix generation.
2. **Phase 07**: All 51 single-node vLLM benchmark runs.
3. **Phase 08**: Open-loop Poisson queue admission benchmarks.
4. **Phase 09**: All 30 multi-node scale-out serving benchmarks.
5. **Phase 10: Deep Profiler Matrix (35 Comprehensive Traces)**:
   - **Multi-Node Distributed Traces (25 Captures)**:
     - `tp4_pp2_dist`: Prefill at 1K, 128K, 512K; interactive decode at 8K c1 and 8K c8; network degradation traces under 100G and 20G. *(9 traces)*
     - `tp8_pp2_dist`: Prefill and decode traces under Native, 100G, and 20G. *(6 traces)*
     - `tp4_pp4_dist`: Pipeline bubble and inter-node transfer traces under Native, 100G, and 20G. *(6 traces)*
     - `tp16_pp1_dist`: Cross-node AllReduce collective barrier traces under Native, 100G, and 20G. *(9 traces)*
     - `tp8_pp2_ep_dist`: Cross-node MoE token routing AllToAll trace. *(1 trace)*
   - **Single-Node Traces (10 Captures)**:
     - TP4: 1K prefill, 8K decode, 128K prefill, 512K prefill, 8K c8 batched decode. *(5 traces)*
     - TP8: 1K prefill, 8K decode, 128K prefill, 512K prefill, 8K c8 batched decode. *(5 traces)*
6. **Phase 11: Runtime Diagnostics & Profiler Analysis**:
   - Automatically parses all Nsight SQLite databases and PyTorch JSON traces.
   - Extracts top-10 longest executing kernels, memory transfer bandwidth, and collective communication overhead.
7. **Phase 12: Collect and Validate (`90_collect_and_validate_v9.py`)**:
   - Enforces strict audit sign-off against all 103 contract invariants.
8. **Phase 13: Package Results (`99_package_v9_full_results.sh`)**:
   - Bundles all raw logs, processed JSONs, timeline traces, and CSV summaries into a compressed distribution archive (`V9_FULL_EVIDENCE_<RUN_ID>.tar.gz`).

### Exact Wall-Clock Timings for Test 3
Profiler runs require restarting the vLLM engine with profiling hooks, disabling CUDA graph memory caching to trace distinct kernel launches, capturing traces to disk, and exporting traces to SQLite/CSV:
- Average profiler capture duration: ~8 to 12 minutes per trace capture.
- 35 traces $\times$ ~10 minutes average = **~5.5 to 6.5 Hours of profiling overhead**.

| Pipeline Phase | Description | Wall-Clock Time |
|---|---|:---:|
| **Phase 01–06** | Preflight, Hardware Prep & Network Sweeps | **~25 Mins** |
| **Phase 07** | 51 Single-Node Model Benchmarks (1K to 1M) | **~4 Hours 15 Mins** |
| **Phase 08** | Open-Loop Poisson Traffic Testing | **~35 Mins** |
| **Phase 09** | 30 Multi-Node Scale-Out Serving Benchmarks | **~2 Hours 20 Mins** |
| **Phase 10** | 35 Deep Nsight & PyTorch Profiler Traces | **~5 Hours 45 Mins** |
| **Phase 11** | Runtime Diagnostics & SQL Trace Parsing | **~45 Mins** |
| **Phase 12–13** | Strict Contract Validation & Packaging | **~20 Mins** |
| **Total** | **Full 13-Phase Test 3 Execution** | **~13.5 – 15.5 Hours** |

### Step-by-Step Command Line to Run Test 3 (Overnight Run)
Because Test 3 runs for ~14 hours, it should be launched with `nohup` inside a dedicated `tmux` or `screen` session:

```bash
cd ~/v9_bench/V9_FULL

# Launch full 13-phase suite with background persistence
nohup ./00_run_v9_full.sh \
  configs/models/deepseek_v41_flash.json \
  configs/clusters/my_cluster.json \
  configs/suite_default.json \
  > v9_full_production.log 2>&1 &
```

---

## Live Monitoring, Progress Tracking & Troubleshooting

### 1. Real-Time Phase Monitoring
Follow the JSONL phase status tracker to view exact progress:
```bash
tail -f ~/v9_full_results/*/logs/phase_status.jsonl
```
Example output:
```json
{"time":"2026-09-28T00:00:15+00:00","phase":"static_validate","rc":0}
{"time":"2026-09-28T00:01:05+00:00","phase":"readiness","rc":0}
{"time":"2026-09-28T00:18:42+00:00","phase":"hardware_network_smoke","rc":0}
{"time":"2026-09-28T04:35:10+00:00","phase":"vllm_single","rc":0}
{"time":"2026-09-28T05:10:20+00:00","phase":"vllm_openloop","rc":0}
{"time":"2026-09-28T07:30:15+00:00","phase":"vllm_scaleout","rc":0}
{"time":"2026-09-28T13:15:40+00:00","phase":"profiles","rc":0}
{"time":"2026-09-28T14:00:10+00:00","phase":"runtime_diagnostics","rc":0}
{"time":"2026-09-28T14:20:05+00:00","phase":"package_results","rc":0}
{"time":"2026-09-28T14:20:30+00:00","phase":"strict_signoff","rc":0}
```

### 2. Multi-Node GPU Utilization Monitoring
Watch GPU memory and compute across both nodes in real time:
```bash
# Node 0
watch -n 1 nvidia-smi

# Node 1 (via SSH in a separate pane)
ssh node1 "watch -n 1 nvidia-smi"
```

### 3. Fail-Safe Resume Mechanism
If a network disconnect or transient error halts the run at hour 7, you **do not lose any work**:
```bash
# Re-run with V9FULL_RESUME=1; completed phases will be automatically skipped
cd ~/v9_bench/V9_FULL
V9FULL_RESUME=1 ./00_run_v9_full.sh \
  configs/models/deepseek_v41_flash.json \
  configs/clusters/my_cluster.json \
  configs/suite_default.json
```

---

## Final Comparison & Decision Matrix

| Dimension | TEST 1: Smoke Test | TEST 2: Core Benchmark | TEST 3: Full Production |
|---|---|---|---|
| **Primary Goal** | Infrastructure & Connectivity Proof | Throughput & Latency Characterization | Exhaustive Profiling & Architectural Sign-Off |
| **Wall-Clock Time** | **~15 – 30 Minutes** | **~6 – 7.5 Hours** | **~13 – 16 Hours** |
| **GPU Profiling Overhead** | None | None | 35 Nsight & PyTorch captures (~6 hrs) |
| **Single-Node Model Tests** | 0 (or minimal sanity) | 51 benchmarks (1K to 1M) | 51 benchmarks (1K to 1M) |
| **Scale-Out Distributed Tests** | 1 case (`tp4_pp2_dist` short context) | 30 benchmarks (Native, 100G, 20G) | 30 benchmarks (Native, 100G, 20G) |
| **Network Fabric Degradation** | Synthetic smoke (`tc` verification) | Full vLLM serving under 100G & 20G | Full vLLM serving + deep kernel profiling |
| **Recommended Window** | Day 1 Morning (Immediate) | Day 1 Afternoon | Day 1 Overnight |
| **Evidence Output** | Smoke validation log | Complete latency & throughput dataset | Full publication bundle with GPU traces |
