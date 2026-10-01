import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ps aux | grep vllm'], capture_output=True, text=True)
print(res.stdout)
