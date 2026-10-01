import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "grep -E -C 3 '(ERROR|Traceback|RuntimeError|Exception)' /home/ayu23/v9_full_results/v9_full_production_20260930_090004/vllm_single_node_v9_matrix/tp8_context_baseline/server.log | head -n 35"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
