#!/usr/bin/env bash
# ==============================================================================
# DEMO STEP 1: Provision 2x G4 RTX PRO 6000 Nodes (Run on your Local Laptop/Cloud Shell)
# ==============================================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-mevreon}"
ZONE="${ZONE:-us-central1-b}"
MACHINE_TYPE="g4-standard-384"
IMAGE="rocky-linux-10-optimized-gcp-nvidia-580-v20260910"
IMAGE_PROJECT="rocky-linux-accelerator-cloud"

echo "======================================================================"
echo " [DEMO] Provisioning 2x 8-GPU RTX PRO 6000 Nodes in $ZONE ($PROJECT_ID)"
echo "======================================================================"

# Node 0 (Head Node)
echo "--> Launching rtx-demo-node-0..."
gcloud compute instances create rtx-demo-node-0 \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --accelerator="count=8,type=nvidia-rtx-pro-6000" \
    --boot-disk-size=1000GB \
    --boot-disk-type=hyperdisk-balanced \
    --image="$IMAGE" \
    --image-project="$IMAGE_PROJECT" \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --tags=kimi-ray-node --scopes=cloud-platform &

# Node 1 (Worker Node)
echo "--> Launching rtx-demo-node-1..."
gcloud compute instances create rtx-demo-node-1 \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --accelerator="count=8,type=nvidia-rtx-pro-6000" \
    --boot-disk-size=1000GB \
    --boot-disk-type=hyperdisk-balanced \
    --image="$IMAGE" \
    --image-project="$IMAGE_PROJECT" \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --tags=kimi-ray-node --scopes=cloud-platform &

wait

echo ""
echo "======================================================================"
echo " [DEMO] Both Nodes Provisioned Successfully!"
echo "======================================================================"
gcloud compute instances list --filter="name:rtx-demo-node" \
    --format="table(name, zone, status, networkInterfaces[0].networkIP:label=INTERNAL_IP, networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
