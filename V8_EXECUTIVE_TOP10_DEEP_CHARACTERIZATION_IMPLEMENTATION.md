# V8-FULL Dashboard — Executive Deep-Characterization Top 10 Implementation Spec

**Target UI:** `MASTER_CHARACTERIZATION_DASHBOARD_realrun_v4_new_latest.html`  
**Model under test:** Kimi-Linear-48B-A3B-Instruct BF16 surrogate  
**Evidence package:** `results_V8_runs.zip`  
**Purpose:** Add the ten highest-value, non-obvious characterization discoveries to the **Executive** tab while keeping the existing detailed tabs as drill-down/source-of-truth views.

---

## 0. Executive principle

The Executive tab should no longer behave like a summary of benchmark cards. It should answer, in order:

1. **What changed as the workload changed?**
2. **What resource became exposed?**
3. **What does that do to a real user's TTFT/TPOT/throughput?**
4. **Which parallelism/runtime knob has leverage?**
5. **Which common metric can mislead us?**
6. **What exact measured artifacts prove the conclusion?**

The two Kimi K3 reference PDFs provide the methodology, **not the numerical model parameters**:

- `Kimi K3 V4 Performance-Accounting Model and UI Design.pdf`
- `Kimi K3 Performance Decomposition and V4_V5 Deep-Characterisation UI.pdf`

For the actual 48B run, all dimensions and results must come from the V8 run package. The core accounting discipline to preserve is:

```text
MEASURED    = directly present in benchmark / telemetry / trace
CROSS-VALIDATED = same behavior independently visible in another evidence layer
DERIVED     = deterministic arithmetic/regression from measured values
MODELED     = interpolation/extrapolation or assumed mapping
UNRESOLVED  = not defensible from available evidence
```

Never render a derived regression, profiler aggregate, or heuristic kernel group as `DIRECT_MEASURED`.

---

# 1. Executive layout recommendation

## 1.1 First screen: the Top 3 hero discoveries

The first screen should contain only the three discoveries that most change deployment understanding.

### Hero A — Hybrid-Attention Regime Shift
**One-line takeaway**

> **Long context changes the dominant scaling law: full-attention work grows ~quadratically while KDA/MoE remain approximately linear.**

### Hero B — Fabric Exposure Fingerprint
**One-line takeaway**

> **TP16 is roughly two orders of magnitude more fabric-exposed than TP4/PP4 in the measured bandwidth-sensitivity experiment.**

### Hero C — Concurrency Value Destruction
**One-line takeaway**

> **At 1M, more concurrency adds almost no useful throughput; 96–98% of the additional TTFT is queue residence.**

Each hero card must have:
- one visual,
- one large number,
- one implication,
- an evidence badge,
- a click-through source list.

Do **not** place a generic profiler pie chart above these.

---

## 1.2 Second Executive section: seven deeper discoveries

Show discoveries #4–#10 below the hero row as a compact **“Deep Characterization”** section.

Recommended layout:
- 2-column cards on desktop;
- each card contains a small high-information visual;
- expanded card shows formula, evidence chain, exact artifact paths and caveat;
- all values should be populated from normalized data, not manually typed Chart.js arrays.

---

# 2. Common data sources and canonical hierarchy

Use these as the canonical data hierarchy for all ten discoveries.

## Primary canonical summaries

```text
results/real_data/final_validation/FINAL_VALIDATION.json
results/real_data/final_validation/coverage.json
results/real_data/final_validation/combined_vllm_runs.csv
results/real_data/final_validation/combined_vllm_runs.json
results/real_data/final_validation/NCCL_POLICY_AUDIT.json
results/real_data/final_validation/SCALEOUT_TELEMETRY_AUDIT.json
results/real_data/final_validation/SCALEOUT_NETWORK_COVERAGE.md
```

## Model identity

```text
results/real_data/model_validation.json
```

Important real-model fields to surface in the evidence drawer:
- hidden size: **2304**
- layers: **27**
- KDA layers: **20**
- full-attention layers: **7**
- experts: **256**
- top-k experts/token: **8**
- precision in this run: **BF16 surrogate**

Do not copy K3's 7168 hidden size or 93-layer dimensions into this UI.

## Hardware / fabric primitives

```text
results/real_data/hardware_processed/iperf.csv
results/real_data/hardware_processed/nccl_points.csv
results/real_data/hardware_processed/nvbandwidth_metrics.csv
results/real_data/hardware_processed/babelstream.csv
results/real_data/hardware_processed/summary.json
```

## Single-node Nsight

```text
results/real_data/profiles_single_node/
```

Relevant subfolders:

```text
tp4_prefill/
tp4_decode/
tp4_batched_decode/
tp8_prefill/
tp8_decode/
tp8_batched_decode/
```

Each contains:
- `cuda_gpu_kern_sum.csv`
- `cuda_api_sum.csv`
- `nvtx_pushpop_sum.csv`
- `bench.json`
- `PROFILE_METADATA.json`
- `nsys_stats.txt`

Guardrail:

```text
results/real_data/profiles_single_node/PROFILE_ANALYSIS.json
```

explicitly warns that aggregate GPU work is **not wall-clock critical-path time**.

## PyTorch Profiler

```text
results/real_data/profiles_torch_single_node/tp4_8k_decode/
results/real_data/profiles_torch_single_node/tp8_8k_decode/
```

Rank-local text exports:

```text
torch/profiler_out_0.txt
...
```

## Distributed Nsight

```text
results/real_data/profiles_multi_node_native/
```

Each profile case contains:
- `PROFILE_VALIDATION.json`
- `NSYS_ANALYSIS.json`
- per-rank `cuda_gpu_kern_sum.csv`
- per-rank `cuda_api_sum.csv`
- `nccl_gpu_time_sum.csv`
- `nccl_op_sum.csv`
- `nvtx_pushpop_sum.csv`
- workload `bench.json`
- workload `PROFILE_CASE_MANIFEST.json`

For Top-10 discovery #1, specifically use:

