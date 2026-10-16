# Performance Intelligence Platform (PIP) — Empirical Coverage Matrix

**Document ID:** `PIP-COVERAGE-20261016`  
**Total Configured Points:** 261  
**Target Workload:** `moonshotai/Kimi-Linear-48B-A3B-Instruct`  
**Target Cluster:** Dual 8× NVIDIA RTX PRO 6000 Ada / Blackwell Server Nodes (16× GPUs, 960 GB VRAM), 100 Gbps Andromeda VPC  
**Canonical Data Source:** [`data/PIP_COVERAGE_MATRIX.json`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/data/PIP_COVERAGE_MATRIX.json)  
**Tabular CSV File:** [`data/PIP_COVERAGE_MATRIX.csv`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/data/PIP_COVERAGE_MATRIX.csv)  

---

## 1. Executive Coverage Overview

| Evaluation Domain | Configured Points | Primary Topologies | Contexts Evaluated | Key Invariants Verified |
| :--- | :---: | :--- | :--- | :--- |
| **Master Serving & Characterization** | **160** | TP4/PP1, TP8/PP1, TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 | 1K, 2K, 8K, 16K, 32K, 64K, 128K, 256K, 512K, 1M | Bounded 1M concurrency ($c \le 4$); server session amortization |
| **Continuous Batching (CB 7-Block Suite)** | **77** | TP4/PP1, TP8/PP1, TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 | 1K, 8K, 128K, 1M | Step budgets (2K–32K), chunk caps, mixed conversational interference |
| **Deep Distributed Profiling (Nsys + PyTorch)**| **24** | TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 | 1K, 8K (c1, c8), 128K, 512K, 1M | Symmetric 6-point distributed matrix; CUDA Graphs decode |
| **Total Configured PIP Execution Horizon** | **261** | **All 6 Cluster Layouts** | **Full 1K → 1M Token Horizon** | **0 points refused (100% within 1,048,576 limit)** |

---

## 2. Cluster Topology Layout Matrix

| Topology Layout | Tensor Parallel (TP) | Pipeline Parallel (PP) | Total GPUs | Node Allocation | Configured Points | Evaluated Concurrencies | Context Length Span |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `TP16/PP1` | TP=16 | PP=1 | 16 GPUs | Dual Nodes (Node 0 + Node 1) | **29** | [1, 2, 4, 8, 32, 64, 128] | 0K → 1M |
| `TP4/PP1` | TP=4 | PP=1 | 4 GPUs | Single Node (Node 0) | **96** | [1, 2, 4, 8, 16, 32, 64] | 0K → 1M |
| `TP4/PP2` | TP=4 | PP=2 | 8 GPUs | Dual Nodes (Node 0 + Node 1) | **39** | [1, 2, 4, 8, 32, 64, 128] | 0K → 1M |
| `TP4/PP4` | TP=4 | PP=4 | 16 GPUs | Dual Nodes (Node 0 + Node 1) | **32** | [1, 2, 4, 8, 32, 64, 128] | 0K → 1M |
| `TP8/PP1` | TP=8 | PP=1 | 8 GPUs | Single Node (Node 0) | **22** | [1, 2, 4, 8, 32] | 1K → 1M |
| `TP8/PP2` | TP=8 | PP=2 | 16 GPUs | Dual Nodes (Node 0 + Node 1) | **43** | [1, 2, 4, 8, 32, 64, 128] | 0K → 1M |

---

## 3. Context Length & Prompt Horizon Coverage

| Context Size | Input Tokens | Generation Output | Concurrencies Tested | Max Model Ceiling | Refusal Status | Benchmark Purpose |
| :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| **0** | 0 | 256 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Short conversational baseline |
| **1K** | 1,024 | 8–512 tokens | [1, 8, 16, 32, 64] | 1,048,576 | **0 Refused (PASS)** | Short conversational baseline |
| **2K** | 2,048 | 128 tokens | [1, 8, 32] | 1,048,576 | **0 Refused (PASS)** | Short conversational baseline |
| **3K** | 3,072 | 128 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Primary characterization knee |
| **4K** | 4,096 | 128 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Primary characterization knee |
| **5K** | 5,120 | 128 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Primary characterization knee |
| **8K** | 8,192 | 256–2048 tokens | [1, 4, 8, 16, 32, 64, 128] | 1,048,576 | **0 Refused (PASS)** | Primary characterization knee |
| **16K** | 16,384 | 64 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Continuous scaling curve |
| **32K** | 32,768 | 64 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Continuous scaling curve |
| **64K** | 65,536 | 64 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Continuous scaling curve |
| **128K** | 131,072 | 8–256 tokens | [1, 2, 4, 8, 64] | 1,048,576 | **0 Refused (PASS)** | Long-context primary evaluation |
| **256K** | 262,144 | 64 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Ultra-long context evaluation |
| **512K** | 524,288 | 8–64 tokens | [1, 2, 4] | 1,048,576 | **0 Refused (PASS)** | Ultra-long context evaluation |
| **586K** | 600,256 | 32 tokens | [1] | 1,048,576 | **0 Refused (PASS)** | Ultra-long context evaluation |
| **1M** | 1,000,000 | 8–256 tokens | [1, 2, 4] | 1,048,576 | **0 Refused (PASS)** | Maximum VRAM-bounded context limit |

