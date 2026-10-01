import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "cat /home/ayu23/V9_FULL/configs/models/deepseek_v41_flash.json"]
res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
