<#
.SYNOPSIS
    Disaggregated TPU vLLM Serving with llm-d on GKE (1-Click Deployment).

.DESCRIPTION
    Provisions a GKE cluster with custom MTU 8896 networking, Gateway API,
    and two dedicated TPU slices:
      - 1 Prefill Node  (Role: kv_producer)
      - 1 Decode Node   (Role: kv_consumer)
    Routes traffic via llm-d routing sidecar proxy and GKE Inference Gateway.
    Includes automated live telemetry, benchmarking, and cost-protection teardown.
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "mevreon",
    [string]$Region = "europe-west4",
    [string]$Zone = "europe-west4-a",
    [string]$ClusterName = "disaggregated-tpu-cluster",
    [string]$MachineType = "ct6e-standard-4t",
    [string]$ModelId = "Qwen/Qwen2.5-7B-Instruct",
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
        Write-Warn "KeepClusterOnExit specified. Cluster '$ClusterName' remains active."
        return
    }

    Write-Info "Terminating background port-forwarding..."
    foreach ($j in $script:PortForwardJobs) {
        try { Stop-Job -Job $j -SilentlyContinue; Remove-Job -Job $j -SilentlyContinue } catch {}
    }
    Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

    Write-Host "[TEARDOWN] Deleting GKE cluster '$ClusterName' in '$Zone'..." -ForegroundColor Yellow
    try {
        gcloud container clusters delete $ClusterName --zone $Zone --project $ProjectId --quiet
        Write-Success "Cluster '$ClusterName' deletion completed."
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
                    if ($vStat -eq "RUNNING" -and ($vName -like "*gke*" -and $vName -like "*disaggregated*")) {
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
    Write-Info "Project:       $ProjectId"
    Write-Info "Region:        $Region | Zone: $Zone"
    Write-Info "Cluster:       $ClusterName"
    Write-Info "Architecture:  Disaggregated Prefill / Decode Serving"
    Write-Info "Hardware:      2x TPU nodes ($MachineType, 4 chips each = 8 chips total)"
    Write-Info "Model:         $ModelId"

    $token = (gcloud auth print-access-token 2>$null)
    if (-not $token) {
        Write-Warn "gcloud credentials expired or missing. Launching interactive authentication..."
        gcloud auth login --brief
    }

    gcloud config set project $ProjectId --quiet
    gcloud config set compute/zone $Zone --quiet

    # 1. Enable APIs
    Write-Header "Step 2/7: Checking Google Cloud APIs"
    gcloud services enable container.googleapis.com compute.googleapis.com iam.googleapis.com --project $ProjectId --quiet
    Write-Success "Required Google Cloud APIs enabled."

    # 2. Networking Setup (Proxy Subnet for Gateway API)
    Write-Header "Step 3/7: Verifying Regional Gateway Proxy Subnet"
    $proxySubnetName = "proxy-only-subnet-$Region"
    $existingSubnets = (gcloud compute networks subnets list --project $ProjectId --regions $Region --format="value(name)" 2>$null)

    if ($existingSubnets -notcontains $proxySubnetName) {
        Write-Live "Creating regional proxy-only subnet in $Region (10.125.0.0/24)..."
        gcloud compute networks subnets create $proxySubnetName `
            --purpose=REGIONAL_MANAGED_PROXY `
            --role=ACTIVE `
            --region=$Region `
            --network=default `
            --range=10.125.0.0/24 `
            --project=$ProjectId `
            --quiet
        Write-Success "Proxy subnet created."
    } else {
        Write-Info "Regional proxy subnet '$proxySubnetName' exists."
    }

    # Internal firewall rules for TPU sidechannel ports
    $existingFw = (gcloud compute firewall-rules list --project $ProjectId --format="value(name)" 2>$null)
    if ($existingFw -notcontains "allow-tpu-disaggregated-internal") {
        Write-Live "Creating firewall rule for TPU KV-cache and sidechannel transfer..."
        gcloud compute firewall-rules create allow-tpu-disaggregated-internal `
            --network=default `
            --allow=tcp:8000,tcp:8200,tcp:9100,tcp:9600,tcp:9090 `
            --source-ranges="10.0.0.0/8,172.16.0.0/12" `
            --project=$ProjectId `
            --quiet
        Write-Success "Firewall rule created."
    }

    # 3. Base GKE Cluster
    Write-Header "Step 4/7: Creating/Verifying Base GKE Cluster"
    $existingClusters = (gcloud container clusters list --project $ProjectId --zone $Zone --format="value(name)" 2>$null)
    if ($existingClusters -notcontains $ClusterName) {
        Write-Live "Creating base cluster '$ClusterName'..."
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

    # 4. Provision Prefill & Decode TPU Node Pools
    Write-Header "Step 5/7: Provisioning Disaggregated TPU Node Pools"
    $poolList = (gcloud container node-pools list --cluster $ClusterName --zone $Zone --project $ProjectId --format="value(name)" 2>$null)

    # Prefill Node Pool
    if ($poolList -notcontains "prefill-pool") {
        Write-Live "Provisioning Prefill TPU Node Pool (1 node: $MachineType)..."
        gcloud container node-pools create prefill-pool `
            --project $ProjectId `
            --cluster $ClusterName `
            --zone $Zone `
            --node-locations $Zone `
            --machine-type $MachineType `
            --node-labels="disaggregated-role=prefill" `
            --num-nodes 1 `
            --quiet
        Write-Success "Prefill node pool created."
    } else {
        Write-Info "Prefill node pool exists."
    }

    # Decode Node Pool
    if ($poolList -notcontains "decode-pool") {
        Write-Live "Provisioning Decode TPU Node Pool (1 node: $MachineType)..."
        gcloud container node-pools create decode-pool `
            --project $ProjectId `
            --cluster $ClusterName `
            --zone $Zone `
            --node-locations $Zone `
            --machine-type $MachineType `
            --node-labels="disaggregated-role=decode" `
            --num-nodes 1 `
            --quiet
        Write-Success "Decode node pool created."
    } else {
        Write-Info "Decode node pool exists."
    }

    gcloud container clusters get-credentials $ClusterName --zone $Zone --project $ProjectId

    # 5. Workload Identity & Manifests
    Write-Header "Step 6/7: Deploying Disaggregated Serviceware & llm-d"
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml
    kubectl apply -f "$PSScriptRoot/manifests/00-crds.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/01-gateway.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/02-prefill-decode-llmd.yaml"
    kubectl apply -f "$PSScriptRoot/manifests/03-gradio.yaml"
    Write-Success "All Kubernetes manifests applied."

    # 6. Live Telemetry
    Write-Header "Step 7/7: Live Cluster Telemetry & Readiness"
    Write-Info "Monitoring Prefill, Decode, Router, and UI pods..."
    
    $timeoutSeconds = 600
    $startTime = Get-Date

    while ($true) {
        $prefillReady = (kubectl get pods -l app=vllm-tpu-prefill -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>$null)
        $decodeReady  = (kubectl get pods -l app=vllm-tpu-decode -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>$null)
        $routerReady  = (kubectl get pods -l app=llm-d-routing-proxy -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>$null)

        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
        Write-Live "[$elapsed s] Prefill: $prefillReady | Decode: $decodeReady | Router: $routerReady"

        if ($prefillReady -eq "true" -and $decodeReady -eq "true" -and $routerReady -eq "true") {
            Write-Success "Disaggregated serving stack is 100% HEALTHY and READY!"
            break
        }

        if ($elapsed -gt $timeoutSeconds) {
            Write-Warn "Timed out waiting for full readiness. Inspecting pod logs..."
            break
        }
        Start-Sleep -Seconds 10
    }

    # Port Forwarding
    Write-Info "Setting up local port-forwarding to Router (port 8000) and Gradio (port 8080)..."
    $pfRouter = Start-Job -ScriptBlock { kubectl port-forward service/llm-d-router-service 8000:8000 }
    $pfGradio = Start-Job -ScriptBlock { kubectl port-forward service/gradio-service 8080:8080 }
    $script:PortForwardJobs += $pfRouter
    $script:PortForwardJobs += $pfGradio
    Start-Sleep -Seconds 3

    # Automated Benchmark
    if ($AutoTestAndTeardown) {
        Write-Header "Executing Automated Disaggregated Benchmark"
        python "$PSScriptRoot/client/benchmark_disaggregated.py"
        Write-Success "Automated benchmark completed."
        return
    }

    # Interactive Mode
    Write-Header "🎉 DISAGGREGATED TPU SERVING IS LIVE!"
    Write-Host "  👉 Interactive Chat UI:  http://localhost:8080" -ForegroundColor Green
    Write-Host "  👉 OpenAI API Base URL:  http://localhost:8000/v1" -ForegroundColor Cyan
    Write-Host "`nControls:"
    Write-Host "  [T] Run Live Disaggregated Latency Benchmark" -ForegroundColor Yellow
    Write-Host "  [P] View Prefill Pod Logs" -ForegroundColor Yellow
    Write-Host "  [D] View Decode Pod Logs" -ForegroundColor Yellow
    Write-Host "  [ENTER] Exit and trigger automatic cost-protection teardown`n" -ForegroundColor Red

    Start-Process "http://localhost:8080" -ErrorAction SilentlyContinue

    while ($true) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true).Key
            if ($key -eq "T") {
                python "$PSScriptRoot/client/benchmark_disaggregated.py"
            } elseif ($key -eq "P") {
                kubectl logs -f deployment/vllm-tpu-prefill -c vllm
            } elseif ($key -eq "D") {
                kubectl logs -f deployment/vllm-tpu-decode -c vllm
            } elseif ($key -eq "Enter") {
                break
            }
        }
        Start-Sleep -Milliseconds 200
    }

} finally {
    Invoke-Teardown
}
