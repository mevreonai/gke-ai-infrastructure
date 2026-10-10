#!/usr/bin/env bash
set -uo pipefail

echo "========================================================================"
echo "  V8 MASTER CAMPAIGN — STAGE 2 RESUME EXECUTION"
echo "  Start Time : $(date)"
echo "========================================================================"

# 1. Reset network disciplines
sudo tc qdisc del dev ens3 root 2>/dev/null || true
sudo tc qdisc del dev ens3 ingress 2>/dev/null || true
ssh -o StrictHostKeyChecking=no 10.128.0.40 "sudo tc qdisc del dev ens3 root 2>/dev/null || true; sudo tc qdisc del dev ens3 ingress 2>/dev/null || true" 2>/dev/null || true

# 2. Cleanup leftover Ray / vLLM
pkill -9 -f "VLLM::Worker" 2>/dev/null || true
pkill -9 -f "vllm serve" 2>/dev/null || true
ray stop -f 2>/dev/null || true
ssh -o StrictHostKeyChecking=no 10.128.0.40 "pkill -9 -f 'VLLM::Worker' 2>/dev/null || true; pkill -9 -f 'vllm serve' 2>/dev/null || true; ray stop -f 2>/dev/null || true" 2>/dev/null || true

# 3. Clean incomplete s2_03 dir if partial
rm -rf /home/ayu23/v8_additional_runs/20261009_104123/stage2/03_multi_node_load/* 2>/dev/null || true

# 4. Resume Stage 2
SUITE_ROOT="/home/ayu23/v8_additional_runs_suite"
RUN_ID="20261009_104123"
cd "$SUITE_ROOT"

STAGE2_RESUME=1 RUN_ID="$RUN_ID" bash ./02_run_stage2_failed_and_scaleout.sh >> /home/ayu23/v8_stage2_execution.log 2>&1
STAGE2_RC=$?

echo "========================================================================"
echo "  STAGE 2 RESUME FINISHED with RC=$STAGE2_RC at $(date)"
echo "========================================================================"
exit $STAGE2_RC
