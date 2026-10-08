#!/usr/bin/env bash
# ==============================================================================
# DEMO STEP 2: Install System Tools, PyTorch, Ray & vLLM
# (Run on BOTH Node 0 and Node 1)
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo " [DEMO] 1/5: Installing System Utilities (iperf3, git, pciutils)..."
echo "======================================================================"
sudo dnf install -y iperf3 git pciutils > /dev/null 2>&1 || true

echo "======================================================================"
echo " [DEMO] 2/5: Installing uv High-Speed Package Manager..."
echo "======================================================================"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

echo "======================================================================"
echo " [DEMO] 3/5: Creating Isolated Virtual Environment (~/vllm_env)..."
echo "======================================================================"
rm -rf "$HOME/vllm_env"
uv venv "$HOME/vllm_env"

echo "======================================================================"
echo " [DEMO] 4/5: Installing PyTorch (CUDA 12.8 sm_120 Blackwell Nightly)..."
echo "======================================================================"
uv pip install --python "$HOME/vllm_env/bin/python" \
    --pre torch torchvision \
    --index-url https://download.pytorch.org/whl/nightly/cu128

echo "======================================================================"
echo " [DEMO] 5/5: Installing vLLM, Ray Core & Ecosystem Libraries..."
echo "======================================================================"
uv pip install --python "$HOME/vllm_env/bin/python" \
    vllm "ray[default]" triton transformers huggingface-hub fastapi

echo ""
echo "======================================================================"
echo " [DEMO] Verification & Self-Test"
echo "======================================================================"
"$HOME/vllm_env/bin/python" - << 'EOF'
import torch, shutil, sys

print(f" Python Version : {sys.version.split()[0]}")
print(f" PyTorch Version: {torch.__version__}")
print(f" CUDA Runtime   : {torch.version.cuda}")
print(f" CUDA Available : {torch.cuda.is_available()}")
print(f" GPU Count      : {torch.cuda.device_count()} GPUs detected")
for i in range(torch.cuda.device_count()):
    name = torch.cuda.get_device_name(i)
    mem = torch.cuda.get_device_properties(i).total_memory / (1024**3)
    arch = torch.cuda.get_device_capability(i)
    print(f"   -> GPU {i}: {name} (sm_{arch[0]}{arch[1]}) | {mem:.1f} GB GDDR7")

print(f" Ray CLI Path   : {shutil.which('ray', path='/home/ayu23/vllm_env/bin')}")
print(f" vLLM CLI Path  : {shutil.which('vllm', path='/home/ayu23/vllm_env/bin')}")
print(" STATUS: Ready for Multi-Node Ray Cluster & vLLM Serving!")
EOF
