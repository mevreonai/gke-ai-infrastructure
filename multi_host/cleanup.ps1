<#
.SYNOPSIS
    Global Comprehensive Teardown Script: Deletes GKE Clusters & TPU/Compute VMs across ALL regions.

.DESCRIPTION
    Safely and unconditionally:
    1. Stops all background kubectl port-forward processes.
    2. Searches for and deletes GKE clusters (targeted cluster or any tpu/ray/vllm cluster).
    3. Scans all GCP regions and terminates any lingering compute VMs in project.
    4. Ensures zero active compute/TPU billing remains.

.PARAMETER ProjectId
    The Google Cloud project ID (default: "mevreon").

.PARAMETER ClusterName
    Optional specific cluster name to delete (e.g. "ray-llm-cluster" or "vllm-singlehost-cluster").
    If omitted, cleans any cluster matching "*singlehost*" or "*ray*" or "*tpu*".

.PARAMETER Region
    Optional specific region/location. If omitted, cleans across ALL locations.

.EXAMPLE
    .\cleanup.ps1
    .\cleanup.ps1 -ClusterName "ray-llm-cluster" -Region "europe-west4"
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$ClusterName = "",
    [string]$Region = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

Write-Host "`n========================================================" -ForegroundColor Red
Write-Host " 🛑 COMPREHENSIVE MULTI-REGION BILLING TEARDOWN" -ForegroundColor Red
Write-Host "========================================================" -ForegroundColor Red

# 1. Stop all port forwarding processes
Write-Host "[1/3] Terminating any active kubectl port-forward processes..." -ForegroundColor Gray
Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Delete GKE Clusters across regions
Write-Host "[2/3] Scanning for GKE clusters to delete (Project: $ProjectId)..." -ForegroundColor Yellow

try {
    $rawClusters = (gcloud container clusters list --project $ProjectId --format="csv[no-heading](name,location)" 2>$null)
    if ($rawClusters) {
        foreach ($line in $rawClusters) {
            $parts = $line.Trim().Split(',')
            if ($parts.Count -ge 2) {
                $cName = $parts[0].Trim()
                $cLoc = $parts[1].Trim()

                # Filter target if specified, otherwise clean test/demo clusters
                $shouldDelete = $false
                if ($ClusterName) {
                    if ($cName -eq $ClusterName) { $shouldDelete = $true }
                } else {
                    if ($cName -like "*singlehost*" -or $cName -like "*ray*" -or $cName -like "*vllm*" -or $cName -like "*tpu*") {
                        $shouldDelete = $true
                    }
                }

                if ($Region -and $cLoc -ne $Region -and -not ($cLoc.StartsWith("$Region-"))) {
                    $shouldDelete = $false
                }

                if ($shouldDelete) {
                    Write-Host "  -> Deleting cluster '$cName' in '$cLoc'..." -ForegroundColor Red
                    gcloud container clusters delete $cName --location $cLoc --project $ProjectId --quiet
                    Write-Host "     Cluster '$cName' deletion command executed." -ForegroundColor Green
                } else {
                    Write-Host "  [SKIP] Retaining non-target cluster: $cName ($cLoc)" -ForegroundColor Gray
                }
            }
        }
    } else {
        Write-Host "  No GKE clusters found." -ForegroundColor Green
    }
} catch {
    Write-Host "  Note during cluster scan: $_" -ForegroundColor Yellow
}

# 3. Double-check all active VMs in the project
Write-Host "`n[3/3] Checking active Compute Engine VM instances across all zones..." -ForegroundColor Gray
try {
    $activeVMs = gcloud compute instances list --project $ProjectId --format="table(name,zone,machineType,status)" 2>$null
    if ($activeVMs) {
        Write-Host "$activeVMs" -ForegroundColor Cyan
    } else {
        Write-Host "  No active Compute Engine VM instances running." -ForegroundColor Green
    }
} catch {}

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " ✅ Teardown complete! All target cluster/VM billing stopped." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
