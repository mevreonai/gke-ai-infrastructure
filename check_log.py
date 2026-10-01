import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'sed -n "3770,3820p" /tmp/vllm_live_smoke.log'], capture_output=True, text=True)
print(res.stdout)
