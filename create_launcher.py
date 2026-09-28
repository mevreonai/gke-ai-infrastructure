import base64
import subprocess

script = """#!/usr/bin/env bash
set -uo pipefail

ln -sf /home/ayu23/.ssh/id_ed25519 /home/ayu23/.ssh/id_rsa

cd /home/ayu23/V9_FULL
source /home/ayu23/vllm_env/bin/activate
export PATH=/home/ayu23/vllm_env/bin:/home/ayu23/.local/bin:/home/ayu23/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin

LOG="/home/ayu23/v9_test2_execution.log"
echo "=== Starting V9 Test 2 Run (Native + 20G, No Profilers) at $(date) ===" > "$LOG"

export RUN_HW_PREP=0
export RUN_NODE_LOCAL_HW=1
export RUN_NETWORK_SMOKE=1
export RUN_SINGLE_NODE=1
export RUN_OPEN_LOOP=1
export RUN_SCALEOUT=1
export RUN_PROFILES=0
export RUN_HEAVY_PROFILE=0
export RUN_TARGETED_CAPPED_DECODE_PROFILE=0

RUN_ID="v9_test2_$(date +%Y%m%d_%H%M%S)"
export V9FULL_RUN_ID="$RUN_ID"
RESULT_ROOT="/home/ayu23/v9_full_results/$RUN_ID"
export V9FULL_ROOT="$RESULT_ROOT"

./00_run_v9_full.sh configs/models/kimi_linear_48b.json configs/clusters/kimi_2x8.json configs/suite_native_20g.json >> "$LOG" 2>&1
RUN_RC=$?

echo "=== V9 Execution finished with rc=$RUN_RC at $(date) ===" >> "$LOG"

echo "=== Packaging final results ===" >> "$LOG"
if [ -d "$RESULT_ROOT" ]; then
    ./99_package_v9_full_results.sh "$RESULT_ROOT" >> "$LOG" 2>&1 || true
    tar -czf "/home/ayu23/V9_TEST2_RESULTS_${RUN_ID}.tar.gz" -C "/home/ayu23/v9_full_results" "$RUN_ID" >> "$LOG" 2>&1 || true
    echo "SUCCESS: Results archived to /home/ayu23/V9_TEST2_RESULTS_${RUN_ID}.tar.gz" >> "$LOG"
fi

echo "=== Syncing filesystem ===" >> "$LOG"
sync

echo "=== Auto-terminating VMs to stop GCP billing ===" >> "$LOG"
ssh -o StrictHostKeyChecking=no 10.128.0.40 "sudo poweroff" >> "$LOG" 2>&1 || true
sleep 5
sudo poweroff
"""

b64 = base64.b64encode(script.encode('utf-8')).decode('utf-8')
cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --command="echo {b64} | base64 -d > /home/ayu23/run_v9_test2_bg.sh && chmod +x /home/ayu23/run_v9_test2_bg.sh && cat /home/ayu23/run_v9_test2_bg.sh"'
print("Running command...")
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
