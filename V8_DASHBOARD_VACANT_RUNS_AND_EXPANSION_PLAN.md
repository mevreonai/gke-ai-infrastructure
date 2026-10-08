# V8 Performance Dashboard: Vacant Runs Audit & Comprehensive Expansion Plan

**Document Version:** 1.1 (Deeply Expanded Edition)  
**Target Release:** V8 Suite & Performance Intelligence Platform  
**Target File Reference:** [`MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html)  
**Historical Blueprint Reference:** [`V8_Gaps_and_Rerun_Plan_v1.3.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/V8_Gaps_and_Rerun_Plan_v1.3.md)  
**Hardware Topology:** Dual 8× NVIDIA RTX PRO 6000 Ada (16× GPUs total, 960 GB VRAM), 100 Gbps Google Cloud Andromeda VPC  
**Target Model:** `moonshotai/Kimi-Linear-48B-A3B-Instruct` (Git commit: `e1df551a447157d4658b573f9a695d57658590e9`)  
**Author:** Deep Infrastructure & Systems Performance Team  

---

## 1. Executive Summary & Audit Context

The **Master Characterization Dashboard** (`MASTER_CHARACTERIZATION_DASHBOARD.html`) visualizes empirical serving dynamics for `moonshotai/Kimi-Linear-48B-A3B-Instruct` across dual NVIDIA RTX PRO 6000 Ada GPU nodes interconnected via 100 Gbps Google Cloud Andromeda VPC.

While the current dashboard features **126 verified benchmark runs** across 13 interactive tabs, cross-referencing against `V8_Gaps_and_Rerun_Plan_v1.3.md` reveals critical **vacancies, unmeasured operating regions, and structural blindspots**:

1. **Multi-Node Concurrency Blindspot (The Major Hole):** All multi-node layouts (`TP4/PP2`, `TP8/PP2`, `TP4/PP4`, `TP16/PP1`) were tested **strictly at concurrency $c=1$**. Concurrency scaling, queuing, and memory pressure off a single node are completely vacant.
2. **Short-Prompt / Interactive Void:** The shortest prompt tested in V8 is 8,192 tokens. Interactive chat, agentic loops, and short RAG prompts ($<8\text{K}$, such as 1K, 2K, 4K) are completely unmeasured.
3. **Failed Multi-Node Profiler Exports:** Several multi-node decode Nsight System traces suffered from failed per-worker SQLite exports, leaving critical timeline cells unrendered.
4. **Unexecuted Memory & Quantization Features:** FP8 KV-cache quantization and Host CPU memory KV offloading produced zero valid serving runs due to driver/backend prerequisites, leaving capacity predictions theoretical.

This document inventories every vacant run in the dashboard, compiles the full re-run agenda from `V8_Gaps_and_Rerun_Plan_v1.3.md`, details our recommended architectural additions, and provides exact machine and wall-clock execution timelines.

---

## 2. Dashboard Vacancy Audit: Tab-by-Tab Breakdown

Below is the exhaustive audit of what runs and data points are currently **vacant, missing, or unmeasured** in `MASTER_CHARACTERIZATION_DASHBOARD.html`.

