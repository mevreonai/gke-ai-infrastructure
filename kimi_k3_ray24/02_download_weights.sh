#!/usr/bin/env bash
# ==============================================================================
# 02_download_weights.sh
# Download / Sync Moonshot AI Kimi-K3 weights (1.45 TB, 96 shards) to local NVMe
# Supports both Hugging Face Hub (HF Transfer) and GCS Bucket Sync
# ==============================================================================

set -euo pipefail

TARGET_DIR="/data/models/kimi-k3"
SOURCE_MODE="${1:-huggingface}" # 'huggingface' or 'gcs'
GCS_BUCKET="${2:-gs://mevreon-kimi-k3-weights/moonshotai/Kimi-K3}"

echo "======================================================================"
echo " Preparing Local Storage: $TARGET_DIR"
echo " Ingestion Source:       $SOURCE_MODE"
echo "======================================================================"

sudo mkdir -p "$TARGET_DIR"
sudo chown -R "$USER:$USER" /data

if [ "$SOURCE_MODE" = "gcs" ]; then
    echo "=== Syncing from Google Cloud Storage ($GCS_BUCKET) ==="
    gcloud storage rsync -r "$GCS_BUCKET" "$TARGET_DIR" \
        --threads=16 \
        --no-user-output-enabled=false || gsutil -m rsync -r "$GCS_BUCKET" "$TARGET_DIR"
else
    echo "=== Downloading directly from Hugging Face (moonshotai/Kimi-K3) ==="
    pip install -q huggingface_hub[hf_transfer]
    export HF_HUB_ENABLE_HF_TRANSFER=1

    python3 -c "
from huggingface_hub import snapshot_download
print('Starting high-speed Hugging Face snapshot download for moonshotai/Kimi-K3...')
snapshot_download(
    repo_id='moonshotai/Kimi-K3',
    local_dir='$TARGET_DIR',
    local_dir_use_symlinks=False,
    max_workers=16
)
print('Hugging Face download complete!')
"
fi

echo "======================================================================"
echo " Verifying Downloaded Weights"
echo "======================================================================"
SHARD_COUNT=$(ls -1 "$TARGET_DIR"/*.safetensors 2>/dev/null | wc -l || echo 0)
echo "Safetensors shards found: $SHARD_COUNT (Expected: 96 shards)"

if [ "$SHARD_COUNT" -eq 96 ]; then
    echo "SUCCESS: All 96 shards of Kimi-K3 verified on local disk!"
    ls -lh "$TARGET_DIR"/config.json "$TARGET_DIR"/model.safetensors.index.json
else
    echo "WARNING: Found $SHARD_COUNT shards instead of 96. Please inspect storage."
    exit 1
fi
