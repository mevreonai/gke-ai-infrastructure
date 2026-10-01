import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ps -u ayu23 -f'], capture_output=True, text=True)
print("AYU23 PROCS:\n", res.stdout)
res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'cat /home/ayu23/v9_full_production_execution.log | tail -n 20'], capture_output=True, text=True)
print("TAIL LOG:\n", res2.stdout)
