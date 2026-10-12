#!/usr/bin/env bash
# ==============================================================================
# run_all.sh — End-to-End Orchestrator
# DeepSeek V4.1 Flash Performance Characterization Suite
# Target: kimi-node-0 (8× RTX PRO 6000)
#
# This script runs the full benchmark pipeline:
#   1. Preflight environment checks
#   2. Launch vLLM server
#   3. Execute benchmarks across Native, 100Gbps, 20Gbps
#   4. Collect and summarize results
#   5. Shut down server
#
# Usage:
#   sudo ./run_all.sh              # Full run
#   sudo ./run_all.sh --dry-run    # Print commands without executing
#   sudo ./run_all.sh --skip-server  # Skip server start (already running)
# ==============================================================================
set -euo pipefail

BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"; CYAN="\033[36m"; RESET="\033[0m"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTAINER_NAME="vllm-deepseek-perf"

# ─── Parse Arguments ─────────────────────────────────────────────────────────
DRY_RUN=""
SKIP_SERVER=false
SKIP_SHUTDOWN=false

for arg in "$@"; do
    case "$arg" in
        --dry-run)     DRY_RUN="--dry-run" ;;
        --skip-server) SKIP_SERVER=true ;;
        --skip-shutdown) SKIP_SHUTDOWN=true ;;
        --help|-h)
            echo "Usage: sudo ./run_all.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run        Print benchmark commands without executing"
            echo "  --skip-server    Skip vLLM server launch (assume already running)"
            echo "  --skip-shutdown  Don't stop the vLLM container after benchmarks"
            echo "  --help, -h       Show this help"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            exit 1
            ;;
    esac
done

# ─── Banner ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║  DeepSeek V4.1 Flash — Performance Characterization Suite   ║${RESET}"
echo -e "${CYAN}${BOLD}║  Target: kimi-node-0 · 8× RTX PRO 6000 · TP8               ║${RESET}"
echo -e "${CYAN}${BOLD}║  Conditions: Native · 100Gbps · 20Gbps                      ║${RESET}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Start time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo -e "  Script dir: ${SCRIPT_DIR}"
[ -n "$DRY_RUN" ] && echo -e "  ${YELLOW}Mode: DRY RUN (no benchmarks will be executed)${RESET}"
echo ""

START_TIME=$(date +%s)

# ─── Step 1: Preflight ───────────────────────────────────────────────────────
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  STEP 1/4: Environment Preflight Checks${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

bash "${SCRIPT_DIR}/01_preflight.sh"
echo ""

# ─── Step 2: Start Server ────────────────────────────────────────────────────
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  STEP 2/4: vLLM Server${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

if [ "$SKIP_SERVER" = true ]; then
    echo -e "${YELLOW}⚠ Skipping server start (--skip-server)${RESET}"
    # Verify server is actually running
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/v1/models" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✔ Server is already running and responding${RESET}"
    else
        echo -e "${RED}✘ Server is not responding (HTTP: ${HTTP_CODE}). Remove --skip-server or start manually.${RESET}"
        exit 1
    fi
elif [ -n "$DRY_RUN" ]; then
    echo -e "${YELLOW}⚠ Dry run — skipping server start${RESET}"
else
    bash "${SCRIPT_DIR}/02_start_vllm_server.sh"
fi
echo ""

# ─── Step 3: Run Benchmarks ─────────────────────────────────────────────────
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  STEP 3/4: Running Benchmarks${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

python3 "${SCRIPT_DIR}/03_run_benchmarks.py" $DRY_RUN
echo ""

# ─── Step 4: Collect Results ─────────────────────────────────────────────────
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  STEP 4/4: Collecting Results${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

if [ -z "$DRY_RUN" ]; then
    python3 "${SCRIPT_DIR}/04_collect_results.py"
else
    echo -e "${YELLOW}⚠ Dry run — no results to collect${RESET}"
fi
echo ""

# ─── Cleanup ─────────────────────────────────────────────────────────────────
if [ "$SKIP_SHUTDOWN" = false ] && [ -z "$DRY_RUN" ]; then
    echo -e "${BOLD}Stopping vLLM server container...${RESET}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✔ Server stopped${RESET}"
else
    if [ "$SKIP_SHUTDOWN" = true ]; then
        echo -e "${YELLOW}ℹ Server left running (--skip-shutdown)${RESET}"
    fi
fi

# ─── Done ────────────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║  CHARACTERIZATION COMPLETE                                  ║${RESET}"
echo -e "${CYAN}${BOLD}║  Duration: ${MINUTES}m ${SECONDS}s                                          ║${RESET}"
echo -e "${CYAN}${BOLD}║  Results:  ${SCRIPT_DIR}/results/                      ║${RESET}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

if [ -z "$DRY_RUN" ]; then
    echo -e "  ${GREEN}✔${RESET} summary.csv       — Raw metrics table"
    echo -e "  ${GREEN}✔${RESET} SUMMARY.md         — Markdown report"
    echo -e "  ${GREEN}✔${RESET} comparison.json    — Cross-condition deltas"
    echo ""
    echo -e "  To re-generate summaries: python3 04_collect_results.py"
fi
echo ""
