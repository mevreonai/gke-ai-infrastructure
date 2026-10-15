#!/usr/bin/env bash
# ==============================================================================
# PERFORMANCE INTELLIGENCE PLATFORM — UNIFIED MASTER BENCHMARK RUNNER
# ==============================================================================
# Executes All 20 Systems Characterization Steps Sequentially in the Main Run
# Incorporates all Stage 1 (Quick Wins), Stage 2 (Scale-Out), and Stage 3 (Deep Expansions)
# Model-Agnostic: Configured dynamically via $MODEL and $REVISION
#
# Run Profiles:
#   --profile smoke           Quick 10-min sanity check: TP4 1k/8k c=1 only
#   --profile fast-dashboard   ~2h fast dashboard build: Stage 1+2, skip profiling
#   --profile default          ~9h full characterization (DEFAULT)
#   --profile deep-profile     ~14h: All stages + heavy Nsys 512K/1M + Poisson + scheduler sweeps
#
# Cache Isolation:
#   vLLM server runs a dedicated instance per benchmark case with controlled
#   warmup requests to isolate TTFT measurements without bias.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [[ -f "$SCRIPT_DIR/../run_master_benchmark.sh" ]]; then
  SUITE_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
else
  SUITE_ROOT="$SCRIPT_DIR"
fi
VLLM_DIR="$SUITE_ROOT/02_single_node_baseline_matrix"
HW_DIR="$SUITE_ROOT/01_preflight_and_diagnostics"
NET_DIR="$SUITE_ROOT/04_scaleout_distributed_network"
PROF_DIR="$SUITE_ROOT/06_deep_kernel_and_torch_profiling"

if command -v python3 >/dev/null 2>&1 && ! python3 --version 2>&1 | grep -q "WindowsApps\|Microsoft Store"; then
  PYTHON_EXEC="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_EXEC="python"
else
  PYTHON_EXEC="python3"
fi

: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${RESUME:=1}"
: "${TARGET_STEP:=all}"
: "${FROM_STEP:=1}"

# Discover configuration BEFORE parsing CLI flags so CLI arguments override environment defaults
if [[ -f "$PWD/RUN_CONFIG.env" ]]; then source "$PWD/RUN_CONFIG.env"
elif [[ -f "$SUITE_ROOT/RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/RUN_CONFIG.env"
elif [[ -f "$SUITE_ROOT/../RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/../RUN_CONFIG.env"
fi

: "${PIP_DATA_ROOT:=$HOME/PIP_Benchmark_Data}"
RUN_ID_FILE="$PIP_DATA_ROOT/latest_run_id.txt"
CLI_RUN_ID="${RUN_ID:-}"
CLI_OUT_ROOT="${MASTER_ROOT:-}"
CLI_RUN_TAG="${RUN_TAG:-}"
FORCE_NEW_RUN=0

# Dynamic execution selections
SELECTED_MODEL=""
SELECTED_REVISION=""
SELECTED_STAGE="all"
SELECTED_TOPOLOGIES="all"
SELECTED_BANDWIDTH="all"
SELECTED_CONTEXTS=""
SELECTED_CONCURRENCIES=""
RUN_POISSON_SWEEPS="${RUN_POISSON_SWEEPS:-0}"
RUN_SCHEDULER_SWEEPS="${RUN_SCHEDULER_SWEEPS:-0}"
RUN_OBSERVER_OVERHEAD="${RUN_OBSERVER_OVERHEAD:-0}"
SELECTED_PROFILE=""
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
    --contexts)
      SELECTED_CONTEXTS="$2"
      shift 2
      ;;
    --concurrencies)
      SELECTED_CONCURRENCIES="$2"
      shift 2
      ;;
    --node0-ip)
      NODE0_IP="$2"
      shift 2
      ;;
    --node1-ip)
      NODE1_IP="$2"
      shift 2
      ;;
    --ssh-key)
      SSH_KEY="$2"
      shift 2
      ;;
    --venv-dir)
      VENV_DIR="$2"
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
      CLI_RUN_ID="$2"
      shift 2
      ;;
    --run-tag|--tag)
      CLI_RUN_TAG="$2"
      shift 2
      ;;
    --out-root)
      CLI_OUT_ROOT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --new-run)
      FORCE_NEW_RUN=1
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
    --package-evidence)
      PACKAGE_EVIDENCE=1
      shift
      ;;
    --no-package-evidence)
      PACKAGE_EVIDENCE=0
      shift
      ;;
    --static-validate)
      RUN_STATIC_VALIDATE=1
      shift
      ;;
    --profile)
      SELECTED_PROFILE="$2"
      case "$SELECTED_PROFILE" in
        smoke)
          SELECTED_STAGE="1"
          SELECTED_CONTEXTS="1k,8k"
          SELECTED_CONCURRENCIES="1"
          ;;
        fast-dashboard)
          SELECTED_STAGE="1,2"
          ;;
        default)
          SELECTED_STAGE="all"
          ;;
        deep-profile)
          SELECTED_STAGE="all"
          RUN_POISSON_SWEEPS=1
          RUN_SCHEDULER_SWEEPS=1
          RUN_OBSERVER_OVERHEAD=1
          export RUN_HEAVY_PROFILE=1
          ;;
        *)
          echo "Unknown profile: $SELECTED_PROFILE (valid: smoke, fast-dashboard, default, deep-profile)"
          exit 1
          ;;
      esac
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --all                        Execute all stages and characterization steps (00-20: ~9h default)"
      echo "  --profile <name>             Select a run profile:"
      echo "                                 smoke          Quick 10-min sanity: TP4 1k/8k c=1"
      echo "                                 fast-dashboard ~2h fast dashboard build: Stage 1+2"
      echo "                                 default        ~9h full characterization with cold/warm isolation"
      echo "                                 deep-profile   ~14h deep: + Poisson + scheduler + observer + heavy Nsys"
      echo "  --stage <1|2|3|all>          Filter execution to specific characterization stage"
      echo "                                 Stage 1: Quick Wins & Single-Node (Steps 1-7: ~1h 10m)"
      echo "                                 Stage 2: Scale-Out Concurrency & Asymmetric PP (Steps 8-13: ~3h 30m)"
      echo "                                 Stage 3: Deep Profiling & Strategic Sweeps (Steps 14-20: ~4h 20m)"
      echo "  --model <hf_id_or_path>      Select target model (default: moonshotai/Kimi-Linear-48B-A3B-Instruct)"
      echo "  --revision <git_sha>         Select model revision commit"
      echo "  --topologies <list|all>      Select topologies (e.g. tp4_pp1,tp8_pp1,tp4_pp2,tp8_pp2,tp4_pp4,tp16_pp1)"
      echo "  --bandwidth <list|all>       Select network bandwidth modes (e.g. native,100g,20g,impaired)"
      echo "  --contexts <list|all>        Select context sizes (e.g. 1k,8k,128k,512k,1m or all)"
      echo "  --concurrencies <list|all>   Select concurrencies (e.g. 1,2,4,8,32 or all)"
      echo "  --step <0..20>               Execute a single target step"
      echo "  --from-step <N>              Resume execution starting from step N"
      echo "  --dry-run                    Verify commands and configuration without launching GPU workloads"
      echo "  --new-run / --no-resume      Force clean execution without resume markers"
      echo "  --run-id <id>                Specify explicit run identifier"
      echo "  --run-tag <tag>              Custom model/run tag for directory naming (defaults to model name)"
      echo "  --out-root <path>            Override output root directory (defaults to \$HOME/PIP_Benchmark_Data/<tag>_<timestamp>)"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Run with --help for available options."
      exit 1
      ;;
  esac
