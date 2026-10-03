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

cmd = "tail -n 35 /home/ayu23/tp4_pp2_dist_live.log"
out, err, code = run_ssh(cmd)
print("tp4_pp2_dist_live.log tail:\n", out)
