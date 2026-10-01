import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ps aux | grep cicc'], capture_output=True, text=True)
print(res.stdout)
res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ls -la /home/ayu23/.cache/flashinfer/0.6.18/120f/cached_ops/sparse_mla_sm120/'], capture_output=True, text=True)
print("Cache dir:", res2.stdout)
