#!/usr/bin/env bash
# ==============================================================================
# DEMO STEP 8: Run the Complete Master Benchmark Suite on the Cluster
# ==============================================================================
# Executes the unified 15-step systems characterization campaign or targeted steps.
# Usage:
#   Full 15-Step Suite : ./08_run_full_master_benchmark.sh --all
#   Targeted Step 1    : ./08_run_full_master_benchmark.sh --step 1
#   From Step N        : ./08_run_full_master_benchmark.sh --from-step 1
# ==============================================================================
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
MASTER_RUNNER="$REPO_ROOT/scripts/run_master_benchmark.sh"

export VENV_DIR="$HOME/vllm_env"
export BENCH_ROOT="$HOME/rtx_g4_smoke"
export PATH="$VENV_DIR/bin:$PATH"

# Discover Internal IPs
NODE0_INTERNAL_IP=$(hostname -I | awk '{print $1}')
echo "======================================================================"
echo " [DEMO] Initializing Unified Master Benchmark Suite"
echo "======================================================================"
echo " Primary Node 0 IP : $NODE0_INTERNAL_IP"
echo " Execution Script   : $MASTER_RUNNER"
echo " Target Mode        : ${*:-'--step 1 (Fast Demo Step)'}"
echo "======================================================================"

# If no argument is passed, default to --step 1 for live demo pacing
ARGS="${*:-"--step 1"}"

# Ensure scripts are executable
chmod +x "$REPO_ROOT"/scripts/*.sh 2>/dev/null || true

cd "$REPO_ROOT/scripts"
exec bash "$MASTER_RUNNER" $ARGS
