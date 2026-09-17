#!/bin/bash
# ==============================================================================
# Complete AllReduce Benchmark Suite Across All Topologies and Bandwidth Caps
# Clusters: kimi-node-0 (10.128.0.39) and kimi-node-1 (10.128.0.40)
# Topologies:
#   - TP=16 Multi-Node (8 ranks on Node 0 + 8 ranks on Node 1)
#   - TP=8  Multi-Node (4 ranks on Node 0 + 4 ranks on Node 1)
#   - TP=4  Multi-Node (2 ranks on Node 0 + 2 ranks on Node 1)
#   - TP=8  Node-Local Single-Host (8 GPUs, cross-socket PCIe Gen4)
#   - TP=4  Socket-Local Single-NUMA (4 GPUs, NUMA 0)
# Network Rates: NATIVE (173.6 Gbps), 100G, 50G, 20G, 10G
# Message Sizes: 8 KiB to 256 MiB (-b 8K -e 256M -f 2)
# ==============================================================================
set -euo pipefail

BASE_DIR="${1:-/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite/allreduce}"
mkdir -p "$BASE_DIR"

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE1_IP="10.128.0.40"
IFACE="ens3"

# 1. Setup container wrapper on both nodes to ensure proper rank-to-GPU device mapping
cat << 'EOF' > /tmp/all_reduce_perf_docker
#!/bin/bash
LOCAL_RANK=${OMPI_COMM_WORLD_LOCAL_RANK:-0}
exec docker run --rm --gpus all --ipc=host --net=host -e CUDA_VISIBLE_DEVICES=${LOCAL_RANK} \
    -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest \
    -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf $*"
EOF

chmod +x /tmp/all_reduce_perf_docker
sudo install -m 755 /tmp/all_reduce_perf_docker /usr/local/bin/all_reduce_perf_docker
scp -o StrictHostKeyChecking=no /tmp/all_reduce_perf_docker "$NODE1_IP:/tmp/"
ssh -o StrictHostKeyChecking=no "$NODE1_IP" "sudo install -m 755 /tmp/all_reduce_perf_docker /usr/local/bin/all_reduce_perf_docker"

# 2. Traffic Control (tc) helpers
cleanup_tc() {
    sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
    ssh -o StrictHostKeyChecking=no "$NODE1_IP" "sudo tc qdisc del dev '$IFACE' root 2>/dev/null || true" || true
}
trap cleanup_tc EXIT

apply_tc() {
    local rate="$1"
    cleanup_tc
    if [ "$rate" != "NATIVE" ]; then
        echo "=== [Traffic Control] Applying ${rate}Gbps cap on $IFACE ==="
        sudo tc qdisc add dev "$IFACE" root handle 1: htb default 10
        sudo tc class add dev "$IFACE" parent 1: classid 1:10 htb rate "${rate}gbit" ceil "${rate}gbit"
        ssh -o StrictHostKeyChecking=no "$NODE1_IP" "
            sudo tc qdisc add dev '$IFACE' root handle 1: htb default 10
            sudo tc class add dev '$IFACE' parent 1: classid 1:10 htb rate ${rate}gbit ceil ${rate}gbit
        "
        sleep 2
    else
        echo "=== [Traffic Control] Running on unthrottled GCP_NATIVE (173.6 Gbps) ==="
    fi
}

MPI_RUN="/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root -x PATH -x LD_LIBRARY_PATH"
DOCKER_LOCAL="docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c"

# ==============================================================================
# PHASE 1: NODE-LOCAL BASELINES (No network interface touched)
# ==============================================================================
echo ">>> [Phase 1/2] Running Local Baselines <<<"
echo "Running TP=4 Socket-Local (Single-NUMA 0)..."
$DOCKER_LOCAL "CUDA_VISIBLE_DEVICES=0,1,2,3 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf -b 8K -e 256M -f 2 -g 4" | tee "$BASE_DIR/tp4.log"

echo "Running TP=8 Node-Local (Cross-Socket PCIe Gen4)..."
$DOCKER_LOCAL "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 NCCL_P2P_LEVEL=SYS /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf -b 8K -e 256M -f 2 -g 8" | tee "$BASE_DIR/tp8.log"

# ==============================================================================
# PHASE 2: MULTI-NODE NETWORK SWEEPS (TP=16, TP=8, TP=4 across 5 bandwidth caps)
# ==============================================================================
echo ">>> [Phase 2/2] Running Multi-Node Network Sweeps <<<"
RATES="NATIVE 100 50 20 10"

for RATE in $RATES; do
    echo "===================================================================="
    echo "=== NETWORK RATE: $RATE ==="
    echo "===================================================================="
    apply_tc "$RATE"

    # 1. TP=16 Multi-Node (8 ranks on Node 0 + 8 ranks on Node 1)
    echo ">>> Running Multi-Node AllReduce: TP=16 at $RATE"
    $MPI_RUN --hostfile "$HOSTFILE" -np 16 --map-by ppr:8:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/tp16_${RATE}.log"

    # 2. TP=8 Multi-Node (4 ranks on Node 0 + 4 ranks on Node 1)
    echo ">>> Running Multi-Node AllReduce: TP=8 at $RATE"
    $MPI_RUN --hostfile "$HOSTFILE" -np 8 --map-by ppr:4:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/tp8_${RATE}.log"

    # 3. TP=4 Multi-Node (2 ranks on Node 0 + 2 ranks on Node 1)
    echo ">>> Running Multi-Node AllReduce: TP=4 at $RATE"
    $MPI_RUN --hostfile "$HOSTFILE" -np 4 --map-by ppr:2:node --bind-to none \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=WARN \
        /usr/local/bin/all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1 | tee "$BASE_DIR/tp4_${RATE}.log"
done

cleanup_tc
echo "===================================================================="
echo "ALL ALLREDUCE BENCHMARKS COMPLETED SUCCESSFULLY!"
echo "Results stored in: $BASE_DIR"
echo "===================================================================="
