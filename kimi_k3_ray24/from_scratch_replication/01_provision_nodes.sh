#!/usr/bin/env bash
# ==============================================================================
# 01_provision_nodes.sh
# Provision 3x Multi-GPU Nodes with 8x NVIDIA RTX Pro 6000 (24 GPUs total)
# for Moonshot AI Kimi-K3 inference on Google Cloud Platform
# ==============================================================================

set -euo pipefail

PROJECT="${GCP_PROJECT:-mevreon}"
MACHINE_TYPE="g4-standard-384"
ACCELERATOR_TYPE="nvidia-rtx-pro-6000"
ACCELERATOR_COUNT=8
DISK_SIZE="2000GB"
DISK_TYPE="hyperdisk-balanced"

# Topology: 2 nodes in us-central1-b, 1 node in us-west1-a
NODE_CONFIGS=(
    "kimi-node-0:us-central1-b"
    "kimi-node-1:us-central1-b"
    "kimi-node-2:us-west1-a"
)

echo "======================================================================"
echo " Starting Provisioning of 3 Nodes (24x RTX Pro 6000 GPUs)"
echo " Project:      $PROJECT"
echo " Machine Type: $MACHINE_TYPE"
echo " Accelerators: 8x $ACCELERATOR_TYPE per node (24 total)"
echo " Storage:      $DISK_SIZE ($DISK_TYPE) per node"
echo "======================================================================"

# Step 1: Ensure Firewall Rules for Ray (6379, 8265, 10001-19999) and vLLM (8000)
echo "=== Step 1: Ensuring VPC Firewall Rules for Ray & vLLM ==="
gcloud compute firewall-rules create allow-kimi-ray-cluster \
    --project="$PROJECT" \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:6379,tcp:8265,tcp:8000,tcp:10000-19999,udp:10000-19999 \
    --source-ranges=10.128.0.0/9,10.138.0.0/16,0.0.0.0/0 \
    --target-tags=kimi-ray-node 2>/dev/null || echo "Firewall rule already exists."

# Step 2: Provision the 3 Nodes
echo "=== Step 2: Creating Disks and Launching Instances ==="

for ENTRY in "${NODE_CONFIGS[@]}"; do
    IFS=":" read -r NODE ZONE <<< "$ENTRY"
    echo "--- Launching $NODE in $ZONE ---"
    gcloud compute instances create "$NODE" \
        --project="$PROJECT" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --accelerator="count=$ACCELERATOR_COUNT,type=$ACCELERATOR_TYPE" \
        --boot-disk-size="100GB" \
        --boot-disk-type="pd-balanced" \
        --image-family="common-cu124-debian-11" \
        --image-project="ml-images" \
        --create-disk="name=${NODE}-data,size=$DISK_SIZE,type=$DISK_TYPE,auto-delete=no" \
        --provisioning-model="SPOT" \
        --instance-termination-action="STOP" \
        --maintenance-policy="TERMINATE" \
        --tags="kimi-ray-node,http-server,https-server" \
        --scopes="cloud-platform" &
done

wait

echo "======================================================================"
echo " All 3 Nodes Provisioned Successfully!"
echo "======================================================================"
gcloud compute instances list \
    --project="$PROJECT" \
    --filter="name ~ kimi-node" \
    --format="table(name, zone, status, networkInterfaces[0].networkIP:label=INTERNAL_IP, networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
