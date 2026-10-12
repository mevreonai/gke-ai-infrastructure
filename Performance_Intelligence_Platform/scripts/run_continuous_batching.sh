#!/usr/bin/env bash
# ==============================================================================
# RUN CONTINUOUS BATCHING BENCHMARKS (TASK 2)
# ==============================================================================
# Orchestrates configurable continuous batching sweeps across Blocks 1-7:
#   Block 1: Two long prompts at once (Chunk cap vs big step)
#   Block 2: Step budget sweep (4K, 8K, 16K, 32K)
#   Block 3: Request cap binding (16, 32, 64)
#   Block 4: Mixed traffic concurrent streams (short + long)
#   Block 5: Memory pressure under load (KV limit)
#   Block 6: Long answers (1024, 2048 decode steps)
#   Block 7: Steady arrivals (Poisson / fixed-rate on two servers)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/RUN_CONFIG.env"
if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

: "${VENV_DIR:=$HOME/vllm_env}"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "$VENV_DIR/bin/activate"
fi

RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
OUT_ROOT="${OUT_ROOT:-$HOME/platform_benchmark_runs/$RUN_ID/continuous_batching}"
BLOCKS="${CB_BLOCKS:-all}"
DRY_RUN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --blocks)
      BLOCKS="$2"
      shift 2
      ;;
    --block)
      BLOCKS="$2"
      shift 2
      ;;
    --out-root|--out)
      OUT_ROOT="$2"
      shift 2
      ;;
    --model)
      export MODEL="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="--dry-run"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo "  --blocks <1,2...>   Select continuous batching blocks (1-7 or all, default: all)"
      echo "  --block <N>         Select single block"
      echo "  --out-root <dir>    Output directory"
      echo "  --model <id>        Target model override"
      echo "  --dry-run           Plan cases without launching server or GPUs"
      exit 0
      ;;
    *)
      shift
      ;;
  esac
done

# Resolve python binary
PYTHON_BIN=""
for candidate in python3 python py /c/Python314/python.exe /usr/bin/python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    ver=$("$candidate" --version 2>&1 || true)
    if [[ "$ver" == *"Python 3"* ]]; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done
[[ -n "$PYTHON_BIN" ]] || PYTHON_BIN="python3"

echo "================================================================================"
echo "  LAUNCHING CONTINUOUS BATCHING SWEEP"
echo "  Blocks Target : $BLOCKS"
echo "  Output Vault  : $OUT_ROOT"
echo "  Dry Run       : ${DRY_RUN:-false}"
echo "================================================================================"

mkdir -p "$OUT_ROOT"
"$PYTHON_BIN" "$SCRIPT_DIR/run_continuous_batching.py" \
  --out "$OUT_ROOT" \
  --blocks "$BLOCKS" \
  $DRY_RUN

echo ""
echo "Generating result summaries..."
"$PYTHON_BIN" "$SCRIPT_DIR/generate_result_summary.py" "$OUT_ROOT" || true

echo ""
echo "================================================================================"
echo "  CONTINUOUS BATCHING COMPLETE"
echo "  Results   : $OUT_ROOT"
echo "  Summary   : $OUT_ROOT/RESULT_SUMMARY.md"
echo "================================================================================"

