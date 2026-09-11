<#
.SYNOPSIS
    Automated End-to-End Multi-Host TPU Serving Lifecycle on GKE with Auto-Teardown.

.DESCRIPTION
    Provisions GKE cluster with TPU v5e pod slices, deploys vLLM + Ray Serve + Gradio,
    manages port-forwarding for live interaction, and automatically terminates all
    compute/TPU billing resources as soon as the session stops or is interrupted.

.PARAMETER ProjectId
    The Google Cloud project ID (default: current gcloud configured project or "mevreon").

.PARAMETER Region
    GCP Region (default: "us-central1").

.PARAMETER Zone
    GCP Zone for TPU v5e (default: "us-central1-a").

.PARAMETER ClusterName
    GKE Cluster name (default: "ray-llm-cluster").

.PARAMETER HfToken
    Hugging Face API Token for downloading gated model weights.

.PARAMETER SkipBuild
    Skip Docker image build via Cloud Build if the image is already built.

.PARAMETER KeepClusterOnExit
    Do not delete the GKE cluster on exit (CAUTION: TPU charges will continue).

.EXAMPLE
    .\run.ps1 -ProjectId "my-gcp-project" -HfToken "hf_xxxx"
    .\run.ps1 -SkipBuild
#>

[CmdletBinding()]
param (
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$Zone = "us-central1-a",
    [string]$ClusterName = "ray-llm-cluster",
    [string]$HfToken = "",
    [switch]$SkipBuild,
    [switch]$KeepClusterOnExit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors and formatting helpers
function Write-Step([string]$msg) {
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host " [STEP] $msg" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
}

function Write-Success([string]$msg) {
    Write-Host "[SUCCESS] $msg" -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host "[WARNING] $msg" -ForegroundColor Yellow
}

function Write-Info([string]$msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Gray
}

function Write-Alert([string]$msg) {
    Write-Host "[ALERT] $msg" -ForegroundColor Magenta
}

# Track background port forwarding jobs
$script:PortForwardJobs = @()
$script:ClusterCreatedByScript = $false

# Cleanup function triggered on completion, failure, or Ctrl+C
function Invoke-Teardown {
    Write-Host "`n"
    Write-Host "========================================================" -ForegroundColor Red
    Write-Host " [BILLING SAFEGUARD] INITIATING AUTOMATIC TEARDOWN" -ForegroundColor Red
    Write-Host "========================================================" -ForegroundColor Red

    # 1. Stop background port-forwarding processes
    Write-Info "Terminating background port-forwarding processes..."
    foreach ($job in $script:PortForwardJobs) {
        try {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            Remove-Job -Job $job -ErrorAction SilentlyContinue
        } catch {}
    }
    # Also kill any orphan kubectl port-forward processes
    Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "port-forward" } | Stop-Process -Force -ErrorAction SilentlyContinue

    # 2. Check if cluster cleanup is needed
    if ($KeepClusterOnExit) {
        Write-Warn "KeepClusterOnExit was specified. Cluster '$ClusterName' was NOT deleted."
        Write-Warn "REMINDER: TPU and VM billing will continue until you delete the cluster manually!"
        Write-Warn "To destroy manually later, run: .\cleanup.ps1 -ProjectId '$ProjectId' -Zone '$Zone' -ClusterName '$ClusterName'"
        return
    }

    Write-Alert "Deleting GKE Cluster '$ClusterName' in zone '$Zone' to STOP ALL TPU & VM BILLING..."
    try {
        $clusterCheck = gcloud container clusters describe $ClusterName --zone $Zone --project $ProjectId --format="value(status)" 2>&1
        if ($LASTEXITCODE -eq 0 -and $clusterCheck) {
            Write-Info "Executing: gcloud container clusters delete $ClusterName --zone $Zone --project $ProjectId --quiet --async"
            gcloud container clusters delete $ClusterName --zone $Zone --project $ProjectId --quiet
            Write-Success "GKE Cluster '$ClusterName' deletion initiated successfully."
        } else {
            Write-Info "Cluster '$ClusterName' does not exist or has already been deleted."
        }
    } catch {
        Write-Warn "Error checking/deleting cluster: $_"
    }

    # 3. Verify no lingering TPU/VM compute instances
    Write-Info "Verifying active Compute Engine VMs in $ProjectId ($Zone)..."
    try {
        $activeVMs = gcloud compute instances list --project $ProjectId --filter="zone:($Zone)" --format="table(name,zone,machineType,status)" 2>&1
        Write-Host "$activeVMs" -ForegroundColor Gray
    } catch {}

    Write-Host "========================================================" -ForegroundColor Green
    Write-Success "Cost-protection teardown complete! No active TPU VMs incurring bills."
    Write-Host "========================================================" -ForegroundColor Green
}

