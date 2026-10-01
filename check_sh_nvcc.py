import subprocess

cmd = ["python", "run_ssh.py", "kimi-node-0", "echo PATH=$PATH; which nvcc"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
