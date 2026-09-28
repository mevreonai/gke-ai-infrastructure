# V8 Characterization Campaign: Missed, Guarded, and Non-Completed Runs Audit

> **Document Status**: Authoritative Technical Audit  
> **Scope**: **Strictly V8 Campaign Only** (`run_id: 20260921_195656`)  
> **Target Architecture**: NVIDIA RTX 6000 Ada (Blackwell B200 surrogate architecture: 27 layers, 20 KDA, 7 full-attention, 256 routed MoE experts, BF16 checkpoint, max model length 1,048,576 tokens)  
> **Canonical Sources**: [coverage.json](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/final_validation/coverage.json), [FINAL_VALIDATION.json](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/final_validation/FINAL_VALIDATION.json), [combined_vllm_runs.csv](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/final_validation/combined_vllm_runs.csv), [model_validation.json](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/model_validation.json), raw `server.log` files, distributed `PROFILE_VALIDATION.json` records, and [90_collect_and_validate.py](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/release_specs/suite_scripts/90_collect_and_validate.py).

---

## 1. Executive Summary

During the V8 characterization campaign, **126 application benchmark runs** and **22 distributed profiler runs** were systematically configured to evaluate single-node and multi-node serving performance across context lengths up to 1,000,000 tokens (1M).

Across the entire campaign:
- **0 runs failed mid-execution** (no unexpected crashes during benchmark measurements; `failed_count: 0`).
- **119 application benchmark runs successfully completed** (95 under Primary `GCP_NATIVE`, 12 under `GCP_CAPPED_100G`, and 12 under `GCP_CAPPED_20G`).
- **7 application benchmark runs were NOT_RUN** due to vLLM server startup rejections during backend initialization.
- **8 distributed profiler runs failed strict completion** out of 22 expected (3 completed the workload but had incomplete multi-rank Nsys exports; 5 were not captured or omitted from the final archive).
- **50G and 10G networks had 0 application runs** because they were explicitly specified as hardware-only microbenchmark sensitivity points, not application serving sweeps.

As recorded in canonical [FINAL_VALIDATION.json](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/final_validation/FINAL_VALIDATION.json):
```json
{
  "coverage_counts": { "COMPLETED": 119, "NOT_RUN": 7 },
  "failed_count": 0,
  "not_run_count": 7,
  "safety_skipped_count": 0,
  "distributed_profiles_expected": 22,
  "distributed_profile_validation_count": 17,
  "distributed_profiles_complete_count": 14,
  "profiles_all_complete": false,
  "serving_matrix_complete": false,
  "nccl_policy_ok": false,
  "strict_full_coverage": false,
  "full_suite_valid": false,
  "note": "Safety skips are scientifically valid evidence but prevent strict full-coverage sign-off. Missing results are never treated as zero."
}
```

This document details every omitted, guarded, incomplete, and out-of-scope run from V8, isolating the exact technical, architectural, and runtime root causes with verbatim log evidence.

---

## 2. High-Level Inventory of Non-Completed V8 Runs

| Category | Total Configured / Expected | Succeeded / Completed | Missed / Guarded / Incomplete | Primary Technical Cause |
|---|---:|---:|---:|---|
| **Application: FP8 KV Cache** | 4 runs | 0 | **4 NOT_RUN** | vLLM Kimi-K3 MLA kernel threw `AssertionError` requiring `--attention-config '{"use_prefill_query_quantization": true}'` |
| **Application: CPU KV Offload** | 3 runs | 0 | **3 NOT_RUN** | vLLM v1 engine threw `ValueError` because 4 GiB KV budget < 7.89 GiB required for 1 request of max sequence length |
| **Distributed Profiles: Native Decode** | 14 runs | 11 | **3 INCOMPLETE** | High-concurrency (`c8`) multi-rank Nsys export dropped rank reports (`node1` or `node0` `.nsys-rep` missing) |
| **Distributed Profiles: Capped Network** | 8 runs | 3 | **5 NOT CAPTURED** | `GCP_CAPPED_100G` TP16 report missing from archive; `GCP_CAPPED_20G` 4 profiles not ingested into validation tree |
| **Application: 50G & 10G Networks** | 0 configured | 0 | **0 (Out of Scope)** | Intentionally restricted to hardware transport (iperf/NCCL) microbenchmarks by suite design |

---

## 3. The 7 Application Runs Missed (`NOT_RUN`)

