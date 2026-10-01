import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'ls -la /home/ayu23/v9_full_results/v9_full_production_20260930_090004/hardware_raw/node0/'], capture_output=True, text=True)
print("NODE0 HW RAW:\n", res.stdout)
