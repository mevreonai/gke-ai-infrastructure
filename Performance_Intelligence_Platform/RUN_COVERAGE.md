# Performance Intelligence Platform — Run Coverage Matrix

**Document Version:** 2.0  
**Last Updated:** October 2026  
**Platform Version:** PIP v2.0 (Post-V8 Parity Upgrade)

---

## 1. Run Profile Summary

| Profile | Flag | Approx. Duration | Steps Executed | Description |
| :--- | :--- | :---: | :--- | :--- |
| **Smoke** | `--profile smoke` | ~10 min | Steps 0-1 (TP4 1k/8k c=1 only) | Quick sanity check |
| **Fast Dashboard** | `--profile fast-dashboard` | ~2h | Steps 0-13 (Stage 1+2) | Minimum data for dashboard build |
| **Default** | `--profile default` | ~9h | Steps 0-17 (All Stages) | Full characterization with cold/warm isolation |
| **Deep Profile** | `--profile deep-profile` | ~14h | Steps 0-20 (All + Extensions) | V8-parity deep: Poisson, scheduler, observer, heavy Nsys |

---

## 2. Step-by-Step Execution Map

| Step | Name | Stage | Duration | Description |
| :---: | :--- | :---: | :---: | :--- |
| 00 | Preflight & Environment Snapshot | 0 | ~2 min | SHA256 checksums, Python stack, nvidia-smi, env vars |
| 01 | Chunk Budget A/B Test | 1 | ~8 min | 8192 vs 8448 chunked prefill budget comparison |
| 02 | PyTorch Profiler Batched Analysis | 1 | ~25 min | Cold-cache TP4/TP8 c=8 & c=32 torch traces with vLLM restart between concurrencies |
| 03 | NCCL Socket Tuning | 1 | ~10 min | AllReduce & SendRecv nccl-tests across nodes |
| 04 | TP8 NUMA Pinning | 1 | ~12 min | Unpinned vs NUMA-pinned TP8 single-node comparison |
| 05 | Short Prompts & Streaming Jitter | 1 | ~15 min | Sub-8K scaling (1K/2K) + R4 ITL jitter at c=1,8,16 |
| 06 | Chunk Sensitivity & Knee Repeats | 1 | ~20 min | 128K chunk=16384, 3x knee repeats, R1 continuous curve |
| 07 | KV Pool Audit & Trace Trimming | 1 | ~3 min | Automated KV pool allocation audit across all prior runs |
| 08 | FP8 Quantization Evaluation | 2 | ~20 min | FP8 KV cache dtype with prefill query quantization |
| 09 | CPU Offload & Agentic Decay | 2 | ~25 min | KV offload reuse test + R2 5-turn prefix cache decay |
| 10 | Multi-Node Distributed Load | 2 | ~90 min | TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 full concurrency ladders |
| 11 | PP2 Layer Split Evaluation | 2 | ~30 min | 15/12 vs default pipeline partition comparison |
| 12 | Network Capped & Resilience | 2 | ~45 min | Native vs 100G vs 20G vs 0.05% loss stress test |
| 13 | TP16 512K Prefill Profile | 2 | ~20 min | Nsight Systems profile for 16-GPU long prefill |
| 14 | Deep Kernel Timeline Profiles | 3 | ~45 min | B1 CUDA Graph decode, single/multi-node Nsys & PyTorch traces |
| 15 | Canonical Aggregation & Audit | 3 | ~5 min | Compile dashboard canonical data + invariant verification |
| 16 | Waves, Stalls & Pause Audit | 3 | ~5 min | pip_waves + pip_scan decode silence analysis |
| 17 | Continuous Batching Sweeps | 3 | ~105 min | 7-block CB: step budgets, chunk caps, request caps, mixed traffic, memory |
| 18 | Open-Loop Poisson Sweep | 3 | ~25 min | Poisson arrival at RPS=1,2,4,8,∞ for throughput-latency curve |
| 19 | Scheduler max_num_seqs Sweep | 3 | ~30 min | Admission cap sensitivity: 8,16,64,128 at 8K c=32 |
| 20 | Observer Overhead Test | 3 | ~15 min | Minimal vs full Prometheus telemetry cost quantification |

