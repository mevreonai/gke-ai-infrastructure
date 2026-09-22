# V8-FULL Release Validation Report

**Release:** 8.0.0  
**Release date:** 2026-09-21  
**Target:** 2 nodes × 8 NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs  
**Primary objective:** preserve the proven V6 vLLM path while adding complete hardware/fabric characterization, deeper 1M-context coverage, scale-out at Native/100G/20G, distributed profiling, and strict evidence validation.

## 1. Release conclusion

V8-FULL is source-, syntax-, matrix-, provenance-, and validator-tested for release. The current package passes **210/210 static checks** and the strict synthetic full-run validator accepts a complete 111-point fixed serving matrix with **22/22 distributed profiler cases**. Negative tests intentionally corrupting NCCL policy, readiness, distributed telemetry, 1M coverage, and hardware evidence are rejected as expected.

This validation materially reduces script/configuration risk, but it is not a claim that a future cloud run cannot encounter an external runtime failure. Driver state, GCP networking, Ray/NCCL runtime behavior, disk pressure, transient VM/network faults, and third-party tool behavior can only be proven on the actual two-node cluster. V8-FULL therefore fails early, preserves partial raw evidence, and supports resume rather than silently converting failures into measurements.

## 2. Frozen network matrices

### vLLM scale-out

Only these three model-run network states are used:

- `GCP_NATIVE`
- `GCP_CAPPED_100G`
- `GCP_CAPPED_20G`

`GCP_CAPPED_10G` is **not** a vLLM model-run state in V8-FULL.

For every vLLM network state, V8-FULL attempts all four topologies and all three contexts:

| Topology | 128K c1 | 512K c1 | 1,000,000 c1 |
|---|---:|---:|---:|
| TP4 / PP2 | configured | configured | configured, safety-gated after 512K |
| TP8 / PP2 | configured | configured | configured, safety-gated after 512K |
| TP4 / PP4 | configured | configured | configured, safety-gated after 512K |
| TP16 / PP1 | configured | configured, gated after 128K | configured, gated after 512K |

This is **4 × 3 × 3 = 36 fixed scale-out vLLM operating points**.

### Hardware / fabric smoke

The lower-cost hardware/fabric layer keeps the complete transport curve:

- `GCP_NATIVE`
- `GCP_CAPPED_100G`
- `GCP_CAPPED_50G`
- `GCP_CAPPED_20G`
- `GCP_CAPPED_10G`

At every state it executes forward/reverse iperf, NCCL SendRecv at six message sizes, and cross-node TP2/TP8/TP16 AllReduce curves. This allows the vLLM 20G operating point to be interpreted against the denser transport sensitivity curve without spending model-runtime budget at every intermediate cap.

## 3. 1M-context coverage

V8-FULL reruns the original V6 single-node matrix and then adds a separate V8 extension file rather than altering the known-good V6 case file.

### Preserved V6 1M coverage

The preserved V6 matrix includes TP4/TP8 1M context baselines, TP4 1M prefill focus, TP4 4K/8K/16K chunked-prefill 1M cases, TP4 closed-loop 1M c1/c2, and TP4 native CPU-offload-pressure 1M.

### V8 1M additions

- TP4 1M c1 → c2 → c4 concurrency progression
- TP8 1M c1 → c2 → c4 concurrency progression
- TP4 1M `max_num_seqs` = 4 / 8 / 16 at c4
- TP4 FP8-KV 1M c1
- deterministic TP4 1M prefix-reuse case
- all four distributed topologies at 1M c1 under Native/100G/20G

The requested input length is **1,000,000 tokens**, intentionally distinguished from `max_model_len=1,048,576`.

A safety-gated scale-out 1M case is recorded as a skip, not zero and not OOM unless the raw runtime explicitly reports OOM. Strict full-coverage sign-off requires all required 1M points to complete.

## 4. Compute/kernel and memory/fabric characterization

V8-FULL includes:

