#!/usr/bin/env bash
# ==============================================================================
# Master Orchestrator: V8 Additional Characterization Runs (Stage 1 & Stage 2)
# ==============================================================================
# Fully updated per Code Review v1.4.
# ==============================================================================
set -euo pipefail

SUITE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${V8_RUN_STAGE1:=1}"
: "${V8_RUN_STAGE2:=1}"
: "${V8_RUN_STAGE3:=1}"
: "${RESUME:=1}"

RUN_ID_FILE="$HOME/v8_additional_runs/latest_run_id.txt"
if [[ "$RESUME" == 1 && -f "$RUN_ID_FILE" && -z "${RUN_ID:-}" ]]; then
  DEFAULT_RUN_ID=$(cat "$RUN_ID_FILE")
else
  DEFAULT_RUN_ID=$(date +%Y%m%d_%H%M%S)
fi
: "${RUN_ID:=$DEFAULT_RUN_ID}"
: "${MASTER_ROOT:=$HOME/v8_additional_runs/$RUN_ID}"

# Command line flag parsing
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stage1-only)
      V8_RUN_STAGE1=1
      V8_RUN_STAGE2=0
      V8_RUN_STAGE3=0
      shift
      ;;
    --stage2-only)
      V8_RUN_STAGE1=0
      V8_RUN_STAGE2=1
      V8_RUN_STAGE3=0
      shift
      ;;
    --stage3-only)
      V8_RUN_STAGE1=0
      V8_RUN_STAGE2=0
      V8_RUN_STAGE3=1
      shift
      ;;
    --all)
      V8_RUN_STAGE1=1
      V8_RUN_STAGE2=1
      V8_RUN_STAGE3=1
      shift
      ;;
    --run-id)
      RUN_ID="$2"
      MASTER_ROOT="$HOME/v8_additional_runs/$RUN_ID"
      shift 2
      ;;
    --out-root)
      MASTER_ROOT="$2"
      shift 2
      ;;
    --new-run)
      RUN_ID=$(date +%Y%m%d_%H%M%S)
      MASTER_ROOT="$HOME/v8_additional_runs/$RUN_ID"
      RESUME=0
      shift
      ;;
    --no-resume)
      RESUME=0
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: $0 [--stage1-only | --stage2-only | --all] [--new-run] [--run-id <id>] [--out-root <path>]"
      exit 1
      ;;
  esac
done

mkdir -p "$MASTER_ROOT" "$MASTER_ROOT/logs" "$MASTER_ROOT/.done" "$HOME/v8_additional_runs"
echo "$RUN_ID" > "$RUN_ID_FILE"
MASTER_LOG="$MASTER_ROOT/logs/ADDITIONAL_RUNS_MASTER.log"
exec > >(tee -a "$MASTER_LOG") 2>&1

echo "================================================================================"
echo "  V8 ADDITIONAL RUNS SUITE — MASTER EXECUTION"
echo "  Run ID       : $RUN_ID"
echo "  Output Root  : $MASTER_ROOT"
echo "  Suite Root   : $SUITE_ROOT"
echo "  Run Stage 1  : $V8_RUN_STAGE1 (~2.0 hours)"
echo "  Run Stage 2  : $V8_RUN_STAGE2 (~3.5 hours)"
echo "  Run Stage 3  : $V8_RUN_STAGE3 (~10.4 hours wall-clock / 13.5 machine hours)"
echo "================================================================================"

