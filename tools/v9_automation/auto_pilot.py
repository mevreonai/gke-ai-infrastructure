import subprocess
import time
import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZONE = "us-central1-b"
NODES = ["kimi-node-0", "kimi-node-1"]

def run_cmd(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.stdout or "", res.stderr or "", res.returncode

def is_job_running():
    cmd = [
        "gcloud.cmd", "compute", "ssh", "kimi-node-0",
        f"--zone={ZONE}", "--tunnel-through-iap",
        "--command=ps aux | grep run_single_case | grep -v grep | wc -l"
    ]
    stdout, stderr, rc = run_cmd(cmd)
    try:
        count = int(stdout.strip().split()[-1])
        return count > 0
    except Exception:
        # fallback
        return True

def get_status_summary():
    cmd = [
        "gcloud.cmd", "compute", "ssh", "kimi-node-0",
        f"--zone={ZONE}", "--tunnel-through-iap",
        "--command=echo === DIRS ===; ls /home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist; echo === RECENT LOG ===; tail -n 5 $(ls -t /home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist/*/bench_stdout.log 2>/dev/null | head -n 1) 2>/dev/null || true"
    ]
    stdout, stderr, rc = run_cmd(cmd)
    return stdout.strip()

def log(msg):
    print(msg, flush=True)

def download_and_stop():
    log("\n=======================================================")
    log("JOB FINISHED! DOWNLOADING ARTIFACTS AND STOPPING VMS...")
    log("=======================================================")
    
    os.makedirs("v9_full_result/tp4_pp2_dist_live", exist_ok=True)
    scp_cmd = [
        "gcloud.cmd", "compute", "scp", "--recurse",
        "kimi-node-0:/home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist",
        "v9_full_result/tp4_pp2_dist_live",
        f"--zone={ZONE}", "--tunnel-through-iap"
    ]
    log("Executing SCP...")
    out, err, rc = run_cmd(scp_cmd)
    log(f"SCP Output: {out} {err}")

    log("\nSTOPPING INSTANCES (Stop GPU billing immediately)...")
    stop_cmd = ["gcloud.cmd", "compute", "instances", "stop"] + NODES + [f"--zone={ZONE}"]
    out, err, rc = run_cmd(stop_cmd)
    log(f"Stop Output: {out} {err}")

    verif_cmd = ["gcloud.cmd", "compute", "instances", "list", "--filter=name:(kimi-node-0 OR kimi-node-1)"]
    out, err, rc = run_cmd(verif_cmd)
    log(f"Final Instance States:\n{out}")

def main():
    log("Auto-pilot started. Monitoring tp4_pp2_dist execution...")
    iteration = 0
    while True:
        iteration += 1
        running = is_job_running()
        summary = get_status_summary()
        log(f"[{time.strftime('%H:%M:%S')}] Check #{iteration} - Job running: {running}")
        log(summary)
        log("-" * 50)
        
        if not running:
            log("Job has completed!")
            break
            
        time.sleep(20)
        
    download_and_stop()

if __name__ == "__main__":
    main()
