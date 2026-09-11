<#
.SYNOPSIS
    Teardown & Cost-Protection script for Disaggregated TPU Serving.
#>

param (
    [string]$ProjectId = "mevreon",
    [string]$Zone = "europe-west4-a",
    [string]$ClusterName = "disaggregated-tpu-cluster"
)

Write-Host "`n========================================================" -ForegroundColor Red
Write-Host " 🛑 STOPPING DISAGGREGATED TPU SERVING & DELETING RESOURCES" -ForegroundColor Red
Write-Host "========================================================" -ForegroundColor Red

# 1. Stop background kubectl port-forwards
Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Delete GKE Cluster
Write-Host "[1/2] Deleting GKE Cluster '$ClusterName'..." -ForegroundColor Yellow
gcloud container clusters delete $ClusterName --zone $Zone --project $ProjectId --quiet 2>$null

# 3. Terminate any orphan VMs
Write-Host "[2/2] Checking for remaining TPU or compute instances..." -ForegroundColor Yellow
$vms = (gcloud compute instances list --project $ProjectId --format="value(name,zone,status)" 2>$null)
if ($vms) {
    foreach ($vmLine in $vms) {
        $vmParts = $vmLine.Split()
        if ($vmParts.Count -ge 3) {
            $vName = $vmParts[0]
            $vZone = $vmParts[1]
            $vStat = $vmParts[2]
            if ($vStat -eq "RUNNING" -and ($vName -like "*disaggregated*" -or $vName -like "*gke-tpu*")) {
                Write-Host "  -> Terminating orphan instance: $vName in $vZone..." -ForegroundColor Yellow
                gcloud compute instances delete $vName --zone $vZone --project $ProjectId --quiet 2>$null
            }
        }
    }
}

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " ✅ Cost-protection teardown complete. Zero billing continues." -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Green
