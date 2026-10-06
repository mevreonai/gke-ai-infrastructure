#!/usr/bin/env bash
# ==============================================================================
# V8 Benchmark Suite — Beginner-Friendly 1-Click Quickstart Runner
# ==============================================================================
# Usage:
#   Option A (Interactive/Auto):
#       ./run_quickstart.sh
#
#   Option B (Pass IPs on command line):
#       ./run_quickstart.sh <NODE0_IP> <NODE1_IP>
#       Example: ./run_quickstart.sh 10.240.0.10 10.240.0.11
# ==============================================================================
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo "===================================================================="
echo "          V8 BENCHMARK SUITE — QUICKSTART LAUNCHER"
echo "===================================================================="

# 1. Accept CLI Arguments for IPs if provided
if [[ $# -ge 2 ]]; then
  export NODE0_IP="$1"
  export NODE1_IP="$2"
  echo "--> Using provided IPs: Node 0 = $NODE0_IP, Node 1 = $NODE1_IP"
elif [[ -f "$SCRIPT_DIR/RUN_CONFIG.env" ]]; then
  echo "--> Loading configuration from RUN_CONFIG.env..."
  source "$SCRIPT_DIR/RUN_CONFIG.env"
  echo "--> Loaded IPs: Node 0 = ${NODE0_IP:-UNSET}, Node 1 = ${NODE1_IP:-UNSET}"
else
  echo "--> No RUN_CONFIG.env found. Copying template from RUN_CONFIG.env.example..."
  cp "$SCRIPT_DIR/RUN_CONFIG.env.example" "$SCRIPT_DIR/RUN_CONFIG.env"
  source "$SCRIPT_DIR/RUN_CONFIG.env"
fi

# 2. Validate IPs
if [[ -z "${NODE0_IP:-}" || -z "${NODE1_IP:-}" ]]; then
  echo "ERROR: NODE0_IP or NODE1_IP is missing!"
  echo "Please edit $SCRIPT_DIR/RUN_CONFIG.env or run:"
  echo "    ./run_quickstart.sh <NODE0_IP> <NODE1_IP>"
  exit 1
fi

export VLLM_HOST="$NODE0_IP"
export VLLM_WORKER_HOST="$NODE1_IP"
export NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME:-ens3}"
export NCCL_NET="${NCCL_NET:-Socket}"
export NCCL_BUFFSIZE="${NCCL_BUFFSIZE:-4194304}"

echo "--> Configuration summary:"
echo "    Primary Node 0 IP : $NODE0_IP"
echo "    Worker Node 1 IP  : $NODE1_IP"
echo "    Network Interface : $NCCL_SOCKET_IFNAME (MTU 1460)"
echo "    NCCL Transport    : $NCCL_NET"
echo "===================================================================="
echo "--> Starting Master Orchestrator (00_run_master_additional_runs.sh)..."
echo "===================================================================="

cd "$SCRIPT_DIR"
exec bash ./00_run_master_additional_runs.sh "$@"
