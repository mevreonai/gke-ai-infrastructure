#!/usr/bin/env python3
"""
Watcher and Auto-Wake Daemon for kimi-node-1.
- Monitors Single-Node benchmarks on kimi-node-0.
- When Single-Node benchmarks reach 80% (>= 13 cases) or Open-Loop begins,
  automatically boots kimi-node-1 and verifies inter-node SSH readiness
  well in advance of multi-node scale-out testing.
- Updates v9_execution_tracker.json continuously.
"""

import subprocess
import time
import json
import os
import sys
from datetime import datetime

PROJECT = "mevreon"
ZONE = "us-central1-b"
HEAD_NODE = "kimi-node-0"
WORKER_NODE = "kimi-node-1"
WORKER_IP = "10.128.0.40"
RUN_ID = "v9_full_production_20260929_180331"
TRACKER_FILE = os.path.join(os.path.dirname(__file__), "v9_execution_tracker.json")
TOTAL_ESTIMATED_RUN_HOURS = 14.5
START_TIMESTAMP = time.time() - (2.35 * 3600)  # Started at 23:33 IST (~2.35h ago)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_cmd(cmd, timeout=300):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout expired"

def ssh_node0(cmd_str, timeout=60):
    escaped_cmd = cmd_str.replace('"', '\\"')
    full_cmd = f'gcloud compute ssh {HEAD_NODE} --zone={ZONE} --project={PROJECT} --command="{escaped_cmd}"'
    return run_cmd(full_cmd, timeout=timeout)

def update_tracker(phase, progress_pct, elapsed_hours, details="", worker_state="STOPPED"):
    eta_hours = max(0.0, TOTAL_ESTIMATED_RUN_HOURS - elapsed_hours)
    data = {
        "timestamp": datetime.now().isoformat(),
        "run_id": RUN_ID,
        "phase": phase,
        "worker_state": worker_state,
        "progress_percent": round(progress_pct, 1),
        "elapsed_hours": round(elapsed_hours, 2),
        "eta_hours": round(eta_hours, 1),
        "details": details
    }
    try:
        with open(TRACKER_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"Warning: Failed to write tracker file: {e}")

def get_node1_status():
    rc, out, _ = run_cmd(f"gcloud compute instances describe {WORKER_NODE} --zone={ZONE} --project={PROJECT} --format=\"value(status)\"")
    return out if rc == 0 else "UNKNOWN"

def wake_node1():
    log("=== Triggering Auto-Wake for kimi-node-1 ===")
    update_tracker("waking_node1", 45.0, (time.time() - START_TIMESTAMP)/3600.0, "Waking kimi-node-1 for upcoming multi-node benchmarks...", worker_state="STARTING")
    rc, out, err = run_cmd(f"gcloud compute instances start {WORKER_NODE} --zone={ZONE} --project={PROJECT} --quiet")
    if rc != 0:
        log(f"Error starting {WORKER_NODE}: {err}")
        return False
    log(f"Instance start command accepted. Waiting for {WORKER_NODE} to become RUNNING and SSH-ready...")
    
    # Wait for SSH connectivity from node 0
    for attempt in range(40):
        time.sleep(10)
        rc_ssh, out_ssh, _ = ssh_node0(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {WORKER_IP} 'hostname'")
        if rc_ssh == 0 and WORKER_NODE in out_ssh:
            log(f"SUCCESS: {WORKER_NODE} is ONLINE and verified ready via inter-node SSH: {out_ssh}")
            update_tracker("node1_ready", 48.0, (time.time() - START_TIMESTAMP)/3600.0, "kimi-node-1 is online and ready for scale-out benchmarks!", worker_state="RUNNING")
            return True
        log(f"Attempt {attempt+1}/40: Waiting for {WORKER_NODE} SSH...")
    
    log(f"Warning: Timed out waiting for {WORKER_NODE} SSH readiness.")
    return False

def main():
    log("=== Starting Watcher and Auto-Wake Daemon for kimi-node-1 ===")
    node1_awake = False
    
    while True:
        try:
            now_sec = time.time()
            elapsed_hours = (now_sec - START_TIMESTAMP) / 3600.0
            
            # Query Node 0 for single-node progress
            check_cmd = f"ls -1 /home/ayu23/v9_full_results/{RUN_ID}/vllm_single_node_v9_matrix/ 2>/dev/null | wc -l; tail -n 1 /home/ayu23/v9_full_results/{RUN_ID}/logs/phase_status.jsonl 2>/dev/null; ps aux | grep -v grep | grep run_single | wc -l"
            rc, out, _ = ssh_node0(check_cmd)
            
            lines = out.split("\n") if rc == 0 else []
            case_count = int(lines[0].strip()) if len(lines) >= 1 and lines[0].strip().isdigit() else 0
            last_phase = lines[1].strip() if len(lines) >= 2 else ""
            is_running_single = int(lines[2].strip()) if len(lines) >= 3 and lines[2].strip().isdigit() else 1
            
            # Progress calculation: Single-node has 17 cases. Total suite reaches ~45% at end of single-node.
            progress_pct = min(42.0, 16.0 + (case_count / 17.0) * 26.0)
            
            w_state = get_node1_status()
            log(f"Status Check: single-node cases completed={case_count}/17, last_phase={last_phase}, worker={w_state}, elapsed={elapsed_hours:.2f}h")
            
            details_str = f"Single-node vLLM active on Node 0 ({case_count}/17 configurations complete). Node 1 is {w_state} to eliminate compute charges."
            update_tracker("vllm_single", progress_pct, elapsed_hours, details=details_str, worker_state=w_state)
            
            # Trigger condition: case_count >= 13, or openloop started, or single finished
            if not node1_awake and (case_count >= 13 or "openloop" in last_phase or "scaleout" in last_phase):
                log(f"Single-node reached threshold (cases={case_count}, last_phase={last_phase}). Waking Node 1 now!")
                success = wake_node1()
                if success:
                    node1_awake = True
                    log("Auto-Wake successfully completed. Daemon will continue monitoring until scale-out.")
            
            # If scaleout has already completed or whole suite finished, exit
            if "package_results" in last_phase or elapsed_hours > 15.0:
                log("Suite has progressed past scale-out. Daemon task completed.")
                break
                
        except Exception as e:
            log(f"Exception in watcher loop: {e}")
            
        time.sleep(45)

if __name__ == "__main__":
    main()
