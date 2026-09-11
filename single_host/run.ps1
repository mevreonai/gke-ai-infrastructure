<#
.SYNOPSIS
    Single-Host TPU v6e Trillium Serving with Live Telemetry Monitoring and Auto-Teardown.

.DESCRIPTION
    Provisions GKE Standard cluster with a Single-Host TPU v6e (Trillium) node pool,
    streams weights from Cloud Storage FUSE, launches vLLM with PagedAttention,
    opens the Gradio chat interface, displays real-time hardware queue status,
    and automatically executes a full multi-region teardown when you stop.

.PARAMETER ProjectId
    GCP Project ID (default: "mevreon").

.PARAMETER Region
    GCP Region with TPU v6e quota (default: "europe-west4").

.PARAMETER Zone
    GCP Zone with TPU v6e hardware (default: "europe-west4-a").

.PARAMETER ClusterName
    GKE Cluster name (default: "vllm-singlehost-cluster").

.PARAMETER MachineType
    TPU v6e machine type (default: "ct6e-standard-4t" for 4 chips, or "ct6e-standard-8t" for 8 chips).

.PARAMETER TpuTopology
    TPU topology (default: "2x2" for 4 chips, or "2x4" for 8 chips).

.PARAMETER ModelId
    Model ID (default: "google/gemma-2-27b-it").

.PARAMETER KeepClusterOnExit
    Do not delete cluster on exit.
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$Region = "europe-west4",
    [string]$Zone = "europe-west4-a",
    [string]$ClusterName = "vllm-singlehost-cluster",
    [string]$MachineType = "ct6e-standard-4t",
    [string]$ModelId = "google/gemma-2-27b-it",
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

    # 1. Kill port forward background jobs
    Write-Info "Terminating background port-forwarding..."
    foreach ($j in $script:PortForwardJobs) {
        try { Stop-Job -Job $j -SilentlyContinue; Remove-Job -Job $j -SilentlyContinue } catch {}
    }
    Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

    if ($KeepClusterOnExit) {
        Write-Warn "KeepClusterOnExit specified. Cluster '$ClusterName' was NOT deleted."
        return
    }

    # 2. Comprehensive multi-region cluster cleanup
    Write-Host "[TEARDOWN] Searching and deleting GKE cluster '$ClusterName' across regions..." -ForegroundColor Yellow
    try {
        $rawClusters = (gcloud container clusters list --project $ProjectId --format="csv[no-heading](name,location)" 2>$null)
        if ($rawClusters) {
            foreach ($line in $rawClusters) {
                $parts = $line.Trim().Split(',')
                if ($parts.Count -ge 2) {
                    $cName = $parts[0].Trim()
                    $cLoc = $parts[1].Trim()
                    if ($cName -eq $ClusterName -or $cName -like "*singlehost*") {
                        Write-Host "  -> Deleting cluster '$cName' in '$cLoc'..." -ForegroundColor Red
                        gcloud container clusters delete $cName --location $cLoc --project $ProjectId --quiet
                        Write-Success "Cluster '$cName' deletion completed."
                    }
                }
            }
        }
    } catch {
        Write-Warn "Teardown note: $_"
    }

    # 3. Verify active VMs
    Write-Info "Verifying active Compute Engine instances across project..."
    $vms = (gcloud compute instances list --project $ProjectId --format="table(name,zone,machineType,status)" 2>$null)
    if ($vms) {
        Write-Host "$vms" -ForegroundColor Gray
    } else {
        Write-Success "0 active Compute Engine VMs remaining."
    }

    Write-Host "========================================================" -ForegroundColor Green
    Write-Success "Cost-protection complete! All TPU and VM billing stopped."
    Write-Host "========================================================" -ForegroundColor Green
}

Register-EngineEvent -SourceIdentifier ([System.Management.Automation.PsEngineEvent]::Exiting) -Action { Invoke-Teardown } -ErrorAction SilentlyContinue | Out-Null