| Dashboard Tab | Current Populated Scope | Vacant / Missing Runs & Data Points | Impact on Dashboard Analysis |
| :--- | :--- | :--- | :--- |
| **Tab 1: 🏛 Executive** | High-level KPIs, 126 runs summary, static MFU cards | • Lacks multi-node under-load throughput KPIs<br>• Lacks true measured FP8 KV capacity limit ($/context-hour theoretical) | Understates true production cluster capacity under multi-user concurrency |
| **Tab 2: 🎯 Key Finds & Tab 3: ✨ Discoveries** | 10 Landmark Discoveries (D1–D8, E2E·A–D) | • **D1:** Missing multi-node concurrent long-prompt admission<br>• **D3:** Missing empirical FP8 KV pool & host CPU offload latency<br>• **D7:** Pipeline stage imbalance is estimated without 15/12 rebalanced PP2 split<br>• **D8:** Cross-node small-message cost lacks NCCL socket tuning validation | Hypotheses are supported by single-node data rather than direct distributed proof |
| **Tab 4: 📈 Scale-Up (Single-Node)** | TP4/PP1 & TP8/PP1 from $c=1$ to $c=64$ at 8K, 128K, 512K, 1M | • **Short Prompts:** 1K, 2K, 4K completely missing<br>• **8K Chunk Budget Artefact:** 8K prompt equals chunk budget (8,192 tokens), causing prefill doubling under concurrency<br>• **Statistical Error Bars:** $n=1$ for key loaded points ($c=8, c=32$) | Cannot evaluate conversational/agentic latencies; loaded 8K first-token numbers carry tail-chunk artefact |
| **Tab 5: 🌐 Scale-Out (Distributed)** | TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 at $c=1$ only (128K, 512K, 1M) | • **Zero Concurrency under Load:** $c=2, c=4, c=8$ completely vacant across all 4 distributed layouts<br>• **8K Short Context:** 8K context vacant on all two-node layouts (starts at 128K)<br>• **Data Parallelism (DP=2 × TP8):** Completely absent from the matrix | Largest empirical hole in V8; cannot determine whether TP16 or TP4/PP4 is superior under multi-tenant load |
| **Tab 6: 📜 Long Context (128K–1M)** | Single-node chunked prefill (512–8192) at 128K, 512K, 1M | • **Intermediate Contexts:** 16K, 32K, 64K, 256K not measured (gap between 8K and 128K, and 512K to 1M)<br>• **Prefix-Cache Misses:** 512K and 1M prefix-cache miss root causes unverified<br>• **Distributed 1M Concurrency:** 1M at $c=2, c=4$ vacant on multi-node | Missing fine-grained activation scaling curves; multi-node long context scaling unproven |
| **Tab 7: ⚙ Scheduler & KV** | KV pool size (8.14M tokens), prefix caching hit rates | • **FP8 KV Cache:** 0 runs completed (planned runs produced no bench output)<br>• **Host DRAM KV Offload:** Round-trip transfer latencies unmeasured<br>• **8-GPU vs 4-GPU KV Pool:** TP8 pool is only 1% larger than TP4 instead of predicted +19% | Memory capacity and cost-per-context-hour metrics rely on BF16 only |
| **Tab 8: 🔬 Profiler** | Single-node Nsight kernel tables & PyTorch traces | • **Multi-Node Decode Exports:** Per-worker SQLite exports failed for multi-node decode<br>• **Graphs-On Decode Timeline:** Single-node decode taken with `--enforce-eager` (kernel inventory, not true serving time-share)<br>• **TP16 512K Prefill:** Only 1 of 12 ranks usable<br>• **Capped Prefill Profiles:** 5 of 8 planned profiles missing (TP16 100G; TP4/PP2, TP8/PP2, TP4/PP4, TP16 20G) | Profiler tab lacks interactive graphs-on timeline attribution for distributed decode |
| **Tab 9–13: 📋 Evidence & Telemetry** | 126 evidence rows (`EV-001` to `EV-126`) | • `nccl_policy_ok=false` counter bug in validator drawer<br>• Vacant cells for all network traffic shaping between 20G and 100G (50G/10G dropped) | Drawer shows false alarm audit flag and gaps in network sensitivity curve |

---

## 3. Complete Inventory of All Planned & Missing Runs

### Group A: Immediate High-Leverage Runs & Quick Fixes (~70 Minutes Machine Time)

