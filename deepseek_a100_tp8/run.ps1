# ==============================================================================
# End-to-End Launcher: DeepSeek FP8 on 8x NVIDIA A100 (80GB) Spot VM with TP=8
# Cost Protection: Uses SPOT VM (~$8.79/hr, ~70% discount) with auto-teardown support
# ==============================================================================

[CmdletBinding()]
param(
    [string]$ProjectId = "mevreon",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "deepseek-a100-spot",
    [string]$MachineType = "a2-ultragpu-8g",
    [string]$FirewallRule = "allow-deepseek-ports"
)

$ErrorActionPreference = "Continue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " DeepSeek-V4.1-Flash (FP8) on 8x A100 (80GB) Spot" -ForegroundColor Cyan
Write-Host " Tensor Parallelism: 8" -ForegroundColor Yellow
Write-Host " Monitoring:         Prometheus (Port 9090) + DCGM" -ForegroundColor Yellow
Write-Host " Project:            $ProjectId" -ForegroundColor Gray
Write-Host " Zone:               $Zone" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check GCloud Authentication
Write-Host "`n[1/6] Verifying Google Cloud Authentication..." -ForegroundColor Green
$activeAccount = gcloud config get-value account 2>$null
if (-not $activeAccount) {
    Write-Error "No active gcloud authentication found. Run 'gcloud auth login' first."
    exit 1
}
Write-Host "Authenticated as: $activeAccount" -ForegroundColor Gray

# 2. Configure Firewall Rule for vLLM, Gradio & Prometheus
Write-Host "`n[2/6] Configuring Firewall Rules for Ports 7860, 8000, 9090, 9400..." -ForegroundColor Green
$fwExists = (gcloud compute firewall-rules list --filter="name=$FirewallRule" --project=$ProjectId --format="value(name)")
if (-not $fwExists) {
    Write-Host "Creating firewall rule '$FirewallRule'..." -ForegroundColor Yellow
    gcloud compute firewall-rules create $FirewallRule `
        --project=$ProjectId `
        --direction=INGRESS `
        --priority=1000 `
        --network=default `
        --action=ALLOW `
        --rules="tcp:7860,tcp:8000,tcp:9090,tcp:9400" `
        --source-ranges="0.0.0.0/0" `
        --target-tags=deepseek-node `
        --quiet
} else {
    Write-Host "Firewall rule '$FirewallRule' already exists." -ForegroundColor Gray
}

# 3. Resolve Startup Script Path
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$StartupScriptPath = Join-Path $ScriptDir "startup-script.sh"

if (-not (Test-Path $StartupScriptPath)) {
    Write-Error "startup-script.sh not found in $ScriptDir"
    exit 1
}

# 4. Provision the Instance (with multi-zone availability fallback)
Write-Host "`n[3/6] Provisioning Instance '$InstanceName' ($MachineType)..." -ForegroundColor Green
Write-Host "Pricing model: Standard On-Demand (Instant Provisioning)" -ForegroundColor Yellow

$CandidateZones = @($Zone, "us-central1-c", "us-east4-c", "europe-west4-a") | Select-Object -Unique
$created = $false
$activeZone = $Zone

foreach ($z in $CandidateZones) {
    Write-Host "Checking capacity in zone: $z..." -ForegroundColor Yellow
    $vmExists = (gcloud compute instances list --filter="name=$InstanceName AND zone:($z)" --project=$ProjectId --format="value(name)" 2>$null)
    if ($vmExists) {
        Write-Host "Found existing instance '$InstanceName' in $z." -ForegroundColor Green
        $activeZone = $z
        $created = $true
        break
    }

    $createOutput = gcloud compute instances create $InstanceName `
        --project=$ProjectId `
        --zone=$z `
        --machine-type=$MachineType `
        --image-family=common-cu129-ubuntu-2204-nvidia-580 `
        --image-project=deeplearning-platform-release `
        --boot-disk-size=500GB `
        --boot-disk-type=pd-ssd `
        --metadata-from-file=startup-script="$StartupScriptPath" `
        --metadata="install-nvidia-driver=True" `
        --scopes=cloud-platform `
        --tags=deepseek-node `
        --quiet 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully provisioned instance '$InstanceName' in zone '$z'!" -ForegroundColor Green
        $activeZone = $z
        $created = $true
        break
    } else {
        Write-Host "Zone $z unavailable: $createOutput" -ForegroundColor Gray
    }
}

if (-not $created) {
    Write-Error "Could not find capacity in candidate zones: $($CandidateZones -join ', ')."
    exit 1
}


$Zone = $activeZone

# 5. Fetch VM External IP
Write-Host "`n[4/6] Retrieving External IP Address from $Zone..." -ForegroundColor Green
$externalIp = gcloud compute instances describe $InstanceName `
    --zone=$Zone `
    --project=$ProjectId `
    --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

Write-Host "External IP: $externalIp" -ForegroundColor Cyan


# 6. Wait for Engine Readiness
Write-Host "`n[5/6] Waiting for vLLM & Prometheus stack initialization..." -ForegroundColor Green
Write-Host "Bootstrap log is being written to /var/log/deepseek_startup.log on the VM." -ForegroundColor Gray
Write-Host "Model weights (~510 GB) mounting from gs://mevreon-deepseek-models..." -ForegroundColor Yellow

$ready = $false
$attempts = 0
$maxAttempts = 90

while (-not $ready -and $attempts -lt $maxAttempts) {
    Start-Sleep -Seconds 10
    $attempts++
    try {
        $resp = Invoke-WebRequest -Uri "http://${externalIp}:8000/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        Write-Host -NoNewline "."
    }
}

if (-not $ready) {
    Write-Host "`n[NOTE] Engine is still initializing weights across 8 GPUs." -ForegroundColor Yellow
    Write-Host "To view real-time bootstrap progress, run:" -ForegroundColor Gray
    Write-Host "  gcloud compute instances tail-serial-port-output $InstanceName --zone=$Zone --project=$ProjectId" -ForegroundColor Cyan
} else {
    Write-Host "`n`n[SUCCESS] DeepSeek-V4.1-Flash TP=8 is LIVE!" -ForegroundColor Green
}

# 7. Endpoint Summary & Next Steps
Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host " Access Endpoints:" -ForegroundColor Cyan
Write-Host "  - Gradio Chat UI:   http://${externalIp}:7860" -ForegroundColor Green
Write-Host "  - vLLM API:         http://${externalIp}:8000/v1" -ForegroundColor Yellow
Write-Host "  - Prometheus UI:    http://${externalIp}:9090" -ForegroundColor Yellow
Write-Host "  - vLLM Metrics:     http://${externalIp}:8000/metrics" -ForegroundColor Yellow
Write-Host "  - DCGM GPU Metrics: http://${externalIp}:9400/metrics" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan

Write-Host "`nTo launch the local Gradio Web UI with Prometheus telemetry:" -ForegroundColor Green
Write-Host "  python web_ui.py --host $externalIp" -ForegroundColor Cyan

Write-Host "`nTo run the CLI inference test:" -ForegroundColor Green
Write-Host "  python test_inference.py --host $externalIp" -ForegroundColor Cyan

Write-Host "`nWhen you are finished testing, STOP BILLING by running:" -ForegroundColor Red
Write-Host "  .\cleanup.ps1 -Zone $Zone" -ForegroundColor Red
Write-Host "==================================================" -ForegroundColor Cyan