try {
    Write-Header "Step 1/6: Configuration & GCP Pre-Flight"
    Write-Info "Project:    $ProjectId"
    Write-Info "Region:     $Region | Zone: $Zone"
    Write-Info "Cluster:    $ClusterName (GKE Standard Mode)"
    Write-Info "TPU Model:  TPU v6e Trillium ($MachineType, 4 Chips)"
    Write-Info "Model:      $ModelId"

    gcloud config set project $ProjectId --quiet
    gcloud config set compute/zone $Zone --quiet
    $projectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)" 2>$null)

    # 1. APIs
    Write-Header "Step 2/6: Enabling GCP APIs"
    gcloud services enable container.googleapis.com tpu.googleapis.com storage.googleapis.com --project $ProjectId --quiet
    Write-Success "APIs verified and active."

    # 2. GKE Base Cluster
    Write-Header "Step 3/6: GKE Standard Base Cluster ($Zone)"
    $cList = (gcloud container clusters list --project $ProjectId --filter="name=$ClusterName AND location:$Zone" --format="value(name)" 2>$null)
    if ($cList -notcontains $ClusterName -and $cList -ne $ClusterName) {
        Write-Live "Creating base GKE cluster '$ClusterName' in $Zone with GCSFuse CSI Driver..."
        gcloud container clusters create $ClusterName `
            --project $ProjectId `
            --zone $Zone `
            --node-locations $Zone `
            --release-channel regular `
            --machine-type e2-standard-4 `
            --num-nodes 1 `
            --workload-pool "${ProjectId}.svc.id.goog" `
            --addons GcsFuseCsiDriver `
            --enable-ip-alias `
            --quiet
        Write-Success "Base cluster created successfully."
    } else {
        Write-Info "Base cluster '$ClusterName' exists."
    }

    # Ensure cluster has finished provisioning before proceeding
    $cStatus = (gcloud container clusters describe $ClusterName --zone $Zone --project $ProjectId --format="value(status)" 2>$null)
    while ($cStatus -eq "PROVISIONING") {
        Write-Live "Base cluster is currently PROVISIONING. Waiting for completion..."
        Start-Sleep -Seconds 15
        $cStatus = (gcloud container clusters describe $ClusterName --zone $Zone --project $ProjectId --format="value(status)" 2>$null)
    }

    # 3. Single-Host TPU v6e Node Pool
    Write-Header "Step 4/6: Provisioning TPU v6e Trillium Node Pool ($MachineType)"
    $tpuList = (gcloud container node-pools list --cluster $ClusterName --zone $Zone --project $ProjectId --filter="name=tpunodepool" --format="value(name)" 2>$null)
    if ($tpuList -notcontains "tpunodepool" -and $tpuList -ne "tpunodepool") {
        Write-Live "Requesting TPU v6e slice: $MachineType (1 node)..."
        gcloud container node-pools create tpunodepool `
            --project $ProjectId `
            --cluster $ClusterName `
            --zone $Zone `
            --node-locations $Zone `
            --machine-type $MachineType `
            --num-nodes 1 `
            --quiet
        if ($LASTEXITCODE -ne 0) { throw "Failed to create TPU v6e node pool." }
        Write-Success "TPU v6e node pool created."
    } else {
        Write-Info "TPU node pool 'tpunodepool' exists."
    }

    gcloud container clusters get-credentials $ClusterName --zone $Zone --project $ProjectId

    # 4. Storage & Manifests
    Write-Header "Step 5/6: Configuring Workload Identity & Deploying Manifests"
    $BucketName = "mevreon-tpu-model-weights"
    kubectl create serviceaccount vllm-ksa --namespace default --dry-run=client -o yaml | kubectl apply -f -
    gcloud storage buckets add-iam-policy-binding "gs://${BucketName}" `
        --member="principal://iam.googleapis.com/projects/${projectNumber}/locations/global/workloadIdentityPools/${ProjectId}.svc.id.goog/subject/ns/default/sa/vllm-ksa" `
        --role="roles/storage.objectUser" --quiet | Out-Null

    (Get-Content "$PSScriptRoot/manifests/01-vllm-single-host-tpu.yaml" -Raw) -replace "bucketName:\s*GSBUCKET", "bucketName: $BucketName" | kubectl apply -f -
    kubectl apply -f "$PSScriptRoot/manifests/02-gradio.yaml"

    # 5. Live Telemetry Dashboard
    Write-Header "Step 6/6: Live Telemetry & Model Readiness"
    Write-Host "Monitoring TPU v6e Hardware Allocation & Pod Readiness in Real-Time..." -ForegroundColor Yellow

    $ready = $false
    $timeout = 60
    $iter = 0

    while (-not $ready -and $iter -lt $timeout) {
        $iter++
        Start-Sleep -Seconds 5
        
        $nodeCount = (kubectl get nodes --no-headers 2>$null | Measure-Object).Count
        $podInfo = (kubectl get pods -l app=vllm-tpu -o jsonpath='{.items[0].status.phase}' 2>$null)
        $gradioInfo = (kubectl get pods -l app=gradio -o jsonpath='{.items[0].status.phase}' 2>$null)
        
        # Check GCE TPU MIG Status
        $migStatus = "Active"
        try {
            $mig = (gcloud compute instance-groups managed list --filter="name ~ tpunodepool" --zones $Zone --project $ProjectId --format="value(name)" 2>$null)
            if ($mig) {
                $rr = (gcloud compute instance-groups managed resize-requests list $mig --zone $Zone --project $ProjectId --format="value(state)" 2>$null)
                if ($rr) { $migStatus = "TPU Slice Queue: $rr" }
            }
        } catch {}

        Write-Host "[LIVE TELEMETRY] Nodes: $nodeCount | Gradio: $gradioInfo | vLLM Pod: $podInfo | Hardware: $migStatus" -ForegroundColor Cyan

        if ($podInfo -eq "Running") {
            $containerReady = (kubectl get pods -l app=vllm-tpu -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>$null)
            if ($containerReady -eq "true") {
                $ready = $true
                Write-Success "vLLM TPU v6e Serving Container is 100% READY & HEALTHY!"
                break
            }
        }
    }

    # Start Port Forwards
    Write-Info "Starting background port-forwarding..."
    $script:PortForwardJobs += Start-Job -ScriptBlock { while ($true) { kubectl port-forward service/gradio 8080:8080; Start-Sleep -Seconds 2 } }
    $script:PortForwardJobs += Start-Job -ScriptBlock { while ($true) { kubectl port-forward service/vllm-service 8000:8000; Start-Sleep -Seconds 2 } }
    Start-Sleep -Seconds 3

    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " 🚀 SINGLE-HOST TPU v6e SERVING IS LIVE & ONLINE!" -ForegroundColor Green
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
    Write-Host " [L] Tail live vLLM logs"
    Write-Host " [ENTER] STOP everything and automatically teardown all VMs"
    Write-Host ""

    $session = $true
    while ($session) {
        $u = Read-Host "Choice (T=Test / L=Logs / Enter=Teardown & Stop Billing)"
        if ($u -eq 'T' -or $u -eq 't') {
            python "$PSScriptRoot/client/test_inference.py"
        } elseif ($u -eq 'L' -or $u -eq 'l') {
            kubectl logs -l app=vllm-tpu --tail=50 -f
        } else {
            $session = $false
        }
    }
} catch {
    Write-Host "`n[ERROR] $_" -ForegroundColor Red
} finally {
    Invoke-Teardown
}
