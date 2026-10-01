import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "grep -n -C 10 '_required_sm120_sparse_topk' /home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/nvidia/flashinfer_sparse.py"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
