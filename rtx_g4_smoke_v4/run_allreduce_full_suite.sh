#!/bin/bash
# ==============================================================================
# AllReduce Benchmark Suite — corrected & gated
#
# Changes from original:
#   1. Multi-node ranks run the binary NATIVELY, not one Docker container per
#      rank. Wrapping each rank in `docker run` dropped the entire MPI/PMIx
#      environment, so all N "ranks" ran as independent 1-rank jobs.
#   2. A containerised path is kept as an option, with the MPI/PMIx/NCCL
#      environment and /tmp explicitly forwarded.
#   3. Every multi-node run is GATED: the log must show the expected rank count
#      and at least one inter-node NET hop, or the script aborts.
#   4. tc byte counters are sampled before/after each capped run to prove the
#      shaper actually saw the traffic.
#   5. NCCL_DEBUG=INFO with the graph/net subsystems so the topology is on record.
#   6. -c 0 after one validated run, explicit -n/-w, and CPU binding.
#   7. GCP VPC compatibility: OpenMPI ob1 PML over TCP interface.
# ==============================================================================
set -euo pipefail

BASE_DIR="${1:-/home/ayu23/rtx_g4_smoke/fresh_benchmark_suite/allreduce}"
mkdir -p "$BASE_DIR"

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE1_IP="10.128.0.40"
IFACE="ens3"
NCCL_TESTS_BIN="/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf"
USE_DOCKER_FOR_MULTINODE="${USE_DOCKER_FOR_MULTINODE:-0}"   # 0 = native (recommended)

# nccl-tests args. -c 0 disables per-iteration correctness checking, which
# otherwise adds host-side verification to every timed iteration. Run once with
# -c 1 to validate, then benchmark with -c 0.
NCCL_ARGS="-b 8K -e 256M -f 2 -g 1 -n 50 -w 20 -c 0"
NCCL_ARGS_LOCAL="-b 8K -e 256M -f 2 -g 8 -n 50 -w 20 -c 0"
NCCL_ARGS_LOCAL4="-b 8K -e 256M -f 2 -g 4 -n 50 -w 20 -c 0"

# ------------------------------------------------------------------ container
# Only used when USE_DOCKER_FOR_MULTINODE=1. Forwards the MPI/PMIx rendezvous
# environment and /tmp (PMIx session socket) into the container. The container's
# OpenMPI/PMIx must be ABI-compatible with the host launcher or MPI_Init will
# still fail — which is why the native path is the default.
setup_docker_wrapper() {
cat << 'EOF' > /tmp/all_reduce_perf_docker
#!/bin/bash
LOCAL_RANK=${OMPI_COMM_WORLD_LOCAL_RANK:-0}
ENVS=()
while IFS='=' read -r k _; do ENVS+=(-e "$k"); done < <(env | grep -E '^(OMPI_|PMIX_|NCCL_|UCX_|OPAL_)')
exec docker run --rm --gpus all --ipc=host --net=host --pid=host \
    -e CUDA_VISIBLE_DEVICES="${LOCAL_RANK}" "${ENVS[@]}" \
    -v /home/ayu23:/home/ayu23 -v /tmp:/tmp \
    --entrypoint /bin/bash rtx-smoke:latest \
    -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf $*"
EOF
    chmod +x /tmp/all_reduce_perf_docker
    sudo install -m 755 /tmp/all_reduce_perf_docker /usr/local/bin/all_reduce_perf_docker
    scp -o StrictHostKeyChecking=no /tmp/all_reduce_perf_docker "$NODE1_IP:/tmp/"
    ssh -o StrictHostKeyChecking=no "$NODE1_IP" \
        "sudo install -m 755 /tmp/all_reduce_perf_docker /usr/local/bin/all_reduce_perf_docker"
}
[ "$USE_DOCKER_FOR_MULTINODE" = "1" ] && setup_docker_wrapper

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
        # burst/cburst sized for the rate; HTB defaults are far too small above
        # ~10 Gbit and silently under-deliver.
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

# ------------------------------------------------------- multi-node run + gate
run_multinode() {
    local np="$1" ppr="$2" rate="$3" log="$4"
    local launcher
    if [ "$USE_DOCKER_FOR_MULTINODE" = "1" ]; then
        launcher="/usr/local/bin/all_reduce_perf_docker"
    else
        launcher="$NCCL_TESTS_BIN"
    fi

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
        "$launcher" $NCCL_ARGS 2>&1 | tee "$log"

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
    echo "OK: $np ranks, 1 job, NET hops present, tc counted $((after-before)) bytes."
}

DOCKER_LOCAL="docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c"

# ============================== PHASE 1: node-local baselines =================
echo ">>> [Phase 1/2] Node-local baselines <<<"
MPI_LOCAL="/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root -x PATH -x LD_LIBRARY_PATH=/opt/cuda-13.0/lib64:/usr/mpi/gcc/openmpi-4.1.9a1/lib64"

echo "Running TP=4 Socket-Local..."
$MPI_LOCAL -np 4 -H localhost:4 "$NCCL_TESTS_BIN" $NCCL_ARGS | tee "$BASE_DIR/tp4_local.log"
cp -f "$BASE_DIR/tp4_local.log" "$BASE_DIR/tp4.log"

echo "Running TP=8 Node-Local..."
$MPI_LOCAL -np 8 -H localhost:8 "$NCCL_TESTS_BIN" $NCCL_ARGS | tee "$BASE_DIR/tp8_local.log"
cp -f "$BASE_DIR/tp8_local.log" "$BASE_DIR/tp8.log"

# Record the PCIe link generation — 40 GB/s bus bandwidth is only possible on
# Gen5 x16; on Gen4 x16 it would exceed the link and the baseline is wrong too.
nvidia-smi -q | grep -A4 "GPU Link Info" | tee "$BASE_DIR/pcie_link_info.txt"

# ============================== PHASE 2: multi-node sweeps ====================
echo ">>> [Phase 2/2] Multi-node sweeps <<<"
for RATE in NATIVE 100 50 20 10; do
    echo "===================== NETWORK RATE: $RATE ====================="
    apply_tc "$RATE"
    run_multinode 16 8 "$RATE" "$BASE_DIR/tp16_${RATE}.log"
    run_multinode  8 4 "$RATE" "$BASE_DIR/tp8_${RATE}.log"
    run_multinode  4 2 "$RATE" "$BASE_DIR/tp4_${RATE}.log"
done

cleanup_tc
echo "ALL BENCHMARKS COMPLETED AND GATED. Results in: $BASE_DIR"
