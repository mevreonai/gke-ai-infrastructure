#!/bin/bash
# ==============================================================================
# Full Multi-Collective Benchmark Suite (AllReduce, AllGather, ReduceScatter)
# Incorporating 3 Hard Gates, HTB burst sizing, and native OpenMPI execution
# ==============================================================================
set -euo pipefail

BASE_DIR="${1:-/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite}"
mkdir -p "$BASE_DIR/allreduce" "$BASE_DIR/allgather" "$BASE_DIR/reducescatter"

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE1_IP="10.128.0.40"
IFACE="ens3"
BIN_DIR="/home/ayu23/rtx_g4_smoke/nccl-tests/build"

# nccl-tests args: -c 0 disables per-iteration correctness checking
NCCL_ARGS="-b 8K -e 256M -f 2 -g 1 -n 50 -w 20 -c 0"
NCCL_ARGS_LOCAL="-b 8K -e 256M -f 2 -g 8 -n 50 -w 20 -c 0"
NCCL_ARGS_LOCAL4="-b 8K -e 256M -f 2 -g 4 -n 50 -w 20 -c 0"

# ------------------------------------------------------------------- tc helpers
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

# ------------------------------------------------------- multi-node run + gates
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

    # ---- GATE 1: exactly $np ranks took part, in ONE job ----------------------
    local nranks nheaders
    nranks=$(grep -cE "Rank +[0-9]+ .*Pid" "$log" || true)
    nheaders=$(grep -c "nThread" "$log" || true)
    if [ "$nranks" -ne "$np" ] || [ "$nheaders" -ne 1 ]; then
        echo "FATAL: expected $np ranks in 1 job; found $nranks rank lines across $nheaders job headers." >&2
        echo "       More than one header means the ranks ran as independent jobs." >&2
        exit 1
    fi

    # ---- GATE 2: at least one ring hop actually crossed the network ----------
    if ! grep -qE "via NET|\[send\] via NET|NET/(Socket|IB)" "$log"; then
        echo "FATAL: no inter-node NET hop in the topology dump — ranks never left a host." >&2
        exit 1
    fi

    # ---- GATE 3: the shaper saw the traffic ---------------------------------
    if [ "$rate" != "NATIVE" ] && [ "$after" = "$before" ]; then
        echo "FATAL: tc byte counter did not move during a capped run." >&2
        echo "       The cap is on an interface NCCL is not using." >&2
        exit 1
    fi
    echo "OK: [$coll] $np ranks, 1 job, NET hops present, tc counted $((after-before)) bytes."
}

DOCKER_LOCAL="docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c"

# ============================== PHASE 1: node-local baselines =================
echo ">>> [Phase 1/2] Node-local baselines <<<"
for coll in all_reduce all_gather reduce_scatter; do
    coll_short="${coll//_/}"
    bin="$BIN_DIR/${coll}_perf"
    $DOCKER_LOCAL "CUDA_VISIBLE_DEVICES=0,1,2,3 NCCL_P2P_LEVEL=SYS NCCL_DEBUG=INFO $bin $NCCL_ARGS_LOCAL4" | tee "$BASE_DIR/$coll_short/tp4.log"
    $DOCKER_LOCAL "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 NCCL_P2P_LEVEL=SYS NCCL_DEBUG=INFO $bin $NCCL_ARGS_LOCAL" | tee "$BASE_DIR/$coll_short/tp8.log"
done

nvidia-smi -q | grep -A4 "GPU Link Info" | tee "$BASE_DIR/pcie_link_info.txt"

# ============================== PHASE 2: multi-node sweeps ====================
echo ">>> [Phase 2/2] Multi-node sweeps <<<"
for RATE in NATIVE 100 50 20 10; do
    echo "===================== NETWORK RATE: $RATE ====================="
    apply_tc "$RATE"
    for coll in all_reduce all_gather reduce_scatter; do
        coll_short="${coll//_/}"
        run_multinode "$coll" 16 8 "$RATE" "$BASE_DIR/$coll_short/tp16_${RATE}.log"
        run_multinode "$coll"  8 4 "$RATE" "$BASE_DIR/$coll_short/tp8_${RATE}.log"
        run_multinode "$coll"  4 2 "$RATE" "$BASE_DIR/$coll_short/tp4_${RATE}.log"
    done
done

cleanup_tc
echo "ALL BENCHMARKS COMPLETED AND GATED. Results in: $BASE_DIR"
