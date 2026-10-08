# ==============================================================================
# COPY ENTIRE PLATFORM & DEMO SCRIPTS TO BOTH NODES (PowerShell)
# Usage:
#   .\copy_scripts_to_nodes.ps1 <NODE0_EXTERNAL_IP> <NODE1_EXTERNAL_IP>
# ==============================================================================
param(
    [Parameter(Mandatory=$true)][string]$Node0IP,
    [Parameter(Mandatory=$false)][string]$Node1IP = ""
)

$SSH_KEY = "$env:USERPROFILE\.ssh\google_compute_engine"
$PLATFORM_DIR = Split-Path -Parent $PSScriptRoot

Write-Host "--> Deploying Performance_Intelligence_Platform to Node 0 ($Node0IP)..." -ForegroundColor Cyan
ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node0IP "mkdir -p ~/Performance_Intelligence_Platform"
scp.exe -i $SSH_KEY -o StrictHostKeyChecking=no -r "$PLATFORM_DIR\*" "ayu23@${Node0IP}:~/Performance_Intelligence_Platform/"
ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node0IP "ln -sfn ~/Performance_Intelligence_Platform/demo ~/demo && chmod +x ~/Performance_Intelligence_Platform/scripts/*.sh ~/Performance_Intelligence_Platform/demo/*.sh"

if ($Node1IP -ne "") {
    Write-Host "--> Deploying Performance_Intelligence_Platform to Node 1 ($Node1IP)..." -ForegroundColor Cyan
    ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node1IP "mkdir -p ~/Performance_Intelligence_Platform"
    scp.exe -i $SSH_KEY -o StrictHostKeyChecking=no -r "$PLATFORM_DIR\*" "ayu23@${Node1IP}:~/Performance_Intelligence_Platform/"
    ssh.exe -i $SSH_KEY -o StrictHostKeyChecking=no ayu23@$Node1IP "ln -sfn ~/Performance_Intelligence_Platform/demo ~/demo && chmod +x ~/Performance_Intelligence_Platform/scripts/*.sh ~/Performance_Intelligence_Platform/demo/*.sh"
}

Write-Host "--> SUCCESS: Full suite deployed to ~/Performance_Intelligence_Platform and symlinked to ~/demo" -ForegroundColor Green
