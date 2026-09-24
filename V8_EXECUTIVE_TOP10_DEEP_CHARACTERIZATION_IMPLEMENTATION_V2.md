# V8-FULL Dashboard — Executive Deep-Characterization Top 10 Implementation Spec V2

**Target UI:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_23rdSept_9pmIST.html`  
**Model under test:** `moonshotai/Kimi-Linear-48B-A3B-Instruct` BF16 surrogate  
**Primary empirical evidence:** `results_V8_runs.zip`  
**V2 basis:** raw campaign artifacts + `V8_V4_23SEP_9PM_CLOSURE_AUDIT.md` + `V8_Dashboard_realrun_v4_new_latest_RAW_DATA_DEEP_AUDIT.md` + the V1 Top-10 implementation spec  
**Purpose:** turn the Executive tab into a defensible deployment-decision surface that explains **WHAT happened, WHERE it happened, WHY the evidence supports the interpretation, WHAT DECISION changes, and WHAT remains unresolved**.

---

## 0. V2 executive decision

The V1 Top-10 framework is retained. The underlying campaign is rich enough to support all ten discoveries, but several claims need tighter scope, terminology, provenance, and confidence boundaries.

### V2 disposition

| # | Discovery | V2 action | Evidence confidence | Causal confidence |
|---:|---|---|---|---|
| 1 | Hybrid-Attention Resource-Pressure Regime Shift | **REFINE** | HIGH | MEDIUM |
| 2 | Fabric Exposure Fingerprint | **KEEP / STRENGTHEN** | HIGH | MEDIUM-HIGH |
| 3 | Concurrency Value Destruction + Queue Accounting Closure | **KEEP / STRENGTHEN** | HIGH | HIGH for added-TTFT queue closure; MEDIUM for TPOT mechanism |
| 4 | Prefix Reuse Changes the Measured Scaling Curve | **KEEP / REFINE** | HIGH | MEDIUM-HIGH |
| 5 | Prompt-Token Admission Fingerprint | **RENAME / REFINE** | MEDIUM | LOW-MEDIUM |
| 6 | Parallelism Directional Elasticity + GPU-Second Frontier | **KEEP / CORRECT** | HIGH | MEDIUM |
| 7 | TP Decode Evidence Chain | **KEEP / STRENGTHEN** | HIGH | MEDIUM-HIGH |
| 8 | Runtime-Knob Derivative Fingerprint | **KEEP / SCOPE** | HIGH | MEDIUM-HIGH |
| 9 | Busy GPU != Efficient Serving | **KEEP** | HIGH | MEDIUM |
| 10 | KV Headroom != VRAM Headroom | **KEEP / TIGHTEN** | HIGH | LOW-MEDIUM for allocator interpretation |

**No Top-10 discovery is removed.** The main V2 change is that each claim must separate measurement from interpretation and must state the deployment decision it changes.

---

# 1. Non-negotiable evidence contract

## 1.1 Canonical source hierarchy

For campaign state and end-to-end serving metrics, use this order:

```text
results/real_data/final_validation/FINAL_VALIDATION.json
results/real_data/final_validation/coverage.json
results/real_data/final_validation/combined_vllm_runs.csv
results/real_data/final_validation/combined_vllm_runs.json
results/real_data/final_validation/NCCL_POLICY_AUDIT.json
results/real_data/final_validation/SCALEOUT_TELEMETRY_AUDIT.json
results/real_data/final_validation/SCALEOUT_NETWORK_COVERAGE.md
```

For model identity:

```text
results/real_data/model_validation.json
```

For hardware/fabric primitives:

```text
results/real_data/hardware_processed/iperf.csv
results/real_data/hardware_processed/nccl_points.csv
results/real_data/hardware_processed/nvbandwidth_metrics.csv
results/real_data/hardware_processed/babelstream.csv
results/real_data/hardware_processed/summary.json
```

For profile-specific conclusions, use only the exact raw profile artifacts for that profile and require a complete profile validation state.

## 1.2 Evidence classes

```text
MEASURED
  Direct field or raw measurement from the campaign.

CROSS-VALIDATED
  Same direction/mechanism independently visible in another evidence layer.

DERIVED
  Deterministic arithmetic, normalization, regression, or fit from MEASURED values.

MODELED
  Interpolation/extrapolation or assumed mapping beyond directly measured points.

UNRESOLVED
  Available evidence cannot defensibly establish the claim.
```

Never render `DERIVED`, `MODELED`, or profiler aggregates as `DIRECT_MEASURED`.

## 1.3 Two confidence dimensions

Every discovery card must show both:

```text
Evidence confidence
  How strongly/reproducibly the observed effect is measured.

Causal confidence
  How strongly the available evidence establishes why the effect occurred.