- NVBandwidth H2D and D2H
- NVBandwidth D2D bandwidth
- device-to-device latency
- BabelStream/GDDR bandwidth on representative GPUs from both NUMA groups
- native TP4 and TP8 NCCL AllReduce exact-size points
- TP4/TP8 NCCL AllReduce/AllGather/ReduceScatter curves
- cross-node TP2/TP8/TP16 AllReduce
- NCCL SendRecv/PP-proxy measurements
- CUTLASS FP16 tensor-core reference GEMMs, including an 8192³ shape and Kimi-width `N=K=7168` reference shapes

CUTLASS rows are deliberately labeled **reference compute roofs**, not Kimi K3 MXFP4 efficiency. Actual vLLM execution kernels are retained through Nsight/PyTorch profiling so the run can expose the real attention/KDA/MLA/MoE/GEMM/normalization/NCCL kernel stream used by the installed stack.

## 5. V6 NCCL alignment

The exact V6 suite and V6 qualification artifacts were re-audited before V8 release.

- Exact V6 source ZIP SHA-256: `e0ea335c4a92c5cfb48483ca433aa5d4742badae2bb0cbd21dafed06b94e636c`
- V6 qualification ZIP SHA-256: `df70814fcab1d7acdaee4c99ac5a1bfbe18a2d2978d9ed8119fb06643aec2683`
- Older 2026-09-15 hardware ZIP SHA-256: `0225500fab8771376f6d58d42cde245c1c8a3ebd3594e39c76684b5ba6d33c28`

The exact V6 source contains no `NCCL_P2P_DISABLE`, `NCCL_SHM_DISABLE`, or `NCCL_P2P_LEVEL` assignment. The successful V6 qualification environment captured no NCCL overrides. By contrast, the older V4-era local TP8 hardware command explicitly used both `NCCL_P2P_DISABLE=1` and `NCCL_SHM_DISABLE=1`; those historical numbers are therefore sensitivity evidence only.

V8 policy is consequently:

- **single node:** clear all `NCCL_*` overrides before V6-aligned vLLM and primary native local NCCL tests;
- **multi-node:** preserve allowed V6/GCP network settings such as Socket-network configuration, but clear P2P/SHM/P2P-level forcing;
- **remote Ray node:** explicitly propagate the allowed NCCL network environment and `LD_LIBRARY_PATH`, then audit every live Ray node for symmetry before workers are used;
- **forced P2P:** one explicitly labeled `SENSITIVITY_ONLY` hardware row;
- **SHM disable:** no executable `NCCL_SHM_DISABLE=1` assignment in V8-FULL.

## 6. Profiler matrix

### Single-node

- TP4 prefill
- TP4 decode
- TP4 batched decode
- TP8 prefill
- TP8 decode
- TP8 batched decode
- separate TP4 and TP8 PyTorch profiler captures

### Native distributed

For each of TP4/PP2, TP8/PP2, TP4/PP4 and TP16/PP1:

- 128K prefill
- 8K decode
- 8K c8 batched decode

With the default `RUN_HEAVY_PROFILE=1`:

- TP4/PP4 512K prefill
- TP16/PP1 512K prefill

### Capped distributed

For every topology:

- 128K prefill at 100G
- 128K prefill at 20G

The default therefore expects **22 distributed profile validations**: 12 native base + 2 heavy native + 8 capped.

1M end-to-end benchmarks and telemetry run, but 1M Nsight is intentionally not a default requirement because a 16-rank 1M trace can be extremely large and intrusive.

## 7. Raw and processed evidence retention

V8-FULL retains separate source layers rather than collapsing evidence into one summary:

