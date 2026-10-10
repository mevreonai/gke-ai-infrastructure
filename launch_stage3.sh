#!/usr/bin/env bash

echo "=========================================================="
echo "APPLYING SUITE UPDATE & VERIFYING SYNTAX"
echo "=========================================================="
tar -xzf /home/ayu23/suite_update.tar.gz -C /home/ayu23/v8_additional_runs_suite/
chmod -R +x /home/ayu23/v8_additional_runs_suite

# Syntax verification across all scripts
for s in /home/ayu23/v8_additional_runs_suite/*.sh /home/ayu23/v8_additional_runs_suite/rtx_g4_smoke_v5/*.sh; do
  bash -n "$s" || { echo "SYNTAX ERROR in $s"; exit 1; }
done
echo "All shell scripts passed bash -n syntax validation."

# Sync to node 1
scp -o StrictHostKeyChecking=no /home/ayu23/suite_update.tar.gz 10.128.0.40:~/
ssh -o StrictHostKeyChecking=no 10.128.0.40 "tar -xzf ~/suite_update.tar.gz -C ~/v8_additional_runs_suite/ && chmod -R +x ~/v8_additional_runs_suite"

# Clean up dangling processes on both nodes
echo "Cleaning lingering GPU processes..."
pkill -9 -f "vllm" 2>/dev/null || true
pkill -9 -f "nsys" 2>/dev/null || true
pkill -9 -f "ray" 2>/dev/null || true
ssh -o StrictHostKeyChecking=no 10.128.0.40 "pkill -9 -f 'vllm' 2>/dev/null || true; pkill -9 -f 'ray' 2>/dev/null || true" 2>/dev/null || true
sleep 2

# Reset any tc qdisc
sudo -n tc qdisc del dev ens3 root 2>/dev/null || true
ssh -o StrictHostKeyChecking=no 10.128.0.40 "sudo -n tc qdisc del dev ens3 root 2>/dev/null || true" 2>/dev/null || true

# Kill old tmux
tmux kill-server 2>/dev/null || true
sleep 1

# Launch Stage 3 with --new-run (RESUME=0: guarantees NO steps skipped!)
echo "Starting detached tmux session v8_stage3 with --new-run --stage3-only..."
tmux new-session -d -s v8_stage3 'cd /home/ayu23/v8_additional_runs_suite && bash ./run_quickstart.sh --new-run --stage3-only > /home/ayu23/v8_stage3_execution.log 2>&1'

sleep 12

echo "=========================================================="
echo "TMUX STATUS:"
tmux ls 2>/dev/null || true
echo "=========================================================="
echo "RUNNING PROCESS TREE:"
ps aux | grep -E 'run_quickstart|00_run_master|03_run_stage3|nsys|vllm|python' | grep -v grep || true
echo "=========================================================="
echo "LOG FILE HEAD / TAIL:"
cat /home/ayu23/v8_stage3_execution.log | tail -n 35 2>/dev/null || true
echo "=========================================================="
