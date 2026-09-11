<#
.SYNOPSIS
    GKE Inference Gateway (llm-d + TPU v6e Trillium) 1-Click Deployment & Testing.

.DESCRIPTION
    Provisions GKE Standard cluster with Gateway API (HttpLoadBalancing), Cloud Storage FUSE CSI driver,
    TPU v6e Trillium node pool, Gateway API Inference Extension CRDs, llm-d Endpoint Picker (EPP),
    vLLM on TPU v6e (Gemma-2-27B-IT), and Gradio UI.
    Guarantees automatic clean teardown of all resources upon exit.
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$Region = "europe-west4",
    [string]$Zone = "europe-west4-a",
    [string]$ClusterName = "inference-gateway-cluster",
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

    if ($KeepClusterOnExit) {
        Write-Warn "KeepClusterOnExit specified. Cluster '$ClusterName' and port-forwarding remain active for your demo!"
        return
    }

    Write-Info "Terminating background port-forwarding..."
    foreach ($j in $script:PortForwardJobs) {
        try { Stop-Job -Job $j -SilentlyContinue; Remove-Job -Job $j -SilentlyContinue } catch {}
    }
    Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

    Write-Host "[TEARDOWN] Searching and deleting GKE cluster '$ClusterName' across regions..." -ForegroundColor Yellow
    try {
        $rawClusters = (gcloud container clusters list --project $ProjectId --format="csv[no-heading](name,location)" 2>$null)
        if ($rawClusters) {
            foreach ($line in $rawClusters) {
                $parts = $line.Trim().Split(',')
                if ($parts.Count -ge 2) {
                    $cName = $parts[0].Trim()
                    $cLoc = $parts[1].Trim()
                    if ($cName -eq $ClusterName -or $cName -like "*inference-gateway*") {
                        Write-Host "  -> Deleting cluster '$cName' in '$cLoc'..." -ForegroundColor Red
                        gcloud container clusters delete $cName --location $cLoc --project $ProjectId --quiet
                        Write-Success "Cluster '$cName' deletion completed."
                    }
                }
            }
        }
    } catch {
        Write-Warn "Cluster deletion encountered: $_"
    }

    Write-Info "Verifying active Compute Engine instances across project..."
    try {
        $vms = (gcloud compute instances list --project $ProjectId --format="value(name,zone,status)" 2>$null)
        if ($vms) {
            foreach ($vmLine in $vms) {
                $vmParts = $vmLine.Split()
                if ($vmParts.Count -ge 3) {
                    $vName = $vmParts[0]
                    $vZone = $vmParts[1]
                    $vStat = $vmParts[2]
                    if ($vStat -eq "RUNNING" -and ($vName -like "*gke-tpu*" -or $vName -like "*inference-gateway*")) {
                        Write-Host "  -> Terminating remaining VM '$vName' in '$vZone'..." -ForegroundColor Yellow
                        gcloud compute instances delete $vName --zone $vZone --project $ProjectId --quiet 2>$null
                    }
                }
            }
        }
    } catch {}

    Write-Host "========================================================" -ForegroundColor Green
    Write-Success "Cost-protection complete! All TPU, Gateway, and VM billing stopped."
    Write-Host "========================================================`n" -ForegroundColor Green
}

