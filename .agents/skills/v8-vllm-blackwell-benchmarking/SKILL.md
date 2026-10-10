---
name: v8-vllm-blackwell-benchmarking
description: Comprehensive runbook, post-mortem, and optimization knowledge base for benchmarking, profiling, and optimizing LLMs/MoE models (e.g. Kimi-Linear 48B) on NVIDIA Blackwell/RTX PRO 6000 multi-GPU clusters using vLLM, FlashInfer CUTLASS, Torch Profiler, and PyTorch/Gloo/NCCL.
---

# V8 vLLM Blackwell & RTX PRO 6000 Benchmarking & Optimization Skill

This skill documents all architectural decisions, hard-won root-cause fixes, runtime environment configurations, and execution best practices developed across the end-to-end benchmarking campaign (Pilot $\rightarrow$ Stage 3 $\rightarrow$ Stage 1 $\rightarrow$ Stage 2) for large Mixture-of-Experts (MoE) models (specifically **Kimi-Linear-48B-A3B-Instruct**) on multi-GPU clusters of **NVIDIA RTX PRO 6000 Blackwell / Ada Generation GPUs** (16x GPUs across dual-node GCP instances `kimi-node-0` and `kimi-node-1`).

Use this guide whenever deploying, benchmarking, or profiling any new model using this pipeline to ensure zero repetitive failures, optimal kernel selection, and deterministic execution.

---

## 1. System & Target Architecture Overview

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Cluster Topology** | 2 Nodes (`kimi-node-0`, `kimi-node-1`) | GCP `us-central1-b` VPC |
| **Node Hardware** | 8x NVIDIA RTX PRO 6000 GPUs per node (16x total) | PCIe Gen5 topology (No inter-node NVLink) |
| **Host Interconnect** | High-performance VPC Virtual NIC (`ens3`) | Line rate ~100 Gbps, TCP socket transport |
| **Model** | `moonshotai/Kimi-Linear-48B-A3B-Instruct` | 48B total params, ~3B active per token |
| **MoE Architecture** | 64 routed experts, Top-6 routing, shared experts | Heavy GEMM / All-to-All / Reduce communication |
| **Attention Mechanism**| Hybrid Linear Attention + Sliding Window Attention (SWA) | Chunk-based prefill and low KV cache footprint |
| **vLLM Engine** | vLLM v0.6.x+ with V6/V8 custom optimization patches | FlashInfer backend with C++ CUTLASS kernels |

---

## 2. Core Evolution: Pilot Baseline vs. Current Optimized Runs

### 2.1 The MoE Kernel Transition: Triton vs. FlashInfer CUTLASS
* **Pilot Baseline Configuration**:
  - Ran **Triton MoE** (`TritonExperts`).
  - Performance: **931 ms TTFT**, **10.89 ms TPOT** at Concurrency $c=8$ ($8192 \rightarrow 256$).
* **Optimized Runs (Stage 1 / Stage 3 / Current)**:
  - Runs **FlashInfer CUTLASS MoE** (`FlashInferExperts`).
  - Performance: **653 ms TTFT** (~29.9% faster), **7.72 ms TPOT** (~29.1% faster) at $c=8$.
  - Per-iteration decode times drop from ~8.5 ms down to **5.61 ms – 5.85 ms**.

### 2.2 Why Multi-Node Showed Higher Latencies (~46 ms TPOT)
* In early multi-node Stage 2 runs (`20261005_210750`), latencies reached ~46 ms. This was **not** a regression of CUTLASS vs. Triton.
* Root cause:
  1. **Inter-Node VPC Socket Overhead**: TP/PP ranks crossing physical host boundaries via `NCCL_NET=Socket` on virtual network interfaces incur TCP stack latency compared to single-node intra-PCIe transfers.
  2. **Host RAM Offloading**: Offloading KV cache or weights across PCIe and system memory (`02_cpu_offload_reuse`) throttles memory bandwidth.
* On identical single-node hardware, **FlashInfer CUTLASS consistently outperforms Triton by ~29%**.

---

## 3. The FlashInfer Autotune Deadlock Post-Mortem (CRITICAL PITFALL)

### 3.1 The Failure Mode
When launching vLLM with `--optimization-level 2`, vLLM automatically enables FlashInfer autotuning (`enable_flashinfer_autotune: True`).
Under the hood in `vllm/model_executor/layers/fused_moe/oracle/unquantized.py`, the autotuner evaluates candidates in this order:
```python
[FLASHINFER_TRTLLM, FLASHINFER_CUTLASS, TRITON, BATCHED_TRITON]
```

When evaluating candidate #1 (`FLASHINFER_TRTLLM`), FlashInfer invokes TensorRT-LLM MoE kernels (`trtllm::fused_moe::gemm1`, `trtllm::fused_moe::gemm2`).
On multi-GPU setups without hardware NVLink (such as PCIe RTX PRO 6000 nodes), rank 0 and worker ranks execute non-collective CUDA probe paths, triggering an asymmetric collective barrier.
Worker ranks hang waiting on Gloo TCP socket receive:
```text
Gloo TCP socket timed out after 1800000 ms (30.0 minutes)
```
The server freezes during model weight loading and crashes 30 minutes later.