```text
results/real_data/profiles_multi_node_native/tp4_pp4_dist/prefill_128k/
results/real_data/profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/
```

Only use profiles whose `PROFILE_VALIDATION.json` says the required capture is complete.

---

# 3. TOP 10 executive discoveries

---

# TOP 1 — Hybrid-Attention Regime Shift

## Executive message

> **The 48B model does not have one long-context scaling law. The full-attention component grows almost as N², while KDA and MoE remain approximately N¹; the resource-pressure regime flips as context grows.**

This should be the most scientifically distinctive card.

## Why it is useful

A conventional profiler can tell us that NCCL, attention or MoE consumed some percentage in one trace.

This analysis asks the deeper question:

> **How does each subsystem's measured GPU work scale when the context itself grows?**

That predicts which optimization class will retain leverage as context increases.

## Formula

For component `k`, using the matched 128K and 512K TP4/PP4 distributed profiles:

\[
p_k =
\frac{\ln[W_k(512K)/W_k(128K)]}
{\ln(512K/128K)}
\]

Where `W_k` is the **median per-rank aggregate GPU kernel work** for the component.

This is a **resource-pressure exponent**, not a wall-clock critical-path exponent.

## Real-run results

| Component | 128K aggregate work | 512K aggregate work | Growth | Empirical exponent |
|---|---:|---:|---:|---:|
| Full attention | ~0.30 s | ~4.7–4.8 s | ~15.7× | **~1.99** |
| KDA | ~0.04–0.05 s | ~0.16–0.18 s | ~3.9× | **~0.99** |
| MoE | ~0.17 s | ~0.65 s | ~3.8× | **~0.96** |
| NCCL | ~1.63 s | ~3.56 s | ~2.18× | **~0.56** |
| GEMM family | ~0.10 s | ~0.50 s | ~5.25× | **~1.20** |

The exact dashboard build should recalculate these values from all valid per-rank kernel CSVs rather than hard-code the rounded values above.

## Cross-validation with E2E

Same TP4/PP4 E2E TTFT:

```text
128K -> ~1.710 s
512K -> ~10.222 s
1M   -> ~28.568 s
```

Empirical E2E context exponent:

```text
128K -> 512K : ~1.29
512K -> 1M   : ~1.59
```

The E2E curve is itself becoming more super-linear as attention becomes a larger part of resource pressure.

## Derived crossover

A two-point resource-pressure interpolation places the Attention-vs-NCCL crossover around **~420K tokens**.

Badge this as:

```text
DERIVED — interpolation between profiled 128K and 512K endpoints
```

Do not claim 420K as a directly measured critical-path crossover.

## Required visual

### “Hybrid-Attention Scaling Fingerprint”

Use a **log-log line chart**:

- X: context length
- Y: median per-rank aggregate GPU kernel work
- series:
  - Full attention
  - KDA
  - MoE
  - NCCL
  - optional GEMM
- print the fitted exponent beside each line:
  - Attention `p≈1.99`
  - KDA `p≈0.99`
  - MoE `p≈0.96`
  - NCCL `p≈0.56`

Add a subtle dashed derived crossover marker around 420K.

Add a footer:

> Aggregate GPU kernel work measures resource pressure. It is not exclusive wall-clock attribution.

## Source artifacts

```text
results/real_data/model_validation.json

results/real_data/profiles_multi_node_native/tp4_pp4_dist/prefill_128k/PROFILE_VALIDATION.json
results/real_data/profiles_multi_node_native/tp4_pp4_dist/prefill_128k/NSYS_ANALYSIS.json
results/real_data/profiles_multi_node_native/tp4_pp4_dist/prefill_128k/node0_capture/worker_process_*_processed/cuda_gpu_kern_sum.csv
results/real_data/profiles_multi_node_native/tp4_pp4_dist/prefill_128k/node1_capture/worker_process_*_processed/cuda_gpu_kern_sum.csv

results/real_data/profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/PROFILE_VALIDATION.json
results/real_data/profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/NSYS_ANALYSIS.json
results/real_data/profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/node0_capture/worker_process_*_processed/cuda_gpu_kern_sum.csv
results/real_data/profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/node1_capture/worker_process_*_processed/cuda_gpu_kern_sum.csv

results/real_data/final_validation/combined_vllm_runs.csv
```

## Evidence class

```text
Kernel endpoint values: MEASURED
Exponent: DERIVED
~420K crossover: DERIVED
Architecture interpretation: CROSS-VALIDATED
1M kernel composition: UNRESOLVED — no matched 1M Nsight profile should be invented
```

---

# TOP 2 — Fabric Exposure Fingerprint

## Executive message

> **NIC bandwidth is not the model's communication bandwidth. TP16's TTFT response behaves as if ~116 hidden-width-equivalent bytes/token remain serially exposed to the measured NCCL transport curve, versus roughly ~1 or less for TP4/PP4.**

This is the strongest hardware→application accounting correlation.

## Step 1 — distinguish the bandwidth roofs

Measured Native environment:

```text
iperf/VPC roof:               ~173.6 Gb/s = ~21.70 GB/s
large-message NCCL SendRecv:  ~7.11 GB/s
```

Under caps:

```text
configured 100G:
  iperf       ~54.2 Gb/s
  256M NCCL SendRecv ~5.54 GB/s

configured 20G:
  iperf       ~16.7 Gb/s
  256M NCCL SendRecv ~2.04 GB/s
```

UI must show:

```text
Configured cap
Measured iperf bandwidth
Measured NCCL SendRecv bandwidth
Application TTFT
```

Never label a run only as “100G” if achieved bandwidth was ~54–57 Gb/s.

## Step 2 — fit application sensitivity to the communication primitive

For each context, fit TP16/PP1 TTFT against the measured 256-MiB NCCL SendRecv bandwidth:

\[
T_{\rm TTFT}(B) = T_0 + \frac{V_{\rm exposed}}{B}
\]

Use only the measured Native / configured-100G / configured-20G application runs.

