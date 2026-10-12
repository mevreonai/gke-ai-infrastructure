#!/usr/bin/env bash
set -u

RUN_ID="20261005_210750"
STAGE2_ROOT="/home/ayu23/v8_additional_runs/$RUN_ID/stage2"
PID_FILE="/home/ayu23/stage2.pid"

echo "=== STAGE 2 PROCESS STATUS ==="
if [[ -f "$PID_FILE" ]]; then
  PID=$(cat "$PID_FILE")
  if ps -p "$PID" > /dev/null 2>&1; then
    echo "Process $PID is RUNNING"
    ps -p "$PID" -o pid,stat,etime,%cpu,%mem,cmd
  else
    echo "Process $PID is NOT RUNNING (Completed or Exited)"
  fi
else
  echo "PID file not found"
fi

echo ""
echo "=== COMPLETED STAGE 2 STEPS (.done) ==="
if [[ -d "$STAGE2_ROOT/.done" ]]; then
  ls -1 "$STAGE2_ROOT/.done"
else
  echo "No .done directory yet"
fi

echo ""
echo "=== STEP STATUS JSONL ==="
if [[ -f "$STAGE2_ROOT/step_status.jsonl" ]]; then
  cat "$STAGE2_ROOT/step_status.jsonl"
else
  echo "No step_status.jsonl yet"
fi

echo ""
echo "=== LAST 30 LINES OF NOHUP LOG ==="
if [[ -f /home/ayu23/stage2_nohup.log ]]; then
  tail -n 30 /home/ayu23/stage2_nohup.log
fi

echo ""
echo "=== LAST 30 LINES OF MASTER LOG ==="
if [[ -f "$STAGE2_ROOT/logs/STAGE2_MASTER.log" ]]; then
  tail -n 30 "$STAGE2_ROOT/logs/STAGE2_MASTER.log"
fi
