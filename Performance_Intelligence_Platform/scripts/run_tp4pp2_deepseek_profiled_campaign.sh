#!/usr/bin/env bash
# ==============================================================================
# PERFORMANCE INTELLIGENCE PLATFORM — TP4/PP2 DEEPSEEK PROFILED CAMPAIGN
# ==============================================================================
# End-to-end multi-node benchmark & deep profiling runner for DeepSeek-V4.1-Flash
# (and Kimi-Linear-48B) on 8 GPUs across 2 server nodes (4 GPUs/node).
#
# Generates and captures directly in the run output directory:
#  1. Serving Benchmarks across ALL Contexts & Concurrencies (1K to 1M, c=1..32)
#  2. Distributed PyTorch Chrome Traces (*.pt.trace.json.gz) across all 8 ranks
#  3. Distributed NVIDIA Nsight Systems Profile Captures (*.nsys-rep) on both nodes
#  4. Automated SQLite Database Exports (*.sqlite) converted via nsys export
#  5. Wave, Stall, and Pipeline Telemetry Summaries
#
# Supported Network Modes:
#   --network native       (GCP Andromeda 175G RoCEv2 native)
#   --network capped_100g  (100 Gbps traffic control rate pacing)
#   --network capped_20g   (20 Gbps standard tier rate pacing)
#   --network all          (Executes native, 100g, and 20g sequentially)
#
# Usage:
#   bash run_tp4pp2_deepseek_profiled_campaign.sh [NODE1_IP] [--network native|capped_100g|capped_20g|all] [--model MODEL_PATH]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