This is a local empirical response model over the measured range, not a universal extrapolation.

## Real-run TP16 result

| Context | Effective exposed byte-equivalent | Fit R² | Hidden-width equivalents/token |
|---|---:|---:|---:|
| 128K | ~69.85 GB | ~0.9996 | **~115.6** |
| 512K | ~279.50 GB | ~0.9995 | **~115.7** |
| 1M | ~535.79 GB | ~0.9997 | **~116.3** |

Normalization:

\[
E_H =
\frac{V_{\rm exposed}}
{N_{\rm tokens}\times H\times b}
\]

with:

```text
H = 2304
b = 2 bytes (BF16)
```

The invariance from 128K→1M is the important finding.

For TP4/PP4, the analogous fitted exposure is around one hidden-width equivalent/token or below across the measured contexts; do not force a fit for topologies whose slope is below the measurement/noise floor.

## Interpretation boundary

Do **not** say:

> TP16 physically sends exactly 116 hidden states per token.

Say:

> TP16's measured TTFT bandwidth sensitivity is equivalent to ~116 hidden-width-equivalent bytes/token of **serially exposed communication** over this measured bandwidth range.

This coefficient can include repeated communication and non-overlapped effects.

## Required visual

### “Fabric Exposure Fingerprint”

Main visual:
- X: context 128K / 512K / 1M
- Y: effective hidden-width equivalents/token
- log Y-axis
- series:
  - TP16/PP1
  - TP4/PP4
  - TP4/PP2
  - only show TP8/PP2 if the fit passes quality/noise gating

Inset:
- TP16 TTFT versus `1 / measured NCCL SendRecv bandwidth`
- display `R²≈0.999`

Add a small 3-step strip:

```text
VPC/IPERF ROOF -> NCCL SENDRECV ROOF -> APPLICATION-EXPOSED RESPONSE
173.6 Gb/s      -> 7.11 GB/s           -> topology-dependent
```

## Source artifacts

```text
results/real_data/model_validation.json
results/real_data/hardware_processed/iperf.csv
results/real_data/hardware_processed/nccl_points.csv
results/real_data/hardware_processed/summary.json

results/real_data/hardware_raw/network_node0/220_sendrecv_GCP_NATIVE_256m_gpu_query.csv
results/real_data/hardware_raw/network_node0/220_sendrecv_GCP_CAPPED_100G_256m_gpu_query.csv
results/real_data/hardware_raw/network_node0/220_sendrecv_GCP_CAPPED_20G_256m_gpu_query.csv

results/real_data/vllm_scaleout_network_matrix/GCP_NATIVE/network_validation/IPERF_VALIDATION.json
results/real_data/vllm_scaleout_network_matrix/GCP_CAPPED_100G/network_validation/IPERF_VALIDATION.json
results/real_data/vllm_scaleout_network_matrix/GCP_CAPPED_20G/network_validation/IPERF_VALIDATION.json

results/real_data/final_validation/combined_vllm_runs.csv
```

Application rows:

```text
case=tp16_pp1_dist
case=tp4_pp4_dist
case=tp4_pp2_dist
bench=128k_c1 / 512k_c1 / 1m_c1
network_mode=native / 100g / 20g
```

## Evidence class

```text
iperf/NCCL/application points: MEASURED
fit coefficients and hidden-state equivalents: DERIVED
physical collective count: UNRESOLVED
```

---

# TOP 3 — Concurrency Value Destruction + Queue Accounting Closure

## Executive message

> **At 1M, concurrency stops buying useful capacity. c4 gives only ~1.5% extra throughput on TP4, while TTFT becomes 2.48×, TPOT ~26× and queue residence ~134 s. 96–98% of the added TTFT is explained by queueing.**

This should replace the current “c≤2 is safe / knee at c4” narrative.

## TP4/PP1 real 1M results

| Load | Output throughput | TTFT | TPOT | Queue mean | Prefill mean | KV | Preemptions |
|---|---:|---:|---:|---:|---:|---:|---:|
| c1 | 0.3415 tok/s | 93.39 s | 10.23 ms | ~0 s | 92.03 s | 12.29% | 0 |
| c2 | 0.3449 tok/s | 139.37 s | 181.97 ms | 44.34 s | 92.89 s | 15.52% | 0 |
| c4 | 0.3467 tok/s | 231.27 s | 267.41 ms | 134.43 s | 93.32 s | 15.51% | 0 |

Relative to c1:

```text
c2:
  throughput +0.99%
  TTFT       1.49x
  TPOT       17.79x

c4:
  throughput +1.52%
  TTFT       2.48x
  TPOT       26.15x
```

Queue-accounting closure:

\[
Q_{\rm closure}(c)
=
\frac{Queue(c)-Queue(c1)}
{TTFT(c)-TTFT(c1)}
\]

TP4:

```text
c2 ~96.4%
c4 ~97.5%
```

TP8 independently shows approximately:

```text
c2 ~95.7%
c4 ~97.2%
```

That independent TP4/TP8 replication is important.

## Interpretation

Two distinct failure modes are visible:

```text
TTFT degradation ≈ queue residence
TPOT degradation  = in-service batching/interference after admission
```

Meanwhile:
- KV remains only ~15% utilized;
- no preemptions occur;
- prefill execution itself remains around ~93 s on TP4.

So OOM/KV/preemption are **late or misleading capacity signals** for this regime.

## Required visual

### “Concurrency Dividend — Capacity Gain vs User-Latency Tax”

Recommended scatter/bubble plot:

- X = TTFT multiplier vs c1
- Y = output-throughput multiplier vs c1
- bubble size = queue seconds
- label = c1 / c2 / c4
- separate series = TP4 and TP8

Annotate TP4 c4:

```text
+1.5% throughput
2.48x TTFT
26.1x TPOT
134 s queue
KV only 15.5%
```

Add a secondary thin bar:

```text
Added TTFT explained by queue:
TP4 c2 96.4%
TP4 c4 97.5%
TP8 c2 95.7%
TP8 c4 97.2%
```

