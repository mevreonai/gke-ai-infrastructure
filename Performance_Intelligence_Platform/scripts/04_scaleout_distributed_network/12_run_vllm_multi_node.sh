#!/usr/bin/env bash
# Enterprise Platform: V6-aligned Ray orchestration with explicit local-P2P/SHM protection.
# TP4/PP2 is guaranteed to span nodes with rock-solid Ray initialization.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/20_nccl_policy.sh"
PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE=${PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE:-}
V8_GCP_NETWORK_PROVENANCE_OVERRIDE=${V8_GCP_NETWORK_PROVENANCE_OVERRIDE:-$PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE}
CALLER_TOPO="${TOPOLOGY_SELECTION:-}"
CALLER_BW="${NETWORK_BANDWIDTH_SELECTION:-}"
CALLER_NET_MODE="${V8_VLLM_NETWORK_MODE:-}"
CALLER_NET_CAP="${V8_VLLM_NETWORK_CAP_GBPS:-}"
CALLER_PROV="${V8_GCP_NETWORK_PROVENANCE_OVERRIDE:-$PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE}"
CALLER_SKIP_OPS="${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-}"
CALLER_CASES="${CASES_FILE:-}"
CALLER_OUT_ROOT="${OUT_ROOT:-}"
CALLER_PP_SPLIT="${VLLM_PP_LAYER_PARTITION:-}"
CALLER_NODE0="${NODE0_IP:-}"
CALLER_NODE1="${NODE1_IP:-}"
CALLER_SSH_KEY="${SSH_KEY:-}"
CALLER_VENV_DIR="${VENV_DIR:-}"
CALLER_MODEL="${MODEL:-}"
CALLER_REVISION="${REVISION:-}"

CONFIG_CANDIDATES=("$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env" "$HOME/v8_additional_runs_suite/RUN_CONFIG.env")
for f in "${CONFIG_CANDIDATES[@]}"; do if [[ -f "$f" ]]; then source "$f"; break; fi; done

# Caller overrides and clean environment invariants take precedence over sourced defaults
[[ -n "$CALLER_TOPO" ]] && export TOPOLOGY_SELECTION="$CALLER_TOPO"
[[ -n "$CALLER_BW" ]] && export NETWORK_BANDWIDTH_SELECTION="$CALLER_BW"
[[ -n "$CALLER_NET_MODE" ]] && export V8_VLLM_NETWORK_MODE="$CALLER_NET_MODE"
[[ -n "$CALLER_NET_CAP" ]] && export V8_VLLM_NETWORK_CAP_GBPS="$CALLER_NET_CAP"
[[ -n "$CALLER_PROV" ]] && export V8_GCP_NETWORK_PROVENANCE_OVERRIDE="$CALLER_PROV"
[[ -n "$CALLER_SKIP_OPS" ]] && export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="$CALLER_SKIP_OPS"
[[ -n "$CALLER_CASES" ]] && export CASES_FILE="$CALLER_CASES"
[[ -n "$CALLER_OUT_ROOT" ]] && export OUT_ROOT="$CALLER_OUT_ROOT"
[[ -n "$CALLER_NODE0" ]] && export NODE0_IP="$CALLER_NODE0"
[[ -n "$CALLER_NODE1" ]] && export NODE1_IP="$CALLER_NODE1"
[[ -n "$CALLER_SSH_KEY" ]] && export SSH_KEY="$CALLER_SSH_KEY"
[[ -n "$CALLER_VENV_DIR" ]] && export VENV_DIR="$CALLER_VENV_DIR"
[[ -n "$CALLER_MODEL" ]] && export MODEL="$CALLER_MODEL"
[[ -n "$CALLER_REVISION" ]] && export REVISION="$CALLER_REVISION"
unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL VLLM_PP_LAYER_PARTITION 2>/dev/null || true
[[ -n "$CALLER_PP_SPLIT" ]] && export VLLM_PP_LAYER_PARTITION="$CALLER_PP_SPLIT"

if [[ -n "$V8_GCP_NETWORK_PROVENANCE_OVERRIDE" ]]; then export GCP_NETWORK_PROVENANCE="$V8_GCP_NETWORK_PROVENANCE_OVERRIDE"; fi
: "${NODE0_IP:?NODE0_IP missing; run 00_init_gcp_config.sh or provide RUN_CONFIG.env}"
: "${NODE1_IP:?NODE1_IP missing; multi-node run requires node1}"
: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${CASES_FILE:=$SCRIPT_DIR/10b_vllm_multi_node_cases.json}"
: "${OUT_ROOT:=$HOME/v5_profiling/results/$(date +%Y%m%d_%H%M%S)/$(hostname -s)/vllm_multi_node}"
mkdir -p "$OUT_ROOT"
source "$VENV_DIR/bin/activate"

# Export FlashInfer autotune skips to prevent Triton MoE hang (empty value skips nothing)
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2}"

