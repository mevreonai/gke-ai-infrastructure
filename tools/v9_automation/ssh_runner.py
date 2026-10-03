import subprocess

def run_ssh(cmd):
    full_cmd = [
        "gcloud.cmd", "compute", "ssh", "kimi-node-0",
        "--zone=us-central1-b",
        "--tunnel-through-iap",
        f"--command={cmd}"
    ]
    p = subprocess.run(full_cmd, capture_output=True, text=True)
    return p.stdout, p.stderr, p.returncode

cmd = "/home/ayu23/vllm_env/bin/python3 -c \"import ray; print('Ray version:', ray.__version__)\""
out, err, code = run_ssh(cmd)
print("Output:\n", out)
if err: print("Error:\n", err)
