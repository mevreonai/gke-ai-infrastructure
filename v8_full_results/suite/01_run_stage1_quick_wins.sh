#!/usr/bin/env bash
# Stage 1: High-Leverage Quick Wins & Diagnostics (~2 hours)
# Format and execution conventions strictly match the V8 benchmark suite.
# Fully updated per Code Review v1.4.
set -euo pipefail

SUITE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VLLM_DIR="$SUITE_ROOT/rtx_g4_smoke_v5"
HW_DIR="$SUITE_ROOT/rtx_g4_smoke_v8_hw"

: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${RUN_ID:=$(date +%Y%m%d_%H%M%S)}"
: "${STAGE1_ROOT:=$HOME/v8_additional_runs/$RUN_ID/stage1}"
: "${STAGE1_RESUME:=1}"

mkdir -p "$STAGE1_ROOT" "$STAGE1_ROOT/logs" "$STAGE1_ROOT/.done"
MASTER="$STAGE1_ROOT/logs/STAGE1_MASTER.log"
exec > >(tee -a "$MASTER") 2>&1

echo "================================================================="
echo "  V8 ADDITIONAL RUNS — STAGE 1: QUICK WINS & DIAGNOSTICS"
echo "  RUN_ID      : $RUN_ID"
echo "  STAGE1_ROOT : $STAGE1_ROOT"
echo "  SUITE_ROOT  : $SUITE_ROOT"
echo "================================================================="

