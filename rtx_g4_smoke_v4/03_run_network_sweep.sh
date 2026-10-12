#!/usr/bin/env bash
# Run ONLY on Node 0 after both nodes are prepared.
# Requires passwordless SSH and passwordless sudo on both disposable benchmark VMs
# for traffic shaping. Collects native + 100G + 50G + 20G + 10G results.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/00_smoke_common.sh"
init_smoke_env

: "${NODE0_IP:?Set NODE0_IP}"
: "${NODE1_IP:?Set NODE1_IP}"
export PEER_IP="$NODE1_IP"

NCCL_DIR="$BENCH_ROOT/nccl-tests"
HOSTFILE="$BENCH_ROOT/hosts"

LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
REMOTE_IFACE=$(ssh -o BatchMode=yes "$NODE1_IP" \
  "ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'")

if [ -z "$LOCAL_IFACE" ] || [ -z "$REMOTE_IFACE" ]; then
  echo "ERROR: Could not determine peer interfaces."
  exit 2
fi

# For deterministic NCCL interface selection, require same interface name.
# Identical GCP shapes normally satisfy this. If not, stop rather than silently bypass shaping.
if [ "$LOCAL_IFACE" != "$REMOTE_IFACE" ]; then
  echo "ERROR: Local interface '$LOCAL_IFACE' != remote '$REMOTE_IFACE'."
  echo "The automated sweep intentionally stops so NCCL cannot bypass the shaped interface."
  echo "Run manually with per-host NCCL_SOCKET_IFNAME if interface names differ."
  exit 3
fi

export IFACE="$LOCAL_IFACE"
export NCCL_SOCKET_IFNAME="=$IFACE"
export NCCL_DIR HOSTFILE IFACE NCCL_SOCKET_IFNAME NODE0_IP NODE1_IP

meta "TEST_SCOPE=NETWORK_SWEEP"
meta "LOCAL_IFACE=$LOCAL_IFACE"
meta "REMOTE_IFACE=$REMOTE_IFACE"

run_logged 200_network_preflight "
echo NODE0_IP=$NODE0_IP
echo NODE1_IP=$NODE1_IP
echo IFACE=$IFACE
ip route get \"$NODE1_IP\"
ip -s link show dev \"$IFACE\"
ethtool \"$IFACE\" || true
ssh -o BatchMode=yes \"$NODE1_IP\" hostname -f
ssh -o BatchMode=yes \"$NODE1_IP\" sudo -n true
"

cat > "$HOSTFILE" <<EOF
$NODE0_IP slots=8
$NODE1_IP slots=8
EOF

run_logged 201_mpi_preflight "
cat \"$HOSTFILE\"
/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root --hostfile \"$HOSTFILE\" -np 2 --map-by ppr:1:node --bind-to none hostname -f
"

# Start iperf server remotely.
ssh "$NODE1_IP" "pkill -x iperf3 2>/dev/null || true; iperf3 -s -D"

cleanup_caps() {
  sudo tc qdisc del dev "$LOCAL_IFACE" root 2>/dev/null || true
  ssh "$NODE1_IP" "sudo -n tc qdisc del dev '$REMOTE_IFACE' root 2>/dev/null || true" || true
}
trap cleanup_caps EXIT

apply_cap() {
  local rate="$1"
  cleanup_caps
  sudo tc qdisc add dev "$LOCAL_IFACE" root handle 1: htb default 10
  sudo tc class add dev "$LOCAL_IFACE" parent 1: classid 1:10 htb rate "${rate}gbit" ceil "${rate}gbit"

  ssh "$NODE1_IP" "
    sudo -n tc qdisc del dev '$REMOTE_IFACE' root 2>/dev/null || true
    sudo -n tc qdisc add dev '$REMOTE_IFACE' root handle 1: htb default 10
    sudo -n tc class add dev '$REMOTE_IFACE' parent 1: classid 1:10 \
      htb rate '${rate}gbit' ceil '${rate}gbit'
  "
}

