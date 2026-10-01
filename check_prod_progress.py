import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'tail -n 35 /home/ayu23/v9_full_production_execution.log'], capture_output=True, text=True)
print("LOG:\n", res.stdout)
res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'cat /home/ayu23/v9_full_results/v9_full_production_20260930_090004/logs/phase_status.jsonl'], capture_output=True, text=True)
print("PHASES:\n", res2.stdout)