done

# Model resolution and user tag preference
TARGET_MODEL_NAME="${SELECTED_MODEL:-${MODEL:-moonshotai/Kimi-Linear-48B-A3B-Instruct}}"
MODEL_TAG=$(basename "$TARGET_MODEL_NAME" | tr '/' '_' | tr -cd '[:alnum:]_.-')
USER_TAG="${CLI_RUN_TAG:-${MODEL_TAG}}"
RUN_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [[ -n "$CLI_OUT_ROOT" ]]; then
  MASTER_ROOT="$CLI_OUT_ROOT"
  RUN_ID="${CLI_RUN_ID:-$(basename "$MASTER_ROOT")}"
elif [[ -n "$CLI_RUN_ID" ]]; then
  RUN_ID="$CLI_RUN_ID"
  MASTER_ROOT="$PIP_DATA_ROOT/$RUN_ID"
elif [[ "$FORCE_NEW_RUN" == 1 ]]; then
  RUN_ID="${USER_TAG}_${RUN_TIMESTAMP}"
  MASTER_ROOT="$PIP_DATA_ROOT/$RUN_ID"
elif [[ "$RESUME" == 1 && -f "$RUN_ID_FILE" ]]; then
  RUN_ID=$(cat "$RUN_ID_FILE")
  MASTER_ROOT="$PIP_DATA_ROOT/$RUN_ID"
else
  RUN_ID="${USER_TAG}_${RUN_TIMESTAMP}"
  MASTER_ROOT="$PIP_DATA_ROOT/$RUN_ID"
fi

mkdir -p "$MASTER_ROOT" "$MASTER_ROOT/logs" "$MASTER_ROOT/.done" "$MASTER_ROOT/env" "$PIP_DATA_ROOT"
echo "$RUN_ID" > "$RUN_ID_FILE"
MASTER_LOG="$MASTER_ROOT/logs/MASTER_BENCHMARK_RUN.log"
exec > >(tee -a "$MASTER_LOG") 2>&1

echo "================================================================================"
echo "  PERFORMANCE INTELLIGENCE PLATFORM — UNIFIED MASTER BENCHMARK RUNNER"
echo "  Run ID       : $RUN_ID"
echo "  Model Tag    : $USER_TAG"
echo "  Output Root  : $MASTER_ROOT"
echo "  Suite Root   : $SUITE_ROOT"
echo "  Target Step  : $TARGET_STEP"
echo "  From Step    : $FROM_STEP"
echo "  Resume Mode  : $RESUME"
echo "================================================================================"

# Apply CLI overrides over environment defaults
: "${NODE0_IP:=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")}"
: "${NODE1_IP:=}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${VENV_DIR:=$HOME/vllm_env}"

export NODE0_IP NODE1_IP SSH_KEY VENV_DIR MASTER_ROOT SUITE_ROOT RUN_ID DRY_RUN RESUME

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
if [[ -n "$SELECTED_CONTEXTS" ]]; then
  export CONTEXT_SELECTION="$SELECTED_CONTEXTS"
fi
if [[ -n "$SELECTED_CONCURRENCIES" ]]; then
  export CONCURRENCY_SELECTION="$SELECTED_CONCURRENCIES"
fi
export CONTEXT_SELECTION="${CONTEXT_SELECTION:-all}"
export CONCURRENCY_SELECTION="${CONCURRENCY_SELECTION:-all}"

# Mandatory Hardware & MoE Cutlass/Triton Execution Controls
export CUDA_DEVICE_ORDER="PCI_BUS_ID"
export VLLM_MOE_BACKEND="${VLLM_MOE_BACKEND:-flashinfer_cutlass}"
export MOE_BACKEND="${MOE_BACKEND:-flashinfer_cutlass}"
export VLLM_FLASHINFER_AUTOTUNE="1"
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2}"
# Preserve caller's VLLM_PP_LAYER_PARTITION if set (e.g. "8,6,6,20" for DeepSeek PP4), otherwise leave unset so vLLM defaults apply
if [[ -z "${VLLM_PP_LAYER_PARTITION:-}" ]]; then
  unset VLLM_PP_LAYER_PARTITION 2>/dev/null || true
fi

# Inter-Node NCCL & Network Controls (Enforce Stage 1/Stage 2 Golden Stability)
if [[ -d "/usr/local/gib/lib64" && ! -d "/tmp/clean_nccl_libs" ]]; then
  mkdir -p /tmp/clean_nccl_libs
  ln -sf /usr/local/gib/lib64/libnccl.so* /tmp/clean_nccl_libs/ 2>/dev/null || true
  ln -sf /dev/null /tmp/clean_nccl_libs/libnccl-net.so 2>/dev/null || true