```

This prevents a strong measurement from being mistaken for an equally strong causal explanation.

---

# 2. Canonical campaign identity locked for V2

## Model identity

From `results/real_data/model_validation.json`:

```text
model                 = moonshotai/Kimi-Linear-48B-A3B-Instruct
resolved revision     = e1df551a447157d4658b573f9a695d57658590e9
checkpoint dtype      = bfloat16
hidden size           = 2304
hidden layers         = 27
KDA layers            = 20
full-attention layers = 7
experts                = 256
experts/token          = 8
model max length       = 1,048,576
```

**Guardrail:** never transfer Kimi K3 dimensions into this 48B surrogate analysis.

## Hardware identity

Raw preflight inventory on both nodes reports:

```text
NVIDIA RTX PRO 6000 Blackwell Server Edition
97,887 MiB reported device memory per GPU
8 GPUs per node
```

The README text that says `RTX 6000 Ada` is stale metadata and must not be treated as hardware truth.

## Campaign status

From `FINAL_VALIDATION.json`:

```text
configured rows                         126
completed application rows             119
NOT_RUN                                  7
failed                                   0
native/local completed application rows 95
auxiliary capped application rows       24
expected distributed profiles           22
complete distributed profiles           14
profiles_all_complete                 false
nccl_policy_ok                        false
strict_full_coverage                  false
full_suite_valid                      false
```

Executive status wording should be:

> **E2E RUN MATRIX VALIDATED · STRICT SUITE SIGN-OFF INCOMPLETE**

Do not collapse application completion, profile completeness, NCCL policy completeness, and strict publication sign-off into one PASS badge.

---

# 3. Executive information architecture

The Executive tab should not begin with generic profiler charts. It should answer the expensive deployment questions first.

## First screen — three hero discoveries

Render in this order:

1. **Fabric Exposure Fingerprint** — topology/network risk
2. **Concurrency Value Destruction** — admission/SLO risk
3. **Long-Context Resource-Pressure Regime Shift** — optimization priority changes with context

The stable discovery IDs can remain `#2`, `#3`, `#1` to preserve implementation lineage.

Each hero must include:

```text
WHAT happened
WHERE / under which workload
WHY the evidence supports the interpretation
DECISION CHANGED
Evidence confidence
Causal confidence
Boundary / what is not proven
Evidence drill-down
```

## Second section — deployment levers

```text
#4 Prefix reuse
#5 Prompt-token admission fingerprint
#6 Parallelism elasticity + GPU-second frontier
```

## Third section — low-level corroboration

```text
#7 TP decode evidence chain
#8 Runtime-knob derivative fingerprint
```

## Fourth section — misleading operational metrics

```text
#9 Busy GPU != efficient serving
#10 KV headroom != VRAM headroom
```

---

# 4. TOP 1 — Hybrid-Attention Resource-Pressure Regime Shift

## Executive message

> **Long context changes which subsystem accumulates GPU work fastest: in matched TP4/PP4 profiles, full-attention work grows close to N² from 128K to 512K while KDA and MoE remain approximately N¹.**

Do **not** write:

> “Attention becomes the wall-clock critical path at ~420K.”

The available profile summaries establish aggregate GPU-work scaling, not exclusive wall-clock critical-path attribution.

## Why this matters to an LLM/GPU architect

A single profile percentage answers “what was active in this trace?” This scaling fingerprint answers a more useful deployment question:

> **Which optimization class gains pressure as context grows?**

That helps decide whether further optimization effort should target attention kernels, communication, MoE/GEMM, or scheduler/runtime behavior.

## Measured/derived reference

Matched valid TP4/PP4 distributed prefill profiles:

```text
128K: profiles_multi_node_native/tp4_pp4_dist/prefill_128k/
512K: profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/
```

V1/raw-audit reference grouping produced approximately:

| Component | 128K aggregate work | 512K aggregate work | Growth | Resource-pressure exponent |
|---|---:|---:|---:|---:|
| Full attention | ~0.30 s | ~4.7–4.8 s | ~15.7× | ~1.99 |
| KDA | ~0.04–0.05 s | ~0.16–0.18 s | ~3.9× | ~0.99 |
| MoE | ~0.17 s | ~0.65 s | ~3.8× | ~0.96 |
| NCCL | ~1.63 s | ~3.56 s | ~2.18× | ~0.56 |
| GEMM family | ~0.10 s | ~0.50 s | ~5.25× | ~1.20 |

**V2 implementation requirement:** these rounded values must be regenerated from every valid per-rank `cuda_gpu_kern_sum.csv` using one versioned grouping function. Do not copy the table into frontend arrays.

Formula:

```text
p_k = ln[W_k(512K) / W_k(128K)] / ln(512K / 128K)
```

where `W_k` is the documented aggregation statistic, recommended as **median per-rank aggregate GPU work**.

## E2E cross-check

Native TP4/PP4 c1 TTFT:

```text
128K = 1.709966 s
512K = 10.221758 s
1M   = 28.567955 s
```

The E2E curve becomes more super-linear between the larger contexts, but that does not by itself establish the exclusive source of the curvature.

## Derived crossover

A two-endpoint interpolation of the grouped resource-pressure curves may place the attention-vs-NCCL crossover around ~420K tokens.

Required badge:

```text
DERIVED / MODELED INTERPOLATION
NOT A MEASURED CRITICAL-PATH CROSSOVER
```

## Decision changed

> **Do not tune long-context performance from a single 128K profile. Re-evaluate the optimization target as context increases because subsystem pressure scales at different rates.**

## Best Executive visual

### Hybrid-Attention Scaling Fingerprint

- X: context tokens, log scale
- Y: median per-rank aggregate GPU kernel work, log scale
- series: Full attention, KDA, MoE, NCCL, GEMM
- label each fitted exponent
- optional dashed resource-pressure crossover only if fit quality and endpoint methodology are visible
- footer: `Aggregate GPU work != exclusive request wall-clock critical path`

## Confidence

```text
Evidence confidence: HIGH for endpoint profile data and architecture manifest.
Causal confidence:   MEDIUM for user-visible bottleneck interpretation.
```

## Evidence

```text
results/real_data/model_validation.json
results/real_data/profiles_multi_node_native/tp4_pp4_dist/prefill_128k/
results/real_data/profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/
results/real_data/final_validation/combined_vllm_runs.csv
```

