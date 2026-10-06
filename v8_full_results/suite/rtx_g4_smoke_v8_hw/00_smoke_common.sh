#!/usr/bin/env bash
# Common logging/telemetry helpers for RTX PRO 6000 GCP smoke tests.
set -o pipefail

init_smoke_env() {
  : "${BENCH_ROOT:=$HOME/rtx_g4_smoke}"
  : "${RUN_ID:=$(date +%Y%m%d_%H%M%S)}"
  : "${HOST_SHORT:=$(hostname -s)}"
  : "${RESULT_DIR:=$BENCH_ROOT/results/$RUN_ID/$HOST_SHORT}"
  mkdir -p "$RESULT_DIR"
  export BENCH_ROOT RUN_ID HOST_SHORT RESULT_DIR
  export MASTER_LOG="$RESULT_DIR/MASTER_${RUN_ID}_${HOST_SHORT}.log"
  touch "$MASTER_LOG"
}

log_note() {
  local msg="$*"
  {
    echo
    echo "================================================================"
    echo "NOTE"
    echo "HOST      : $(hostname -f)"
    echo "TIME      : $(date --iso-8601=seconds)"
    echo "MESSAGE   : $msg"
    echo "================================================================"
  } | tee -a "$MASTER_LOG"
}

run_logged() {
  local label="$1"; shift
  local cmd="$*"
  local outfile="$RESULT_DIR/${label}.log"
  {
    echo
    echo "================================================================"
    echo "TEST      : $label"
    echo "HOST      : $(hostname -f)"
    echo "START     : $(date --iso-8601=seconds)"
    echo "PWD       : $(pwd)"
    echo "COMMAND   : $cmd"
    echo "----------------------------------------------------------------"
  } | tee -a "$MASTER_LOG" "$outfile"

  set +e
  bash -lc "set -o pipefail; $cmd" \
    > >(tee -a "$MASTER_LOG" "$outfile") \
    2> >(tee -a "$MASTER_LOG" "$outfile" >&2)
  local rc=$?
  set -e

  {
    echo "----------------------------------------------------------------"
    echo "END       : $(date --iso-8601=seconds)"
    echo "EXIT_CODE : $rc"
    echo "================================================================"
  } | tee -a "$MASTER_LOG" "$outfile"
  return $rc
}

start_gpu_telemetry() {
  local label="$1"
  nvidia-smi dmon -s pcu -d 1 -o DT \
    -f "$RESULT_DIR/${label}_nvsmi_dmon.log" >/dev/null 2>&1 &
  export DMON_PID=$!

  (
    while true; do
      nvidia-smi \
        --query-gpu=timestamp,index,name,pstate,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,temperature.gpu,clocks.sm,clocks.mem \
        --format=csv,noheader,nounits
      sleep 1
    done
  ) > "$RESULT_DIR/${label}_gpu_query.csv" 2>&1 &
  export GPUQUERY_PID=$!
}

stop_gpu_telemetry() {
  if [ -n "${DMON_PID:-}" ]; then
    kill "$DMON_PID" 2>/dev/null || true
    wait "$DMON_PID" 2>/dev/null || true
  fi
  if [ -n "${GPUQUERY_PID:-}" ]; then
    kill "$GPUQUERY_PID" 2>/dev/null || true
    wait "$GPUQUERY_PID" 2>/dev/null || true
  fi
  unset DMON_PID GPUQUERY_PID
}

meta() {
  # Emit one machine-parseable metadata line into the master log.
  echo "META $*" | tee -a "$MASTER_LOG"
}

# V8 NCCL transport policy helpers.
# Native/local evidence must not inherit legacy transport-forcing variables.
nccl_sanitize_local_native() {
  # Match the actual V6 single-node qualification environment: no NCCL_* overrides.
  local v
  while IFS= read -r v; do
    [[ -n "$v" ]] && unset "$v" || true
  done < <(compgen -v | grep '^NCCL_' | grep -v '^NCCL_DIR$' || true)
}

nccl_assert_local_native() {
  local bad=0
  for v in NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; do
    if [[ -n "${!v+x}" ]]; then
      echo "ERROR: $v is set (${!v}); native/local NCCL evidence would be contaminated" >&2
      bad=1
    fi
  done
  [[ "$bad" == 0 ]]
}

capture_nccl_env() {
  local out=${1:?output path required}
  {
    echo "timestamp=$(date --iso-8601=seconds)"
    env | LC_ALL=C sort | grep '^NCCL_' || true
  } > "$out"
}
