import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'tail -n 20 /tmp/vllm_live_smoke.log'], capture_output=True, text=True)
print(res.stdout)