---

## 3. Topology Coverage Matrix

| Topology | TP | PP | GPUs | Node Config | Stages |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `tp4_pp1` | 4 | 1 | 4 | Single-node sub-cluster | Stage 1, 2, 3 |
| `tp8_pp1` | 8 | 1 | 8 | Single-node full socket | Stage 1, 3 |
| `tp4_pp2` | 4 | 2 | 8 | 2-node (4 GPUs/node) | Stage 2, 3 |
| `tp8_pp2` | 8 | 2 | 16 | 2-node (8 GPUs/node) | Stage 2, 3 |
| `tp4_pp4` | 4 | 4 | 16 | 2-node (8 GPUs/node) | Stage 2, 3 |
| `tp16_pp1` | 16 | 1 | 16 | 2-node (8 GPUs/node) | Stage 2, 3 |

---

## 4. Context Length Coverage

| Context Size | Token Count | Output Tokens | Concurrencies Tested | Warmups | Notes |
| :---: | ---: | :---: | :--- | :---: | :--- |
| **1K** | 1,024 | 128 | c=1, 8, 32 | 2 | Sub-8K scaling baseline |
| **2K** | 2,048 | 128 | c=1, 8, 32 | 2 | Sub-8K scaling mid-point |
| **8K** | 8,192 | 256 | c=1, 4, 8, 16, 32 | 2 | Primary characterization context |
| **16K** | 16,384 | 64 | c=1 | 1 | R1 continuous curve inflection point |
| **32K** | 32,768 | 64 | c=1 | 1 | R1 continuous curve |
| **64K** | 65,536 | 64 | c=1 | 1 | R1 continuous curve |
| **128K** | 131,072 | 64-128 | c=1, 2, 4, 8 | 1 | Long-context primary evaluation |
| **256K** | 262,144 | 64 | c=1 | 0 | R1 continuous curve upper bound |
| **512K** | 524,288 | 32-64 | c=1, 2, 4 | 0 | Extended long-context |
| **1M** | 1,000,000-1,048,576 | 32 | c=1, 2, 4 | 0 | Maximum context (VRAM-bounded) |

---

## 5. Concurrency Grid Coverage

| Concurrency | Use Case | Context Lengths Applied |
| :---: | :--- | :--- |
| **c=1** | Latency floor (TTFT, TPOT) | All (1K → 1M) |
| **c=2** | Low-load scaling | 128K, 512K, 1M |
| **c=4** | Moderate batching | 8K, 128K, 512K, 1M |
| **c=8** | Production batching | 1K, 8K, 128K |
| **c=16** | Heavy batching / knee-point | 8K (knee repeats), 1K (streaming jitter) |
| **c=32** | Saturation / throughput ceiling | 1K, 2K, 8K |
| **c=64** | Open-loop Poisson arrival cap | 8K (Poisson sweep only) |

---

## 6. Profiling Tools Coverage

### 6.1 Nsight Systems (nsys)

| Profile Point | Topology | Context | Concurrency | Mode | Step |
| :--- | :--- | :---: | :---: | :--- | :---: |
| B1 CUDA Graph decode | TP4 | 8K | c=1 | `decode` (Graphs ON) | 14 |
| Single-node standard | TP4, TP8 | 8K | c=1 | `prefill+decode` | 14 |
| Multi-node decode | TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 | 8K | c=1 | `decode` | 14 |
| Network-capped prefill | All 16-GPU | 128K | c=1 | `prefill_128k` | 12 |
| TP16 512K prefill | TP16/PP1 | 512K | c=1 | `long_prefill_512k` | 13 |

### 6.2 PyTorch Profiler (Chrome Trace)

| Profile Point | Topology | Context | Concurrency | Step |
| :--- | :--- | :---: | :---: | :---: |
| Single-node cold c=8 | TP4, TP8 | 8K | c=8 | 2 |
| Single-node cold c=32 | TP4, TP8 | 8K | c=32 | 2 |
| Multi-node cold c=8 | TP4/PP4, TP8/PP2, TP16/PP1 | 8K | c=8 | 2 |
| Standard batched | TP4 | 8K | c=8 | 14 |

