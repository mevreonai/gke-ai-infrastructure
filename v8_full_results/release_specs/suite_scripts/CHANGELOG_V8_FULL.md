# V8-FULL changes from V7-FULL

## Transport correctness

- Re-audited the exact V6 source and actual V6 qualification manifest.
- Confirmed V6 single-node qualification did not use `NCCL_P2P_DISABLE`, `NCCL_SHM_DISABLE`, or `NCCL_P2P_LEVEL`.
- Explicitly documented that the older 2026-09-15 local NCCL hardware run *did* force `NCCL_P2P_DISABLE=1` and `NCCL_SHM_DISABLE=1`.
- Added `20_nccl_policy.sh` and a single-node wrapper that removes all `NCCL_*` overrides before native single-node vLLM.
- Native local hardware NCCL now removes all `NCCL_*` overrides before primary measurements.
- Multi-node Ray/vLLM explicitly clears P2P/SHM forcing while retaining configured GCP Socket-network settings.
- Added runtime `NCCL_ENV*.txt` capture and final `NCCL_POLICY_AUDIT.json`.

## vLLM network matrix

- Added full scale-out vLLM execution under exactly:
  - `GCP_NATIVE`
  - `GCP_CAPPED_100G`
  - `GCP_CAPPED_20G`
- Keeps the full Native/100G/50G/20G/10G hardware/NCCL sensitivity sweep; 50G and 10G are not used for vLLM model runs.
- Adds qdisc state, forward/reverse iperf and explicit network provenance before each model run.
- Reconciles coverage by network provenance so repeated case/bench names cannot overwrite one another.

## Profiling

- Retains full native distributed profile matrix.
- Adds matched 128K prefill profiles for all four topologies at 100G and 20G.
- Captures network provenance and configured cap in profile manifests.

## Validation/output

- New network-aware final collector.
- New `SCALEOUT_NETWORK_COVERAGE.md`.
- New `V6_ALIGNMENT_EVIDENCE.json`.
- Static validator expanded to enforce P2P/SHM policy and exact network-mode coverage.

## V8-FULL release hardening

- Added `22_v8_readiness.py` on both nodes before long GPU work; exact successful V6 core-stack versions are enforced by default.
- Added Ray-worker NCCL environment symmetry audit across every live node, including allowed NCCL network settings and `LD_LIBRARY_PATH`.
- Propagates the V6-aligned multi-node NCCL network environment to the remote Ray node while always removing P2P/SHM/P2P-level forcing.
- Auto-discovers and validates the peer-facing interface, then pins `NCCL_SOCKET_IFNAME` consistently across nodes.
- Expanded hardware network coverage so forward/reverse iperf, NCCL SendRecv, and TP2/TP8/TP16 cross-node all-reduce run at Native/100G/50G/20G/10G.
- Added strict both-node telemetry validation for every completed distributed vLLM result.
- Hardware tool preparation reuses existing known-good binaries by default (`V8_REBUILD_HW_TOOLS=0`) and rebuilds only when missing or explicitly requested.
- Result packaging now includes the file inventory before archive creation and carries the release/source hash manifest into the run evidence.
- Final vLLM scale-out network matrix is **Native / 100G / 20G**; 10G is hardware-smoke only.
