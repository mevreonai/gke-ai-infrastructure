#!/usr/bin/env bash
# V8-FULL NCCL environment policy.
#
# V6 alignment facts:
# - V6 single-node qualification manifest captured no NCCL_* variables.
# - V6 source never set NCCL_P2P_DISABLE/NCCL_SHM_DISABLE/NCCL_P2P_LEVEL.
# - Multi-node GCP may retain the V6 Socket net-plugin workaround (NCCL_NET=Socket),
#   but must never disable local P2P or SHM inside a node.
set -o pipefail

nccl_clear_all_for_single_node() {
  local v
  while IFS= read -r v; do
    [[ -n "$v" ]] && unset "$v" || true
  done < <(compgen -v | grep '^NCCL_' || true)
}

nccl_clear_local_forcing_only() {
  unset NCCL_P2P_DISABLE || true
  unset NCCL_SHM_DISABLE || true
  unset NCCL_P2P_LEVEL || true
}

nccl_assert_no_local_forcing() {
  local bad=0 v
  for v in NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; do
    if [[ -n "${!v+x}" ]]; then
      echo "ERROR: forbidden native NCCL override present: $v=${!v}" >&2
      bad=1
    fi
  done
  [[ "$bad" == 0 ]]
}

nccl_capture_env() {
  local out=${1:?output path required}
  mkdir -p "$(dirname "$out")"
  {
    echo "timestamp=$(date --iso-8601=seconds)"
    env | LC_ALL=C sort | grep '^NCCL_' || true
  } > "$out"
}

nccl_single_node_v6_aligned_env() {
  nccl_clear_all_for_single_node
  nccl_assert_no_local_forcing
}

nccl_multi_node_v6_aligned_env() {
  # Preserve V6 network-specific settings such as NCCL_NET=Socket / NCCL_SOCKET_IFNAME
  # if RUN_CONFIG.env provides them, but guarantee local GPU IPC paths are not disabled.
  nccl_clear_local_forcing_only
  nccl_assert_no_local_forcing
}

# Emit shell exports that can be prepended to an SSH command before starting a
# remote Ray process.  All currently configured NCCL_* variables are propagated
# except the three local-transport forcing variables, which are always omitted.
# LD_LIBRARY_PATH is propagated because the proven GCP/V6 Socket workaround uses
# /tmp/clean_nccl_libs on both hosts.
nccl_remote_v6_aligned_exports() {
  local v value q
  for v in $(compgen -v | grep '^NCCL_' | LC_ALL=C sort || true); do
    case "$v" in
      NCCL_P2P_DISABLE|NCCL_SHM_DISABLE|NCCL_P2P_LEVEL) continue ;;
    esac
    value=${!v}
    printf -v q '%q' "$value"
    printf 'export %s=%s; ' "$v" "$q"
  done
  if [[ -n "${LD_LIBRARY_PATH+x}" ]]; then
    printf -v q '%q' "$LD_LIBRARY_PATH"
    printf 'export LD_LIBRARY_PATH=%s; ' "$q"
  fi
}
