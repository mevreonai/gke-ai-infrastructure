#!/bin/bash
set -euo pipefail

mkdir -p /root/.ssh
cp /home/ayu23/.ssh/authorized_keys /root/.ssh/authorized_keys
cp /home/ayu23/.ssh/id_ed25519 /root/.ssh/id_ed25519
chmod 700 /root/.ssh
chmod 600 /root/.ssh/*

# Enable root login with public key in sshd if needed
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config 2>/dev/null || true
systemctl reload sshd 2>/dev/null || systemctl restart sshd 2>/dev/null || true
echo "Root SSH configured on $(hostname)"
