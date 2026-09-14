# ==============================================================================
# cluster.ps1 - Automated Management for Kimi-K3 24-GPU Cluster
#
# Usage:
#   .\cluster.ps1 start   - Power ON all 3 nodes (Ray & vLLM boot automatically)
#   .\cluster.ps1 status  - Inspect VM states, Ray 24-GPU topology, & API endpoint
#   .\cluster.ps1 logs    - Stream real-time model loading logs (Ctrl+C to exit)
#   .\cluster.ps1 query   - Send a live completion query to the 24-GPU model
#   .\cluster.ps1 stop    - Power OFF all 3 nodes to pause compute billing
# ==============================================================================

param (
    [Parameter(Position=0)]
    [ValidateSet("start", "status", "logs", "query", "stop")]
    [string]$Action = "status"
)

$PROJECT = "mevreon"
$NODES = @(
    @{ Name = "kimi-node-0"; Zone = "us-central1-b"; Role = "Head Node (vLLM API Port 8000)"; InternalIP = "10.128.0.39" },
    @{ Name = "kimi-node-1"; Zone = "us-central1-b"; Role = "Worker Node 1 (8 GPUs)";         InternalIP = "10.128.0.40" },
    @{ Name = "kimi-node-2"; Zone = "us-west1-a";   Role = "Worker Node 2 (8 GPUs)";         InternalIP = "10.138.0.3" }
)

switch ($Action) {
    "start" {
        Write-Host "`n========================================================" -ForegroundColor Cyan
        Write-Host " Starting Kimi-K3 Distributed Cluster (24x RTX 6000 Pro)" -ForegroundColor Cyan
        Write-Host "========================================================" -ForegroundColor Cyan
        foreach ($node in $NODES) {
            $success = $false
            $attempt = 1
            while (-not $success) {
                Write-Host ">> Starting $($node.Name) ($($node.Role)) in $($node.Zone)..."
                gcloud compute instances start $($node.Name) --zone=$($node.Zone) --project=$PROJECT --quiet
                if ($LASTEXITCODE -eq 0) {
                    $success = $true
                    Write-Host "   [OK] $($node.Name) is RUNNING!" -ForegroundColor Green
                } else {
                    Write-Host "   [!] Zone capacity lock. Retrying in 10s (Attempt $attempt)..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 10
                    $attempt++
                }
            }
        }
        Write-Host "`n========================================================" -ForegroundColor Green
        Write-Host " Auto-Boot Sequence Initialized" -ForegroundColor Green
        Write-Host " - Ray Cluster and vLLM are automatically launching via systemd." -ForegroundColor Green
        Write-Host " - To watch weight loading: .\cluster.ps1 logs" -ForegroundColor Yellow
        Write-Host " - To test the endpoint:     .\cluster.ps1 query" -ForegroundColor Yellow
        Write-Host "========================================================`n" -ForegroundColor Green
    }

    "status" {
        Write-Host "`n=== [1/3] Compute Engine VM Status ===" -ForegroundColor Cyan
        gcloud compute instances list --project=$PROJECT --filter="name ~ kimi-node" --format="table(name, zone, status, machineType.basename(), networkInterfaces[0].networkIP:label=INTERNAL_IP, networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
        
        Write-Host "`n=== [2/3] Ray 24-GPU Cluster Health ===" -ForegroundColor Cyan
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project=$PROJECT --command="docker exec ray-head ray status 2>/dev/null || echo 'Ray cluster container starting up...'"
        
        Write-Host "`n=== [3/3] vLLM Inference API Server (Port 8000) ===" -ForegroundColor Cyan
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project=$PROJECT --command="curl -s http://localhost:8000/v1/models 2>/dev/null || echo 'vLLM is currently loading weights into GPUs (Port 8000 not yet open)'"
    }

    "logs" {
        Write-Host "`n=== Streaming Live Loading Logs (Ctrl+C to exit) ===" -ForegroundColor Cyan
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project=$PROJECT --command="docker exec ray-head bash -c 'tail -f `$(ls -S /tmp/ray/session_latest/logs/worker-*.err | head -n 1)'"
    }

    "query" {
        Write-Host "`n=== Querying Kimi-K3 (24 GPUs) ===" -ForegroundColor Cyan
        $prompt = "Explain quantum computing and why 24 GPUs are needed for 1.45 TB MoE models in 2 concise sentences."
        Write-Host "Prompt: $prompt`n" -ForegroundColor Yellow
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project=$PROJECT --command="curl -s -X POST http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\": \"moonshotai/Kimi-K3\", \"messages\": [{\"role\": \"system\", \"content\": \"You are Moonshot AI Kimi-K3 running on a 24-GPU cluster.\"}, {\"role\": \"user\", \"content\": \"$prompt\"}], \"max_tokens\": 120, \"temperature\": 0.6}' | jq ."
    }

    "stop" {
        Write-Host "`n=== Stopping Cluster Nodes (Pausing Billing) ===" -ForegroundColor Cyan
        foreach ($node in $NODES) {
            Write-Host ">> Powering off $($node.Name)..."
            gcloud compute instances stop $($node.Name) --zone=$($node.Zone) --project=$PROJECT --quiet
        }
        Write-Host "`nAll 3 nodes stopped. GPU billing paused. Model disks preserved." -ForegroundColor Green
    }
}