---

# 5. TOP 2 — Fabric Exposure Fingerprint

## Executive message

> **The same measured fabric constraint has radically different application impact by topology: at 1M, configured-20G changes TP16/PP1 TTFT by ~+276.7%, while TP4/PP4 changes by only ~+3.9%.**

This is the strongest direct hardware-to-application discovery in the campaign.

## Step 1 — separate bandwidth layers

Do not use one number called “network bandwidth.” Show three separate layers:

```text
Configured cap
Measured iperf transport
Measured NCCL SendRecv transport primitive
Application TTFT response
```

Measured campaign network state:

```text
GCP_NATIVE:
  application validation iperf forward ~173.58 Gb/s

GCP_CAPPED_100G:
  configured 100G
  measured application-validation iperf ~56.84 Gb/s

GCP_CAPPED_20G:
  configured 20G
  measured application-validation iperf ~16.48 Gb/s
```

Processed 256-MiB SendRecv bus-bandwidth points:

```text
Native ~7.11 GB/s
100G   ~5.54 GB/s
20G    ~2.04 GB/s
```

Keep message size and `busbw` provenance visible.

## Measured application sensitivity

At 1M c1:

| Topology | Native TTFT | 100G TTFT | 100G delta | 20G TTFT | 20G delta |
|---|---:|---:|---:|---:|---:|
| TP4/PP2 | 52.526 s | 52.600 s | ~+0.14% | 53.127 s | ~+1.14% |
| TP8/PP2 | 41.515 s | 41.462 s | noise-level | 41.472 s | noise-level |
| TP4/PP4 | 28.568 s | 28.866 s | ~+1.04% | 29.684 s | ~+3.91% |
| TP16/PP1 | 68.197 s | 92.992 s | ~+36.36% | 256.889 s | ~+276.7% |

This table alone is already an Executive-level deployment finding.

## Derived transport-response fingerprint

V1 proposed a local fit:

```text
TTFT(B) = T0 + V_exposed / B
```

using measured Native / configured-100G / configured-20G points and the measured 256-MiB NCCL SendRecv bandwidth.

For TP16/PP1, prior raw analysis found approximately stable fitted exposure across 128K→1M, equivalent to roughly ~116 hidden-width-equivalent bytes/token when normalized by:

```text
E_H = V_exposed / (N_tokens * H * b)
H = 2304
b = 2 bytes for BF16
```

**Interpretation boundary:**

> This is a local empirical sensitivity coefficient over the measured bandwidth range. It is **not** a literal claim that the model physically transmits exactly 116 hidden states per token.

## Decision changed

> **Do not provision distributed inference from NIC/iperf capability alone. Topology determines how much transport degradation becomes exposed to user-visible TTFT.**

## Best Executive visual

### Fabric Exposure Fingerprint

Primary:
- X: topology
- Y: TTFT delta vs Native under measured 100G/20G conditions
- contexts toggle: 128K / 512K / 1M

Secondary/inset:
- measured iperf -> measured 256M SendRecv -> application TTFT

Optional advanced drawer:
- fitted `V_exposed`
- hidden-width-equivalent normalization
- R² and exact three fit points

## Confidence

```text
Evidence confidence: HIGH for network and application points.
Causal confidence:   MEDIUM-HIGH that exposed communication explains TP16 sensitivity;
                     lower for any literal transfer-count interpretation.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
results/real_data/final_validation/SCALEOUT_NETWORK_COVERAGE.md
results/real_data/hardware_processed/iperf.csv
results/real_data/hardware_processed/nccl_points.csv
results/real_data/model_validation.json
results/real_data/vllm_scaleout_network_matrix/*/network_validation/
```

---

# 6. TOP 3 — Concurrency Value Destruction + Queue Accounting Closure

## Executive message

> **At 1M, added concurrency buys almost no output throughput but destroys user latency. On TP4, c4 adds only ~1.52% output throughput while TTFT becomes 2.48×, TPOT 26.15×, and mean queue residence reaches ~134.43 s.**

## TP4/PP1 measured 1M results

| Load | Output TPS | TTFT | TPOT | Queue mean | Peak KV | Preemptions |
|---|---:|---:|---:|---:|---:|---:|
| c1 | 0.34147 | 93.395 s | 10.228 ms | ~0 s | 12.290% | 0 |
| c2 | 0.34486 | 139.374 s | 181.974 ms | 44.340 s | 15.517% | 0 |
| c4 | 0.34666 | 231.268 s | 267.411 ms | 134.428 s | 15.511% | 0 |

Relative to c1:

```text
TP4 c2:
  output TPS +0.99%
  TTFT       1.49x
  TPOT       17.79x

TP4 c4:
  output TPS +1.52%
  TTFT       2.48x
  TPOT       26.15x
```

## Queue-accounting closure

```text
Q_closure(c) = [Queue(c) - Queue(c1)] / [TTFT(c) - TTFT(c1)]
```

Measured/derived:

```text
TP4 c2 ~96.4%
TP4 c4 ~97.5%
TP8 c2 ~95.7%
TP8 c4 ~97.2%
```

The independent TP4 and TP8 replication is important.

## What the data does and does not prove

Strongly supported:

```text
Added TTFT is numerically dominated by queue residence once the 1M concurrency cliff begins.
KV remains far from exhaustion.
Preemptions remain zero.
```

Do not collapse TPOT into the same explanation:

```text
TPOT degradation is an in-service batching/interference effect after admission.
The current evidence does not fully decompose its exclusive root cause.
```

## Decision changed

