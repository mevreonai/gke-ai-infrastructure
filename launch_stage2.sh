#!/usr/bin/env bash
set -euo pipefail

cd /home/ayu23/v8_additional_runs_suite
nohup ./00_run_master_additional_runs.sh --stage2-only --run-id 20261005_210750 > /home/ayu23/stage2_nohup.log 2>&1 &
PID=$!
echo "STAGE2_LAUNCHED_PID=$PID"
echo "$PID" > /home/ayu23/stage2.pid
sleep 2
ps -p "$PID" -o pid,stat,cmd