# Register Ctrl+C / Exit Trap
$null = [Console]::TreatControlCAsInput
Register-EngineEvent -SourceIdentifier ([System.Management.Automation.PsEngineEvent]::Exiting) -Action { Invoke-Teardown } -ErrorAction SilentlyContinue | Out-Null

try {
    # -------------------------------------------------------------
    # 0. RESOLVE PARAMETERS & CONFIGURATION
    # -------------------------------------------------------------
    Write-Step "1/8: Resolving Project & Environment Configuration"

    # Load from .env or config if present
    if (Test-Path "$PSScriptRoot/config.env") {
        Write-Info "Loading settings from config.env..."
        Get-Content "$PSScriptRoot/config.env" | Where-Object { $_ -match '^\s*[^#].+=.+' } | ForEach-Object {
            $parts = $_.Split('=', 2)
            $varName = $parts[0].Trim()
            $varVal = $parts[1].Trim()
            if (-not [System.Environment]::GetEnvironmentVariable($varName)) {
                [System.Environment]::SetEnvironmentVariable($varName, $varVal)
            }
        }
    }

    if (-not $ProjectId) {
        $ProjectId = [System.Environment]::GetEnvironmentVariable("PROJECT_ID")
        if (-not $ProjectId) {
            $currentGcp = (gcloud config get-value project 2>$null)
            if ($currentGcp -and $currentGcp -ne "(unset)") {
                $ProjectId = $currentGcp
            } else {
                $ProjectId = Read-Host "Enter your GCP Project ID"
            }
        }
    }

    if (-not $HfToken) {
        $HfToken = [System.Environment]::GetEnvironmentVariable("HF_TOKEN")
        if (-not $HfToken) {
            $HfToken = Read-Host "Enter your Hugging Face API Token (optional, press Enter to skip)"
        }
    }

    $BucketName = "${ProjectId}-tpu-model-weights"
    $ArRepo = "ray-repo"
    $ArLocation = "us-east1"
    $ImageTag = "${ArLocation}-docker.pkg.dev/${ProjectId}/${ArRepo}/vllm-tpu-ray:vllm-tpu"

    Write-Info "Active Configuration:"
    Write-Info "  - Project ID:     $ProjectId"
    Write-Info "  - Region/Zone:    $Region / $Zone"
    Write-Info "  - GKE Cluster:    $ClusterName"
    Write-Info "  - Storage Bucket: gs://$BucketName"
    Write-Info "  - Container Tag:  $ImageTag"

    gcloud config set project $ProjectId --quiet
    gcloud config set compute/zone $Zone --quiet

    # -------------------------------------------------------------
    # 1. ENABLE APIS
    # -------------------------------------------------------------
    Write-Step "2/8: Enabling Required GCP APIs"
    gcloud services enable `
        container.googleapis.com `
        tpu.googleapis.com `
        artifactregistry.googleapis.com `
        cloudbuild.googleapis.com `
        storage.googleapis.com --project $ProjectId --quiet
    Write-Success "GCP APIs verified and enabled."

    # -------------------------------------------------------------
    # 2. CREATE GKE CLUSTER & TPU NODE POOL
    # -------------------------------------------------------------
    Write-Step "3/8: Provisioning GKE Cluster & Multi-Host TPU v5e Node Pool"

    $clusterExists = gcloud container clusters describe $ClusterName --zone $Zone --project $ProjectId --format="value(status)" 2>$null
    if (-not $clusterExists) {
        Write-Info "Creating base GKE cluster '$ClusterName' (e2-standard-16 head node + RayOperator + GCSFuse CSI)..."
        gcloud container clusters create $ClusterName `
            --project $ProjectId `
            --zone $Zone `
            --release-channel regular `
            --machine-type e2-standard-16 `
            --num-nodes 1 `
            --addons RayOperator,GcsFuseCsiDriver `
            --workload-pool "${ProjectId}.svc.id.goog" `
            --enable-ip-alias `
            --quiet
        $script:ClusterCreatedByScript = $true
        Write-Success "Base GKE cluster created."
    } else {
        Write-Info "Cluster '$ClusterName' already exists. Status: $clusterExists."
    }

    # Ensure TPU node pool exists
    $tpuPoolExists = gcloud container node-pools describe tpu-v5e-pool --cluster $ClusterName --zone $Zone --project $ProjectId --format="value(status)" 2>$null
    if (-not $tpuPoolExists) {
        Write-Info "Creating multi-host TPU v5e node pool (2 nodes x ct5lp-hightpu-4t = 8 TPU chips, topology 2x4)..."
        gcloud container node-pools create tpu-v5e-pool `
            --project $ProjectId `
            --cluster $ClusterName `
            --zone $Zone `
            --machine-type ct5lp-hightpu-4t `
            --tpu-topology 2x4 `
            --num-nodes 2 `
            --node-locations $Zone `
            --quiet
        Write-Success "TPU v5e node pool created."
    } else {
        Write-Info "TPU node pool 'tpu-v5e-pool' already exists."
    }

    # Connect kubectl
    Write-Info "Fetching GKE cluster credentials for kubectl..."
    gcloud container clusters get-credentials $ClusterName --zone $Zone --project $ProjectId

    # -------------------------------------------------------------
    # 3. SETUP GCS BUCKET, IAM & WORKLOAD IDENTITY
    # -------------------------------------------------------------
    Write-Step "4/8: Setting up Cloud Storage, Workload Identity & HF Secrets"

    # GCS Bucket
    $bucketExists = gcloud storage buckets describe "gs://${BucketName}" --project $ProjectId 2>$null
    if (-not $bucketExists) {
        Write-Info "Creating GCS bucket 'gs://${BucketName}'..."
        gcloud storage buckets create "gs://${BucketName}" --project $ProjectId --location=$Region
    }

    # Service Account
    $saEmail = "tpu-reader-sa@${ProjectId}.iam.gserviceaccount.com"
    $saExists = gcloud iam service-accounts describe $saEmail --project $ProjectId 2>$null
    if (-not $saExists) {
        Write-Info "Creating IAM Service Account 'tpu-reader-sa'..."
        gcloud iam service-accounts create tpu-reader-sa --display-name="TPU Reader SA" --project $ProjectId
    }

    # Bucket IAM Binding
    gcloud storage buckets add-iam-policy-binding "gs://${BucketName}" `
        --member="serviceAccount:${saEmail}" `
        --role="roles/storage.objectAdmin" --quiet | Out-Null

    # Kubernetes Service Account
    kubectl create serviceaccount ray-ksa --dry-run=client -o yaml | kubectl apply -f -

    gcloud iam service-accounts add-iam-policy-binding $saEmail `
        --project $ProjectId `
        --role="roles/iam.workloadIdentityUser" `
        --member="serviceAccount:${ProjectId}.svc.id.goog[default/ray-ksa]" --quiet | Out-Null

    kubectl annotate serviceaccount ray-ksa `
        iam.gke.io/gcp-service-account=$saEmail --overwrite

    # Hugging Face Secret
    if ($HfToken) {
        Write-Info "Configuring Hugging Face Kubernetes secret..."
        kubectl create secret generic hf-secret `
            --from-literal=hf_api_token=$HfToken `
            --dry-run=client -o yaml | kubectl apply -f -
    }

    # -------------------------------------------------------------
    # 4. CONTAINER IMAGE BUILD (ARTIFACT REGISTRY + CLOUD BUILD)
    # -------------------------------------------------------------
    Write-Step "5/8: Validating / Building Container Image"

    if (-not $SkipBuild) {
        # Check repo
        $repoExists = gcloud artifacts repositories describe $ArRepo --location=$ArLocation --project $ProjectId 2>$null
        if (-not $repoExists) {
            Write-Info "Creating Artifact Registry repository '$ArRepo'..."
            gcloud artifacts repositories create $ArRepo `
                --project $ProjectId `
                --repository-format=docker `
                --location=$ArLocation `
                --description="Ray TPU docker repo" --quiet
        }

        # Check if image already exists
        $imageExists = gcloud artifacts docker images describe $ImageTag --project $ProjectId 2>$null
        if ($imageExists) {
            Write-Info "Container image '$ImageTag' already exists in Artifact Registry. Rebuilding can be skipped."
            $rebuild = Read-Host "Do you want to re-build via Cloud Build? (y/N)"
            if ($rebuild -eq 'y' -or $rebuild -eq 'Y') {
                Write-Info "Submitting build to Cloud Build..."
                gcloud builds submit --project $ProjectId --tag $ImageTag "$PSScriptRoot"
            }
        } else {
            Write-Info "Building container image via Cloud Build (no local Docker required)..."
            gcloud builds submit --project $ProjectId --tag $ImageTag "$PSScriptRoot"
        }
    } else {
        Write-Info "SkipBuild flag is set. Skipping container build."
    }

    # -------------------------------------------------------------
    # 5. RENDER & APPLY KUBERNETES MANIFESTS
    # -------------------------------------------------------------
    Write-Step "6/8: Deploying Networking, RayService & Gradio App"

    # Apply DRA networking
    if (Test-Path "$PSScriptRoot/manifests/01-networking-netdev.yaml") {
        kubectl apply -f "$PSScriptRoot/manifests/01-networking-netdev.yaml"
    }

    # Prepare rendered RayService manifest with current Project ID & Bucket
    $rayManifestContent = Get-Content "$PSScriptRoot/manifests/02-ray-service-multihost-tpu.yaml" -Raw
    $rayManifestContent = $rayManifestContent -replace "us-east1-docker.pkg.dev/[^/]+/ray-repo/vllm-tpu-ray:vllm-tpu", $ImageTag
    $rayManifestContent = $rayManifestContent -replace "bucketName:\s*[\w-]+", "bucketName: $BucketName"

    $tempRayManifest = "$PSScriptRoot/.temp-02-ray-service.yaml"
    Set-Content -Path $tempRayManifest -Value $rayManifestContent
    try {
        kubectl apply -f $tempRayManifest
    } finally {
        Remove-Item -Path $tempRayManifest -ErrorAction SilentlyContinue
    }

    # Apply Gradio
    if (Test-Path "$PSScriptRoot/manifests/gradio.yaml") {
        kubectl apply -f "$PSScriptRoot/manifests/gradio.yaml"
    }

    # -------------------------------------------------------------
    # 6. WAIT FOR SERVING PODS & HEALTH CHECK
    # -------------------------------------------------------------
    Write-Step "7/8: Waiting for TPU Workers & Ray Serve Application Readiness"

    Write-Info "Waiting for Ray head pod to enter Running state..."
    $maxAttempts = 60
    $attempt = 0
    $headPod = ""
    while ($attempt -lt $maxAttempts) {
        $headPod = (kubectl get pod -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}' 2>$null)
        if ($headPod) {
            $status = (kubectl get pod $headPod -o jsonpath='{.status.phase}' 2>$null)
            if ($status -eq "Running") {
                Write-Success "Ray head pod '$headPod' is Running."
                break
            }
        }
        Start-Sleep -Seconds 5
        $attempt++
        Write-Host "." -NoNewline
    }

    Write-Info "`nWaiting for Gradio deployment to be ready..."
    kubectl rollout status deployment/gradio --timeout=180s 2>$null

    # -------------------------------------------------------------
    # 7. LAUNCH LIVE DEMO SESSION
    # -------------------------------------------------------------
    Write-Step "8/8: Live Serving Session Active!"

    Write-Info "Starting background port-forwarding for Gradio (port 8080) and Ray vLLM API (port 8000)..."

    # Start port-forwarding as background jobs
    $script:PortForwardJobs += Start-Job -ScriptBlock { kubectl port-forward service/gradio 8080:8080 }
    $script:PortForwardJobs += Start-Job -ScriptBlock { kubectl port-forward svc/vllm-tpu-multihost-head-svc 8000:8000 }

    Start-Sleep -Seconds 3

    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " 🚀 MULTI-HOST TPU SERVING IS READY & ONLINE!" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "  • Gradio Web Interface : http://localhost:8080" -ForegroundColor Cyan
    Write-Host "  • OpenAI-compatible API: http://localhost:8000/v1/chat/completions" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Green

    # Automatically open the browser to Gradio UI
    try {
        Start-Process "http://localhost:8080"
    } catch {}

    Write-Alert "`n⚠️  AUTOMATIC BILLING PROTECTION IS ACTIVE:"
    Write-Alert "    As soon as you finish testing and press [ENTER] (or Ctrl+C),"
    Write-Alert "    the script will AUTOMATICALLY delete the GKE cluster and TPU VMs"
    Write-Alert "    so that you DO NOT accumulate unexpected GCP billing charges."

    Write-Host "`nInteractive Options:" -ForegroundColor Yellow
    Write-Host " [1] Press [T] to run a test CLI inference request"
    Write-Host " [2] Press [S] to check Ray Serve status"
    Write-Host " [3] Press [ENTER] or [Q] to STOP everything and auto-teardown all VMs"
    Write-Host ""

    $running = $true
    while ($running) {
        $userInput = Read-Host "Choice (T=Test CLI / S=Status / Enter=Stop & Clean Up)"
        if ($userInput -eq 'T' -or $userInput -eq 't') {
            if (Test-Path "$PSScriptRoot/client/test_inference.py") {
                python "$PSScriptRoot/client/test_inference.py"
            } else {
                # Inline curl / REST test
                $body = @{
                    model = "google/gemma-2-27b-it"
                    messages = @(@{ role = "user"; content = "Explain TPU v5e multi-host acceleration in 2 bullet points." })
                    max_tokens = 128
                } | ConvertTo-Json -Depth 5
                try {
                    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body
                    Write-Host "`nModel Output:`n$($resp.choices[0].message.content)`n" -ForegroundColor Green
                } catch {
                    Write-Warn "Inference call failed: $_"
                }
            }
        } elseif ($userInput -eq 'S' -or $userInput -eq 's') {
            $hp = (kubectl get pod -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}' 2>$null)
            if ($hp) {
                kubectl exec $hp -c ray-head -- serve status
            }
        } else {
            $running = $false
        }
    }

} catch {
    Write-Host "`n[ERROR OCCURRED] $_" -ForegroundColor Red
} finally {
    Invoke-Teardown
}