> **Admission control should be driven by TTFT/TPOT/queue SLOs before KV exhaustion or preemption. “Fits in memory” is not a sufficient capacity criterion.**

Do not write `strict cap c=1` without the product SLO. Correct phrasing:

> `c2 is already inside the measured severe-degradation regime; choose an admission threshold from the required TTFT/TPOT SLO.`

## Best Executive visual

### Concurrency Dividend — Capacity Gain vs Latency Tax

- X: TTFT multiplier vs c1
- Y: output-TPS multiplier vs c1
- bubble size: queue seconds
- label: c1/c2/c4
- series: TP4 and TP8
- small lower bar: queue-accounting closure %

## Confidence

```text
Evidence confidence: HIGH.
Causal confidence:   HIGH for queue contribution to added TTFT;
                     MEDIUM for TPOT root mechanism.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
case=tp4_1m_concurrency_extension
case=tp8_1m_concurrency_extension
results/real_data/vllm_single_node_v8_1m_extensions/
```

---

# 7. TOP 4 — Prefix Reuse Changes the Measured Scaling Curve

## Executive message

> **For repeated-prefix workloads, prefix caching changes the observed 128K→1M repeat-request TTFT curve from strongly super-linear cold behavior to approximately linear over the measured range.**

## Use hit-conditioned fields only

Do not use the mixed `mean_ttft_ms` as “warm-hit latency.”

Canonical first/repeat fields:

| Context case | First/cold TTFT | Repeat-hit median | Speedup | Hits / queries |
|---|---:|---:|---:|---:|
| ~128K | 4.8965 s | 0.3307 s | ~14.8× | 917,504 / 1,050,624 = 87.33% |
| ~512K | 32.5762 s | 1.1679 s | ~27.9× | 1,048,576 / 2,098,177 = 49.98% |
| 1M | 94.2272 s | 2.6140 s | ~36.0× | 1,998,848 / 4,000,000 = 49.97% |

The prefix test case input lengths are not all exactly the simple display label because the repeated-prefix workload includes its own request construction. Display the user-friendly context label but preserve exact requested-input fields in the evidence drawer.

## Derived empirical slopes

Using the three measured prefix cases:

```text
cold/first TTFT exponent  p ~= 1.4427   log-fit R² ~= 0.9979
repeat-hit TTFT exponent p ~= 1.0013   log-fit R² ~= 0.9935
```

These are empirical deployment scaling exponents over the measured range, **not universal algorithmic complexity claims**.

## Decision changed

> **Prefix reuse should be treated as a workload-routing/caching lever: workloads with repeated prefixes can occupy a fundamentally different latency regime than one-off long prompts.**

Do not recommend prefix caching unconditionally. Its value depends on reuse frequency, cache residency, eviction, and workload mix.

## Best Executive visual

### Prefix Reuse Changes the Curve

- log X: input context
- log Y: TTFT
- series: first/cold, repeat-hit median
- show empirical exponents
- annotate `1M: 94.23 s -> 2.61 s`
- evidence drawer includes prefix hit/query counters

## Confidence

```text
Evidence confidence: HIGH for the measured prefix cases.
Causal confidence:   MEDIUM-HIGH that the repeat-hit path drives the observed latency reduction.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
case=tp4_prefix128k
case=tp4_prefix512k
case=tp4_prefix1m
results/real_data/vllm_single_node_v6_matrix/tp4_prefix128k/
results/real_data/vllm_single_node_v6_matrix/tp4_prefix512k/
results/real_data/vllm_single_node_v8_1m_extensions/tp4_prefix1m/
```

---

# 8. TOP 5 — Prompt-Token Admission Fingerprint

## V2 rename

Replace **“Prompt-Token Admission Law”** with:

> **Prompt-Token Admission Fingerprint — measured 8K/128K open-loop capacity normalization**

The original “law” wording is too broad because only two open-loop context lengths establish the normalization.

## Executive message

> **Raw RPS changes dramatically between 8K and 128K, but the high-load accepted rate is much closer when normalized to input tokens/s: ~27.5K vs ~24.2K input tok/s.**

## Measured high-load region

Use median achieved request throughput across the measured `1.00x / 1.10x / 1.25x` offered-load points.

```text
8K:
  median achieved request throughput ~= 3.3586 req/s
  3.3586 * 8192 ~= 27.5K input tok/s

128K:
  median achieved request throughput ~= 0.18457 req/s
  0.18457 * 131072 ~= 24.2K input tok/s
```

The normalized values differ by roughly 14% even though prompt length differs by 16×.

## Boundary

Do not extrapolate this to 512K/1M or another topology without corresponding open-loop sweeps.

This is an **empirical admission fingerprint**, not a universal serving constant.

## Decision changed

> **Capacity planning for prefill-heavy traffic should normalize demand into prompt tokens/s rather than compare workloads only in requests/s.**

## Best Executive visual

Two aligned panels:

1. achieved requests/s for 8K and 128K
2. achieved input tokens/s for the same points

Make the normalization visually obvious.

## Confidence

```text
Evidence confidence: MEDIUM-HIGH for the two measured contexts.
Causal confidence:   LOW-MEDIUM for claiming a general invariant.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
case=tp4_openloop_8192
case=tp4_openloop_131072
results/real_data/vllm_open_loop/
```

---

# 9. TOP 6 — Parallelism Directional Elasticity + GPU-Second Frontier

## Executive message

> **The useful question is not “more GPUs or fewer GPUs?” It is “which parallelism dimension gives latency benefit for this context, and what resource occupancy does that benefit consume?”**

