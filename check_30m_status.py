import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'cat /home/ayu23/v9_full_results/v9_full_production_20260930_090004/logs/phase_status.jsonl'], capture_output=True, text=True)
print("PHASES:\n", res.stdout)

res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ps -u ayu23 -f'], capture_output=True, text=True)
print("PROCS:\n", res2.stdout)

res3 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'tail -n 30 /home/ayu23/v9_full_production_execution.log'], capture_output=True, text=True)
print("EXEC_LOG:\n", res3.stdout)

res4 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ls -la /home/ayu23/v9_full_results/v9_full_production_20260930_090004/'], capture_output=True, text=True)
print("RESULT_ROOT_DIR:\n", res4.stdout)