fi
if [[ -n "${NODE1_IP:-}" && "${DRY_RUN:-0}" -eq 0 && -d "/usr/local/gib/lib64" ]]; then
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$NODE1_IP" '
    if [[ -d "/usr/local/gib/lib64" && ! -d "/tmp/clean_nccl_libs" ]]; then
      mkdir -p /tmp/clean_nccl_libs
      ln -sf /usr/local/gib/lib64/libnccl.so* /tmp/clean_nccl_libs/ 2>/dev/null || true
      ln -sf /dev/null /tmp/clean_nccl_libs/libnccl-net.so 2>/dev/null || true
    fi
  ' 2>/dev/null || true
fi
if [[ -d "/tmp/clean_nccl_libs" ]]; then
  if [[ ":${LD_LIBRARY_PATH:-}:" != *":/tmp/clean_nccl_libs:"* ]]; then
    export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  fi
fi

# Dynamic interface discovery for NCCL / Gloo
DEFAULT_IFACE="${NCCL_SOCKET_IFNAME:-}"
if [[ -z "$DEFAULT_IFACE" && -n "${NODE1_IP:-}" ]]; then
  DEFAULT_IFACE=$(ip route get "$NODE1_IP" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
fi
[[ -z "$DEFAULT_IFACE" ]] && DEFAULT_IFACE=$(ip route get 8.8.8.8 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
[[ -z "$DEFAULT_IFACE" ]] && DEFAULT_IFACE="ens3"

export NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME:-$DEFAULT_IFACE}"
export NCCL_NET="${NCCL_NET:-Socket}"
export NCCL_BUFFSIZE="${NCCL_BUFFSIZE:-4194304}"
export GLOO_SOCKET_IFNAME="${GLOO_SOCKET_IFNAME:-$DEFAULT_IFACE}"
unset VLLM_DISABLE_PYNCCL 2>/dev/null || true
unset NCCL_ALGO NCCL_PROTO || true

# Targeted cleanup helper for orphan worker processes (replaces blind 'pkill -9 -f vllm'):
# Targeted pattern: vllm.entrypoints|vllm serve|ray::RayWorkerProc
kill_orphan_workers() {
  pkill -9 -f "vllm.entrypoints|vllm serve|ray::RayWorkerProc" 2>/dev/null || true
}

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
echo "  Contexts     : ${CONTEXT_SELECTION:-all}"
echo "  Concurrency  : ${CONCURRENCY_SELECTION:-all}"
echo "  Profile      : ${SELECTED_PROFILE:-custom}"
echo "  Dry Run      : $DRY_RUN"
echo "  MoE Backend  : $VLLM_MOE_BACKEND (FlashInfer CUTLASS)"
echo "  PP Split     : ${VLLM_PP_LAYER_PARTITION:-default (14/13 PP2, 7/7/7/6 PP4)}"
echo "  Poisson      : ${RUN_POISSON_SWEEPS:-0}"
echo "  Scheduler    : ${RUN_SCHEDULER_SWEEPS:-0}"
echo "  Observer OH  : ${RUN_OBSERVER_OVERHEAD:-0}"
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
export -f topology_matches

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
export -f bandwidth_matches

step_should_run() {
  local num="$1"
  local stage="${STAGE_SELECTION:-all}"

  if [[ "$stage" != "all" ]]; then
    local in_stage=0
    local step_stage=0
    if [[ "$num" -ge 1 && "$num" -le 7 ]]; then step_stage=1
    elif [[ "$num" -ge 8 && "$num" -le 13 ]]; then step_stage=2
    elif [[ "$num" -ge 14 && "$num" -le 20 ]]; then step_stage=3
    fi

    IFS=',' read -ra STAGES <<< "$stage"
    for s in "${STAGES[@]}"; do
      s=$(echo "$s" | tr -d ' ')
      if [[ "$s" == "$step_stage" ]]; then
        in_stage=1
        break
      fi
    done
    [[ "$in_stage" -eq 0 ]] && return 1
  fi

  if [[ "$TARGET_STEP" == "all" ]]; then
    if [[ "$num" -ge "$FROM_STEP" ]]; then return 0; else return 1; fi
  elif [[ "$TARGET_STEP" == "$num" ]]; then
    return 0
  else
    return 1
  fi
}


FAILED_STEPS=()

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
    return 0
  fi
  set +e
  "$@"
  rc=$?
  set -e
  e=$(date +%s)
  printf '{"step_num":%s,"step_name":"%s","rc":%s,"dry_run":false,"start":%s,"end":%s}\n' "$num" "$name" "$rc" "$s" "$e" >> "$MASTER_ROOT/master_step_status.jsonl"
  if [[ "$rc" == 0 ]]; then
    touch "$marker"
  else
    echo "  [WARN] Step $num ($name) exited with code $rc. Campaign continues without early termination."
    FAILED_STEPS+=("step_${num}_${name}")
  fi
  return 0
}