# Preserve cross-node Socket-network workaround, protect local P2P/SHM within each node
nccl_multi_node_v6_aligned_env
if [[ -z "${NCCL_SOCKET_IFNAME:-}" ]]; then
  _local_if=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
  _remote_if=$(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'")
  [[ -n "$_local_if" && "$_local_if" == "$_remote_if" ]] || { echo "ERROR: peer interface discovery mismatch: local=$_local_if remote=$_remote_if" >&2; exit 3; }
  export NCCL_SOCKET_IFNAME="=$_local_if"
fi
nccl_capture_env "$OUT_ROOT/NCCL_ENV_BEFORE_MULTI_NODE.txt"
REMOTE_V6_ENV="$(nccl_remote_v6_aligned_exports)"

SELECT_MODE="qualification"
if [[ ${1:-} == "--all" ]]; then SELECT_MODE="all"; shift; fi
if [[ ${1:-} == "--group" ]]; then SELECT_MODE="$2"; shift 2; fi
if [[ ${1:-} == "--case" ]]; then SELECT_MODE="case:$2"; shift 2; fi

mapfile -t CASE_ROWS < <(python3 - "$CASES_FILE" "$SELECT_MODE" <<'PY'
import json,sys,os
cfg=json.load(open(sys.argv[1])); sel=sys.argv[2]
raw_cases = cfg['cases']
if isinstance(raw_cases, dict):
    raw_cases = list(raw_cases.values())
topo_sel = os.environ.get('TOPOLOGY_SELECTION', 'all')
topos = [t.strip().lower() for t in topo_sel.split(',')] if (topo_sel and topo_sel != 'all') else []
for c in raw_cases:
    ok = sel=='all' or (sel.startswith('case:') and c['name']==sel.split(':',1)[1]) or (not sel.startswith('case:') and sel in c.get('groups',[]))
    if not ok:
        continue
    if topos:
        derived_topo = f"tp{c.get('tp')}_pp{c.get('pp')}".lower() if ('tp' in c and 'pp' in c) else ''
        c_tags = [derived_topo, str(c.get('topology', '')).lower(), str(c.get('name', '')).lower()] + [g.lower() for g in c.get('groups', [])]
        matched = False
        for t in topos:
            if any(t == tag or t in tag or tag in t for tag in c_tags if tag):
                matched = True; break
            if t in ('tp16', 'tp16_pp1') and (derived_topo == 'tp16_pp1' or 'tp16' in c['name']):
                matched = True; break
            if t in ('pp4', 'tp4_pp4') and (derived_topo == 'tp4_pp4' or 'pp4' in c['name']):
                matched = True; break
            if t == 'multi_node' and ('multi_node' in c_tags or c.get('ray_gpus_per_node', 8) > 0):
                matched = True; break
        if not matched:
            continue
    print(f"{c['name']}|{c.get('ray_gpus_per_node',8)}")
PY
)
[[ ${#CASE_ROWS[@]} -gt 0 ]] || { echo "No multi-node cases selected"; exit 2; }

# Ensure the remote worker has the exact metrics sampler used by this bundle.
scp -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$SCRIPT_DIR/09_metrics_sampler.py" "$NODE1_IP:/tmp/v5_metrics_sampler.py"

stop_ray_both() {
  ray stop -f >/dev/null 2>&1 || true
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; ray stop -f >/dev/null 2>&1 || true" || true
}
trap stop_ray_both EXIT INT TERM

FAILED_CASES=()

for row in "${CASE_ROWS[@]}"; do
  IFS='|' read -r CASE GPUS <<<"$row"
  echo "==== CASE=$CASE ray_gpus_per_node=$GPUS ===="
  GPU_LIST=$(python3 - <<PY
print(','.join(str(i) for i in range(int('$GPUS'))))
PY
)
  # Stop Ray cleanly and allow port 6379 to clear TIME_WAIT
  stop_ray_both
  sleep 4

  PP_EXPORT=""
  if [[ -n "${VLLM_PP_LAYER_PARTITION:-}" ]]; then
    PP_EXPORT="export VLLM_PP_LAYER_PARTITION='$VLLM_PP_LAYER_PARTITION'; "
  fi

  eval "${PP_EXPORT}CUDA_VISIBLE_DEVICES='$GPU_LIST' ray start --head --node-ip-address='$NODE0_IP' --port=6379 --num-gpus='$GPUS'"
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" \
    "$REMOTE_V6_ENV $PP_EXPORT unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; CUDA_VISIBLE_DEVICES='$GPU_LIST' ray start --address='$NODE0_IP:6379' --num-gpus='$GPUS'"
  sleep 8
  ray status | tee "$OUT_ROOT/${CASE}_ray_status_before.log"
  # Audit actual Ray-worker environments on every live node before vLLM actors are created.
  nccl_capture_env "$OUT_ROOT/${CASE}_NCCL_ENV_NODE0_BEFORE_RAY_WORKERS.txt"
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" \
    "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; env | LC_ALL=C sort | grep '^NCCL_' || true" \
    > "$OUT_ROOT/${CASE}_NCCL_ENV_NODE1_SHELL_BEFORE_RAY_WORKERS.txt"
  python3 "$SCRIPT_DIR/20_ray_nccl_env_audit.py" --out "$OUT_ROOT/${CASE}_RAY_NCCL_ENV_AUDIT.json" --expected-nodes 2
  export CUDA_VISIBLE_DEVICES="$GPU_LIST"

  set +e
  python3 "$SCRIPT_DIR/12_run_vllm_multi_node.py" --cases "$CASES_FILE" --out "$OUT_ROOT/$CASE" --case "$CASE" --node1-ip "$NODE1_IP" --ssh-key "$SSH_KEY"
  CASE_RC=$?
  set -e
  if [[ $CASE_RC -ne 0 ]]; then
    echo "WARNING: Multi-node case $CASE failed with rc=$CASE_RC; recording failure and continuing..."
    FAILED_CASES+=("$CASE")
  fi

  stop_ray_both
done

echo "Multi-node results: $OUT_ROOT"
if [[ ${#FAILED_CASES[@]} -gt 0 ]]; then
  echo "ERROR: Failed multi-node cases: ${FAILED_CASES[*]}" >&2
  exit 1
fi
