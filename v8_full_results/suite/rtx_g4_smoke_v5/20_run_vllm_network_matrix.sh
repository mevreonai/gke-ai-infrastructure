#!/usr/bin/env bash
# V8-FULL vLLM scale-out network sensitivity matrix.
# Required vLLM modes by default: GCP_NATIVE, GCP_CAPPED_100G, GCP_CAPPED_20G.
# Intermediate bandwidth caps remain in the cheaper hardware/NCCL sweep only.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/20_nccl_policy.sh"
for f in "$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env"; do
  [[ -f "$f" ]] && { source "$f"; break; }
done
: "${NODE0_IP:?NODE0_IP missing}"
: "${NODE1_IP:?NODE1_IP missing}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${VENV_DIR:=$HOME/vllm_env}"
: "${CASES_FILE:=$SCRIPT_DIR/10b_vllm_multi_node_cases.json}"
: "${OUT_ROOT:=$HOME/v8_full_results/$(date +%Y%m%d_%H%M%S)/vllm_scaleout_network_matrix}"
: "${VLLM_NETWORK_MODES:=native 100g 20g}"
: "${V8_REQUIRE_CAPS:=1}"
mkdir -p "$OUT_ROOT"
source "$VENV_DIR/bin/activate"
nccl_multi_node_v6_aligned_env
SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)

LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
REMOTE_IFACE=$("${SSH[@]}" "$NODE1_IP" "ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'")
[[ -n "$LOCAL_IFACE" && -n "$REMOTE_IFACE" ]] || { echo "ERROR: peer interface discovery failed"; exit 2; }
[[ "$LOCAL_IFACE" == "$REMOTE_IFACE" ]] || { echo "ERROR: interface names differ ($LOCAL_IFACE vs $REMOTE_IFACE)"; exit 2; }
export NCCL_SOCKET_IFNAME="=$LOCAL_IFACE"
PHYSICAL_PROVENANCE=${GCP_NETWORK_PROVENANCE:-GCP_UNSPECIFIED}

