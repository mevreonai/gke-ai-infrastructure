#!/usr/bin/env bash
# V8-FULL: V6-aligned Ray orchestration with explicit local-P2P/SHM protection.
# TP4/PP2 is guaranteed to span nodes.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/20_nccl_policy.sh"
V8_GCP_NETWORK_PROVENANCE_OVERRIDE=${V8_GCP_NETWORK_PROVENANCE_OVERRIDE:-}
CONFIG_CANDIDATES=("$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env")
for f in "${CONFIG_CANDIDATES[@]}"; do if [[ -f "$f" ]]; then source "$f"; break; fi; done
if [[ -n "$V8_GCP_NETWORK_PROVENANCE_OVERRIDE" ]]; then export GCP_NETWORK_PROVENANCE="$V8_GCP_NETWORK_PROVENANCE_OVERRIDE"; fi
: "${NODE0_IP:?NODE0_IP missing; run 00_init_gcp_config.sh or provide RUN_CONFIG.env}"
: "${NODE1_IP:?NODE1_IP missing; multi-node run requires node1}"
: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${CASES_FILE:=$SCRIPT_DIR/10b_vllm_multi_node_cases.json}"
: "${OUT_ROOT:=$HOME/v5_profiling/results/$(date +%Y%m%d_%H%M%S)/$(hostname -s)/vllm_multi_node}"
mkdir -p "$OUT_ROOT"
source "$VENV_DIR/bin/activate"
# Preserve V6 cross-node Socket-network workaround if configured, but never disable
# local GPU P2P/SHM within either node.
nccl_multi_node_v6_aligned_env
# Direct invocations (outside 20_run_vllm_network_matrix.sh) still bind NCCL Socket
# to the peer-facing interface.  Network-matrix callers already provide this.
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
import json,sys
cfg=json.load(open(sys.argv[1])); sel=sys.argv[2]
for c in cfg['cases']:
    ok = sel=='all' or (sel.startswith('case:') and c['name']==sel.split(':',1)[1]) or (not sel.startswith('case:') and sel in c.get('groups',[]))
    if ok: print(f"{c['name']}|{c.get('ray_gpus_per_node',8)}")
PY
)
[[ ${#CASE_ROWS[@]} -gt 0 ]] || { echo "No multi-node cases selected"; exit 2; }

# Ensure the remote worker has the exact metrics sampler used by this bundle.
scp -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$SCRIPT_DIR/09_metrics_sampler.py" "$NODE1_IP:/tmp/v5_metrics_sampler.py"

for row in "${CASE_ROWS[@]}"; do
  IFS='|' read -r CASE GPUS <<<"$row"
  echo "==== CASE=$CASE ray_gpus_per_node=$GPUS ===="
  GPU_LIST=$(python3 - <<PY
print(','.join(str(i) for i in range(int('$GPUS'))))
PY
)
  ray stop -f || true
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; ray stop -f || true"

  CUDA_VISIBLE_DEVICES="$GPU_LIST" ray start --head --node-ip-address="$NODE0_IP" --port=6379 --num-gpus="$GPUS"
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" \
    "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; CUDA_VISIBLE_DEVICES='$GPU_LIST' ray start --address='$NODE0_IP:6379' --num-gpus='$GPUS'"
  sleep 8
  ray status | tee "$OUT_ROOT/${CASE}_ray_status_before.log"
  # Audit actual Ray-worker environments on every live node before vLLM actors are created.
  nccl_capture_env "$OUT_ROOT/${CASE}_NCCL_ENV_NODE0_BEFORE_RAY_WORKERS.txt"
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" \
    "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; env | LC_ALL=C sort | grep '^NCCL_' || true" \
    > "$OUT_ROOT/${CASE}_NCCL_ENV_NODE1_SHELL_BEFORE_RAY_WORKERS.txt"
  python3 "$SCRIPT_DIR/20_ray_nccl_env_audit.py" --out "$OUT_ROOT/${CASE}_RAY_NCCL_ENV_AUDIT.json" --expected-nodes 2
  export CUDA_VISIBLE_DEVICES="$GPU_LIST"
  python3 "$SCRIPT_DIR/12_run_vllm_multi_node.py" --cases "$CASES_FILE" --out "$OUT_ROOT/$CASE" --case "$CASE" --node1-ip "$NODE1_IP" --ssh-key "$SSH_KEY"

  ray stop -f || true
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; ray stop -f || true"
done

echo "Multi-node results: $OUT_ROOT"