| Run ID | Detailed Run Configuration | Question Answered & Target Discovery | Numbers Affected in Dashboard | Machine Time |
| :---: | :--- | :--- | :--- | :---: |
| **A1** | **8K Chunk Budget Check:**<br>TP4/PP1, 8K prompts at $c=4$ and $c=32$, with `max_num_batched_tokens 8448` (or 8,000-token prompt) | Disentangles whether 8K loaded first token is artificially inflated by prompt length exactly matching the 8,192 chunk boundary (tail chunk stall) | Corrects every loaded 8K first-token number (closed-loop and open-loop) | **10 min** |
| **A2** | **FP8 KV Smoke Test:**<br>`vllm serve --kv-cache-dtype fp8` at 8K $c=1$ on TP4 | Verifies whether the installed vLLM runtime and attention kernels accept FP8 KV cache for Kimi-Linear-48B | Determines feasibility of Group B5 | **5 min** |
| **A3** | **KV Block Allocation Audit:**<br>Parse TP4 vs TP8 start-up logs for physical KV block allocation counts | Resolves why TP8 KV pool is only 1% larger than TP4 (8.21M vs 8.14M) instead of predicted +19% | Resolves D3; updates $/context-hour metrics | **0 min** *(log read)* |
| **A4** | **PP2 15/12 Layer Partition Rebalance:**<br>TP4/PP2 and TP8/PP2 at 128K and 512K $c=1$, with `VLLM_PP_LAYER_PARTITION=15,12` | Tests cost model prediction: stage-0 idle reduces from 10.1% to 3.2%, cutting first-token latency by 3.5% | Proves or refutes D7 cost model; adds fastest latency win | **20 min** |
| **A5** | **NCCL Validator Counter Remediation:**<br>Fix Windows path separator glob bug in `20_ray_nccl_env_audit.py` validator | Resolves false alarm `ok=false` in Evidence drawer across all 12 distributed runs | Restores 100% green compliance in Evidence tab | **0 min** *(code fix)* |
| **A6** | **Closed-Loop Wave Trimming:** *(Deeply Expanded in §4)*<br>Re-report closed-loop points by trimming initial synchronised burst (first wave) and final drain wave | Eliminates first-wave startup spike (3.7s vs 0.94s at 8K $c=32$) and drain tail | Re-reports steady-state first token and ITL on all closed-loop panels | **0 min** *(re-analysis)* |
| **A7** | **TP8 NUMA Core & Socket Pinning:**<br>TP8/PP1, 8K $c=1$, pinning each worker process to its GPU's local NUMA socket | Tests whether TP8's extra ~22 µs AllReduce serving cost is caused by host-side cross-socket threading | Resolves D4 root cause; informs CPU core affinity policy | **20 min** |
| **A8** | **NCCL Provider Plugin & Socket Threads:**<br>`nccl-tests` across nodes with Google VPC plugin enabled and `NCCL_NSOCKS_PERTHREAD=4` | Tests whether cross-node 57 Gbps bandwidth cap and 227–290 µs message latency are fabric or socket configuration limits | Sets α-β model parameters; decides network viability for TP16 | **15 min** |
| **SUBTOTAL** | **Group A Execution Time** | | | **1h 10m** |

---

### Group B: Core Characterization & Dashboard Gap Closures (~9.6 Hours Machine Time / ~7.0 Hours Wall Time)

