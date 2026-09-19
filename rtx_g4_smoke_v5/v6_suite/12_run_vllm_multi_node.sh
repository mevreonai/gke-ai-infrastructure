#!/usr/bin/env bash
# Orchestrate Ray per topology so TP4/PP2 is guaranteed to span nodes.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CONFIG_CANDIDATES=("$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env")
for f in "${CONFIG_CANDIDATES[@]}"; do if [[ -f "$f" ]]; then source "$f"; break; fi; done
: "${NODE0_IP:?NODE0_IP missing; run 00_init_gcp_config.sh or provide RUN_CONFIG.env}"
: "${NODE1_IP:?NODE1_IP missing; multi-node run requires node1}"
: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${CASES_FILE:=$SCRIPT_DIR/10b_vllm_multi_node_cases.json}"
: "${OUT_ROOT:=$HOME/v5_profiling/results/$(date +%Y%m%d_%H%M%S)/$(hostname -s)/vllm_multi_node}"
mkdir -p "$OUT_ROOT"
source "$VENV_DIR/bin/activate"

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
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$SCRIPT_DIR/09_metrics_sampler.py" "$NODE1_IP:/tmp/v5_metrics_sampler.py"

for row in "${CASE_ROWS[@]}"; do
  IFS='|' read -r CASE GPUS <<<"$row"
  echo "==== CASE=$CASE ray_gpus_per_node=$GPUS ===="
  GPU_LIST=$(python3 - <<PY
print(','.join(str(i) for i in range(int('$GPUS'))))
PY
)
  ray stop -f || true
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "source '$VENV_DIR/bin/activate'; ray stop -f || true"

  CUDA_VISIBLE_DEVICES="$GPU_LIST" ray start --head --node-ip-address="$NODE0_IP" --port=6379 --num-gpus="$GPUS"
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" \
    "source '$VENV_DIR/bin/activate'; CUDA_VISIBLE_DEVICES='$GPU_LIST' ray start --address='$NODE0_IP:6379' --num-gpus='$GPUS'"
  sleep 8
  ray status | tee "$OUT_ROOT/${CASE}_ray_status_before.log"
  export CUDA_VISIBLE_DEVICES="$GPU_LIST"
  python3 "$SCRIPT_DIR/12_run_vllm_multi_node.py" --cases "$CASES_FILE" --out "$OUT_ROOT/$CASE" --case "$CASE" --node1-ip "$NODE1_IP" --ssh-key "$SSH_KEY"

  ray stop -f || true
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "source '$VENV_DIR/bin/activate'; ray stop -f || true"
done

echo "Multi-node results: $OUT_ROOT"
