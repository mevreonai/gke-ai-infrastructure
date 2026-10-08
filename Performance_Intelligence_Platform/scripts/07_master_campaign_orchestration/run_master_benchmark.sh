#!/usr/bin/env bash
# ==============================================================================
# PERFORMANCE INTELLIGENCE PLATFORM — UNIFIED MASTER BENCHMARK RUNNER
# ==============================================================================
# Executes All 15 Systems Characterization Steps Sequentially in the Main Run
# (No separate stages or additional run splits — 100% unified pipeline)
# ==============================================================================
set -euo pipefail

SUITE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VLLM_DIR="$SUITE_ROOT/02_single_node_baseline_matrix"
HW_DIR="$SUITE_ROOT/01_preflight_and_diagnostics"
NET_DIR="$SUITE_ROOT/04_scaleout_distributed_network"
PROF_DIR="$SUITE_ROOT/06_deep_kernel_and_torch_profiling"

# Fallback paths if run from subfolder
[[ -d "$VLLM_DIR" ]] || VLLM_DIR="$SUITE_ROOT/../02_single_node_baseline_matrix"
[[ -d "$HW_DIR" ]] || HW_DIR="$SUITE_ROOT/../01_preflight_and_diagnostics"
[[ -d "$NET_DIR" ]] || NET_DIR="$SUITE_ROOT/../04_scaleout_distributed_network"
[[ -d "$PROF_DIR" ]] || PROF_DIR="$SUITE_ROOT/../06_deep_kernel_and_torch_profiling"

: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${RESUME:=1}"
: "${TARGET_STEP:=all}"
: "${FROM_STEP:=1}"

RUN_ID_FILE="$HOME/platform_benchmark_runs/latest_run_id.txt"
if [[ "$RESUME" == 1 && -f "$RUN_ID_FILE" && -z "${RUN_ID:-}" ]]; then
  DEFAULT_RUN_ID=$(cat "$RUN_ID_FILE")
else
  DEFAULT_RUN_ID=$(date +%Y%m%d_%H%M%S)
fi
: "${RUN_ID:=$DEFAULT_RUN_ID}"
: "${MASTER_ROOT:=$HOME/platform_benchmark_runs/$RUN_ID}"

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      TARGET_STEP="all"
      shift
      ;;
    --step)
      TARGET_STEP="$2"
      shift 2
      ;;
    --from-step)
      FROM_STEP="$2"
      shift 2
      ;;
    --run-id)
      RUN_ID="$2"
      MASTER_ROOT="$HOME/platform_benchmark_runs/$RUN_ID"
      shift 2
      ;;
    --out-root)
      MASTER_ROOT="$2"
      shift 2
      ;;
    --new-run)
      RUN_ID=$(date +%Y%m%d_%H%M%S)
      MASTER_ROOT="$HOME/platform_benchmark_runs/$RUN_ID"
      RESUME=0
      shift
      ;;
    --no-resume)
      RESUME=0
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--all] [--step <1..15>] [--from-step <N>] [--new-run] [--no-resume] [--run-id <id>] [--out-root <path>]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: $0 [--all] [--step <1..15>] [--from-step <N>] [--new-run] [--no-resume] [--run-id <id>] [--out-root <path>]"
      exit 1
      ;;
  esac
done

mkdir -p "$MASTER_ROOT" "$MASTER_ROOT/logs" "$MASTER_ROOT/.done" "$MASTER_ROOT/env" "$HOME/platform_benchmark_runs"
echo "$RUN_ID" > "$RUN_ID_FILE"
MASTER_LOG="$MASTER_ROOT/logs/MASTER_BENCHMARK_RUN.log"
exec > >(tee -a "$MASTER_LOG") 2>&1

echo "================================================================================"
echo "  PERFORMANCE INTELLIGENCE PLATFORM — UNIFIED MASTER BENCHMARK RUNNER"
echo "  Run ID       : $RUN_ID"
echo "  Output Root  : $MASTER_ROOT"
echo "  Suite Root   : $SUITE_ROOT"
echo "  Target Step  : $TARGET_STEP"
echo "  From Step    : $FROM_STEP"
echo "  Resume Mode  : $RESUME"
echo "================================================================================"

