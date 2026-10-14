#!/usr/bin/env bash
cd $HOME/v8_additional_runs_suite
source $HOME/vllm_env/bin/activate
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"
$HOME/v8_additional_runs_suite/rtx_g4_smoke_v5/20_run_single_node_v6_aligned.sh \
  python3 $HOME/v8_additional_runs_suite/rtx_g4_smoke_v5/11_run_vllm_surrogate.py \
  --cases $HOME/v8_additional_runs_suite/stage2_cases_single_node.json \
  --case tp4_native_offload_reuse_test \
  --out $HOME/v8_additional_runs/20261009_104123/stage2/02_cpu_offload_reuse \
  --port 8070