## Source artifacts

Canonical summary:

```text
results/real_data/final_validation/combined_vllm_runs.csv
```

Rows:

```text
case=tp4_1m_concurrency_extension
bench=1m_c1 / 1m_c2 / 1m_c4

case=tp8_1m_concurrency_extension
bench=1m_c1 / 1m_c2 / 1m_c4
```

Raw cases:

```text
results/real_data/vllm_single_node_v8_1m_extensions/tp4_1m_concurrency_extension/
results/real_data/vllm_single_node_v8_1m_extensions/tp8_1m_concurrency_extension/
```

Per run:

```text
1m_c1/1m_c1.json
1m_c2/1m_c2.json
1m_c4/1m_c4.json
METRICS_COMMAND.txt
COMMAND.txt
warmup_manifest.json
```

## Evidence class

```text
TTFT/TPOT/throughput/queue/KV/preemption: MEASURED
queue closure ratio: DERIVED
admission recommendation: DERIVED from defined SLO, not universal
```

---

# TOP 4 — Prefix Reuse Changes the Scaling Law

## Executive message

> **Prefix caching does not merely lower latency; in the measured 128K→1M range it changes the repeat-request scaling from super-linear to approximately linear.**

## Real hit-conditioned data

| Context | Cold/first TTFT | Repeat-hit median | Speedup |
|---|---:|---:|---:|
| ~128K | 4.897 s | 0.331 s | **14.8×** |
| ~512K | 32.576 s | 1.168 s | **27.9×** |
| 1M | 94.227 s | 2.614 s | **36.0×** |

Fit:

\[
TTFT\propto N^p
\]

Measured three-point empirical exponents:

```text
cold: p = 1.443, log-fit R² ~0.998
warm: p = 1.001, log-fit R² ~0.994
```

Do not call these universal algorithmic complexity exponents; call them **empirical deployment scaling exponents over the measured range**.

Important: the current dashboard's “48.2% reduction” is based on a mixed mean and understates the actual prefix-hit conditioned behavior.

## Required visual

### “Prefix Reuse Changes the Curve”

Log-log line:
- cold/first request
- warm repeat-hit median

Show:

```text
cold p≈1.44
warm p≈1.00
1M: 94.2s -> 2.61s
```

Optional mini-card:
- prefix hits delta
- prefix queries delta
- hit/query ratio

## Source artifacts

Canonical:

```text
results/real_data/final_validation/combined_vllm_runs.csv
```

Rows:

```text
case=tp4_prefix128k
case=tp4_prefix512k
case=tp4_prefix1m
```

Raw:

```text
results/real_data/vllm_single_node_v6_matrix/tp4_prefix128k/prefix128k/prefix128k.json
results/real_data/vllm_single_node_v6_matrix/tp4_prefix512k/prefix512k/prefix512k.json
results/real_data/vllm_single_node_v8_1m_extensions/tp4_prefix1m/prefix1m/prefix1m.json
```

Also retain:
- `case_manifest.json`
- `warmup_manifest.json`
- `METRICS_COMMAND.txt`

## Evidence class

```text
cold/repeat request latency: MEASURED
power-law exponents: DERIVED
universal complexity claim: NOT ALLOWED
```

---

# TOP 5 — Prompt-Token Admission Law

## Executive message

> **Requests/sec hides the real prefill pressure. Across the measured 8K and 128K open-loop sweeps, high-load accepted capacity is much more stable when expressed as input tokens/sec.**

## Real high-load plateaus

Use median request throughput for the measured 1.00x / 1.10x / 1.25x region.

8K:

```text
median accepted request rate ~3.3586 req/s
3.3586 * 8192 ~= 27.5K input tok/s
```

128K:

```text
median accepted request rate ~0.18457 req/s
0.18457 * 131072 ~= 24.2K input tok/s
```

Prompt is 16× longer but normalized token ingress remains within roughly 14%.

Define:

\[
\lambda_{\rm prompt}
=
RPS_{\rm accepted}\times N_{\rm input}
\]

For this TP4/PP1 campaign, show an empirical high-load band:

```text
~24–28K input tokens/s
```

Only for the two measured open-loop contexts.

Do not extrapolate this as a universal 512K/1M capacity law without those open-loop sweeps.

## Required visual

### “Prompt-Token Admission Budget”

Two-part visual:

1. bars for accepted **requests/s**:
   - 8K
   - 128K

2. below, normalized bars for **input tokens/s**.

The top chart should look radically different; the normalized chart should converge.

Simple annotation:

> 16× prompt length → ~18× lower RPS, but only ~14% difference in accepted prompt-token rate.

## Source artifacts

Canonical:

```text
results/real_data/final_validation/combined_vllm_runs.csv
```

Rows:

```text
case=tp4_openloop_8192
bench=rps_0.25x ... rps_1.25x

case=tp4_openloop_131072
bench=rps_0.25x ... rps_1.25x
```

Raw:

```text
results/real_data/vllm_open_loop/tp4_openloop_8192/
results/real_data/vllm_open_loop/tp4_openloop_131072/
```

## Evidence class

```text
request rates: MEASURED
input-tokens/s normalization: DERIVED
24–28K region: measured-context empirical band, not universal
```

---

# TOP 6 — Parallelism Directional Elasticity + GPU-Second Pareto Frontier

## Executive message

> **The question is not “more GPUs or fewer GPUs?” It is “where should the next GPUs go?” For long context, doubling PP is far more effective than doubling TP in this campaign.**

This card should combine two related deployment economics views.

---

## Part A — Directional scaling elasticity

Define:

\[
\eta=
\frac{\log(\text{TTFT speedup})}
{\log(\text{GPU multiplier})}
\]

For a 2× GPU increase:
- `eta = 1` is ideal linear speedup;
- `eta = 0` gives no latency benefit;
- `eta < 0` means more GPUs made latency worse.

### Double TP: TP4/PP1 -> TP8/PP1

