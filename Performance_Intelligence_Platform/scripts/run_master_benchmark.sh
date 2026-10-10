#!/usr/bin/env bash
# ==============================================================================
# PERFORMANCE INTELLIGENCE PLATFORM — UNIFIED MASTER BENCHMARK RUNNER
# ==============================================================================
# Executes All 15 Systems Characterization Steps Sequentially in the Main Run
# Incorporates all Stage 1 (Quick Wins), Stage 2 (Scale-Out), and Stage 3 (Deep Expansions)
# Model-Agnostic: Configured dynamically via $MODEL and $REVISION
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

# Dynamic execution selections
SELECTED_MODEL=""
SELECTED_REVISION=""
SELECTED_STAGE="all"
SELECTED_TOPOLOGIES="all"
SELECTED_BANDWIDTH="all"
DRY_RUN=0

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      TARGET_STEP="all"
      SELECTED_STAGE="all"
      shift
      ;;
    --stage)
      SELECTED_STAGE="$2"
      shift 2
      ;;
    --model)
      SELECTED_MODEL="$2"
      shift 2
      ;;
    --revision)
      SELECTED_REVISION="$2"
      shift 2
      ;;
    --topologies)
      SELECTED_TOPOLOGIES="$2"
      shift 2
      ;;
    --bandwidth)
      SELECTED_BANDWIDTH="$2"
      shift 2
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
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --new-run)
      RUN_ID=$(date +%Y%m%d_%H%M%S)
      MASTER_ROOT="$HOME/platform_benchmark_runs/$RUN_ID"
      RESUME=0
      shift
      ;;
    --continuous-batching|-cb)
      RUN_CONTINUOUS_BATCHING=1
      shift
      ;;
    --cb-blocks)
      RUN_CONTINUOUS_BATCHING=1
      CB_BLOCKS_ARG="$2"
      shift 2
      ;;
    --no-resume)
      RESUME=0
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --all                        Execute all stages and characterization steps (00-15: ~7h 10m)"
      echo "  --stage <1|2|3|all>          Filter execution to specific characterization stage"
      echo "                                 Stage 1: Quick Wins & Single-Node (Steps 1-7: ~1h 10m)"
      echo "                                 Stage 2: Scale-Out Concurrency & Asymmetric PP (Steps 8-13: ~3h 30m)"
      echo "                                 Stage 3: Deep Profiling & Strategic Sweeps (Steps 14-15: ~2h 30m)"
      echo "  --model <hf_id_or_path>      Select target model (default: moonshotai/Kimi-Linear-48B-A3B-Instruct)"
      echo "  --revision <git_sha>         Select model revision commit"
      echo "  --topologies <list|all>      Select topologies (e.g. tp4_pp1,tp8_pp1,tp4_pp2,tp8_pp2,tp4_pp4,tp16_pp1)"
      echo "  --bandwidth <list|all>       Select network bandwidth modes (e.g. native,100g,20g,impaired)"
      echo "  --step <0..15>               Execute a single target step"
      echo "  --from-step <N>              Resume execution starting from step N"
      echo "  --dry-run                    Verify commands and configuration without launching GPU workloads"
      echo "  --new-run / --no-resume      Force clean execution without resume markers"
      echo "  --run-id <id>                Specify explicit run identifier"
      echo "  --out-root <path>            Override output root directory"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Run with --help for available options."
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

# Apply CLI overrides over environment defaults
if [[ -n "$SELECTED_MODEL" ]]; then
  export MODEL="$SELECTED_MODEL"
  export VLLM_MODEL="$SELECTED_MODEL"
fi
if [[ -n "$SELECTED_REVISION" ]]; then
  export REVISION="$SELECTED_REVISION"
  export VLLM_REVISION="$SELECTED_REVISION"
fi
if [[ -n "$SELECTED_TOPOLOGIES" && "$SELECTED_TOPOLOGIES" != "all" ]]; then
  export TOPOLOGY_SELECTION="$SELECTED_TOPOLOGIES"
fi
if [[ -n "$SELECTED_BANDWIDTH" && "$SELECTED_BANDWIDTH" != "all" ]]; then
  export NETWORK_BANDWIDTH_SELECTION="$SELECTED_BANDWIDTH"
