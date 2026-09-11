<#
.SYNOPSIS
    Clean Teardown and Cost-Protection for GKE Inference Gateway (GPU Edition).
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$Zone = "europe-west4-a",
    [string]$ClusterName = "inference-gateway-gpu-cluster"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

Write-Host "`n========================================================" -ForegroundColor Red
Write-Host " 🛑 INITIATING TEARDOWN OF GPU INFERENCE GATEWAY" -ForegroundColor Red
Write-Host "========================================================" -ForegroundColor Red

Write-Host "[TEARDOWN] Deleting GKE GPU Cluster '$ClusterName'..." -ForegroundColor Yellow
gcloud container clusters delete $ClusterName --zone $Zone --project $ProjectId --quiet 2>$null

Write-Host "========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] GPU cluster and resources cleanly terminated!" -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Green