| Run ID | Detailed Run Configuration | Question Answered & Target Discovery | Numbers Affected in Dashboard | Machine Time |
| :---: | :--- | :--- | :--- | :---: |
| **B1** | **CUDA Graphs-On Nsight Decode Timeline:** *(Deeply Expanded in §4)*<br>TP4 and TP8 at $c=1, c=8, c=32$, captured via `nsys profile --cuda-graph-trace=node` | Captures micro-architectural kernel timeline inside real serving step; measures wave-quantization tails and launch gaps | Replaces eager kernel inventory with true serving time-shares in Profiler tab | **1h 00m** |
| **B2** | **Distributed Layouts Under Load (The Major Gap):**<br>TP4/PP4 and TP16/PP1 at 128K ($c=2, c=4, c=8$), 1M ($c=2, c=4$), and 8K $c=8$ on native fabric (TP4/PP2 if time allows) | Establishes multi-user concurrency scaling, queue delays, KV memory limits, and pipeline bubble collapse under load | Fills the largest vacant area in the dashboard; adds under-load rows to Scale-Out tab | **3h 00m** |
| **B3** | **Statistical Repeatability ($n=5$ Runs):**<br>5 consecutive runs at: 8K $c=8, c=32$; open-loop 0.75×, 0.90×, 1.0×; 128K $c=4, c=8$; open-loop 0.50× (warm engine, prefix caching off) | Replaces $n=1$ with rigorous statistical confidence intervals where run-to-run noise reaches 2–5% | Adds error bars to throughput knee and loaded latency curves | **2h 00m** |
| **B4** | **API Server Process Concurrency Scaling:**<br>Test `--api-server-count 2` and `4` with engine-core pinning at 8K $c=8, c=32$, and open-loop 1.0× | Isolates non-GPU server overhead (tokenization, admission, streaming) which scales from 15 ms to 230 ms under load | Quantifies the "outside-engine" segment of the first-token latency budget | **30 min** |
| **B5** | **FP8 KV-Cache Serving Benchmark:**<br>TP4/PP1 at 128K ($c=1, c=4$), 512K $c=1$, and 1M $c=1$ under FP8 KV (contingent on A2 pass) | Validates predicted 2× KV capacity (16.3M tokens) and decode token speedup (10.3 ms → 7.9 ms at 1M) | Validates D3 capacity; provides ground truth for long-context cost per token | **15 min** |
| **B6** | **Re-capture TP16 512K Prefill Profile:**<br>TP16/PP1 at 512K $c=1$, capturing all 16 ranks under Nsight Systems | Replaces single usable rank (1/12) with full multi-rank trace | Validates TP16 long-prompt split on wall-time budget charts | **15 min** |
| **B7** | **Interactive Short-Prompt Sweeps (<8K):**<br>TP4/PP1 at 1,024 and 2,048 token prompts: $c=1, c=8, c=32$, plus open-loop arrival sweep | Characterizes the interactive conversational regime where AllReduce percentage is highest and chunking is absent | Adds interactive chat rows to Scale-Up tab; maps AllReduce curve below 8K | **30 min** |
| **B8** | **Prefix-Cache Miss Root-Cause Audit:**<br>512K repeats with token-exact prompt alignment; 1M repeats with 2 requests following cold prompt | Verifies whether 512K/1M cache misses were caused by tokenizer padding mismatch or eviction threshold | Confirms prefix-reuse guarantees in Scheduler & KV tab | **20 min** |
| **B9** | **Host CPU Memory KV-Cache Offload:**<br>Transfer KV cache to host DRAM and reload at 128K, 512K, and 1M $c=1$ | Measures empirical round-trip context parking latency against 56.5 GB/s PCIe Gen5 bus (predicts 0.28s reload vs 93s prefill at 1M) | Establishes viability of hierarchical KV-cache tiering and agentic session pause | **20 min** |
| **B10** | **Capped Network Prefill Profiles (5 Missing Runs):**<br>128K $c=1$: TP16 at 100G; TP4/PP2, TP8/PP2, TP4/PP4, TP16 at 20G | Completes the planned 8-profile matrix; verifies stage-wait stretch under 16.7 Gbps throttled interconnect | Closes D7 network check and D8 prefill communication mechanism | **25 min** |
| **B11** | **Two-Node Graphs-On Decode Nsight Capture:** *(Deeply Expanded in §4)*<br>CUDA graphs-on decode re-capture across TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 (single and batched) | Measures cross-node pipeline hop and TP16 AllReduce decode overhead directly instead of by subtraction | Provides direct timeline proof for E2E·B distributed decode rows | **30 min** |
| **B12** | **8K Context on Two-Node Distributed Layouts:**<br>8K $c=1$ on TP4/PP2, TP8/PP2, TP4/PP4, and TP16/PP1 | Establishes the short-prompt baseline for multi-node serving (currently two-node data starts at 128K) | Completes full prompt span on distributed comparison panels | **15 min** |
| **B13** | **Profiled Multi-Node Run Under Load:**<br>TP4/PP4 at 512K $c=2$, full per-rank Nsight Systems trace | Measures whether pipeline bubbles expand or compress when multiple requests interleave across stages | Disentangles pipeline fill latency from structural layer imbalance under load | **15 min** |
| **SUBTOTAL** | **Group B Execution Time** | | | **9h 35m** *(~7h wall time)* |

---

### Group C: Production Architecture & Advanced Characterizations (~3.0+ Hours)

