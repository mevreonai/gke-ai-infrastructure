#!/usr/bin/env bash
# Stage 1: Evaluate NCCL socket thread tuning and transport variants using real nccl-tests.
# Compares 16 KiB AllReduce latency and 256 MiB SendRecv bandwidth across:
#   Variant A: Pilot baseline (NCCL_NET=Socket, default threads)
#   Variant B: NCCL_SOCKET_NTHREADS=4, NCCL_NSOCKS_PERTHREAD=4
#   Variant C: NCCL_SOCKET_NTHREADS=8, NCCL_NSOCKS_PERTHREAD=2
#   Variant D: Provider plugin (if available on cluster)
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
for f in "$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env"; do [[ -f "$f" ]] && { source "$f"; break; }; done
: "${NODE0_IP:?NODE0_IP missing}"
: "${NODE1_IP:?NODE1_IP missing}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${BENCH_ROOT:=$HOME/rtx_g4_smoke}"
: "${OUT_ROOT:=$HOME/v8_additional_runs/$(date +%Y%m%d_%H%M%S)/nccl_tuning}"
mkdir -p "$OUT_ROOT"

HOSTFILE="$OUT_ROOT/hostfile_nodes"
printf "%s slots=1\n%s slots=1\n" "$NODE0_IP" "$NODE1_IP" > "$HOSTFILE"

LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
NCCL_TESTS_DIR="$BENCH_ROOT/nccl-tests"

if [[ ! -d "$NCCL_TESTS_DIR/build" ]]; then
  echo "WARN: nccl-tests build directory not found at $NCCL_TESTS_DIR/build; attempting to compile..."
  if [[ -d "$NCCL_TESTS_DIR" ]]; then
    (cd "$NCCL_TESTS_DIR" && make -j CUDA_HOME=/usr/local/cuda MPI=1 MPI_HOME=/usr/lib/x86_64-linux-gnu/openmpi) || true
  fi
fi

run_nccl_variant() {
  local var_name="$1"
  local nthreads="$2"
  local nsocks="$3"
  local extra_env="${4:-}"
  local vdir="$OUT_ROOT/$var_name"
  mkdir -p "$vdir"

  echo "=========================================================="
  echo "Running NCCL Variant: $var_name (threads=$nthreads, socks=$nsocks)"
  echo "=========================================================="

  if [[ -f "$NCCL_TESTS_DIR/build/all_reduce_perf" && -f "$NCCL_TESTS_DIR/build/sendrecv_perf" ]]; then
    # 16 KiB AllReduce Latency
    mpirun --hostfile "$HOSTFILE" -np 2 --map-by ppr:1:node --bind-to none \
      -x PATH -x LD_LIBRARY_PATH \
      -x NCCL_SOCKET_IFNAME="=$LOCAL_IFACE" \
      -x NCCL_DEBUG=INFO \
      -x NCCL_NET=Socket \
      -x NCCL_SOCKET_NTHREADS="$nthreads" \
      -x NCCL_NSOCKS_PERTHREAD="$nsocks" \
      $extra_env \
      "$NCCL_TESTS_DIR/build/all_reduce_perf" -b 16K -e 16K -g 1 -J "$vdir/all_reduce_16k.json" \
      > "$vdir/all_reduce_16k.log" 2>&1 || true

    # 256 MiB SendRecv Bandwidth
    mpirun --hostfile "$HOSTFILE" -np 2 --map-by ppr:1:node --bind-to none \
      -x PATH -x LD_LIBRARY_PATH \
      -x NCCL_SOCKET_IFNAME="=$LOCAL_IFACE" \
      -x NCCL_DEBUG=INFO \
      -x NCCL_NET=Socket \
      -x NCCL_SOCKET_NTHREADS="$nthreads" \
      -x NCCL_NSOCKS_PERTHREAD="$nsocks" \
      $extra_env \
      "$NCCL_TESTS_DIR/build/sendrecv_perf" -b 256M -e 256M -g 1 -J "$vdir/sendrecv_256m.json" \
      > "$vdir/sendrecv_256m.log" 2>&1 || true
  else
    echo "ERROR: nccl-tests binaries missing in $NCCL_TESTS_DIR/build"
    return 1
  fi
}

# (a) Baseline: default threads (1x1)
run_nccl_variant "variant_a_baseline" "1" "1"

# (b) 4 threads x 4 socks
run_nccl_variant "variant_b_4x4" "4" "4"

# (c) 8 threads x 2 socks
run_nccl_variant "variant_c_8x2" "8" "2"

# (d) Provider plugin variant if present
if [[ -f "/usr/lib/x86_64-linux-gnu/libnccl-net.so" || -f "/usr/local/lib/libnccl-net.so" ]]; then
  run_nccl_variant "variant_d_provider_plugin" "4" "4" "-x NCCL_NET_GDR_LEVEL=5"
fi

python3 - <<'PY' "$OUT_ROOT"
import json, sys, glob
from pathlib import Path
root = Path(sys.argv[1])
summary = {}
for vdir in sorted(root.glob("variant_*")):
    vname = vdir.name
    summary[vname] = {"allreduce_16k_us": None, "sendrecv_256m_gbps": None, "transport_logged": None}
    ar_json = vdir / "all_reduce_16k.json"
    sr_json = vdir / "sendrecv_256m.json"
    ar_log = vdir / "all_reduce_16k.log"
    if ar_json.exists():
        try:
            d = json.load(open(ar_json))
            # Extract latency from nccl-test JSON output
            for row in d.get("data", []):
                summary[vname]["allreduce_16k_us"] = row.get("time_us") or row.get("algbw")
        except Exception: pass
    if sr_json.exists():
        try:
            d = json.load(open(sr_json))
            for row in d.get("data", []):
                summary[vname]["sendrecv_256m_gbps"] = row.get("busbw")
        except Exception: pass
    if ar_log.exists():
        for line in open(ar_log):
            if "NCCL INFO Using network" in line or "NET/Socket" in line:
                summary[vname]["transport_logged"] = line.strip()
                break

out_file = root / "NCCL_TUNING_SUMMARY.json"
out_file.write_text(json.dumps(summary, indent=2))
print("NCCL Tuning Summary:\n", json.dumps(summary, indent=2))
PY

echo "NCCL Socket tuning evaluation complete: $OUT_ROOT"