### 6.3 Multi-Node Nsight Profile Matrix

| Topology | Modes Captured | Contexts | Step |
| :--- | :--- | :--- | :---: |
| TP4/PP2 | short_prefill_1k, decode_8k, batched_8k_c8, prefill_128k, 512k*, 1m* | 1K/8K/128K/512K/1M | 14 |
| TP8/PP2 | short_prefill_1k, decode_8k, batched_8k_c8, prefill_128k, 512k*, 1m* | 1K/8K/128K/512K/1M | 14 |
| TP4/PP4 | short_prefill_1k, decode_8k, batched_8k_c8, prefill_128k, 512k*, 1m* | 1K/8K/128K/512K/1M | 14 |
| TP16/PP1 | short_prefill_1k, decode_8k, batched_8k_c8, prefill_128k, 512k*, 1m* | 1K/8K/128K/512K/1M | 14 |

> `*` = Optional heavy profiles, enabled with `--profile deep-profile` or `RUN_HEAVY_PROFILE=1`

---

## 7. Cold vs Warm Cache Isolation

### Architecture

PIP enforces cold-cache measurement integrity through the **4-Pillar Architecture**:

1. **VRAM Drain Barrier:** `pkill -9 -f vllm` followed by 3-second GPU memory drain between concurrency levels in Step 2 profiling and Steps 18-20 sweep cases. This ensures no KV cache state leaks between concurrency measurements.

2. **Server Restart Per Case:** In `11_run_vllm_surrogate.py`, a fresh vLLM serve instance is launched per case definition. Each case gets a clean model initialization with no residual KV cache from prior runs.

3. **Wave-Trimmed Analysis:** The `pip_waves.py` tool decomposes each benchmark's request arrivals into waves (Wave 1 burst, Steady-state waves, Final wave drain). All dashboard metrics are trimmed to steady-state waves only, removing arrival burst contamination.

4. **Explicit Warmup Tracking:** Each benchmark records `warmups` count and the `warmup_manifest.json`. Metrics output distinguishes:
   - `warmups=0` → **cold** measurement (first-ever request hits empty KV cache)
   - `warmups≥1` → **warm** measurement (KV cache populated by warmup requests)

### Cold/Warm Coverage by Context

| Context | Cold (warmups=0) | Warm (warmups≥1) | Where Measured |
| :---: | :---: | :---: | :--- |
| 1K | ✓ (R2 turn1_cold_1k) | ✓ (1k_c1, 1k_c8, 1k_c32) | Step 5, 9 |
| 8K | ✓ (Step 2 profiling c=8, c=32) | ✓ (8k_c4, 8k_c32) | Step 1, 2, 5 |
| 128K | ✓ (128k_c1 offload) | ✓ (128k_c1, 128k_c4) | Step 6, 8, 9 |
| 512K | ✓ (512k_c1 offload, no warmup) | — | Step 9, 10 |
| 1M | ✓ (1m_c1 all cases, no warmup) | — | Step 9, 10 |

---

## 8. Open-Loop Traffic Patterns (Step 18)

| Arrival Rate | Type | Prompts | Concurrency | Context |
| :---: | :--- | :---: | :---: | :---: |
| 1.0 RPS | Poisson | 40 | 64 | 8K |
| 2.0 RPS | Poisson | 60 | 64 | 8K |
| 4.0 RPS | Poisson | 80 | 64 | 8K |
| 8.0 RPS | Poisson | 120 | 64 | 8K |
| ∞ (closed-loop) | Saturated | 128 | 64 | 8K |

---

## 9. Scheduler Sensitivity Sweep (Step 19)

| max_num_seqs | Context | Concurrency | Prompts | Purpose |
| :---: | :---: | :---: | :---: | :--- |
| 8 | 8K | c=32 | 128 | Minimum admission (deep queuing) |
| 16 | 8K | c=32 | 128 | Moderate admission |
| 64 | 8K | c=32 | 128 | Baseline comparison |
| 128 | 8K | c=32 | 128 | Over-admission stress test |

---

## 10. Observability Overhead Test (Step 20)