remove_cap() {
  cleanup_caps
}

run_sendrecv_points() {
  local tag="$1"
  local cap="$2"

  for SIZE in 16K 128K 512K 64M 128M 256M; do
    SAFE=$(echo "$SIZE" | tr '[:upper:]' '[:lower:]')
    LABEL="220_sendrecv_${tag}_${SAFE}"
    start_gpu_telemetry "$LABEL"
    run_logged "$LABEL" "
      cd \"$NCCL_DIR\"
      echo 'META TEST_KIND=SENDRECV NETWORK_PROVENANCE=$tag CAP_GBIT=$cap SIZE=$SIZE'
      /usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun \
        --prefix /usr/mpi/gcc/openmpi-4.1.9a1 \
        --allow-run-as-root \
        --hostfile "$HOSTFILE" \
        -np 2 --map-by ppr:1:node --bind-to none \
        -x PATH -x LD_LIBRARY_PATH \
        -x NCCL_SOCKET_IFNAME \
        -x NCCL_DEBUG=WARN \
        /usr/local/bin/sendrecv_perf_docker -b $SIZE -e $SIZE -g 1 -J "$RESULT_DIR/nccl_sendrecv_${tag}_${SAFE}.json"
    "
    stop_gpu_telemetry
  done
}

run_iperf() {
  local tag="$1"
  local cap="$2"
  local raw="$RESULT_DIR/iperf_${tag}.raw.json"
  run_logged "210_iperf_${tag}" "
    echo 'META TEST_KIND=IPERF NETWORK_PROVENANCE=$tag CAP_GBIT=$cap'
    iperf3 -c \"$NODE1_IP\" -t 20 -P 32 -J | tee \"$raw\"
  "
}

# Native first.
remove_cap
export NETWORK_PROVENANCE=GCP_NATIVE
log_note "NETWORK_PROVENANCE=$NETWORK_PROVENANCE"
run_logged 205_ping_native "ping -c 100 \"$NODE1_IP\""
run_iperf GCP_NATIVE 0
run_sendrecv_points GCP_NATIVE 0

# Controlled sweep.
for RATE in 100 50 20 10; do
  TAG="GCP_CAPPED_${RATE}G"
  log_note "Applying bandwidth cap: $TAG"
  apply_cap "$RATE"
  sleep 2

  run_logged "211_qdisc_${RATE}g" "
    echo 'LOCAL'
    sudo tc -s qdisc show dev \"$LOCAL_IFACE\"
    sudo tc -s class show dev \"$LOCAL_IFACE\"
    echo 'REMOTE'
    ssh \"$NODE1_IP\" \"sudo -n tc -s qdisc show dev '$REMOTE_IFACE'; sudo -n tc -s class show dev '$REMOTE_IFACE'\"
  "

  run_iperf "$TAG" "$RATE"
  run_sendrecv_points "$TAG" "$RATE"
done

remove_cap
run_logged 230_qdisc_after "
sudo tc qdisc show dev \"$LOCAL_IFACE\"
ssh \"$NODE1_IP\" \"sudo -n tc qdisc show dev '$REMOTE_IFACE'\"
"

# Native NCCL debug trace once.
start_gpu_telemetry 240_nccl_debug_sendrecv_native_128m
run_logged 240_nccl_debug_sendrecv_native_128m "
cd \"$NCCL_DIR\"
mpirun \
  --hostfile \"$HOSTFILE\" \
  -np 2 --map-by ppr:1:node --bind-to none \
  -x PATH -x LD_LIBRARY_PATH \
  -x NCCL_SOCKET_IFNAME \
  -x NCCL_DEBUG=INFO \
  -x NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET \
  ./build/sendrecv_perf -b 128M -e 128M -g 1
"
stop_gpu_telemetry

log_note "NETWORK SWEEP COMPLETE. RESULT_DIR=$RESULT_DIR"