## Part A — directional TTFT elasticity

Define:

```text
eta = ln(TTFT_before / TTFT_after) / ln(GPU_multiplier)
```

For a 2× GPU increase:

```text
eta = 1  ideal linear TTFT speedup
eta = 0  no TTFT benefit
eta < 0  more GPUs made TTFT worse
```

### Doubling TP: TP4/PP1 -> TP8/PP1

Canonical context-baseline values:

| Context | TP4 TTFT | TP8 TTFT | Speedup | eta |
|---|---:|---:|---:|---:|
| 8K | 0.2222 s | 0.2633 s | 0.844× | -0.245 |
| 128K | 4.5321 s | 4.8096 s | 0.942× | -0.086 |
| 512K | 31.9162 s | 28.0887 s | 1.136× | +0.184 |
| 1M | 93.2479 s | 74.6875 s | 1.249× | +0.320 |

This corrects any stale claim that TP8 is worse at 1M. TP8 **does** improve 1M TTFT on the matched single-node baseline, but the scaling is sub-linear and uses twice the GPUs.

### Doubling PP: TP4/PP2 -> TP4/PP4 on Native

| Context | TP4/PP2 TTFT | TP4/PP4 TTFT | Speedup | eta |
|---|---:|---:|---:|---:|
| 128K | 2.6472 s | 1.7100 s | 1.548× | +0.631 |
| 512K | 17.9455 s | 10.2218 s | 1.756× | +0.812 |
| 1M | 52.5264 s | 28.5680 s | 1.839× | +0.879 |

## Part B — GPU-second occupancy proxy

Define:

```text
C_GPU = active GPU count * TTFT
```

At 1M c1:

| Configuration | TTFT | GPUs | GPU-s/request proxy |
|---|---:|---:|---:|
| TP4/PP1 | 93.248 s | 4 | 373.0 |
| TP4/PP2 | 52.526 s | 8 | 420.2 |
| TP4/PP4 | 28.568 s | 16 | 457.1 |
| TP8/PP1 | 74.688 s | 8 | 597.5 |
| TP8/PP2 | 41.515 s | 16 | 664.2 |
| TP16/PP1 | 68.197 s | 16 | 1091.1 |

`GPU-s/request` is a simple reservation/occupancy proxy. It is **not** power, energy, dollar cost, or utilization-weighted cost.

## Decision changed

> **Allocate additional GPUs along the parallelism dimension that has positive measured elasticity for the workload/SLO, and expose the GPU-second trade-off instead of declaring a universal topology winner.**

## Best Executive visual

Primary:
- X: GPU-s/request proxy
- Y: TTFT
- point: topology
- highlight non-dominated measured points only as a workload-specific frontier

Inset:
- TP-doubling and PP-doubling elasticity vs context

## Confidence

```text
Evidence confidence: HIGH.
Causal confidence:   MEDIUM; the metric shows directional scaling efficiency but does not isolate every mechanism.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
case=tp4_context_baseline
case=tp8_context_baseline
case=tp4_pp2_dist / GCP_NATIVE
case=tp4_pp4_dist / GCP_NATIVE
case=tp8_pp2_dist / GCP_NATIVE
case=tp16_pp1_dist / GCP_NATIVE
```

---

# 10. TOP 7 — TP Decode Evidence Chain

## Executive message

> **The TP8 decode penalty appears independently at four evidence layers: small-message NCCL latency, PyTorch Profiler AllReduce CUDA time, Nsight aggregate decode work, and user-visible TPOT.**

This is one of the campaign's strongest cross-tool correlations.

## Layer A — NCCL primitive

Representative processed small-message AllReduce points:

```text
16 KiB:
  TP4 ~19 us
  TP8 ~37 us

128 KiB:
  TP4 ~28.6 us
  TP8 ~54.6–55.5 us

512 KiB:
  TP4 ~78 us
  TP8 ~168 us
```

The small-message TP8/TP4 latency ratio is roughly ~1.9–2.2× in these points.

## Layer B — PyTorch Profiler

Exact rank-0 profile rows:

```text
tp4_8k_decode:
  ncclDevKernel_AllReduce...
  Self CUDA = 251.529 ms
  Self CUDA share = 32.14%
  Calls = 7040

tp8_8k_decode:
  Self CUDA = 583.866 ms
  Self CUDA share = 55.41%
  Calls = 7040
```

Same call count; rank-local AllReduce Self CUDA time is:

```text
583.866 / 251.529 ~= 2.32x
```

This does **not** mean TP8 has more AllReduce calls in this profile.

## Layer C — Nsight

Single-node decode profiles independently show NCCL AllReduce as a dominant aggregate GPU-work category.

Required semantics:

> `aggregate GPU kernel work`, not `exclusive request critical-path wall time`.

## Layer D — E2E

Matched single-node 8K c1 context baseline:

```text
TP4/PP1 TPOT = 4.4748 ms
TP8/PP1 TPOT = 6.3500 ms
```

TP8 TPOT is ~41.9% higher.

## Decision changed

> **Do not assume wider TP improves interactive decode. For short decode-heavy work, collective synchronization can erase the extra compute parallelism.**

## Best Executive visual

Horizontal evidence chain:

```text
NCCL MICROBENCH
~2x small-message latency
    ->
PT PROFILER
same 7040 calls, 2.32x rank-local AR CUDA time
    ->
NSIGHT
NCCL-heavy aggregate decode work
    ->
E2E
TP8 TPOT ~41.9% higher
```

Each node drills to its exact raw artifact.

## Confidence

