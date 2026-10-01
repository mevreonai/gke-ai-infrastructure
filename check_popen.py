import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "grep -n -C 10 'Popen' /home/ayu23/V9_FULL/v9_core/run_single.py"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