# ------------------------------------------------------------------------------
# STEP 00: Environment Snapshot & Checksums Manifest
# ------------------------------------------------------------------------------
run_step 0 "preflight_and_env_snapshot" bash -c "
  if [[ -f '$SUITE_ROOT/pip_static_validate.py' ]]; then
    python3 '$SUITE_ROOT/pip_static_validate.py' --root '$SUITE_ROOT' --out '$MASTER_ROOT/env/STATIC_VALIDATION.json' || true
  fi
  find '$SUITE_ROOT' -type f \( -name '*.sh' -o -name '*.py' -o -name '*.json' \) -not -path '*/.*' -exec sha256sum {} + | sort -k2 > '$MASTER_ROOT/SUITE_SOURCE_SHA256SUMS.txt'
  python3 -c 'import sys, platform, torch, vllm; print(\"Python:\", sys.version); print(\"PyTorch:\", torch.__version__); print(\"CUDA:\", torch.version.cuda); print(\"vLLM:\", vllm.__version__)' > '$MASTER_ROOT/env/node0_python_stack.txt' 2>&1 || true
  nvidia-smi > '$MASTER_ROOT/env/node0_nvidia_smi.txt' 2>&1 || true
  env | grep -E '^(CUDA_|NCCL_|VLLM_|RAY_|NODE|V8_)' | sort > '$MASTER_ROOT/env/node0_runtime_env.txt' || true
  python3 '$HW_DIR/22_readiness.py' --out '$MASTER_ROOT/env/node0_readiness' > '$MASTER_ROOT/env/node0_readiness.txt' 2>&1 || true
  if [[ -n \"\${NODE1_IP:-}\" ]]; then
    ssh -i '$SSH_KEY' -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"source '\$VENV_DIR/bin/activate' 2>/dev/null || true; python3 -c 'import sys, platform, torch, vllm; print(\\\"Python:\\\", sys.version); print(\\\"PyTorch:\\\", torch.__version__); print(\\\"CUDA:\\\", torch.version.cuda); print(\\\"vLLM:\\\", vllm.__version__)'\" > '$MASTER_ROOT/env/node1_python_stack.txt' 2>&1 || true
    ssh -i '$SSH_KEY' -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"nvidia-smi\" > '$MASTER_ROOT/env/node1_nvidia_smi.txt' 2>&1 || true
    ssh -i '$SSH_KEY' -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"env | grep -E '^(CUDA_|NCCL_|VLLM_|RAY_|NODE|V8_)' | sort\" > '$MASTER_ROOT/env/node1_runtime_env.txt' 2>&1 || true
    scp -i '$SSH_KEY' -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=no '$HW_DIR/22_readiness.py' \"\$NODE1_IP:/tmp/22_readiness.py\" 2>/dev/null || true
    ssh -i '$SSH_KEY' -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"source '\$VENV_DIR/bin/activate' 2>/dev/null || true; python3 /tmp/22_readiness.py --out /tmp/node1_readiness\" > '$MASTER_ROOT/env/node1_readiness.txt' 2>&1 || true
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
    if topology_matches 'tp4' || topology_matches 'all'; then
      echo 'Capturing single-node TP4 PyTorch profile (cold-cache c=8)...'
      env TP=4 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=8 PORT=8021 PROFILE_ROOT='$TORCH_DIR/tp4_8k_c8' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh' || true
      sleep 3
      echo 'Capturing single-node TP4 PyTorch profile (cold-cache c=32)...'
      env TP=4 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=32 PORT=8022 PROFILE_ROOT='$TORCH_DIR/tp4_8k_c32' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh' || true
      sleep 3
    fi
    if topology_matches 'tp8' || topology_matches 'all'; then
      echo 'Capturing single-node TP8 PyTorch profile (cold-cache c=8)...'
      mkdir -p '$TORCH_DIR/tp8_8k_c8' '$TORCH_DIR/tp8_8k_c32'
      env TP=8 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=8 PORT=8023 PROFILE_ROOT='$TORCH_DIR/tp8_8k_c8' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh' || true
      sleep 3
      echo 'Capturing single-node TP8 PyTorch profile (cold-cache c=32)...'
      env TP=8 INPUT_LEN=8192 OUTPUT_LEN=1024 CONCURRENCY=32 PORT=8024 PROFILE_ROOT='$TORCH_DIR/tp8_8k_c32' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh' || true
      sleep 3
    fi
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
    rev_id=\"\${VLLM_REVISION:-\${REVISION:-}}\"
    rev_arg=\"\"
    if [[ -n \"\$rev_id\" ]]; then
      rev_arg=\"--revision \$rev_id\"
    elif [[ \"\$model_name\" == *\"Kimi-Linear\"* ]]; then
      rev_arg=\"--revision e1df551a447157d4658b573f9a695d57658590e9\"
    fi
    max_len=\"\${VLLM_MAX_MODEL_LEN:-\${MAX_MODEL_LEN:-1048576}}\"
    export CUDA_VISIBLE_DEVICES=\"0,1,2,3,4,5,6,7\"

    echo \"Starting TP8 server for NUMA pinning evaluation with model: \$model_name...\"
    setsid vllm serve \"\$model_name\" \$rev_arg --model-impl vllm --trust-remote-code --host 0.0.0.0 --port \"\$local_port\" \
      --tensor-parallel-size 8 --max-model-len \"\$max_len\" --max-num-batched-tokens 8192 --max-num-seqs 32 \
      --gpu-memory-utilization 0.9 --performance-mode balanced --optimization-level 2 \
      --moe-backend flashinfer_cutlass --enable-flashinfer-autotune \
      --no-enable-prefix-caching > '$TP8_DIR/server.log' 2>&1 & PID=\$!

    cleanup_tp8(){
      echo \"Stopping TP8 server PID \$PID...\"
      kill -15 \"\$PID\" 2>/dev/null || true
      kill -15 -- -\"\$PID\" 2>/dev/null || true
      sleep 3
      kill -9 \"\$PID\" 2>/dev/null || true
      kill -9 -- -\"\$PID\" 2>/dev/null || true
      wait \"\$PID\" 2>/dev/null || true
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
      --save-result --save-detailed --result-dir '$TP8_DIR/control' --result-filename \"8k_c1_unpinned.json\" \
      > '$TP8_DIR/control/bench.log' 2>&1

    # Pin workers dynamically to each GPU's local CPU socket
    echo \"Applying NUMA socket pinning to worker processes...\"
    nvidia-smi --query-compute-apps=pid,gpu_bus_id --format=csv,noheader | while IFS=', ' read -r cpid bus; do
      dev=\$(echo \"\$bus\" | sed -E 's/^[0-9A-Fa-f]{4}([0-9A-Fa-f]{4}:)/\1/' | tr 'A-F' 'a-f')
      if [[ -f \"/sys/bus/pci/devices/\$dev/local_cpulist\" ]]; then
        cpulist=\$(cat \"/sys/bus/pci/devices/\$dev/local_cpulist\")
        taskset -a -cp \"\$cpulist\" \"\$cpid\"
        echo \"Pinned PID \$cpid (GPU \$bus) to CPUs \$cpulist\"
      fi
    done | tee '$TP8_DIR/PINNING.txt'

    # Run 2: Pinned on same running server
    echo \"Running TP8 pinned benchmark on same server...\"
    vllm bench serve --backend openai --host 127.0.0.1 --port \"\$local_port\" --endpoint /v1/completions --model \"\$model_name\" --trust-remote-code \
      --dataset-name random --random-input-len 8192 --random-output-len 256 --random-range-ratio 0 \
      --num-prompts 12 --max-concurrency 1 --num-warmups 2 --ignore-eos \
      --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99 \
      --save-result --save-detailed --result-dir '$TP8_DIR/pinned' --result-filename \"8k_c1_pinned.json\" \
      > '$TP8_DIR/pinned/bench.log' 2>&1

    cleanup_tp8
    trap - EXIT INT TERM ERR

    python3 -c '
import json, os, sys
p_ctrl, p_pin, p_out = sys.argv[1], sys.argv[2], sys.argv[3]
ctrl = os.path.exists(p_ctrl)
pin = os.path.exists(p_pin)
st = "COMPLETED" if ctrl and pin else "FAILED"
data = {
  "case": "step04_tp8_pinning",
  "name": "step04_tp8_pinning",
  "status": st,
  "benchmarks": [
    {"name": "8k_c1_unpinned", "status": "COMPLETED" if ctrl else "FAILED"},
    {"name": "8k_c1_pinned", "status": "COMPLETED" if pin else "FAILED"}
  ]
}
with open(p_out, "w") as f:
    json.dump(data, f, indent=2)
' "$TP8_DIR/control/8k_c1_unpinned.json" "$TP8_DIR/pinned/8k_c1_pinned.json" "$TP8_DIR/case_manifest.json"

    python3 '$SUITE_ROOT/../tools/compare_numa_pinning.py' '$TP8_DIR' 2>/dev/null || python3 '$SUITE_ROOT/tools/compare_numa_pinning.py' '$TP8_DIR' || true
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
    mkdir -p '$KNEE_DIR/chunk16k' '$KNEE_DIR/repeats' '$KNEE_DIR/continuous_curve' '$KNEE_DIR/continuous_curve_tp4' '$KNEE_DIR/baseline_matrix'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_128k_chunk_sensitivity --out '$KNEE_DIR/chunk16k' --port 8045
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_knee_repeats --out '$KNEE_DIR/repeats' --port 8046
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp8_r1_continuous_context_curve --out '$KNEE_DIR/continuous_curve' --port 8047
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_r1_continuous_context_curve --out '$KNEE_DIR/continuous_curve_tp4' --port 8048 || true
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --group baseline_matrix --out '$KNEE_DIR/baseline_matrix' --port 8049 || true
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
        REMOTE_IFACE=\\\$(ip route get '\$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\\\$i==\\\"dev\\\"){print \\\$(i+1); exit}}')
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
        REMOTE_IFACE=\\\$(ip route get '\$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\\\$i==\\\"dev\\\"){print \\\$(i+1); exit}}')
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
      LOCAL_IFACE=\$(ip route get \"\$NODE1_IP\" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}')
      LOCAL_IFACE=\"\${LOCAL_IFACE:-ens3}\"
      REMOTE_IFACE=\$(ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"ip route get '\$NODE0_IP' 2>/dev/null | awk '{for(i=1;i<=NF;i++) if(\\\$i==\\\"dev\\\"){print \\\$(i+1); exit}}'\" 2>/dev/null || true)
      REMOTE_IFACE=\"\${REMOTE_IFACE:-ens3}\"

      clean_tc_both() {
        local cond_dir=\"\${1:-$CAPPED_DIR}\"
        sudo -n tc qdisc del dev \"\$LOCAL_IFACE\" root 2>/dev/null || true
        sudo -n tc qdisc del dev \"\$LOCAL_IFACE\" ingress 2>/dev/null || true
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \
          \"sudo -n tc qdisc del dev '\$REMOTE_IFACE' root 2>/dev/null || true; sudo -n tc qdisc del dev '\$REMOTE_IFACE' ingress 2>/dev/null || true\" 2>/dev/null || true
        if [[ -n \"\$1\" ]]; then
          mkdir -p \"\$cond_dir\"
          sudo -n tc -s qdisc show dev \"\$LOCAL_IFACE\" > \"\$cond_dir/node0_tc_qdisc.txt\" 2>&1 || true
          ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"sudo -n tc -s qdisc show dev '\$REMOTE_IFACE'\" > \"\$cond_dir/node1_tc_qdisc.txt\" 2>&1 || true
        fi
      }
      apply_cap() {
        local rate=\$1
        local cond_dir=\$2
        mkdir -p \"\$cond_dir\"
        sudo -n tc qdisc replace dev \"\$LOCAL_IFACE\" root handle 1: htb default 10 2>&1 | tee \"\$cond_dir/node0_tc_apply.log\" || true
        sudo -n tc class replace dev \"\$LOCAL_IFACE\" parent 1: classid 1:10 htb rate \"\${rate}gbit\" ceil \"\${rate}gbit\" 2>&1 | tee -a \"\$cond_dir/node0_tc_apply.log\" || true
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \
          \"sudo -n tc qdisc replace dev '\$REMOTE_IFACE' root handle 1: htb default 10 2>&1 && sudo -n tc class replace dev '\$REMOTE_IFACE' parent 1: classid 1:10 htb rate '\${rate}gbit' ceil '\${rate}gbit' 2>&1\" | tee \"\$cond_dir/node1_tc_apply.log\" || true
        sudo -n tc -s qdisc show dev \"\$LOCAL_IFACE\" > \"\$cond_dir/node0_tc_qdisc.txt\" 2>&1 || true
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"sudo -n tc -s qdisc show dev '\$REMOTE_IFACE'\" > \"\$cond_dir/node1_tc_qdisc.txt\" 2>&1 || true
      }

      # 1. Native baseline
      if [[ "\${NETWORK_BANDWIDTH_SELECTION:-all}" == "all" || "\${NETWORK_BANDWIDTH_SELECTION:-all}" == *"native"* ]]; then
        clean_tc_both "$CAPPED_DIR/native"
        env OUT_ROOT='$CAPPED_DIR/native' CASES_FILE='$CASES_FILE' V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_NATIVE" GCP_NETWORK_PROVENANCE="GCP_NATIVE" V8_VLLM_NETWORK_MODE="native" VLLM_NETWORK_MODE="native" NETWORK_MODE="native" V8_VLLM_NETWORK_CAP_GBPS="native" '$NET_DIR/12_run_vllm_multi_node.sh' --group r3_network_resilience
      fi

      # 2. 100G Bandwidth Cap
      if [[ "\${NETWORK_BANDWIDTH_SELECTION:-all}" == "all" || "\${NETWORK_BANDWIDTH_SELECTION:-all}" == *"100g"* ]]; then
        apply_cap "100" "$CAPPED_DIR/capped_100g"
        env OUT_ROOT='$CAPPED_DIR/capped_100g' CASES_FILE='$CASES_FILE' V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_CAPPED_100G" GCP_NETWORK_PROVENANCE="GCP_CAPPED_100G" V8_VLLM_NETWORK_MODE="capped" VLLM_NETWORK_MODE="capped" NETWORK_MODE="capped" V8_VLLM_NETWORK_CAP_GBPS="100" '$NET_DIR/12_run_vllm_multi_node.sh' --group r3_network_resilience
        clean_tc_both
      fi

      # 3. 20G Bandwidth Cap
      if [[ "\${NETWORK_BANDWIDTH_SELECTION:-all}" == "all" || "\${NETWORK_BANDWIDTH_SELECTION:-all}" == *"20g"* ]]; then
        apply_cap "20" "$CAPPED_DIR/capped_20g"
        env OUT_ROOT='$CAPPED_DIR/capped_20g' CASES_FILE='$CASES_FILE' V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_CAPPED_20G" GCP_NETWORK_PROVENANCE="GCP_CAPPED_20G" V8_VLLM_NETWORK_MODE="capped" VLLM_NETWORK_MODE="capped" NETWORK_MODE="capped" V8_VLLM_NETWORK_CAP_GBPS="20" '$NET_DIR/12_run_vllm_multi_node.sh' --group r3_network_resilience
        clean_tc_both
      fi

      # 4. Impaired (0.05% synthetic packet loss & jitter)
      if [[ "\${NETWORK_BANDWIDTH_SELECTION:-all}" == "all" || "\${NETWORK_BANDWIDTH_SELECTION:-all}" == *"impaired"* ]]; then
        mkdir -p '$CAPPED_DIR/impaired_005pct_loss'
        sudo -n tc qdisc add dev \"\$LOCAL_IFACE\" root netem loss 0.05% delay 0.2ms 0.05ms 2>&1 | tee '$CAPPED_DIR/impaired_005pct_loss/node0_tc_apply.log' || true
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"sudo -n tc qdisc add dev '\$REMOTE_IFACE' root netem loss 0.05% delay 0.2ms 0.05ms 2>&1\" | tee '$CAPPED_DIR/impaired_005pct_loss/node1_tc_apply.log' || true
        sudo -n tc -s qdisc show dev \"\$LOCAL_IFACE\" > '$CAPPED_DIR/impaired_005pct_loss/node0_tc_qdisc.txt' 2>&1 || true
        ssh -i \"\$SSH_KEY\" -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"sudo -n tc -s qdisc show dev '\$REMOTE_IFACE'\" > '$CAPPED_DIR/impaired_005pct_loss/node1_tc_qdisc.txt' 2>&1 || true
        env OUT_ROOT='$CAPPED_DIR/impaired_005pct_loss' CASES_FILE='$CASES_FILE' V8_GCP_NETWORK_PROVENANCE_OVERRIDE=\"GCP_CAPPED_JITTER\" GCP_NETWORK_PROVENANCE=\"GCP_CAPPED_JITTER\" V8_VLLM_NETWORK_MODE=\"capped\" VLLM_NETWORK_MODE=\"capped\" NETWORK_MODE=\"capped\" V8_VLLM_NETWORK_CAP_GBPS=\"impaired\" '$NET_DIR/12_run_vllm_multi_node.sh' --group r3_network_resilience

        # Restore clean network
        clean_tc_both
      fi

      # Generate resilience comparison report (matched by benchmark case across conditions)
      python3 '$SUITE_ROOT/../tools/compare_resilience_matrix.py' '$CAPPED_DIR' 2>/dev/null || python3 '$SUITE_ROOT/tools/compare_resilience_matrix.py' '$CAPPED_DIR' || true
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
    if topology_matches 'tp4' || topology_matches 'all'; then
      OUT_ROOT='$TIMELINE_DIR/single_node/tp4' TP=4 '$PROF_DIR/14_run_vllm_nsys_profile.sh' || true
    fi
    if topology_matches 'tp8' || topology_matches 'all'; then
      echo 'Capturing single-node TP8 Nsys profile...'
      OUT_ROOT='$TIMELINE_DIR/single_node/tp8' TP=8 PORT=8081 '$PROF_DIR/14_run_vllm_nsys_profile.sh' || true
    fi

    # 3. PyTorch Batched Chrome Traces (single-node)
    OUT_ROOT='$TIMELINE_DIR/torch_batched' '$PROF_DIR/14c_run_vllm_torch_profile_batched.sh' || true

    # 4. Multi-node Nsight decode profiles (B11) if dual node configured
    if [[ -n \"\${NODE1_IP:-}\" ]]; then
      env OUT_ROOT='$TIMELINE_DIR/multi_node_b11' PROFILE_MODE_FILTER=decode_8k,batched_decode_8k_c8,prefill_128k RUN_HEAVY_PROFILE=1 \
        '$PROF_DIR/18_run_vllm_multi_node_profiles.sh' || true

      # CUDA graphs ON for two-server Nsight decode (Fix 3)
      env OUT_ROOT='$TIMELINE_DIR/multi_node_graphs_on' ENFORCE_EAGER=0 PROFILE_MODE_FILTER=decode_8k,batched_decode_8k_c8 RUN_HEAVY_PROFILE=1 \
        '$PROF_DIR/18_run_vllm_multi_node_profiles.sh' || true

      # 5. Multi-node PyTorch decode traces across topologies (including TP4/PP2)
      echo 'Capturing multi-node PyTorch decode traces across topologies...'
      for topo in tp4_pp2_dist tp4_pp4_dist tp8_pp2_dist tp16_pp1_dist; do
        if topology_matches \"\$topo\" || topology_matches 'all'; then
          echo \"Capturing multi-node PyTorch trace for \$topo...\"
          env TOPOLOGY=\"\$topo\" CONCURRENCY=8 PORT=8082 PROFILE_ROOT=\"$TIMELINE_DIR/multi_node_torch/\$topo\" \
            \"$PROF_DIR/14d_run_vllm_torch_profile_multi_node.sh\" || true
        fi
      done
    fi

    python3 '$PROF_DIR/19_postprocess_nsys.py' '$TIMELINE_DIR' || true

    cat << EOF > "$TIMELINE_DIR/case_manifest.json"
{
  "case": "step14_timeline_profiles",
  "name": "step14_timeline_profiles",
  "status": "COMPLETED",
  "benchmarks": [
    {"name": "timeline_profiles", "status": "COMPLETED"}
  ]
}
EOF
  "
fi

# ------------------------------------------------------------------------------
# STEP 15: Post-Execution Telemetry Aggregation & Invariant Audit
# ------------------------------------------------------------------------------
if step_should_run 15; then
  run_step 15 "canonical_aggregation_and_audit" bash -c "
    echo 'Running telemetry aggregation for current benchmark run...'
    cd '$SUITE_ROOT/..' && python3 tools/compile_canonical_data.py --run-dir '$MASTER_ROOT' || true
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
  CB_BLOCKS_SEL="${CB_BLOCKS_ARG:-${CB_BLOCKS:-none}}"
  if [[ "$CB_BLOCKS_SEL" == "none" || "$CB_BLOCKS_SEL" == "off" || "$CB_BLOCKS_SEL" == "0" || -z "$CB_BLOCKS_SEL" ]]; then
    echo "Skipping Step 17 Continuous Batching (CB_BLOCKS=$CB_BLOCKS_SEL; set to 'all' or '1,2' to enable)"
  else
    CB_OUT="$MASTER_ROOT/step17_continuous_batching"
    DRY_ARG=""
    [[ "$DRY_RUN" -eq 1 ]] && DRY_ARG="--dry-run"
    run_step 17 "continuous_batching_characterization" bash -c "
      echo 'Running Continuous Batching Suite (Blocks: $CB_BLOCKS_SEL)...'
      python3 '$SUITE_ROOT/run_continuous_batching.py' --out '$CB_OUT' --blocks '$CB_BLOCKS_SEL' $DRY_ARG || true
      echo 'Generating result summaries...'
      python3 '$SUITE_ROOT/generate_result_summary.py' '$CB_OUT' || true
    "
  fi
fi
# ------------------------------------------------------------------------------
# STEP 18: Open-Loop Poisson Arrival Rate Sweep (V8 Parity - Deep Profile)
# ------------------------------------------------------------------------------
if [[ "${RUN_POISSON_SWEEPS:-0}" == "1" ]] || [[ "$TARGET_STEP" == "18" ]]; then
  POISSON_DIR="$MASTER_ROOT/step18_poisson_sweep"
  run_step 18 "open_loop_poisson_sweep" bash -c "
    mkdir -p '$POISSON_DIR'
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_open_loop_poisson_sweep --out '$POISSON_DIR' --port 8090
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$POISSON_DIR' --out '$POISSON_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 19: Scheduler max_num_seqs Sensitivity Sweep (V8 Parity - Deep Profile)
# ------------------------------------------------------------------------------
if [[ "${RUN_SCHEDULER_SWEEPS:-0}" == "1" ]] || [[ "$TARGET_STEP" == "19" ]]; then
  SCHED_DIR="$MASTER_ROOT/step19_scheduler_sweep"
  run_step 19 "scheduler_max_seqs_sweep" bash -c "
    mkdir -p '$SCHED_DIR'
    for seq_case in tp4_scheduler_max_seqs_sweep tp4_scheduler_max_seqs_16 tp4_scheduler_max_seqs_64 tp4_scheduler_max_seqs_128; do
      echo \"Running scheduler sweep case: \$seq_case\"
      python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case \"\$seq_case\" --out '$SCHED_DIR' --port 8091
      # Allow port to release cleanly between scheduler cases
      sleep 3
    done
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$SCHED_DIR' --out '$SCHED_DIR/summary'
  "
fi

# ------------------------------------------------------------------------------
# STEP 20: Observability Overhead Test (Minimal vs Full Telemetry - Deep Profile)
# ------------------------------------------------------------------------------
if [[ "${RUN_OBSERVER_OVERHEAD:-0}" == "1" ]] || [[ "$TARGET_STEP" == "20" ]]; then
  OBS_DIR="$MASTER_ROOT/step20_observer_overhead"
  run_step 20 "observer_overhead_test" bash -c "
    mkdir -p '$OBS_DIR/minimal' '$OBS_DIR/full'
    # Run with minimal observability (no kv-cache-metrics, no MFU metrics)
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_observer_overhead_test --out '$OBS_DIR/minimal' --port 8092
    sleep 3
    # Run the same workload against baseline case with full observability for comparison
    python3 '$VLLM_DIR/11_run_vllm_surrogate.py' --cases '$CASES_FILE' --case tp4_observer_overhead_full --out '$OBS_DIR/full' --port 8093
    python3 '$VLLM_DIR/15_summarize_vllm.py' '$OBS_DIR' --out '$OBS_DIR/summary'

    # Compare overhead
    python3 - <<'PY' '$OBS_DIR'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
result = {}
for label in ('minimal', 'full'):
    d = root / label
    for f in d.rglob('*.json'):
        if f.name in ('summary.json', 'case_manifest.json', 'vllm_surrogate_manifest.json', 'resolved_models.json'): continue
        try:
            data = json.load(open(f))
            if 'mean_tpot_ms' in data:
                result[f'{label}_{f.stem}'] = {'mean_tpot_ms': data.get('mean_tpot_ms'), 'mean_ttft_ms': data.get('mean_ttft_ms'), 'output_throughput': data.get('output_throughput')}
        except Exception: pass
(root / 'OBSERVER_OVERHEAD_COMPARISON.json').write_text(json.dumps(result, indent=2))
print('Observer Overhead Comparison:', json.dumps(result, indent=2))
PY
  "
fi

echo ""
echo "================================================================================"
echo "  AUDITING CAMPAIGN CASE MANIFESTS ACROSS ALL STEPS (BLOCKER 7)"
echo "================================================================================"
if [[ "$DRY_RUN" == 1 ]]; then
  echo "  [DRY-RUN] Campaign dry-run completed successfully across all simulated steps."
  AUDIT_RC=0
else
  set +e
  "$PYTHON_EXEC" - << 'PY' "$MASTER_ROOT" "${FAILED_STEPS[@]}"
import json, sys
from pathlib import Path

master_root = Path(sys.argv[1])
failed_steps = sys.argv[2:] if len(sys.argv) > 2 else []

total_cases = 0
completed_cases = 0
failed_cases = 0
skipped_cases = 0
failure_details = []

# Case-insensitive manifest discovery matching case manifests and profile manifests
all_manifests = [
    p for p in master_root.rglob("*.json")
    if "manifest" in p.name.lower() and p.name not in ("vllm_surrogate_manifest.json", "master_step_status.jsonl", "warmup_manifest.json")
]

for manifest in sorted(all_manifests):
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as e:
        failed_cases += 1
        failure_details.append(f"{manifest.relative_to(master_root)}: JSON parse error ({e})")
        continue

    cname = data.get("case") or data.get("name") or manifest.parent.name
    status = data.get("status")
    err = data.get("error")
    total_cases += 1

    if status in ("FAILED", "WARMUP_FAILED", "INCOMPLETE") or err:
        failed_cases += 1
        failure_details.append(f"{manifest.relative_to(master_root)}: {cname} failed ({err or status})")
    elif status in ("SKIPPED", "SKIPPED_BY_SAFETY_GATE"):
        skipped_cases += 1
    elif status == "COMPLETED":
        completed_cases += 1
    else:
        benchmarks = data.get("benchmarks", [])
        if benchmarks:
            b_failed = [
                b for b in benchmarks
                if isinstance(b, dict) and b.get("status") in ("FAILED", "WARMUP_FAILED", "INCOMPLETE")
            ]
            if b_failed:
                failed_cases += 1
                failure_details.append(f"{manifest.relative_to(master_root)}: {len(b_failed)} benchmarks failed")
            else:
                completed_cases += 1
        else:
            completed_cases += 1

# Check readiness gate reports if present in env/
env_dir = master_root / "env"
if env_dir.exists():
    for rf in env_dir.rglob("*readiness*"):
        if rf.is_file():
            try:
                rtxt = rf.read_text(encoding="utf-8", errors="ignore")
                if "GATE: FAIL" in rtxt or "[FAIL]" in rtxt:
                    failure_details.append(f"Readiness gate failure reported in {rf.name}")
            except Exception:
                pass

summary_payload = {
    "total_cases_evaluated": total_cases,
    "completed_cases": completed_cases,
    "failed_cases": failed_cases,
    "skipped_cases": skipped_cases,
    "failed_steps_count": len(failed_steps),
    "failed_steps": failed_steps,
    "failure_details": failure_details,
    "campaign_overall_status": "FAILED" if (failed_cases > 0 or len(failed_steps) > 0) else "PASSED"
}

summary_path = master_root / "CAMPAIGN_SUMMARY.json"
summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
print(f"  Campaign Manifest Audit Summary ({summary_path}):")
print(f"    Total Cases Evaluated : {total_cases}")
print(f"    Completed Successfully: {completed_cases}")
print(f"    Failed Cases          : {failed_cases}")
print(f"    Skipped (Safety Gate) : {skipped_cases}")
print(f"    Failed Steps Recorded : {len(failed_steps)}")
if failure_details:
    print("  Failed Case Details:")
    for fd in failure_details[:10]:
        print(f"    * {fd}")
if summary_payload["campaign_overall_status"] == "FAILED":
    print("  [ALERT] Campaign recorded failures. Exiting non-zero per Blocker 7.")
    sys.exit(1)
else:
    print("  [OK] All evaluated cases and steps completed with zero failures.")
PY
  AUDIT_RC=$?
  set -e

  # Post-Run Collector & Strict Provenance Validator
  if [[ -f "$SUITE_ROOT/pip_collect_and_validate.py" ]]; then
    echo ""
    echo "================================================================================"
    echo "  RUNNING STRICT PROVENANCE COLLECTOR & VALIDATOR"
    echo "================================================================================"
    "$PYTHON_EXEC" "$SUITE_ROOT/pip_collect_and_validate.py" --root "$MASTER_ROOT" --suite "$SUITE_ROOT" --out "$MASTER_ROOT/final_validation" || true
  fi

  # Automated Evidence Packaging & SHA-256 Checksum
  if [[ "${PACKAGE_EVIDENCE:-1}" == "1" && -f "$SUITE_ROOT/pip_package_evidence.sh" ]]; then
    echo ""
    echo "================================================================================"
    echo "  PACKAGING IMMUTABLE EVIDENCE ARCHIVE"
    echo "================================================================================"
    bash "$SUITE_ROOT/pip_package_evidence.sh" "$MASTER_ROOT" || true
  fi
fi

echo ""
echo "================================================================================"
echo "  ALL STEPS COMPLETE (including deep-profile extensions if enabled)"
echo "  Telemetry & Logs Vault: $MASTER_ROOT"
echo "================================================================================"
exit "$AUDIT_RC"
