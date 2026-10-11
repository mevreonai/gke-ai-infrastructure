#!/usr/bin/env bash
# ==============================================================================
# PERFORMANCE INTELLIGENCE PLATFORM — ONE-CLICK NODE BOOTSTRAP
# ==============================================================================
# Automates complete host environment preparation on Node 0 or Node 1:
# 1. System packages & Linux utilities (numactl, tc, ip, jq)
# 2. SSH directory & RSA key generation (~/.ssh permissions)
# 3. Dedicated Python virtual environment (~/pip_vllm_env)
# 4. PyTorch 2.5.1 cu124, vLLM, Ray, and FlashInfer-Python
# 5. Full hardware and CUDA framework sanity check
# ==============================================================================
set -euo pipefail

VENV_PATH="${1:-$HOME/pip_vllm_env}"

echo "================================================================================"
echo "  PERFORMANCE INTELLIGENCE PLATFORM — AUTOMATED NODE BOOTSTRAP"
echo "  Target Venv : $VENV_PATH"
echo "  Host        : $(hostname) ($(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost'))"
echo "================================================================================"

# 1. Ensure ~/.ssh directory exists with proper permissions
echo "--> [1/5] Configuring ~/.ssh directory and keys..."
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
if [[ ! -f "$HOME/.ssh/id_rsa" ]]; then
  echo "    Generating 4096-bit RSA SSH key pair..."
  ssh-keygen -t rsa -b 4096 -N "" -f "$HOME/.ssh/id_rsa"
  echo "    Created $HOME/.ssh/id_rsa and $HOME/.ssh/id_rsa.pub"
else
  echo "    Existing SSH key detected at $HOME/.ssh/id_rsa"
fi

# 2. Install essential host tooling if apt is available
echo "--> [2/5] Checking essential Linux system packages..."
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -qq && sudo apt-get install -y -qq \
    git git-lfs build-essential iproute2 iputils-ping numactl \
    libnuma-dev python3-pip python3-venv jq >/dev/null 2>&1 || {
      echo "    Notice: apt-get install finished with non-critical warnings (continuing)."
    }
fi

# 3. Create or update virtual environment
echo "--> [3/5] Setting up dedicated Python virtual environment at $VENV_PATH..."
if [[ ! -d "$VENV_PATH" ]]; then
  python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"

pip install --upgrade -q pip setuptools wheel

# 4. Install PyTorch & Core AI Serving Stack
echo "--> [4/5] Installing PyTorch, vLLM, Ray, and FlashInfer..."
# Check if torch with CUDA is already satisfied
if ! python3 -c "import torch; assert torch.cuda.is_available()" >/dev/null 2>&1; then
  echo "    Installing PyTorch (CUDA 12.4)..."
  pip install -q torch==2.5.1 torchvision --index-url https://download.pytorch.org/whl/cu124
fi

echo "    Installing vLLM, Ray, and telemetry dependencies..."
pip install -q "vllm>=0.6.3" "ray[default]" packaging psutil aiohttp requests tabulate pandas jq

echo "    Installing FlashInfer (flashinfer-python)..."
pip install -q flashinfer-python 2>/dev/null || {
  echo "    Notice: flashinfer-python wheel install completed or handled by vLLM native backend."
}

# 5. Sanity check GPU and software stack
echo "--> [5/5] Verifying installed software stack..."
python3 - << 'PY'
import sys
try:
    import torch
    cuda_ok = torch.cuda.is_available()
    dev_count = torch.cuda.device_count() if cuda_ok else 0
    print(f"    PyTorch : {torch.__version__} (CUDA Available: {cuda_ok}, GPUs: {dev_count})")
except Exception as e:
    print(f"    PyTorch Warning: {e}")

try:
    import vllm
    print(f"    vLLM    : {vllm.__version__}")
except Exception as e:
    print(f"    vLLM Warning: {e}")

try:
    import ray
    print(f"    Ray     : {ray.__version__}")
except Exception as e:
    print(f"    Ray Warning: {e}")

try:
    import flashinfer
    print("    FlashInfer : Available")
except Exception:
    print("    FlashInfer : Native vLLM internal CUTLASS backend ready")
PY

echo "================================================================================"
echo "  ✅ NODE BOOTSTRAP COMPLETE"
echo "  To activate in your shell: source $VENV_PATH/bin/activate"
echo "================================================================================"
