#!/usr/bin/env bash
# V8-FULL node-local hardware characterization. Run on BOTH nodes.
# Primary rows are native/default transport; forced P2P policies are isolated as sensitivity tests.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/00_smoke_common.sh"
init_smoke_env

: "${PEER_IP:?Set PEER_IP to the other node INTERNAL IP.}"
: "${NUMA0_GPUS:?Set NUMA0_GPUS after inspecting nvidia-smi topo -m, e.g. 0,1,2,3}"
: "${NUMA1_GPUS:?Set NUMA1_GPUS after inspecting nvidia-smi topo -m, e.g. 4,5,6,7}"
: "${RUN_CUTLASS:=1}"

meta "SUITE=V8_FULL"
meta "TEST_SCOPE=NODE_LOCAL"
meta "PRIMARY_TRANSPORT=NCCL_NATIVE_DEFAULT"
meta "NUMA0_GPUS=$NUMA0_GPUS"
meta "NUMA1_GPUS=$NUMA1_GPUS"

export NVBW_BIN=$(find "$BENCH_ROOT/nvbandwidth" -type f -name nvbandwidth -perm -111 | head -1 || true)
export BABEL_BIN=$(find "$BENCH_ROOT/BabelStream/build_cuda" -type f -name cuda-stream -perm -111 | head -1 || true)
export NCCL_DIR="$BENCH_ROOT/nccl-tests"
export CUTLASS_BIN="$BENCH_ROOT/cutlass/build_sm120/tools/profiler/cutlass_profiler"
[[ -x "$NVBW_BIN" ]] || { echo "ERROR: nvbandwidth not built. Run 01_prepare_node.sh"; exit 2; }
[[ -x "$BABEL_BIN" ]] || { echo "ERROR: BabelStream not built. Run 01_prepare_node.sh"; exit 2; }
[[ -x "$NCCL_DIR/build/all_reduce_perf" ]] || { echo "ERROR: nccl-tests not built. Run 01_prepare_node.sh"; exit 2; }

run_logged 090_runtime_inventory '
nvidia-smi --query-gpu=index,uuid,name,memory.total,pci.bus_id --format=csv
nvidia-smi topo -m
numactl -H || true
cat /sys/class/dmi/id/product_name 2>/dev/null || true
'

start_gpu_telemetry 100_nvbandwidth_host_gpu
run_logged 100_nvbandwidth_host_gpu '
"$NVBW_BIN" -t host_to_device_memcpy_ce device_to_host_memcpy_ce -i 10 --format json | tee "$RESULT_DIR/nvbandwidth_host_gpu.raw.json"
'
stop_gpu_telemetry

start_gpu_telemetry 101_nvbandwidth_d2d
run_logged 101_nvbandwidth_d2d '
"$NVBW_BIN" -p device_to_device -i 10 --format json | tee "$RESULT_DIR/nvbandwidth_d2d.raw.json"
'
stop_gpu_telemetry

start_gpu_telemetry 102_nvbandwidth_latency
run_logged 102_nvbandwidth_latency '
"$NVBW_BIN" -t device_to_device_latency_sm -i 20 --format json | tee "$RESULT_DIR/nvbandwidth_latency.raw.json"
'
stop_gpu_telemetry

for GPU in 0 "$(echo "$NUMA1_GPUS" | cut -d, -f1)"; do
  LABEL="110_babelstream_gpu${GPU}"
  start_gpu_telemetry "$LABEL"
  run_logged "$LABEL" "CUDA_VISIBLE_DEVICES=$GPU \"$BABEL_BIN\""
  stop_gpu_telemetry
done

# Native/default NCCL is the source of truth. Explicitly clear legacy P2P/SHM forcing before primary rows.
nccl_sanitize_local_native
export NCCL_DIR="$BENCH_ROOT/nccl-tests"
nccl_assert_local_native
capture_nccl_env "$RESULT_DIR/NCCL_ENV_NATIVE_BEFORE.txt"
meta "NCCL_NATIVE_POLICY=P2P_DEFAULT SHM_DEFAULT P2P_LEVEL_DEFAULT"
for SIZE in 16K 128K 512K 64M 128M 256M; do
  SAFE=$(echo "$SIZE" | tr '[:upper:]' '[:lower:]')
  start_gpu_telemetry "120_ar_tp4_native_${SAFE}"
  run_logged "120_ar_tp4_native_${SAFE}" "
    cd \"$NCCL_DIR\"
    echo 'META TEST_KIND=ALLREDUCE TP=4 SIZE=$SIZE TRANSPORT=NATIVE_DEFAULT NUMA_SCOPE=NUMA0'
    CUDA_VISIBLE_DEVICES=$NUMA0_GPUS ./build/all_reduce_perf -b $SIZE -e $SIZE -g 4 -J \"$RESULT_DIR/nccl_ar_tp4_native_${SAFE}.json\"
  "
  stop_gpu_telemetry

  start_gpu_telemetry "121_ar_tp8_native_${SAFE}"
  run_logged "121_ar_tp8_native_${SAFE}" "
    cd \"$NCCL_DIR\"
    echo 'META TEST_KIND=ALLREDUCE TP=8 SIZE=$SIZE TRANSPORT=NATIVE_DEFAULT NUMA_SCOPE=CROSS_SOCKET'
    ./build/all_reduce_perf -b $SIZE -e $SIZE -g 8 -J \"$RESULT_DIR/nccl_ar_tp8_native_${SAFE}.json\"
  "
  stop_gpu_telemetry
