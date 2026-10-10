# ==============================================================================
# DEMO STEP 1: Provision 2x G4 RTX PRO 6000 Nodes (PowerShell for Windows)
# Usage:
#   .\01_provision_cluster.ps1
#   .\01_provision_cluster.ps1 -Node0Name "my-node-0" -Node1Name "my-node-1"
# ==============================================================================
param(
    [string]$Project = "mevreon",
    [string]$Zone = "us-central1-b",
    [string]$Node0Name = "rtx-demo-node-0",
    [string]$Node1Name = "rtx-demo-node-1"
)

$MACHINE_TYPE = "g4-standard-384"
$IMAGE = "rocky-linux-10-optimized-gcp-nvidia-580-v20260910"
$IMAGE_PROJECT = "rocky-linux-accelerator-cloud"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " [DEMO] Provisioning 2x 8-GPU RTX PRO 6000 Nodes in $Zone ($Project)" -ForegroundColor Cyan
Write-Host "   Node 0 Target Name : $Node0Name (Head Node)"
Write-Host "   Node 1 Target Name : $Node1Name (Worker Node)"
Write-Host "======================================================================" -ForegroundColor Cyan

Write-Host "--> Launching $Node0Name and $Node1Name simultaneously..." -ForegroundColor Yellow

$p0 = Start-Process gcloud -ArgumentList "compute instances create $Node0Name --project=$Project --zone=$Zone --machine-type=$MACHINE_TYPE --accelerator=count=8,type=nvidia-rtx-pro-6000 --boot-disk-size=1000GB --boot-disk-type=hyperdisk-balanced --image=$IMAGE --image-project=$IMAGE_PROJECT --provisioning-model=SPOT --instance-termination-action=STOP --tags=kimi-ray-node --scopes=cloud-platform" -PassThru -NoNewWindow
$p1 = Start-Process gcloud -ArgumentList "compute instances create $Node1Name --project=$Project --zone=$Zone --machine-type=$MACHINE_TYPE --accelerator=count=8,type=nvidia-rtx-pro-6000 --boot-disk-size=1000GB --boot-disk-type=hyperdisk-balanced --image=$IMAGE --image-project=$IMAGE_PROJECT --provisioning-model=SPOT --instance-termination-action=STOP --tags=kimi-ray-node --scopes=cloud-platform" -PassThru -NoNewWindow

$p0.WaitForExit()
$p1.WaitForExit()

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " [DEMO] Provisioning Request Finished! Fetching IP Addresses:" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green

gcloud compute instances list --project=$Project --filter="name:($Node0Name|$Node1Name)" `
    --format="table(name, zone, status, networkInterfaces[0].networkIP:label=INTERNAL_IP, networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