| Context | Speedup | Elasticity |
|---|---:|---:|
| 8K | 0.844× | **−0.245** |
| 128K | 0.942× | **−0.086** |
| 512K | 1.136× | **+0.184** |
| 1M | 1.249× | **+0.320** |

### Double PP: TP4/PP2 -> TP4/PP4

| Context | Speedup | Elasticity |
|---|---:|---:|
| 128K | 1.548× | **0.631** |
| 512K | 1.756× | **0.812** |
| 1M | 1.839× | **0.879** |

Non-obvious conclusion:

> **PP scaling efficiency improves as context grows, while TP scaling is negative at short context and still substantially sub-linear at 1M.**

This connects directly to Top #1's context-regime shift.

---

## Part B — GPU-second Pareto frontier

Define a reservation/occupancy proxy:

\[
C_{\rm GPU}=N_{\rm GPU}\times TTFT
\]

This is:
- not energy;
- not cloud cost;
- not utilization weighted.

It is a simple **GPU-seconds per request** occupancy proxy.

### 1M

| Configuration | TTFT | GPUs | GPU-s |
|---|---:|---:|---:|
| TP4/PP1 | 93.25 s | 4 | **373** |
| TP4/PP2 | 52.53 s | 8 | **420** |
| TP4/PP4 | 28.57 s | 16 | **457** |
| TP8/PP1 | 74.69 s | 8 | 598 |
| TP8/PP2 | 41.51 s | 16 | 664 |
| TP16/PP1 | 68.20 s | 16 | **1091** |

At 128K, 512K and 1M, the latency/resource Pareto frontier is consistently:

```text
TP4/PP1 -> TP4/PP2 -> TP4/PP4
```

TP8/PP1, TP8/PP2 and TP16/PP1 are dominated by another measured point on both TTFT and GPU-second proxy in these matched c1 comparisons.

## Required visual

### “Where Should the Next GPUs Go?”

Main:
- X = GPU-seconds/request
- Y = TTFT
- points = topology
- connect Pareto frontier

Inset:
- grouped bars of directional elasticity:
  - TP doubling
  - PP doubling
  across context.

## Source artifacts

```text
results/real_data/final_validation/combined_vllm_runs.csv
```

Rows:

Single node:

```text
case=tp4_context_baseline
case=tp8_context_baseline
```

Scale-out:

```text
case=tp4_pp2_dist
case=tp4_pp4_dist
case=tp8_pp2_dist
case=tp16_pp1_dist
network_mode=native
```

## Evidence class

```text
TTFT / topology / GPU count: MEASURED
GPU-seconds and elasticity: DERIVED
financial cost or energy: NOT CLAIMED
```

---

# TOP 7 — TP Decode Causal Chain: Microbenchmark -> PT Profiler -> Nsight -> TPOT

## Executive message

> **TP8 decode is slower for a reason that appears independently at four layers: small-message NCCL, framework profiler, GPU kernel profile, and user-visible TPOT.**

This is a rare cross-tool causal triangulation and should be visually presented as an evidence chain.

## Layer A — NCCL primitive

Small AllReduce TP8 / TP4 latency ratio:

```text
16 KiB  ~1.9–2.0x
128 KiB ~1.9x
512 KiB ~2.1x
```

Representative processed points:
- TP4 16K ~19 μs
- TP8 16K ~37 μs

At large messages, TP4 and TP8 **bus bandwidth converges much more closely**, showing that decode-size synchronization is a different regime from large prefill payloads.

## Layer B — PyTorch Profiler

TP4 rank-local profile:

```text
ncclDevKernel_AllReduce...
Self CUDA: 251.529 ms
Self CUDA %: 32.14%
Calls: 7040
```

TP8:

```text
Self CUDA: 583.866 ms
Self CUDA %: 55.41%
Calls: 7040
```

Same call count; TP8 consumes:

\[
583.866 / 251.529 \approx 2.32\times
\]

more rank-local AllReduce CUDA time.

This is much stronger than saying TP8 runs “more operations.”

## Layer C — Nsight

Single-node decode profiles independently show NCCL as the dominant aggregate GPU-work category.

Do not label aggregate Nsight kernel percentage as exclusive wall-clock critical-path percentage.

## Layer D — E2E

Matched 8K c1 context baseline:

```text
TP4/PP1 TPOT ~4.475 ms
TP8/PP1 TPOT ~6.350 ms
```

TP8 user-visible TPOT is roughly **42% worse**.

## Required visual

### “TP Decode Evidence Chain”

Horizontal causal chain:

```text
NCCL MICROBENCH
~2x small-message latency
       ->
PT PROFILER
same 7040 AR calls, 2.32x CUDA time
       ->
NSIGHT
NCCL dominates decode GPU work
       ->
VLLM E2E
TP8 TPOT ~42% worse
```

Each node should be clickable.

This is a better visual than another kernel pie chart.

## Source artifacts

NCCL:

```text
results/real_data/hardware_processed/nccl_points.csv
```

PT profiler:

```text
results/real_data/profiles_torch_single_node/tp4_8k_decode/torch/profiler_out_0.txt
results/real_data/profiles_torch_single_node/tp8_8k_decode/torch/profiler_out_0.txt
```

Also allow drill-down to all rank outputs.

Nsight:

```text
results/real_data/profiles_single_node/tp4_decode/cuda_gpu_kern_sum.csv
results/real_data/profiles_single_node/tp8_decode/cuda_gpu_kern_sum.csv
results/real_data/profiles_single_node/PROFILE_ANALYSIS.json
```

E2E:

```text
results/real_data/final_validation/combined_vllm_runs.csv

case=tp4_context_baseline, bench=8k_c1
case=tp8_context_baseline, bench=8k_c1
```

## Evidence class

```text
four endpoints: MEASURED
wider-TP synchronization as contributor: CROSS-VALIDATED
exact exclusive critical-path fraction: UNRESOLVED
```

---

# TOP 8 — Runtime Knob Derivative Fingerprint

