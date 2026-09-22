# V8-FULL RTX PRO 6000 / vLLM Characterization Suite

V8-FULL is the hardened successor to the working V6/V7 characterization flow. Its primary goal is to preserve the known-good V6 execution behavior while closing three evidence gaps:

1. native local NCCL must not be contaminated by legacy `NCCL_P2P_DISABLE` / `NCCL_SHM_DISABLE` forcing;
2. scale-out vLLM must be measured under the three network modes actually needed by the team: **GCP_NATIVE**, **GCP_CAPPED_100G**, **GCP_CAPPED_20G**;
3. all raw, processed, network-validation and profiler artifacts must remain auditable after the run.

## V6 alignment that V8 preserves

The exact V6 source package was re-inspected before V8 was built.

- The V6 source contains **no** `NCCL_P2P_DISABLE`, `NCCL_SHM_DISABLE`, or `NCCL_P2P_LEVEL` usage.
- The actual V6 single-node qualification manifest captured an empty `NCCL_*` environment (`env: {}`), so the successful TP4/TP8 vLLM qualification was not run with P2P or SHM disabled.
- A separate, older 2026-09-15 hardware/NCCL run **did** execute local TP8 all-reduce with `NCCL_P2P_DISABLE=1` and `NCCL_SHM_DISABLE=1`. Those legacy numbers are therefore forced-transport sensitivity evidence, not native local NCCL evidence.

The machine-readable audit is `V6_ALIGNMENT_EVIDENCE.json`.

For V8, all preserved V6 single-node files listed in `V6_COMPATIBILITY_MANIFEST.json` remain byte-identical to the exact V6 package. V8 modifies only the layers that need new 1M, network, provenance, summarization or profiling functionality.

## NCCL transport policy

### Single-node vLLM and local native NCCL

V8 explicitly removes **all `NCCL_*` overrides** before single-node vLLM and before native local NCCL microbenchmarks. This reproduces the actual successful V6 single-node qualification environment and prevents stale shell variables from silently changing the local transport path.

### Multi-node vLLM

V8 may retain the V6 GCP Socket network workaround (`NCCL_NET=Socket` / clean NCCL library path) when provided by `RUN_CONFIG.env`, but it explicitly clears:

- `NCCL_P2P_DISABLE`
- `NCCL_SHM_DISABLE`
- `NCCL_P2P_LEVEL`

before Ray/vLLM starts. This keeps local intra-node GPU communication on NCCL defaults while preserving the known GCP cross-node network setup.

### Forced P2P sensitivity

`NCCL_P2P_DISABLE=1` exists only in one explicitly labeled hardware **SENSITIVITY_ONLY** measurement. V8 never uses `NCCL_SHM_DISABLE=1` in executable benchmark code.

## Full default execution

Running:

```bash
./00_run_v8_full.sh
```

attempts the full suite by default.

| Phase | Default coverage |
|---|---|
| Preflight | GPU/CPU/NUMA/PCIe/network, CUDA/NCCL/vLLM/Ray/Nsight, exact model revision |
| Hardware/local | NVBandwidth H2D/D2H/D2D/P2P latency, BabelStream, TP4/TP8 NCCL AR/AG/RS, CUTLASS reference GEMMs |
| Hardware/network | Native + 100/50/20/10G **forward/reverse iperf + SendRecv + cross-node TP2/TP8/TP16 all-reduce at every network state** |
| V6 single-node vLLM | Full original V6 matrix |
| V8 1M extensions | TP4/TP8 concurrency, max-num-seqs, FP8 KV and prefix-reuse extensions |
| Single-node open-loop | Evidence-derived rates |
| Scale-out vLLM | All four topologies under **Native / 100G / 20G** |
| Single-node Nsight | TP4/TP8 prefill, decode, batched decode |
| Single-node Torch profiler | TP4 and TP8 diagnostic captures |
| Distributed Nsight native | All four topologies, 128K prefill + 8K decode + 8K c8 batched decode; optional-heavy 512K prefill for TP4/PP4 and TP16/PP1 |
| Distributed Nsight capped | Matched 128K prefill for all four topologies at **100G and 20G** |
| Final validation | Unified coverage, 1M matrix, network matrix, NCCL-policy audit, artifact hashes |

