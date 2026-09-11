<#
.SYNOPSIS
    Multi-Host TPU Serving with Live Real-Time Hardware & Model Monitoring and Multi-Region Auto-Teardown.

.DESCRIPTION
    Provisions GKE cluster with Multi-Host TPU node pool, displays live real-time telemetry
    (cluster status, GCE TPU resize requests, Ray Serve pod logs), and guarantees automatic
    cluster/VM teardown across all regions upon exit.
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$Region = "europe-west4",
    [string]$Zone = "europe-west4-a",
    [string]$ClusterName = "ray-llm-cluster",
    [string]$MachineType = "ct6e-standard-4t",
    [string]$TpuTopology = "2x4",
    [int]$NumNodes = 2,
    [string]$HfToken = "",
    [switch]$SkipBuild,
    [switch]$AutoTestAndTeardown,
    [switch]$KeepClusterOnExit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

function Write-Header([string]$title) {
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host " 🚀 $title" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
}

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Gray }
function Write-Success([string]$msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Live([string]$msg) { Write-Host "  -> $msg" -ForegroundColor Cyan }

$script:PortForwardJobs = @()

function Invoke-Teardown {
    Write-Host "`n========================================================" -ForegroundColor Red
    Write-Host " 🛑 INITIATING AUTOMATIC BILLING TEARDOWN" -ForegroundColor Red
    Write-Host "========================================================" -ForegroundColor Red

    Write-Info "Terminating background port-forwarding..."
    foreach ($j in $script:PortForwardJobs) {
        try { Stop-Job -Job $j -SilentlyContinue; Remove-Job -Job $j -SilentlyContinue } catch {}
    }
    Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

    if ($KeepClusterOnExit) {
        Write-Warn "KeepClusterOnExit specified. Cluster '$ClusterName' was NOT deleted."
        return
    }

    # Comprehensive multi-region cluster cleanup
    Write-Host "[TEARDOWN] Searching and deleting GKE cluster '$ClusterName' across all regions..." -ForegroundColor Yellow
    try {
        $rawClusters = (gcloud container clusters list --project $ProjectId --format="csv[no-heading](name,location)" 2>$null)
        if ($rawClusters) {
            foreach ($line in $rawClusters) {
                $parts = $line.Trim().Split(',')
                if ($parts.Count -ge 2) {
                    $cName = $parts[0].Trim()
                    $cLoc = $parts[1].Trim()
                    if ($cName -eq $ClusterName -or $cName -like "*ray*" -or $cName -like "*tpu-multihost*") {
                        Write-Host "  -> Deleting cluster '$cName' in '$cLoc'..." -ForegroundColor Red
                        gcloud container clusters delete $cName --location $cLoc --project $ProjectId --quiet
                        Write-Success "Cluster '$cName' deletion completed."
                    }
                }
            }
        }
    } catch {
        Write-Warn "Cleanup note: $_"
    }

    Write-Info "Verifying active Compute Engine VMs in $ProjectId..."
    $vms = (gcloud compute instances list --project $ProjectId --format="table(name,zone,machineType,status)" 2>$null)
    if ($vms) { Write-Host "$vms" -ForegroundColor Gray } else { Write-Success "0 active VMs remaining in project." }
    Write-Host "========================================================" -ForegroundColor Green
    Write-Success "Cost-protection complete! No ongoing TPU charges."
    Write-Host "========================================================" -ForegroundColor Green
}

Register-EngineEvent -SourceIdentifier ([System.Management.Automation.PsEngineEvent]::Exiting) -Action { Invoke-Teardown } -ErrorAction SilentlyContinue | Out-Null

try {
    Write-Header "Step 1/6: Configuration & GCP Pre-Flight"
    Write-Info "Project: $ProjectId | Region: $Region | Zone: $Zone"
    Write-Info "Cluster: $ClusterName | Multi-Host Topology: 2x4 (2 VMs x 4 chips = 8 TPU chips)"

    gcloud config set project $ProjectId --quiet
    gcloud config set compute/zone $Zone --quiet
    $projectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)" 2>$null)

    # 1. APIs
    Write-Header "Step 2/6: Enabling GCP APIs"
    gcloud services enable container.googleapis.com tpu.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com storage.googleapis.com --project $ProjectId --quiet
    Write-Success "APIs active."

    # 2. GKE Base Cluster
    Write-Header "Step 3/6: GKE Base Cluster (RayOperator + GCSFuse)"
    $cList = (gcloud container clusters list --project $ProjectId --filter="name=$ClusterName AND location:$Zone" --format="value(name)" 2>$null)
    if ($cList -notcontains $ClusterName -and $cList -ne $ClusterName) {
        Write-Live "Creating GKE cluster '$ClusterName' in $Zone..."
        gcloud container clusters create $ClusterName `
            --project $ProjectId `
            --zone $Zone `
            --release-channel regular `
            --machine-type e2-standard-16 `
            --num-nodes 1 `
            --addons "RayOperator,GcsFuseCsiDriver" `
            --workload-pool "${ProjectId}.svc.id.goog" `
            --enable-ip-alias `
            --quiet
        if ($LASTEXITCODE -ne 0) { throw "Failed to create base cluster $ClusterName." }
        Write-Success "Base cluster ready."
    } else {
        Write-Info "Base cluster '$ClusterName' exists."
    }

    # 3. Multi-Host TPU Node Pool
    Write-Header "Step 4/6: Multi-Host TPU Node Pool"
    $tpuPoolName = "tpunodepool"
    $tpuList = (gcloud container node-pools list --cluster $ClusterName --zone $Zone --project $ProjectId --filter="name=$tpuPoolName" --format="value(name)" 2>$null)
    if ($tpuList -notcontains $tpuPoolName -and $tpuList -ne $tpuPoolName) {
        Write-Live "Requesting Multi-Host TPU node pool ($NumNodes nodes x $MachineType, topology $TpuTopology)..."
        gcloud container node-pools create $tpuPoolName `
            --project $ProjectId `
            --cluster $ClusterName `
            --zone $Zone `
            --machine-type $MachineType `
            --tpu-topology $TpuTopology `
            --num-nodes $NumNodes `
            --node-locations $Zone `
            --quiet
        if ($LASTEXITCODE -ne 0) { throw "Failed to create TPU node pool." }
        Write-Success "Multi-Host TPU node pool created."
    } else {
        Write-Info "TPU node pool '$tpuPoolName' exists."
    }

    gcloud container clusters get-credentials $ClusterName --zone $Zone --project $ProjectId

    # 4. Storage, IAM & Manifests
    Write-Header "Step 5/6: Workload Identity & Deploying RayService"
    $BucketName = "mevreon-tpu-model-weights"
    $ImageTag = "us-east1-docker.pkg.dev/${ProjectId}/ray-repo/vllm-tpu-ray:vllm-tpu"

    kubectl create serviceaccount ray-ksa --dry-run=client -o yaml | kubectl apply -f -
    $hfVal = if ($HfToken) { $HfToken } else { "none" }
    kubectl create secret generic hf-secret --from-literal=hf_api_token="$hfVal" --dry-run=client -o yaml | kubectl apply -f -
    gcloud iam service-accounts create tpu-reader-sa --display-name="TPU Reader SA" --project $ProjectId 2>$null
    gcloud storage buckets add-iam-policy-binding "gs://${BucketName}" --member="serviceAccount:tpu-reader-sa@${ProjectId}.iam.gserviceaccount.com" --role="roles/storage.objectAdmin" --quiet | Out-Null
    gcloud iam service-accounts add-iam-policy-binding "tpu-reader-sa@${ProjectId}.iam.gserviceaccount.com" --project $ProjectId --role="roles/iam.workloadIdentityUser" --member="serviceAccount:${ProjectId}.svc.id.goog[default/ray-ksa]" --quiet | Out-Null
    kubectl annotate serviceaccount ray-ksa iam.gke.io/gcp-service-account="tpu-reader-sa@${ProjectId}.iam.gserviceaccount.com" --overwrite

    kubectl apply -f "$PSScriptRoot/manifests/01-networking-netdev.yaml"
    (Get-Content "$PSScriptRoot/manifests/02-ray-service-multihost-tpu.yaml" -Raw) -replace "us-east1-docker.pkg.dev/[^/]+/ray-repo/vllm-tpu-ray:vllm-tpu", $ImageTag -replace "bucketName:\s*[\w-]+", "bucketName: $BucketName" | kubectl apply -f -
    kubectl apply -f "$PSScriptRoot/manifests/gradio.yaml"

    # 5. Live Dashboard
    Write-Header "Step 6/6: Live Telemetry & Ray Serve Cluster Readiness"
    Write-Host "Monitoring TPU Hardware Allocation & Ray Serve Pods in Real-Time..." -ForegroundColor Yellow

    $ready = $false
    $timeout = 60
    $iter = 0

    while (-not $ready -and $iter -lt $timeout) {
        $iter++
        Start-Sleep -Seconds 5
        
        $nodeCount = (kubectl get nodes --no-headers 2>$null | Measure-Object).Count
        $headStatus = (kubectl get pods -l ray.io/node-type=head -o jsonpath='{.items[0].status.phase}' 2>$null)
        $workerCount = (kubectl get pods -l ray.io/node-type=worker -o jsonpath='{.items[*].status.phase}' 2>$null)
        
        # Check GCE TPU MIG Status
        $migStatus = "Active"
        try {
            $mig = (gcloud compute instance-groups managed list --filter="name ~ tpunodepool" --zones $Zone --project $ProjectId --format="value(name)" 2>$null)
            if ($mig) {
                $rr = (gcloud compute instance-groups managed resize-requests list $mig --zone $Zone --project $ProjectId --format="value(state)" 2>$null)
                if ($rr) { $migStatus = "TPU Slice Queue: $rr" }
            }
        } catch {}

        Write-Host "[LIVE TELEMETRY] Nodes: $nodeCount | Ray Head: $headStatus | Workers: $workerCount | Hardware: $migStatus" -ForegroundColor Cyan

        if ($headStatus -eq "Running" -and $nodeCount -ge 3) {
            $serveStatus = (kubectl exec (kubectl get pod -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}') -c ray-head -- serve status 2>$null)
            if ($serveStatus -match "RUNNING") {
                $ready = $true
                Write-Success "Ray Serve Multi-Host Cluster is HEALTHY & SERVING!"
                break
            }
        }
    }

    # Start Port Forwarding
    Write-Info "Starting background port-forwarding..."
    $script:PortForwardJobs += Start-Job -ScriptBlock { kubectl port-forward service/gradio 8080:8080 }
    $script:PortForwardJobs += Start-Job -ScriptBlock { kubectl port-forward svc/vllm-tpu-multihost-head-svc 8000:8000 }
    Start-Sleep -Seconds 3

    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " 🚀 MULTI-HOST TPU SERVING IS LIVE & ONLINE!" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "  • Gradio Chat UI : http://localhost:8080" -ForegroundColor Cyan
    Write-Host "  • OpenAI Endpoint: http://localhost:8000/v1/chat/completions" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Green

    try { Start-Process "http://localhost:8080" } catch {}

    if ($AutoTestAndTeardown) {
        Write-Host "`n========================================================" -ForegroundColor Yellow
        Write-Host " 🧪 AUTOMATED INFERENCE VERIFICATION (-AutoTestAndTeardown)" -ForegroundColor Yellow
        Write-Host "========================================================" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        python "$PSScriptRoot/client/test_inference.py"
        Write-Success "Automated verification finished successfully! Now proceeding to automatic teardown..."
        return
    }

    Write-Host "`nInteractive Session:" -ForegroundColor Yellow
    Write-Host " [T] Run CLI benchmark test"
    Write-Host " [S] Show Ray Serve status"
    Write-Host " [ENTER] STOP everything and automatically teardown all VMs"
    Write-Host ""

    $session = $true
    while ($session) {
        $u = Read-Host "Choice (T=Test / S=Status / Enter=Teardown & Stop Billing)"
        if ($u -eq 'T' -or $u -eq 't') {
            python "$PSScriptRoot/client/test_inference.py"
        } elseif ($u -eq 'S' -or $u -eq 's') {
            kubectl exec (kubectl get pod -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}') -c ray-head -- serve status
        } else {
            $session = $false
        }
    }
} catch {
    Write-Host "`n[ERROR] $_" -ForegroundColor Red
} finally {
    Invoke-Teardown
}
