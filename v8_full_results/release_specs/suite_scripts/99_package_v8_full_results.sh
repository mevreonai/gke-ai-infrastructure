#!/usr/bin/env bash
set -euo pipefail
ROOT=${1:?Usage: 99_package_v8_full_results.sh RESULT_ROOT}
ROOT=$(readlink -f "$ROOT")
PARENT=$(dirname "$ROOT"); BASE=$(basename "$ROOT")
OUT="$PARENT/${BASE}_FULL_EVIDENCE.tar.gz"
mkdir -p "$ROOT/final_validation"
# Generate the file inventory before tar creation so the inventory itself is part
# of the immutable evidence archive.
find "$ROOT" -type f -printf '%P\t%s\n' | sort > "$ROOT/final_validation/FILE_LIST.tsv"
echo "Packaging V8-FULL raw + processed + profiler evidence: $OUT"
tar -C "$PARENT" -czf "$OUT" "$BASE"
sha256sum "$OUT" > "$OUT.sha256"
echo "Archive: $OUT"
echo "Checksum: $OUT.sha256"
