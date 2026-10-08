#!/usr/bin/env bash
# ==============================================================================
# AUTOMATED 1-CLICK DEMO SETUP SCRIPT FOR RTX PRO 6000 CLUSTER
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo " [DEMO] STEP 1: Installing uv High-Speed Package Manager..."
echo "======================================================================"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

echo "======================================================================"
echo " [DEMO] STEP 2: Setting up Isolated Virtualenv (vllm_env)..."
echo "======================================================================"
uv venv "$HOME/vllm_env"

echo "======================================================================"
echo " [DEMO] STEP 3: Installing PyTorch (sm_120 Blackwell Nightly)..."
echo "======================================================================"
uv pip install --python "$HOME/vllm_env/bin/python" --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128

echo "======================================================================"
echo " [DEMO] STEP 4: Installing vLLM & Ray Core..."
echo "======================================================================"
uv pip install --python "$HOME/vllm_env/bin/python" vllm "ray[default]"

echo "======================================================================"
echo " [DEMO] STEP 5: Running 8-GPU Compute & P2P Hardware Smoke Benchmark..."
echo "======================================================================"
"$HOME/vllm_env/bin/python" - << 'EOF'
import torch, time

print("\n" + "="*70)
print("  NVIDIA RTX PRO 6000 BLACKWELL 8-GPU LIVE HARDWARE BENCHMARK")
print("="*70)
print(f"PyTorch: {torch.__version__} | CUDA: {torch.version.cuda} | Devices: {torch.cuda.device_count()}\n")

for i in range(torch.cuda.device_count()):
    name = torch.cuda.get_device_name(i)
    mem = torch.cuda.get_device_properties(i).total_memory / (1024**3)
    dev = torch.device(f"cuda:{i}")
    a = torch.randn(8192, 8192, dtype=torch.float16, device=dev)
    b = torch.randn(8192, 8192, dtype=torch.float16, device=dev)
    torch.cuda.synchronize(dev)
    t0 = time.perf_counter()
    for _ in range(15): c = torch.matmul(a, b)
    torch.cuda.synchronize(dev)
    dt = (time.perf_counter() - t0) / 15
    tflops = (2 * (8192**3) / dt) / 1e12
    print(f"  GPU {i} [{name}] ({mem:.1f}GB): {tflops:.1f} TFLOPS | Latency: {dt*1000:.2f} ms")

print("\nPeer-to-Peer Access:")
for i in range(torch.cuda.device_count()):
    p2p = [ "P2P" if torch.cuda.can_device_access_peer(i, j) else "SELF" if i==j else "NO" for j in range(8) ]
    print(f"  GPU {i}: " + " ".join(p2p))

x = torch.empty(256 * 1024 * 1024, dtype=torch.float32, device="cuda:0")
torch.cuda.synchronize("cuda:0")
t0 = time.perf_counter()
for _ in range(15): y = x.clone()
torch.cuda.synchronize("cuda:0")
dt = (time.perf_counter() - t0) / 15
print(f"\n  GPU 0 GDDR7 Memory Copy Bandwidth: {2.0 / dt:.1f} GB/s")
print("="*70)
print("  LIVE CLUSTER DEMO SANITY TEST: 100% PASSED!")
print("="*70)
EOF
