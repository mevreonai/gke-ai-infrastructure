#!/usr/bin/env bash
set -euo pipefail
cd ~/v8_full_suite/V8_FULL
source ~/vllm_env/bin/activate
export VLLM_NETWORK_MODES="native"
export RUN_CAPPED_PROFILE=0
export V8FULL_RESUME=1
./00_run_v8_full.sh 2>&1 | tee -a ~/v8_full_suite/V8_FULL_RUN.log