```text
Evidence confidence: HIGH.
Causal confidence:   MEDIUM-HIGH that wider-TP synchronization is a contributor;
                     exclusive critical-path fraction remains UNRESOLVED.
```

## Evidence

```text
results/real_data/hardware_processed/nccl_points.csv
results/real_data/profiles_torch_single_node/tp4_8k_decode/torch/profiler_out_0.txt
results/real_data/profiles_torch_single_node/tp8_8k_decode/torch/profiler_out_0.txt
results/real_data/profiles_single_node/tp4_decode/
results/real_data/profiles_single_node/tp8_decode/
results/real_data/profiles_single_node/PROFILE_ANALYSIS.json
results/real_data/final_validation/combined_vllm_runs.csv
```

---

# 11. TOP 8 — Runtime-Knob Derivative Fingerprint

## Executive message

> **Some runtime knobs are non-binding in a measured state while others have large latency leverage. At 1M c4, changing `max_num_seqs` 4→16 barely moves TTFT; changing chunk/token budget materially changes c1 TTFT.**

## max_num_seqs — measured non-binding state

1M c4 TP4:

```text
max_num_seqs 4  -> TTFT ~232.342 s
max_num_seqs 8  -> TTFT ~232.364 s
max_num_seqs 16 -> TTFT ~232.250 s
```

Total spread is ~0.05%.

In the same state:

```text
peak_running = 2
peak_waiting = 3
```

So the configured ceiling is not reached. This is a stronger explanation than simply saying “the knob does not matter.”

## Chunk/token budget — measured high-sensitivity state

TP4 c1 TTFT:

```text
128K: 4K 5.228 s -> 8K 4.534 s -> 16K 4.364 s
512K: 4K 40.271 s -> 8K 31.936 s -> 16K 30.455 s
1M:   4K 122.049 s -> 8K 93.277 s -> 16K 88.951 s
```

At 1M, 4K→16K reduces TTFT by ~27%.

Do not call 16K universally optimal. A fairness/decode-interference optimum needs matched fairness/decode evidence.

## Decision changed

> **Stop spending optimization effort on `max_num_seqs` in this measured 1M c4 state; direct tuning effort toward token budget, topology, prefix reuse, and admission where the measured derivative is materially larger.**

## Best Executive visual

### Knob Derivative Fingerprint

Two mini-panels:
- flat `max_num_seqs` line
- steep chunk-size TTFT line

Optional normalized derivative bars across all measured knobs, but only if every bar is generated from a documented matched A/B experiment.

## Confidence

```text
Evidence confidence: HIGH.
Causal confidence:   MEDIUM-HIGH that max_num_seqs is non-binding because runtime occupancy never reaches the configured ceiling.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
cases tp4_1m_maxseq4 / 8 / 16
cases tp4_chunk4k / tp4_chunk8k / tp4_chunk16k
```

---

# 12. TOP 9 — Busy GPU != Efficient Serving

## Executive message

> **Higher GPU-utilization telemetry can coexist with substantially worse TTFT. “GPU busy” measures activity, not useful-token efficiency.**

## Native measured examples

### 128K

```text
TP4/PP4:
  TTFT = 1.710 s
  mean GPU util across nodes ~= 35.2%

TP16/PP1:
  TTFT = 6.420 s
  mean GPU util across nodes ~= 63.2%
```

### 1M

```text
TP4/PP4:
  TTFT = 28.568 s
  mean GPU util across nodes ~= 62.8%

TP16/PP1:
  TTFT = 68.197 s
  mean GPU util across nodes ~= 80.6%
```

Top #2 independently shows that TP16 is far more fabric-sensitive under the cap sweep.

## Boundary

Do not fit a causal regression from four topology points.

Do not interpret high utilization as bad. The correct statement is:

> GPU utilization is semantically incomplete because communication kernels also count as GPU activity.

## Decision changed

> **Do not choose or validate a topology from GPU utilization alone. Pair utilization with user latency, throughput, communication exposure, and profiler composition.**

## Best Executive visual

Scatter:
- X: mean GPU utilization
- Y: TTFT
- point: topology
- separate 128K / 1M panels or context toggle
- no causal regression line

## Confidence

```text
Evidence confidence: HIGH.
Causal confidence:   MEDIUM for the communication-heavy interpretation.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
gpu_node_stats_json -> gpu_util_mean_pct
results/real_data/profiles_multi_node_native/
results/real_data/hardware_processed/nccl_points.csv
```

---

# 13. TOP 10 — KV Headroom != VRAM Headroom

## Executive message

> **Pipeline parallelism can sharply reduce the reported KV-cache utilization percentage while total per-GPU memory remains in roughly the same high-80-GiB range. Low KV% is not low VRAM use.**

## Native 1M measured data

| Configuration | Peak KV usage | Peak GPU memory telemetry |
|---|---:|---:|
| TP4/PP1 | 12.29% | ~88.39 GiB |
| TP4/PP2 | 5.91% | ~88.69 GiB |
| TP4/PP4 | 2.75% | ~88.83 GiB |
| TP16/PP1 | 12.13% | ~86.71 GiB |

The normalization:

```text
PP * KV%
TP4/PP1 ~12.29
TP4/PP2 ~11.82
TP4/PP4 ~10.99
```

is consistent with active KV state being spread across deeper PP stages, but it does **not** prove the runtime allocator's exact sharding formula.

## What V2 must not claim

Do not write:

```text
98% of memory is weights
weights dominate exactly X GiB
KV is physically sharded by exactly 1/PP
```

