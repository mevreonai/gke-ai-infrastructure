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

cmd = "/home/ayu23/vllm_env/bin/ray stop --force >/dev/null 2>&1; ssh -o StrictHostKeyChecking=no 10.128.0.40 '/home/ayu23/vllm_env/bin/ray stop --force' >/dev/null 2>&1; sleep 2; nohup /home/ayu23/vllm_env/bin/python3 /home/ayu23/run_single_case.py tp4_pp2_dist native > /home/ayu23/tp4_pp2_dist_live.log 2>&1 & echo $!"
out, err, code = run_ssh(cmd)
print("Returncode:", code)
print("PID Output:\n", out)
if err: print("Error:\n", err)