done

# Full native curves: AR, AG, RS for TP4 and TP8.
for TP in 4 8; do
  if [[ "$TP" == 4 ]]; then VIS="CUDA_VISIBLE_DEVICES=$NUMA0_GPUS"; else VIS=""; fi
  for EXE in all_reduce_perf all_gather_perf reduce_scatter_perf; do
    LABEL="130_${EXE%_perf}_tp${TP}_native_curve"
    start_gpu_telemetry "$LABEL"
    run_logged "$LABEL" "
      cd \"$NCCL_DIR\"
      echo 'META TEST_KIND=${EXE%_perf} TP=$TP TRANSPORT=NATIVE_DEFAULT'
      $VIS ./build/$EXE -b 8 -e 512M -f 2 -g $TP
    "
    stop_gpu_telemetry
  done
done

# Transport sensitivity is deliberately separated from native measurements.
for LEVEL in SYS PHB; do
  LABEL="140_ar_tp8_sensitivity_p2p_${LEVEL}"
  start_gpu_telemetry "$LABEL"
  run_logged "$LABEL" "
    cd \"$NCCL_DIR\"
    echo 'META TEST_KIND=ALLREDUCE TP=8 SENSITIVITY_ONLY=1 NCCL_P2P_LEVEL=$LEVEL'
    NCCL_P2P_LEVEL=$LEVEL ./build/all_reduce_perf -b 16K -e 256M -f 2 -g 8
  "
  stop_gpu_telemetry
done
start_gpu_telemetry 141_ar_tp8_sensitivity_p2p_disabled
run_logged 141_ar_tp8_sensitivity_p2p_disabled "
  cd \"$NCCL_DIR\"
  echo 'META TEST_KIND=ALLREDUCE TP=8 SENSITIVITY_ONLY=1 P2P_DISABLED_FOR_SENSITIVITY=1'
  NCCL_P2P_DISABLE=1 ./build/all_reduce_perf -b 16K -e 256M -f 2 -g 8
"
stop_gpu_telemetry

start_gpu_telemetry 150_nccl_debug_tp8_128m_native
run_logged 150_nccl_debug_tp8_128m_native "
  cd \"$NCCL_DIR\"
  NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET ./build/all_reduce_perf -b 128M -e 128M -g 8
"
stop_gpu_telemetry

# CUTLASS is intentionally a shape/reference compute roof; it is NOT a K3 MXFP4 efficiency measurement.
if [[ "$RUN_CUTLASS" == 1 && -x "$CUTLASS_BIN" ]]; then
  run_logged 159_cutlass_version "\"$CUTLASS_BIN\" --version || true; git -C \"$BENCH_ROOT/cutlass\" rev-parse HEAD || true"
  start_gpu_telemetry 160_cutlass_fp16_large_shape_reference
  run_logged 160_cutlass_fp16_large_shape_reference "
    CUDA_VISIBLE_DEVICES=0 \"$CUTLASS_BIN\" --operation=gemm --op_class=tensorop \\
      --A=f16:row --B=f16:column --C=f32 --accum=f32 \\
      --m=8192 --n=8192 --k=8192 --profiling-iterations=20 --output=\"$RESULT_DIR/cutlass_fp16_large\"
  "
  stop_gpu_telemetry

  start_gpu_telemetry 161_cutlass_fp16_kimi_width_shape_reference
  run_logged 161_cutlass_fp16_kimi_width_shape_reference "
    CUDA_VISIBLE_DEVICES=0 \"$CUTLASS_BIN\" --operation=gemm --op_class=tensorop \\
      --A=f16:row --B=f16:column --C=f32 --accum=f32 \\
      --m=8,32,128,512,2048,8192 --n=7168 --k=7168 --profiling-iterations=20 \\
      --output=\"$RESULT_DIR/cutlass_fp16_kimi_width\"
  "
  stop_gpu_telemetry
  cat > "$RESULT_DIR/CUTLASS_SCOPE.txt" <<'EOF'
CUTLASS rows are FP16 tensor-core shape/reference measurements only.
They are not a measurement of Kimi K3 MXFP4 weight/operator efficiency.
EOF
else
  echo "CUTLASS skipped: RUN_CUTLASS=$RUN_CUTLASS binary=$CUTLASS_BIN" | tee "$RESULT_DIR/CUTLASS_SKIPPED.txt"
fi

log_note "V8-FULL NODE-LOCAL BENCHMARKS COMPLETE. RESULT_DIR=$RESULT_DIR"