## vLLM network matrix

V8 intentionally limits expensive model runs to the three network states needed for team communication:

- `GCP_NATIVE`
- `GCP_CAPPED_100G`
- `GCP_CAPPED_20G`

The cheaper hardware/network phase retains the full Native/100G/50G/20G/10G transport sweep; compared with the vLLM matrix, 50G and 10G are hardware-only sensitivity points.

For each vLLM network mode, all four scale-out topologies are attempted:

| Topology | 128K c1 | 512K c1 | 1M c1 |
|---|---:|---:|---:|
| TP4 / PP2 | yes | yes | gated after 512K |
| TP8 / PP2 | yes | yes | gated after 512K |
| TP4 / PP4 | yes | yes | gated after 512K |
| TP16 / PP1 | yes | yes | gated after 512K |

This produces up to **36 scale-out model operating points** (4 topologies × 3 contexts × 3 network modes).

`GCP_CAPPED_20G` is a bandwidth-sensitivity proxy for a 20Gb/s-class constrained path. It must not be labeled `LOCAL_REAL_2x10G`, because traffic shaping does not reproduce physical NIC bonding, NUMA, switch, queueing, offload or firmware behavior.

## 1M context coverage

V8 keeps all original V6 1M cases and adds separate V8 extension cases rather than mutating the proven V6 single-node matrix.

Single-node additions include:

- TP4 1M c1/c2/c4
- TP8 1M c1/c2/c4
- TP4 1M `max_num_seqs` sweep
- TP4 FP8-KV 1M
- deterministic 1M prefix-reuse

Scale-out adds 1M c1 for every topology under every required network mode. A gated skip is recorded as `SKIPPED_BY_SAFETY_GATE`; it is never converted to zero and is not called OOM unless raw logs explicitly show OOM.

`1,000,000` requested input tokens remain distinct from the `max_model_len=1,048,576` bound.

## Profiler coverage

### Native distributed profile matrix

For every topology:

- 128K prefill-focused
- 8K decode-focused
- 8K c8 batched decode

With `RUN_HEAVY_PROFILE=1` (default), V8 also profiles 512K prefill for TP4/PP4 and TP16/PP1.

### Capped-network distributed profiles

To avoid a huge trace explosion while still explaining network sensitivity, V8 captures matched **128K prefill** profiles for all four topologies at:

- 100G
- 20G

The native matrix remains the full profiler source of truth for decode/batched-decode and heavy long-prefill traces.

Each distributed profile retains both-node `.nsys-rep` files, Ray worker logs, workload JSON, exact commands, GPU telemetry, Prometheus logs, topology snapshots, available SQLite/NVTX/CUDA/NCCL summaries and a `PROFILE_VALIDATION.json` completeness record.

## Result tree

```text
~/v8_full_results/<RUN_ID>/
  logs/
  preflight_node0/
  preflight_node1/
  readiness_node0/
  readiness_node1/
  model_validation.json
  RUN_CONFIG.env
  SUITE_SOURCE_SHA256SUMS.txt
  V8_FULL_RELEASE.json
  hardware_prepare/
  hardware_raw/
    node0/
    node1/
    network_node0/
  hardware_processed/
  vllm_single_node_v6_matrix/
  vllm_single_node_v8_1m_extensions/
  10c_v8_generated_load_cases.json
  vllm_open_loop/
  vllm_scaleout_network_matrix/
    GCP_NATIVE/
      network_validation/
      results/
      summary_v8full/
    GCP_CAPPED_100G/
      network_validation/
      results/
      summary_v8full/
    GCP_CAPPED_20G/
      network_validation/
      results/
      summary_v8full/
  profiles_single_node/
  profiles_torch_single_node/
  profiles_multi_node_native/
  profiles_multi_node_capped/
    GCP_CAPPED_100G/
    GCP_CAPPED_20G/
  final_validation/
    combined_vllm_runs.json
    combined_vllm_runs.csv
    coverage.json
    coverage.csv
    ONE_MILLION_COVERAGE.md
    SCALEOUT_NETWORK_COVERAGE.md
    NCCL_POLICY_AUDIT.json
    artifact_index.json
    FINAL_VALIDATION.json
    FINAL_VALIDATION.md
    FILE_LIST.tsv
```