| Run ID | Detailed Run Configuration | Question Answered & Target Discovery | Numbers Affected in Dashboard | Machine Time |
| :---: | :--- | :--- | :--- | :---: |
| **C1** | **Dual-Node Data Parallelism (DP=2 × TP=8):**<br>One TP8 replica per node, zero cross-node forward-pass communication, $2 \times 8.2\text{M}$ token KV pool. Run under load at 8K ($c=8..64$), 128K ($c=4..16$), 512K ($c=2..4$) | Characterizes the optimal production serving layout: coordinator overhead, dummy waves, and aggregate usable tokens/s | Adds a premier production deployment tier to the Executive & Scale-Out tabs | **3h 00m** |
| **C2** | **FP8 KV Long-Context Accuracy (Needle-in-a-Haystack):**<br>Needle retrieval across 128K, 512K, 1M context windows under FP8 KV vs BF16 baseline | Evaluates accuracy and retrieval degradation under 8-bit quantized KV cache | Quality audit (reported in dedicated accuracy card) | *Separate harness* |
| **SUBTOTAL** | **Group C Execution Time** | | | **3h 00m** |

---

## 4. Deep Technical Expansion: Deep Dives on A6, B1, B11, and R1–R4

This section provides comprehensive technical derivations, root causes, execution commands, and mathematical formulations for the key requested runs:

---

### Deep Dive A6: Closed-Loop Wave Trimming & Start-Burst De-Contamination
* **The Root Problem:**
  In closed-loop benchmarking (`concurrency = C`), all $C$ client threads dispatch their first requests simultaneously at timestamp $t=0$. This creates an artificial, synchronized wave burst that never occurs in real production serving (where arrivals follow a stochastic Poisson or Gamma process).
* **The Mathematical Distortion in V8:**
  Because V8 ran 4 waves per closed-loop point ($4 \times C$ total requests), the first synchronized wave heavily skews the run mean:
  * **At 8K $c=32$:** The first 32 requests encounter massive queuing and average **3.70 s** TTFT. The subsequent 96 requests execute at steady state, averaging **0.94 s** TTFT. However, the dashboard currently reports the unweighted mean of **1.62 s** (a +72% artificial distortion)!
  * **At 8K $c=16$:** Wave 1 averages **2.00 s** vs **0.88 s** for Waves 2–4.
  * **At 8K $c=8$:** Wave 1 averages **1.10 s** vs **0.81 s** for Waves 2–4.
  * **At 128K $c=8$:** Wave 1 averages **20.3 s** vs **8.8 s** for steady-state waves.
* **The Drain Distortion on Inter-Token Latency (ITL):**
  The opposite artifact distorts the token decode time at the end of the run: during the final drain wave, requests finish and leave the engine running with fewer concurrent requests, running faster than true loaded steady state.
  * **At 8K $c=32$:** The reported run mean ITL is **34.5 ms**, but the steady-state loaded ITL (excluding the drain) is **37.0 ms**.
  * **At 128K $c=8$:** The reported run mean ITL is **188 ms**, whereas steady-state loaded ITL is **218 ms**.
* **Remediation Specification (Zero Machine Time):**
  This requires **zero machine hours** because per-request timestamps (`start_time`, `first_token_time`, `finish_time`, `token_latencies`) are preserved in `metrics_node0.jsonl` and `bench.json`.
  1. **Trimming Algorithm:**
     $$\text{TTFT}_{\text{steady}} = \frac{1}{N - C} \sum_{i = C}^{N - 1} \text{TTFT}_i \quad \text{(Drop Wave 1: requests } 0 \dots C-1\text{)}$$
     $$\text{ITL}_{\text{steady}} = \text{Mean ITL across steady-state active concurrency window}$$
  2. **Rule for all future runs:** Size every new closed-loop run at $\ge 10$ waves so the startup transient represents $<10\%$ of total samples.
  3. **Dashboard Impact:** Re-renders all TTFT vs Concurrency curves in Tab 4 with steady-state numbers, removing the misleading "knee" spike at $c=32$.

---

### Deep Dive B1: True CUDA Graphs-On Nsight Decode Kernel Breakdown
* **The Root Problem:**
  In V8, single-node decode Nsight System traces were captured with `--enforce-eager`. While this yielded a complete inventory of individual kernel names, eager mode forces individual host-to-device kernel launches, stretching a decode step from **4.47 ms** (in production serving) to **30.5 ms**!
  * Although PyTorch profiler traces were taken with CUDA graphs ON (closing on the serving token at 4.52 ms vs 4.47 ms), PyTorch traces lack SM warp occupancy, memory throughput, and microsecond hardware timeline resolution.
