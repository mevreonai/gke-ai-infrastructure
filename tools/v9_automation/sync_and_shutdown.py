import subprocess
import json
import time
import os

ZONE = "us-central1-b"
NODES = ["kimi-node-0", "kimi-node-1"]

def run_cmd(cmd_list):
    print("Running:", " ".join(cmd_list))
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    if res.returncode != 0:
        print("STDERR:", res.stderr)
    return res.stdout, res.returncode

def check_progress():
    cmd = [
        "gcloud.cmd", "compute", "ssh", "kimi-node-0",
        f"--zone={ZONE}", "--tunnel-through-iap",
        "--command=ls -la /home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist; cat /home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist/case_manifest.json 2>/dev/null; ps aux | grep run_single_case | grep -v grep || true"
    ]
    out, rc = run_cmd(cmd)
    return out

def stop_instances():
    print("\n>>> CRITICAL: INITIATING IMMEDIATE CLUSTER SHUTDOWN ($0/HR) <<<")
    cmd = ["gcloud.cmd", "compute", "instances", "stop"] + NODES + [f"--zone={ZONE}"]
    out, rc = run_cmd(cmd)
    print(out)
    # verify status
    verif_cmd = ["gcloud.cmd", "compute", "instances", "list", "--filter=name:(kimi-node-0 OR kimi-node-1)"]
    out, rc = run_cmd(verif_cmd)
    print("Instance states:\n", out)

def scp_results():
    print("\n>>> DOWNLOADING LIVE BENCHMARK RESULTS TO LOCAL <<<")
    os.makedirs("v9_full_result/tp4_pp2_dist_live", exist_ok=True)
    cmd = [
        "gcloud.cmd", "compute", "scp", "--recurse",
        "kimi-node-0:/home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist",
        "v9_full_result/tp4_pp2_dist_live",
        f"--zone={ZONE}", "--tunnel-through-iap"
    ]
    out, rc = run_cmd(cmd)
    print("SCP finished.")

if __name__ == "__main__":
    out = check_progress()
    print("Current progress:\n", out)