The packaging phase builds `<RUN_ID>_FULL_EVIDENCE.tar.gz` and a SHA-256 checksum. `FILE_LIST.tsv` is generated before the archive so the archive contains its own inventory. The strict collector also audits both-node telemetry for every completed scale-out benchmark and fails sign-off if a completed distributed row is missing node0 telemetry, node1 telemetry, Prometheus evidence, or has a sampler error.

## Before the GPU run

Run the static validator after unpacking:

```bash
python3 21_static_validate_suite.py
```

The package-generation validation checks Python syntax, shell syntax, JSON syntax, gate ordering, preserved V6 hashes, all four 1M scale-out topologies, profile-matrix coverage, V6 P2P/SHM alignment, local NCCL sanitization, remote Ray NCCL-environment symmetry, the exact Native/100G/20G vLLM matrix, full hardware Native/100G/50G/20G/10G coverage, capped profiler coverage, readiness integration, and stale executable paths.

Before long GPU work, `22_v8_readiness.py` also runs on **both nodes**. By default it enforces the exact core software versions observed in the successful V6 qualification (`V8_REQUIRE_V6_CORE_STACK=1`), verifies 8 RTX PRO 6000 Blackwell GPUs per node, required vLLM/Ray/Nsight CLI capabilities, free disk space, and the absence of forbidden local NCCL forcing flags.

## Running

```bash
unzip V8_FULL_vLLM_RTXPRO6000_Characterization.zip
cd V8_FULL
source ~/vllm_env/bin/activate
./00_run_v8_full.sh
```

Useful controls:

```bash
# Skip the hardware preparation phase entirely only when the tools are already present.
export RUN_HW_PREP=0

# When preparation runs, reuse known-good existing binaries by default.
# Set to 1 only when you intentionally want a fresh rebuild.
export V8_REBUILD_HW_TOOLS=0

# Hardware/network microbench caps. Keep 1 for the full hardware curve.
export RUN_NETWORK_CAPS=1

# vLLM scale-out modes. Default and recommended:
export VLLM_NETWORK_MODES="native 100g 20g"

# V8 readiness defaults: preserve the successful V6 core stack and require
# sufficient disk for large profiler/raw-log output.
export V8_REQUIRE_V6_CORE_STACK=1
export V8_MIN_FREE_GIB=100

# Skip only the two heavy 512K native distributed Nsight profiles.
export RUN_HEAVY_PROFILE=0

# Skip capped 100G/20G profiler subset while retaining capped vLLM benchmarks.
export RUN_CAPPED_PROFILE=0

# Resume a partially completed V8 run.
export V8FULL_RUN_ID=<existing_run_id>
export V8FULL_ROOT=~/v8_full_results/$V8FULL_RUN_ID
export V8FULL_RESUME=1
./00_run_v8_full.sh
```

## Success semantics

- `COMPLETED`: benchmark command completed successfully.
- `SAFETY_SKIPPED`: a prerequisite/gate prevented a more expensive case; valid evidence but not strict full coverage.
- `FAILED`: benchmark/profiler failed; raw evidence is retained.
- `NOT_RUN`: configured point has no manifest; strict validation fails.
- `NOT_CAPTURED` / `UNRESOLVED`: metric was unavailable; never converted to zero.

No source review can guarantee a future cloud/runtime outcome. V8 therefore emphasizes fail-fast preflight, explicit environment provenance, cleanup of stale transport flags, resumable phases, raw evidence retention and strict post-run coverage validation.
