#!/usr/bin/env bash
# Run an arbitrary command with the V6 single-node NCCL environment policy:
# no NCCL_* overrides are inherited. This matches the actual V6 qualification manifest.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/20_nccl_policy.sh"
target_log="${NCCL_POLICY_LOG:-}"
nccl_single_node_v6_aligned_env
if [[ -n "$target_log" ]]; then nccl_capture_env "$target_log"; fi
exec "$@"
