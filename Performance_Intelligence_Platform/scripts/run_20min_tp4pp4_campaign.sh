#!/usr/bin/env bash
# ==============================================================================
# PERFORMANCE INTELLIGENCE PLATFORM — 20-MINUTE TP4/PP4 20G MASTER CAMPAIGN
# ==============================================================================
# Executes the full ~20 minute end-to-end multi-node characterization campaign
# for Kimi-Linear-48B on 16 GPUs (TP4/PP4) with 20 Gbps network rate pacing:
#
# 1. Environment Snapshot & Hardware Checksums (~10s)
# 2. Multi-Node TP4/PP4 PyTorch Profiler Chrome Trace (cold-cache c=8) (~2.5 min)
# 3. Step 10: Full Load Sweep across ALL Contexts & Concurrencies (~9 min)
#    - 1K Context   : c=1, c=8, c=32
#    - 8K Context   : c=1, c=8, c=32
#    - 128K Context : c=1, c=2, c=4, c=8
#    - 512K Context : c=1, c=2, c=4
#    - 1M Context   : c=1, c=2, c=4
# 4. Step 12: Network Resilience Under 20G Capped Bandwidth (~5 min)
# 5. Continuous Batching, Wave & Stall Telemetry Analysis (~1 min)
# 6. Consolidated Markdown & JSON Performance Summary Report (~30s)
#
# Total Expected Wall-Clock Runtime: ~20 to 22 minutes
#
# Usage:
#   bash run_20min_tp4pp4_campaign.sh [NODE1_IP]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

INPUT_NODE1_IP="${1:-}"

# Load existing environment config if available
if [[ -f "$SCRIPT_DIR/RUN_CONFIG.env" ]]; then
  source "$SCRIPT_DIR/RUN_CONFIG.env"
fi

NODE0_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
NODE1_IP="${INPUT_NODE1_IP:-${NODE1_IP:-}}"

if [[ -z "$NODE1_IP" ]]; then
  echo "ERROR: Node 1 IP is required to execute distributed TP4/PP4 across 2 nodes."
  echo "Usage: bash run_20min_tp4pp4_campaign.sh <NODE1_IP>"
  exit 1
fi

VENV_DIR="${VENV_DIR:-$HOME/pip_vllm_env}"
[[ -d "$VENV_DIR" ]] || VENV_DIR="$HOME/vllm_env"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

echo "================================================================================"
echo "  PERFORMANCE INTELLIGENCE PLATFORM — 20-MINUTE TP4/PP4 CAMPAIGN"
echo "  Model             : moonshotai/Kimi-Linear-48B-A3B-Instruct"
echo "  Topology          : TP4 / PP4 (16 GPUs across 2 Nodes)"
echo "  Pipeline Partition: 7, 7, 7, 6 (4 stages for 27 layers)"
echo "  MoE Backend       : FlashInfer CUTLASS (Autotuned)"
echo "  Interconnect      : 20 Gbps (tc HTB rate-paced on ens3)"
echo "  Primary Node 0    : $NODE0_IP"
echo "  Worker Node 1     : $NODE1_IP"
echo "  Expected Runtime  : ~20 to 22 minutes"
echo "================================================================================"

# 1. Verify Inter-Node Passwordless SSH
echo "--> [1/4] Verifying inter-node passwordless SSH connectivity..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$NODE1_IP" "nvidia-smi" >/dev/null 2>&1; then
  echo "ERROR: Passwordless SSH to Node 1 ($NODE1_IP) failed."
  echo "Please verify ~/.ssh/authorized_keys on Node 1 before starting."
  exit 2
fi
echo "    ✅ Dual-node cluster verified. 16 GPUs accessible."

# 2. Enforce 20 Gbps Traffic Control on ens3 (Both Nodes)
echo "--> [2/4] Applying 20 Gbps rate shaping (tc HTB) on ens3 across both nodes..."
if ip link show ens3 >/dev/null 2>&1; then
  sudo tc qdisc replace dev ens3 root handle 1: htb default 10 2>/dev/null || true
  sudo tc class replace dev ens3 parent 1: classid 1:10 htb rate 20gbit ceil 20gbit burst 256k cburst 256k 2>/dev/null || true
  echo "    Node 0: ens3 configured at 20 Gbps."
