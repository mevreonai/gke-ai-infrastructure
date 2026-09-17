#!/bin/bash
set -euo pipefail

echo "================================================================"
echo "STARTING MULTI-NODE TP=8 AND TP=4 NETWORK BANDWIDTH SWEEPS"
echo "Nodes: kimi-node-0 (10.128.0.39), kimi-node-1 (10.128.0.40)"
echo "Topologies: Multi-Node TP=8 (ppr:4:node) and TP=4 (ppr:2:node)"
echo "Rates     : NATIVE (175G), 100G, 50G, 20G, 10G"
echo "Collectives: AllReduce, AllGather, ReduceScatter"
echo "Buffer sizes: 8 KiB to 256 MiB (-b 8K -e 256M -f 2)"
echo "================================================================"

BASE_DIR="/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite"
mkdir -p "$BASE_DIR/allreduce" "$BASE_DIR/allgather" "$BASE_DIR/reducescatter"

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE1_IP="10.128.0.40"
IFACE="ens3"

# Setup docker wrappers with proper LOCAL_RANK device binding
cat << 'EOF' > /tmp/all_reduce_perf_docker
#!/bin/bash
LOCAL_RANK=${OMPI_COMM_WORLD_LOCAL_RANK:-0}
exec docker run --rm --gpus all --ipc=host --net=host -e CUDA_VISIBLE_DEVICES=${LOCAL_RANK} -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf $*"
EOF

cat << 'EOF' > /tmp/all_gather_perf_docker
#!/bin/bash
LOCAL_RANK=${OMPI_COMM_WORLD_LOCAL_RANK:-0}
exec docker run --rm --gpus all --ipc=host --net=host -e CUDA_VISIBLE_DEVICES=${LOCAL_RANK} -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_gather_perf $*"
EOF

cat << 'EOF' > /tmp/reduce_scatter_perf_docker
#!/bin/bash
LOCAL_RANK=${OMPI_COMM_WORLD_LOCAL_RANK:-0}
exec docker run --rm --gpus all --ipc=host --net=host -e CUDA_VISIBLE_DEVICES=${LOCAL_RANK} -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/reduce_scatter_perf $*"
EOF

chmod +x /tmp/all_reduce_perf_docker /tmp/all_gather_perf_docker /tmp/reduce_scatter_perf_docker
sudo install -m 755 /tmp/all_reduce_perf_docker /usr/local/bin/all_reduce_perf_docker
sudo install -m 755 /tmp/all_gather_perf_docker /usr/local/bin/all_gather_perf_docker
sudo install -m 755 /tmp/reduce_scatter_perf_docker /usr/local/bin/reduce_scatter_perf_docker

scp -o StrictHostKeyChecking=no /tmp/all_reduce_perf_docker 10.128.0.40:/tmp/
scp -o StrictHostKeyChecking=no /tmp/all_gather_perf_docker 10.128.0.40:/tmp/
scp -o StrictHostKeyChecking=no /tmp/reduce_scatter_perf_docker 10.128.0.40:/tmp/
ssh -o StrictHostKeyChecking=no 10.128.0.40 "
    sudo install -m 755 /tmp/all_reduce_perf_docker /usr/local/bin/all_reduce_perf_docker
    sudo install -m 755 /tmp/all_gather_perf_docker /usr/local/bin/all_gather_perf_docker
    sudo install -m 755 /tmp/reduce_scatter_perf_docker /usr/local/bin/reduce_scatter_perf_docker
"

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

MPI_RUN="/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root -x PATH -x LD_LIBRARY_PATH"

RATES="NATIVE 100 50 20 10"

for RATE in $RATES; do
    echo "========================================================"
    echo "=== RUNNING MULTI-NODE SWEEPS AT RATE: $RATE ==="
    echo "========================================================"
    apply_tc "$RATE"

    # --- TP = 8 (4 ranks on Node 0, 4 ranks on Node 1) ---
    echo ">>> Running Multi-Node TP=8 AllReduce ($RATE)"
    $MPI_RUN --hostfile "$HOSTFILE" -np 8 --map-by ppr:4:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/allreduce/tp8_${RATE}.log"

    echo ">>> Running Multi-Node TP=8 AllGather ($RATE)"
    $MPI_RUN --hostfile "$HOSTFILE" -np 8 --map-by ppr:4:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_gather_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/allgather/tp8_${RATE}.log"

    echo ">>> Running Multi-Node TP=8 ReduceScatter ($RATE)"
    $MPI_RUN --hostfile "$HOSTFILE" -np 8 --map-by ppr:4:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/reduce_scatter_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/reducescatter/tp8_${RATE}.log"

    # --- TP = 4 (2 ranks on Node 0, 2 ranks on Node 1) ---
    echo ">>> Running Multi-Node TP=4 AllReduce ($RATE)"
    $MPI_RUN --hostfile "$HOSTFILE" -np 4 --map-by ppr:2:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/allreduce/tp4_${RATE}.log"

    echo ">>> Running Multi-Node TP=4 AllGather ($RATE)"
    $MPI_RUN --hostfile "$HOSTFILE" -np 4 --map-by ppr:2:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_gather_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/allgather/tp4_${RATE}.log"

    echo ">>> Running Multi-Node TP=4 ReduceScatter ($RATE)"
    $MPI_RUN --hostfile "$HOSTFILE" -np 4 --map-by ppr:2:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/reduce_scatter_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/reducescatter/tp4_${RATE}.log"
done

cleanup_tc
echo "================================================================"
echo "MULTI-NODE TP=8 AND TP=4 SWEEPS SUCCESSFULLY COMPLETED!"
echo "================================================================"
