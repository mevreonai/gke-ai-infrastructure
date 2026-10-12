#!/usr/bin/env bash
# ==============================================================================
# AllGather & ReduceScatter Benchmark Suite — Corrected & Gated
# Runs host-native OpenMPI binaries with hard gates and HTB burst sizing
# ==============================================================================
set -euo pipefail

BASE_DIR="${1:-/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite}"
mkdir -p "$BASE_DIR/allgather" "$BASE_DIR/reducescatter"

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE1_IP="10.128.0.40"
IFACE="ens3"
BIN_DIR="/home/ayu23/rtx_g4_smoke/nccl-tests/build"

# nccl-tests args. -c 0 disables per-iteration host-side verification overhead
NCCL_ARGS="-b 8K -e 256M -f 2 -g 1 -n 50 -w 20 -c 0"
NCCL_ARGS_LOCAL="-b 8K -e 256M -f 2 -g 8 -n 50 -w 20 -c 0"

cleanup_tc() {
    sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
    ssh -o StrictHostKeyChecking=no "$NODE1_IP" "sudo tc qdisc del dev '$IFACE' root 2>/dev/null || true" || true
}
trap cleanup_tc EXIT

apply_tc() {
    local rate="$1"
    cleanup_tc
    if [ "$rate" != "NATIVE" ]; then
        echo "=== [tc] Applying ${rate}Gbps egress cap on $IFACE (both nodes) ==="
        local burst=$(( rate * 1024 * 16 ))
        for host in LOCAL "$NODE1_IP"; do
            local cmd="sudo tc qdisc add dev '$IFACE' root handle 1: htb default 10 && \
                       sudo tc class add dev '$IFACE' parent 1: classid 1:10 htb \
                            rate ${rate}gbit ceil ${rate}gbit burst ${burst}b cburst ${burst}b"
            if [ "$host" = "LOCAL" ]; then eval "$cmd"; else ssh -o StrictHostKeyChecking=no "$host" "$cmd"; fi
        done
        sleep 2
    else
        echo "=== [tc] Unthrottled native link ==="
    fi
}

tc_bytes() { sudo tc -s class show dev "$IFACE" 2>/dev/null | awk '/Sent/{print $2; exit}' || echo 0; }

run_multinode() {
    local coll="$1" np="$2" ppr="$3" rate="$4" log="$5"
    local bin="$BIN_DIR/${coll}_perf"

    local before after
    before=$(tc_bytes)

    /usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun \
        --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root \
        --mca pml ob1 --mca btl tcp,self --mca btl_tcp_if_include "$IFACE" \
        --hostfile "$HOSTFILE" -np "$np" --map-by "ppr:${ppr}:node:PE=4" --bind-to core \
        -x PATH -x LD_LIBRARY_PATH=/opt/cuda-13.0/lib64:/usr/mpi/gcc/openmpi-4.1.9a1/lib64 \
        -x NCCL_SOCKET_IFNAME="$IFACE" \
        -x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET \
        -x NCCL_ALGO=Ring \
        "$bin" $NCCL_ARGS 2>&1 | tee "$log"

    after=$(tc_bytes)

    # GATE 1: Expected rank count across 1 job header
    local nranks nheaders
    nranks=$(grep -cE "Rank +[0-9]+ .*Pid" "$log" || true)
    nheaders=$(grep -c "nThread" "$log" || true)
    if [ "$nranks" -ne "$np" ] || [ "$nheaders" -ne 1 ]; then
        echo "FATAL: expected $np ranks in 1 job; found $nranks rank lines across $nheaders job headers." >&2
        exit 1
    fi

    # GATE 2: Inter-node NET hop verified
    if ! grep -qE "via NET|\[send\] via NET|NET/(Socket|IB)" "$log"; then
        echo "FATAL: no inter-node NET hop found in topology dump." >&2
        exit 1
    fi

    # GATE 3: TC shaper byte counter verification
    if [ "$rate" != "NATIVE" ] && [ "$after" = "$before" ]; then
        echo "FATAL: tc byte counter did not move during a capped run." >&2
        exit 1
    fi
    echo "OK: [$coll] $np ranks, 1 job, NET hops present, tc counted $((after-before)) bytes."
}

# Phase 1: Local Baselines
echo ">>> [Phase 1/2] Node-Local Baselines <<<"
MPI_LOCAL="/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root -x PATH -x LD_LIBRARY_PATH=/opt/cuda-13.0/lib64:/usr/mpi/gcc/openmpi-4.1.9a1/lib64"

for coll in all_gather reduce_scatter; do
    coll_short="${coll//_/}"
    bin="$BIN_DIR/${coll}_perf"
    echo ">>> Running Local TP=4 for $coll <<<"
    $MPI_LOCAL -np 4 -H localhost:4 "$bin" $NCCL_ARGS | tee "$BASE_DIR/$coll_short/tp4.log"
    cp -f "$BASE_DIR/$coll_short/tp4.log" "$BASE_DIR/$coll_short/tp4_local.log"

    echo ">>> Running Local TP=8 for $coll <<<"
    $MPI_LOCAL -np 8 -H localhost:8 "$bin" $NCCL_ARGS | tee "$BASE_DIR/$coll_short/tp8.log"
    cp -f "$BASE_DIR/$coll_short/tp8.log" "$BASE_DIR/$coll_short/tp8_local.log"
done

# Phase 2: Multi-Node Sweeps
echo ">>> [Phase 2/2] Multi-Node Sweeps <<<"
for RATE in NATIVE 100 50 20 10; do
    echo "===================== NETWORK RATE: $RATE ====================="
    apply_tc "$RATE"
    for coll in all_gather reduce_scatter; do
        coll_short="${coll//_/}"
        run_multinode "$coll" 16 8 "$RATE" "$BASE_DIR/$coll_short/tp16_${RATE}.log"
        run_multinode "$coll"  8 4 "$RATE" "$BASE_DIR/$coll_short/tp8_${RATE}.log"
        run_multinode "$coll"  4 2 "$RATE" "$BASE_DIR/$coll_short/tp4_${RATE}.log"
    done
done

cleanup_tc
echo "ALLGATHER & REDUCESCATTER BENCHMARKS COMPLETED AND GATED!"
