#!/bin/bash
set -euo pipefail

echo "================================================================"
echo "STARTING COMPLETE FRESH LIVE BENCHMARK SUITE ON KIMI CLUSTER"
echo "Collectives: AllReduce, AllGather, ReduceScatter"
echo "Topologies : TP=16 (Network Sweep: Native, 100G, 50G, 20G, 10G)"
echo "             TP=8  (Node-Local Cross-Socket: 8 GPUs)"
echo "             TP=4  (Socket-Local Single-NUMA: 4 GPUs)"
echo "Message size: 8 KiB to 256 MiB (-b 8K -e 256M -f 2)"
echo "================================================================"

BASE_DIR="/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite"
mkdir -p "$BASE_DIR/allreduce" "$BASE_DIR/allgather" "$BASE_DIR/reducescatter"

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE1_IP="10.128.0.40"
IFACE="ens3"

# Setup docker wrappers for multi-node OpenMPI
cat << 'EOF' > /tmp/all_reduce_perf_docker
#!/bin/bash
exec docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf $*"
EOF
cat << 'EOF' > /tmp/all_gather_perf_docker
#!/bin/bash
exec docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_gather_perf $*"
EOF
cat << 'EOF' > /tmp/reduce_scatter_perf_docker
#!/bin/bash
exec docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/reduce_scatter_perf $*"
EOF

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

DOCKER_RUN="docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c"

# ==========================================
# 1. RUN TP=4 (Single-NUMA, 4 GPUs on Node 0)
# ==========================================
echo ">>> [1/3] Running TP=4 Local Benchmarks (GPUs 0,1,2,3) <<<"
$DOCKER_RUN "CUDA_VISIBLE_DEVICES=0,1,2,3 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf -b 8K -e 256M -f 2 -g 4" | tee "$BASE_DIR/allreduce/tp4.log"
$DOCKER_RUN "CUDA_VISIBLE_DEVICES=0,1,2,3 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_gather_perf -b 8K -e 256M -f 2 -g 4" | tee "$BASE_DIR/allgather/tp4.log"
$DOCKER_RUN "CUDA_VISIBLE_DEVICES=0,1,2,3 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/reduce_scatter_perf -b 8K -e 256M -f 2 -g 4" | tee "$BASE_DIR/reducescatter/tp4.log"
echo "TP=4 Complete!"

# ==========================================
# 2. RUN TP=8 (Node-Local, 8 GPUs on Node 0)
# ==========================================
echo ">>> [2/3] Running TP=8 Node-Local Benchmarks (8 GPUs) <<<"
$DOCKER_RUN "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf -b 8K -e 256M -f 2 -g 8" | tee "$BASE_DIR/allreduce/tp8.log"
$DOCKER_RUN "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_gather_perf -b 8K -e 256M -f 2 -g 8" | tee "$BASE_DIR/allgather/tp8.log"
$DOCKER_RUN "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/reduce_scatter_perf -b 8K -e 256M -f 2 -g 8" | tee "$BASE_DIR/reducescatter/tp8.log"
echo "TP=8 Complete!"

# ==========================================
# 3. RUN TP=16 (Multi-Node Sweep: 16 GPUs)
# ==========================================
echo ">>> [3/3] Running TP=16 Multi-Node Bandwidth Sweep <<<"
RATES="NATIVE 100 50 20 10"

for RATE in $RATES; do
    echo "--------------------------------------------------------"
    echo "Running TP=16 at Network RATE=$RATE"
    echo "--------------------------------------------------------"
    apply_tc "$RATE"

    # AllReduce
    $MPI_RUN --hostfile "$HOSTFILE" -np 16 --map-by ppr:8:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/allreduce/tp16_${RATE}.log"

    # AllGather
    $MPI_RUN --hostfile "$HOSTFILE" -np 16 --map-by ppr:8:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_gather_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/allgather/tp16_${RATE}.log"

    # ReduceScatter
    $MPI_RUN --hostfile "$HOSTFILE" -np 16 --map-by ppr:8:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/reduce_scatter_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/reducescatter/tp16_${RATE}.log"
done

cleanup_tc
echo "================================================================"
echo "ALL LIVE BENCHMARKS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!"
echo "Outputs stored in $BASE_DIR"
echo "================================================================"
