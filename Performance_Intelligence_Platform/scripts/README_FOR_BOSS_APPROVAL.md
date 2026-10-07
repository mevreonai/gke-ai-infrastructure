# Technical Specification & Run Package: Platform Characterization Gap Closures

**Target Infrastructure**: Dual-Node 16× NVIDIA RTX PRO 6000 Blackwell Server Edition (8 GPUs/node, 48 GB VRAM/GPU)  
**Model**: Moonshot Kimi-Linear-48B-A3B-Instruct BF16 (`e1df551a447157d4658b573f9a695d57658590e9`)  
**Package Version**: v1.4 (Addresses all findings from Code Review v1.0)  

---

## 1. Verified Pilot Findings (Zero Machine Cost)

Direct inspection of the pilot's local logs (`Performance_Intelligence_Platform/results/real_data/.../server.log`) settled three major questions before executing any cluster commands:

1. **8-GPU KV Cache Pool Size (Item 5 answered outright)**:
   * **TP4 Pool Size**: **8,141,673 tokens** (15,886 GPU blocks of 512 tokens). Maximum concurrency for 1,048,576 tokens: **7.76×**.
   * **TP8 Pool Size**: **8,214,143 tokens** (16,043 GPU blocks of 512 tokens). Maximum concurrency for 1,048,576 tokens: **7.83×**.
   * *Conclusion*: KV pool size is essentially invariant between TP4 and TP8 (+0.9% on TP8). TP8 saves ~11.5 GB/GPU of weight memory, but MLA KV head layout distributes tokens across 8 ranks.

2. **Root Cause of Failed FP8 KV Server Start (`tp4_fp8_kv/server.log`)**:
   * Exact exception:  
     `AssertionError: Kimi-K3 fp8 KV cache requires an fp8 prefill query; enable --attention-config '{"use_prefill_query_quantization": true}'.`
   * *Fix*: Implemented `--attention-config '{"use_prefill_query_quantization": true}'` and enforced via `require_flag`.

3. **Root Cause of Failed Offload Server Start (`tp4_native_offload_pressure/server.log`)**:
   * Exact exception:  
     `ValueError: To serve at least one request with the model's max seq len (1048576), 7.89 GiB KV cache is needed, which is larger than the available KV cache memory (4.0 GiB). Based on the available memory, the estimated maximum model length is 530432.`
   * *Fix*: Designed as a true eviction/reload reuse test with prefix caching enabled: Prompt A (600K) -> Prompt B (600K, forces eviction to CPU) -> Revisit A (reloads from CPU memory).

---

## 2. Summary of Implemented Code Fixes

| Code Review Item | Finding in v1.0 | Implementation in v1.4 |
| :--- | :--- | :--- |
| **C1 · TP8 Pinning** | `numactl` or `CUDA_VISIBLE_DEVICES` did not pin individual workers to local NUMA nodes. | Script boots TP8 server, runs 8K c1 unpinned control, dynamically queries worker PIDs via `nvidia-smi`, pins each worker to its GPU's PCI bus local CPUs with `taskset -a -cp`, and reruns 8K c1 on the same server to test the 6.35 ms -> 5.2 ms hypothesis. |
| **C2 · PP2 15/12 Split** | Split wasn't exported and ran single-node. | Moved to two-node runner (`12_run_vllm_multi_node.sh`), exported `VLLM_PP_LAYER_PARTITION=15,12` to both nodes (including remote Ray workers), added default 14/13 control, tested TP4/PP2 and TP8/PP2 at 128K and 512K c1 to balance full-attention layers (stage 0 holds 3 of 7). |
| **C3 · NCCL Tuning** | Ran `iperf3` instead of NCCL; ignored NCCL variables. | Rewrote to execute `nccl-tests` (`all_reduce_perf` 16K and `sendrecv_perf` 256M) via `mpirun` across Baseline, 4×4 threads, 8×2 threads, and provider plugin variants with `NCCL_DEBUG=INFO`. |
| **C4 · Nsight Export** | Sleep occurred after copy; 0-byte reports counted as complete. | Implemented `wait_nsys` loop on both nodes waiting for Nsys daemons to exit and report file sizes to stabilize > 0 bytes *before* copying and stopping Ray. |
| **C5 · KV & Trace Audit** | Read non-existent keys; trimmed arbitrary 10%. | Rewrote `24_audit_kv_and_trim_traces.py` to parse `vllm:cache_config_info` and `server.log`, and trim exactly by E2E C/D definition (drop first $C$ requests from TTFT, drop last $C$ requests from ITL/TPOT). Tested and verified against pilot data. |
| **C6 · KV Offload** | 8.5 GiB held 1.13M tokens; offload was never exercised. | Configured true eviction & reload test with `--enable-prefix-caching` using cold Prompt A -> cold Prompt B (evicts A) -> revisit A (reloads from CPU). |
| **H1 · FP8 1M Point** | Rerun dropped 1M point; flag wasn't validated. | Restored full 4-point matrix (`128k_c1`, `128k_c4`, `512k_c1`, `1m_c1`) + `8k_c8`. Flag is strictly enforced via `require_flag`. |
| **H2 · Torch Profiling** | Profile window captured mostly prefill. | Removed `--profile`, extended output to 1024 tokens, and triggered `/start_profile` via HTTP after prefills complete to capture a pure decode window with CUDA graphs on. |
| **H3 · 8K Chunk A/B** | Different wave counts; no same-session control. | Matched pilot counts (c4: 24 prompts, c32: 128 prompts) and added a same-session 8,192 chunk budget control run. |
| **M1–M3 · Multi-Node & Packaging** | Network label unchecked; Windows zip lacked Unix execute bits. | Added native network provenance enforcement, 5 waves at 128K, automated SHA256 checksums, dual-node environment snapshotting, and POSIX `0o755` executable packaging. |

