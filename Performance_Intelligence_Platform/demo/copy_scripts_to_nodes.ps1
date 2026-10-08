# ==============================================================================
# COPY DEMO SCRIPTS TO BOTH NODES (PowerShell)
# Usage:
#   .\copy_scripts_to_nodes.ps1 <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
# Example:
#   .\copy_scripts_to_nodes.ps1 34.70.242.214 35.225.118.110
# ==============================================================================
param(
    [Parameter(Mandatory=$false)][string]$Node0IP = "34.70.242.214",
    [Parameter(Mandatory=$false)][string]$Node1IP = "35.225.118.110"
)

$SSH_KEY = "$env:USERPROFILE\.ssh\google_compute_engine"
$DEMO_DIR = "$PSScriptRoot"

Write-Host "--> Copying demo scripts to Node 0 ($Node0IP)..." -ForegroundColor Cyan
ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node0IP "mkdir -p ~/demo"
scp.exe -i $SSH_KEY -o StrictHostKeyChecking=no -r "$DEMO_DIR\*" "ayu23@${Node0IP}:~/demo/"
ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node0IP "chmod +x ~/demo/*.sh"

Write-Host "--> Copying demo scripts to Node 1 ($Node1IP)..." -ForegroundColor Cyan
ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node1IP "mkdir -p ~/demo"
scp.exe -i $SSH_KEY -o StrictHostKeyChecking=no -r "$DEMO_DIR\*" "ayu23@${Node1IP}:~/demo/"
ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node1IP "chmod +x ~/demo/*.sh"

Write-Host "--> SUCCESS: Demo scripts deployed to both nodes under ~/demo/" -ForegroundColor Green
Write-Host "--> To enter Node 0: ssh -i $SSH_KEY ayu23@$Node0IP" -ForegroundColor Yellow
Write-Host "--> To enter Node 1: ssh -i $SSH_KEY ayu23@$Node1IP" -ForegroundColor Yellow
