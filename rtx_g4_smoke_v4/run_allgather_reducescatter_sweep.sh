#!/bin/bash
set -euo pipefail

# 1. Setup Docker wrapper scripts on both Node 0 and Node 1
setup_wrappers() {
    echo "=== Setting up all_gather_perf_docker and reduce_scatter_perf_docker ==="
    cat << 'EOF' > /tmp/all_gather_perf_docker
#!/bin/bash
exec docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_gather_perf $*"
EOF
    sudo install -m 755 /tmp/all_gather_perf_docker /usr/local/bin/all_gather_perf_docker

    cat << 'EOF' > /tmp/reduce_scatter_perf_docker
#!/bin/bash
exec docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/reduce_scatter_perf $*"
EOF
    sudo install -m 755 /tmp/reduce_scatter_perf_docker /usr/local/bin/reduce_scatter_perf_docker

    # Copy to Node 1
    scp -o StrictHostKeyChecking=no /tmp/all_gather_perf_docker 10.128.0.40:/tmp/
    scp -o StrictHostKeyChecking=no /tmp/reduce_scatter_perf_docker 10.128.0.40:/tmp/
    ssh -o StrictHostKeyChecking=no 10.128.0.40 "
        sudo install -m 755 /tmp/all_gather_perf_docker /usr/local/bin/all_gather_perf_docker
        sudo install -m 755 /tmp/reduce_scatter_perf_docker /usr/local/bin/reduce_scatter_perf_docker
    "
}

setup_wrappers

RESULTS_DIR="/home/ayu23/rtx_g4_smoke/allgather_reducescatter_sweep"
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
            sudo tc qdisc add dev '$IFACE' root handle 1: htb default 10
            sudo tc class add dev '$IFACE' parent 1: classid 1:10 htb rate ${rate}gbit ceil ${rate}gbit
        "
        sleep 2
    else
        echo "=== Running on unthrottled GCP_NATIVE (173.58 Gbps) ==="
    fi
}

RATES="NATIVE 100 50 20 10"

# 2. Run AllGather Sweep
echo "=========================================================="
echo "Starting Multi-Node AllGather (TP=16) Bandwidth Sweep"
echo "Message size: 8 KiB to 256 MiB (-b 8K -e 256M -f 2)"
echo "=========================================================="

for RATE in $RATES; do
    echo "--- AllGather at RATE=$RATE ---"
    apply_tc "$RATE"
    OUTLOG="$RESULTS_DIR/allgather_tp16_${RATE}.log"
    /usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun \
        --prefix /usr/mpi/gcc/openmpi-4.1.9a1 \
        --allow-run-as-root \
        --hostfile "$HOSTFILE" \
        -np 16 --map-by ppr:8:node --bind-to none \
        -x PATH -x LD_LIBRARY_PATH \
        -x NCCL_SOCKET_IFNAME="$IFACE" \
        -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_gather_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$OUTLOG"
    echo "Finished AllGather RATE=$RATE"
done

# 3. Run ReduceScatter Sweep
echo "=========================================================="
echo "Starting Multi-Node ReduceScatter (TP=16) Bandwidth Sweep"
echo "Message size: 8 KiB to 256 MiB (-b 8K -e 256M -f 2)"
echo "=========================================================="

for RATE in $RATES; do
    echo "--- ReduceScatter at RATE=$RATE ---"
    apply_tc "$RATE"
    OUTLOG="$RESULTS_DIR/reducescatter_tp16_${RATE}.log"
    /usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun \
        --prefix /usr/mpi/gcc/openmpi-4.1.9a1 \
        --allow-run-as-root \
        --hostfile "$HOSTFILE" \
        -np 16 --map-by ppr:8:node --bind-to none \
        -x PATH -x LD_LIBRARY_PATH \
        -x NCCL_SOCKET_IFNAME="$IFACE" \
        -x NCCL_DEBUG=WARN \
        /usr/local/bin/reduce_scatter_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$OUTLOG"
    echo "Finished ReduceScatter RATE=$RATE"
done

cleanup_tc
echo "ALLGATHER AND REDUCE_SCATTER SWEEPS COMPLETED SUCCESSFULLY!"