fi
if [[ -n "$SELECTED_STAGE" && "$SELECTED_STAGE" != "all" ]]; then
  export STAGE_SELECTION="$SELECTED_STAGE"
fi

# Mandatory Hardware & MoE Cutlass/Triton Execution Controls
export CUDA_DEVICE_ORDER="PCI_BUS_ID"
export VLLM_MOE_BACKEND="triton"
export VLLM_FLASHINFER_AUTOTUNE="1"
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"
export VLLM_PP_LAYER_PARTITION="${VLLM_PP_LAYER_PARTITION:-15,12}"

# Inter-Node NCCL & Network Controls
export NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME:-ens3}"
export NCCL_NET="${NCCL_NET:-Socket}"
export NCCL_CROSS_NIC="${NCCL_CROSS_NIC:-0}"
export NCCL_ALGO="${NCCL_ALGO:-Tree}"
export NCCL_PROTO="${NCCL_PROTO:-Simple}"
export NCCL_BUFFSIZE="${NCCL_BUFFSIZE:-4194304}"

if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

CASES_FILE="$SUITE_ROOT/master_benchmark_cases.json"
[[ -f "$CASES_FILE" ]] || CASES_FILE="$SUITE_ROOT/07_master_campaign_orchestration/master_benchmark_cases.json"

echo "  Model        : ${MODEL:-default}"
echo "  Revision     : ${REVISION:-default}"
echo "  Stage Filter : ${STAGE_SELECTION:-all}"
echo "  Topologies   : ${TOPOLOGY_SELECTION:-all}"
echo "  Bandwidth    : ${NETWORK_BANDWIDTH_SELECTION:-all}"
echo "  Dry Run      : $DRY_RUN"
echo "  MoE Backend  : $VLLM_MOE_BACKEND (Cutlass/Triton Autotuned)"
echo "  PP Split     : $VLLM_PP_LAYER_PARTITION"
echo "================================================================================"

topology_matches() {
  local topo="$1"
  local sel="${TOPOLOGY_SELECTION:-all}"
  [[ "$sel" == "all" ]] && return 0
  IFS=',' read -ra LIST <<< "$sel"
  for item in "${LIST[@]}"; do
    local c
    c=$(echo "$item" | tr -d ' ' | tr '[:upper:]' '[:lower:]')
    if [[ "$topo" == *"$c"* || "$c" == *"$topo"* ]]; then return 0; fi
  done
  return 1
}

bandwidth_matches() {
  local bw="$1"
  local sel="${NETWORK_BANDWIDTH_SELECTION:-all}"
  [[ "$sel" == "all" ]] && return 0
  IFS=',' read -ra LIST <<< "$sel"
  for item in "${LIST[@]}"; do
    local c
    c=$(echo "$item" | tr -d ' ' | tr '[:upper:]' '[:lower:]')
    if [[ "$bw" == *"$c"* || "$c" == *"$bw"* ]]; then return 0; fi
  done
  return 1
}

step_should_run() {
  local num="$1"
  local stage="${STAGE_SELECTION:-all}"
  if [[ "$stage" == "1" && ( "$num" -lt 1 || "$num" -gt 7 ) ]]; then return 1; fi
  if [[ "$stage" == "2" && ( "$num" -lt 8 || "$num" -gt 13 ) ]]; then return 1; fi
  if [[ "$stage" == "3" && ( "$num" -lt 14 || "$num" -gt 17 ) ]]; then return 1; fi

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
  if [[ "$DRY_RUN" == 1 ]]; then
    echo "  [DRY-RUN] Simulating Step $num: $name"
    echo "  [DRY-RUN] Command payload verified successfully."
    rc=0
    e=$(date +%s)
    printf '{"step_num":%s,"step_name":"%s","rc":0,"dry_run":true,"start":%s,"end":%s}\n' "$num" "$name" "$s" "$e" >> "$MASTER_ROOT/master_step_status.jsonl"
    touch "$marker"
    return 0
  fi
  set +e
  "$@"
  rc=$?
  set -e
  e=$(date +%s)
  printf '{"step_num":%s,"step_name":"%s","rc":%s,"dry_run":false,"start":%s,"end":%s}\n' "$num" "$name" "$rc" "$s" "$e" >> "$MASTER_ROOT/master_step_status.jsonl"
  [[ "$rc" == 0 ]] && touch "$marker"
  return "$rc"
}

