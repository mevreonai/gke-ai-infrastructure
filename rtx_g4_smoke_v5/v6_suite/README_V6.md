# RTX PRO 6000 V5 vLLM Deep-Characterization Suite — V6

This is a drop-in evolution of the attached working V5 suite. It preserves the same GCP node names, vLLM virtual environment assumption (`~/vllm_env`), model, revision, Ray architecture, and result-folder style, while fixing the correctness gaps found in the architectural review.

## Evidence guardrail

The model under test is `moonshotai/Kimi-Linear-48B-A3B-Instruct` at revision `e1df551a447157d4658b573f9a695d57658590e9`. It is a **BF16-weight surrogate**. Absolute TTFT, TPOT or tokens/s from these runs must not be scaled to Kimi K3. Use the runs for runtime mechanisms, relative topology/chunk/cache/scheduler trends, and regime changes.

## Main V6 fixes

- Per-case `kv_cache_dtype` is honored; FP8-KV is no longer silently replaced by the default.
- Exact HF revision is passed to `vllm serve` and the `/v1/models` response is saved.
- TP4 only exposes and samples GPUs 0–3; idle GPUs 4–7 no longer dilute utilization/power.
- Warmups are run **before** the telemetry window; measured Prometheus deltas exclude warmup traffic.
- `max_num_seqs` is first-class and has dedicated long-context sensitivity cases.
- Closed-loop concurrency and open-loop arrival-rate tests are separated.
- Open-loop RPS is generated from measured service rate; no arbitrary RPS numbers are hard-coded.
- 512K/1M higher-concurrency tests are safety-gated using prior KV usage/preemption evidence.
- Prefix caching uses `prefix_repetition` with a deterministic single shared prefix.
- `kv_cache_memory_bytes` and `gpu_memory_utilization` are not combined misleadingly.
- Native KV offload size is recorded as total across TP ranks and derived per-rank size is saved.
- Multi-node uses `--distributed-executor-backend ray` and captures Ray placement snapshots.
- TP4/PP2 forces 4 visible GPUs/node so an 8-GPU job cannot collapse onto one node.
- Multi-node GPU telemetry is captured from both nodes.
- Dedicated Nsight profiles include NCCL and separate prefill/decode/batched-decode modes.
- Dedicated Torch profiler run is separated from benchmark runs because of its high overhead.
- Summaries validate actual input lengths and do not treat missing metrics as zero.
- p95 is treated as statistically trustworthy only at N>=20; p99 at N>=100. Raw values remain available.
- Kernel-name KDA/MLA/MoE attribution is explicitly heuristic; aggregate kernel time is not mislabeled as wall-clock critical path.

## 1. Install / unpack

Copy this bundle to Node 0 and keep the same environment as the prior successful suite.

```bash
cd ~/v5_profiling
source ~/vllm_env/bin/activate
```

## 2. Discover nodes and preserve transport provenance

```bash
./rtx_g4_smoke_v5/00_init_gcp_config.sh
source RUN_CONFIG.env
```

By default this preserves the prior GCP Socket/NCCL net-shim workaround. Every distributed result is tagged through `GCP_NETWORK_PROVENANCE` and `NCCL_TRANSPORT_PROVENANCE` so it is not confused with RoCE/GPUDirect or the local physical 10GbE cluster.

## 3. Mandatory preflight

```bash
python3 rtx_g4_smoke_v5/07_preflight_v5.py --out ./preflight
python3 rtx_g4_smoke_v5/08_validate_kimi_linear.py \
  --revision e1df551a447157d4658b573f9a695d57658590e9 \
  --out ./kimi_linear_provenance_resolved.json
```

Do not start the expensive sweep if preflight reports required CLI flags missing.

## 4. Qualification run first

```bash
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py \
  --out ./v5_single_node_results \
  --group qualification
```

Then summarize:

```bash
python3 rtx_g4_smoke_v5/15_summarize_vllm.py \
  ./v5_single_node_results \
  --out ./v5_single_node_results/summary_v6

python3 rtx_g4_smoke_v5/17_build_serving_analysis.py \
  ./v5_single_node_results/summary_v6/vllm_runs.json \
  --out ./v5_single_node_results/analysis
```

Review the qualification data before launching 512K/1M, concurrency, cache, or distributed cases.

## 5. Recommended single-node groups

Run groups independently to control GCP cost:

```bash
# Context scaling, including nominal 1,000,000-token input
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_baseline --group baseline

# Prefill vs decode separation
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_phase --group prefill_decode

# 4K / 8K / 16K chunked prefill
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_chunk --group chunking

# Backlogged / closed-loop concurrency ladders
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_closedloop --group closed_loop

# max_num_seqs long-context sensitivity
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_scheduler --group scheduler_limits

# Deterministic prefix caching
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_prefix --group prefix_cache

# FP8 KV cache sensitivity
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_kv --group kv_dtype

# Native vLLM CPU KV offload pressure
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_offload --group offload

# Instrumentation overhead A/B
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py --out ./runs_observer --group observer_overhead
```

`--all` exists, but is intentionally **not** the default.

