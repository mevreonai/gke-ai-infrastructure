#!/usr/bin/env bash
# V8-FULL targeted capped-network distributed profiles.
# To control profiler cost, capped modes capture only the matched 128K prefill point
# for all four topologies. Native mode retains the full profile matrix elsewhere.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
for f in "$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env"; do [[ -f "$f" ]] && { source "$f"; break; }; done
: "${NODE0_IP:?NODE0_IP missing}"
: "${NODE1_IP:?NODE1_IP missing}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${OUT_ROOT:=$HOME/v8_full_results/$(date +%Y%m%d_%H%M%S)/profiles_multi_node_capped}"
: "${CAPPED_PROFILE_MODES:=100g 20g}"
mkdir -p "$OUT_ROOT"
SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
REMOTE_IFACE=$("${SSH[@]}" "$NODE1_IP" "ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'")
[[ -n "$LOCAL_IFACE" && "$LOCAL_IFACE" == "$REMOTE_IFACE" ]] || { echo "ERROR: interface discovery mismatch"; exit 2; }
export NCCL_SOCKET_IFNAME="=$LOCAL_IFACE"
cleanup(){ sudo -n tc qdisc del dev "$LOCAL_IFACE" root 2>/dev/null || true; "${SSH[@]}" "$NODE1_IP" "sudo -n tc qdisc del dev '$REMOTE_IFACE' root 2>/dev/null || true" >/dev/null 2>&1 || true; }
apply(){ local r=$1; sudo -n tc qdisc replace dev "$LOCAL_IFACE" root handle 1: htb default 10; sudo -n tc class replace dev "$LOCAL_IFACE" parent 1: classid 1:10 htb rate "${r}gbit" ceil "${r}gbit"; "${SSH[@]}" "$NODE1_IP" "sudo -n tc qdisc replace dev '$REMOTE_IFACE' root handle 1: htb default 10 && sudo -n tc class replace dev '$REMOTE_IFACE' parent 1: classid 1:10 htb rate '${r}gbit' ceil '${r}gbit'"; }
trap cleanup EXIT
sudo -n true >/dev/null 2>&1 || { echo "ERROR: capped profiles require passwordless sudo on node0"; exit 3; }
"${SSH[@]}" "$NODE1_IP" sudo -n true >/dev/null 2>&1 || { echo "ERROR: capped profiles require passwordless sudo on node1"; exit 3; }
"${SSH[@]}" "$NODE1_IP" "pkill -x iperf3 2>/dev/null || true; iperf3 -s -D"
for mode in $CAPPED_PROFILE_MODES; do
  cleanup
  case "$mode" in 100g) cap=100; tag=GCP_CAPPED_100G;; 20g) cap=20; tag=GCP_CAPPED_20G;; *) echo "unsupported $mode"; exit 4;; esac
  apply "$cap"; sleep 2
  MODE_ROOT="$OUT_ROOT/$tag"; mkdir -p "$MODE_ROOT/network_validation"
  export V8_GCP_NETWORK_PROVENANCE_OVERRIDE="$tag" GCP_NETWORK_PROVENANCE="$tag" V8_VLLM_NETWORK_MODE="$mode" V8_VLLM_NETWORK_CAP_GBPS="$cap"
  iperf3 -c "$NODE1_IP" -t 8 -P 16 -J > "$MODE_ROOT/network_validation/iperf_forward.json"
  python3 - "$MODE_ROOT/network_validation/iperf_forward.json" "$cap" "$MODE_ROOT/network_validation/IPERF_VALIDATION.json" <<'PYV'
import json,sys
src,cap_s,out=sys.argv[1:]; cap=float(cap_s); d=json.load(open(src))
bps=((d.get('end') or {}).get('sum_received') or {}).get('bits_per_second'); gbps=None if bps is None else float(bps)/1e9
ok=gbps is not None and gbps>0 and gbps<=cap*1.15
r={'measured_forward_gbps':gbps,'configured_cap_gbps':cap,'cap_enforced_upper_bound':ok}
open(out,'w').write(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
if not ok: raise SystemExit(5)
PYV
  sudo -n tc -s qdisc show dev "$LOCAL_IFACE" > "$MODE_ROOT/network_validation/node0_qdisc.txt" 2>&1 || true
  "${SSH[@]}" "$NODE1_IP" "sudo -n tc -s qdisc show dev '$REMOTE_IFACE'" > "$MODE_ROOT/network_validation/node1_qdisc.txt" 2>&1 || true
  OUT_ROOT="$MODE_ROOT/profiles" PROFILE_MODE_FILTER=prefill_128k RUN_HEAVY_PROFILE=0 "$SCRIPT_DIR/18_run_vllm_multi_node_profiles.sh"
  cleanup; sleep 2
done
trap - EXIT
cleanup
echo "Capped distributed profile results: $OUT_ROOT"