try {
    Write-Header "Step 1/7: Configuration & Pre-Flight"
    Write-Info "Project:     $ProjectId"
    Write-Info "Region:      $Region | Zone: $Zone"
    Write-Info "Cluster:     $ClusterName (GKE Gateway + llm-d + TPU v6e)"
    Write-Info "TPU Model:   TPU v6e Trillium ($MachineType, 4 Chips)"
    Write-Info "Model ID:    $ModelId"

    # Check gcloud authentication
    $token = (gcloud auth print-access-token 2>$null)
    if (-not $token) {
        Write-Warn "gcloud credentials expired or missing. Launching interactive authentication in your browser..."
        gcloud auth login --brief
    }

    gcloud config set project $ProjectId --quiet
    gcloud config set compute/zone $Zone --quiet
    $projectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)" 2>$null)

    # 1. Enable APIs
    Write-Header "Step 2/7: Enabling GCP APIs"
    gcloud services enable container.googleapis.com tpu.googleapis.com storage.googleapis.com networkservices.googleapis.com compute.googleapis.com --project $ProjectId --quiet
    Write-Success "APIs verified and active."

    # 2. Regional Proxy-Only Subnet for Gateway (Required by GKE Gateway Controller)
    Write-Header "Step 3/7: Regional Proxy-Only Subnet ($Region)"
    $proxySubnet = (gcloud compute networks subnets list --network=default --filter="region:$Region AND purpose:REGIONAL_MANAGED_PROXY" --project=$ProjectId --format="value(name)" 2>$null)
    if (-not $proxySubnet) {
        Write-Live "Creating Regional Proxy-Only Subnet in $Region (10.125.0.0/24)..."
        gcloud compute networks subnets create proxy-only-subnet `
            --purpose=REGIONAL_MANAGED_PROXY `
            --role=ACTIVE `
            --region=$Region `
            --network=default `
            --range=10.125.0.0/24 `
            --project=$ProjectId --quiet
        Write-Success "Proxy-only subnet created."
    } else {
        Write-Info "Proxy-only subnet exists ($proxySubnet)."
    }

    # 3. GKE Base Cluster
    Write-Header "Step 4/7: GKE Base Cluster ($Zone)"
    $cList = (gcloud container clusters list --project $ProjectId --filter="name=$ClusterName AND location:$Zone" --format="value(name)" 2>$null)
    if ($cList -notcontains $ClusterName -and $cList -ne $ClusterName) {
        Write-Live "Creating GKE cluster '$ClusterName' in $Zone with Gateway API (HttpLoadBalancing) & GcsFuse..."
        gcloud container clusters create $ClusterName `
            --project $ProjectId `
            --zone $Zone `
            --node-locations $Zone `
            --release-channel regular `
            --machine-type e2-standard-4 `
            --num-nodes 1 `
            --workload-pool "${ProjectId}.svc.id.goog" `
            --addons="HttpLoadBalancing,GcsFuseCsiDriver" `
            --gateway-api=standard `
            --enable-ip-alias `
            --quiet
        if ($LASTEXITCODE -ne 0) { throw "Failed to create base cluster $ClusterName." }
        Write-Success "Base cluster created successfully."
    } else {
        Write-Info "Base cluster '$ClusterName' exists."
    }

    # Ensure base cluster is ready
    $cStatus = (gcloud container clusters describe $ClusterName --zone $Zone --project $ProjectId --format="value(status)" 2>$null)
    while ($cStatus -eq "PROVISIONING") {
        Write-Live "Cluster is PROVISIONING. Waiting for completion..."
        Start-Sleep -Seconds 15
        $cStatus = (gcloud container clusters describe $ClusterName --zone $Zone --project $ProjectId --format="value(status)" 2>$null)
    }

    # 4. TPU v6e Node Pool
    Write-Header "Step 5/7: Provisioning TPU v6e Trillium Node Pool ($MachineType)"
    $poolList = (gcloud container node-pools list --cluster $ClusterName --zone $Zone --project $ProjectId --format="value(name)" 2>$null)
    if ($poolList -notcontains "tpunodepool") {
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

    # 5. Gateway API Inference Extension CRDs & Workload Identity
    Write-Header "Step 6/7: Installing Inference Extension CRDs & Deploying Manifests"
    Write-Live "Installing Standard Gateway API CRDs & Inference Extension CRDs..."
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml
    kubectl apply -f "$PSScriptRoot/manifests/00-crds.yaml"

    $BucketName = "mevreon-tpu-model-weights"
    kubectl create serviceaccount vllm-ksa --namespace default --dry-run=client -o yaml | kubectl apply -f -
    gcloud storage buckets add-iam-policy-binding "gs://${BucketName}" `
        --member="principal://iam.googleapis.com/projects/${projectNumber}/locations/global/workloadIdentityPools/${ProjectId}.svc.id.goog/subject/ns/default/sa/vllm-ksa" `
        --role="roles/storage.objectUser" --quiet | Out-Null

    Write-Live "Deploying Gateway, llm-d EPP, TPU Model Server, InferencePool, HTTPRoute & Gradio..."
    kubectl apply -f "$PSScriptRoot/manifests/01-gateway.yaml"
    (Get-Content "$PSScriptRoot/manifests/02-vllm-tpu-modelserver.yaml" -Raw) -replace "bucketName:\s*GSBUCKET", "bucketName: $BucketName" | kubectl apply -f -
    kubectl apply -f "$PSScriptRoot/manifests/03-llmd-epp.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/04-inference-pool.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/05-http-route.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/06-inference-objective.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/07-gradio.yaml"

    # 6. Live Telemetry Dashboard
    Write-Header "Step 7/7: Live Telemetry & Model Readiness"
    Write-Host "Monitoring TPU Allocation, llm-d EPP, and Gateway External IP..." -ForegroundColor Yellow

    $ready = $false
    $timeout = 70
    $iter = 0

    while (-not $ready -and $iter -lt $timeout) {
        $iter++
        Start-Sleep -Seconds 5

        $nodes = (kubectl get nodes --no-headers 2>$null | Measure-Object).Count
        $vllmStatus = (kubectl get pods -l app=vllm-tpu-model-server -o jsonpath='{.items[0].status.phase}' 2>$null)
        $eppStatus = (kubectl get pods -l app=llm-d-epp -o jsonpath='{.items[0].status.phase}' 2>$null)
        $gatewayIp = (kubectl get gateway inference-gateway -o jsonpath='{.status.addresses[0].value}' 2>$null)

        Write-Host "[LIVE TELEMETRY] Nodes: $nodes | TPU Pod: $vllmStatus | llm-d EPP: $eppStatus | Gateway IP: $gatewayIp" -ForegroundColor Cyan

        if ($vllmStatus -eq "Running") {
            $cReady = (kubectl get pods -l app=vllm-tpu-model-server -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>$null)
            if ($cReady -eq "true") {
                $ready = $true
                Write-Success "TPU v6e Model Server & llm-d Endpoint Picker are 100% READY!"
                break
            }
        }
    }

    # Start Port Forwards for local access & Gradio
    Write-Info "Starting background port-forwarding..."
    $script:PortForwardJobs += Start-Job -ScriptBlock { while ($true) { kubectl port-forward service/gradio 8080:8080; Start-Sleep -Seconds 2 } }
    $script:PortForwardJobs += Start-Job -ScriptBlock { while ($true) { kubectl port-forward service/vllm-tpu-service 8000:8000; Start-Sleep -Seconds 2 } }
    Start-Sleep -Seconds 3

    $finalGatewayIp = (kubectl get gateway inference-gateway -o jsonpath='{.status.addresses[0].value}' 2>$null)

    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " 🚀 GKE INFERENCE GATEWAY (llm-d + TPU v6e) IS LIVE!" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    if ($finalGatewayIp) {
        Write-Host "  • External Gateway URL : http://$finalGatewayIp" -ForegroundColor Cyan
        Write-Host "  • Inference Endpoint   : http://$finalGatewayIp/v1/chat/completions" -ForegroundColor Cyan
    } else {
        Write-Host "  • Local Gateway Proxy  : http://localhost:8000" -ForegroundColor Cyan
    }
    Write-Host "  • Gradio Chat UI       : http://localhost:8080" -ForegroundColor Cyan
    Write-Host "  • EPP Scheduler Port   : 9090 (gRPC ext-proc)" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Green

    try { Start-Process "http://localhost:8080" } catch {}

    if ($AutoTestAndTeardown) {
        Write-Host "`n========================================================" -ForegroundColor Yellow
        Write-Host " 🧪 AUTOMATED INFERENCE VERIFICATION (-AutoTestAndTeardown)" -ForegroundColor Yellow
        Write-Host "========================================================" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        python "$PSScriptRoot/client/test_inference.py"
        Write-Success "Automated verification complete! Initiating automatic teardown..."
        return
    }

    if ($KeepClusterOnExit) {
        Write-Host "`n========================================================" -ForegroundColor Yellow
        Write-Host " 🧪 AUTOMATED INFERENCE VERIFICATION (-KeepClusterOnExit)" -ForegroundColor Yellow
        Write-Host "========================================================" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        python "$PSScriptRoot/client/test_inference.py"
        Write-Success "Automated verification complete! Cluster and demo are LIVE."
        Write-Host "Cluster and port-forwarding remain online for your demo." -ForegroundColor Green
        Write-Host "Run '.\cleanup.ps1' whenever you are ready to tear down and stop billing." -ForegroundColor Yellow
        return
    }

    Write-Host "`nInteractive Session:" -ForegroundColor Yellow
    Write-Host " [T] Run CLI benchmark test"
    Write-Host " [L] Tail live vLLM logs"
    Write-Host " [E] Tail llm-d EPP logs"
    Write-Host " [ENTER] STOP everything and automatically teardown all VMs"
    Write-Host ""

    $session = $true
    while ($session) {
        $u = Read-Host "Choice (T=Test / L=vLLM Logs / E=EPP Logs / Enter=Teardown & Stop Billing)"
        if ($u -eq 'T' -or $u -eq 't') {
            python "$PSScriptRoot/client/test_inference.py"
        } elseif ($u -eq 'L' -or $u -eq 'l') {
            kubectl logs -l app=vllm-tpu-model-server -c vllm-tpu --tail=50 -f
        } elseif ($u -eq 'E' -or $u -eq 'e') {
            kubectl logs -l app=llm-d-epp -c epp --tail=50 -f
        } else {
            $session = $false
        }
    }
} catch {
    Write-Host "`n[ERROR] $_" -ForegroundColor Red
} finally {
    Invoke-Teardown
}