## 6. Open-loop arrival-rate / user-load characterization

First run and summarize closed-loop concurrency. Then generate RPS cases from the **measured request throughput**:

```bash
python3 rtx_g4_smoke_v5/13_generate_load_cases.py \
  --summary-json ./runs_closedloop/summary_v6/vllm_runs.json \
  --out ./10c_vllm_generated_load_cases.json \
  --include-probe
```

The generator creates Poisson/gamma arrival-rate points at fractions of the highest measured successful request throughput. It does not invent an absolute RPS.

Run them:

```bash
python3 rtx_g4_smoke_v5/11_run_vllm_surrogate.py \
  --cases ./10c_vllm_generated_load_cases.json \
  --out ./runs_openloop \
  --all
```

This is the dataset to use for real capacity-envelope / queueing-knee analysis. `max-concurrency` alone is not a user-arrival model.

## 7. Multi-node topology runs

```bash
source RUN_CONFIG.env
./rtx_g4_smoke_v5/12_run_vllm_multi_node.sh --group qualification
./rtx_g4_smoke_v5/12_run_vllm_multi_node.sh --group topology
```

The script restarts Ray per topology. `tp4_pp2_dist` exposes only four GPUs on each node, guaranteeing a remote PP boundary. Ray status, node, actor and placement-group snapshots are stored per case. Node 0 and Node 1 GPU telemetry are captured separately.

Cross-zone results remain **GCP_CROSS_ZONE** mechanism/sensitivity evidence and must not be presented as a direct measurement of the local 10GbE cluster.

## 8. Nsight Systems profiles — run separately

These are profiling runs, not benchmark measurements:

```bash
PROFILE_MODE=prefill TP=4 ./rtx_g4_smoke_v5/14_run_vllm_nsys_profile.sh
PROFILE_MODE=decode TP=4 ./rtx_g4_smoke_v5/14_run_vllm_nsys_profile.sh
PROFILE_MODE=batched_decode TP=4 ./rtx_g4_smoke_v5/14_run_vllm_nsys_profile.sh
```

The script traces CUDA + NVTX + NCCL and exports CSV plus SQLite when supported. Aggregate GPU kernel work must not be interpreted as wall-clock critical path.

Optional high-overhead Torch profile:

```bash
TP=4 INPUT_LEN=8192 OUTPUT_LEN=128 CONCURRENCY=1 \
  ./rtx_g4_smoke_v5/14b_run_vllm_torch_profile.sh
```

## 9. Safety gate for 512K / 1M concurrency

The c2/c4 long-context cases do not launch blindly. They depend on a preceding successful run and require captured KV/preemption metrics below the configured safety threshold. If metrics are absent, the next case is marked `SKIPPED_BY_SAFETY_GATE` instead of being guessed safe.

The threshold is a run-safety control, **not** a performance conclusion.

## 10. What the final dataset can answer

After all selected groups are summarized, the analysis can produce:

- TTFT scaling: 8K -> 128K -> 512K -> 1M.
- TPOT/ITL decode behavior vs context and active concurrency.
- Matched TP4 vs TP8 runtime ratios and correlation with V4 topology/NCCL evidence.
- 4K/8K/16K chunk tradeoff: TTFT, TPOT, throughput, queueing, KV pressure.
- Closed-loop batching frontier by context.
- Open-loop arrival-rate capacity envelope: request rate -> queue -> TTFT/TPOT -> throughput.
- max_num_seqs sensitivity at long context.
- Prefix first-request vs repeated-prefix TTFT and prefix metrics.
- FP8-KV capacity/runtime changes without conflating KV dtype with model weight precision.
- Native CPU KV-offload traffic/time and whether it coincides with GPU idle/queue/preemption.
- TP16/PP1 vs TP8/PP2 vs TP4/PP4 vs TP4/PP2 mechanism-level topology behavior.
- With Nsight: prefill/decode kernel mix, NCCL event frequency, launch gaps and overlap patterns.

## Files added / changed

- `07_preflight_v5.py` — CLI/environment validation.
- `09_metrics_sampler.py` — GPU selection + remote/GPU-only + host telemetry.
- `10_vllm_surrogate_cases.json` — stronger cost-conscious test matrix.
- `10b_vllm_multi_node_cases.json` — explicit Ray GPU/node topology.
- `11_run_vllm_surrogate.py` — correctness fixes, warmup isolation, safety gates, load support.
- `12_run_vllm_multi_node.py/.sh` — current Ray backend, placement evidence, two-node telemetry.
- `13_generate_load_cases.py` — evidence-derived open-loop RPS and probe workload generator.
- `14_run_vllm_nsys_profile.sh` — phase-specific CUDA/NVTX/NCCL profiling.
- `14b_run_vllm_torch_profile.sh` — dedicated high-overhead CPU/shape profiler.
- `15_summarize_vllm.py` — validated, uncertainty-aware aggregation.
- `16_analyze_vllm_profiles.py` — conservative profile grouping.
- `17_build_serving_analysis.py` — serving-oriented matched comparisons/frontiers.

