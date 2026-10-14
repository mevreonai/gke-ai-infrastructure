#!/usr/bin/env bash
set -e
echo "Backing up stock libraries..."
cp -rn $HOME/vllm_env/lib64/python3.12/site-packages/transformers $HOME/transformers_stock_bak 2>/dev/null || true
cp -rn $HOME/vllm_env/lib64/python3.12/site-packages/vllm $HOME/vllm_stock_bak 2>/dev/null || true

echo "Extracting patched packages from custom container..."
CID=$(sudo docker create vllm/vllm-openai:deepseekv41-flash-0909)
sudo docker cp "${CID}:/usr/local/lib/python3.12/dist-packages/transformers" $HOME/vllm_env/lib64/python3.12/site-packages/
sudo docker cp "${CID}:/usr/local/lib/python3.12/dist-packages/vllm" $HOME/vllm_env/lib64/python3.12/site-packages/
sudo chown -R $(id -u):$(id -g) $HOME/vllm_env/lib64/python3.12/site-packages/transformers
sudo chown -R $(id -u):$(id -g) $HOME/vllm_env/lib64/python3.12/site-packages/vllm
sudo docker rm -v "${CID}"

echo "PATCHED_PACKAGES_INSTALLED_SUCCESSFULLY"