All 7 missed application runs occurred on single-node TP4 configurations. They were classified as `NOT_RUN` rather than `FAILED` because the vLLM server crashed during the initial pre-warmup/CUDA graph capture phase before any benchmark request could be issued or any test harness could measure output.

### 3.1 Ledger of the 7 NOT_RUN Rows

| # | Case ID | Benchmark | Scope | TP / PP | Nominal Context | Concurrency | Configured Feature | Root Cause |
|---|---|---|---|---:|---:|---:|---|---|
| **1** | `tp4_fp8_kv` | `128k_c1` | `SINGLE_V6_BASE` | TP4 / PP1 | 131,072 in / 128 out | 1 | `--kv-cache-dtype fp8` | MLA kernel prefill quantization assertion |
| **2** | `tp4_fp8_kv` | `128k_c4` | `SINGLE_V6_BASE` | TP4 / PP1 | 131,072 in / 128 out | 4 | `--kv-cache-dtype fp8` | MLA kernel prefill quantization assertion |
| **3** | `tp4_fp8_kv` | `512k_c1` | `SINGLE_V6_BASE` | TP4 / PP1 | 524,288 in / 64 out | 1 | `--kv-cache-dtype fp8` | MLA kernel prefill quantization assertion |
| **4** | `tp4_fp8_kv_1m` | `1m_c1` | `SINGLE_V8_1M_EXT` | TP4 / PP1 | 1,000,000 in / 32 out | 1 | `--kv-cache-dtype fp8` | MLA kernel prefill quantization assertion |
| **5** | `tp4_native_offload_pressure` | `128k_c1` | `SINGLE_V6_BASE` | TP4 / PP1 | 131,072 in / 64 out | 1 | `--kv-offloading-size 32` | 4 GiB KV budget < 7.89 GiB minimum engine floor |
| **6** | `tp4_native_offload_pressure` | `512k_c1` | `SINGLE_V6_BASE` | TP4 / PP1 | 524,288 in / 64 out | 1 | `--kv-offloading-size 32` | 4 GiB KV budget < 7.89 GiB minimum engine floor |
| **7** | `tp4_native_offload_pressure` | `1m_c1` | `SINGLE_V6_BASE` | TP4 / PP1 | 1,000,000 in / 32 out | 1 | `--kv-offloading-size 32` | 4 GiB KV budget < 7.89 GiB minimum engine floor |

---

### 3.2 Deep Dive: FP8 KV-Cache Sensitivity Runs (Rows 1–4)

#### Workload & Configuration Details
- **Test Intent**: Evaluate memory footprint reduction and TTFT/TPOT sensitivity when storing the multi-head latent attention (MLA) KV cache in 8-bit floating point (`fp8`) format, while leaving model weights in BF16.
- **Manifest Definition**:
  ```json
  {
    "name": "tp4_fp8_kv",
    "groups": ["kv_dtype", "long_context"],
    "purpose": "KV cache dtype sensitivity; model weights remain BF16 surrogate weights.",
    "kv_cache_dtype": "fp8"
  }
  ```
- **Conditional Requirement**: The suite manifest explicitly defined this as a conditional exploration:
  > *"Runs only if the installed vLLM/backend accepts fp8 KV for this model."*

#### Server Launch Command
```bash
/home/ayu23/vllm_env/bin/vllm serve moonshotai/Kimi-Linear-48B-A3B-Instruct \
  --model-impl vllm \
  --trust-remote-code \
  --revision e1df551a447157d4658b573f9a695d57658590e9 \
  --host 0.0.0.0 --port 8000 \
  --tensor-parallel-size 4 --pipeline-parallel-size 1 \
  --max-model-len 1048576 --max-num-batched-tokens 8192 \
  --kv-cache-dtype fp8 \
  --max-num-seqs 16 --gpu-memory-utilization 0.9 \
  --performance-mode balanced --optimization-level 2 \
  --no-enable-prefix-caching --kv-cache-metrics \
  --cudagraph-metrics --enable-mfu-metrics --enable-logging-iteration-details
```

#### Exact Failure Mechanism (from `server.log`)
During server startup, vLLM initialized worker processes and attempted to profile and capture piecewise breakable CUDA graphs (`Capturing CUDA graphs (PIECEWISE)`). During graph capture of the attention layer in `mla.py`, the model runner executed `_forward_prefill_fused()` and encountered an explicit Python assertion:

```text
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055] WorkerProc hit an exception.
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055] Traceback (most recent call last):
...
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]   File ".../vllm/models/kimi_k3/nvidia/mla.py", line 626, in forward
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]     attn_out, gate = self._forward_full_rank_q(positions, hidden_states)
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]   File ".../vllm/models/kimi_k3/nvidia/mla.py", line 615, in _forward_full_rank_q
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]     self._attention(positions, q, kv_c_normed, k_pe.unsqueeze(1), attn_out)
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]   File ".../vllm/models/kimi_k3/nvidia/mla.py", line 687, in _attention
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]     self._forward_prefill_fused(
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]   File ".../vllm/models/kimi_k3/nvidia/mla.py", line 1024, in _forward_prefill_fused
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055]     assert fp8_prefill, (
(Worker_TP3 pid=291580) ERROR 09-22 01:18:11 [multiproc_executor.py:1055] AssertionError: Kimi-K3 fp8 KV cache requires an fp8 prefill query; enable --attention-config '{"use_prefill_query_quantization": true}'.
...
RuntimeError: Engine core initialization failed. See root cause above. Failed core proc(s): {}
```

#### Why It Got Missed
1. The Kimi-K3 model architecture's MLA prefill kernel implementation in vLLM enforces coupled quantization: it refuses to operate with an FP8 KV cache unless query quantization during prefill is simultaneously activated.
2. The benchmark harness passed `--kv-cache-dtype fp8` but omitted `--attention-config '{"use_prefill_query_quantization": true}'`.
3. Worker processes aborted, the engine core shut down with exit code 1, and no benchmark requests could be issued.
4. **Scientific Integrity**: Because the backend rejected the configuration before benchmark execution, recording these 4 runs as `NOT_RUN` (with null metrics) prevents fabricating non-existent throughput or misrepresenting an unsupported kernel path as an OOM crash.

---

### 3.3 Deep Dive: CPU KV-Cache Native Offload Pressure Runs (Rows 5–7)

#### Workload & Configuration Details
- **Test Intent**: Artificially constrain GPU VRAM allocated to the KV cache to force vLLM's native CPU offload connector into active eviction and paging to system host RAM (DRAM) over PCIe.
- **Manifest Definition**:
  ```json
  {
    "name": "tp4_native_offload_pressure",
    "groups": ["offload", "long_context"],
    "purpose": "Deliberately pressure GPU KV and observe native CPU KV offload. Not a proxy for local SimpleCPUOffloadConnector.",
    "kv_cache_memory_bytes": 4294967296,
    "offload_gib": 32
  }
  ```

#### Server Launch Command
```bash
/home/ayu23/vllm_env/bin/vllm serve moonshotai/Kimi-Linear-48B-A3B-Instruct \
  --model-impl vllm \
  --trust-remote-code \
  --revision e1df551a447157d4658b573f9a695d57658590e9 \
  --host 0.0.0.0 --port 8000 \
  --tensor-parallel-size 4 --pipeline-parallel-size 1 \
  --max-model-len 1048576 --max-num-batched-tokens 8192 \
  --kv-cache-dtype auto --max-num-seqs 8 \
  --kv-cache-memory-bytes 4294967296 \
  --performance-mode balanced --optimization-level 2 \
  --no-enable-prefix-caching \
  --kv-offloading-size 32 --kv-offloading-backend native \
  --kv-cache-metrics --cudagraph-metrics --enable-mfu-metrics --enable-logging-iteration-details
```

#### Exact Failure Mechanism (from `server.log`)
During vLLM v1 engine initialization, the engine checked whether the specified GPU KV cache memory budget (`--kv-cache-memory-bytes 4294967296`, exactly 4.0 GiB) was sufficient to service at least one request at the model's configured maximum sequence length (`--max-model-len 1048576` tokens).

The engine threw a fatal `ValueError`:

```text
(Worker_TP3 pid=294384) INFO 09-22 01:20:17 [gpu_worker.py:544] Initial free memory 93.95 GiB, reserved 4.0 GiB memory for KV Cache as specified by kv_cache_memory_bytes config and skipped memory profiling.
(EngineCore pid=294070) ERROR 09-22 01:20:17 [core.py:1374] EngineCore failed to start.
(EngineCore pid=294070) ERROR 09-22 01:20:17 [core.py:1374] Traceback (most recent call last):
  File ".../vllm/v1/engine/core.py", line 1336, in run_engine_core
    engine_core = EngineCoreProc(*args, engine_index=dp_rank, **kwargs)
  File ".../vllm/v1/engine/core.py", line 145, in __init__
    kv_cache_config = self._initialize_kv_caches(vllm_config)
  File ".../vllm/v1/engine/core.py", line 319, in _initialize_kv_caches
    kv_cache_configs = get_kv_cache_configs(vllm_config)
  File ".../vllm/v1/core/kv_cache_utils.py", line 2331, in get_kv_cache_configs
    _check_enough_kv_cache_memory(vllm_config, kv_cache_configs)
  File ".../vllm/v1/core/kv_cache_utils.py", line 879, in _check_enough_kv_cache_memory
    raise ValueError(
ValueError: To serve at least one request with the model's max seq len (1048576), 7.89 GiB KV cache is needed, which is larger than the available KV cache memory (4.0 GiB). Based on the available memory, the estimated maximum model length is 530432. Try increasing `gpu_memory_utilization` (which also controls CPU memory on the CPU backend) or decreasing `max_model_len` when initializing the engine.
```

