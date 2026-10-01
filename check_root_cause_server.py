import subprocess

cmd = ["python", "run_ssh.py", "kimi-node-0", "grep -A 25 'make_layers' /home/ayu23/v9_full_results/v9_full_production_20260930_090004/vllm_single_node_v9_matrix/tp4_closedloop_1024/server.log"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
