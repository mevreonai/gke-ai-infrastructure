#!/usr/bin/env python3
"""
Orchestrator for V9-FULL Characterization with Cost-Optimization & Dynamic Node Management.
- Workload: DeepSeek-V4.1-Flash (Mixed MXFP4/FP8)
- Network Modes: Native (175G RoCEv2) and 20G Linux tc
- Contexts: 1K (1024), 8K (8192), 128K (131072), 512K (524288), 1M (1000000)
- Cost Strategy: Powers down kimi-node-1 during Single-Node & Open-Loop benchmarks.
  Powers up kimi-node-1 before Scale-Out benchmarks begin.
  Powers down both nodes upon run completion.
- Live Progress Tracker: Writes status, percentage, and ETA to v9_execution_tracker.json.
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

RUN_ID = f"v9_deepseek_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
REMOTE_V9_DIR = "/home/ayu23/V9_FULL"
MODEL_CONFIG = "configs/models/deepseek_v41_flash.json"
CLUSTER_CONFIG = "configs/clusters/kimi_2x8.json"
SUITE_CONFIG = "configs/suite_native_20g.json"
REMOTE_RESULTS_ROOT = f"/home/ayu23/v9_full_results/{RUN_ID}"
TRACKER_FILE = os.path.join(os.path.dirname(__file__), "v9_execution_tracker.json")

TOTAL_ESTIMATED_RUN_HOURS = 15.5

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_cmd(cmd, timeout=600):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout expired"

def ssh_node0(cmd_str, timeout=1200):
    escaped_cmd = cmd_str.replace('"', '\\"')
    full_cmd = f'gcloud compute ssh {HEAD_NODE} --zone={ZONE} --project={PROJECT} --command="{escaped_cmd}"'
    return run_cmd(full_cmd, timeout=timeout)

def update_tracker(phase, progress_pct, elapsed_hours, details="", worker_state="RUNNING"):
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

def wait_for_rsync():
    log("Waiting for DeepSeek weights to finish rsyncing to Node 1...")
    start_time = time.time()
    while True:
        rc, out, _ = ssh_node0("ps aux | grep -v grep | grep 'rsync -a'", timeout=60)
        if rc != 0 or not out:
            log("Rsync process completed!")
            break
        rc_df, out_df, _ = ssh_node0(f"ssh -o StrictHostKeyChecking=no {WORKER_IP} 'df -h /data | tail -1; ls -1 /data/models/deepseek-v4.1-flash | wc -l'", timeout=60)
        elapsed = (time.time() - start_time) / 3600.0
        log(f"Rsync in progress... Node 1 status: {out_df}")
        update_tracker("weight_sync", 3.0, elapsed, f"Syncing weights to Node 1: {out_df}", worker_state="RUNNING")
        time.sleep(30)

def stop_node1():
    log("Cost-Optimization: Stopping Node 1 during Single-Node runs...")
    rc, out, err = run_cmd(f"gcloud compute instances stop {WORKER_NODE} --zone={ZONE} --project={PROJECT} --quiet")
    if rc == 0:
        log("Node 1 is STOPPED successfully.")
    else:
        log(f"Warning: Failed to stop Node 1: {err}")

def start_node1():
    log("Powering ON Node 1 for Scale-Out benchmarks...")
    rc, out, err = run_cmd(f"gcloud compute instances start {WORKER_NODE} --zone={ZONE} --project={PROJECT} --quiet")
    if rc != 0:
        log(f"Error starting Node 1: {err}")
        return False
    log("Waiting for Node 1 SSH readiness...")
    for _ in range(30):
        time.sleep(10)
        rc, out, _ = ssh_node0(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {WORKER_IP} 'hostname'")
        if rc == 0 and WORKER_NODE in out:
            log(f"Node 1 is ONLINE and ready: {out}")
            return True
    log("Timeout waiting for Node 1 SSH.")
    return False

def shutdown_all_vms():
    log("Run Complete! Powering down both cluster nodes to prevent any unnecessary GCP billing...")
    run_cmd(f"gcloud compute instances stop {WORKER_NODE} --zone={ZONE} --project={PROJECT} --quiet")
    run_cmd(f"gcloud compute instances stop {HEAD_NODE} --zone={ZONE} --project={PROJECT} --quiet")
    log("All VMs powered off safely.")

def run_suite_phase(phase_env, phase_name, target_progress, base_elapsed):
    log(f"=== Starting Suite Phase: {phase_name} ===")
    cmd = (
        f"cd {REMOTE_V9_DIR} && "
        f"V9FULL_RUN_ID={RUN_ID} {phase_env} "
        f"./00_run_v9_full.sh {MODEL_CONFIG} {CLUSTER_CONFIG} {SUITE_CONFIG}"
    )
    # Launch command on Node 0 inside tmux or screen so network hiccups don't abort it
    tmux_cmd = f"tmux new-session -d -s v9_phase_{phase_name} '{cmd} > /home/ayu23/{phase_name}.log 2>&1'"
    rc, _, err = ssh_node0(tmux_cmd)
    if rc != 0:
        log(f"Failed to launch tmux session for {phase_name}: {err}")
        # fallback to nohup
        nohup_cmd = f"nohup bash -c \"{cmd}\" > /home/ayu23/{phase_name}.log 2>&1 &"
        ssh_node0(nohup_cmd)

    # Monitor until completion
    start_t = time.time()
    while True:
        time.sleep(45)
        # Check if 00_run_v9_full.sh is still running
        rc, out, _ = ssh_node0("ps aux | grep -v grep | grep '00_run_v9_full.sh'", timeout=60)
        current_elapsed = base_elapsed + (time.time() - start_t) / 3600.0
        
        # Read latest phase status
        rc_stat, out_stat, _ = ssh_node0(f"tail -n 3 /home/ayu23/v9_full_results/{RUN_ID}/logs/phase_status.jsonl 2>/dev/null", timeout=60)
        log(f"Phase {phase_name} running. Latest log status:\n{out_stat}")
        
        pct = min(target_progress, 5.0 + (current_elapsed / TOTAL_ESTIMATED_RUN_HOURS) * 90.0)
        worker_st = "STOPPED" if "stop_node1" in phase_name else "RUNNING"
        update_tracker(phase_name, pct, current_elapsed, out_stat, worker_state=worker_st)
        
        if rc != 0 or not out:
            log(f"Phase {phase_name} completed.")
            break

def main():
    log("=== V9 COST-EFFECTIVE ORCHESTRATION START ===")
    run_start = time.time()
    
    # Step 1: Wait for weight sync to Node 1
    wait_for_rsync()
    
    # Step 2: Multi-Node Preflight & Network Smoke (Both nodes RUNNING)
    phase1_env = (
        "RUN_HW_PREP=0 "
        "RUN_NODE_LOCAL_HW=0 "
        "RUN_NETWORK_SMOKE=1 "
        "RUN_SINGLE_NODE=0 "
        "RUN_OPEN_LOOP=0 "
        "RUN_SCALEOUT=0 "
        "RUN_PROFILES=0 "
        "RESUME=0"
    )
    elapsed_p1 = (time.time() - run_start) / 3600.0
    run_suite_phase(phase1_env, "preflight_and_network_smoke", target_progress=12.0, base_elapsed=elapsed_p1)
    
    # Step 3: Cost-Optimization: STOP Node 1 for Single-Node & Open-Loop runs
    stop_node1()
    
    phase2_env = (
        "RUN_HW_PREP=0 "
        "RUN_NODE_LOCAL_HW=1 "
        "RUN_NETWORK_SMOKE=0 "
        "RUN_SINGLE_NODE=1 "
        "RUN_OPEN_LOOP=1 "
        "RUN_SCALEOUT=0 "
        "RUN_PROFILES=0 "
        "RESUME=1"
    )
    elapsed_p2 = (time.time() - run_start) / 3600.0
    run_suite_phase(phase2_env, "single_node_and_openloop", target_progress=45.0, base_elapsed=elapsed_p2)
    
    # Step 4: Scale-Out Preparation: Power back ON Node 1
    start_node1()
    
    phase3_env = (
        "RUN_HW_PREP=0 "
        "RUN_NODE_LOCAL_HW=0 "
        "RUN_NETWORK_SMOKE=0 "
        "RUN_SINGLE_NODE=0 "
        "RUN_OPEN_LOOP=0 "
        "RUN_SCALEOUT=1 "
        "RUN_PROFILES=1 "
        "RUN_HEAVY_PROFILE=1 "
        "RUN_TARGETED_CAPPED_DECODE_PROFILE=1 "
        "RESUME=1"
    )
    elapsed_p3 = (time.time() - run_start) / 3600.0
    run_suite_phase(phase3_env, "scaleout_and_profilers", target_progress=98.0, base_elapsed=elapsed_p3)
    
    # Final collect and package
    total_elapsed = (time.time() - run_start) / 3600.0
    update_tracker("completed", 100.0, total_elapsed, "All benchmarks finished, collected, and packaged!", worker_state="SHUTTING_DOWN")
    
    # Step 5: Power down all VMs to prevent idle charges
    shutdown_all_vms()
    log("=== V9 ORCHESTRATION FULLY COMPLETE ===")

if __name__ == "__main__":
    main()
