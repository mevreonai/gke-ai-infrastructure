import subprocess
import sys

def ssh_cmd(host, cmd, node="kimi-node-0"):
    full_cmd = f'gcloud compute ssh ayu23@{node} --zone=us-central1-b --tunnel-through-iap --command="{cmd}"'
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return res.stdout, res.stderr, res.returncode

if __name__ == '__main__':
    c = "nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader"
    print("=== NODE 0 ===")
    out, err, rc = ssh_cmd("node0", c, "kimi-node-0")
    print(out)
    print("=== NODE 1 ===")
    out, err, rc = ssh_cmd("node1", c, "kimi-node-1")
    print(out)
