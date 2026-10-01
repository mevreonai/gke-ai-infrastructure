import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-1', 'ps -u ayu23 -f'], capture_output=True, text=True)
print("NODE 1 PROCS:\n", res.stdout)
res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-1', 'ls -la /tmp/v9_hw_result_132262_1/'], capture_output=True, text=True)
print("NODE 1 RESULTS:\n", res2.stdout)
