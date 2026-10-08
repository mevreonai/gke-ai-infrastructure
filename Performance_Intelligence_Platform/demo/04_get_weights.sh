#!/usr/bin/env bash
# ==============================================================================
# DEMO STEP 4: Model Weights Ingestion
# Options:
#   1. Cloud Storage FUSE Mount (INSTANT - Zero Download Wait Time)
#   2. Direct High-Speed GCS Parallel Download
# ==============================================================================
set -euo pipefail

TARGET_DIR="${TARGET_DIR:-/data/models}"
sudo mkdir -p "$TARGET_DIR"
sudo chown -R "$USER:$USER" "$TARGET_DIR"

MODE="${1:-fuse}"

if [[ "$MODE" == "fuse" ]]; then
  echo "======================================================================"
  echo " [DEMO] Mounting Google Cloud Storage via FUSE (Instant Zero-Copy)..."
  echo "======================================================================"
  # Install gcsfuse if missing
  if ! command -v gcsfuse &> /dev/null; then
    sudo dnf install -y gcsfuse > /dev/null 2>&1 || true
  fi
  
  mkdir -p /mnt/models
  fusermount -u /mnt/models 2>/dev/null || true
  gcsfuse --implicit-dirs mevreon-kimi-k3-weights /mnt/models
  
  echo ""
  echo "--> Successfully mounted gs://mevreon-kimi-k3-weights to /mnt/models!"
  echo "--> Model Files Available:"
  ls -lh /mnt/models/moonshotai/Kimi-K3/ 2>/dev/null || ls -lh /mnt/models/
  echo ""
  echo "vLLM can now load model directly from: /mnt/models/moonshotai/Kimi-K3"

elif [[ "$MODE" == "download" ]]; then
  BUCKET_URI="${2:-gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash}"
  echo "======================================================================"
  echo " [DEMO] Streaming Weights from Google Cloud Storage: $BUCKET_URI"
  echo "======================================================================"
  gcloud storage cp -r -m "$BUCKET_URI" "$TARGET_DIR/"
  echo "--> Model Downloaded to $TARGET_DIR!"

else
  echo "Usage:"
  echo "  Option A (Instant Zero-Copy): ./04_get_weights.sh fuse"
  echo "  Option B (Direct Download):   ./04_get_weights.sh download <GCS_BUCKET_URI>"
fi
