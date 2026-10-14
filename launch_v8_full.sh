#!/usr/bin/env bash
set -euo pipefail
cd $HOME/v8_full_suite/V8_FULL
export V8FULL_RUN_ID=20260921_195656
export V8FULL_RESUME=1
export RUN_HW_PREP=0
export VLLM_NETWORK_MODES="native 100g 20g"
export RUN_NETWORK_CAPS=1
export RUN_HEAVY_PROFILE=1
export RUN_CAPPED_PROFILE=1
source $HOME/vllm_env/bin/activate
nohup ./00_run_v8_full.sh > $HOME/v8_full_suite/V8_FULL_RUN.log 2>&1 &
echo "LAUNCHED_PID=$!"