#### Why It Got Missed
1. **Engine Invariant**: vLLM v1 enforces an unbypassable admission guard: on-device GPU KV memory must never be configured smaller than $1 \times \text{max\_model\_len}$ request. Even with `--kv-offloading-size 32` (32 GiB host DRAM allocated for offloading), the primary GPU cache was hard-capped at 4.0 GiB.
2. For Kimi-K3 on TP4, 1,048,576 tokens requires **7.89 GiB** of KV cache memory.
3. Because 4.0 GiB < 7.89 GiB, the engine refused to start, estimating that 4.0 GiB could support at most 530,432 tokens.
4. Server process terminated immediately (`RuntimeError: server exited rc=1`), leaving all 3 benchmarks (`128k_c1`, `512k_c1`, `1m_c1`) unexecuted (`NOT_RUN`).

---

## 4. The 8 Non-Complete Distributed Profiler Runs

In the V8 distributed characterization matrix, 22 profiling points were specified across the four scale-out topologies (`tp4_pp2_dist`, `tp8_pp2_dist`, `tp4_pp4_dist`, `tp16_pp1_dist`).

### 4.1 Expected vs Actual Profiler Matrix

| Network Condition | Workload Mode | Expected Points | Files Present | Complete Validations | Incomplete / Missing Points |
|---|---|---:|---:|---:|---|
| **GCP_NATIVE** | Prefill 128K (`prefill_128k`) | 4 | 4 | 4 | 0 |
| **GCP_NATIVE** | Decode 8K (`decode_8k`) | 4 | 4 | 4 | 0 |
| **GCP_NATIVE** | Batched Decode 8K c8 (`batched_decode_8k_c8`) | 4 | 4 | 1 | **3 INCOMPLETE** (trace drop) |
| **GCP_NATIVE** | Heavy Prefill 512K (`long_prefill_512k`) | 2 | 2 | 2 | 0 |
| **GCP_CAPPED_100G** | Matched Prefill 128K (`prefill_128k`) | 4 | 3 | 3 | **1 NOT CAPTURED** (TP16 empty) |
| **GCP_CAPPED_20G** | Matched Prefill 128K (`prefill_128k`) | 4 | 0 | 0 | **4 NOT CAPTURED** (omitted from archive) |
| **TOTALS** | | **22** | **17** | **14** | **8 NON-COMPLETE** |

---

### 4.2 Detailed Ledger of the 8 Non-Complete Profiler Runs

