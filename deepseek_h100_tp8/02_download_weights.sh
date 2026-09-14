#!/usr/bin/env bash
# ==============================================================================
# 02_download_weights.sh
# Download DeepSeek-V4.1-Flash weights directly to local high-speed disk
# Run this inside the VM if starting from a clean disk.
# ==============================================================================

TARGET_DIR="/data/models/deepseek-v4.1-flash"
REPO_ID="deepseek-ai/DeepSeek-V4.1-Flash"

echo "=== 1. Setting up directory ==="
sudo mkdir -p "$TARGET_DIR"
sudo chown -R "$USER:$USER" "$TARGET_DIR"

echo "=== 2. Installing HuggingFace Hub CLI ==="
pip install -q huggingface_hub[hf_transfer]

# Enable hf_transfer for multi-gigabit multi-stream downloads
export HF_HUB_ENABLE_HF_TRANSFER=1

echo "=== 3. Downloading DeepSeek-V4.1-Flash Weights ==="
# DeepSeek-V4.1-Flash consists of 48 safetensors shards (~475 GB)
huggingface-cli download "$REPO_ID" \
    --local-dir "$TARGET_DIR" \
    --local-dir-use-symlinks False

echo "=== 4. Verifying Model Shards ==="
ls -lh "$TARGET_DIR"/*.safetensors | wc -l
echo "Expected: 48 shards."
