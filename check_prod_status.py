import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ps aux | grep run_v9_full'], capture_output=True, text=True)
print("Processes:\n", res.stdout)
res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'cat /home/ayu23/v9_full_production_execution.log'], capture_output=True, text=True)
print("Log:\n", res2.stdout)
