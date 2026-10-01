import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'grep -n "block_size=32" /home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/attention.py'], capture_output=True, text=True)
print(res.stdout)
