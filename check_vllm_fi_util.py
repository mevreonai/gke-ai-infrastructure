import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "grep -n -C 15 'has_flashinfer_sparse_mla_sm120_config' /home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/utils/flashinfer.py"]
res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
