#!/bin/bash
set -euo pipefail

RESULTS_DIR="/home/ayu23/rtx_g4_smoke/allreduce_network_sweep"
mkdir -p "$RESULTS_DIR"
HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE1_IP="10.128.0.40"
IFACE="ens3"

cleanup_tc() {
    sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
    ssh -o StrictHostKeyChecking=no "$NODE1_IP" "sudo tc qdisc del dev '$IFACE' root 2>/dev/null || true" || true
}
trap cleanup_tc EXIT

echo "=== Applying traffic cap: 20Gbit on $IFACE ==="
cleanup_tc
sudo tc qdisc add dev "$IFACE" root handle 1: htb default 10
sudo tc class add dev "$IFACE" parent 1: classid 1:10 htb rate 20gbit ceil 20gbit
ssh -o StrictHostKeyChecking=no "$NODE1_IP" "
    sudo tc qdisc add dev '$IFACE' root handle 1: htb default 10
    sudo tc class add dev '$IFACE' parent 1: classid 1:10 htb rate 20gbit ceil 20gbit
"
sleep 2

OUTLOG="$RESULTS_DIR/allreduce_tp16_20.log"
echo "=== Running 20G Multi-Node AllReduce (TP=16) from 8 KiB to 256 MiB ==="
/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun \
    --prefix /usr/mpi/gcc/openmpi-4.1.9a1 \
    --allow-run-as-root \
    --hostfile "$HOSTFILE" \
    -np 16 --map-by ppr:8:node --bind-to none \
    -x PATH -x LD_LIBRARY_PATH \
    -x NCCL_SOCKET_IFNAME="$IFACE" \
    -x NCCL_DEBUG=WARN \
    /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$OUTLOG"

cleanup_tc
echo "20G ALLREDUCE COMPLETE!"
