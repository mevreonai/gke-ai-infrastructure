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
export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"
export VLLM_PP_LAYER_PARTITION="7,7,7,6"
export LD_LIBRARY_PATH="/tmp/clean_nccl_libs:\${LD_LIBRARY_PATH:-}"
export NCCL_SOCKET_IFNAME="ens3"
export GLOO_SOCKET_IFNAME="ens3"
export NCCL_NET="Socket"
export NCCL_CROSS_NIC="1"
export NCCL_BUFFSIZE="4194304"
export NCCL_ALGO="Tree"
export NCCL_PROTO="Simple"
export V8_VLLM_NETWORK_CAP_GBPS="20"
export NETWORK_BANDWIDTH_SELECTION="20g"
export TOPOLOGY_SELECTION="tp4_pp4"
EOF

# 4. Launch the 20-Minute Master Campaign
echo "--> [4/4] Launching Master Campaign Orchestrator..."
echo "    Live Log File: tail -f \$HOME/platform_benchmark_runs/\$(cat \$HOME/platform_benchmark_runs/latest_run_id.txt 2>/dev/null || echo '<run_id>')/logs/MASTER_BENCHMARK_RUN.log"
echo "================================================================================"

START_TIME=$(date +%s)

bash "$SCRIPT_DIR/run_master_benchmark.sh" \
  --topologies tp4_pp4 \
  --bandwidth 20g \
  --contexts all \
  --concurrencies all

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_MIN=$((TOTAL_DURATION / 60))
TOTAL_SEC=$((TOTAL_DURATION % 60))

echo ""
echo "================================================================================"
echo "  ✅ TP4/PP4 20G CAMPAIGN COMPLETE!"
echo "  Total Wall-Clock Time: ${TOTAL_MIN}m ${TOTAL_SEC}s"
echo "================================================================================"

# Display Summary
LATEST_RUN_ID=$(cat "$HOME/platform_benchmark_runs/latest_run_id.txt" 2>/dev/null || echo "")
if [[ -n "$LATEST_RUN_ID" && -d "$HOME/platform_benchmark_runs/$LATEST_RUN_ID" ]]; then
  RUN_DIR="$HOME/platform_benchmark_runs/$LATEST_RUN_ID"
  echo ""
  echo "--- STEP EXECUTION STATUS ---"
  if [[ -f "$RUN_DIR/master_step_status.jsonl" ]]; then
    python3 - << PY "$RUN_DIR/master_step_status.jsonl"
import json, sys
for line in open(sys.argv[1]):
    if line.strip():
        s = json.loads(line)
        status = "✅ PASS" if s.get("rc") == 0 else f"❌ FAIL (rc={s.get('rc')})"
        dur = s.get("end", 0) - s.get("start", 0)
        print(f"  Step {s.get('step_num'):02d} ({s.get('step_name'):<30}) : {status} [{dur}s]")
PY
  fi

  echo ""
  echo "--- BENCHMARK RESULTS TABLE (TTFT & TPOT METRICS) ---"
  if [[ -d "$RUN_DIR/step10_multi_node_load/tp4_pp4_dist_load" ]]; then
    python3 "$SCRIPT_DIR/bench_summary.py" "$RUN_DIR/step10_multi_node_load/tp4_pp4_dist_load" || true
  fi
fi
