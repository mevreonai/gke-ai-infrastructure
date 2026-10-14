#!/usr/bin/env bash
set -e
export PATH=$HOME/vllm_env/bin:$PATH
cd $HOME/v5_profiling/rtx_g4_smoke_v5/v6_suite

echo "=== STARTING V6 END-TO-END BENCHMARK RUN ==="
date

python 11_run_vllm_surrogate.py --out $HOME/v5_profiling/v5_single_node_results --all

echo "=== BENCHMARK SUITE COMPLETE. GENERATING SUMMARIES ==="
python 15_summarize_vllm.py --runs $HOME/v5_profiling/v5_single_node_results --out $HOME/v5_profiling/v5_single_node_results/summary_v6
python 17_build_serving_analysis.py --runs $HOME/v5_profiling/v5_single_node_results --out $HOME/v5_profiling/v5_single_node_results/analysis

echo "=== ALL DONE ==="
date
