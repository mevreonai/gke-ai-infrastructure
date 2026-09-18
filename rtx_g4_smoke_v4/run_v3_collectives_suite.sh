#!/usr/bin/env bash
# ==============================================================================
# Master Unified Distributed Collectives Benchmark Suite (v3)
# Platform: 2x GCP Nodes (16x RTX PRO 6000 Blackwell Server Edition)
# Collectives: SendRecv (2-Node P2P), AllToAll, AllGather, ReduceScatter, AllReduce
# Sweeps: TP=16, TP=8, TP=4 across 5 Network Bandwidths (175G Native, 100G, 50G, 20G, 10G)
# Baselines: Local Node-Local (TP8, TP4, SendRecv Intra-NUMA, SendRecv Cross-NUMA)
# ==============================================================================
set -euo pipefail

BASE_DIR="/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite"
HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE0="10.128.0.39"
NODE1="10.128.0.40"
IFACE="ens3"
BIN_DIR="/home/ayu23/rtx_g4_smoke/nccl-tests/build"
MPI_PREFIX="/usr/mpi/gcc/openmpi-4.1.9a1"
SWEEP_ARGS="-b 8K -e 256M -f 2 -n 25 -w 10 -c 0"

mkdir -p "$BASE_DIR/sendrecv" "$BASE_DIR/alltoall" "$BASE_DIR/allgather" "$BASE_DIR/reducescatter" "$BASE_DIR/allreduce"

MPI_COMMON="$MPI_PREFIX/bin/mpirun --prefix $MPI_PREFIX --allow-run-as-root -x LD_LIBRARY_PATH=/opt/cuda-13.0/lib64:$MPI_PREFIX/lib64"
MPI_MULTI="$MPI_COMMON --mca pml ob1 --mca btl tcp,self --mca btl_tcp_if_include $IFACE --mca oob_tcp_if_include $IFACE -x NCCL_SOCKET_IFNAME=$IFACE -x NCCL_DEBUG=INFO -x NCCL_IB_DISABLE=1 -x NCCL_ALGO=Ring -x NCCL_P2P_LEVEL=SYS -x NCCL_SOCKET_NTHREADS=4 -x NCCL_NSOCKS_PERTHREAD=4"

cleanup_tc() {
    sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
    ssh -o StrictHostKeyChecking=no "$NODE1" "sudo tc qdisc del dev '$IFACE' root 2>/dev/null || true" || true
}
trap cleanup_tc EXIT INT TERM

verify_tc_clean() {
    local l r
    l=$(sudo tc qdisc show dev "$IFACE" | grep -c 'qdisc htb' || true)
    r=$(ssh -o StrictHostKeyChecking=no "$NODE1" "sudo tc qdisc show dev '$IFACE' | grep -c 'qdisc htb'" || echo 1)
    [ "${l:-0}" -eq 0 ] && [ "${r:-0}" -eq 0 ] || echo "WARN: tc teardown verification had non-zero qdisc"
}

apply_tc() {
    local rate="$1"
    cleanup_tc
    if [ "$rate" = "NATIVE" ]; then
        echo "=== [tc] Unthrottled Native Link (173.6 Gbps) ==="
        return 0
    fi
    local burst=$(( rate * 125000 ))
    echo "=== [tc] Applying ${rate}Gbit egress cap on $IFACE (burst ${burst}B, fq_codel leaf) ==="
    local cmd="sudo tc qdisc replace dev $IFACE root handle 1: htb default 10 r2q 1000 && \
               sudo tc class add dev $IFACE parent 1: classid 1:10 htb rate ${rate}gbit ceil ${rate}gbit burst ${burst}b cburst ${burst}b && \
               sudo tc qdisc add dev $IFACE parent 1:10 handle 10: fq_codel"
    eval "$cmd"
    ssh -o StrictHostKeyChecking=no "$NODE1" "$cmd"
    sleep 1
}

# ==============================================================================
# SECTION 1: SENDRECV (2-Node P2P Across Message Sizes)
# ==============================================================================
echo "================================================================="
echo "=== EXECUTING SENDRECV BENCHMARK SUITE ==="
echo "================================================================="

