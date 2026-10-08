#!/usr/bin/env bash
# ==============================================================================
# COPY ENTIRE PLATFORM & DEMO SCRIPTS TO BOTH NODES (Bash)
# Usage:
#   ./copy_scripts_to_nodes.sh <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
# ==============================================================================
set -euo pipefail

NODE0_IP="${1:-}"
NODE1_IP="${2:-}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/google_compute_engine}"

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PLATFORM_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

if [[ -z "$NODE0_IP" ]]; then
  echo "Usage: ./copy_scripts_to_nodes.sh <NODE0_IP> [NODE1_IP]"
  exit 1
fi

echo "--> Deploying Performance_Intelligence_Platform to Node 0 ($NODE0_IP)..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE0_IP" "mkdir -p ~/Performance_Intelligence_Platform"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$PLATFORM_DIR"/* "ayu23@$NODE0_IP:~/Performance_Intelligence_Platform/"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE0_IP" "ln -sfn ~/Performance_Intelligence_Platform/demo ~/demo && chmod +x ~/Performance_Intelligence_Platform/scripts/*.sh ~/Performance_Intelligence_Platform/demo/*.sh"

if [[ -n "$NODE1_IP" ]]; then
  echo "--> Deploying Performance_Intelligence_Platform to Node 1 ($NODE1_IP)..."
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE1_IP" "mkdir -p ~/Performance_Intelligence_Platform"
  scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$PLATFORM_DIR"/* "ayu23@$NODE1_IP:~/Performance_Intelligence_Platform/"
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE1_IP" "ln -sfn ~/Performance_Intelligence_Platform/demo ~/demo && chmod +x ~/Performance_Intelligence_Platform/scripts/*.sh ~/Performance_Intelligence_Platform/demo/*.sh"
fi

echo "--> SUCCESS: Full suite deployed to ~/Performance_Intelligence_Platform and symlinked to ~/demo"