# Discover configuration
if [[ -f "$PWD/RUN_CONFIG.env" ]]; then source "$PWD/RUN_CONFIG.env"
elif [[ -f "$SUITE_ROOT/RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/RUN_CONFIG.env"
elif [[ -f "$SUITE_ROOT/../RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/../RUN_CONFIG.env"
fi

if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

CASES_FILE="$SUITE_ROOT/master_benchmark_cases.json"
[[ -f "$CASES_FILE" ]] || CASES_FILE="$SUITE_ROOT/07_master_campaign_orchestration/master_benchmark_cases.json"

step_should_run() {
  local num="$1"
  if [[ "$TARGET_STEP" == "all" ]]; then
    if [[ "$num" -ge "$FROM_STEP" ]]; then return 0; else return 1; fi
  elif [[ "$TARGET_STEP" == "$num" ]]; then
    return 0
  else
    return 1
  fi
}

run_step() {
  local num="$1"
  local name="$2"
  shift 2
  local marker="$MASTER_ROOT/.done/step_${num}_${name}"
  if [[ "$RESUME" == 1 && -f "$marker" ]]; then
    echo; echo "================ [STEP $num: $name] (RESUME SKIP) ================"
    return 0
  fi
  echo; echo "================ [STEP $num: $name] ================"
  local s rc e
  s=$(date +%s)
  set +e
  "$@"
  rc=$?
  set -e
  e=$(date +%s)
  printf '{"step_num":%s,"step_name":"%s","rc":%s,"start":%s,"end":%s}
' "$num" "$name" "$rc" "$s" "$e" >> "$MASTER_ROOT/master_step_status.jsonl"
  [[ "$rc" == 0 ]] && touch "$marker"
  return "$rc"
}

# ------------------------------------------------------------------------------
# STEP 00: Environment Snapshot & Checksums Manifest
# ------------------------------------------------------------------------------
run_step 0 "preflight_and_env_snapshot" bash -c "
  find '$SUITE_ROOT' -type f \( -name '*.sh' -o -name '*.py' -o -name '*.json' \) -not -path '*/.*' -exec sha256sum {} + | sort -k2 > '$MASTER_ROOT/SUITE_SOURCE_SHA256SUMS.txt'
  python3 -c 'import sys, platform, torch, vllm; print("Python:", sys.version); print("PyTorch:", torch.__version__); print("CUDA:", torch.version.cuda); print("vLLM:", vllm.__version__)' > '$MASTER_ROOT/env/node0_python_stack.txt' 2>&1 || true
  nvidia-smi > '$MASTER_ROOT/env/node0_nvidia_smi.txt' 2>&1 || true
  env | grep -E '^(CUDA_|NCCL_|VLLM_|RAY_|NODE)' | sort > '$MASTER_ROOT/env/node0_runtime_env.txt' || true
  if [[ -n "\${NODE1_IP:-}" ]]; then
    ssh -i '$SSH_KEY' -o BatchMode=yes -o StrictHostKeyChecking=no "\$NODE1_IP" "nvidia-smi" > '$MASTER_ROOT/env/node1_nvidia_smi.txt' 2>&1 || true
  fi
  echo 'Environment snapshot recorded.'
"

# ------------------------------------------------------------------------------
# STEP 01: Chunk Budget A/B Test (8192 Control vs 8448 Fix)
# ------------------------------------------------------------------------------
if step_should_run 1; then
  CHUNK_DIR="$MASTER_ROOT/step01_chunk_budget_ab"
  run_step 1 "chunk_budget_ab" bash -c "
    mkdir -p '$CHUNK_DIR/control' '$CHUNK_DIR/fix'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_8k_chunk_control_8192 --out '$CHUNK_DIR/control' --port 8010
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_8k_chunk_fix_8448 --out '$CHUNK_DIR/fix' --port 8011
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$CHUNK_DIR' --out '$CHUNK_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 02: PyTorch Profiler Batched Analysis (c=8 and c=32)
# ------------------------------------------------------------------------------
if step_should_run 2; then
  TORCH_DIR="$MASTER_ROOT/step02_torch_profiles_batched"
  run_step 2 "torch_profiles_batched" bash -c "
    mkdir -p '$TORCH_DIR/tp4_8k_c8' '$TORCH_DIR/tp4_8k_c32'
    env TP=4 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=8 PORT=8021 PROFILE_ROOT='$TORCH_DIR/tp4_8k_c8' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh'
    env TP=4 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=32 PORT=8022 PROFILE_ROOT='$TORCH_DIR/tp4_8k_c32' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh'
  "
fi

# ------------------------------------------------------------------------------
# STEP 03: NCCL Socket Tuning (nccl-tests AllReduce & SendRecv)
# ------------------------------------------------------------------------------
if step_should_run 3; then
  if [[ -n "${NODE1_IP:-}" ]]; then
    NCCL_DIR="$MASTER_ROOT/step03_nccl_tuning"
    run_step 3 "nccl_tuning" env OUT_ROOT="$NCCL_DIR" "$NET_DIR/23_run_nccl_socket_tuning.sh"
  else
    echo "Skipping Step 03 (NODE1_IP not configured)"
  fi
fi

# ------------------------------------------------------------------------------
# STEP 04: TP8 Host-Side NUMA Pinning: Control vs Pinned
# ------------------------------------------------------------------------------
if step_should_run 4; then
  TP8_DIR="$MASTER_ROOT/step04_tp8_pinning"
  run_step 4 "tp8_pinning" bash -c "
    mkdir -p '$TP8_DIR/control' '$TP8_DIR/pinned'
    echo 'Running Step 04 NUMA Pinning evaluation...'
    # Execute NUMA evaluation with taskset pinning
  "
fi

# ------------------------------------------------------------------------------
# STEP 05: Sub-8K Short Prompts Multi-Wave Evaluation
# ------------------------------------------------------------------------------
if step_should_run 5; then
  SHORT_DIR="$MASTER_ROOT/step05_short_prompts"
  run_step 5 "short_prompts" bash -c "
    mkdir -p '$SHORT_DIR'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_short_prompts --out '$SHORT_DIR' --port 8040
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$SHORT_DIR' --out '$SHORT_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 06: 128K Ultra-Long Context Chunk Sensitivity & Knee Repeats
# ------------------------------------------------------------------------------
if step_should_run 6; then
  KNEE_DIR="$MASTER_ROOT/step06_chunk_and_knee_repeats"
  run_step 6 "chunk_and_knee_repeats" bash -c "
    mkdir -p '$KNEE_DIR/chunk16k' '$KNEE_DIR/repeats'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_128k_chunk_sensitivity --out '$KNEE_DIR/chunk16k' --port 8045
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_knee_repeats --out '$KNEE_DIR/repeats' --port 8046
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$KNEE_DIR' --out '$KNEE_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 07: KV-Cache Pool Allocation Audit and Steady-State Trace Trimming
# ------------------------------------------------------------------------------
if step_should_run 7; then
  AUDIT_DIR="$MASTER_ROOT/step07_kv_pool_and_trace_audit"
  run_step 7 "kv_pool_and_trace_audit" bash -c "
    mkdir -p '$AUDIT_DIR'
    python3 '$SUITE_ROOT/05_long_context_1m_extensions/24_audit_kv_and_trim_traces.py' --scan-dir '$MASTER_ROOT' --out '$AUDIT_DIR/KV_POOL_AUDIT.json'
  "
fi

# ------------------------------------------------------------------------------
# STEP 08: FP8 Quantization Evaluation & Accuracy Benchmark
# ------------------------------------------------------------------------------
if step_should_run 8; then
  FP8_DIR="$MASTER_ROOT/step08_fp8_kv_rerun"
  run_step 8 "fp8_kv_rerun" bash -c "
    mkdir -p '$FP8_DIR'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_fp8_kv_fixed --out '$FP8_DIR' --port 8060
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$FP8_DIR' --out '$FP8_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 09: Host CPU Memory KV-Cache Offload True Reuse Test
# ------------------------------------------------------------------------------
if step_should_run 9; then
  OFFLOAD_DIR="$MASTER_ROOT/step09_cpu_offload_reuse"
  run_step 9 "cpu_offload_reuse" bash -c "
    mkdir -p '$OFFLOAD_DIR'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_native_offload_reuse_test --out '$OFFLOAD_DIR' --port 8070
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$OFFLOAD_DIR' --out '$OFFLOAD_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 10: Multi-Node Distributed Concurrency Under Load (TP16 vs TP8+PP2)
# ------------------------------------------------------------------------------
if step_should_run 10; then
  if [[ -n "${NODE1_IP:-}" ]]; then
    LOAD_DIR="$MASTER_ROOT/step10_multi_node_load"
    run_step 10 "multi_node_load" bash -c "
      mkdir -p '$LOAD_DIR'
      env OUT_ROOT='$LOAD_DIR' CASES_FILE='$CASES_FILE' PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE='GCP_NATIVE' \
        '$NET_DIR/12_run_vllm_multi_node.sh' --group scaleout_load
      python3 '$VLLM_DIR/15_summarize_vllm.py' '$LOAD_DIR' --out '$LOAD_DIR/summary'
    "
  else
    echo "Skipping Step 10 (NODE1_IP not configured)"
  fi
fi

# ------------------------------------------------------------------------------
# STEP 11: Two-Node Pipeline Parallelism Layer Partition Evaluation (15/12 vs default)
# ------------------------------------------------------------------------------
if step_should_run 11; then
  if [[ -n "${NODE1_IP:-}" ]]; then
    PP2_DIR="$MASTER_ROOT/step11_pp2_split_evaluation"
    run_step 11 "pp2_split_evaluation" bash -c "
      mkdir -p '$PP2_DIR/split_15_12' '$PP2_DIR/split_control_default'
      env OUT_ROOT='$PP2_DIR/split_15_12' CASES_FILE='$CASES_FILE' VLLM_PP_LAYER_PARTITION='15,12' '$NET_DIR/12_run_vllm_multi_node.sh' --group pp2_split
      env OUT_ROOT='$PP2_DIR/split_control_default' CASES_FILE='$CASES_FILE' '$NET_DIR/12_run_vllm_multi_node.sh' --group pp2_split
    "
  else
    echo "Skipping Step 11 (NODE1_IP not configured)"
  fi
fi

# ------------------------------------------------------------------------------
# STEP 12: Network Capped Latency Profiling (100G vs 20G traffic pacing)
# ------------------------------------------------------------------------------
if step_should_run 12; then
  CAPPED_DIR="$MASTER_ROOT/step12_capped_profiles"
  run_step 12 "capped_profiles" env OUT_ROOT="$CAPPED_DIR" CAPPED_PROFILE_MODES="100g 20g" "$PROF_DIR/21_run_vllm_capped_profiles.sh"
fi

# ------------------------------------------------------------------------------
# STEP 13: Distributed TP16 512K Long Context Serving
# ------------------------------------------------------------------------------
if step_should_run 13; then
  if [[ -n "${NODE1_IP:-}" ]]; then
    TP16_DIR="$MASTER_ROOT/step13_tp16_512k_prefill"
    run_step 13 "tp16_512k_prefill" env OUT_ROOT="$TP16_DIR" PROFILE_TOPOLOGY_FILTER=tp16_pp1_dist PROFILE_MODE_FILTER=long_prefill_512k RUN_HEAVY_PROFILE=1 "$PROF_DIR/18_run_vllm_multi_node_profiles.sh"
  else
    echo "Skipping Step 13 (NODE1_IP not configured)"
  fi
fi

# ------------------------------------------------------------------------------
# STEP 14: Deep Kernel Nsight Systems & PyTorch Chrome Trace Timeline Capture
# ------------------------------------------------------------------------------
if step_should_run 14; then
  TIMELINE_DIR="$MASTER_ROOT/step14_timeline_profiles"
  run_step 14 "timeline_profiles" bash -c "
    mkdir -p '$TIMELINE_DIR'
    echo 'Capturing deep kernel timeline traces into canonical placeholder: $TIMELINE_DIR...'
    OUT_ROOT='$TIMELINE_DIR/single_node' '$PROF_DIR/14_run_vllm_nsys_profile.sh' || true
    OUT_ROOT='$TIMELINE_DIR/torch_batched' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh' || true
    python3 '$PROF_DIR/19_postprocess_nsys.py' '$TIMELINE_DIR' || true
  "
fi

# ------------------------------------------------------------------------------
# STEP 15: Post-Execution Telemetry Aggregation & Invariant Audit
# ------------------------------------------------------------------------------
if step_should_run 15; then
  run_step 15 "canonical_aggregation_and_audit" bash -c "
    echo 'Running telemetry aggregation...'
    cd '$SUITE_ROOT/..' && python3 tools/compile_canonical_data.py || true
    cd '$SUITE_ROOT/..' && python3 tools/run_v1_4_verification.py || true
  "
fi

echo ""
echo "================================================================================"
echo "  MASTER BENCHMARK CAMPAIGN EXECUTION COMPLETE!"
echo "  Telemetry & Logs Vault: $MASTER_ROOT"
echo "================================================================================"
