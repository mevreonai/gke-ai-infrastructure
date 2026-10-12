#!/usr/bin/env bash
# audit/check_pip_compliance.sh: Executive PIP Scripts Verification Runner
# Runs the full affirmative audit suite and coverage matrix verification.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PIP_DIR="$REPO_ROOT/Performance_Intelligence_Platform"

echo "================================================================================"
echo "  PERFORMANCE INTELLIGENCE PLATFORM — EXECUTIVE AUDIT RUNNER"
echo "  Auditing PIP Scripts against Scripts_Review_v1.3.md"
echo "  Repository Root : $REPO_ROOT"
echo "  Platform Dir    : $PIP_DIR"
echo "================================================================================"

PYTHON_BIN=""
for candidate in python3 python py /usr/bin/python3 /c/Python314/python.exe; do
  if command -v "$candidate" >/dev/null 2>&1; then
    ver=$("$candidate" --version 2>&1 || true)
    if [[ "$ver" == *"Python 3"* ]]; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "ERROR: Python 3 runtime not found." >&2
  exit 1
fi

echo "Using Python binary: $PYTHON_BIN ($("$PYTHON_BIN" --version))"
echo ""

# 1. Run Coverage Matrix Audit
echo "--> [1/2] Generating Section 6 Coverage Matrix and Context Limits Audit..."
"$PYTHON_BIN" "$SCRIPT_DIR/coverage_matrix.py" "$PIP_DIR"

echo ""
# 2. Run Comprehensive Affirmative Audit Suite
echo "--> [2/2] Running Affirmative Audit Verification Suite (Blockers 1-13 & Invariants)..."
"$PYTHON_BIN" "$SCRIPT_DIR/verify_all_scripts_fixes.py" "$PIP_DIR"

echo ""
echo "================================================================================"
echo "  EXECUTIVE AUDIT COMPLETE: 100% OF PIP CHECKS PASSED"
echo "  All 13 blockers, Section 4 invariants, Section 5 autotune syntax,"
echo "  and Section 6 coverage extensions are fully verified and hardened."
echo "================================================================================"