* **Technical Execution Requirements:**
  Capture TP4 and TP8 at $c=1$, $c=8$, and $c=32$ using Nsight Systems with explicit graph node interception:
  ```bash
  nsys profile \
    --trace-fork-before-exec=true \
    --cuda-graph-trace=node \
    --trace=cuda,nvtx,nccl,cublas,osrt \
    --capture-range=cudaProfilerApi \
    --capture-range-end=repeat \
    -o "$PROFILE_ROOT/vllm_decode_graphson" \
    "${SERVER_CMD[@]}"
  ```
* **Why `--cuda-graph-trace=node` is Crucial:**
  Without `--cuda-graph-trace=node`, Nsight Systems renders the entire CUDA graph execution as a single monolithic block labeled `cudaGraphLaunch`. With `--cuda-graph-trace=node`, the profiler instruments the inner execution nodes:
  1. `ncclKernel_AllReduce_RING_LL`: Exact communication time inside the graph.
  2. `cutlass_gemm_kernel`: Weight projection and attention QKV GEMMs.
  3. `flashinfer::BatchDecodeWithPagedKVCacheKernel`: Memory-bound KV cache lookup.
  4. LayerNorm & RMSNorm elementwise kernels.
* **Key Discoveries Resolved by B1:**
  * **The TP8 Serving AllReduce Gap:** Explains why TP8 AllReduce is **58.7 µs** per call in serving vs **37.6 µs** in synthetic `nccl-tests`. It will reveal whether the gap is CUDA graph launch overhead, stream synchronization, or warp serialization across the NUMA socket.
  * **Batched Decode Wave-Quantization:** At $c=32$, reveals whether GEMM tiles evenly divide into Ada SMs (142 SMs on RTX PRO 6000 Ada) or leave idle SM tails.

---

### Deep Dive B11: Two-Node Distributed Decode Re-Capture (CUDA Graphs On)
* **The Root Problem:**
  On the two-node distributed configurations (`TP4/PP2`, `TP8/PP2`, `TP4/PP4`, `TP16/PP1`), the per-worker SQLite exports failed in V8:
  * Usable rank export ratios: `TP4/PP2` had 2 of 16 ranks; `TP8/PP2` had 0 of 9 ranks; `TP16/PP1` had 0 of 16 ranks; batched decode had 0 usable ranks across all configurations.
  * Consequently, the dashboard's cross-node decode penalty (**208 µs per call**) had to be derived *indirectly by subtraction* rather than proven by direct timeline trace.
* **Root Cause of Previous Export Failure:**
  1. Ray worker processes on Node 1 exited immediately upon client completion before the Nsight background daemon completed writing the final buffer to disk.
  2. Ray helper worker ranks produced 0-byte `.nsys-rep` stubs that caused batch postprocessing scripts to error out.
* **Remediation Specification:**
  1. Apply the flush synchronization daemon implemented in [`18_run_vllm_multi_node_profiles.sh`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profiles.sh):
     ```bash
     # Wait until Nsys process terminates and buffer stabilizes
     wait_nsys_local "$NODE0_SESSION/logs/nsight"
     wait_nsys_remote "$NODE1_SESSION/logs/nsight"
     ```
  2. Purge all 0-byte `.nsys-rep` stubs before running [`19_postprocess_nsys.py`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/scripts/06_deep_kernel_and_torch_profiling/19_postprocess_nsys.py).
  3. Re-run single ($c=1$) and batched ($c=8$) decode across all four distributed layouts.
* **Target Insight Delivered:**
  * Directly measures the physical **P2P activation transfer** between Node 0 and Node 1 in PP2 and PP4.
  * Directly isolates the **100G VPC socket latency** of cross-node AllReduce in TP16, closing Discovery D8 with empirical ground truth.

---

### Deep Dive R1: Continuous Intermediate Context Inflection Curve (16K, 32K, 64K, 256K)
* **The Root Problem:**
  V8 measures context length in massive discrete leaps: $8\text{K} \to 128\text{K} \to 512\text{K} \to 1\text{M}$. There are zero data points between 8K and 128K, and zero points between 512K and 1M.
  * This creates an empirical blindspot: Where does activation memory exceed L2 cache? At what prompt length does chunked prefill become mandatory? How does TTFT scale in the common enterprise document window (16K to 64K)?
