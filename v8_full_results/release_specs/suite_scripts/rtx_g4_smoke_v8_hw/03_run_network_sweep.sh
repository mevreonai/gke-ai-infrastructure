#!/usr/bin/env bash
# V8-FULL network/fabric characterization. Run on node0 only.
# Primary evidence is GCP_NATIVE. 100/50/20/10G are bandwidth-sensitivity experiments.
# The same iperf, NCCL SendRecv and cross-node TP2/TP8/TP16 AllReduce families are
# executed at every network provenance so the smoke layer has a complete transport matrix.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/00_smoke_common.sh"
init_smoke_env
: "${NODE0_IP:?Set NODE0_IP}"
: "${NODE1_IP:?Set NODE1_IP}"
: "${RUN_NETWORK_CAPS:=1}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
export PEER_IP="$NODE1_IP"
NCCL_DIR="$BENCH_ROOT/nccl-tests"
HOSTFILE="$RESULT_DIR/hosts"
SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
REMOTE_IFACE=$("${SSH[@]}" "$NODE1_IP" "ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'")
[[ -n "$LOCAL_IFACE" && -n "$REMOTE_IFACE" ]] || { echo "ERROR: peer interface discovery failed"; exit 2; }
[[ "$LOCAL_IFACE" == "$REMOTE_IFACE" ]] || { echo "ERROR: interface names differ ($LOCAL_IFACE vs $REMOTE_IFACE); refuse ambiguous shaping/NCCL binding"; exit 3; }
export IFACE="$LOCAL_IFACE" NCCL_SOCKET_IFNAME="=$LOCAL_IFACE"

# Preserve the normal NCCL network stack, but never let legacy local P2P/SHM forcing
# contaminate cross-node tests. These variables are intentionally not exported by mpirun.
unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL || true
for v in NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; do
  [[ -z "${!v+x}" ]] || { echo "ERROR: forbidden NCCL local transport override remains: $v=${!v}" >&2; exit 4; }
done
REMOTE_FORBIDDEN=$("${SSH[@]}" "$NODE1_IP" "env | grep -E '^NCCL_(P2P_DISABLE|SHM_DISABLE|P2P_LEVEL)=' || true")
[[ -z "$REMOTE_FORBIDDEN" ]] || { echo "ERROR: node1 login environment contains forbidden NCCL local transport override(s): $REMOTE_FORBIDDEN" >&2; exit 4; }
{ echo "timestamp=$(date --iso-8601=seconds)"; env | LC_ALL=C sort | grep '^NCCL_' || true; } > "$RESULT_DIR/NCCL_ENV_NETWORK_NODE0.txt"
"${SSH[@]}" "$NODE1_IP" "env | LC_ALL=C sort | grep '^NCCL_' || true" > "$RESULT_DIR/NCCL_ENV_NETWORK_NODE1.txt"
meta "SUITE=V8_FULL TEST_SCOPE=NETWORK_SWEEP IFACE=$IFACE PRIMARY=GCP_NATIVE"
cat > "$HOSTFILE" <<HOSTS
$NODE0_IP slots=8
$NODE1_IP slots=8
HOSTS

run_logged 200_network_preflight "
echo NODE0_IP=$NODE0_IP NODE1_IP=$NODE1_IP IFACE=$IFACE
ip route get \"$NODE1_IP\"
ip -s link show dev \"$IFACE\"
ethtool \"$IFACE\" || true
ping -c 20 \"$NODE1_IP\" || true
${SSH[*]} \"$NODE1_IP\" 'hostname -f; ip -s link show dev $REMOTE_IFACE; nvidia-smi -L'
"
run_logged 201_mpi_preflight "mpirun --hostfile \"$HOSTFILE\" -np 2 --map-by ppr:1:node --bind-to none hostname -f"
"${SSH[@]}" "$NODE1_IP" "pkill -x iperf3 2>/dev/null || true; iperf3 -s -D"

cleanup_caps() {
  sudo -n tc qdisc del dev "$LOCAL_IFACE" root 2>/dev/null || true
  "${SSH[@]}" "$NODE1_IP" "sudo -n tc qdisc del dev '$REMOTE_IFACE' root 2>/dev/null || true" >/dev/null 2>&1 || true
}
trap cleanup_caps EXIT

apply_cap() {
  local rate="$1"
  sudo -n tc qdisc replace dev "$LOCAL_IFACE" root handle 1: htb default 10
  sudo -n tc class replace dev "$LOCAL_IFACE" parent 1: classid 1:10 htb rate "${rate}gbit" ceil "${rate}gbit"
  "${SSH[@]}" "$NODE1_IP" "sudo -n tc qdisc replace dev '$REMOTE_IFACE' root handle 1: htb default 10 && sudo -n tc class replace dev '$REMOTE_IFACE' parent 1: classid 1:10 htb rate '${rate}gbit' ceil '${rate}gbit'"
}