---

## 4. Continuous Batching (CB) 7-Block Coverage

| Block # | Capability Domain | Server Configurations Tested | Layouts Evaluated | Key Metrics Captured |
| :---: | :--- | :--- | :--- | :--- |
| **Block 1** | **Step Budget Sweeps** | `--max-num-batched-tokens` 2K, 4K, 8K, 16K, 32K | TP4/PP1, TP4/PP4, TP8/PP2 | Prefill SM saturation vs decode latency starvation |
| **Block 2** | **Chunk Prefill Dynamics** | `--max-num-seqs` 64, 128, 256; chunk caps 4K, 8K | TP4/PP1, TP4/PP2, TP8/PP1, TP8/PP2 | Chunk preemption cost on active decode streams |
| **Block 3** | **Request Cap Binding** | Request queue surges from $c=1$ up to $c=64$ | TP4/PP1, TP4/PP4, TP8/PP2 | Queue admission delay & pipeline backpressure |
| **Block 4** | **Mixed-Traffic Concurrency** | Short 1K requests colliding with 128K background streams | TP16/PP1, TP4/PP1, TP4/PP2, TP4/PP4, TP8/PP2 | Inter-stream TTFT degradation and decode jitter |
| **Block 5** | **Memory Pressure & KV Limits**| Stress testing under $\ge 90\%$ VRAM allocation | TP4/PP1 | KV block eviction, preemption deltas, and swap thrashing |
| **Block 6** | **Long Answer Decode Scaling** | Output scaling up to 1,024 tokens under load | TP4/PP1 | Sustained decode TPOT and ITL percentile stability |
| **Block 7** | **Steady Poisson Arrivals** | Open-loop arrival rates $\lambda = 1, 2, 4, 8, \infty$ req/s | TP16/PP1, TP4/PP2, TP4/PP4, TP8/PP2 | Throughput-latency Pareto frontier and saturation knee |

---

## 5. Distributed Deep Profiling Matrix (Nsight Systems & PyTorch)