| Mode | kv-cache-metrics | MFU metrics | cudagraph-metrics | iteration-details | Prometheus interval |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Full** (default) | ✓ | ✓ | ✓ | ✓ | 0.5s |
| **Minimal** | ✗ | ✗ | ✗ | ✗ | 1.0s |

---

## 11. Continuous Batching Coverage (Step 17)

| Block | Name | Description | Context | Concurrency |
| :---: | :--- | :--- | :---: | :--- |
| 1 | Long Prompts Side-by-Side | 128K & 512K sequential serving | 128K, 512K | c=1 |
| 2 | Step Budget Sweep | max_num_batched_tokens: 2048, 4096, 8192, 16384, 32768 | 8K | c=8 |
| 3 | Request Cap Binding | max_num_seqs vs max_num_active_seqs comparison | 8K | c=32 |
| 4 | Mixed Traffic | Short + long context interference pattern | 1K + 128K | c=4 |
| 5 | Memory Pressure | KV cache limits under constrained memory | 8K | c=32 |
| 6 | Long Answers | Extended output generation (1024+ tokens) | 2K | c=1 |
| 7 | Steady Arrivals | Controlled request_rate arrival patterns | 8K | c=8 |

---

## 12. Network Impairment Coverage (Step 12)

| Mode | Bandwidth | Packet Loss | Jitter | Topologies Tested |
| :--- | :---: | :---: | :---: | :--- |
| **Native** | Full (~100 Gbps) | 0% | 0 | TP16/PP1, TP4/PP4 |
| **100G Cap** | 100 Gbps | 0% | 0 | TP16/PP1, TP4/PP4 |
| **20G Cap** | 20 Gbps | 0% | 0 | TP16/PP1, TP4/PP4 |
| **Impaired** | Full | 0.05% | 0.2±0.05 ms | TP16/PP1, TP4/PP4 |

---

## 13. Analysis Tools Coverage

| Tool | Script | Purpose | Input | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Wave Decomposition** | `pip_waves.py` | Decomposes request arrival bursts into waves | Detailed JSON results | Wave statistics, trimmed means |
| **Stall Scanner** | `pip_scan.py` | Detects decode pauses ≥3 steps, stalls >100ms | Run directory tree | CSV of all detected pauses |
| **Timeline Visualizer** | `pip_timeline.py` | Publication-grade Gantt charts | Detailed JSON results | PNG/SVG timeline charts |
| **Step-Cost Fitter** | `pip_step_cost.py` | Linear regression T=a+b·gen+c·ctx | Server microsecond logs | Regression coefficients |
| **Mixed Traffic** | `pip_mixed_traffic.py` | Short/long context TTFT interference | Multi-context run results | Penalty ratio report |
| **Metrics Diff** | `metrics_diff.py` | Prometheus vs client timeline discrepancy | Prometheus scrape + client JSON | Discrepancy audit |
| **Server Log Parser** | `server_log.py` | Extract server logs ±2s around pause events | Server logs + pause CSV | Correlated log windows |
| **Result Summary** | `15_summarize_vllm.py` | Aggregate all runs into CSV/JSON summary | Run directory tree | Summary CSV + JSON |
| **KV Pool Audit** | `24_audit_kv_and_trim_traces.py` | KV pool allocation and trace health | Run directory tree | JSON audit report |
| **Canonical Compiler** | `compile_canonical_data.py` | Dashboard data compilation | All run artifacts | `DASHBOARD_CANONICAL_DATA.json` |
| **Bench Summary** | `bench_summary.py` | Quick per-run wave/stall counts | Run directory tree | Text summary |

---

## 14. Total Benchmark Count by Profile

| Profile | Benchmark Runs | Server Boots | Profiling Passes | Estimated Time |
| :--- | :---: | :---: | :---: | :---: |
| `smoke` | ~6 | 1 | 0 | ~10 min |
| `fast-dashboard` | ~80 | ~12 | 2 (torch batched) | ~2h |
| `default` | ~150 | ~25 | 8 (Nsys + torch) | ~9h |
| `deep-profile` | ~185+ | ~35 | 12+ (all Nsys + torch + heavy) | ~14h |
