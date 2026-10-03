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

import time
cmd = "echo === DIRS ===; ls -la /home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist; echo === RECENT BENCH LOG ===; tail -n 8 $(ls -t /home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist/*/bench_stdout.log 2>/dev/null | head -n 1) 2>/dev/null || true"
out, err, code = run_ssh(cmd)
print(out)
