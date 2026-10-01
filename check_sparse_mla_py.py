import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "cat /home/ayu23/vllm_env/lib64/python3.12/site-packages/flashinfer/mla/_sparse_mla_sm120.py"]
res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
