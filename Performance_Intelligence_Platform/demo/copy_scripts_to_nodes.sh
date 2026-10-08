#!/usr/bin/env bash
# ==============================================================================
# COPY DEMO SCRIPTS TO BOTH NODES (Bash)
# Usage:
#   ./copy_scripts_to_nodes.sh <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
# ==============================================================================
set -euo pipefail

NODE0_IP="${1:-34.70.242.214}"
NODE1_IP="${2:-35.225.118.110}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/google_compute_engine}"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo "--> Copying demo suite to Node 0 ($NODE0_IP)..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE0_IP" "mkdir -p ~/demo"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$SCRIPT_DIR"/* "ayu23@$NODE0_IP:~/demo/"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE0_IP" "chmod +x ~/demo/*.sh"

echo "--> Copying demo suite to Node 1 ($NODE1_IP)..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE1_IP" "mkdir -p ~/demo"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$SCRIPT_DIR"/* "ayu23@$NODE1_IP:~/demo/"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ayu23@$NODE1_IP" "chmod +x ~/demo/*.sh"

echo "--> SUCCESS: Demo scripts deployed to both nodes under ~/demo/"
