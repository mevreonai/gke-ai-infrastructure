<#
.SYNOPSIS
    GKE Inference Gateway (llm-d + NVIDIA GPU) 1-Click Deployment & Testing.

.DESCRIPTION
    Provisions GKE Standard cluster with Gateway API (HttpLoadBalancing),
    NVIDIA GPU node pool (g2-standard-4 with 1x NVIDIA L4),
    Gateway API Inference Extension CRDs, llm-d Endpoint Picker (EPP),
    vLLM GPU Model Server (google/gemma-2-9b-it), and Gradio Chat UI.
    Provides complete isolation from any running TPU clusters.
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$Region = "europe-west4",
    [string]$Zone = "europe-west4-a",
    [string]$ClusterName = "inference-gateway-gpu-cluster",
    [string]$MachineType = "g2-standard-8",
    [string]$ModelId = "Qwen/Qwen2.5-7B-Instruct",
    [string]$HfToken = "",
    [switch]$KeepClusterOnExit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

function Write-Header([string]$title) {
    Write-Host "`n========================================================" -ForegroundColor Magenta
    Write-Host " 🎮 $title" -ForegroundColor Magenta
    Write-Host "========================================================" -ForegroundColor Magenta
}

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Gray }
function Write-Success([string]$msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Live([string]$msg) { Write-Host "  -> $msg" -ForegroundColor Cyan }

try {
    Write-Header "Step 1/6: Configuration & Pre-Flight (GPU Edition)"
    Write-Info "Project:     $ProjectId"
    Write-Info "Region:      $Region | Zone: $Zone"
    Write-Info "Cluster:     $ClusterName (GKE Gateway + llm-d + NVIDIA GPU)"
    Write-Info "GPU Machine: $MachineType (1x NVIDIA L4 GPU)"
    Write-Info "Model ID:    $ModelId"

    gcloud config set project $ProjectId --quiet
    gcloud config set compute/zone $Zone --quiet

    # 1. Enable APIs
    Write-Header "Step 2/6: Enabling GCP APIs"
    gcloud services enable container.googleapis.com storage.googleapis.com networkservices.googleapis.com compute.googleapis.com --project $ProjectId --quiet
    Write-Success "APIs verified and active."

    # 2. Regional Proxy-Only Subnet & Ingress Firewall
    Write-Header "Step 3/6: Regional Proxy Subnet & Firewall ($Region)"
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
    } else {
        Write-Info "Proxy-only subnet exists ($proxySubnet)."
    }

    $fw = (gcloud compute firewall-rules list --filter="name=allow-proxy-only-subnet" --project=$ProjectId --format="value(name)" 2>$null)
    if (-not $fw) {
        Write-Live "Creating firewall rule allow-proxy-only-subnet..."
        gcloud compute firewall-rules create allow-proxy-only-subnet `
            --network=default `
            --action=allow `
            --direction=ingress `
            --source-ranges=10.125.0.0/24 `
            --rules=all `
            --project=$ProjectId --quiet
    }

    # 3. GKE Base Cluster
    Write-Header "Step 4/6: Provisioning GKE Cluster ($ClusterName)"
    $cList = (gcloud container clusters list --project $ProjectId --filter="name=$ClusterName AND location:$Zone" --format="value(name)" 2>$null)
    if ($cList -notcontains $ClusterName -and $cList -ne $ClusterName) {
        Write-Live "Creating GKE cluster '$ClusterName' with Gateway API standard..."
        gcloud container clusters create $ClusterName `
            --project $ProjectId `
            --zone $Zone `
            --node-locations $Zone `
            --release-channel regular `
            --machine-type e2-standard-4 `
            --num-nodes 1 `
            --workload-pool "${ProjectId}.svc.id.goog" `
            --addons="HttpLoadBalancing" `
            --gateway-api=standard `
            --enable-ip-alias `
            --quiet
        if ($LASTEXITCODE -ne 0) { throw "Failed to create base cluster $ClusterName." }
        Write-Success "Base cluster created."
    } else {
        Write-Info "Base cluster '$ClusterName' exists."
    }

    # 4. NVIDIA GPU Node Pool
    Write-Header "Step 5/6: Provisioning NVIDIA GPU Node Pool ($MachineType)"
    $poolList = (gcloud container node-pools list --cluster $ClusterName --zone $Zone --project $ProjectId --format="value(name)" 2>$null)
    if ($poolList -notcontains "gpunodepool") {
        Write-Live "Creating GPU node pool 'gpunodepool' with $MachineType..."
        gcloud container node-pools create gpunodepool `
            --project $ProjectId `
            --cluster $ClusterName `
            --zone $Zone `
            --node-locations $Zone `
            --machine-type $MachineType `
            --accelerator="type=nvidia-l4,count=1" `
            --num-nodes 1 `
            --quiet
        if ($LASTEXITCODE -ne 0) { throw "Failed to create GPU node pool." }
        Write-Success "GPU node pool created."
    } else {
        Write-Info "GPU node pool 'gpunodepool' exists."
    }

    gcloud container clusters get-credentials $ClusterName --zone $Zone --project $ProjectId

    # 5. Hugging Face Secret (Required for gated Gemma 2 9B model weights)
    $tokenToUse = $HfToken
    if (-not $tokenToUse -and $env:HF_TOKEN) { $tokenToUse = $env:HF_TOKEN }
    if ($tokenToUse) {
        Write-Live "Configuring Hugging Face secret 'hf-secret'..."
        kubectl create secret generic hf-secret --from-literal=hf_api_token="$tokenToUse" --dry-run=client -o yaml | kubectl apply -f -
    } else {
        Write-Warn "No Hugging Face token specified. If google/gemma-2-9b-it fails to download, provide -HfToken 'hf_...' or `$env:HF_TOKEN."
    }

    # 6. Gateway API Inference Extension & Manifests
    Write-Header "Step 6/6: Deploying Gateway API Inference Extension & GPU Manifests"
    Write-Live "Installing Standard Gateway API & Inference Extension CRDs..."
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml
    kubectl apply -f "$PSScriptRoot/manifests/00-crds.yaml"

    Write-Live "Deploying Gateway, llm-d EPP, vLLM GPU Server, Route, HealthCheckPolicy, and Gradio..."
    kubectl apply -f "$PSScriptRoot/manifests/01-gateway.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/02-vllm-gpu-modelserver.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/03-llmd-epp.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/04-inference-pool.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/05-http-route.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/06-inference-objective.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/07-gradio.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/08-healthcheckpolicy.yaml"

    Write-Success "All GPU Inference Gateway resources deployed!"

    # Monitor Gateway IP & Gradio IP
    Write-Header "Waiting for External IPs & Model Readiness"
    Write-Live "Waiting for Gateway IP allocation..."
    $gwIp = ""
    for ($i = 0; $i -lt 30; $i++) {
        $gwIp = (kubectl get gateway inference-gateway-gpu -o jsonpath="{.status.addresses[0].value}" 2>$null)
        if ($gwIp -and $gwIp -ne "<no value>") { break }
        Start-Sleep -Seconds 5
    }

    $gradioIp = ""
    for ($i = 0; $i -lt 30; $i++) {
        $gradioIp = (kubectl get svc gradio-gpu -o jsonpath="{.status.loadBalancer.ingress[0].ip}" 2>$null)
        if ($gradioIp -and $gradioIp -ne "<no value>") { break }
        Start-Sleep -Seconds 5
    }

    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " 🎉 GPU INFERENCE GATEWAY DEPLOYMENT ACTIVE!" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    if ($gwIp) { Write-Success "Gateway External IP:   http://${gwIp}:80" }
    if ($gradioIp) { Write-Success "Gradio Chat Web UI:    http://${gradioIp}:8080" }
    Write-Host "========================================================`n" -ForegroundColor Green

} catch {
    Write-Host "[FATAL ERROR] $_" -ForegroundColor Red
}