fi

ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$NODE1_IP" "
  if ip link show ens3 >/dev/null 2>&1; then
    sudo tc qdisc replace dev ens3 root handle 1: htb default 10 2>/dev/null || true
    sudo tc class replace dev ens3 parent 1: classid 1:10 htb rate 20gbit ceil 20gbit burst 256k cburst 256k 2>/dev/null || true
    echo '    Node 1: ens3 configured at 20 Gbps.'
  fi
" 2>/dev/null || true

# 3. Synchronize RUN_CONFIG.env
echo "--> [3/4] Exporting execution environment and kernel parameters..."
cat << EOF > "$SCRIPT_DIR/RUN_CONFIG.env"
export VENV_DIR="$VENV_DIR"
export NODE0_IP="$NODE0_IP"
export NODE1_IP="$NODE1_IP"
export SSH_KEY="\$HOME/.ssh/id_rsa"
export MODEL="moonshotai/Kimi-Linear-48B-A3B-Instruct"
export REVISION="e1df551a447157d4658b573f9a695d57658590e9"
export CUDA_DEVICE_ORDER="PCI_BUS_ID"
export VLLM_MOE_BACKEND="flashinfer_cutlass"
export MOE_BACKEND="flashinfer_cutlass"
export VLLM_FLASHINFER_AUTOTUNE="1"
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="\${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2}"
unset VLLM_PP_LAYER_PARTITION VLLM_DISABLE_PYNCCL || true
export LD_LIBRARY_PATH="/tmp/clean_nccl_libs:\${LD_LIBRARY_PATH:-}"
export NCCL_SOCKET_IFNAME="ens3"
export GLOO_SOCKET_IFNAME="ens3"
export NCCL_NET="Socket"
unset NCCL_CROSS_NIC NCCL_ALGO NCCL_PROTO || true
export NCCL_BUFFSIZE="4194304"
export V8_VLLM_NETWORK_CAP_GBPS="20"
export NETWORK_BANDWIDTH_SELECTION="20g"
export TOPOLOGY_SELECTION="tp4_pp4"
EOF

# 4. Launch the 20-Minute Distributed TP4/PP4 Campaign on Ray Cluster
echo "--> [4/4] Launching Distributed TP4/PP4 20G Suite (16 GPUs across 2 Nodes)..."
RUN_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="$HOME/platform_benchmark_runs/tp4_pp4_20g_${RUN_TIMESTAMP}"
mkdir -p "$OUT_DIR" "$HOME/platform_benchmark_runs"
echo "$RUN_TIMESTAMP" > "$HOME/platform_benchmark_runs/latest_run_id.txt"
echo "    Output Directory: $OUT_DIR"
echo "    Live Server Log : tail -f $OUT_DIR/tp4_pp4_dist/tp4_pp4_dist/server.log"
echo "================================================================================"

# Pre-flight cleanup
echo "    Purging any lingering Ray / vLLM workers across cluster..."
ray stop -f 2>/dev/null || true
ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" "ray stop -f 2>/dev/null || true; pkill -9 -f 'vllm.entrypoints|vllm serve|ray::RayWorkerProc' 2>/dev/null || true" 2>/dev/null || true
pkill -9 -f 'vllm.entrypoints|vllm serve|ray::RayWorkerProc' 2>/dev/null || true
sleep 3

START_TIME=$(date +%s)

cd "$SCRIPT_DIR/04_scaleout_distributed_network"
export OUT_ROOT="$OUT_DIR"
export CASES_FILE="$SCRIPT_DIR/04_scaleout_distributed_network/10b_vllm_multi_node_cases.json"
bash ./12_run_vllm_multi_node.sh --case tp4_pp4_dist

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_MIN=$((TOTAL_DURATION / 60))
TOTAL_SEC=$((TOTAL_DURATION % 60))

echo ""
echo "================================================================================"
echo "  ✅ TP4/PP4 20G CAMPAIGN COMPLETE!"
echo "  Total Wall-Clock Time: ${TOTAL_MIN}m ${TOTAL_SEC}s"
echo "  Results Directory: $OUT_DIR"
echo "================================================================================"

# Display Summary
echo ""
echo "--- BENCHMARK RESULTS TABLE (TTFT, TPOT & METRICS) ---"
python3 "$SCRIPT_DIR/bench_summary.py" "$OUT_DIR" || true