## Executive message

> **Not every runtime knob deserves optimization effort. `max_num_seqs` is almost completely non-binding in the measured long-context c4 regime, while chunk/token budget materially changes TTFT.**

## max_num_seqs experiment

### 1M c4

```text
max_num_seqs: 4 / 8 / 16

TTFT:
232.342 s
232.364 s
232.250 s

TPOT:
267.532 ms
267.451 ms
267.480 ms

peak_running = 2 for all three
peak_waiting = 3 for all three
```

TTFT total spread is only ~0.05%.

512K c4 shows the same behavior.

Interpretation:

> The configured `max_num_seqs` value is not the binding limit in this measured state because the active runtime never reaches those configured ceilings.

## Chunk budget experiment

TP4 c1 TTFT:

### 128K

```text
4K chunk  : 5.228 s
8K chunk  : 4.534 s
16K chunk : 4.364 s
```

### 512K

```text
4K  : 40.271 s
8K  : 31.936 s
16K : 30.455 s
```

### 1M

```text
4K  : 122.049 s
8K  : 93.277 s
16K : 88.951 s
```

At 1M, 4K -> 16K improves TTFT by ~27%.

Do not call 16K universally optimal because fairness/decode-interference objectives require their own matched measurement.

## Required visual

### “Knob Sensitivity Fingerprint”

Horizontal sensitivity bars:

```text
Topology TP/PP      VERY HIGH
Prefix reuse        VERY HIGH
Chunk/token budget  HIGH
Network bandwidth   HIGH but topology-dependent
max_num_seqs        ~ZERO in tested long-context c4 regime
```

Then a small two-panel evidence inset:
- flat max_num_seqs line
- strong chunk TTFT slope

## Source artifacts

Canonical:

```text
results/real_data/final_validation/combined_vllm_runs.csv
```

Raw chunk cases:

```text
results/real_data/vllm_single_node_v6_matrix/tp4_chunk4k/
results/real_data/vllm_single_node_v6_matrix/tp4_chunk8k/
results/real_data/vllm_single_node_v6_matrix/tp4_chunk16k/
```

Raw maxseq cases are referenced through the canonical combined file and their case manifests/results in the single-node matrices/extensions.

Relevant cases:

```text
tp4_512k_maxseq4
tp4_512k_maxseq8
tp4_512k_maxseq16

tp4_1m_maxseq4
tp4_1m_maxseq8
tp4_1m_maxseq16
```

## Evidence class

```text
A/B measurements: MEASURED
sensitivity ranking: DERIVED
universal scheduler setting: NOT CLAIMED
```

---

# TOP 9 — Busy GPU != Efficient Serving

## Executive message

> **The topology with the highest GPU-utilization telemetry can deliver much worse TTFT. Communication kernels count as GPU activity too; utilization alone is not productive-work efficiency.**

## Real Native examples

### 128K

TP4/PP4:

```text
TTFT ~1.710 s
mean GPU util across nodes ~35.2%
```

TP16/PP1:

```text
TTFT ~6.420 s
mean GPU util ~63.2%
```

### 1M

TP4/PP4:

```text
TTFT ~28.568 s
mean GPU util ~62.8%
```

TP16/PP1:

```text
TTFT ~68.197 s
mean GPU util ~80.6%
```

Meanwhile Top #2 shows TP16 is far more bandwidth-sensitive.

The point is not that utilization is “bad”; the point is that **utilization is semantically incomplete**.

It means the GPU is running kernels, not that those kernels produce proportionally useful tokens.

## Required visual

### “Busy != Efficient”

Scatter:
- X = mean GPU utilization %
- Y = TTFT
- point = topology
- optional point outline / annotation = bandwidth sensitivity

Do not use a fitted regression line as a causal claim; there are only four topology points per context.

Use the visual to show the inversion qualitatively.

Add a simple card:

```text
TP16/PP1 @ 1M
80.6% util
68.2 s TTFT

TP4/PP4 @ 1M
62.8% util
28.6 s TTFT
```

## Source artifacts

```text
results/real_data/final_validation/combined_vllm_runs.csv
```

Columns:

```text
gpu_node_stats_json
mean_ttft_ms
case
network_mode
requested_input_tokens
```

For each node inside `gpu_node_stats_json`, use:

```text
gpu_util_mean_pct
gpu_util_peak_pct
gpu_mem_used_peak_mb
gpu_power_mean_w
```

Use `gpu_util_mean_pct`, not `gpu_util_peak_pct=100`, for this plot.

Cross-check with:

```text
results/real_data/profiles_multi_node_native/
results/real_data/hardware_processed/nccl_points.csv
```

## Evidence class

```text
GPU util and TTFT: MEASURED
“high utilization can be communication-heavy”: CROSS-VALIDATED
causal correlation coefficient: do not promote as causal
```

---

# TOP 10 — KV Headroom != VRAM Headroom

## Executive message

> **Pipeline parallelism drastically lowers the reported KV-cache utilization percentage, but total GPU memory remains ~87–89 GiB. Low KV% is not low VRAM use.**

## Real 1M data

| Configuration | Peak KV usage | Peak GPU memory |
|---|---:|---:|
| TP4/PP1 | 12.29% | ~88.39 GiB |
| TP4/PP2 | 5.91% | ~88.69 GiB |
| TP4/PP4 | **2.75%** | **~88.83 GiB** |
| TP16/PP1 | 12.13% | ~86.71 GiB |

An interesting normalization:

```text
PP * KV%
TP4/PP1 ~12.29
TP4/PP2 ~11.82
TP4/PP4 ~10.99
```

This is consistent with active KV-cache state being distributed across deeper PP stages, while weights/runtime allocations continue to dominate total GPU memory.

Do not overstate this as a proof of the allocator's exact sharding formula.

## Required visual

### “Cache Headroom ≠ VRAM Headroom”

Grouped bars per topology:
- KV-cache usage %
- total GPU memory used GiB

Because these have different units, use either:
- two aligned mini-panels; or
- normalized index view.