cleanup_caps(){
  sudo -n tc qdisc del dev "$LOCAL_IFACE" root 2>/dev/null || true
  "${SSH[@]}" "$NODE1_IP" "sudo -n tc qdisc del dev '$REMOTE_IFACE' root 2>/dev/null || true" >/dev/null 2>&1 || true
}
apply_cap(){
  local rate=$1
  sudo -n tc qdisc replace dev "$LOCAL_IFACE" root handle 1: htb default 10
  sudo -n tc class replace dev "$LOCAL_IFACE" parent 1: classid 1:10 htb rate "${rate}gbit" ceil "${rate}gbit"
  "${SSH[@]}" "$NODE1_IP" "sudo -n tc qdisc replace dev '$REMOTE_IFACE' root handle 1: htb default 10 && sudo -n tc class replace dev '$REMOTE_IFACE' parent 1: classid 1:10 htb rate '${rate}gbit' ceil '${rate}gbit'"
}
record_net_state(){
  local dir=$1
  mkdir -p "$dir"
  ip route get "$NODE1_IP" > "$dir/node0_route.txt" 2>&1 || true
  ip -s link show dev "$LOCAL_IFACE" > "$dir/node0_link.txt" 2>&1 || true
  sudo -n tc -s qdisc show dev "$LOCAL_IFACE" > "$dir/node0_qdisc.txt" 2>&1 || true
  sudo -n tc -s class show dev "$LOCAL_IFACE" > "$dir/node0_class.txt" 2>&1 || true
  "${SSH[@]}" "$NODE1_IP" "ip route get '$NODE0_IP'; ip -s link show dev '$REMOTE_IFACE'; sudo -n tc -s qdisc show dev '$REMOTE_IFACE' 2>/dev/null || true; sudo -n tc -s class show dev '$REMOTE_IFACE' 2>/dev/null || true" > "$dir/node1_network_state.txt" 2>&1 || true
  nccl_capture_env "$dir/NCCL_ENV.txt"
}
verify_iperf(){
  local dir=$1 cap=${2:-0}
  "${SSH[@]}" "$NODE1_IP" "pkill -x iperf3 2>/dev/null || true; iperf3 -s -D"
  iperf3 -c "$NODE1_IP" -t 10 -P 16 -J > "$dir/iperf_forward.json"
  iperf3 -c "$NODE1_IP" -t 10 -P 16 -R -J > "$dir/iperf_reverse.json" || true
  python3 - "$dir/iperf_forward.json" "$cap" "$dir/IPERF_VALIDATION.json" <<'PYV'
import json,sys
src,cap_s,out=sys.argv[1:]; cap=float(cap_s)
d=json.load(open(src)); bps=((d.get('end') or {}).get('sum_received') or {}).get('bits_per_second')
if bps is None: bps=((d.get('end') or {}).get('sum_sent') or {}).get('bits_per_second')
gbps=None if bps is None else float(bps)/1e9
ok=gbps is not None and gbps>0
cap_enforced=True if cap<=0 else (ok and gbps <= cap*1.15)
r={'measured_forward_gbps':gbps,'configured_cap_gbps':cap,'measurement_ok':ok,'cap_enforced_upper_bound':cap_enforced,
   'note':'Upper-bound check catches a missing tc cap. No lower-bound performance assumption is imposed.'}
open(out,'w').write(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
if not ok or not cap_enforced: raise SystemExit(5)
PYV
}
trap cleanup_caps EXIT

if echo " $VLLM_NETWORK_MODES " | grep -Eq ' (100g|20g) '; then
  if ! sudo -n true >/dev/null 2>&1 || ! "${SSH[@]}" "$NODE1_IP" sudo -n true >/dev/null 2>&1; then
    if [[ "$V8_REQUIRE_CAPS" == 1 ]]; then
      echo "ERROR: native/100G/20G vLLM matrix requires passwordless sudo on both nodes for tc shaping" >&2
      exit 3
    fi
  fi
fi

for mode in $VLLM_NETWORK_MODES; do
  cleanup_caps
  cap=0
  case "$mode" in
    native) tag=GCP_NATIVE; cap=0 ;;
    100g) tag=GCP_CAPPED_100G; cap=100; apply_cap "$cap" ;;
    20g) tag=GCP_CAPPED_20G; cap=20; apply_cap "$cap" ;;
    *) echo "ERROR: unsupported VLLM network mode '$mode'; allowed: native 100g 20g"; exit 4 ;;
  esac
  sleep 2
  MODE_ROOT="$OUT_ROOT/$tag"
  mkdir -p "$MODE_ROOT/network_validation" "$MODE_ROOT/results"
  export GCP_PHYSICAL_NETWORK_PROVENANCE="$PHYSICAL_PROVENANCE"
  export GCP_NETWORK_PROVENANCE="$tag"
  export V8_GCP_NETWORK_PROVENANCE_OVERRIDE="$tag"
  export V8_VLLM_NETWORK_MODE="$mode"
  export V8_VLLM_NETWORK_CAP_GBPS="$cap"
  nccl_multi_node_v6_aligned_env
  nccl_assert_no_local_forcing
  record_net_state "$MODE_ROOT/network_validation"
  verify_iperf "$MODE_ROOT/network_validation" "$cap"
  printf '{"network_provenance":"%s","physical_provenance":"%s","mode":"%s","configured_cap_gbps":%s,"iface":"%s"}\n' \
    "$tag" "$PHYSICAL_PROVENANCE" "$mode" "$cap" "$LOCAL_IFACE" > "$MODE_ROOT/network_validation/NETWORK_MODE.json"
  echo "===== V8 vLLM scale-out mode=$tag cap=${cap}G ====="
  OUT_ROOT="$MODE_ROOT/results" CASES_FILE="$CASES_FILE" "$SCRIPT_DIR/12_run_vllm_multi_node.sh" --all
  python3 "$SCRIPT_DIR/15_summarize_vllm.py" "$MODE_ROOT/results" --out "$MODE_ROOT/summary_v8full"
  cleanup_caps
  sleep 2
done
trap - EXIT
cleanup_caps
echo "V8 vLLM scale-out network matrix complete: $OUT_ROOT"
