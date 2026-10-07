# Time Budget Data & Methodology Guide (Review v1.2 §7)

This directory contains the unified end-to-end wall-time budget data files and charts for DeepSeek V4.1 Flash (Kimi 48B) serving characterization on NVIDIA H100 PCIe (NVLink-free) clusters.

## Delivered Artifacts

1. **First Token (TTFT) Time Budget:**
   - `wall_time_budget_first_token.png` & `.csv`: 6-layout comparison across 8K, 128K, 512K, 1M context lengths (24 operating points).
   - `wall_time_budget_first_token_under_load.png` & `.csv`: Every loaded point run during the pilot (24 operating points covering closed-loop c1–c32 and open-loop sweeps).

2. **Decode Token (TPOT / ITL) Time Budget:**
   - `wall_time_budget_decode_token.png` & `.csv`: 6-layout comparison across 8K, 128K, 512K, 1M context lengths (24 operating points).
   - `wall_time_budget_decode_token_under_load.png` & `.csv`: Every loaded point run during the pilot (24 operating points), including batch size metrics.

3. **Prefill Composition (128K):**
   - `prefill_composition_128k_by_layout.csv`: Cross-layout kernel work share across TP4/PP1, TP8/PP1, TP4/PP2, TP8/PP2, TP4/PP4, and TP16/PP1.

---

## Column Definitions

### First Token Budget (`wall_time_budget_first_token*.csv`)
- `operating_point`: Model execution configuration (Layout · Context · Concurrency / Load).
- `split_source`: `measured` (from per-worker profiler traces/engine histograms) or `modelled` (†).
- `first_token_ttft_s`: Total end-to-end client Time-To-First-Token in seconds.
- `queue_wait_pct`: Time spent queued waiting for admission (from vLLM engine histogram `vllm:time_in_queue_seconds`).
- `prefill_collectives_pct`: Time spent in tensor parallel collectives (AllReduce) during prompt processing.
- `pipeline_waits_pct`: Time spent waiting across pipeline parallel stage boundaries (SendRecv / P2P handoffs).
- `prefill_kernels_pct`: Active execution time in FlashAttention, GEMM, MoE, and KDA compute kernels.
- `shared_steps_pct`: Time where prompt chunks share execution steps with other concurrently active requests (their decodes or chunked prefills).
- `outside_engine_pct`: Residual time spent outside engine core (tokenization, network HTTP transit, API server serialization, scheduler bookkeeping, sampling).

### Decode Token Budget (`wall_time_budget_decode_token*.csv`)
- `operating_point`: Model execution configuration.
- `split_source`: `measured` or `modelled` (†).
- `decode_tpot_ms`: Mean inter-token latency (TPOT) in milliseconds.
- `collectives_ar_pct`: Percentage of step time in AllReduce ring barriers.
- `pipeline_hops_pct`: Percentage of step time crossing PP stage boundaries.
- `memory_floor_pct`: Theoretical bandwidth floor: $(1.6\text{B model weights read} + \text{active expert weights} + \text{active KV}) / 1.72\text{ TB/s}$.
- `kernels_above_floor_pct`: Compute execution, CUDA launch overhead, and small-batch wave quantization tail latency.
- `waiting_behind_prefills_pct`: Token latency spent blocked while long chunked prefills occupy the forward step.
- `own_step_ms`: Median duration of a normal decoding forward pass (ITL $\le 100\text{ ms}$).
- `decoders_per_step`: Mean number of requests actively producing tokens simultaneously in the step.
- `experts_touched`: Expected unique MoE experts accessed per step out of 256 routed experts.
- `stalled_tokens_pct`: Percentage of generated tokens experiencing ITL $> 100\text{ ms}$.

---

## Key Empirical Findings Surfaced Under Load

1. **Chunk Boundary Bottleneck (8K at c4):**
   The prompt length ($8,192\text{ tokens}$) exactly equals `max_num_batched_tokens`. As soon as a single decode token sits in the engine, the prompt exceeds the batch token ceiling and requires a second chunk. That tail chunk waits an entire forward step behind the next request's first chunk, causing own prefill to double ($0.21\text{ s} \to 0.42\text{ s}$) at c4. Expanding the chunk budget to $8,448\text{ tokens}$ eliminates this delay.

2. **MoE Batch Expansion & Memory Floor Re-binding:**
   At concurrency 1, an MoE step reads only 8 active experts per token ($0.9\text{ ms}$ at memory bandwidth). As concurrency scales to c32, uniform routing expands the active expert set to 163 of 256 experts (and 222 at full load), driving the weight read floor to $10.5\text{ ms}$ and $14.9\text{ ms}$. By c16, the decode step is firmly memory-bound on routed weights, causing throughput to scale sub-linearly with concurrency.

3. **vLLM Engine Waves vs GPU Wave Quantization:**
   - **vLLM V1 Waves:** Data-parallel / Expert-parallel lockstep coordination episodes. With $DP=1, EP=1$, no engine waves occurred.
   - **GPU SM Wave Quantization:** Incomplete SM thread block scheduling at small batches, which lives inside the *kernels above memory floor* component.