Do not put percentage and GiB on an unlabeled shared axis.

The simple surprise should be obvious:

```text
KV usage: 12.3% -> 2.75%
VRAM:     ~88.4 -> ~88.8 GiB
```

## Source artifacts

```text
results/real_data/final_validation/combined_vllm_runs.csv
```

Fields:

```text
peak_kv_usage
gpu_node_stats_json -> gpu_mem_used_peak_mb
```

Rows:

```text
tp4_context_baseline / 1m_c1
tp4_pp2_dist / native / 1m_c1
tp4_pp4_dist / native / 1m_c1
tp16_pp1_dist / native / 1m_c1
```

## Evidence class

```text
KV and GPU memory values: MEASURED
approximate PP-partition interpretation: CROSS-VALIDATED / interpretation
exact allocator/sharding mechanism: do not claim without source/runtime proof
```

---

# 4. How the ten discoveries should appear in the Executive tab

Recommended page order:

## Section A — Campaign status

Keep the existing campaign/evidence KPIs, but status language must be consistent with `FINAL_VALIDATION.json`.

Do not collapse:
- application-run completeness,
- strict validation completeness,
- profiler completeness,
- NCCL policy audit

into one blanket `PASS`.

---

## Section B — “Three Things This Campaign Discovered”

Full-width Top 3:

```text
1. Hybrid-Attention Regime Shift
2. Fabric Exposure Fingerprint
3. Concurrency Value Destruction / Queue Closure
```

These are the narrative headline.

---

## Section C — “What This Means for Deployment”

Use three compact cards:

```text
4. Prefix scaling-law change
5. Prompt-token admission law
6. Parallelism directional elasticity / Pareto frontier
```

These answer:
- can repeated workloads be accelerated?
- how should requests be admitted?
- where should more GPUs go?

---

## Section D — “What the Low-Level Evidence Proves”

Use two cards:

```text
7. TP decode causal chain
8. Runtime knob derivative fingerprint
```

These connect:
- hardware primitive
- profiler evidence
- runtime choice
- E2E behavior.

---

## Section E — “Metrics That Can Mislead You”

Use two compact warning cards:

```text
9. Busy GPU != efficient serving
10. KV headroom != VRAM headroom
```

These are highly useful for production operators.

---

# 5. Evidence drawer / click-through design

Every Executive discovery must expose a small `Evidence` control.

On click, show:

```text
Observation
Formula / derivation
Evidence class
Exact source rows/cases
Raw file paths
Known boundary
Required follow-up
```

Example for Top #3:

```text
Observation:
TP4 1M c1->c4 throughput +1.52%; TTFT 2.48x; TPOT 26.15x.

Derived:
97.5% of added TTFT is numerically explained by queue residence.

Sources:
combined_vllm_runs.csv
case=tp4_1m_concurrency_extension
bench=1m_c1 / c4

Raw:
vllm_single_node_v8_1m_extensions/tp4_1m_concurrency_extension/...

Boundary:
This does not define a universal c1 admission limit; the limit depends on product SLO.
```

---

# 6. Mandatory implementation rules

## Rule 1 — no hand-maintained performance arrays

The current HTML contains multiple hard-coded Chart.js arrays that have drifted from the canonical result tables.

For these Top-10 charts:

```text
normalized source data -> calculation function -> chart
```

not:

```text
manually typed chart array
```

Recommended build flow:

```text
FINAL_VALIDATION
      |
combined_vllm_runs
      |
hardware summaries + profile validation
      |
normalized discovery dataset
      |
Executive charts
```

---

## Rule 2 — preserve denominator semantics

Do not mix:

```text
aggregate GPU kernel-time %
wall-clock %
CUDA API %
request latency %
GPU utilization %
```

in one stacked “100%” chart.

Nsight aggregate kernel work can exceed or overlap wall-clock because different devices/streams execute concurrently.

---

## Rule 3 — source every derived number

Every derived discovery should have a structured record such as:

```json
{
  "discovery_id": "fabric_exposure",
  "status": "DERIVED",
  "inputs": [
    "hardware_processed/nccl_points.csv",
    "final_validation/combined_vllm_runs.csv",
    "model_validation.json"
  ],
  "formula_version": "v1",
  "fit_quality": 0.9997,
  "boundary": "local sensitivity fit over measured Native/100G/20G points"
}
```

---

## Rule 4 — do not transfer K3 dimensions

The PDFs are references for the performance-accounting method.

The V8 UI must use:

```text
48B run model manifest
```

for all tensor-size/accounting formulas.

---

## Rule 5 — do not convert correlation into unsupported causality

Acceptable:

> Small-message NCCL, PT profiler, Nsight and E2E TPOT independently support wider-TP synchronization as a contributor.

Not acceptable:

> 42% of TP8 TPOT is caused by NCCL.

The current traces do not provide that exclusive wall-clock causal percentage.

---

## Rule 6 — distinguish configured network cap from achieved bandwidth

UI labels should be:

```text
Configured cap: 100G
Measured iperf: ~54–57 Gb/s
Measured 256M NCCL SendRecv: ~5.5 GB/s
```

rather than simply:

```text
100G
```

---

# 7. Corrections required before adding the Top 10

The Executive discoveries should not sit on top of contradictory existing cards.

At minimum correct:

### Existing 1M concurrency guidance
Remove:
```text
TP4/PP4 c<=2
zero queue at c<=2
queue knee at c4
```

The measured c1/c2/c4 concurrency campaign is single-node TP4/PP1 and TP8/PP1, and c2 already has major queue/TPOT degradation.

### Existing bandwidth-cap language
Do not state:
```text
bandwidth sensitivity NOT MEASURED
```

Application Native/100G/20G sensitivity exists, while hardware primitives also include 50G/10G.

### Existing profiler “critical path” percentages
Do not present:
```text
54% compute + 46% NCCL = complete wall-clock prefill attribution
residual = 0%
```

unless a timeline-exclusive analysis proves those exact wall-clock shares.