# Local baselines
echo ">>> Running Local SendRecv Intra-NUMA (GPU 0 -> GPU 1)"
$MPI_COMMON -np 2 -H localhost:2 -x CUDA_VISIBLE_DEVICES=0,1 "$BIN_DIR/sendrecv_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/sendrecv/sendrecv_local_intra_numa.log"

echo ">>> Running Local SendRecv Cross-NUMA (GPU 0 -> GPU 4)"
$MPI_COMMON -np 2 -H localhost:2 -x CUDA_VISIBLE_DEVICES=0,4 "$BIN_DIR/sendrecv_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/sendrecv/sendrecv_local_cross_numa.log"

# Multi-node sweeps
for RATE in NATIVE 100 50 20 10; do
    echo ">>> Running 2-Node SendRecv (Node 0 Rank 0 -> Node 1 Rank 1) at $RATE"
    apply_tc "$RATE"
    $MPI_MULTI -np 2 --host "$NODE0:1,$NODE1:1" "$BIN_DIR/sendrecv_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/sendrecv/sendrecv_2node_${RATE}.log"
done
cleanup_tc

# ==============================================================================
# SECTION 2: ALLTOALL (TP16, TP8, TP4 Across 5 Network Rates + Local)
# ==============================================================================
echo "================================================================="
echo "=== EXECUTING ALLTOALL BENCHMARK SUITE ==="
echo "================================================================="

# Local baselines (OpenMPI on localhost to prevent ATS dual-socket deadlock)
echo ">>> Running Local TP=8 AllToAll"
$MPI_COMMON -np 8 -H localhost:8 "$BIN_DIR/alltoall_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/alltoall/tp8_local.log"

echo ">>> Running Local TP=4 AllToAll (Socket-Local NUMA0)"
$MPI_COMMON -np 4 -H localhost:4 -x CUDA_VISIBLE_DEVICES=0,1,2,3 "$BIN_DIR/alltoall_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/alltoall/tp4_local.log"

# Multi-node sweeps
for RATE in NATIVE 100 50 20 10; do
    apply_tc "$RATE"
    echo ">>> Running TP=16 AllToAll at $RATE"
    $MPI_MULTI -np 16 --hostfile "$HOSTFILE" "$BIN_DIR/alltoall_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/alltoall/tp16_${RATE}.log"

    echo ">>> Running TP=8 Multi-Node AllToAll at $RATE"
    $MPI_MULTI -np 8 --host "$NODE0:4,$NODE1:4" "$BIN_DIR/alltoall_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/alltoall/tp8_${RATE}.log"

    echo ">>> Running TP=4 Multi-Node AllToAll at $RATE"
    $MPI_MULTI -np 4 --host "$NODE0:2,$NODE1:2" "$BIN_DIR/alltoall_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/alltoall/tp4_${RATE}.log"
done
cleanup_tc

# ==============================================================================
# SECTION 3: ALLGATHER (TP16, TP8, TP4 Across 5 Network Rates + Local)
# ==============================================================================
echo "================================================================="
echo "=== EXECUTING ALLGATHER BENCHMARK SUITE ==="
echo "================================================================="

echo ">>> Running Local TP=8 AllGather"
$MPI_COMMON -np 8 -H localhost:8 "$BIN_DIR/all_gather_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allgather/tp8_local.log"

echo ">>> Running Local TP=4 AllGather"
$MPI_COMMON -np 4 -H localhost:4 -x CUDA_VISIBLE_DEVICES=0,1,2,3 "$BIN_DIR/all_gather_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allgather/tp4_local.log"

for RATE in NATIVE 100 50 20 10; do
    apply_tc "$RATE"
    echo ">>> Running TP=16 AllGather at $RATE"
    $MPI_MULTI -np 16 --hostfile "$HOSTFILE" "$BIN_DIR/all_gather_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allgather/tp16_${RATE}.log"

    echo ">>> Running TP=8 Multi-Node AllGather at $RATE"
    $MPI_MULTI -np 8 --host "$NODE0:4,$NODE1:4" "$BIN_DIR/all_gather_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allgather/tp8_${RATE}.log"

    echo ">>> Running TP=4 Multi-Node AllGather at $RATE"
    $MPI_MULTI -np 4 --host "$NODE0:2,$NODE1:2" "$BIN_DIR/all_gather_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allgather/tp4_${RATE}.log"
