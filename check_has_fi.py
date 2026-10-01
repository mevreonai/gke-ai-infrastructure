import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "sed -n '280,315p' /home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/utils/flashinfer.py"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