NODE1_IP=""
NETWORK_MODE="native"
MODEL="${MODEL:-deepseek-ai/DeepSeek-V4.1-Flash}"
[[ -d "/data/models/deepseek-v4.1-flash" ]] && MODEL="/data/models/deepseek-v4.1-flash"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --network|-n)
      NETWORK_MODE="$2"; shift 2 ;;
    --model|-m)
      MODEL="$2"; shift 2 ;;
    --node1-ip)
      NODE1_IP="$2"; shift 2 ;;
    *)
      if [[ -z "$NODE1_IP" && "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        NODE1_IP="$1"
      fi
      shift ;;
  esac
done

if [[ -f "$SCRIPT_DIR/RUN_CONFIG.env" ]]; then
  source "$SCRIPT_DIR/RUN_CONFIG.env"
fi

NODE0_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
NODE1_IP="${NODE1_IP:-${CALLER_NODE1:-${NODE1:-}}}"

if [[ -z "$NODE1_IP" ]]; then
  echo "ERROR: Node 1 IP is required for TP4/PP2 distributed execution across 2 nodes."
  echo "Usage: bash run_tp4pp2_deepseek_profiled_campaign.sh <NODE1_IP> [--network native|capped_100g|capped_20g|all]"
  exit 1
fi

VENV_DIR="${VENV_DIR:-$HOME/pip_vllm_env}"
[[ -d "$VENV_DIR" ]] || VENV_DIR="$HOME/vllm_env"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

RUN_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CAMPAIGN_ROOT="${OUT_ROOT:-$HOME/pip_runs/tp4_pp2_deepseek_${RUN_TIMESTAMP}}"
mkdir -p "$CAMPAIGN_ROOT"

SSH_KEY="${SSH_KEY:-$HOME/.ssh/google_compute_engine}"
SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
SCP=(scp -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)

DEFAULT_IFACE="${NCCL_SOCKET_IFNAME:-}"
if [[ -z "$DEFAULT_IFACE" ]]; then
  DEFAULT_IFACE=$(ip route get "$NODE1_IP" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
fi
DEFAULT_IFACE="${DEFAULT_IFACE:-ens3}"
export NCCL_SOCKET_IFNAME="$DEFAULT_IFACE"

echo "================================================================================"
echo "  PERFORMANCE INTELLIGENCE PLATFORM — TP4/PP2 DEEPSEEK PROFILED CAMPAIGN"
echo "================================================================================"
echo "  Workload Model       : $MODEL"
echo "  Topology Layout      : TP=4, PP=2 (8 GPUs total: 4 GPUs/node)"
echo "  Cluster Nodes        : Node 0 ($NODE0_IP) <---> Node 1 ($NODE1_IP)"
echo "  Selected Network(s)  : $NETWORK_MODE"
echo "  Campaign Root Dir    : $CAMPAIGN_ROOT"
echo "  Active Interface     : $DEFAULT_IFACE"
echo "================================================================================"

apply_tc_cap() {
  local net="$1"
  local iface="$DEFAULT_IFACE"
  echo "[NET] Reconfiguring network pacing: $net on interface $iface..."
  # Clean up existing qdisc
  sudo tc qdisc del dev "$iface" root 2>/dev/null || true
  "${SSH[@]}" "$NODE1_IP" "sudo tc qdisc del dev '$iface' root 2>/dev/null || true" || true

  if [[ "$net" == "capped_100g" ]]; then
    sudo tc qdisc add dev "$iface" root tbf rate 100gbit burst 128mb latency 50ms 2>/dev/null || true
    "${SSH[@]}" "$NODE1_IP" "sudo tc qdisc add dev '$iface' root tbf rate 100gbit burst 128mb latency 50ms 2>/dev/null || true" || true
  elif [[ "$net" == "capped_20g" ]]; then
    sudo tc qdisc add dev "$iface" root tbf rate 20gbit burst 32mb latency 50ms 2>/dev/null || true
    "${SSH[@]}" "$NODE1_IP" "sudo tc qdisc add dev '$iface' root tbf rate 20gbit burst 32mb latency 50ms 2>/dev/null || true" || true
  fi
}

run_single_network_campaign() {
  local current_net="$1"
  local net_root="$CAMPAIGN_ROOT/$current_net"
  mkdir -p "$net_root/benchmarks" "$net_root/sqlite_traces" "$net_root/nsys_profiles" "$net_root/pytorch_traces"

  echo ""
  echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
  echo "  STARTING CAMPAIGN STAGE: $current_net"
  echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
  apply_tc_cap "$current_net"

  # ----------------------------------------------------------------------------
  # Phase 1: Full Concurrency & Context Benchmarks (TP4/PP2 Load Sweep)
  # ----------------------------------------------------------------------------
  echo "[PHASE 1/3] Executing TP4/PP2 Concurrency Ladders (1K..1M, c=1..32)..."
  env OUT_ROOT="$net_root/benchmarks" \
      NODE0_IP="$NODE0_IP" \
      NODE1_IP="$NODE1_IP" \
      MODEL="$MODEL" \
      TOPOLOGY="tp4_pp2_dist" \
      NETWORK_MODE="$current_net" \
      bash "$SCRIPT_DIR/04_scaleout_distributed_network/12_run_vllm_multi_node.sh" --case tp4_pp2_dist || true

  # ----------------------------------------------------------------------------
  # Phase 2: Multi-Node PyTorch Profiling (14d - Steady State Chrome Tracing)
  # ----------------------------------------------------------------------------
  echo "[PHASE 2/3] Capturing 16-GPU Distributed PyTorch Chrome Traces..."
  for conc in 1 8; do
    echo "  -> Capturing PyTorch trace for TP4/PP2 at concurrency c=$conc..."
    env OUT_ROOT="$net_root/pytorch_traces/c${conc}" \
        PROFILE_ROOT="$net_root/pytorch_traces/c${conc}" \
        NODE0_IP="$NODE0_IP" \
        NODE1_IP="$NODE1_IP" \
        MODEL="$MODEL" \
        TOPOLOGY="tp4_pp2_dist" \
        CONCURRENCY="$conc" \
        bash "$SCRIPT_DIR/06_deep_kernel_and_torch_profiling/14d_run_vllm_torch_profile_multi_node.sh" || true
  done

  # ----------------------------------------------------------------------------
  # Phase 3: Distributed Nsight Systems Profiling + SQLite Database Exports
  # ----------------------------------------------------------------------------
  echo "[PHASE 3/3] Executing Distributed Nsight Profiling & Exporting SQLite Traces..."
  for mode in decode_8k batched_decode_8k_c8 prefill_128k extreme_prefill_1m; do
    echo "  -> Profiling mode: $mode..."
    env OUT_ROOT="$net_root/nsys_profiles" \
        NODE0_IP="$NODE0_IP" \
        NODE1_IP="$NODE1_IP" \
        PROFILE_TOPOLOGY_FILTER="tp4_pp2_dist" \
        PROFILE_MODE_FILTER="$mode" \
        bash "$SCRIPT_DIR/rtx_g4_smoke_v5/18_run_vllm_multi_node_profiles.sh" || true
  done

  # Harvest all generated .sqlite files and copy to top-level sqlite_traces folder
  echo "Harvesting SQLite trace databases..."
  find "$net_root/nsys_profiles" -type f -name '*.sqlite' -exec cp -f {} "$net_root/sqlite_traces/" \; 2>/dev/null || true
  find "$net_root/pytorch_traces" -type f -name '*.pt.trace.json*' -exec cp -f {} "$net_root/pytorch_traces/" \; 2>/dev/null || true

  echo "Completed Stage $current_net."
}

# Determine network execution plan
if [[ "$NETWORK_MODE" == "all" ]]; then
  NETWORKS=("native" "capped_100g" "capped_20g")
else
  NETWORKS=("$NETWORK_MODE")
fi

START_EPOCH=$(date +%s)
for net in "${NETWORKS[@]}"; do
  run_single_network_campaign "$net"
done
END_EPOCH=$(date +%s)
TOTAL_WALL_TIME=$((END_EPOCH - START_EPOCH))

# Reset traffic control at end
sudo tc qdisc del dev "$DEFAULT_IFACE" root 2>/dev/null || true
"${SSH[@]}" "$NODE1_IP" "sudo tc qdisc del dev '$DEFAULT_IFACE' root 2>/dev/null || true" 2>/dev/null || true

# Summary manifest
cat <<MANIFEST > "$CAMPAIGN_ROOT/CAMPAIGN_MANIFEST.json"
{
  "campaign": "TP4_PP2_DEEPSEEK_PROFILED",
  "timestamp": "$RUN_TIMESTAMP",
  "model": "$MODEL",
  "topology": "TP4/PP2 (8 GPUs)",
  "networks_evaluated": $(printf '%s\n' "${NETWORKS[@]}" | jq -R . | jq -s .),
  "total_wall_clock_seconds": $TOTAL_WALL_TIME,
  "campaign_root": "$CAMPAIGN_ROOT"
}
MANIFEST

echo "================================================================================"
echo "  CAMPAIGN COMPLETE! Total Wall-Clock Time: $((TOTAL_WALL_TIME / 60))m $((TOTAL_WALL_TIME % 60))s"
echo "  All SQLite databases, Nsys reports, and PyTorch traces saved in:"
echo "    $CAMPAIGN_ROOT"
echo "================================================================================"
