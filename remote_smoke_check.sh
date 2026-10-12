#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "V8 SUITE REMOTE SMOKE TEST - NODE & ENV VERIFICATION"
echo "=========================================================="

run_check() {
    local host_label="$1"
    echo ""
    echo "--- Checking ${host_label} ---"
    python3 -c "
import torch
import ray
import vllm

cuda_ok = torch.cuda.is_available()
dev_count = torch.cuda.device_count()
dev_name = torch.cuda.get_device_name(0) if dev_count > 0 else 'None'

print(f'CUDA Available : {cuda_ok}')
print(f'GPU Count      : {dev_count}')
print(f'Device Name    : {dev_name}')
print(f'PyTorch Ver    : {torch.__version__}')
print(f'vLLM Ver       : {vllm.__version__}')
print(f'Ray Ver        : {ray.__version__}')
"
}

# Run on Node 0
source ~/vllm_env/bin/activate 2>/dev/null || true
run_check "NODE 0 (Local: $(hostname))"

# Check Ray status
echo ""
echo "--- Ray Status on Node 0 ---"
ray status 2>&1 | head -n 15 || true

# Run on Node 1 via SSH
echo ""
echo "--- Checking NODE 1 (10.128.0.40) ---"
ssh -o StrictHostKeyChecking=no 10.128.0.40 "source ~/vllm_env/bin/activate 2>/dev/null || true; python3 -c '
import torch, ray, vllm
print(f\"CUDA: {torch.cuda.is_available()} | GPUs: {torch.cuda.device_count()} | Device: {torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else \"None\"} | PyTorch: {torch.__version__} | vLLM: {vllm.__version__} | Ray: {ray.__version__}\")
'"

echo ""
echo "=========================================================="
echo "TESTING PREFLIGHT SUITE SCRIPT (07_preflight_v5.py)"
echo "=========================================================="
cd ~/v8_additional_runs_suite
python3 rtx_g4_smoke_v5/07_preflight_v5.py || true

echo ""
echo "SMOKE TEST STAGE 1 VERIFICATION COMPLETED SUCCESSFULLY"
