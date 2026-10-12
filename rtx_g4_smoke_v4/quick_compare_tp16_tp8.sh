#!/usr/bin/env bash
set -euo pipefail

echo "================================================================="
echo "QUICK ALLREDUCE COMPARISON: TP-16 MULTI-NODE vs TP-8 SINGLE-NODE"
echo "Payload sizes: 16M, 64M, 128M, 256M"
echo "Network rates: 175G (Native), 100G, 50G, 20G, 10G"
echo "================================================================="

HOSTFILE="/home/ayu23/rtx_g4_smoke/hosts"
NODE0="10.128.0.39"
NODE1="10.128.0.40"
IFACE="ens3"
BIN="/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf"
OUT_DIR="/tmp/quick_compare"
mkdir -p "$OUT_DIR"

cleanup_tc() {
    sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
    ssh -o StrictHostKeyChecking=no "$NODE1" "sudo tc qdisc del dev '$IFACE' root 2>/dev/null || true" || true
}
trap cleanup_tc EXIT

apply_tc() {
    local rate="$1"
    cleanup_tc
    if [ "$rate" != "NATIVE" ]; then
        echo ">>> [tc] Applying ${rate}Gbps traffic cap..."
        local burst=$(( rate * 1024 * 16 ))
        for host in LOCAL "$NODE1"; do
            local cmd="sudo tc qdisc add dev '$IFACE' root handle 1: htb default 10 && \
                       sudo tc class add dev '$IFACE' parent 1: classid 1:10 htb \
                            rate ${rate}gbit ceil ${rate}gbit burst ${burst}b cburst ${burst}b"
            if [ "$host" = "LOCAL" ]; then eval "$cmd"; else ssh -o StrictHostKeyChecking=no "$host" "$cmd"; fi
        done
        sleep 1
    else
        echo ">>> [tc] Native 175G line rate (unthrottled)"
    fi
}

tc_bytes() { sudo tc -s class show dev "$IFACE" 2>/dev/null | awk '/Sent/{print $2; exit}' || echo 0; }

MPI_COMMON="/usr/mpi/gcc/openmpi-4.1.9a1/bin/mpirun --prefix /usr/mpi/gcc/openmpi-4.1.9a1 --allow-run-as-root \
  -x PATH -x LD_LIBRARY_PATH=/opt/cuda-13.0/lib64:/usr/mpi/gcc/openmpi-4.1.9a1/lib64"

# 1. Single Node TP-8 Local Baseline (PCIe Gen5 across 8 GPUs)
echo "-----------------------------------------------------------------"
echo "STEP 1: Running TP-8 Single Node Local Baseline (8 GPUs, node 0)"
echo "-----------------------------------------------------------------"
cleanup_tc
$MPI_COMMON -np 8 -H localhost:8 "$BIN" -b 16M -e 256M -f 4 -g 1 -n 20 -w 5 -c 0 2>&1 | tee "$OUT_DIR/tp8_local.log"

# 2. Multi-Node TP-16 Sweep across 5 Network Caps
echo "-----------------------------------------------------------------"
echo "STEP 2: Running TP-16 Multi-Node across 5 Network Caps"
echo "-----------------------------------------------------------------"
RATES="NATIVE 100 50 20 10"

for RATE in $RATES; do
    echo "=== Running TP-16 Multi-Node at Rate: $RATE ==="
    apply_tc "$RATE"
    BEFORE=$(tc_bytes)

    $MPI_COMMON --mca pml ob1 --mca btl tcp,self --mca btl_tcp_if_include "$IFACE" \
        -H "$NODE0:8,$NODE1:8" -np 16 --map-by "ppr:8:node:PE=4" --bind-to core \
        -x NCCL_SOCKET_IFNAME="$IFACE" -x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET -x NCCL_ALGO=Ring \
        "$BIN" -b 16M -e 256M -f 4 -g 1 -n 20 -w 5 -c 0 2>&1 | tee "$OUT_DIR/tp16_${RATE}.log"

    AFTER=$(tc_bytes)

    # Gate verification
    NHEADERS=$(grep -c "nThread" "$OUT_DIR/tp16_${RATE}.log" || true)
    NRANKS=$(grep -cE "Rank +[0-9]+ .*Pid" "$OUT_DIR/tp16_${RATE}.log" || true)
    if [ "$NHEADERS" -ne 1 ] || [ "$NRANKS" -ne 16 ]; then
        echo "ERROR: Gate 1 failed for TP-16 $RATE: expected 16 ranks, 1 header; got $NRANKS ranks, $NHEADERS headers" >&2
        exit 1
    fi
    if ! grep -qE "via NET|\[send\] via NET|NET/(Socket|IB)" "$OUT_DIR/tp16_${RATE}.log"; then
        echo "ERROR: Gate 2 failed: no inter-node NET hops detected!" >&2
        exit 1
    fi
    if [ "$RATE" != "NATIVE" ] && [ "$AFTER" = "$BEFORE" ]; then
        echo "ERROR: Gate 3 failed: TC byte counter did not move!" >&2
        exit 1
    fi
    echo "GATE VERIFICATION PASSED: TP-16 $RATE counted $((AFTER-BEFORE)) shaped bytes over $IFACE."
done

cleanup_tc
echo "================================================================="
echo "SWEEPS FINISHED! GENERATING SUMMARY..."
echo "================================================================="