* **Experimental Configuration:**
  * **Topologies:** `TP4/PP1` and `TP8/PP1` (Single Node).
  * **Target Prompt Lengths:**
    1. **16,384 tokens (16K):** Typical long-form technical article / report.
    2. **32,768 tokens (32K):** Standard codebase file bundle / legal contract.
    3. **65,536 tokens (64K):** Enterprise financial repository / multi-PDF bundle.
    4. **262,144 tokens (256K):** High-density book / multi-repo context.
  * **Load:** $c=1$ (latency baseline) and $c=4$ (concurrency pressure).
  * **Machine Time:** 45 minutes total.
* **Deliverables to the Dashboard:**
  * Replaces stepped bar charts with a smooth, continuous power-law regression curve:
    $$T_{\text{prefill}}(L) = \alpha L + \beta L^2$$
  * Pinpoints the exact inflection point where prompt chunking transitions from compute-bound to memory-bandwidth-bound.

---

### Deep Dive R2: Conversational Multi-Turn Agentic Workload Sweeps (4K Context, $c=1..16$)
* **The Root Problem:**
  Contemporary AI systems (coding assistants, autonomous agents, tool-calling pipelines) do not submit isolated, independent 8K or 128K queries. They operate as **stateful, multi-turn conversational sequences** that progressively accumulate context:
  $$\text{Turn 1 (System Prompt + Task)} \to \text{Turn 2 (Tool Output)} \to \text{Turn 3 (Code Execution Result)} \to \dots$$
  V8 only tested prefix caching under static, synthetic repeated prompts.
* **Experimental Configuration:**
  * **Topology:** `TP4/PP1`, `TP8/PP1`.
  * **Sequence Structure (5 Turns per Session):**
    * *Turn 1:* 1,024 input $\to$ 256 output (Cold prefill, Cache Miss).
    * *Turn 2:* 2,048 input (1,280 prefix + 768 new) $\to$ 256 output.
    * *Turn 3:* 3,072 input (2,304 prefix + 768 new) $\to$ 256 output.
    * *Turn 4:* 4,096 input (3,328 prefix + 768 new) $\to$ 256 output.
    * *Turn 5:* 5,120 input (4,352 prefix + 768 new) $\to$ 512 output.
  * **Concurrency:** $c=1, c=4, c=8, c=16$ concurrent agent sessions.
  * **Machine Time:** 25 minutes total.
* **Deliverables to the Dashboard:**
  * **"Agentic Serving Performance" Dashboard Card:**
    * Displays the **effective TTFT decay curve** across turns: Turn 1 TTFT is $\sim 110\,\text{ms}$, dropping to $<25\,\text{ms}$ for subsequent turns due to prefix reuse.
    * Measures KV-cache block retention stability when 16 concurrent agents interleave turns.

---

### Deep Dive R3: Cloud Network Jitter & Loss Resilience Stress Test (`tc netem`)
* **The Root Problem:**
  V8 benchmarked inter-node communication under clean synthetic bandwidth caps (100G and 20G HTB), which model steady-state throughput throttles. However, real enterprise clouds (Google Cloud Andromeda VPC, AWS EFA) exhibit **packet jitter, transient bufferbloat, and dropped packets under load**.
  * Is Pipeline Parallelism (PP4) truly more resilient to network noise than Tensor Parallelism (TP16)?
* **Experimental Configuration:**
  * Inject synthetic network noise on inter-node interfaces using Linux traffic control:
    ```bash
    sudo tc qdisc add dev eth0 root netem delay 1.5ms 0.5ms loss 0.05%
    ```
  * **Target Workloads:**
    1. `TP16/PP1` at 128K $c=1$.
    2. `TP4/PP4` at 128K $c=1$.
  * **Machine Time:** 30 minutes total.
* **Deliverables to the Dashboard:**
  * **Fault-Tolerance Comparison Matrix:**
    * Proves the architectural hypothesis: In `TP16`, because AllReduce occurs at every transformer layer (55 times per step), a 0.05% packet loss causes frequent TCP window collapses, ballooning first-token latency by over **350%**.
    * In `PP4`, communication occurs only at pipeline stage boundaries (3 times total per forward pass), making pipeline parallelism **immune to transient packet jitter** ($<3\%$ latency variation).

