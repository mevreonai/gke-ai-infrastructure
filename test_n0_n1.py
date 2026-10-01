import subprocess

cmd = 'ssh -o StrictHostKeyChecking=no 10.128.0.40 "hostname"'
res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', cmd], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