### Existing prefix statement
Do not use the mixed mean `93.39 -> 48.35 s` as the “warm prefix hit”.

Use the hit-conditioned first/repeat values from the prefix experiment.

---

# 8. Suggested Executive card titles and copy

Use language that can be understood in 5–10 seconds.

## Top 1
**Long Context Changes the Bottleneck**

> Attention work scales ~N² in the measured profiles; KDA/MoE stay ~N. Optimization priority therefore changes as context grows.

## Top 2
**Topology Changes Fabric Exposure by ~100×**

> TP16 TTFT tracks the measured NCCL transport curve with ~116 hidden-width-equivalent exposed bytes/token; TP4/PP4 is ~1 or less.

## Top 3
**Concurrency Can Destroy Latency Without Adding Capacity**

> At 1M TP4 c4: +1.5% throughput, 2.48× TTFT, 26× TPOT, 134 s queue — while KV is only 15.5%.

## Top 4
**Prefix Reuse Changes the Scaling Curve**

> Cold TTFT scales ~N^1.44; repeat-hit TTFT ~N^1.00 over measured 128K–1M.

## Top 5
**Admission Should Count Prompt Tokens, Not Just Requests**

> 8K and 128K high-load RPS differ dramatically, but accepted prompt-token rates converge around ~24–28K tok/s.

## Top 6
**Put the Next GPUs in the Right Dimension**

> PP scaling efficiency rises toward ~0.88 at 1M; doubling TP reaches only ~0.32 and hurts at short context.

## Top 7
**The TP Decode Penalty Appears at Four Independent Layers**

> NCCL microbench → PT Profiler → Nsight → E2E TPOT all show the same wider-TP synchronization penalty.

## Top 8
**Some Knobs Are Almost Dead**

> Changing max_num_seqs 4→16 moves 1M c4 TTFT by only ~0.05%; chunk budget changes 1M c1 TTFT by ~27%.

## Top 9
**Busy GPU Does Not Mean Efficient Serving**

> TP16 uses more GPU activity but produces much worse TTFT and much higher fabric sensitivity than TP4/PP4.

## Top 10
**KV Headroom Is Not VRAM Headroom**

> TP4/PP4 uses only 2.75% of its KV pool at 1M, yet total GPU memory remains ~88.8 GiB.

---

# 9. Data-quality / confidence badges

Recommended badges:

```text
MEASURED
CROSS-VALIDATED
DERIVED
UNRESOLVED
```

For the Top 10:

| Discovery | Badge |
|---|---|
| #1 Hybrid scaling | `MEASURED + DERIVED` |
| #2 Fabric exposure | `CROSS-VALIDATED + DERIVED` |
| #3 Queue closure | `CROSS-VALIDATED + DERIVED` |
| #4 Prefix scaling | `MEASURED + DERIVED` |
| #5 Prompt-token law | `DERIVED FROM MEASURED` |
| #6 Parallelism elasticity | `DERIVED FROM MEASURED` |
| #7 TP decode chain | `CROSS-VALIDATED` |
| #8 Knob derivatives | `MEASURED + DERIVED` |
| #9 Busy != efficient | `CROSS-VALIDATED` |
| #10 KV != VRAM | `CROSS-VALIDATED` |

---

# 10. Acceptance criteria for the team

A Top-10 Executive implementation is ready only if all of the following are true:

- [ ] All ten discoveries are computed from `results_V8_runs.zip` artifacts.
- [ ] No K3 model dimensions are used for the 48B numerical formulas.
- [ ] Every chart can resolve to exact run/profile IDs.
- [ ] Every derived value displays its evidence class.
- [ ] Network visuals show **measured achieved bandwidth**, not only configured cap.
- [ ] Profiler aggregate GPU-work percentages are not called wall-clock critical path.
- [ ] TP4/PP4 is never called a universal winner.
- [ ] `c<=2 safe` is removed unless an explicit product SLO proves it.
- [ ] Prefix-hit latency uses first/repeat metrics, not mixed mean.
- [ ] `max_num_seqs` and chunk-size experiments remain separately identified.
- [ ] GPU-utilization plots use `gpu_util_mean_pct`, not peak=100%.
- [ ] KV-cache usage is not equated with total GPU memory utilization.
- [ ] Fit/regression quality (`R²`, input points, formula version) is visible in the evidence drawer.
- [ ] Missing evidence is `UNRESOLVED`, never zero.
- [ ] Existing technical tabs remain available as drill-down views.
- [ ] Existing Evidence tab remains the canonical row-level audit surface.

---

# 11. Recommended normalized discovery data object

Instead of hard-coding these values in HTML, generate one build artifact:

```text
results/real_data/final_validation/EXECUTIVE_DISCOVERIES.json
```

Suggested structure:

```json
{
  "campaign_id": "20260921_195656",
  "model": {
    "source": "results/real_data/model_validation.json"
  },
  "discoveries": [
    {
      "id": "hybrid_attention_regime_shift",
      "evidence_class": ["MEASURED", "DERIVED"],
      "source_paths": [],
      "formula": "log-growth exponent",
      "values": {},
      "boundaries": []
    }
  ]
}
```

The dashboard should render from this generated object.

The computation script should be version-controlled so a future rerun regenerates the Top-10 findings automatically.

---

# 12. Final message the Executive tab should communicate

The page should leave an experienced LLM-serving engineer with the following understanding:

> **This model does not merely become slower with longer context; its bottleneck regime changes. The usefulness of TP versus PP changes with context, fabric exposure differs by orders of magnitude between topologies, queueing can destroy user latency while KV and preemption still look healthy, and standard metrics such as GPU utilization or KV% can point an operator in the wrong direction. The conclusions are not based on one profiler trace: they are cross-correlated across hardware smoke tests, NCCL microbenchmarks, vLLM end-to-end runs, scheduler telemetry, Nsight and PyTorch Profiler.**

That is the intended difference between a benchmark dashboard and a **deep-characterization / deployment decision system**.
