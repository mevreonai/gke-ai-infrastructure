#!/bin/bash
set -ex

exec > >(tee -a /var/log/deepseek-transfer.log) 2>&1
echo "=== [$(date)] Starting DeepSeek-V4.1-Flash Cloud Ingestion Worker ==="

# 1. System packages
apt-get update -y
apt-get install -y python3-pip git-lfs curl

# 2. High-speed Hugging Face transfer accelerator
pip3 install --break-system-packages -U "huggingface_hub[cli,hf_transfer]"
export HF_HUB_ENABLE_HF_TRANSFER=1

DEST_DIR="/opt/models/DeepSeek-V4.1-Flash"
GCS_DEST="gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash"

mkdir -p "$DEST_DIR"

echo "=== [$(date)] Starting Hugging Face Download (510 GB) ==="
huggingface-cli download deepseek-ai/DeepSeek-V4.1-Flash \
    --local-dir "$DEST_DIR" \
    --local-dir-use-symlinks False

echo "=== [$(date)] Hugging Face Download Finished. Syncing to GCS: $GCS_DEST ==="
gcloud storage rsync -r "$DEST_DIR" "$GCS_DEST"

echo "=== [$(date)] Ingestion & Sync to GCS Completed Successfully! ==="

# 3. Clean up VM to prevent further billing
ZONE=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone | awk -F/ '{print $NF}')
NAME=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/name)

echo "=== [$(date)] Self-terminating worker VM $NAME in $ZONE to protect costs ==="
gcloud compute instances delete "$NAME" --zone="$ZONE" --quiet