### 3.2 The Definitive Fix
Blacklist the hanging TRT-LLM ops before running vLLM by setting this environment export:

```bash
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"
```

* **Effect**: The oracle skips candidate #1 immediately and selects candidate #2 (**`FLASHINFER_CUTLASS`**).
* **Result**: Startup time plummets from **1,800 seconds (hang)** to **14 seconds (200 OK)**!

### 3.3 Orphaned Multiprocessing Workers & VRAM Lockout (CRITICAL GOTCHA)
* **Failure Mode**: When vLLM server processes stop or restart between benchmark cases, worker processes (`VLLM::Worker_TP*`) can become orphaned if only the parent API server process is terminated.
* **Symptom**: Each orphaned worker holds ~88 GiB of VRAM per GPU. The next server startup crashes within 5 seconds with:
  ```text
  ValueError: Free memory on device cuda:0 (8.15/94.97 GiB) on startup is less than desired GPU memory utilization (0.9, 85.47 GiB).
  ```
* **Enforced Resolution**:
  1. In `v5_runner_lib.py`, `kill_process_group` explicitly executes:
     ```python
     subprocess.run(['pkill', '-9', '-f', 'VLLM::Worker'], check=False)
     subprocess.run(['pkill', '-9', '-f', 'vllm serve'], check=False)
     time.sleep(2)
     ```
  2. In `11_run_vllm_surrogate.py`, a pre-flight VRAM cleanup is enforced before spawning any new server process.
  3. All launch scripts verify `nvidia-smi --query-compute-apps=pid,process_name --format=csv` is completely empty before proceeding.

---

## 4. Golden Environment Exports & Configuration Reference

Every launch script (single-node, dual-node, profiler, and benchmark harness) MUST export these variables:

```bash
# ==============================================================================
# 1. FlashInfer & MoE Kernel Configuration
# ==============================================================================
# Prevent 30-minute Gloo deadlock; force FlashInfer CUTLASS
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"

# ==============================================================================
# 2. Host OS & Systemd Process Persistence (CRITICAL)
# ==============================================================================
# Prevent systemd-logind from terminating user tmux / vLLM sessions upon SSH disconnect:
sudo loginctl enable-linger $USER
# Verify: `loginctl show-user $USER | grep Linger` must output `Linger=yes`

# ==============================================================================
# 3. CUDA & Device Isolation
# ==============================================================================
# Enforce deterministic physical PCI bus ordering
export CUDA_DEVICE_ORDER="PCI_BUS_ID"
# Explicitly set per run/rank (e.g. "0,1,2,3" for TP4 or "0,1,2,3,4,5,6,7" for TP8)
# export CUDA_VISIBLE_DEVICES="0,1,2,3"

# ==============================================================================
# 3. Inter-Node & Multi-GPU Networking (NCCL / Gloo)
# Note: Automatically handled by `20_nccl_policy.sh` & wrapper scripts!
# - For SINGLE-NODE runs: `20_run_single_node_v6_aligned.sh` automatically unsets
#   all NCCL_* network variables, enforcing pure PCIe Gen5 P2P / SHM direct DMA.
# - For MULTI-NODE runs: `nccl_remote_v6_aligned_exports` automatically injects:
# ==============================================================================
# Multi-node GCP VPC socket settings (only applied across nodes):
export NCCL_NET="Socket"
export NCCL_SOCKET_IFNAME="ens3"
export NCCL_CROSS_NIC=1
export NCCL_BUFFSIZE=4194304
export NCCL_DEBUG="INFO"
export NCCL_DEBUG_SUBSYS="INIT,COLL,ENV"
export LD_LIBRARY_PATH="/tmp/clean_nccl_libs:${LD_LIBRARY_PATH:-}"

# Gloo TCP tuning for distributed rendezvous
export GLOO_SOCKET_IFNAME="ens3"

# ==============================================================================
# 4. vLLM Engine Optimization Flags
# ==============================================================================
VLLM_SERVER_FLAGS=(
  "--model" "moonshotai/Kimi-Linear-48B-A3B-Instruct"
  "--trust-remote-code"
  "--tensor-parallel-size" "$TP"
  "--pipeline-parallel-size" "$PP"
  "--optimization-level" "2"
  "--max-num-batched-tokens" "8192"   # Or 8448 for chunk-budget alignment
  "--max-num-seqs" "32"
  "--kv-cache-dtype" "auto"
  "--gpu-memory-utilization" "0.90"
  "--enforce-eager"                   # Set to False / omitted when CUDA graphs active
  "--disable-log-requests"
)
```

---

## 5. Architectural Deep Dives & Optimization Insights

### 5.1 Chunk Budget Alignment (8192 vs. 8448)
* In Kimi-Linear, prompt prefill chunks are processed in batch tokens.
* When input length is exactly 8192, setting `--max-num-batched-tokens 8192` causes prefill requests to saturate the entire budget in one step, potentially stalling concurrent decodes.
* Increasing the chunk budget to **8448** provides headroom for ongoing decode iterations alongside prefill chunks, preventing decode starvation and smoothing Inter-Token Latency (ITL).

