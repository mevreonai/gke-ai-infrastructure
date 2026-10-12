#!/usr/bin/env bash
# Run on BOTH nodes after 01_prepare_node.sh.
# This script collects local topology, PCIe/P2P, NCCL, DRAM and compute data.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/00_smoke_common.sh"
init_smoke_env

: "${PEER_IP:?Set PEER_IP to the other node INTERNAL IP.}"
: "${NUMA0_GPUS:?Set NUMA0_GPUS after inspecting nvidia-smi topo -m, e.g. 0,1,2,3}"
: "${NUMA1_GPUS:?Set NUMA1_GPUS after inspecting nvidia-smi topo -m, e.g. 4,5,6,7}"

meta "TEST_SCOPE=NODE_LOCAL"
meta "NUMA0_GPUS=$NUMA0_GPUS"
meta "NUMA1_GPUS=$NUMA1_GPUS"

NVBW_BIN=$(find "$BENCH_ROOT/nvbandwidth" -type f -name nvbandwidth -perm -111 | head -1)
BABEL_BIN=$(find "$BENCH_ROOT/BabelStream/build_cuda" -type f -name cuda-stream -perm -111 | head -1)
NCCL_DIR="$BENCH_ROOT/nccl-tests"
CUTLASS_BIN="$BENCH_ROOT/cutlass/build_sm120/tools/profiler/cutlass_profiler"
export NVBW_BIN BABEL_BIN NCCL_DIR CUTLASS_BIN NUMA0_GPUS NUMA1_GPUS

log_note "NVBW_BIN=$NVBW_BIN ; BABEL_BIN=$BABEL_BIN ; NCCL_DIR=$NCCL_DIR"

# Raw NVBandwidth JSON + logged copy.
start_gpu_telemetry 100_nvbandwidth_host_gpu
run_logged 100_nvbandwidth_host_gpu '
"$NVBW_BIN" \
  -t host_to_device_memcpy_ce device_to_host_memcpy_ce \
  -i 10 --format json \
  | tee "$RESULT_DIR/nvbandwidth_host_gpu.raw.json"
'
stop_gpu_telemetry

start_gpu_telemetry 101_nvbandwidth_d2d
run_logged 101_nvbandwidth_d2d '
"$NVBW_BIN" -p device_to_device -i 10 --format json \
  | tee "$RESULT_DIR/nvbandwidth_d2d.raw.json"
'
stop_gpu_telemetry

start_gpu_telemetry 102_nvbandwidth_latency
run_logged 102_nvbandwidth_latency '
"$NVBW_BIN" -t device_to_device_latency_sm -i 20 --format json \
  | tee "$RESULT_DIR/nvbandwidth_latency.raw.json"
'
stop_gpu_telemetry

# Device DRAM bandwidth.
start_gpu_telemetry 110_babelstream_gpu0
run_logged 110_babelstream_gpu0 '
CUDA_VISIBLE_DEVICES=0 "$BABEL_BIN"
'
stop_gpu_telemetry

NUMA1_FIRST_GPU=$(echo "$NUMA1_GPUS" | cut -d, -f1)
start_gpu_telemetry 111_babelstream_numa1_gpu
run_logged 111_babelstream_numa1_gpu "
CUDA_VISIBLE_DEVICES=$NUMA1_FIRST_GPU \"$BABEL_BIN\"
"
stop_gpu_telemetry

# NCCL exact points. One test/log per point makes downstream parsing deterministic.
for SIZE in 16K 128K 512K 64M 128M 256M; do
  SAFE=$(echo "$SIZE" | tr '[:upper:]' '[:lower:]')

  start_gpu_telemetry "120_ar_tp4_${SAFE}"
  run_logged "120_ar_tp4_${SAFE}" "
  cd \"$NCCL_DIR\"
  echo 'META TEST_KIND=ALLREDUCE TP=4 SIZE=$SIZE P2P_LEVEL=SYS'
  CUDA_VISIBLE_DEVICES=$NUMA0_GPUS NCCL_P2P_LEVEL=SYS \
    ./build/all_reduce_perf -b $SIZE -e $SIZE -g 4 -J "$RESULT_DIR/nccl_ar_tp4_${SAFE}.json"
  "
  stop_gpu_telemetry

  start_gpu_telemetry "121_ar_tp8_${SAFE}"
  run_logged "121_ar_tp8_${SAFE}" "
  cd \"$NCCL_DIR\"
  echo 'META TEST_KIND=ALLREDUCE TP=8 SIZE=$SIZE P2P_LEVEL=SYS'
  NCCL_P2P_LEVEL=SYS \
    ./build/all_reduce_perf -b $SIZE -e $SIZE -g 8 -J "$RESULT_DIR/nccl_ar_tp8_${SAFE}.json"
  "
  stop_gpu_telemetry
