#!/usr/bin/env bash
# ==============================================================================
# 01_provision_vm.sh
# Provision 8x NVIDIA H100 80GB SXM5 VM (a3-highgpu-8g) on Google Cloud Platform
# ==============================================================================

PROJECT="mevreon"
ZONE="us-central1-a"
VM_NAME="deepseek-h100"
DISK_NAME="deepseek-h100-disk"
DISK_SIZE="1000GB"
MACHINE_TYPE="a3-highgpu-8g"

echo "=== 1. Creating 1000GB Boot Disk from Snapshot ==="
# Option A: From existing snapshot (recommended for instant deployment)
# If snapshot exists:
SNAPSHOT_NAME="deepseek-weights-snapshot"
gcloud compute disks create "$DISK_NAME" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --type="hyperdisk-balanced" \
    --size="$DISK_SIZE" \
    --source-snapshot="$SNAPSHOT_NAME"

# Option B (Fresh from Scratch without snapshot):
# gcloud compute disks create "$DISK_NAME" \
#     --project="$PROJECT" \
#     --zone="$ZONE" \
#     --type="hyperdisk-balanced" \
#     --size="$DISK_SIZE" \
#     --image-family="ubuntu-2204-lts" \
#     --image-project="ubuntu-os-cloud"

echo "=== 2. Launching 8x H100 Spot VM ==="
gcloud compute instances create "$VM_NAME" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --provisioning-model="SPOT" \
    --instance-termination-action="STOP" \
    --disk="name=$DISK_NAME,boot=yes,auto-delete=no" \
    --tags="deepseek-node,http-server,https-server" \
    --maintenance-policy="TERMINATE" \
    --scopes="cloud-platform"

echo "=== 3. Ensuring Firewall Rule for Port 8000 ==="
gcloud compute firewall-rules create allow-deepseek-ports \
    --project="$PROJECT" \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:8000,tcp:7860 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=deepseek-node 2>/dev/null || echo "Firewall rule already exists."

echo "=== VM Provisioning Complete ==="
gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --format="table(name, status, networkInterfaces[0].accessConfigs[0].natIP)"