| Profile Point | Profile Mode | Topology | Context Length | Concurrency | Profile Captures |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `tp4_pp2_dist_short_prefill_1k` | `short_prefill_1k` | `tp4_pp2_dist` | 1K (1,024 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp2_dist_decode_8k` | `decode_8k` | `tp4_pp2_dist` | 8K (8,192 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp2_dist_batched_decode_8k_c8` | `batched_decode_8k_c8` | `tp4_pp2_dist` | 8K (8,192 tokens) | $c=8$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp2_dist_prefill_128k` | `prefill_128k` | `tp4_pp2_dist` | 128K (131,072 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp2_dist_long_prefill_512k` | `long_prefill_512k` | `tp4_pp2_dist` | 512K (524,288 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp2_dist_extreme_prefill_1m` | `extreme_prefill_1m` | `tp4_pp2_dist` | 1M (1,000,000 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp8_pp2_dist_short_prefill_1k` | `short_prefill_1k` | `tp8_pp2_dist` | 1K (1,024 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp8_pp2_dist_decode_8k` | `decode_8k` | `tp8_pp2_dist` | 8K (8,192 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp8_pp2_dist_batched_decode_8k_c8` | `batched_decode_8k_c8` | `tp8_pp2_dist` | 8K (8,192 tokens) | $c=8$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp8_pp2_dist_prefill_128k` | `prefill_128k` | `tp8_pp2_dist` | 128K (131,072 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp8_pp2_dist_long_prefill_512k` | `long_prefill_512k` | `tp8_pp2_dist` | 512K (524,288 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp8_pp2_dist_extreme_prefill_1m` | `extreme_prefill_1m` | `tp8_pp2_dist` | 1M (1,000,000 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp4_dist_short_prefill_1k` | `short_prefill_1k` | `tp4_pp4_dist` | 1K (1,024 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp4_dist_decode_8k` | `decode_8k` | `tp4_pp4_dist` | 8K (8,192 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp4_dist_batched_decode_8k_c8` | `batched_decode_8k_c8` | `tp4_pp4_dist` | 8K (8,192 tokens) | $c=8$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp4_dist_prefill_128k` | `prefill_128k` | `tp4_pp4_dist` | 128K (131,072 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp4_dist_long_prefill_512k` | `long_prefill_512k` | `tp4_pp4_dist` | 512K (524,288 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp4_pp4_dist_extreme_prefill_1m` | `extreme_prefill_1m` | `tp4_pp4_dist` | 1M (1,000,000 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp16_pp1_dist_short_prefill_1k` | `short_prefill_1k` | `tp16_pp1_dist` | 1K (1,024 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp16_pp1_dist_decode_8k` | `decode_8k` | `tp16_pp1_dist` | 8K (8,192 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp16_pp1_dist_batched_decode_8k_c8` | `batched_decode_8k_c8` | `tp16_pp1_dist` | 8K (8,192 tokens) | $c=8$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp16_pp1_dist_prefill_128k` | `prefill_128k` | `tp16_pp1_dist` | 128K (131,072 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp16_pp1_dist_long_prefill_512k` | `long_prefill_512k` | `tp16_pp1_dist` | 512K (524,288 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |
| `tp16_pp1_dist_extreme_prefill_1m` | `extreme_prefill_1m` | `tp16_pp1_dist` | 1M (1,000,000 tokens) | $c=1$ | NVIDIA Nsys (`.nsys-rep`) + PyTorch Chrome (`.pt.trace.json.gz`) |

---

## 6. Context Refusal & Verification Audit

- **Configured Points Audited:** 261  
- **Points Refused by vLLM:** **0** (Zero refusal violation)  
- **Context Limit Verification:** All evaluated prompts and outputs satisfy `input + output <= 1,048,576`.  
- **Cold Cache Isolation:** Process restart barriers (`pkill -9 -f vllm` and memory flush) enforced between concurrency sweeps to guarantee zero prefix-cache skew.  
- **Zero Exit Policy:** Validated via [`scripts/pip_collect_and_validate.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/pip_collect_and_validate.py).  

---

## 7. Granular Point-by-Point Index (First 30 Samples)

| Record ID | Suite | Stage | Case Name | Layout | Context | Concurrency | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `PIP-0001` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_8k_chunk_control_8192` | `TP4/PP1` | 8K | $c=4$ | `VALID` |
| `PIP-0002` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_8k_chunk_control_8192` | `TP4/PP1` | 8K | $c=32$ | `VALID` |
| `PIP-0003` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_8k_chunk_fix_8448` | `TP4/PP1` | 8K | $c=4$ | `VALID` |
| `PIP-0004` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_8k_chunk_fix_8448` | `TP4/PP1` | 8K | $c=32$ | `VALID` |
| `PIP-0005` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_short_prompts` | `TP4/PP1` | 1K | $c=1$ | `VALID` |
| `PIP-0006` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_short_prompts` | `TP4/PP1` | 1K | $c=8$ | `VALID` |
| `PIP-0007` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_short_prompts` | `TP4/PP1` | 1K | $c=32$ | `VALID` |
| `PIP-0008` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_short_prompts` | `TP4/PP1` | 2K | $c=1$ | `VALID` |
| `PIP-0009` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_short_prompts` | `TP4/PP1` | 2K | $c=8$ | `VALID` |
| `PIP-0010` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_short_prompts` | `TP4/PP1` | 2K | $c=32$ | `VALID` |
| `PIP-0011` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_128k_chunk_sensitivity` | `TP4/PP1` | 128K | $c=1$ | `VALID` |
| `PIP-0012` | `MASTER_BENCHMARK` | Stage 1: Single Node | `tp4_128k_chunk_sensitivity` | `TP4/PP1` | 128K | $c=4$ | `VALID` |
| `PIP-0013` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_knee_repeats` | `TP4/PP1` | 8K | $c=16$ | `VALID` |
| `PIP-0014` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_knee_repeats` | `TP4/PP1` | 8K | $c=16$ | `VALID` |
| `PIP-0015` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_knee_repeats` | `TP4/PP1` | 8K | $c=16$ | `VALID` |
| `PIP-0016` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_knee_repeats` | `TP4/PP1` | 128K | $c=4$ | `VALID` |
| `PIP-0017` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_knee_repeats` | `TP4/PP1` | 128K | $c=4$ | `VALID` |
| `PIP-0018` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_knee_repeats` | `TP4/PP1` | 128K | $c=4$ | `VALID` |
| `PIP-0019` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 1K | $c=1$ | `VALID` |
| `PIP-0020` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 1K | $c=8$ | `VALID` |
| `PIP-0021` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 1K | $c=32$ | `VALID` |
| `PIP-0022` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 8K | $c=1$ | `VALID` |
| `PIP-0023` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 8K | $c=8$ | `VALID` |
| `PIP-0024` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 8K | $c=32$ | `VALID` |
| `PIP-0025` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 128K | $c=1$ | `VALID` |
| `PIP-0026` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 128K | $c=2$ | `VALID` |
| `PIP-0027` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 128K | $c=4$ | `VALID` |
| `PIP-0028` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 128K | $c=8$ | `VALID` |
| `PIP-0029` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 512K | $c=1$ | `VALID` |
| `PIP-0030` | `MASTER_BENCHMARK` | Stage 2: Multi-Node Scale-Out | `tp4_pp2_dist_load` | `TP4/PP2` | 512K | $c=2$ | `VALID` |

*(Full 100+ point records available in canonical JSON and CSV files)*