- preflight and readiness reports from both nodes
- exact runtime `RUN_CONFIG.env`
- source SHA-256 manifest and release manifest
- raw node-local hardware logs/JSON/telemetry
- raw network iperf/NCCL/qdisc provenance
- processed hardware summaries and strict hardware validation
- original V6 single-node result hierarchy
- separate V8 1M-extension hierarchy
- generated open-loop case file and raw results
- separate Native/100G/20G scale-out hierarchies
- raw both-node distributed telemetry and Prometheus captures
- single-node Nsight and PyTorch profiler output
- both-node distributed `.nsys-rep` and available SQLite/NVTX/CUDA/NCCL summaries
- unified CSV/JSON coverage and validation artifacts
- file inventory and SHA-256 protected evidence archive

## 8. Static validation

Latest package-source validation:

- **210 checks**
- **0 failed**
- Python compile: pass
- shell `bash -n`: pass
- JSON parsing: pass
- V6 byte-compatibility hashes: pass
- gate ordering: pass
- four-topology 1M scale-out matrix: pass
- Native/100G/20G vLLM-mode enforcement: pass
- absence of 50G/10G in vLLM matrix: pass
- full five-state hardware sweep: pass
- remote Ray NCCL environment propagation/audit: pass
- no executable SHM-disable assignment: pass
- P2P-disable restricted to sensitivity-only row: pass

The machine-readable output is `STATIC_VALIDATION.json`.

## 9. Synthetic strict-run validation

A complete synthetic result tree was passed through the same final collector used after the real run. It represented:

- **111/111 fixed serving points COMPLETED** (64 V6 single-node + 11 V8 1M extensions + 36 scale-out; dynamic open-loop is additional)
- both-node readiness PASS
- hardware validation PASS
- all 12 required scale-out 1M topology × network combinations complete
- Native/100G/20G network evidence complete
- both-node telemetry present for every completed scale-out row
- **22/22 distributed profiles complete**
- 12/12 scale-out Ray NCCL audits
- 22/22 profiler Ray NCCL audits
- NCCL policy PASS
- final strict `full_suite_valid = true`

## 10. Fail-closed tests

The release was also checked against deliberately damaged synthetic evidence. Each case returned nonzero strict validation and `full_suite_valid=false`:

| Injected problem | Expected result | Observed |
|---|---|---|
| `NCCL_P2P_DISABLE=1` in Ray evidence | reject NCCL policy | rejected |
| node1 readiness failure | reject readiness | rejected |
| missing node1 scale-out telemetry | reject telemetry completeness | rejected |
| safety-skipped TP16/PP1 1M @20G | reject strict 1M full coverage | rejected |
| missing TP16 @10G hardware network evidence | reject hardware full coverage | rejected |

The hardware validator also accepts a complete synthetic hardware tree (**128 checks, 0 failed**) and rejects the intentionally incomplete hardware tree. The result packager was smoke-tested on the complete synthetic result tree; the generated evidence TAR passed SHA-256 verification and contained its own `final_validation/FILE_LIST.tsv` inventory.

## 11. Readiness / runtime-risk controls

Before long GPU work, V8-FULL verifies both nodes for:

- expected GPU count and RTX PRO 6000 Blackwell identity
- minimum available disk space
- vLLM/Ray/Nsight executable availability
- required vLLM CLI capabilities used by the suite
- exact known-good V6 core stack versions by default
- absence of forbidden NCCL local-transport forcing
- clean-NCCL-library setup when the V6 Socket workaround is active

Hardware preparation reuses already-built tools by default and only rebuilds when a binary is missing or `V8_REBUILD_HW_TOOLS=1` is explicitly requested. This reduces the risk of replacing a known-good benchmark build immediately before a long run.

Every major phase has a resume marker. Failed phases retain logs and can be restarted using the same `V8FULL_RUN_ID`/`V8FULL_ROOT` rather than rerunning completed 1M work.

## 12. Release limitation

This package has been deeply source-reviewed and synthetic-validator-tested, but **the new V8-FULL package itself has not been executed end-to-end on the actual two-node GCP cluster in this environment**. Therefore the correct claim is “release-ready with fail-fast and strict validation,” not “runtime success guaranteed.” The actual cluster run remains the final qualification.
