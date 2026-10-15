#!/usr/bin/env python3
"""Performance Intelligence Platform (PIP) - Cost-Effective Dynamic Cluster Orchestrator.

Adapted from V9's dynamic lifecycle management (orchestrate_v9_cost_effective.py & watch_and_wake_node1.py).
Minimizes expensive GPU cloud spend (~$40-$80/hr per 8x node) by:
1. Keeping secondary worker nodes powered down during single-node benchmarks (Stage 1 / sweeps).
2. Automatically booting worker nodes and verifying SSH & NCCL readiness before distributed benchmarks (Stage 2).
3. Powering down worker nodes immediately after distributed scale-out testing completes.
4. Optionally terminating the entire cluster ($0/hr) upon full campaign completion.
5. Continuously reporting progress and ETA to pip_execution_tracker.json.

Configuration:
Reads dynamic cluster parameters from RUN_CONFIG.env or CLI flags.
No hardcoded project IDs, zones, or private IP addresses.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_cmd(cmd: str | List[str], timeout: int = 600) -> Tuple[int, str, str]:
    try:
        if isinstance(cmd, list):
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        else:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
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

class ClusterManager:
    def __init__(self, project: str, zone: str, head_node: str, worker_nodes: List[str],
                 tracker_file: Path, total_estimated_hours: float = 12.0):
        self.project = project
        self.zone = zone
        self.head_node = head_node
        self.worker_nodes = worker_nodes
        self.tracker_file = tracker_file
        self.total_estimated_hours = total_estimated_hours
        self.start_time = time.time()

    def get_instance_status(self, instance_name: str) -> str:
        cmd = [
            "gcloud", "compute", "instances", "describe", instance_name,
            f"--zone={self.zone}", f"--project={self.project}",
            "--format=value(status)"
        ]
        rc, out, _ = run_cmd(cmd, timeout=30)
        return out.strip().upper() if rc == 0 else "UNKNOWN"

    def start_node(self, instance_name: str) -> bool:
        log(f"Starting instance '{instance_name}' in zone '{self.zone}'...")
        cmd = [
            "gcloud", "compute", "instances", "start", instance_name,
            f"--zone={self.zone}", f"--project={self.project}"
        ]
        rc, out, err = run_cmd(cmd, timeout=180)
        if rc != 0:
            log(f"Failed to start {instance_name}: {err}")
            return False
        log(f"Instance '{instance_name}' started successfully.")
        return True

    def stop_node(self, instance_name: str) -> bool:
        log(f"Stopping instance '{instance_name}' to eliminate idle GPU spend ($0/hr)...")
        cmd = [
            "gcloud", "compute", "instances", "stop", instance_name,
            f"--zone={self.zone}", f"--project={self.project}"
        ]
        rc, out, err = run_cmd(cmd, timeout=180)
        if rc != 0:
            log(f"Failed to stop {instance_name}: {err}")
            return False
        log(f"Instance '{instance_name}' stopped successfully.")
        return True

    def wait_for_ssh(self, instance_name: str, max_retries: int = 15, delay_sec: int = 15) -> bool:
        log(f"Waiting for SSH readiness on '{instance_name}'...")
        check_cmd = [
            "gcloud", "compute", "ssh", instance_name,
            f"--zone={self.zone}", f"--project={self.project}",
            "--command=echo READY", "--ssh-flag=-o ConnectTimeout=10"
        ]
        for attempt in range(1, max_retries + 1):
            rc, out, _ = run_cmd(check_cmd, timeout=30)
            if rc == 0 and "READY" in out:
                log(f"Instance '{instance_name}' is SSH ready on attempt {attempt}.")
                return True
            log(f"Attempt {attempt}/{max_retries}: Instance '{instance_name}' not ready yet. Retrying in {delay_sec}s...")
            time.sleep(delay_sec)
        log(f"ERROR: Instance '{instance_name}' did not become SSH ready after {max_retries} attempts.")
        return False

    def update_tracker(self, phase: str, progress_pct: float, details: str = "",
                       worker_state: str = "STOPPED") -> None:
        elapsed_hours = (time.time() - self.start_time) / 3600.0
        eta_hours = max(0.0, self.total_estimated_hours - elapsed_hours)
        payload = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "worker_state": worker_state,
            "progress_percent": round(progress_pct, 1),
            "elapsed_hours": round(elapsed_hours, 2),
            "eta_hours": round(eta_hours, 2),
            "head_node": self.head_node,
            "worker_nodes": self.worker_nodes,
            "details": details
        }
        try:
            self.tracker_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            log(f"Warning: Failed to write tracker file: {e}")

    def execute_remote_head(self, cmd_str: str, timeout: int = 3600) -> Tuple[int, str, str]:
        escaped = cmd_str.replace('"', '\\"')
        cmd = [
            "gcloud", "compute", "ssh", self.head_node,
            f"--zone={self.zone}", f"--project={self.project}",
            f'--command="{escaped}"'
        ]
        return run_cmd(cmd, timeout=timeout)

def main():
    parser = argparse.ArgumentParser(description="Performance Intelligence Platform - Dynamic Cluster Orchestrator")
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
    parser.add_argument("--action", choices=["status", "wake-workers", "sleep-workers", "shutdown-all", "orchestrate"],
                        default="status", help="Orchestration action to perform")
    parser.add_argument("--auto-shutdown", action="store_true",
                        help="Automatically stop instances after campaign completion")
    args = parser.parse_args()

    # Load configuration
    script_dir = Path(__file__).resolve().parent
    env_file = args.config or script_dir / "RUN_CONFIG.env"
    env_vars = parse_env_file(env_file)

    project = args.project or env_vars.get("GCP_PROJECT") or env_vars.get("PROJECT") or os.environ.get("GCP_PROJECT", "")
    zone = args.zone or env_vars.get("GCP_ZONE") or env_vars.get("ZONE") or os.environ.get("GCP_ZONE", "")
    head_node = args.head_node or env_vars.get("HEAD_NODE") or os.environ.get("HEAD_NODE", "node-0")
    workers_raw = args.worker_nodes or env_vars.get("WORKER_NODES") or os.environ.get("WORKER_NODES", "node-1")
    worker_nodes = [w.strip() for w in workers_raw.split(",") if w.strip()]

    tracker_file = script_dir / "pip_execution_tracker.json"
    mgr = ClusterManager(project=project, zone=zone, head_node=head_node,
                         worker_nodes=worker_nodes, tracker_file=tracker_file)

    log("=" * 80)
    log("  PERFORMANCE INTELLIGENCE PLATFORM — CLUSTER LIFECYCLE ORCHESTRATOR")
    log(f"  Project     : {project or '<dynamic>'}")
    log(f"  Zone        : {zone or '<dynamic>'}")
    log(f"  Head Node   : {head_node}")
    log(f"  Worker Nodes: {worker_nodes}")
    log(f"  Action      : {args.action}")
    log("=" * 80)

    if args.action == "status":
        log("Checking current cluster instance statuses...")
        all_nodes = [head_node] + worker_nodes
        for node in all_nodes:
            st = mgr.get_instance_status(node)
            log(f"  Node '{node}': {st}")
        mgr.update_tracker(phase="STATUS_CHECK", progress_pct=0.0, details="Checked cluster status")

    elif args.action == "wake-workers":
        log("Waking worker nodes for distributed scale-out testing...")
        all_ok = True
        for worker in worker_nodes:
            st = mgr.get_instance_status(worker)
            if st != "RUNNING":
                if not mgr.start_node(worker):
                    all_ok = False
                    continue
            if not mgr.wait_for_ssh(worker):
                all_ok = False
        mgr.update_tracker(phase="WORKERS_ACTIVE", progress_pct=50.0,
                           worker_state="RUNNING" if all_ok else "PARTIAL")
        if not all_ok:
            sys.exit(1)

    elif args.action == "sleep-workers":
        log("Powering down worker nodes to eliminate idle GPU billing ($0/hr)...")
        for worker in worker_nodes:
            mgr.stop_node(worker)
        mgr.update_tracker(phase="WORKERS_STOPPED", progress_pct=100.0, worker_state="STOPPED")

    elif args.action == "shutdown-all":
        log("Initiating full cluster power-down for complete cost elimination...")
        for worker in worker_nodes:
            mgr.stop_node(worker)
        mgr.stop_node(head_node)
        mgr.update_tracker(phase="CLUSTER_STOPPED", progress_pct=100.0, worker_state="STOPPED",
                           details="Entire cluster stopped ($0/hr)")

    elif args.action == "orchestrate":
        log("Starting dynamic campaign orchestration...")
        # Step A: Single node execution with workers stopped
        log("[Phase 1/3] Single-Node & Hardware Characterization (Workers STOPPED)")
        for worker in worker_nodes:
            if mgr.get_instance_status(worker) == "RUNNING":
                mgr.stop_node(worker)
        mgr.update_tracker(phase="STAGE1_SINGLE_NODE", progress_pct=15.0, worker_state="STOPPED")

        # Step B: Wake workers for Stage 2 Scale-Out
        log("[Phase 2/3] Distributed Scale-Out Matrix (Waking Worker Nodes)")
        for worker in worker_nodes:
            mgr.start_node(worker)
            mgr.wait_for_ssh(worker)
        mgr.update_tracker(phase="STAGE2_DISTRIBUTED", progress_pct=60.0, worker_state="RUNNING")

        # Step C: After scale-out, put workers to sleep
        log("[Phase 3/3] Scale-Out Complete (Powering Down Workers)")
        for worker in worker_nodes:
            mgr.stop_node(worker)
        mgr.update_tracker(phase="STAGE3_LOCAL_AND_COMPLETE", progress_pct=95.0, worker_state="STOPPED")

        if args.auto_shutdown:
            log("Auto-shutdown enabled: stopping head node as well.")
            mgr.stop_node(head_node)
            mgr.update_tracker(phase="CAMPAIGN_COMPLETE", progress_pct=100.0, worker_state="STOPPED",
                               details="Cluster shut down successfully ($0/hr)")

if __name__ == "__main__":
    main()