# Discover GCP configuration if present
if [[ -f "$PWD/RUN_CONFIG.env" ]]; then source "$PWD/RUN_CONFIG.env"
elif [[ -f "$SUITE_ROOT/RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/RUN_CONFIG.env"
elif [[ -f "$HOME/rtx_g4_smoke/RUN_CONFIG.env" ]]; then source "$HOME/rtx_g4_smoke/RUN_CONFIG.env"
fi
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"

step(){
  local name="$1"; shift
  local marker="$MASTER_ROOT/.done/$name"
  if [[ "$RESUME" == 1 && -f "$marker" ]]; then
    echo; echo "================ MASTER STEP: $name (RESUME SKIP) ================"
    return 0
  fi
  echo; echo "================ MASTER STEP: $name ================"
  local s rc e
  s=$(date +%s)
  set +e
  "$@"
  rc=$?
  set -e
  e=$(date +%s)
  printf '{"step":"%s","rc":%s,"start":%s,"end":%s}\n' "$name" "$rc" "$s" "$e" >> "$MASTER_ROOT/master_step_status.jsonl"
  [[ "$rc" == 0 ]] && touch "$marker"
  return "$rc"
}

# 1. Generate Suite Source Checksum Manifest
step suite_hash_manifest bash -c "
  find '$SUITE_ROOT' -type f \( -name '*.sh' -o -name '*.py' -o -name '*.json' \) -not -path '*/.*' -exec sha256sum {} + | sort -k2 > '$MASTER_ROOT/SUITE_SOURCE_SHA256SUMS.txt'
  echo 'Suite SHA256 checksums recorded.'
"

# 2. Dual-Node Environment Snapshot
step dual_node_env_snapshot bash -c "
  mkdir -p '$MASTER_ROOT/env'
  # Node 0 Snapshot
  python3 -c 'import sys, platform, torch, vllm; print(\"Python:\", sys.version); print(\"PyTorch:\", torch.__version__); print(\"CUDA:\", torch.version.cuda); print(\"vLLM:\", vllm.__version__)' > '$MASTER_ROOT/env/node0_python_stack.txt' 2>&1 || true
  nvidia-smi > '$MASTER_ROOT/env/node0_nvidia_smi.txt' 2>&1 || true
  env | grep -E '^(CUDA_|NCCL_|VLLM_|RAY_|NODE)' | sort > '$MASTER_ROOT/env/node0_runtime_env.txt' || true

  # Node 1 Snapshot
  if [[ -n \"\${NODE1_IP:-}\" ]]; then
    ssh -i '$SSH_KEY' -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"
      python3 -c 'import sys, platform, torch, vllm; print(\\\"Python:\\\", sys.version); print(\\\"PyTorch:\\\", torch.__version__); print(\\\"CUDA:\\\", torch.version.cuda); print(\\\"vLLM:\\\", vllm.__version__)'
    \" > '$MASTER_ROOT/env/node1_python_stack.txt' 2>&1 || true
    ssh -i '$SSH_KEY' -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"nvidia-smi\" > '$MASTER_ROOT/env/node1_nvidia_smi.txt' 2>&1 || true
    ssh -i '$SSH_KEY' -o BatchMode=yes -o StrictHostKeyChecking=no \"\$NODE1_IP\" \"env | grep -E '^(CUDA_|NCCL_|VLLM_|RAY_|NODE)' | sort\" > '$MASTER_ROOT/env/node1_runtime_env.txt' || true
  fi
"

# 3. Execute Stage 1 (Quick Wins & Diagnostics)
if [[ "$V8_RUN_STAGE1" == 1 ]]; then
  step run_stage1 env RUN_ID="$RUN_ID" STAGE1_ROOT="$MASTER_ROOT/stage1" STAGE1_RESUME="$RESUME" \
    "$SUITE_ROOT/01_run_stage1_quick_wins.sh"
fi

# 4. Execute Stage 2 (Failed Reruns & Scale-Out)
if [[ "$V8_RUN_STAGE2" == 1 ]]; then
  step run_stage2 env RUN_ID="$RUN_ID" STAGE2_ROOT="$MASTER_ROOT/stage2" STAGE2_RESUME="$RESUME" \
    "$SUITE_ROOT/02_run_stage2_failed_and_scaleout.sh"
fi

# 5. Execute Stage 3 (Strategic Expansions, True Serving Profiles & Resilience)
if [[ "$V8_RUN_STAGE3" == 1 ]]; then
  step run_stage3 env RUN_ID="$RUN_ID" STAGE3_ROOT="$MASTER_ROOT/stage3" STAGE3_RESUME="$RESUME" \
    "$SUITE_ROOT/03_run_stage3_expansion_and_profiling.sh"
fi

echo ""
echo "================================================================================"
echo "  ALL ADDITIONAL RUNS SUCCESSFULLY COMPLETED!"
echo "  Results Directory: $MASTER_ROOT"
echo "  Historical V8 results remain untouched in their original archives."
echo "================================================================================"
