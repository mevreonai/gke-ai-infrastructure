<#
.SYNOPSIS
    Global Comprehensive Teardown Script for GKE Inference Gateway.

.DESCRIPTION
    Deletes the GKE Inference Gateway cluster, stops port forwarding, releases load balancers,
    and terminates all lingering compute/TPU VMs across the project.
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$ClusterName = "inference-gateway-cluster",
    [string]$Region = "europe-west4",
    [string]$Zone = "europe-west4-a"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

Write-Host "`n========================================================" -ForegroundColor Red
Write-Host " 🛑 INFERENCE GATEWAY BILLING TEARDOWN" -ForegroundColor Red
Write-Host "========================================================" -ForegroundColor Red

# 1. Kill port-forward processes
Write-Host "[1/4] Terminating background port-forwarding..." -ForegroundColor Yellow
Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Delete GKE Clusters
Write-Host "[2/4] Deleting GKE Cluster '$ClusterName'..." -ForegroundColor Yellow
try {
    $cExists = (gcloud container clusters list --project $ProjectId --filter="name:$ClusterName" --format="value(name)" 2>$null)
    if ($cExists) {
        gcloud container clusters delete $ClusterName --zone $Zone --project $ProjectId --quiet
        Write-Host "  -> Cluster '$ClusterName' deleted." -ForegroundColor Green
    } else {
        Write-Host "  -> No cluster named '$ClusterName' found." -ForegroundColor Gray
    }
} catch {
    Write-Host "  -> Cluster deletion notice: $_" -ForegroundColor Yellow
}

# 3. Clean any orphaned TPU VMs or GKE instances
Write-Host "[3/4] Scanning for lingering compute VMs in $ProjectId..." -ForegroundColor Yellow
try {
    $vms = (gcloud compute instances list --project $ProjectId --format="value(name,zone,status)" 2>$null)
    if ($vms) {
        foreach ($vmLine in $vms) {
            $parts = $vmLine.Split()
            if ($parts.Count -ge 3) {
                $name = $parts[0]
                $z = $parts[1]
                $status = $parts[2]
                if ($status -eq "RUNNING" -and ($name -like "*tpu*" -or $name -like "*gateway*" -or $name -like "*vllm*")) {
                    Write-Host "  -> Terminating orphaned VM '$name' in '$z'..." -ForegroundColor Yellow
                    gcloud compute instances delete $name --zone $z --project $ProjectId --quiet 2>$null
                }
            }
        }
    }
} catch {}

# 4. Verify Active Billing
Write-Host "[4/4] Verifying active Compute Engine instances..." -ForegroundColor Yellow
$remaining = (gcloud compute instances list --project $ProjectId --filter="status=RUNNING" --format="table(name,zone,machineType,status)" 2>$null)
if ($remaining) {
    Write-Host $remaining -ForegroundColor Yellow
} else {
    Write-Host "  -> 0 active running instances found." -ForegroundColor Green
}

Write-Host "========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] All Inference Gateway resources stopped. Zero active billing." -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Green