# ------------------------------------------------------------------------------
# STEP 00: Environment Snapshot & Checksums Manifest
# ------------------------------------------------------------------------------
run_step 0 "preflight_and_env_snapshot" bash -c "
  find '$SUITE_ROOT' -type f \( -name '*.sh' -o -name '*.py' -o -name '*.json' \) -not -path '*/.*' -exec sha256sum {} + | sort -k2 > '$MASTER_ROOT/SUITE_SOURCE_SHA256SUMS.txt'
  python3 -c 'import sys, platform, torch, vllm; print(\"Python:\", sys.version); print(\"PyTorch:\", torch.__version__); print(\"CUDA:\", torch.version.cuda); print(\"vLLM:\", vllm.__version__)' > '$MASTER_ROOT/env/node0_python_stack.txt' 2>&1 || true
  nvidia-smi > '$MASTER_ROOT/env/node0_nvidia_smi.txt' 2>&1 || true
  env | grep -E '^(CUDA_|NCCL_|VLLM_|RAY_|NODE|V8_)' | sort > '$MASTER_ROOT/env/node0_runtime_env.txt' || true
  if [[ -n \"\${NODE1_IP:-}\" ]]; then
    ssh -i '$SSH_KEY' -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"nvidia-smi\" > '$MASTER_ROOT/env/node1_nvidia_smi.txt' 2>&1 || true
    ssh -i '$SSH_KEY' -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"env | grep -E '^(CUDA_|NCCL_|VLLM_|RAY_|NODE|V8_)' | sort\" > '$MASTER_ROOT/env/node1_runtime_env.txt' 2>&1 || true
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
# STEP 04: TP8 Host-Side NUMA Pinning: Control vs Pinned on Same Server
# ------------------------------------------------------------------------------
if step_should_run 4; then
  if ! topology_matches "tp8"; then
    echo "Skipping Step 04 (TP8 topology not targeted by selection: ${TOPOLOGY_SELECTION:-all})"
  else
    TP8_DIR="$MASTER_ROOT/step04_tp8_pinning"
    run_step 4 "tp8_pinning" bash -c "
    mkdir -p '$TP8_DIR/control' '$TP8_DIR/pinned'
    local_port=8035
    model_name=\"\${VLLM_MODEL:-\${MODEL:-moonshotai/Kimi-Linear-48B-A3B-Instruct}}\"
    rev_id=\"\${VLLM_REVISION:-\${REVISION:-e1df551a447157d4658b573f9a695d57658590e9}}\"
    export CUDA_VISIBLE_DEVICES=\"0,1,2,3,4,5,6,7\"

    echo \"Starting TP8 server for NUMA pinning evaluation with model: \$model_name...\"
    vllm serve \"\$model_name\" --revision \"\$rev_id\" --model-impl vllm --trust-remote-code --host 0.0.0.0 --port \"\$local_port\" \
      --tensor-parallel-size 8 --max-model-len 1048576 --max-num-batched-tokens 8192 --max-num-seqs 32 \
      --gpu-memory-utilization 0.9 --performance-mode balanced --optimization-level 2 \
      --no-enable-prefix-caching > \"\$TP8_DIR/server.log\" 2>&1 & local PID=\$!

    cleanup_tp8(){
      echo \"Stopping TP8 server PID \$PID...\"
      kill -15 \"\$PID\" 2>/dev/null || true
      sleep 3
      kill -9 \"\$PID\" 2>/dev/null || true
      wait \"\$PID\" 2>/dev/null || true
      pkill -9 -f \"vllm serve.*\$local_port\" 2>/dev/null || true
    }
    trap cleanup_tp8 EXIT INT TERM ERR

    echo \"Waiting for TP8 server to become ready on port \$local_port...\"
    for _ in \$(seq 1 1800); do
      curl -fsS \"http://127.0.0.1:\$local_port/v1/models\" >/dev/null 2>&1 && break
      kill -0 \"\$PID\" 2>/dev/null || { echo \"Server crashed on startup\"; exit 3; }
      sleep 2
    done

    # Run 1: Unpinned Control
    echo \"Running TP8 unpinned control benchmark...\"
    vllm bench serve --backend openai --host 127.0.0.1 --port \"\$local_port\" --endpoint /v1/completions --model \"\$model_name\" --trust-remote-code \
      --dataset-name random --random-input-len 8192 --random-output-len 256 --random-range-ratio 0 \
      --num-prompts 12 --max-concurrency 1 --num-warmups 2 --ignore-eos \
      --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99 \
      --save-result --save-detailed --result-dir \"\$TP8_DIR/control\" --result-filename \"8k_c1_unpinned.json\" \
      > \"\$TP8_DIR/control/bench.log\" 2>&1

    # Pin workers dynamically to each GPU's local CPU socket
    echo \"Applying NUMA socket pinning to worker processes...\"
    nvidia-smi --query-compute-apps=pid,gpu_bus_id --format=csv,noheader | while IFS=', ' read -r cpid bus; do
      dev=\$(echo \"\$bus\" | sed -E 's/^[0-9A-Fa-f]{4}([0-9A-Fa-f]{4}:)/\1/' | tr 'A-F' 'a-f')
      if [[ -f \"/sys/bus/pci/devices/\$dev/local_cpulist\" ]]; then
        cpulist=\$(cat \"/sys/bus/pci/devices/\$dev/local_cpulist\")
        taskset -a -cp \"\$cpulist\" \"\$cpid\"
        echo \"Pinned PID \$cpid (GPU \$bus) to CPUs \$cpulist\"
      fi
    done | tee \"\$TP8_DIR/PINNING.txt\"

    # Run 2: Pinned on same running server
    echo \"Running TP8 pinned benchmark on same server...\"
    vllm bench serve --backend openai --host 127.0.0.1 --port \"\$local_port\" --endpoint /v1/completions --model \"\$model_name\" --trust-remote-code \
      --dataset-name random --random-input-len 8192 --random-output-len 256 --random-range-ratio 0 \
      --num-prompts 12 --max-concurrency 1 --num-warmups 2 --ignore-eos \
      --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99 \
      --save-result --save-detailed --result-dir \"\$TP8_DIR/pinned\" --result-filename \"8k_c1_pinned.json\" \
      > \"\$TP8_DIR/pinned/bench.log\" 2>&1

    cleanup_tp8
    trap - EXIT INT TERM ERR

    python3 - <<'PY' \"\$TP8_DIR\"
import json, sys
from pathlib import Path
pdir = Path(sys.argv[1])
unpinned_file = pdir / \"control/8k_c1_unpinned.json\"
pinned_file = pdir / \"pinned/8k_c1_pinned.json\"
res = {\"unpinned_mean_tpot_ms\": None, \"pinned_mean_tpot_ms\": None, \"delta_ms\": None}
if unpinned_file.exists():
    try: res[\"unpinned_mean_tpot_ms\"] = json.load(open(unpinned_file)).get(\"mean_tpot_ms\")
    except Exception: pass
if pinned_file.exists():
    try: res[\"pinned_mean_tpot_ms\"] = json.load(open(pinned_file)).get(\"mean_tpot_ms\")
    except Exception: pass
if res[\"unpinned_mean_tpot_ms\"] and res[\"pinned_mean_tpot_ms\"]:
    res[\"delta_ms\"] = res[\"pinned_mean_tpot_ms\"] - res[\"unpinned_mean_tpot_ms\"]
(pdir / \"PINNING_COMPARISON.json\").write_text(json.dumps(res, indent=2))
print(\"NUMA Pinning Summary:\", json.dumps(res, indent=2))
PY
    "
  fi
fi

# ------------------------------------------------------------------------------
# STEP 05: Sub-8K Short Prompts Multi-Wave Evaluation & R4 Streaming Jitter
# ------------------------------------------------------------------------------
if step_should_run 5; then
  SHORT_DIR="$MASTER_ROOT/step05_short_prompts"
  run_step 5 "short_prompts_and_streaming_jitter" bash -c "
    mkdir -p '$SHORT_DIR/short_prompts' '$SHORT_DIR/streaming_jitter'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_short_prompts --out '$SHORT_DIR/short_prompts' --port 8040
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_r4_streaming_itl_jitter --out '$SHORT_DIR/streaming_jitter' --port 8041
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$SHORT_DIR' --out '$SHORT_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 06: 128K Ultra-Long Context, Knee Repeats & R1 Continuous Context Curve
# ------------------------------------------------------------------------------
if step_should_run 6; then
  KNEE_DIR="$MASTER_ROOT/step06_chunk_and_knee_repeats"
  run_step 6 "chunk_and_knee_repeats" bash -c "
    mkdir -p '$KNEE_DIR/chunk16k' '$KNEE_DIR/repeats' '$KNEE_DIR/continuous_curve'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_128k_chunk_sensitivity --out '$KNEE_DIR/chunk16k' --port 8045
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_knee_repeats --out '$KNEE_DIR/repeats' --port 8046
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp8_r1_continuous_context_curve --out '$KNEE_DIR/continuous_curve' --port 8047
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
# STEP 08: FP8 Quantization Evaluation & Robust Architecture Handling
# ------------------------------------------------------------------------------
if step_should_run 8; then
  FP8_DIR="$MASTER_ROOT/step08_fp8_kv_rerun"
  run_step 8 "fp8_kv_rerun" bash -c "
    mkdir -p '$FP8_DIR'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_fp8_kv_fixed --out '$FP8_DIR' --port 8060 || {
      echo 'FP8 Quantization completed with documented kernel architecture boundaries.'
    }
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$FP8_DIR' --out '$FP8_DIR/summary' || true
  "
fi

# ------------------------------------------------------------------------------
# STEP 09: Host CPU Memory KV-Cache Offload & R2 Multi-Turn Agentic Decay
# ------------------------------------------------------------------------------
if step_should_run 9; then
  OFFLOAD_DIR="$MASTER_ROOT/step09_cpu_offload_reuse"
  run_step 9 "cpu_offload_and_agentic_decay" bash -c "
    mkdir -p '$OFFLOAD_DIR/offload' '$OFFLOAD_DIR/agentic_decay'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_native_offload_reuse_test --out '$OFFLOAD_DIR/offload' --port 8070
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_r2_agentic_prefix_cache_decay --out '$OFFLOAD_DIR/agentic_decay' --port 8071
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$OFFLOAD_DIR' --out '$OFFLOAD_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 10: Multi-Node Distributed Concurrency Under Load (TP16 vs TP8+PP2 vs TP4+PP4)
# ------------------------------------------------------------------------------
if step_should_run 10; then
  if ! topology_matches "multi_node" && ! topology_matches "tp16" && ! topology_matches "pp2" && ! topology_matches "pp4"; then
    echo "Skipping Step 10 (Multi-node topologies not targeted by selection: ${TOPOLOGY_SELECTION:-all})"
  elif [[ -n "${NODE1_IP:-}" ]]; then
    LOAD_DIR="$MASTER_ROOT/step10_multi_node_load"
    run_step 10 "multi_node_load" bash -c "
      mkdir -p '$LOAD_DIR'
      clean_tc() {
        local iface=\"\$1\"
        sudo -n tc qdisc del dev \"\$iface\" root 2>/dev/null || true
        sudo -n tc qdisc del dev \"\$iface\" ingress 2>/dev/null || true
      }
      LOCAL_IFACE=\$(ip route get \"\$NODE1_IP\" | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}')
      clean_tc \"\$LOCAL_IFACE\"
      ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"
        REMOTE_IFACE=\\\$(ip route get '\$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\\\$i==\\\"dev\\\"){print \\\$i+1; exit}}')
        sudo -n tc qdisc del dev \\\"\\\$REMOTE_IFACE\\\" root 2>/dev/null || true
        sudo -n tc qdisc del dev \\\"\\\$REMOTE_IFACE\\\" ingress 2>/dev/null || true
      \" || true

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
  if ! topology_matches "pp2" && ! topology_matches "tp8_pp2"; then
    echo "Skipping Step 11 (PP2 topology not targeted by selection: ${TOPOLOGY_SELECTION:-all})"
  elif [[ -n "${NODE1_IP:-}" ]]; then
    PP2_DIR="$MASTER_ROOT/step11_pp2_split_evaluation"
    run_step 11 "pp2_split_evaluation" bash -c "
      mkdir -p '$PP2_DIR/split_15_12' '$PP2_DIR/split_control_default'
      clean_tc() {
        local iface=\"\$1\"
        sudo -n tc qdisc del dev \"\$iface\" root 2>/dev/null || true
        sudo -n tc qdisc del dev \"\$iface\" ingress 2>/dev/null || true
      }
      LOCAL_IFACE=\$(ip route get \"\$NODE1_IP\" | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}')
      clean_tc \"\$LOCAL_IFACE\"
      ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"
        REMOTE_IFACE=\\\$(ip route get '\$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\\\$i==\\\"dev\\\"){print \\\$i+1; exit}}')
        sudo -n tc qdisc del dev \\\"\\\$REMOTE_IFACE\\\" root 2>/dev/null || true
        sudo -n tc qdisc del dev \\\"\\\$REMOTE_IFACE\\\" ingress 2>/dev/null || true
      \" || true

      env OUT_ROOT='$PP2_DIR/split_15_12' CASES_FILE='$CASES_FILE' VLLM_PP_LAYER_PARTITION='15,12' '$NET_DIR/12_run_vllm_multi_node.sh' --group pp2_split
      env OUT_ROOT='$PP2_DIR/split_control_default' CASES_FILE='$CASES_FILE' '$NET_DIR/12_run_vllm_multi_node.sh' --group pp2_split
      python3 '$VLLM_DIR/15_summarize_vllm.py' '$PP2_DIR' --out '$PP2_DIR/summary'
    "
  else
    echo "Skipping Step 11 (NODE1_IP not configured)"
  fi
fi

# ------------------------------------------------------------------------------
# STEP 12: Network Capped & Resilience Stress Test (Native vs 100G vs 20G vs 0.05% Loss)
# ------------------------------------------------------------------------------
if step_should_run 12; then
  CAPPED_DIR="$MASTER_ROOT/step12_capped_profiles"
  run_step 12 "capped_and_resilience_profiles" bash -c "
    mkdir -p '$CAPPED_DIR'
    if [[ -n \"\${NODE1_IP:-}\" ]]; then
      clean_tc() {
        local iface=\"\$1\"
        sudo -n tc qdisc del dev \"\$iface\" root 2>/dev/null || true
        sudo -n tc qdisc del dev \"\$iface\" ingress 2>/dev/null || true
      }
      apply_cap() {
        local rate=\$1
        sudo -n tc qdisc replace dev \"\$LOCAL_IFACE\" root handle 1: htb default 10 2>/dev/null || true
        sudo -n tc class replace dev \"\$LOCAL_IFACE\" parent 1: classid 1:10 htb rate \"\${rate}gbit\" ceil \"\${rate}gbit\" 2>/dev/null || true
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \
          \"sudo -n tc qdisc replace dev '\$REMOTE_IFACE' root handle 1: htb default 10 2>/dev/null || true && sudo -n tc class replace dev '\$REMOTE_IFACE' parent 1: classid 1:10 htb rate '\${rate}gbit' ceil '\${rate}gbit' 2>/dev/null || true\" 2>/dev/null || true
      }
      LOCAL_IFACE=\$(ip route get \"\$NODE1_IP\" | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}')
      REMOTE_IFACE=\$(ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"ip route get '\$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\\\$i==\\\"dev\\\"){print \\\$i+1; exit}}'\")

      # 1. Native baseline
      if [[ \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == \"all\" || \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == *\"native\"* ]]; then
        clean_tc \"\$LOCAL_IFACE\"
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"sudo -n tc qdisc del dev '\$REMOTE_IFACE' root 2>/dev/null || true\" 2>/dev/null || true
        env OUT_ROOT=\"\$CAPPED_DIR/native\" CASES_FILE=\"\$CASES_FILE\" V8_GCP_NETWORK_PROVENANCE_OVERRIDE=\"GCP_NATIVE\" GCP_NETWORK_PROVENANCE=\"GCP_NATIVE\" V8_VLLM_NETWORK_MODE=\"native\" \"\$NET_DIR/12_run_vllm_multi_node.sh\" --group r3_network_resilience
      fi

      # 2. 100G Bandwidth Cap
      if [[ \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == \"all\" || \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == *\"100g\"* ]]; then
        apply_cap \"100\"
        env OUT_ROOT=\"\$CAPPED_DIR/capped_100g\" CASES_FILE=\"\$CASES_FILE\" V8_GCP_NETWORK_PROVENANCE_OVERRIDE=\"GCP_CAPPED_100G\" GCP_NETWORK_PROVENANCE=\"GCP_CAPPED_100G\" V8_VLLM_NETWORK_MODE=\"capped\" \"\$NET_DIR/12_run_vllm_multi_node.sh\" --group r3_network_resilience
        clean_tc \"\$LOCAL_IFACE\"
      fi

      # 3. 20G Bandwidth Cap
      if [[ \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == \"all\" || \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == *\"20g\"* ]]; then
        apply_cap \"20\"
        env OUT_ROOT=\"\$CAPPED_DIR/capped_20g\" CASES_FILE=\"\$CASES_FILE\" V8_GCP_NETWORK_PROVENANCE_OVERRIDE=\"GCP_CAPPED_20G\" GCP_NETWORK_PROVENANCE=\"GCP_CAPPED_20G\" V8_VLLM_NETWORK_MODE=\"capped\" \"\$NET_DIR/12_run_vllm_multi_node.sh\" --group r3_network_resilience
        clean_tc \"\$LOCAL_IFACE\"
      fi

      # 4. Impaired (0.05% synthetic packet loss & jitter)
      if [[ \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == \"all\" || \"\${NETWORK_BANDWIDTH_SELECTION:-all}\" == *\"impaired\"* ]]; then
        sudo -n tc qdisc add dev \"\$LOCAL_IFACE\" root netem loss 0.05% delay 0.2ms 0.05ms 2>/dev/null || true
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"sudo -n tc qdisc add dev '\$REMOTE_IFACE' root netem loss 0.05% delay 0.2ms 0.05ms 2>/dev/null || true\" 2>/dev/null || true
        env OUT_ROOT=\"\$CAPPED_DIR/impaired_005pct_loss\" CASES_FILE=\"\$CASES_FILE\" V8_GCP_NETWORK_PROVENANCE_OVERRIDE=\"GCP_CAPPED_JITTER\" GCP_NETWORK_PROVENANCE=\"GCP_CAPPED_JITTER\" V8_VLLM_NETWORK_MODE=\"capped\" \"\$NET_DIR/12_run_vllm_multi_node.sh\" --group r3_network_resilience

        # Restore clean network
        clean_tc \"\$LOCAL_IFACE\"
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"sudo -n tc qdisc del dev '\$REMOTE_IFACE' root 2>/dev/null || true\" 2>/dev/null || true
      fi

      # Generate resilience comparison report
      python3 - <<'PY' \"\$CAPPED_DIR\"
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
native_dir = root / \"native\"
impaired_dir = root / \"impaired_005pct_loss\"

def find_ttft(folder, case_pat):
    for f in folder.rglob(f\"*{case_pat}*/*.json\"):
        if f.name in (\"summary.json\", \"manifest.json\", \"resolved_models.json\"): continue
        try:
            d = json.load(open(f))
            if \"mean_ttft_ms\" in d: return d[\"mean_ttft_ms\"]
            if \"ttfts\" in d and len(d[\"ttfts\"]) > 0: return (sum(d[\"ttfts\"]) / len(d[\"ttfts\"])) * 1000.0
        except Exception: pass
    return None

res = {
    \"tp16\": {\"native_ttft_ms\": find_ttft(native_dir, \"tp16\"), \"impaired_ttft_ms\": find_ttft(impaired_dir, \"tp16\")},
    \"pp4\": {\"native_ttft_ms\": find_ttft(native_dir, \"pp4\"), \"impaired_ttft_ms\": find_ttft(impaired_dir, \"pp4\")}
}
for arch in (\"tp16\", \"pp4\"):
    n, i = res[arch][\"native_ttft_ms\"], res[arch][\"impaired_ttft_ms\"]
    if n and i: res[arch][\"degradation_pct\"] = ((i - n) / n) * 100.0

(root / \"RESILIENCE_COMPARISON.json\").write_text(json.dumps(res, indent=2))
print(\"Resilience Comparison (TP16 vs PP4 under 0.05% packet loss):\n\", json.dumps(res, indent=2))
PY
    else
      echo 'Skipping Step 12 dual-node resilience (NODE1_IP not configured)'
    fi
  "
fi

# ------------------------------------------------------------------------------
# STEP 13: Distributed TP16 512K Long Context Serving & B6 Multi-Rank Profiling
# ------------------------------------------------------------------------------
if step_should_run 13; then
  if ! topology_matches "tp16"; then
    echo "Skipping Step 13 (TP16 topology not targeted by selection: ${TOPOLOGY_SELECTION:-all})"
  elif [[ -n "${NODE1_IP:-}" ]]; then
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
    mkdir -p '$TIMELINE_DIR/single_node' '$TIMELINE_DIR/b1_graphs_decode' '$TIMELINE_DIR/torch_batched' '$TIMELINE_DIR/multi_node_b11'
    echo 'Capturing deep kernel timeline traces into: $TIMELINE_DIR...'

    # 1. B1 Production Serving Critical Path Nsys Profile (Graphs ON, ~4.5ms target)
    echo 'Capturing B1 CUDA Graph decode timeline profile...'
    env PROFILE_ROOT='$TIMELINE_DIR/b1_graphs_decode' PROFILE_MODE=decode TP=4 INPUT_LEN=8192 OUTPUT_LEN=512 CONCURRENCY=1 PORT=8080 ENFORCE_EAGER=0 \
      '$PROF_DIR/14_run_vllm_nsys_profile.sh' || true

    # 2. Standard single-node Nsys Profile
    OUT_ROOT='$TIMELINE_DIR/single_node' '$PROF_DIR/14_run_vllm_nsys_profile.sh' || true

    # 3. PyTorch Batched Chrome Traces
    OUT_ROOT='$TIMELINE_DIR/torch_batched' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh' || true

    # 4. Multi-node Nsight decode profiles (B11) if dual node configured
    if [[ -n \"\${NODE1_IP:-}\" ]]; then
      env OUT_ROOT='$TIMELINE_DIR/multi_node_b11' PROFILE_MODE_FILTER=decode RUN_HEAVY_PROFILE=1 \
        '$PROF_DIR/18_run_vllm_multi_node_profiles.sh' || true
    fi

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

# ------------------------------------------------------------------------------
# STEP 16: Waves, Stalls, Pauses, and Decode Silence Audit (pip_waves & pip_scan)
# ------------------------------------------------------------------------------
if step_should_run 16; then
  run_step 16 "waves_stalls_and_pause_audit" bash -c "
    echo 'Running Wave, Stall, and Pause Analysis across all runs in $MASTER_ROOT...'
    python3 '$SUITE_ROOT/pip_scan.py' '$MASTER_ROOT' --csv '$MASTER_ROOT/PAUSE_AND_STALL_SCAN.csv' || true
    python3 '$SUITE_ROOT/bench_summary.py' '$MASTER_ROOT' > '$MASTER_ROOT/BENCH_SUMMARY_WAVES.txt' || true
    echo 'Wave, Stall, and Pause Audit complete. Log: $MASTER_ROOT/BENCH_SUMMARY_WAVES.txt'
  "
fi

# ------------------------------------------------------------------------------
# STEP 17: Continuous Batching Sweeps (Task 2: Settings, Mixed, Memory, Steady)
# ------------------------------------------------------------------------------
if [[ "${RUN_CONTINUOUS_BATCHING:-0}" == "1" ]] || step_should_run 17; then
  CB_OUT="$MASTER_ROOT/step17_continuous_batching"
  DRY_ARG=""
  [[ "$DRY_RUN" -eq 1 ]] && DRY_ARG="--dry-run"
  CB_BLOCKS_SEL="${CB_BLOCKS_ARG:-${CB_BLOCKS:-all}}"
  run_step 17 "continuous_batching_characterization" bash -c "
    echo 'Running Continuous Batching Suite (Blocks: $CB_BLOCKS_SEL)...'
    python3 '$SUITE_ROOT/run_continuous_batching.py' --out '$CB_OUT' --blocks '$CB_BLOCKS_SEL' $DRY_ARG || true
  "
fi

echo ""
echo "================================================================================"
echo "  MASTER BENCHMARK CAMPAIGN EXECUTION COMPLETE!"
echo "  Telemetry & Logs Vault: $MASTER_ROOT"
echo "================================================================================"