unless an allocator-level source provides the decomposition.

## Decision changed

> **Use KV% to understand cache pressure, and use total memory telemetry to understand VRAM headroom. Never substitute one for the other when deciding fit, concurrency, or offload strategy.**

## Best Executive visual

Two aligned mini-panels per topology:

1. peak KV utilization %
2. peak total GPU memory GiB

Never put % and GiB on an unlabeled shared axis.

## Confidence

```text
Evidence confidence: HIGH for both measured metrics.
Causal confidence:   LOW-MEDIUM for exact allocator/sharding interpretation.
```

## Evidence

```text
results/real_data/final_validation/combined_vllm_runs.csv
peak_kv_usage
gpu_node_stats_json -> gpu_mem_used_peak_mb
```

---

# 14. Executive card contract

Every Top-10 card must contain these fields in this order:

```text
TITLE
One-line finding
Large measured/derived number
WHAT happened
WHERE / workload scope
WHY / mechanism interpretation
DECISION CHANGED
Evidence confidence
Causal confidence
Boundary / what is not proven
Evidence button
```

Example for Top #3:

```text
Concurrency Can Destroy Latency Without Adding Capacity

1M TP4 c1 -> c4:
+1.52% output throughput
2.48x TTFT
26.15x TPOT
134.43 s queue

DECISION CHANGED:
Trigger admission from queue/TTFT/TPOT SLO before KV exhaustion.

Evidence confidence: HIGH
Causal confidence: HIGH for queue contribution to added TTFT; MEDIUM for TPOT root mechanism.
```

---

# 15. Evidence drawer contract

Every chart point or discovery must resolve to exact evidence, not substring search.

Required drawer fields:

```text
Observation
Exact measured values
Formula / derivation
Evidence class
Evidence confidence
Causal confidence
Case + bench + network provenance
Exact profile/rank aggregation rule if profiler-derived
Raw artifact paths
Boundary
Required follow-up experiment, if any
```

Every plotted datum should carry a structured identity such as:

```json
{
  "evidence_id": "EV-...",
  "case": "tp4_pp4_dist",
  "bench": "1m_c1",
  "network_provenance": "GCP_NATIVE",
  "tp": 4,
  "pp": 4,
  "context_tokens": 1000000,
  "load_semantics": "concurrency",
  "load_value": 1,
  "metric": "mean_ttft_ms",
  "unit": "ms",
  "value": 28567.95494,
  "evidence_class": "MEASURED",
  "artifact_path": "..."
}
```

Do not map charts to Evidence by fuzzy case-name substrings.

---

# 16. Data architecture — mandatory V2 implementation

Do not hard-code Top-10 Chart.js arrays.

Recommended build path:

```text
RAW CAMPAIGN ARTIFACTS
        |
FINAL_VALIDATION + coverage + combined_vllm_runs
        |
hardware normalized tables
        |
profile validation + exact rank exports
        |
DASHBOARD_CANONICAL_DATA.json
        |
versioned deterministic derived functions
        |
EXECUTIVE_DISCOVERIES.json
        |
Executive UI
```

Recommended discovery object:

```json
{
  "id": "concurrency_value_destruction",
  "title": "Concurrency Can Destroy Latency Without Adding Capacity",
  "evidence_confidence": "HIGH",
  "causal_confidence": "HIGH_QUEUE_MEDIUM_TPOT",
  "evidence_class": ["MEASURED", "DERIVED", "CROSS_VALIDATED"],
  "decision_changed": "Use latency/queue SLO admission before KV exhaustion.",
  "inputs": [],
  "derivations": [],
  "boundaries": [],
  "visual": {},
  "drilldown": []
}
```

Version the derivation code. The HTML should be a renderer, not the source of truth.

---

# 17. Performance-cost language

The campaign can support:

```text
latency
throughput
GPU count
GPU-seconds/request proxy
resource-efficiency comparisons
```

It does **not** directly support a dollar/token claim.

Do not write:

> `Topology X reduces token cost by Y%`

unless a separate cost model explicitly defines:

```text
GPU price / reserved or on-demand basis
utilization assumptions
request mix
output length mix
idle/reservation accounting
network/CPU cost treatment
```

Correct Executive phrasing:

> **resource-efficiency / cost-relevant implication**

An optional future cost overlay may consume the measured GPU-second and throughput metrics, but pricing must remain a separate external input.

---

# 18. Claims that must be deleted or prevented

The V2 implementation must not reintroduce any of the following:

```text
Universal “best topology” or winner.
“c=1 is the production cap” without an SLO.
Aggregate Nsight GPU work = wall-clock critical path.
~116 hidden-width equivalents/token = literal transfers/token.
~24–28K prompt tokens/s = universal capacity law beyond measured 8K/128K.
Exact weights/runtime/activation memory split without allocator evidence.
Prefix caching should be enabled unconditionally.
High GPU utilization = compute bound.
TP16 called local on an 8-GPU node.
NVLink wording for this PCIe/NUMA G4 setup.
61-layer communication claims; the model manifest has 27 layers.
“100G” or “20G” labels without measured achieved bandwidth.
Capped completed runs marked FAILED merely because performance is poor.
FP8-KV backend-cause statement unless a direct rejection log proves it.
50G/10G application behavior — these were hardware-only in this campaign.
```

---

# 19. Supporting findings that should remain outside the Top 10

These are important but should be shown as campaign/evidence-health controls rather than promoted as separate performance discoveries:

## Distributed profiler completeness

```text
14 / 22 expected distributed profiles complete
17 validation files present
profiles_all_complete=false
```

