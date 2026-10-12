#!/usr/bin/env bash
# ==============================================================================
# 05_manage_vm.sh
# Start or stop the 8x H100 VM to control cloud billing
# Usage:
#   ./05_manage_vm.sh start
#   ./05_manage_vm.sh stop
# ==============================================================================

PROJECT="mevreon"
ZONE="us-central1-a"
VM_NAME="deepseek-h100"

ACTION="$1"

if [ "$ACTION" == "start" ]; then
    echo "Starting $VM_NAME in $ZONE..."
    gcloud compute instances start "$VM_NAME" --zone="$ZONE" --project="$PROJECT"
    echo "Getting external IP..."
    gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --project="$PROJECT" \
        --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
elif [ "$ACTION" == "stop" ]; then
    echo "Stopping $VM_NAME in $ZONE (discarding local scratch SSD to freeze billing)..."
    gcloud compute instances stop "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --discard-local-ssd=true
    echo "Instance stopped."
else
    echo "Usage: $0 [start|stop]"
    exit 1
fi