---

### Deep Dive R4: High-Resolution Inter-Token Latency (ITL) Jitter & Tail-P99 Analysis
* **The Root Problem:**
  The current dashboard only reports **mean TPOT** and **P95 TPOT**. For real-time human users and streaming voice interfaces, human perception is hypersensitive to **P99 token pauses** (a sudden 150 ms pause ruins the illusion of instantaneous speech or reading).
  * In serving systems with chunked prefill, ongoing token generation is momentarily stalled whenever a new request arrives and its prefill chunk is scheduled.
* **Experimental Configuration:**
  * Capture complete per-token timestamp vectors across 100 requests at:
    1. 8K context at $c=1, c=8, c=16$.
    2. 128K context at $c=1, c=4$.
  * Calculate inter-token time intervals: $\Delta t_i = t_{i} - t_{i-1}$.
  * **Machine Time:** 20 minutes total.
* **Deliverables to the Dashboard:**
  * **"Streaming Smoothness & Pause Frequency" Violin Plot:**
    * Plots P50, P90, P95, P99, and maximum pause latency.
    * Highlights the exact probability of experiencing token generation pauses $>50\,\text{ms}$, $>100\,\text{ms}$, and $>200\,\text{ms}$ under heavy concurrency.

---

## 5. Consolidated Execution Timeline & Machine Time

```mermaid
gantt
    title V8 Benchmark Expansion Execution Timeline
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Group A (Quick Wins)
    A1 Chunk Budget & A2 FP8 Smoke     :a1, 00:00, 15m
    A4 PP2 15/12 Partition Rebalance   :a4, after a1, 20m
    A7 NUMA Pinning & A8 NCCL Socket   :a7, after a4, 35m
    
    section Group B (Core Campaign)
    B1 Graphs-On Decode Nsight Capture :b1, after a7, 60m
    B2 Distributed Layouts Under Load  :b2, after b1, 180m
    B3 Statistical Repeats (n=5)       :b3, after b2, 120m
    B4-B10 Profiling & Offload Sweeps  :b4, after b3, 130m
    B11-B13 Multi-Node Profiles        :b11, after b4, 60m
    
    section Strategic Expansions
    R1-R4 Context & Agentic Sweeps     :r1, after b11, 120m
    C1 DP=2 x TP8 Production Run      :c1, after r1, 180m
```

| Phase / Group | Focus Area & Content | Runs Count | Machine Time Added | Wall-Clock Time (Parallelized) |
| :--- | :--- | :---: | :---: | :---: |
| **Group A** | Immediate Discrepancy & Artefact Fixes (A1–A8) | 8 items (6 runs) | **01h 10m** | **01h 10m** |
| **Group B** | Core Gaps, Multi-Node Load & Profiles (B1–B13) | 13 runs | **09h 35m** | **~07h 00m** |
| **Strategic (R1–R4)** | Intermediate Context, Agentic & Jitter Sweeps | 4 runs | **02h 00m** | **01h 30m** |
| **Group C (C1)** | Dual-Node Data Parallelism (DP=2 × TP8) | 1 suite (12 runs) | **03h 00m** | **03h 00m** |
| **Cooldowns & Sync** | Inter-run VRAM clearing, GCS vault upload & parsing | — | **01h 00m** | **01h 00m** |
| **TOTAL** | **Full Master Characterization Expansion** | **37 Runs** | **16h 45m** | **~13h 40m** |

---

## 6. Recommended Execution Strategy

1. **Phase 1 Priority (Immediate / 70 Minutes):**
   * Run **Group A**. This immediately verifies whether the 8K loaded numbers carry the chunk-budget artifact, tests FP8 capability, confirms PP2 15/12 split gains, and fixes the validator audit.
2. **Phase 2 Overnight Campaign (~7 Hours Wall-Clock):**
   * Run **Group B**. This fills all distributed under-load gaps ($c=2, 4, 8$), captures graphs-on decode timelines, and resolves the multi-node profiler export vacancies.
3. **Phase 3 Strategic Sweeps (~4.5 Hours):**
   * Run **R1–R4** and **C1 (DP=2 × TP=8)**. Maps continuous context curves, multi-turn agentic performance, network jitter robustness, and production data parallelism.