Profiler cards must expose exact profile completeness and node/rank coverage.

## Sample/reliability health

Use the canonical per-row:

```text
p95_reliable
p99_reliable
```

as separate flags. Do not create one frontend “high-N p95/p99 valid” bucket.

## Network provenance

Application E2E:

```text
Native
configured-100G
configured-20G
```

Hardware-only additional sensitivity points:

```text
configured-50G
configured-10G
```

The two scopes must never be silently combined.

---

# 20. V2 acceptance tests for each discovery

A discovery is allowed onto the Executive tab only when all relevant checks pass:

- [ ] All input metrics resolve to exact canonical rows or exact raw profile artifacts.
- [ ] All derivations are reproducible by versioned code.
- [ ] Evidence class is correct.
- [ ] Evidence confidence is displayed.
- [ ] Causal confidence is displayed independently.
- [ ] Workload/context/topology/network scope is visible.
- [ ] `DECISION CHANGED` is explicit.
- [ ] The boundary says what is not proven.
- [ ] No Kimi K3 dimensions are used numerically.
- [ ] No missing evidence is rendered as zero.
- [ ] Profiler aggregate work is never labeled exclusive wall-clock critical path.
- [ ] Network cap and achieved bandwidth are separate fields.
- [ ] Mixed means are not mislabeled as hit-conditioned prefix latency.
- [ ] Cost language is separated from empirical performance data.

---

# 21. Executive publication gates

Before the dashboard is called publication/data-signoff ready:

1. Correct all P0 issues from `V8_V4_23SEP_9PM_CLOSURE_AUDIT.md`.
2. Remove all stale `native-only / bandwidth sensitivity deferred` text.
3. Remove all `Ada`, `NVLink`, `61 layers`, `21.84 GB/s SendRecv`, stale queue, stale TP-width, and stale prefix values.
4. Use `14/22 expected complete` for distributed profiler status.
5. Rebuild 128K open-loop directly from canonical rows.
6. Rebuild prefix visual from first/repeat fields.
7. Use exact p95/p99 reliability flags.
8. Replace fuzzy chart→Evidence mapping with exact IDs.
9. Generate Top-10 datasets from normalized source data rather than HTML arrays.
10. Require an evidence drawer for every derived/causal claim.

---

# 22. Final Executive narrative

The final page should leave an experienced inference architect with this understanding:

> **This campaign shows that deployment behavior is regime-dependent, not described by one throughput number. Topology changes how much fabric limitation becomes user-visible; 1M concurrency can destroy TTFT and TPOT before KV exhaustion or preemption appears; repeated prefixes can move requests into a very different latency regime; and the useful direction for adding GPUs changes with context. Cross-tool evidence from hardware microbenchmarks, vLLM E2E metrics, scheduler/KV telemetry, Nsight, and PyTorch Profiler can explain these effects, but only when measurement and causal interpretation are kept separate. Standard operational metrics such as GPU utilization or KV% are useful signals, not standalone deployment decisions.**

The intended product is therefore not a benchmark summary. It is a **deep-characterization deployment decision system** where every recommendation is workload-scoped, evidence-linked, reproducible, and explicit about uncertainty.

---

# 23. V2 implementation delta from V1

## Keep

```text
Top-10 concept and overall architecture
raw-artifact evidence drawers
normalized generated Executive data object
hybrid-attention scaling analysis
fabric sensitivity correlation
queue closure
prefix scaling
parallelism elasticity
cross-tool TP decode chain
runtime knob sensitivity
GPU-utilization warning
KV-vs-total-memory warning
```

## Modify

```text
Hero order -> Fabric Exposure, Concurrency Cliff, Hybrid-Attention Shift
Top #1 -> resource-pressure regime shift, not proven critical-path regime shift
Top #3 -> SLO-driven admission, not universal c=1 cap
Top #4 -> first/cold vs repeat-hit fields only
Top #5 -> rename “law” to “fingerprint”; constrain to 8K + 128K measured contexts
Top #6 -> correct TP8 1M result and expose GPU-second trade-off
Top #7 -> exact single-node TP4/TP8 PT profiler provenance
Top #8 -> explain max_num_seqs is non-binding because runtime occupancy is below the ceiling
Top #10 -> remove allocator decomposition claims
All cards -> separate evidence confidence from causal confidence
All cards -> add DECISION CHANGED
```

## Delete / prohibit

```text
universal winner language
universal cost-savings language
critical-path percentages from aggregate GPU work
literal interpretation of fitted communication coefficient
unmeasured 512K/1M prompt-token admission extrapolation
unconditional prefix-cache recommendation
exact weights-vs-runtime memory decomposition
stale hardware metadata and unsupported topology language
```

---

# 24. Recommended next implementation artifact

Generate:

```text
results/real_data/final_validation/EXECUTIVE_DISCOVERIES_V2.json
```

with one object per Top-10 discovery containing:

```text
stable discovery ID
version
source artifact hashes/paths
input evidence IDs
formula version
measured values
derived values
fit quality where applicable
evidence class
evidence confidence
causal confidence
decision changed
boundary
visual spec
drill-down targets
```

The dashboard should render from this object. Future reruns then regenerate the discoveries rather than requiring manual chart edits.

---

## Final sign-off rule

**Impact must come from measured contrast and decision consequence, not from stronger language.**

A claim is ready for Executive publication only when an engineer can click it and answer all five questions from the evidence:

```text
WHAT happened?
WHERE did it happen?
WHY is that interpretation supported?
WHAT decision changes?
WHAT is still not proven?
```
