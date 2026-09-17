#!/usr/bin/env bash
set -euo pipefail

echo "================================================================="
echo "STARTING COMPLETE REAL MULTI-NODE BENCHMARK SUITE (OPENMPI NATIVE)"
echo "Nodes: kimi-node-0 (10.128.0.39), kimi-node-1 (10.128.0.40)"
echo "Collectives: AllReduce, AllGather, ReduceScatter"
echo "Topologies : Local TP=8, Local TP=4, Multi-Node TP=16, Multi-Node TP=8, Multi-Node TP=4"
echo "Rates      : NATIVE (175G), 100G, 50G, 20G, 10G"
echo "Buffers    : 8 KiB to 256 MiB (-b 8K -e 256M -f 2 -g 1)"
echo "================================================================="

BASE_DIR="/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite"
mkdir -p "$BASE_DIR/allreduce" "$BASE_DIR/allgather" "$BASE_DIR/reducescatter"

NODE0="10.128.0.39"
NODE1="10.128.0.40"
IFACE="ens3"
BIN_DIR="/home/ayu23/rtx_g4_smoke/nccl-tests/build"
MPI_PREFIX="/usr/mpi/gcc/openmpi-4.1.9a1"
MPI_COMMON="$MPI_PREFIX/bin/mpirun --prefix $MPI_PREFIX -x LD_LIBRARY_PATH=/opt/cuda-13.0/lib64:$MPI_PREFIX/lib64"
MPI_MULTI="$MPI_COMMON --mca pml ob1 --mca btl tcp,self --mca btl_tcp_if_include $IFACE -x NCCL_SOCKET_IFNAME=$IFACE -x NCCL_DEBUG=WARN"

cleanup_tc() {
    sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
    ssh -o StrictHostKeyChecking=no "$NODE1" "sudo tc qdisc del dev '$IFACE' root 2>/dev/null || true" || true
}
trap cleanup_tc EXIT

apply_tc() {
    local rate="$1"
    cleanup_tc
    if [ "$rate" != "NATIVE" ]; then
        echo "=== Applying traffic cap: ${rate}Gbit on $IFACE ==="
        sudo tc qdisc add dev "$IFACE" root tbf rate "${rate}gbit" burst 256kb latency 50ms
        ssh -o StrictHostKeyChecking=no "$NODE1" "sudo tc qdisc add dev '$IFACE' root tbf rate '${rate}gbit' burst 256kb latency 50ms"
        sleep 1
    else
        echo "=== Running on unthrottled GCP NATIVE (173.6 Gbps) ==="
    fi
}

declare -A BIN_MAP=(
    ["allreduce"]="all_reduce_perf"
    ["allgather"]="all_gather_perf"
    ["reducescatter"]="reduce_scatter_perf"
)

# 1. LOCAL BASELINES (Single-Node Node 0)
echo "================================================================"
echo "=== STEP 1: RUNNING LOCAL SINGLE-NODE BASELINES ==="
echo "================================================================"
cleanup_tc

for COLL in allreduce allgather reducescatter; do
    PROG="${BIN_MAP[$COLL]}"
    echo ">>> Running Local TP=8 $COLL"
    $MPI_COMMON -np 8 -H localhost:8 "$BIN_DIR/$PROG" -b 8K -e 256M -f 2 -g 1 > "$BASE_DIR/$COLL/tp8.log"
    echo ">>> Running Local TP=4 $COLL"
    $MPI_COMMON -np 4 -H localhost:4 "$BIN_DIR/$PROG" -b 8K -e 256M -f 2 -g 1 > "$BASE_DIR/$COLL/tp4.log"
done

# 2. MULTI-NODE SWEEP ACROSS ALL 5 RATES
echo "================================================================"
echo "=== STEP 2: RUNNING MULTI-NODE DISTRIBUTED SWEEPS ==="
echo "================================================================"

RATES="NATIVE 100 50 20 10"

for RATE in $RATES; do
    echo "========================================================"
    echo "=== NETWORK RATE: $RATE ==="
    echo "========================================================"
    apply_tc "$RATE"

    for COLL in allreduce allgather reducescatter; do
        PROG="${BIN_MAP[$COLL]}"

        echo ">>> Running Multi-Node TP=16 $COLL ($RATE)"
        $MPI_MULTI -np 16 -H "$NODE0:8,$NODE1:8" "$BIN_DIR/$PROG" -b 8K -e 256M -f 2 -g 1 > "$BASE_DIR/$COLL/tp16_${RATE}.log"

        echo ">>> Running Multi-Node TP=8 $COLL ($RATE)"
        $MPI_MULTI -np 8 -H "$NODE0:4,$NODE1:4" "$BIN_DIR/$PROG" -b 8K -e 256M -f 2 -g 1 > "$BASE_DIR/$COLL/tp8_${RATE}.log"

        echo ">>> Running Multi-Node TP=4 $COLL ($RATE)"
        $MPI_MULTI -np 4 -H "$NODE0:2,$NODE1:2" "$BIN_DIR/$PROG" -b 8K -e 256M -f 2 -g 1 > "$BASE_DIR/$COLL/tp4_${RATE}.log"
    done
done

cleanup_tc
echo "================================================================"
echo "ALL MULTI-NODE BENCHMARKS COMPLETED SUCCESSFULLY!"
echo "================================================================"