run_iperf() {
  local tag="$1" cap="$2"
  run_logged "210_iperf_${tag}" "echo 'META TEST_KIND=IPERF DIRECTION=FORWARD NETWORK_PROVENANCE=$tag CAP_GBIT=$cap'; iperf3 -c '$NODE1_IP' -t 20 -P 32 -J | tee '$RESULT_DIR/iperf_${tag}.raw.json'"
  run_logged "210_iperf_${tag}_reverse" "echo 'META TEST_KIND=IPERF DIRECTION=REVERSE NETWORK_PROVENANCE=$tag CAP_GBIT=$cap'; iperf3 -c '$NODE1_IP' -t 20 -P 32 -R -J | tee '$RESULT_DIR/iperf_${tag}_reverse.raw.json'"
  python3 - "$RESULT_DIR/iperf_${tag}.raw.json" "$cap" "$RESULT_DIR/iperf_${tag}.validation.json" <<'PYV'
import json,sys
src,cap_s,out=sys.argv[1:]; cap=float(cap_s)
d=json.load(open(src))
bps=((d.get('end') or {}).get('sum_received') or {}).get('bits_per_second')
if bps is None: bps=((d.get('end') or {}).get('sum_sent') or {}).get('bits_per_second')
gbps=None if bps is None else float(bps)/1e9
ok=gbps is not None and gbps>0
cap_ok=True if cap<=0 else (ok and gbps<=cap*1.15)
r={'measured_forward_gbps':gbps,'configured_cap_gbps':cap,'measurement_ok':ok,'cap_enforced_upper_bound':cap_ok,
   'note':'Upper-bound validation catches a missing tc cap; no lower-bound throughput assumption is imposed.'}
open(out,'w').write(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
if not ok or not cap_ok: raise SystemExit(6)
PYV
}

run_sendrecv() {
  local tag="$1" cap="$2"
  for SIZE in 16K 128K 512K 64M 128M 256M; do
    local safe label
    safe=$(echo "$SIZE" | tr '[:upper:]' '[:lower:]')
    label="220_sendrecv_${tag}_${safe}"
    start_gpu_telemetry "$label"
    run_logged "$label" "
      cd \"$NCCL_DIR\"
      echo 'META TEST_KIND=SENDRECV NETWORK_PROVENANCE=$tag CAP_GBIT=$cap SIZE=$SIZE'
      mpirun --hostfile \"$HOSTFILE\" -np 2 --map-by ppr:1:node --bind-to none \\
        -x PATH -x LD_LIBRARY_PATH -x NCCL_SOCKET_IFNAME -x NCCL_DEBUG=WARN \\
        ./build/sendrecv_perf -b $SIZE -e $SIZE -g 1 -J \"$RESULT_DIR/nccl_sendrecv_${tag}_${safe}.json\"
    "
    stop_gpu_telemetry
  done
}

run_crossnode_ar() {
  local tag="$1" cap="$2"
  for SPEC in "TP2:1" "TP8:4" "TP16:8"; do
    local tp g label
    tp=${SPEC%%:*}; g=${SPEC##*:}
    label="225_crossnode_ar_${tp}_${tag}"
    start_gpu_telemetry "$label"
    run_logged "$label" "
      cd \"$NCCL_DIR\"
      echo 'META TEST_KIND=ALLREDUCE CROSS_NODE=1 TOPOLOGY=$tp MPI_PROCS=2 GPUS_PER_PROC=$g NETWORK_PROVENANCE=$tag CAP_GBIT=$cap'
      mpirun --hostfile \"$HOSTFILE\" -np 2 --map-by ppr:1:node --bind-to none \\
        -x PATH -x LD_LIBRARY_PATH -x NCCL_SOCKET_IFNAME -x NCCL_DEBUG=WARN \\
        ./build/all_reduce_perf -b 16K -e 256M -f 2 -g $g
    "
    stop_gpu_telemetry
  done
}

cleanup_caps
run_logged 205_ping_native "ping -c 100 \"$NODE1_IP\""
run_iperf GCP_NATIVE 0
run_sendrecv GCP_NATIVE 0
run_crossnode_ar GCP_NATIVE 0

if [[ "$RUN_NETWORK_CAPS" == 1 ]]; then
  if ! sudo -n true >/dev/null 2>&1 || ! "${SSH[@]}" "$NODE1_IP" sudo -n true >/dev/null 2>&1; then
    echo "ERROR: RUN_NETWORK_CAPS=1 but passwordless sudo is unavailable on one or both nodes" >&2
    exit 5
  fi
  for RATE in 100 50 20 10; do
    TAG="GCP_CAPPED_${RATE}G"
    apply_cap "$RATE"
    sleep 2
    run_logged "211_qdisc_${RATE}g" "sudo -n tc -s qdisc show dev \"$LOCAL_IFACE\"; sudo -n tc -s class show dev \"$LOCAL_IFACE\"; ${SSH[*]} \"$NODE1_IP\" \"sudo -n tc -s qdisc show dev '$REMOTE_IFACE'; sudo -n tc -s class show dev '$REMOTE_IFACE'\""
    run_iperf "$TAG" "$RATE"
    run_sendrecv "$TAG" "$RATE"
    run_crossnode_ar "$TAG" "$RATE"
    cleanup_caps
    sleep 2
  done
else
  echo "RUN_NETWORK_CAPS=0; sensitivity sweep intentionally skipped" | tee "$RESULT_DIR/CAPS_SKIPPED.txt"
fi

# One verbose native SendRecv run for NET/GRAPH provenance after all caps are removed.
cleanup_caps
start_gpu_telemetry 240_nccl_debug_sendrecv_native_128m
run_logged 240_nccl_debug_sendrecv_native_128m "
  cd \"$NCCL_DIR\"
  mpirun --hostfile \"$HOSTFILE\" -np 2 --map-by ppr:1:node --bind-to none \\
    -x PATH -x LD_LIBRARY_PATH -x NCCL_SOCKET_IFNAME -x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET \\
    ./build/sendrecv_perf -b 128M -e 128M -g 1
"
stop_gpu_telemetry
cleanup_caps
trap - EXIT
log_note "V8-FULL NETWORK SWEEP COMPLETE. RESULT_DIR=$RESULT_DIR"
