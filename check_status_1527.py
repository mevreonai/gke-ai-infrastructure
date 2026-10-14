import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'cat $HOME/v9_full_results/v9_full_production_20260930_090004/logs/phase_status.jsonl'], capture_output=True, text=True)
print("PHASES:\n", res.stdout)

res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ps -u $(whoami) -f'], capture_output=True, text=True)
print("PROCS:\n", res2.stdout)

res3 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ls -la $HOME/v9_full_results/v9_full_production_20260930_090004/hardware_raw/'], capture_output=True, text=True)
print("HARDWARE_RAW_DIR:\n", res3.stdout)
