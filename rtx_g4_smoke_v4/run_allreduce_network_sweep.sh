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

apply_tc() {
    local rate="$1"
    cleanup_tc
    if [ "$rate" != "NATIVE" ]; then
        echo "=== Applying traffic cap: ${rate}Gbit on $IFACE ==="
        sudo tc qdisc add dev "$IFACE" root handle 1: htb default 10
        sudo tc class add dev "$IFACE" parent 1: classid 1:10 htb rate "${rate}gbit" ceil "${rate}gbit"
        ssh -o StrictHostKeyChecking=no "$NODE1_IP" "
            sudo tc qdisc add dev '$IFACE' root handle 1: htb default 10 &&
            sudo tc class add dev '$IFACE' parent 1: classid 1:10 htb rate ${rate}gbit ceil ${rate}gbit
        "
        sleep 2
    else
        echo "=== Running on unthrottled GCP_NATIVE (173 Gbps) ==="
    fi
}

# We test NATIVE (173 Gbps), 100G, 50G, 10G
for RATE in NATIVE 100 50 10; do
    echo "=========================================================="
    echo "Starting Multi-Node AllReduce (TP=16) at RATE=$RATE"
    echo "Starting message size: 8 KiB (-b 8K -e 256M -f 2)"
    echo "=========================================================="
    apply_tc "$RATE"

    OUTLOG="$RESULTS_DIR/allreduce_tp16_${RATE}.log"
    /usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun \
        --prefix /usr/mpi/gcc/openmpi-4.1.9a1 \
        --allow-run-as-root \
        --hostfile "$HOSTFILE" \
        -np 16 --map-by ppr:8:node --bind-to none \
        -x PATH -x LD_LIBRARY_PATH \
        -x NCCL_SOCKET_IFNAME="$IFACE" \
        -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$OUTLOG"
    
    echo "Finished RATE=$RATE. Output written to $OUTLOG"
done

cleanup_tc
echo "ALL NETWORK ALLREDUCE SWEEPS COMPLETE!"
