#!/usr/bin/env bash
# Package one RUN_ID result tree plus generated summaries.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${BENCH_ROOT:=$HOME/rtx_g4_smoke}"
: "${RUN_ID:?Set RUN_ID to the run being packaged}"

OUT="$BENCH_ROOT/rtx_g4_smoke_${RUN_ID}.tgz"
cd "$BENCH_ROOT"
tar -czf "$OUT" "results/$RUN_ID"
echo "Created: $OUT"
ls -lh "$OUT"
sha256sum "$OUT"
