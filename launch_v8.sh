#!/usr/bin/env bash
set -euo pipefail
cd ~/v8_full_suite/V8_FULL
source ~/vllm_env/bin/activate
export VLLM_NETWORK_MODES="native 100g 20g"
export RUN_NETWORK_CAPS=1
export RUN_HW_PREP=0
export RUN_HEAVY_PROFILE=1
export RUN_CAPPED_PROFILE=1
export V8FULL_RESUME=1
export V8FULL_RUN_ID="20260921_195656"
./00_run_v8_full.sh 2>&1 | tee -a ~/v8_full_suite/V8_FULL_RUN.log
