import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'sed -n "60,95p" /home/ayu23/V9_FULL/00_run_v9_full.sh'], capture_output=True, text=True)
print(res.stdout)