done

# Full curves.
start_gpu_telemetry 122_ar_tp4_curve
run_logged 122_ar_tp4_curve "
cd \"$NCCL_DIR\"
CUDA_VISIBLE_DEVICES=$NUMA0_GPUS NCCL_P2P_LEVEL=SYS \
  ./build/all_reduce_perf -b 8 -e 512M -f 2 -g 4
"
stop_gpu_telemetry

start_gpu_telemetry 123_ar_tp8_curve
run_logged 123_ar_tp8_curve "
cd \"$NCCL_DIR\"
NCCL_P2P_LEVEL=SYS \
  ./build/all_reduce_perf -b 8 -e 512M -f 2 -g 8
"
stop_gpu_telemetry

# AllGather / ReduceScatter.
for EXE in all_gather_perf reduce_scatter_perf; do
  start_gpu_telemetry "130_tp8_${EXE}"
  run_logged "130_tp8_${EXE}" "
  cd \"$NCCL_DIR\"
  NCCL_P2P_LEVEL=SYS ./build/$EXE -b 16K -e 256M -f 2 -g 8
  "
  stop_gpu_telemetry
done

# P2P-policy sensitivity.
for LEVEL in SYS PHB; do
  start_gpu_telemetry "140_ar8_p2p_${LEVEL}"
  run_logged "140_ar8_p2p_${LEVEL}" "
  cd \"$NCCL_DIR\"
  NCCL_P2P_LEVEL=$LEVEL ./build/all_reduce_perf -b 16K -e 256M -f 2 -g 8
  "
  stop_gpu_telemetry
done

start_gpu_telemetry 141_ar8_p2p_off
run_logged 141_ar8_p2p_off "
cd \"$NCCL_DIR\"
NCCL_P2P_DISABLE=1 ./build/all_reduce_perf -b 16K -e 256M -f 2 -g 8
"
stop_gpu_telemetry

# One detailed NCCL graph trace.
start_gpu_telemetry 150_nccl_debug_tp8_128m
run_logged 150_nccl_debug_tp8_128m "
cd \"$NCCL_DIR\"
NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET NCCL_P2P_LEVEL=SYS \
  ./build/all_reduce_perf -b 128M -e 128M -g 8
"
stop_gpu_telemetry

# Optional CUTLASS compute roof.
if [ -x "$CUTLASS_BIN" ] && [ "${RUN_CUTLASS:-1}" = "1" ]; then
  start_gpu_telemetry 160_cutlass_large
  run_logged 160_cutlass_large "
  CUDA_VISIBLE_DEVICES=0 \"$CUTLASS_BIN\" \
    --operation=gemm --op_class=tensorop \
    --A=f16:row --B=f16:column --C=f32 --accum=f32 \
    --m=8192 --n=8192 --k=8192 \
    --profiling-iterations=20 \
    --output="$RESULT_DIR/cutlass_large"
  "
  stop_gpu_telemetry

  start_gpu_telemetry 161_cutlass_kimi_width
  run_logged 161_cutlass_kimi_width "
  CUDA_VISIBLE_DEVICES=0 \"$CUTLASS_BIN\" \
    --operation=gemm --op_class=tensorop \
    --A=f16:row --B=f16:column --C=f32 --accum=f32 \
    --m=8,32,128,512,2048,8192 --n=7168 --k=7168 \
    --profiling-iterations=20 \
    --output="$RESULT_DIR/cutlass_kimi_width"
  "
  stop_gpu_telemetry
else
  log_note "CUTLASS skipped: binary missing or RUN_CUTLASS=0"
fi

log_note "NODE-LOCAL BENCHMARKS COMPLETE. RESULT_DIR=$RESULT_DIR"