| # | Profile ID / Directory | Topology | Workload | Network | Status | Checks Failed | Missing Artifacts | Technical Root Cause |
|---|---|---|---|---|---|---|---|---|
| **1** | `tp16_pp1_dist/batched_decode_8k_c8` | TP16 / PP1 | Batched Decode 8K c8 | `GCP_NATIVE` | **INCOMPLETE** | `node1_nsys_report: false` | `node1` `.nsys-rep` (0 reports on node1, 2 on node0) | Ray worker profiling timeout / export race on remote node under c8 load |
| **2** | `tp4_pp4_dist/batched_decode_8k_c8` | TP4 / PP4 | Batched Decode 8K c8 | `GCP_NATIVE` | **INCOMPLETE** | `node0_nsys_report: false`, `node1_nsys_report: false` | Both `node0` and `node1` `.nsys-rep` files missing (0 reports) | Nsys profiler failed to attach/flush before process group termination |
| **3** | `tp8_pp2_dist/batched_decode_8k_c8` | TP8 / PP2 | Batched Decode 8K c8 | `GCP_NATIVE` | **INCOMPLETE** | `node0_nsys_report: false` | `node0` `.nsys-rep` (0 reports on node0, 1 on node1) | Worker process on node0 exited before Nsys writer finalized report |
| **4** | `tp16_pp1_dist/prefill_128k` | TP16 / PP1 | Prefill 128K | `GCP_CAPPED_100G` | **NOT CAPTURED** | `PROFILE_VALIDATION.json` missing | Directory present but empty; no `.nsys-rep` or CSVs | Profiler execution ran in master log but artifacts failed extraction to release tree |
| **5** | `tp4_pp2_dist/prefill_128k` | TP4 / PP2 | Prefill 128K | `GCP_CAPPED_20G` | **NOT CAPTURED** | Directory missing from package | Complete directory absent from `profiles_multi_node_capped` | 20G profiler sweep was executed but excluded during package assembly |
| **6** | `tp8_pp2_dist/prefill_128k` | TP8 / PP2 | Prefill 128K | `GCP_CAPPED_20G` | **NOT CAPTURED** | Directory missing from package | Complete directory absent from `profiles_multi_node_capped` | 20G profiler sweep was executed but excluded during package assembly |
| **7** | `tp4_pp4_dist/prefill_128k` | TP4 / PP4 | Prefill 128K | `GCP_CAPPED_20G` | **NOT CAPTURED** | Directory missing from package | Complete directory absent from `profiles_multi_node_capped` | 20G profiler sweep was executed but excluded during package assembly |
| **8** | `tp16_pp1_dist/prefill_128k` | TP16 / PP1 | Prefill 128K | `GCP_CAPPED_20G` | **NOT CAPTURED** | Directory missing from package | Complete directory absent from `profiles_multi_node_capped` | 20G profiler sweep was executed but excluded during package assembly |

---

### 4.3 Root Cause Analysis for Incomplete Batched Decode Traces

All 3 incomplete profiles occurred on the identical workload: **`batched_decode_8k_c8`**.
- In single-request workloads (`decode_8k` and `prefill_128k`), request lifecycles are clean and predictable. Nsys hooks cleanly around the single inference pass.
- In multi-request batched decode at concurrency 8 (`c8`), vLLM's dynamic iteration scheduling interleaves multiple token generations across 8 parallel streams.
- The distributed profiler runner (`18_run_vllm_multi_node_profile_case.py`) used Ray actor wrapping to launch `nsys profile` around worker processes.
- Under heavy concurrent decode, worker processes on remote nodes experienced timing skew during benchmark completion. When the benchmark client received the final token and signaled completion, the master script initiated teardown before remote Nsys daemon instances could cleanly flush and finalize `.nsys-rep` binaries to disk.
- Result: The application benchmarks themselves succeeded (`workload_completed: true`, `bench_json: true`), but the profiling validation script marked them `complete: false` due to missing per-rank reports.

---

## 5. Out-of-Scope Hardware-Only Networks: 50G and 10G

A frequent audit question is why the benchmark suite contains no application serving rows for 50 Gbps or 10 Gbps network states, despite containing network validation logs for them.

### 5.1 Explicit Architectural Scope Boundary
The benchmark suite scripts and architectural documentation explicitly scoped application-level serving to three network modes:
1. `GCP_NATIVE` (uncapped baseline VPC, measured at ~173.6 Gbps forward)
2. `GCP_CAPPED_100G` (traffic-shaped via Linux `tc-htb` to 100 Gbps, measured at ~56.8 Gbps forward)
3. `GCP_CAPPED_20G` (traffic-shaped via Linux `tc-htb` to 20 Gbps, measured at ~16.5 Gbps forward)

As recorded verbatim in [README_V8_FULL.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/release_specs/suite_scripts/README_V8_FULL.md) and [SCALEOUT_NETWORK_COVERAGE.md](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/final_validation/SCALEOUT_NETWORK_COVERAGE.md):
> *"vLLM scale-out modes are intentionally limited to Native / 100G / 20G. 50G and 10G remain hardware/NCCL microbenchmark sensitivity points."*
>
> *"V8 intentionally limits expensive model runs to the three network states needed for team communication: GCP_NATIVE, GCP_CAPPED_100G, GCP_CAPPED_20G. The cheaper hardware/network phase retains the full Native/100G/50G/20G/10G transport sweep; compared with the vLLM matrix, 50G and 10G are hardware-only sensitivity points."*

