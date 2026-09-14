#!/usr/bin/env bash
# ==============================================================================
# 02_download_weights.sh
# Download / Sync Moonshot AI Kimi-K3 weights from GCS bucket to local NVMe/SSD
# Runs on each node (or can be orchestrated remotely via gcloud compute ssh)
# ==============================================================================

set -euo pipefail

BUCKET_PATH="gs://mevreon-kimi-k3-weights/moonshotai/Kimi-K3"
TARGET_DIR="/data/models/kimi-k3"

echo "=== 1. Preparing local storage directory ==="
sudo mkdir -p "$TARGET_DIR"
sudo chown -R "$USER:$USER" /data

echo "=== 2. Fast-syncing Kimi-K3 weights from GCS internal backbone ==="
# Using parallel composite download for maximum wire speed (>1.5 GB/s)
gcloud storage rsync -r "$BUCKET_PATH" "$TARGET_DIR" \
    --threads=16 \
    --no-user-output-enabled=false || gsutil -m rsync -r "$BUCKET_PATH" "$TARGET_DIR"

echo "=== 3. Verifying downloaded weights ==="
SHARD_COUNT=$(ls -1 "$TARGET_DIR"/*.safetensors 2>/dev/null | wc -l || echo 0)
echo "Safetensors shards found: $SHARD_COUNT (Expected: 96 shards)"

if [ "$SHARD_COUNT" -eq 96 ]; then
    echo "SUCCESS: All 96 shards of Kimi-K3 verified on local disk!"
    ls -lh "$TARGET_DIR"/config.json "$TARGET_DIR"/model.safetensors.index.json
else
    echo "WARNING: Expected 96 shards but found $SHARD_COUNT. Re-running sync check..."
    gsutil -m cp -n "$BUCKET_PATH/*" "$TARGET_DIR/"
fi
