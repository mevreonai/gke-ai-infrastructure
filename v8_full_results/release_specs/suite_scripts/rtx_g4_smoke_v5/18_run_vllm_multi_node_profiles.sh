#!/usr/bin/env bash
# V8-FULL targeted distributed Nsight Systems profiling.
# Primary path uses vLLM's official --ray-workers-use-nsight integration, while
# Ray cluster formation remains identical to the already-working V6 multi-node path.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/20_nccl_policy.sh"
V8_GCP_NETWORK_PROVENANCE_OVERRIDE=${V8_GCP_NETWORK_PROVENANCE_OVERRIDE:-}
for f in "$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env"; do [[ -f "$f" ]] && { source "$f"; break; }; done
if [[ -n "$V8_GCP_NETWORK_PROVENANCE_OVERRIDE" ]]; then export GCP_NETWORK_PROVENANCE="$V8_GCP_NETWORK_PROVENANCE_OVERRIDE"; fi
: "${NODE0_IP:?NODE0_IP missing}"
: "${NODE1_IP:?NODE1_IP missing}"
: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${PROFILE_MATRIX:=$SCRIPT_DIR/18_multi_node_profile_matrix.json}"
: "${OUT_ROOT:=$HOME/v8_full_results/$(date +%Y%m%d_%H%M%S)/profiles_multi_node}"
: "${RUN_HEAVY_PROFILE:=1}"
: "${PROFILE_TOPOLOGY_FILTER:=}"
: "${PROFILE_MODE_FILTER:=}"
mkdir -p "$OUT_ROOT"
source "$VENV_DIR/bin/activate"
nccl_multi_node_v6_aligned_env
nccl_capture_env "$OUT_ROOT/NCCL_ENV_BEFORE_PROFILES.txt"
command -v nsys >/dev/null || { echo "ERROR: nsys missing on node0"; exit 2; }
command -v ray >/dev/null || { echo "ERROR: ray missing on node0"; exit 2; }
command -v vllm >/dev/null || { echo "ERROR: vllm missing on node0"; exit 2; }
SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
SCP=(scp -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
REMOTE_IFACE=$("${SSH[@]}" "$NODE1_IP" "ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'")
[[ -n "$LOCAL_IFACE" && "$LOCAL_IFACE" == "$REMOTE_IFACE" ]] || { echo "ERROR: interface discovery mismatch: local=$LOCAL_IFACE remote=$REMOTE_IFACE"; exit 2; }
export NCCL_SOCKET_IFNAME="=$LOCAL_IFACE"
nccl_multi_node_v6_aligned_env
nccl_capture_env "$OUT_ROOT/NCCL_ENV_BEFORE_PROFILES.txt"
REMOTE_V6_ENV="$(nccl_remote_v6_aligned_exports)"
"${SSH[@]}" "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; command -v nsys; command -v ray; command -v vllm" >/dev/null || { echo "ERROR: nsys/ray/vllm missing on node1"; exit 2; }

# Require the official vLLM/Ray worker Nsight integration for the primary profile path.
if ! (vllm serve --help=all 2>&1 || vllm serve --help 2>&1) | grep -q -- '--ray-workers-use-nsight'; then
  echo "ERROR: installed vLLM does not expose --ray-workers-use-nsight"; exit 2
fi
if ! (vllm bench serve --help=all 2>&1 || vllm bench serve --help 2>&1) | grep -q -- '--profile'; then
  echo "ERROR: installed vLLM bench serve does not expose --profile"; exit 2
fi

"${SCP[@]}" "$SCRIPT_DIR/09_metrics_sampler.py" "$NODE1_IP:/tmp/v5_metrics_sampler.py"
mapfile -t ROWS < <(python3 - "$PROFILE_MATRIX" "$RUN_HEAVY_PROFILE" <<'PYM'
import json,sys,os
m=json.load(open(sys.argv[1])); heavy=sys.argv[2]=='1'
topo=os.environ.get('PROFILE_TOPOLOGY_FILTER','').strip(); mode=os.environ.get('PROFILE_MODE_FILTER','').strip()
for p in m['profiles']:
    if p.get('optional_heavy') and not heavy: continue
    if topo and p['topology'] != topo: continue
    if mode and p['mode'] != mode: continue
    print('|'.join(map(str,[p['topology'],p['tp'],p['pp'],p['ray_gpus_per_node'],p['mode'],p['input'],p['output'],p['concurrency'],p['prompts']])))
PYM
)

stop_ray_both(){
  ray stop -f >/dev/null 2>&1 || true
  "${SSH[@]}" "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; ray stop -f >/dev/null 2>&1 || true" || true
}
trap stop_ray_both EXIT

for ROW in "${ROWS[@]}"; do
  IFS='|' read -r TOPO TP PP GPUS MODE INPUT OUTPUT CONC PROMPTS <<<"$ROW"
  ID="${TOPO}_${MODE}"
  DIR="$OUT_ROOT/$TOPO/$MODE"; mkdir -p "$DIR/node0_capture" "$DIR/node1_capture"
  GPU_LIST=$(python3 - <<PYG
print(','.join(str(i) for i in range(int('$GPUS'))))
PYG
)
  echo "===== DISTRIBUTED PROFILE $ID TP=$TP PP=$PP GPUs/node=$GPUS =====" | tee "$DIR/PROFILE_START.txt"
  stop_ray_both

  # Provenance before cluster start.
  nsys --version > "$DIR/node0_nsys_version.txt" 2>&1 || true
  nvidia-smi topo -m > "$DIR/node0_topology.txt" 2>&1 || true
  nvidia-smi --query-gpu=index,uuid,name,memory.total,pci.bus_id --format=csv > "$DIR/node0_gpu_inventory.csv" 2>&1 || true
  ip -br addr > "$DIR/node0_network.txt" 2>&1 || true
  "${SSH[@]}" "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; nsys --version; echo ===TOPO===; nvidia-smi topo -m; echo ===GPU===; nvidia-smi --query-gpu=index,uuid,name,memory.total,pci.bus_id --format=csv; echo ===NET===; ip -br addr" > "$DIR/node1_provenance.txt" 2>&1 || true

  # V6-compatible Ray formation: same commands and GPU visibility strategy.
  CUDA_VISIBLE_DEVICES="$GPU_LIST" ray start --head --node-ip-address="$NODE0_IP" --port=6379 --num-gpus="$GPUS" > "$DIR/ray_start_node0.log" 2>&1
  "${SSH[@]}" "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; CUDA_VISIBLE_DEVICES='$GPU_LIST' ray start --address='$NODE0_IP:6379' --num-gpus='$GPUS'" > "$DIR/ray_start_node1.log" 2>&1
  sleep 8
  ray status > "$DIR/ray_status_before_profile.log" 2>&1 || { echo "Ray status failed"; exit 3; }
  # Fail before profiling if any Ray worker inherited legacy local-transport forcing.
  nccl_capture_env "$DIR/NCCL_ENV_NODE0_BEFORE_RAY_WORKERS.txt"
  "${SSH[@]}" "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; env | LC_ALL=C sort | grep '^NCCL_' || true" > "$DIR/NCCL_ENV_NODE1_SHELL_BEFORE_RAY_WORKERS.txt"
  python3 "$SCRIPT_DIR/20_ray_nccl_env_audit.py" --out "$DIR/RAY_NCCL_ENV_AUDIT.json" --expected-nodes 2
  ray list nodes --detail > "$DIR/ray_nodes_before_profile.log" 2>&1 || true
  ray list placement-groups --detail > "$DIR/ray_pg_before_profile.log" 2>&1 || true

  # Record current Ray session paths; vLLM's --ray-workers-use-nsight writes worker reports below logs/nsight.
  NODE0_SESSION=$(readlink -f /tmp/ray/session_latest 2>/dev/null || true)
  NODE1_SESSION=$("${SSH[@]}" "$NODE1_IP" "readlink -f /tmp/ray/session_latest 2>/dev/null || true")
  printf '%s\n' "$NODE0_SESSION" > "$DIR/node0_ray_session.txt"
  printf '%s\n' "$NODE1_SESSION" > "$DIR/node1_ray_session.txt"

  set +e
  python3 "$SCRIPT_DIR/18_run_vllm_multi_node_profile_case.py" \
    --topology "$TOPO" --tp "$TP" --pp "$PP" --ray-gpus-per-node "$GPUS" \
    --mode "$MODE" --input "$INPUT" --output "$OUTPUT" --concurrency "$CONC" --prompts "$PROMPTS" \
    --out "$DIR/workload" --node1-ip "$NODE1_IP" --ssh-key "$SSH_KEY"
  CASE_RC=$?
  set -e
  echo "$CASE_RC" > "$DIR/workload_exit_code.txt"

  # Give Ray/vLLM worker actors time to flush .nsys-rep after server teardown.
  sleep 5
  if [[ -n "$NODE0_SESSION" && -d "$NODE0_SESSION/logs/nsight" ]]; then
    cp -a "$NODE0_SESSION/logs/nsight/." "$DIR/node0_capture/" || true
  fi
  if [[ -n "$NODE1_SESSION" ]]; then
    "${SCP[@]}" -r "$NODE1_IP:$NODE1_SESSION/logs/nsight/." "$DIR/node1_capture/" >/dev/null 2>&1 || true
  fi
  # Preserve Ray worker logs too; they are useful when Nsight fails before producing a report.
  if [[ -n "$NODE0_SESSION" && -d "$NODE0_SESSION/logs" ]]; then
    find "$NODE0_SESSION/logs" -maxdepth 1 -type f \( -name '*worker*' -o -name '*raylet*' \) -size -32M -print0 2>/dev/null | xargs -0 -r cp -t "$DIR/node0_capture/" || true
  fi
  if [[ -n "$NODE1_SESSION" ]]; then
    "${SSH[@]}" "$NODE1_IP" "cd '$NODE1_SESSION/logs' 2>/dev/null && tar -czf /tmp/v8full_${ID}_raylogs.tgz \$(find . -maxdepth 1 -type f \( -name '*worker*' -o -name '*raylet*' \) -size -32M -printf '%P ' 2>/dev/null) 2>/dev/null || true"
    "${SCP[@]}" "$NODE1_IP:/tmp/v8full_${ID}_raylogs.tgz" "$DIR/node1_capture/" >/dev/null 2>&1 || true
  fi

  stop_ray_both
  python3 "$SCRIPT_DIR/19_postprocess_nsys.py" "$DIR" --out "$DIR/NSYS_ANALYSIS.json" || true
  python3 - "$DIR" "$CASE_RC" <<'PYV'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); rc=int(sys.argv[2])
m={}; mp=p/'workload/PROFILE_CASE_MANIFEST.json'
if mp.exists(): m=json.load(open(mp))
node0=list((p/'node0_capture').rglob('*.nsys-rep'))
node1=list((p/'node1_capture').rglob('*.nsys-rep'))
checks={
 'workload_completed': rc==0 and m.get('status')=='COMPLETED',
 'node0_nsys_report': len(node0)>0,
 'node1_nsys_report': len(node1)>0,
 'bench_json': (p/'workload/bench.json').exists(),
 'node0_metrics': (p/'workload/metrics_node0.jsonl').exists(),
 'node1_metrics': (p/'workload/metrics_node1.jsonl').exists(),
}
result={'profile_dir':str(p),'checks':checks,'complete':all(checks.values()),
        'node0_report_count':len(node0),'node1_report_count':len(node1),
        'guardrail':'Complete means required raw artifacts exist. It does not by itself establish request critical-path causality.'}
(p/'PROFILE_VALIDATION.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
PYV
  [[ "$CASE_RC" == 0 ]] || echo "WARN: workload failed for $ID; raw evidence retained" | tee -a "$DIR/PROFILE_START.txt"
done
trap - EXIT
stop_ray_both
echo "Distributed profile results: $OUT_ROOT"
