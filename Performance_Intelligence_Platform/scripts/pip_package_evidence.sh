#!/usr/bin/env bash
# ==============================================================================
# PERFORMANCE INTELLIGENCE PLATFORM — AUTOMATED EVIDENCE PACKAGER
# ==============================================================================
# Generates an immutable file inventory (FILE_LIST.tsv), packages all benchmark
# manifests, profile traces, SQLite telemetry, and logs into a verified archive,
# and generates a SHA-256 checksum file for tamper-proof provenance.
#
# Usage:
#   bash pip_package_evidence.sh [RESULT_ROOT] [OUTPUT_DIR]
# ==============================================================================
set -euo pipefail

: "${PIP_DATA_ROOT:=$HOME/PIP_Benchmark_Data}"

TARGET_ROOT="${1:-${RESULT_ROOT:-${MASTER_ROOT:-}}}"
if [[ -z "$TARGET_ROOT" ]]; then
  if [[ -f "$PIP_DATA_ROOT/latest_run_id.txt" ]]; then
    LATEST_ID=$(cat "$PIP_DATA_ROOT/latest_run_id.txt")
    TARGET_ROOT="$PIP_DATA_ROOT/runs/$LATEST_ID"
  fi
fi

if [[ -z "$TARGET_ROOT" || ! -d "$TARGET_ROOT" ]]; then
  echo "Usage: pip_package_evidence.sh <RESULT_ROOT_DIR> [OUTPUT_DIR]"
  echo "Error: Directory '$TARGET_ROOT' does not exist."
  exit 1
fi

TARGET_ROOT=$(cd "$TARGET_ROOT" && pwd)
PARENT_DIR=$(dirname "$TARGET_ROOT")
BASE_NAME=$(basename "$TARGET_ROOT")
OUT_DIR="${2:-$PARENT_DIR}"
mkdir -p "$OUT_DIR"
ARCHIVE_PATH="$OUT_DIR/${BASE_NAME}_EVIDENCE.tar.gz"
CHECKSUM_PATH="${ARCHIVE_PATH}.sha256"

echo "================================================================================"
echo "  PERFORMANCE INTELLIGENCE PLATFORM — EVIDENCE PACKAGER"
echo "  Target Root : $TARGET_ROOT"
echo "  Archive Out : $ARCHIVE_PATH"
echo "================================================================================"

mkdir -p "$TARGET_ROOT/final_validation"

# Generate immutable inventory before packaging
echo "[1/3] Generating file inventory manifest..."
if command -v find >/dev/null 2>&1; then
  (cd "$TARGET_ROOT" && find . -type f -exec ls -la {} + 2>/dev/null | awk '{print $5 "\t" $9}' | sort) > "$TARGET_ROOT/final_validation/FILE_LIST.tsv" || true
fi

# Package archive
echo "[2/3] Compressing benchmark results into tar.gz..."
tar -C "$PARENT_DIR" -czf "$ARCHIVE_PATH" "$BASE_NAME"

# Compute checksum
echo "[3/3] Generating SHA-256 checksum..."
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$ARCHIVE_PATH" > "$CHECKSUM_PATH"
elif command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "$ARCHIVE_PATH" > "$CHECKSUM_PATH"
else
  # Python fallback
  python3 -c "import hashlib, sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest() + '  ' + sys.argv[1])" "$ARCHIVE_PATH" > "$CHECKSUM_PATH"
fi

echo ""
echo "[+] SUCCESS: Archive and provenance checksum created:"
echo "    Archive  : $ARCHIVE_PATH"
echo "    Checksum : $CHECKSUM_PATH"
if [[ -f "$CHECKSUM_PATH" ]]; then
  cat "$CHECKSUM_PATH"
fi
