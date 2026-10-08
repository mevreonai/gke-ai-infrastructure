#!/usr/bin/env bash
# ==============================================================================
# DEMO STEP 3: Multi-Node Ray Cluster Coordination
# Usage:
#   On Node 0 (Head):   ./03_start_ray_cluster.sh --head
#   On Node 1 (Worker): ./03_start_ray_cluster.sh --worker <NODE0_INTERNAL_IP>
#                       Example: ./03_start_ray_cluster.sh --worker 10.128.0.41
# ==============================================================================
set -euo pipefail

VENV_BIN="$HOME/vllm_env/bin"
export PATH="$VENV_BIN:$PATH"

MODE="${1:-}"

if [[ "$MODE" == "--head" ]]; then
  echo "======================================================================"
  echo " [DEMO] Initializing Ray Cluster HEAD on Node 0..."
  echo "======================================================================"
  ray stop --force > /dev/null 2>&1 || true
  
  ray start --head \
      --port=6379 \
      --dashboard-host=0.0.0.0 \
      --dashboard-port=8265 \
      --num-gpus=8 \
      --disable-usage-stats
      
  echo ""
  echo "--> Ray HEAD is running on $(hostname -I | awk '{print $1}'):6379"
  echo "--> Ray Dashboard: http://$(hostname -I | awk '{print $1}'):8265"
  echo "======================================================================"
  echo "NOW RUN ON NODE 1:"
  echo "    ./03_start_ray_cluster.sh --worker $(hostname -I | awk '{print $1}')"
  echo "======================================================================"

elif [[ "$MODE" == "--worker" ]]; then
  HEAD_IP="${2:-}"
  if [[ -z "$HEAD_IP" ]]; then
    echo "ERROR: Please specify head node IP. Example: ./03_start_ray_cluster.sh --worker 10.128.0.41"
    exit 1
  fi
  
  echo "======================================================================"
  echo " [DEMO] Connecting Worker Node 1 to Head Node ($HEAD_IP:6379)..."
  echo "======================================================================"
  ray stop --force > /dev/null 2>&1 || true
  
  ray start \
      --address="${HEAD_IP}:6379" \
      --num-gpus=8 \
      --disable-usage-stats
      
  echo "--> Worker joined successfully!"

else
  echo "Usage:"
  echo "  On Node 0: ./03_start_ray_cluster.sh --head"
  echo "  On Node 1: ./03_start_ray_cluster.sh --worker <NODE0_INTERNAL_IP>"
  exit 1
fi

echo ""
echo "======================================================================"
echo " [DEMO] Active Cluster Status (Verifying 16 GPUs across 2 Nodes)"
echo "======================================================================"
ray status
