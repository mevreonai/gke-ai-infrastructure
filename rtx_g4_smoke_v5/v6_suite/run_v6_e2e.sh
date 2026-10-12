#!/usr/bin/env bash
set -e
export PATH=/home/ayu23/vllm_env/bin:$PATH
cd /home/ayu23/v5_profiling/rtx_g4_smoke_v5/v6_suite

echo "=== STARTING V6 END-TO-END BENCHMARK RUN ==="
date

python 11_run_vllm_surrogate.py --out /home/ayu23/v5_profiling/v5_single_node_results --all

echo "=== BENCHMARK SUITE COMPLETE. GENERATING SUMMARIES ==="
python 15_summarize_vllm.py --runs /home/ayu23/v5_profiling/v5_single_node_results --out /home/ayu23/v5_profiling/v5_single_node_results/summary_v6
python 17_build_serving_analysis.py --runs /home/ayu23/v5_profiling/v5_single_node_results --out /home/ayu23/v5_profiling/v5_single_node_results/analysis

echo "=== ALL DONE ==="
date