done
cleanup_tc

# ==============================================================================
# SECTION 4: REDUCESCATTER (TP16, TP8, TP4 Across 5 Network Rates + Local)
# ==============================================================================
echo "================================================================="
echo "=== EXECUTING REDUCESCATTER BENCHMARK SUITE ==="
echo "================================================================="

echo ">>> Running Local TP=8 ReduceScatter"
$MPI_COMMON -np 8 -H localhost:8 "$BIN_DIR/reduce_scatter_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/reducescatter/tp8_local.log"

echo ">>> Running Local TP=4 ReduceScatter"
$MPI_COMMON -np 4 -H localhost:4 -x CUDA_VISIBLE_DEVICES=0,1,2,3 "$BIN_DIR/reduce_scatter_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/reducescatter/tp4_local.log"

for RATE in NATIVE 100 50 20 10; do
    apply_tc "$RATE"
    echo ">>> Running TP=16 ReduceScatter at $RATE"
    $MPI_MULTI -np 16 --hostfile "$HOSTFILE" "$BIN_DIR/reduce_scatter_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/reducescatter/tp16_${RATE}.log"

    echo ">>> Running TP=8 Multi-Node ReduceScatter at $RATE"
    $MPI_MULTI -np 8 --host "$NODE0:4,$NODE1:4" "$BIN_DIR/reduce_scatter_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/reducescatter/tp8_${RATE}.log"

    echo ">>> Running TP=4 Multi-Node ReduceScatter at $RATE"
    $MPI_MULTI -np 4 --host "$NODE0:2,$NODE1:2" "$BIN_DIR/reduce_scatter_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/reducescatter/tp4_${RATE}.log"
done
cleanup_tc

# ==============================================================================
# SECTION 5: ALLREDUCE (TP16, TP8, TP4 Across 5 Network Rates + Local)
# ==============================================================================
echo "================================================================="
echo "=== EXECUTING ALLREDUCE BENCHMARK SUITE ==="
echo "================================================================="

echo ">>> Running Local TP=8 AllReduce"
$MPI_COMMON -np 8 -H localhost:8 "$BIN_DIR/all_reduce_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allreduce/tp8_local.log"

echo ">>> Running Local TP=4 AllReduce"
$MPI_COMMON -np 4 -H localhost:4 -x CUDA_VISIBLE_DEVICES=0,1,2,3 "$BIN_DIR/all_reduce_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allreduce/tp4_local.log"

for RATE in NATIVE 100 50 20 10; do
    apply_tc "$RATE"
    echo ">>> Running TP=16 AllReduce at $RATE"
    $MPI_MULTI -np 16 --hostfile "$HOSTFILE" "$BIN_DIR/all_reduce_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allreduce/tp16_${RATE}.log"

    echo ">>> Running TP=8 Multi-Node AllReduce at $RATE"
    $MPI_MULTI -np 8 --host "$NODE0:4,$NODE1:4" "$BIN_DIR/all_reduce_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allreduce/tp8_${RATE}.log"

    echo ">>> Running TP=4 Multi-Node AllReduce at $RATE"
    $MPI_MULTI -np 4 --host "$NODE0:2,$NODE1:2" "$BIN_DIR/all_reduce_perf" $SWEEP_ARGS -g 1 > "$BASE_DIR/allreduce/tp4_${RATE}.log"
done
cleanup_tc

echo "================================================================="
echo "ALL BENCHMARKS COMPLETED SUCCESSFULLY!"
echo "Packaging output logs into tarball..."
tar -czf /home/ayu23/rtx_g4_smoke/fresh_suite_all_collectives.tgz -C "$BASE_DIR" sendrecv alltoall allgather reducescatter allreduce
echo "Archive created: /home/ayu23/rtx_g4_smoke/fresh_suite_all_collectives.tgz"
echo "================================================================="
