import subprocess
import sys
import os

REMOTE_DIR = "kimi-node-0:/home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist"
LOCAL_TARGET = "v9_full_result/tp4_pp2_dist_live"

print("1. Downloading benchmark results via scp...")
res_scp = subprocess.run([
    "gcloud.cmd", "compute", "scp", "--recurse",
    REMOTE_DIR,
    LOCAL_TARGET,
    "--zone=us-central1-b"
], capture_output=True, text=True)
print("SCP STDOUT:", res_scp.stdout)
print("SCP STDERR:", res_scp.stderr)

print("2. Stopping compute instances kimi-node-0 and kimi-node-1...")
res_stop = subprocess.run([
    "gcloud.cmd", "compute", "instances", "stop",
    "kimi-node-0", "kimi-node-1",
    "--zone=us-central1-b"
], capture_output=True, text=True)
print("STOP STDOUT:", res_stop.stdout)
print("STOP STDERR:", res_stop.stderr)

print("3. Verifying instance status...")
res_list = subprocess.run([
    "gcloud.cmd", "compute", "instances", "list",
    "--filter=name:(kimi-node-0 OR kimi-node-1)"
], capture_output=True, text=True)
print(res_list.stdout)
