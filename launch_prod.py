import subprocess

launch_cmd = 'nohup /home/user/run_v9_full_production.sh > /home/user/run_v9_full_production.out 2>&1 &'
res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', launch_cmd], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
