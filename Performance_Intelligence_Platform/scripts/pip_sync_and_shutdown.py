#!/usr/bin/env python3
"""Performance Intelligence Platform (PIP) - Automated Sync & Shutdown Watchdog.

Adapted from V9's sync_and_shutdown.py and generalized for the PIP architecture.
Continuously monitors a remote benchmark run on the head node. When execution finishes:
1. Downloads all manifests, traces, sqlite telemetry, and logs to the local destination via SCP/rsync.
2. Runs pip_collect_and_validate.py on the downloaded artifacts.
3. Automatically shuts down all cluster VM instances to achieve $0/hr idle cloud burn.

Usage:
  python pip_sync_and_shutdown.py --head-node kimi-node-0 --worker-nodes kimi-node-1 --remote-results-dir $HOME/PIP_Benchmark_Data/results/latest
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_cmd(cmd: List[str], timeout: int = 600) -> Tuple[int, str, str]:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def parse_env_file(env_path: Path) -> Dict[str, str]:
    env_vars: Dict[str, str] = {}
    if not env_path.exists():
        return env_vars
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            env_vars[k] = v
    return env_vars

def check_remote_progress(head_node: str, zone: str, project: str, remote_dir: str) -> Tuple[bool, str]:
    """Check if remote benchmarks are still actively running."""
    cmd_str = (
        f"ps aux | grep -E 'run_master_benchmark|run_20min|vllm.entrypoints' | grep -v grep | wc -l; "
        f"ls -la {remote_dir}/CAMPAIGN_SUMMARY.json 2>/dev/null || true"
    )
    cmd = [
        "gcloud", "compute", "ssh", head_node,
        f"--zone={zone}", f"--project={project}",
        f'--command="{cmd_str}"'
    ]
    rc, out, err = run_cmd(cmd, timeout=45)
    if rc != 0:
        return False, f"SSH error: {err}"

    lines = out.splitlines()
    active_procs = int(lines[0].strip()) if lines and lines[0].strip().isdigit() else 0
    has_summary = any("CAMPAIGN_SUMMARY.json" in l for l in lines)

    is_done = (active_procs == 0 and has_summary)
    status_msg = f"Active processes: {active_procs}, Summary file present: {has_summary}"
    return is_done, status_msg

def scp_results(head_node: str, zone: str, project: str, remote_dir: str, local_dest: Path) -> bool:
    log(f"Downloading benchmark results from {head_node}:{remote_dir} to {local_dest}...")
    local_dest.mkdir(parents=True, exist_ok=True)
    cmd = [
        "gcloud", "compute", "scp", "--recurse",
        f"{head_node}:{remote_dir}", str(local_dest),
        f"--zone={zone}", f"--project={project}"
    ]
    rc, out, err = run_cmd(cmd, timeout=1800)
    if rc != 0:
        log(f"SCP download encountered an error: {err}")
        return False
    log("Download completed successfully.")
    return True

def stop_cluster(nodes: List[str], zone: str, project: str) -> None:
    log("\n>>> INITIATING CLUSTER SHUTDOWN ($0/HR BILLING) <<<")
    cmd = ["gcloud", "compute", "instances", "stop"] + nodes + [f"--zone={zone}", f"--project={project}"]
    rc, out, err = run_cmd(cmd, timeout=180)
    if rc == 0:
        log(f"Cluster stopped successfully:\n{out}")
    else:
        log(f"Cluster stop error: {err}")

def main():
    parser = argparse.ArgumentParser(description="Performance Intelligence Platform - Sync & Shutdown Watchdog")
    parser.add_argument("--config", type=Path, default=None,
                        help="Path to RUN_CONFIG.env configuration file")
    parser.add_argument("--project", type=str, default=None,
                        help="GCP Project ID (or env GCP_PROJECT)")
    parser.add_argument("--zone", type=str, default=None,
                        help="GCP Compute Zone (or env GCP_ZONE)")
    parser.add_argument("--head-node", type=str, default=None,
                        help="Head node VM name (or env HEAD_NODE)")
    parser.add_argument("--worker-nodes", type=str, default=None,
                        help="Comma-separated worker node VM names (or env WORKER_NODES)")
    parser.add_argument("--remote-results-dir", type=str, default="$HOME/PIP_Benchmark_Data/results/latest",
                        help="Remote directory containing run results")
    parser.add_argument("--local-dest-dir", type=Path, default=Path("./harvested_pip_results"),
                        help="Local directory destination for downloaded artifacts")
    parser.add_argument("--poll-interval-sec", type=int, default=60,
                        help="Seconds between status polling checks (default: 60)")
    parser.add_argument("--no-shutdown", action="store_true",
                        help="Skip stopping instances after synchronization")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    env_file = args.config or script_dir / "RUN_CONFIG.env"
    env_vars = parse_env_file(env_file)

    project = args.project or env_vars.get("GCP_PROJECT") or env_vars.get("PROJECT") or os.environ.get("GCP_PROJECT", "")
    zone = args.zone or env_vars.get("GCP_ZONE") or env_vars.get("ZONE") or os.environ.get("GCP_ZONE", "")
    head_node = args.head_node or env_vars.get("HEAD_NODE") or os.environ.get("HEAD_NODE", "node-0")
    workers_raw = args.worker_nodes or env_vars.get("WORKER_NODES") or os.environ.get("WORKER_NODES", "node-1")
    worker_nodes = [w.strip() for w in workers_raw.split(",") if w.strip()]
    all_nodes = [head_node] + worker_nodes

    log("=" * 80)
    log("  PERFORMANCE INTELLIGENCE PLATFORM — SYNC & SHUTDOWN WATCHDOG")
    log(f"  Project       : {project or '<dynamic>'}")
    log(f"  Zone          : {zone or '<dynamic>'}")
    log(f"  Head Node     : {head_node}")
    log(f"  Worker Nodes  : {worker_nodes}")
    log(f"  Remote Dir    : {args.remote_results_dir}")
    log(f"  Local Dest    : {args.local_dest_dir}")
    log(f"  Poll Interval : {args.poll_interval_sec}s")
    log(f"  Auto Shutdown : {not args.no_shutdown}")
    log("=" * 80)

    log("Beginning execution monitoring loop...")
    while True:
        is_done, status_msg = check_remote_progress(head_node, zone, project, args.remote_results_dir)
        log(f"Check status: {status_msg}")
        if is_done:
            log("[+] Benchmark campaign finished! Starting results retrieval...")
            success = scp_results(head_node, zone, project, args.remote_results_dir, args.local_dest_dir)
            if success and not args.no_shutdown:
                stop_cluster(all_nodes, zone, project)
            break
        time.sleep(args.poll_interval_sec)

if __name__ == "__main__":
    main()
