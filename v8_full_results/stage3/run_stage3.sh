#!/usr/bin/env bash
# ==============================================================================
# Stage 3 Launcher — Direct Execution Entrypoint
# ==============================================================================
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SUITE_DIR="$SCRIPT_DIR/../suite"

echo "===================================================================="
echo "          V8 BENCHMARK SUITE — STAGE 3 RUNNER"
echo "===================================================================="

cd "$SUITE_DIR"
exec bash ./03_run_stage3_expansion_and_profiling.sh "$@"