# Discover GCP configuration if present
if [[ -f "$PWD/RUN_CONFIG.env" ]]; then source "$PWD/RUN_CONFIG.env"
elif [[ -f "$SUITE_ROOT/RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/RUN_CONFIG.env"
elif [[ -f "$HOME/rtx_g4_smoke/RUN_CONFIG.env" ]]; then source "$HOME/rtx_g4_smoke/RUN_CONFIG.env"
fi

if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

step(){
  local name="$1"; shift
  local marker="$STAGE1_ROOT/.done/$name"
  if [[ "$STAGE1_RESUME" == 1 && -f "$marker" ]]; then
    echo; echo "================ STEP: $name (RESUME SKIP) ================"
    return 0
  fi
  echo; echo "================ STEP: $name ================"
  local s rc e
  s=$(date +%s)
  set +e
  "$@"
  rc=$?
  set -e
  e=$(date +%s)
  printf '{"step":"%s","rc":%s,"start":%s,"end":%s}\n' "$name" "$rc" "$s" "$e" >> "$STAGE1_ROOT/step_status.jsonl"
  [[ "$rc" == 0 ]] && touch "$marker"
  return "$rc"
}

# -----------------------------------------------------------------------------
# 1. 8K Chunk Budget A/B Test (8192 Control vs 8448 Fix in Same Session - 15 min)
# -----------------------------------------------------------------------------
CHUNK_DIR="$STAGE1_ROOT/01_chunk_budget_ab"
step s1_01_chunk_control env NCCL_POLICY_LOG="$CHUNK_DIR/control/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage1_cases.json" --case tp4_8k_chunk_control_8192 --out "$CHUNK_DIR/control" --port 8010

step s1_01_chunk_fix env NCCL_POLICY_LOG="$CHUNK_DIR/fix/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage1_cases.json" --case tp4_8k_chunk_fix_8448 --out "$CHUNK_DIR/fix" --port 8011

step s1_01_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$CHUNK_DIR" --out "$CHUNK_DIR/summary"

# -----------------------------------------------------------------------------
# 2. Graphs-on PyTorch Profiler: Pure Decode Window at c=8 and c=32 (10 min)
# -----------------------------------------------------------------------------
TORCH_DIR="$STAGE1_ROOT/02_torch_profiles_batched"
mkdir -p "$TORCH_DIR"
step s1_02_torch_profile_c8 env NCCL_POLICY_LOG="$TORCH_DIR/c8/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" env TP=4 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=8 PORT=8021 \
  PROFILE_ROOT="$TORCH_DIR/tp4_8k_c8" "$VLLM_DIR/14c_run_vllm_torch_profile_batched.sh"

step s1_02_torch_profile_c32 env NCCL_POLICY_LOG="$TORCH_DIR/c32/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" env TP=4 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=32 PORT=8022 \
  PROFILE_ROOT="$TORCH_DIR/tp4_8k_c32" "$VLLM_DIR/14c_run_vllm_torch_profile_batched.sh"

# -----------------------------------------------------------------------------
# 3. Real NCCL Tuning via nccl-tests (AllReduce 16K & SendRecv 256M - 15 min)
# -----------------------------------------------------------------------------
if [[ -n "${NODE1_IP:-}" ]]; then
  NCCL_TUNE_DIR="$STAGE1_ROOT/03_nccl_tuning"
  step s1_03_nccl_socket_tuning env OUT_ROOT="$NCCL_TUNE_DIR" "$VLLM_DIR/23_run_nccl_socket_tuning.sh"
else
  echo "Skipping step s1_03_nccl_socket_tuning (NODE1_IP not configured)"
fi

# -----------------------------------------------------------------------------
# 4. TP8 Host-Side NUMA Pinning: Control vs Pinned on Same Server (20 min)
# -----------------------------------------------------------------------------
TP8_PIN_DIR="$STAGE1_ROOT/04_tp8_pinning"
run_tp8_pinning_test() {
  local pdir="$TP8_PIN_DIR"; mkdir -p "$pdir/control" "$pdir/pinned"
  local port=8035
  local model="moonshotai/Kimi-Linear-48B-A3B-Instruct"
  local rev="e1df551a447157d4658b573f9a695d57658590e9"
  export CUDA_VISIBLE_DEVICES="0,1,2,3,4,5,6,7"

  echo "Starting TP8 server for NUMA pinning evaluation..."
  vllm serve "$model" --revision "$rev" --model-impl vllm --trust-remote-code --host 0.0.0.0 --port "$port" \
    --tensor-parallel-size 8 --max-model-len 1048576 --max-num-batched-tokens 8192 --max-num-seqs 32 \
    --gpu-memory-utilization 0.9 --performance-mode balanced --optimization-level 2 \
    --no-enable-prefix-caching > "$pdir/server.log" 2>&1 & local PID=$!

  cleanup_tp8(){
    echo "Stopping TP8 server PID $PID..."
    kill -15 "$PID" 2>/dev/null || true
    sleep 3
    kill -9 "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
    pkill -9 -f "vllm serve.*8035" 2>/dev/null || true
  }
  trap cleanup_tp8 EXIT INT TERM ERR

  for _ in $(seq 1 1800); do
    curl -fsS "http://127.0.0.1:$port/v1/models" >/dev/null 2>&1 && break
    kill -0 "$PID" 2>/dev/null || exit 3
    sleep 2
  done

  # Run 1: Unpinned Control
  echo "Running TP8 unpinned control benchmark..."
  vllm bench serve --backend openai --host 127.0.0.1 --port "$port" --endpoint /v1/completions --model "$model" --trust-remote-code \
    --dataset-name random --random-input-len 8192 --random-output-len 256 --random-range-ratio 0 \
    --num-prompts 12 --max-concurrency 1 --num-warmups 2 --ignore-eos \
    --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99 \
    --save-result --save-detailed --result-dir "$pdir/control" --result-filename "8k_c1_unpinned.json" \
    > "$pdir/control/bench.log" 2>&1

  # Pin workers dynamically to each GPU's local CPU socket
  echo "Applying NUMA socket pinning to worker processes..."
  nvidia-smi --query-compute-apps=pid,gpu_bus_id --format=csv,noheader | while IFS=', ' read -r cpid bus; do
    dev=$(echo "$bus" | sed -E 's/^[0-9A-Fa-f]{4}([0-9A-Fa-f]{4}:)/\1/' | tr 'A-F' 'a-f')
    if [[ -f "/sys/bus/pci/devices/$dev/local_cpulist" ]]; then
      cpulist=$(cat "/sys/bus/pci/devices/$dev/local_cpulist")
      taskset -a -cp "$cpulist" "$cpid"
      echo "Pinned PID $cpid (GPU $bus) to CPUs $cpulist"
    fi
  done | tee "$pdir/PINNING.txt"

  # Run 2: Pinned on same running server
  echo "Running TP8 pinned benchmark on same server..."
  vllm bench serve --backend openai --host 127.0.0.1 --port "$port" --endpoint /v1/completions --model "$model" --trust-remote-code \
    --dataset-name random --random-input-len 8192 --random-output-len 256 --random-range-ratio 0 \
    --num-prompts 12 --max-concurrency 1 --num-warmups 2 --ignore-eos \
    --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99 \
    --save-result --save-detailed --result-dir "$pdir/pinned" --result-filename "8k_c1_pinned.json" \
    > "$pdir/pinned/bench.log" 2>&1

  cleanup_tp8
  trap - EXIT

  python3 - <<'PY' "$pdir"
import json, sys
from pathlib import Path
pdir = Path(sys.argv[1])
unpinned_file = pdir / "control/8k_c1_unpinned.json"
pinned_file = pdir / "pinned/8k_c1_pinned.json"
res = {"unpinned_mean_tpot_ms": None, "pinned_mean_tpot_ms": None, "delta_ms": None}
if unpinned_file.exists():
    try: res["unpinned_mean_tpot_ms"] = json.load(open(unpinned_file)).get("mean_tpot_ms")
    except Exception: pass
if pinned_file.exists():
    try: res["pinned_mean_tpot_ms"] = json.load(open(pinned_file)).get("mean_tpot_ms")
    except Exception: pass
if res["unpinned_mean_tpot_ms"] and res["pinned_mean_tpot_ms"]:
    res["delta_ms"] = res["pinned_mean_tpot_ms"] - res["unpinned_mean_tpot_ms"]
(pdir / "PINNING_COMPARISON.json").write_text(json.dumps(res, indent=2))
print("TP8 Pinning Comparison:\n", json.dumps(res, indent=2))
PY
}
step s1_04_tp8_numa_pinning_evaluation run_tp8_pinning_test

# -----------------------------------------------------------------------------
# 5. Sub-8K Short Prompts Sweep (1K & 2K with 4 Waves at c32 - 30 min)
# -----------------------------------------------------------------------------
SHORT_DIR="$STAGE1_ROOT/05_short_prompts"
step s1_05_short_prompts env NCCL_POLICY_LOG="$SHORT_DIR/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage1_cases.json" --case tp4_short_prompts --out "$SHORT_DIR" --port 8040
step s1_05_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$SHORT_DIR" --out "$SHORT_DIR/summary"

# -----------------------------------------------------------------------------
# 6. 128K Stall-vs-Chunk Test & 3x Knee Repeats (Section 4 Items - 25 min)
# -----------------------------------------------------------------------------
KNEE_DIR="$STAGE1_ROOT/06_chunk_and_knee_repeats"
step s1_06_128k_chunk_sensitivity env NCCL_POLICY_LOG="$KNEE_DIR/chunk16k/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage1_cases.json" --case tp4_128k_chunk_sensitivity --out "$KNEE_DIR/chunk16k" --port 8045

step s1_06_knee_repeats env NCCL_POLICY_LOG="$KNEE_DIR/repeats/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage1_cases.json" --case tp4_knee_repeats --out "$KNEE_DIR/repeats" --port 8046

step s1_06_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$KNEE_DIR" --out "$KNEE_DIR/summary"

# -----------------------------------------------------------------------------
# 7. KV Pool Allocation Audit and Steady-State Trace Trimming
# -----------------------------------------------------------------------------
AUDIT_DIR="$STAGE1_ROOT/07_kv_pool_and_trace_audit"
mkdir -p "$AUDIT_DIR"
step s1_07_kv_pool_and_trim python3 "$VLLM_DIR/24_audit_kv_and_trim_traces.py" \
  --server-log "$CHUNK_DIR/control/tp4_8k_chunk_control_8192/server.log" \
  --metrics "$CHUNK_DIR/control/tp4_8k_chunk_control_8192/8k_c4/metrics_gpu.jsonl" \
  --bench "$CHUNK_DIR/control/tp4_8k_chunk_control_8192/8k_c4/8k_c4.json" \
  --scan-dir "$STAGE1_ROOT" \
  --out "$AUDIT_DIR/STAGE1_KV_AUDIT_AND_TRIM.json"

echo "================================================================="
echo "  STAGE 1 COMPLETE: $STAGE1_ROOT"
echo "================================================================="