### 5.2 NUMA Pinning & CPU Affinity
* On dual-socket AMD EPYC / Intel Xeon hosts powering 8x RTX PRO 6000 GPUs, GPUs 0-3 belong to NUMA node 0 and GPUs 4-7 belong to NUMA node 1.
* In our Stage 1 diagnostics (`s1_04_tp8_numa_pinning_evaluation`), we benchmarked:
  - **Unpinned Mean TPOT**: `6.891 ms`
  - **Pinned Mean TPOT (CPUs 96-191, 288-383)**: `6.883 ms`
  - **Delta**: `-0.008 ms` (~0.12% variance)
* **Takeaway**: Kernel execution is heavily GPU-bound (GEMM and VRAM memory bandwidth); CPU thread scheduling latency has minimal impact on TPOT once CUDA graphs are captured.

### 5.3 Safety Gates & Surrogate Error Trapping
* **The Silent Failure Trap**: In early test runners, `11_run_vllm_surrogate.py` caught exceptions in a `try...except` block, logged them to `case_manifest.json`, and exited with code `0`. Upstream orchestrators saw `rc: 0` and marked steps as `.done`, masking failed runs.
* **The Enforcement Rule**: Always validate completion:
  ```python
  if any(c.get("error") for c in top["cases"]):
      raise RuntimeError(f"Case execution failed: {[c.get('error') for c in top['cases']]}")
  ```

---

## 6. Profiling Recipes

### 6.1 PyTorch Profiler: Pure Decode Window (`14c_run_vllm_torch_profile_batched.sh`)
* **Objective**: Isolate steady-state token generation without prefill noise.
* **Configuration**:
  - Warmup: 2 steps
  - Active capture: 5 steps
  - Profile root: exports `.pt.trace.json.gz` viewable in `chrome://tracing` or Perfetto.
* **Key Metrics Observed**:
  - MoE Dispatch & Gemm kernel time: ~3.8 ms per step.
  - AllReduce / All-to-All communication: ~1.4 ms per step.
  - CUDA Graph replay overhead: <0.1 ms.

### 6.2 Prometheus Live Metrics Scraper (`09_metrics_sampler.py`)
* Runs asynchronously alongside `vllm bench serve`, polling `http://127.0.0.1:$PORT/metrics` every 500 ms.
* Captures:
  - `vllm:avg_prompt_throughput_tok_per_s`
  - `vllm:avg_generation_throughput_tok_per_s`
  - `vllm:gpu_cache_usage_factor`
  - `vllm:iteration_tokens_total`

---

## 7. Runbook: Testing a New Model with This Pipeline

When onboarding a new model (e.g. DeepSeek-V3, Qwen-2.5-72B, Mixtral, or new MoE):

1. **Phase 0: Pre-Flight Environment Sanity**
   ```bash
   # Verify all GPUs visible and PCIe links at full speed
   nvidia-smi --query-gpu=index,name,pci.bus_id,pcie.link.gen.current,pcie.link.width.current --format=csv
   # Verify port accessibility and clean Ray state
   ray stop -f 2>/dev/null || true
   ```

2. **Phase 1: MoE Autotune Probe**
   - Check if the model uses MoE layers (`model.layers[*].block_sparse_moe` or `moe_experts`).
   - If using MoE on PCIe GPUs, **always export `VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS`**.
   - Perform a 1-request smoke test to confirm model loads cleanly within <60 seconds.

3. **Phase 2: Single-Node Baseline & Chunk Calibration (Stage 1)**
   - Test TP=4 and TP=8 on single node.
   - Run short prompt baseline ($1024 \rightarrow 128$) to establish lowest-latency ceiling.
   - Run chunk budget test ($8192 \rightarrow 256$) with concurrency sweep ($c=1, 2, 4, 8, 16, 32$).

4. **Phase 3: Scale-Out Distributed Sweeps (Stage 2)**
   - Ensure `kimi-node-1` has matching model weights and environment.
   - Launch multi-node server with Ray or torchrun using `NCCL_NET=Socket`.
   - Run concurrency load sweeps up to $c=64$.

5. **Phase 4: Resilience & Deep Profiles (Stage 3)**
   - Context length curve from 16K up to 256K/512K.
   - Multi-bandwidth traffic shaping (simulate 100G cap, 20G cap, jitter/packet loss via Linux `tc qdisc`).
   - Prefix cache hit decay evaluation.

---

## 8. Summary Checklist Before Running Any Benchmark

- [ ] `export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"` is active.
- [ ] `CUDA_DEVICE_ORDER="PCI_BUS_ID"` is set.
- [ ] No stale vLLM or Ray processes running (`pkill -9 -f vllm`).
- [ ] Warmup requests run separately before telemetry measurement window starts.
- [ ] Result JSON validation enabled (`parse_result` checks that `successful_requests > 0`).
- [ ] Linux Traffic Control (`tc qdisc`) is cleared to native line rate unless deliberately benchmarking network caps.
