#!/usr/bin/env bash
# ==============================================================================
# Universal Gated NCCL Kernel Runner (Host-Native OpenMPI)
# Supports: all_reduce, all_gather, reduce_scatter, sendrecv, alltoall, broadcast, reduce
# ==============================================================================
set -euo pipefail

KERNEL="${1:-all_reduce}"
TOPOLOGY="${2:-tp16}"
RATE="${3:-NATIVE}"

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE0_IP="10.128.0.39"
NODE1_IP="10.128.0.40"
IFACE="ens3"
BIN_DIR="/home/ayu23/rtx_g4_smoke/nccl-tests/build"
PROG="$BIN_DIR/${KERNEL}_perf"

if [ ! -f "$PROG" ]; then
    echo "ERROR: Kernel binary $PROG does not exist!" >&2
    exit 2
fi

cleanup_tc() {
    sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
    ssh -o StrictHostKeyChecking=no "$NODE1_IP" "sudo tc qdisc del dev '$IFACE' root 2>/dev/null || true" || true
}
trap cleanup_tc EXIT

apply_tc() {
    local rate="$1"
    cleanup_tc
    if [ "$rate" != "NATIVE" ]; then
        echo "=== [tc] Applying ${rate}Gbps egress cap on $IFACE ==="
        local burst=$(( rate * 1024 * 16 ))
        for host in LOCAL "$NODE1_IP"; do
            local cmd="sudo tc qdisc add dev '$IFACE' root handle 1: htb default 10 && \
                       sudo tc class add dev '$IFACE' parent 1: classid 1:10 htb \
                            rate ${rate}gbit ceil ${rate}gbit burst ${burst}b cburst ${burst}b"
            if [ "$host" = "LOCAL" ]; then eval "$cmd"; else ssh -o StrictHostKeyChecking=no "$host" "$cmd"; fi
        done
        sleep 2
    fi
}

tc_bytes() { sudo tc -s class show dev "$IFACE" 2>/dev/null | awk '/Sent/{print $2; exit}' || echo 0; }

apply_tc "$RATE"

MPI_COMMON="/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root \
  -x PATH -x LD_LIBRARY_PATH=/opt/cuda-13.0/lib64:/usr/mpi/gcc/openmpi-4.1.9a1/lib64"

LOG_FILE="/tmp/${KERNEL}_${TOPOLOGY}_${RATE}.log"
BEFORE=$(tc_bytes)

if [ "$TOPOLOGY" = "tp8_local" ]; then
    echo ">>> Running Single-Node TP=8 Local ($KERNEL)"
    $MPI_COMMON -np 8 -H localhost:8 "$PROG" -b 8K -e 256M -f 2 -g 1 -n 50 -w 20 -c 0 2>&1 | tee "$LOG_FILE"
elif [ "$TOPOLOGY" = "tp16" ]; then
    echo ">>> Running Multi-Node TP=16 ($KERNEL, $RATE)"
    $MPI_COMMON --mca pml ob1 --mca btl tcp,self --mca btl_tcp_if_include "$IFACE" \
        -H "$NODE0_IP:8,$NODE1_IP:8" -np 16 --map-by "ppr:8:node:PE=4" --bind-to core \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET -x NCCL_ALGO=Ring \
        "$PROG" -b 8K -e 256M -f 2 -g 1 -n 50 -w 20 -c 0 2>&1 | tee "$LOG_FILE"
elif [ "$TOPOLOGY" = "tp8" ]; then
    echo ">>> Running Multi-Node TP=8 ($KERNEL, $RATE)"
    $MPI_COMMON --mca pml ob1 --mca btl tcp,self --mca btl_tcp_if_include "$IFACE" \
        -H "$NODE0_IP:4,$NODE1_IP:4" -np 8 --map-by "ppr:4:node:PE=4" --bind-to core \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET -x NCCL_ALGO=Ring \
        "$PROG" -b 8K -e 256M -f 2 -g 1 -n 50 -w 20 -c 0 2>&1 | tee "$LOG_FILE"
elif [ "$TOPOLOGY" = "sendrecv" ]; then
    echo ">>> Running Point-to-Point SendRecv ($RATE)"
    $MPI_COMMON --mca pml ob1 --mca btl tcp,self --mca btl_tcp_if_include "$IFACE" \
        -H "$NODE0_IP:1,$NODE1_IP:1" -np 2 --map-by "ppr:1:node" \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=INFO \
        "$PROG" -b 8K -e 256M -f 2 -g 1 -n 50 -w 20 -c 0 2>&1 | tee "$LOG_FILE"
fi

AFTER=$(tc_bytes)

# Validate Gates for multi-node
if [ "$TOPOLOGY" != "tp8_local" ]; then
    echo "=== Running Quality Gates ==="
    NHEADERS=$(grep -c "nThread" "$LOG_FILE" || true)
    if [ "$NHEADERS" -ne 1 ]; then
        echo "FATAL GATE 1: Expected exactly 1 job header; found $NHEADERS" >&2
        exit 1
    fi
    if ! grep -qE "via NET|\[send\] via NET|NET/(Socket|IB)" "$LOG_FILE"; then
        echo "FATAL GATE 2: No inter-node NET hops detected in log!" >&2
        exit 1
    fi
    if [ "$RATE" != "NATIVE" ] && [ "$AFTER" = "$BEFORE" ]; then
        echo "FATAL GATE 3: TC shaper byte counter did not increment!" >&2
        exit 1
    fi
    echo "ALL GATES PASSED: 1 job header, real NET traffic verified, TC counted $((AFTER-BEFORE)) bytes."
fi
