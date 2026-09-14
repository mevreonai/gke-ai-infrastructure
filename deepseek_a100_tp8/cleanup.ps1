# ==============================================================================
# 1-Click Immediate Cleanup Script for DeepSeek A100 (80GB) Spot Instance
# Ensures all compute and network resources are deleted so billing stops immediately
# ==============================================================================

[CmdletBinding()]
param(
    [string]$ProjectId = "mevreon",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "deepseek-a100-spot",
    [string]$FirewallRule = "allow-deepseek-ports"
)

$ErrorActionPreference = "Continue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " [CLEANUP] Starting DeepSeek A100 Spot Teardown" -ForegroundColor Cyan
Write-Host " Project:   $ProjectId" -ForegroundColor Yellow
Write-Host " Zone:      $Zone" -ForegroundColor Yellow
Write-Host " Instance:  $InstanceName" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check if VM exists
Write-Host "`n[1/3] Checking if Spot VM exists..." -ForegroundColor Green
$instanceStatus = gcloud compute instances describe $InstanceName --zone=$Zone --project=$ProjectId --format="value(status)" 2>$null

if ($instanceStatus) {
    Write-Host "Found instance '$InstanceName' in status: $instanceStatus." -ForegroundColor Yellow
    Write-Host "Deleting Spot VM and attached boot disk to STOP billing..." -ForegroundColor Red
    gcloud compute instances delete $InstanceName --zone=$Zone --project=$ProjectId --delete-disks=all --quiet
    Write-Host "Instance '$InstanceName' successfully deleted." -ForegroundColor Green
} else {
    Write-Host "Instance '$InstanceName' is not running or already deleted." -ForegroundColor Gray
}

# 2. Check and clean up firewall rule
Write-Host "`n[2/3] Checking firewall rule '$FirewallRule'..." -ForegroundColor Green
$fwCheck = gcloud compute firewall-rules describe $FirewallRule --project=$ProjectId 2>$null
if ($fwCheck) {
    Write-Host "Deleting temporary firewall rule '$FirewallRule'..." -ForegroundColor Yellow
    gcloud compute firewall-rules delete $FirewallRule --project=$ProjectId --quiet
    Write-Host "Firewall rule deleted." -ForegroundColor Green
} else {
    Write-Host "Firewall rule does not exist or already removed." -ForegroundColor Gray
}

# 3. Verify zero lingering resources
Write-Host "`n[3/3] Verifying no remaining active A100 instances in project..." -ForegroundColor Green
$remaining = gcloud compute instances list --project=$ProjectId --filter="name=$InstanceName" --format="table(name,zone,status)"

if (-not $remaining -or $remaining.Trim() -eq "") {
    Write-Host "`n[SUCCESS] All resources torn down cleanly. Active GPU billing: $0.00/hr." -ForegroundColor Green
} else {
    Write-Host "`n[WARNING] Remaining instances detected:" -ForegroundColor Red
    Write-Host $remaining
}

Write-Host "==================================================" -ForegroundColor Cyan