---

## 3. Workload Breakdown & Execution Time

| Stage | Target Area | Workload Details | Machine Time |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **8K Chunk Budget A/B** | 8K at $c=4$ (24 prompts) and $c=32$ (128 prompts): 8192 control vs 8448 fix | **15 min** |
| **Stage 1** | **Batched Torch Profile** | TP4 at 8K $c=8$ and $c=32$ (pure decode capture via `/start_profile`) | **10 min** |
| **Stage 1** | **NCCL Multi-Socket Tuning** | `nccl-tests` 16K AllReduce & 256M SendRecv across 4 transport variants | **15 min** |
| **Stage 1** | **TP8 NUMA Pinning** | Unpinned control vs pinned on same running server (PCI local CPU bind) | **20 min** |
| **Stage 1** | **Sub-8K Short Prompts** | 1K & 2K contexts across $c=1, 8, 32$ (128 prompts at c32) | **30 min** |
| **Stage 1** | **128K Chunk & Knee Repeats** | 128K chunk budget sensitivity (Plan A9) + 3× repeats of 8K/128K knee points | **25 min** |
| **Stage 1** | **KV Pool & Trace Audit** | Offline script auditing block usage and trimming burst/drain tail noise | **< 1 min** |
| **Subtotal** | **Stage 1 Total** | **High-Leverage Quick Wins & Diagnostics** | **~2.0 hours** |
| | | | |
| **Stage 2** | **4× FP8 KV Reruns** | With `--attention-config` at 128K ($c=1,4$), 512K ($c=1$), 1M ($c=1$), and 8K ($c=8$) | **35 min** |
| **Stage 2** | **CPU Offload Reuse Test** | Prefix caching eviction & revisit test with 32 GiB host offload | **45 min** |
| **Stage 2** | **Multi-Node Concurrency** | 4 layouts under load at 128K (5 waves at $c=2,4,8$) and 1M ($c=2,4$) | **75 min** |
| **Stage 2** | **2-Node PP2 15/12 Split** | TP4/PP2 and TP8/PP2 at 128K and 512K (15/12 split vs 14/13 control) | **30 min** |
| **Stage 2** | **Capped Profiles & TP16 512K**| 8 captures with `wait_nsys` barrier and file size validation > 0 bytes | **45 min** |
| **Subtotal** | **Stage 2 Total** | **Failed Runs Recovery, Scale-Out & Distributed Profiling** | **~3.5 hours** |
| **Total** | **Combined Suite** | **Comprehensive Platform Characterization Completion** | **~5.5 hours** |

---

## 4. Execution Commands

```bash
# Extract package
unzip platform_additional_runs_stage1_stage2.zip -d platform_additional_runs_suite
cd platform_additional_runs_suite
chmod +x *.sh rtx_g4_smoke_v5/*.sh rtx_g4_hardware_diagnostics/*.sh

# Option A: Run all gap closures end-to-end (~5.5 hours)
./00_run_master_additional_runs.sh --all

# Option B: Run Stage 1 only (~2.0 hours)
./00_run_master_additional_runs.sh --stage1-only

# Option C: Run Stage 2 only (~3.5 hours)
./00_run_master_additional_runs.sh --stage2-only
```