### 5.2 Why 50G/10G Application Runs Were Excluded
- Running all 4 scale-out topologies across 3 context lengths (128K, 512K, 1M) requires 12 long-duration distributed model serving points per network mode.
- Adding full model sweeps for 50G and 10G would have added 24 multi-hour distributed runs without providing structural architectural insight beyond what the 100G and 20G brackets already prove.
- Therefore, **50G and 10G were characterized at the hardware layer only** (bidirectional iperf3 throughput and multi-node NCCL AllReduce/SendRecv bus bandwidth). Their omission from the application matrix was intentional by design, not a failure or omission of the test harness.

---

## 6. Runtime NCCL Policy Audit Misses (`nccl_policy_ok: false`)

Canonical validation marks `nccl_policy_ok: false` in [FINAL_VALIDATION.json](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/results/real_data/final_validation/FINAL_VALIDATION.json):

```json
{
  "nccl_policy_ok": false,
  "ray_nccl_scaleout_audits": 0,
  "ray_nccl_scaleout_expected": 12,
  "ray_nccl_profile_audits": 17,
  "ray_nccl_profile_expected": 22
}
```

### 6.1 Audit Intent & Mechanism
V8 implemented a strict anti-contamination policy:
- Intra-node communication must never disable P2P or SHM (`NCCL_P2P_DISABLE` and `NCCL_SHM_DISABLE` were forbidden).
- Before launching Ray workers and vLLM actors, the suite executed a live environment probe on every node, dumping `*_RAY_NCCL_ENV_AUDIT.json`.
- The strict validator required:
  - 12 scale-out audits (4 topologies $\times$ 3 network modes).
  - 22 profile audits (matching the 22 expected distributed profilers).

### 6.2 Root Cause of the Audit Failure
1. **Scale-Out Audits (0 / 12)**: While the launch shells verified clean environments (`NCCL_ENV_BEFORE_RUN.txt` files all passed with zero forbidden hits), the pre-actor Ray worker environment dumps were written to temporary run directories that were not preserved in the `vllm_scaleout_network_matrix/` release subdirectories.
2. **Profile Audits (17 / 22)**: Exactly 17 profile audits were present (matching the 17 present `PROFILE_VALIDATION.json` directories). Because the 5 capped profilers were missing from the package, their corresponding Ray environment audits were also absent.
3. **Crucial Finding**: This was an **artifact collection omission**, not an environment violation. Every single captured NCCL environment audit verified `violations: []` and confirmed that `NCCL_P2P_DISABLE` and `NCCL_SHM_DISABLE` were never set.

---

## 7. Impact on Final Sign-Off & Data Integrity Rules

Because of the 7 missed application runs and the 8 non-complete profiler runs:
- `serving_matrix_complete = false` (requires $126 / 126$ completed).
- `profiles_all_complete = false` (requires $22 / 22$ complete).
- `strict_full_coverage = false` (requires full matrix completion).
- `full_suite_valid = false` (requires strict full coverage sign-off).

### Data Integrity Rules Enforced
1. **Never Treat Missing Runs as Zero**: In throughput and latency charts, missing points (such as FP8 KV or CPU offload) are represented as null/empty, never as 0 tokens/s or infinite latency.
2. **Never Label Software Assertions as OOM**: The 4 FP8 KV runs and 3 CPU offload runs failed due to software assertions and configuration validation floors, not GPU physical VRAM exhaustion (OOM).
3. **Safety Skips and Guarded Skips are Scientific Evidence**: The validation harness explicitly treats guarded skips as valid boundary evidence defining the operational limits of the software stack.

---

## 8. Summary Checklist for Re-Execution

If the team chooses to re-run the missed V8 points in a future campaign, the following adjustments are required:

1. **FP8 KV-Cache Runs**:
   - Add flag: `--attention-config '{"use_prefill_query_quantization": true}'` whenever `--kv-cache-dtype fp8` is specified for Kimi-K3 models.
2. **CPU KV Offload Pressure Runs**:
   - Increase `--kv-cache-memory-bytes` to at least `8589934592` (8.0 GiB) or reduce `--max-model-len` to `524288` (512K) to satisfy the engine floor ($> 7.89\text{ GiB}$ for 1M context on TP4).
3. **Distributed Batched Decode Profilers**:
   - Add a post-benchmark sleep buffer ($> 15\text{ s}$) before Ray actor teardown in `18_run_vllm_multi_node_profile_case.py` to allow remote Nsys collectors to finalize report files.
4. **Capped Profiler Packaging**:
   - Ensure the packaging script `99_package_v8_full_results.sh` recursively pulls both `GCP_CAPPED_100G` and `GCP_CAPPED_20G` directories into the release bundle.
