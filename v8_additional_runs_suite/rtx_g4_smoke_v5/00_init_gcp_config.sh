#!/usr/bin/env bash
# Discover the same GCP RTX PRO 6000 nodes used by the prior suite and create RUN_CONFIG.env.
# Default preserves the prior Socket/NCCL net-shim workaround, but records it explicitly as provenance.
set -euo pipefail

: "${PROJECT_ID:=mevreon-diseaseprogression}"
: "${GPU_NODE0_NAME:=rtx-pro-6000-node-0}"
: "${GPU_NODE1_NAME:=rtx-pro-6000-node-1-c}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${V5_FORCE_NCCL_SOCKET:=1}"

NODE_LIST=$(gcloud compute instances list --project="$PROJECT_ID" --filter="status=RUNNING AND name:rtx-pro-6000" --format="value(name,zone,networkInterfaces[0].networkIP)" 2>/dev/null || true)
[[ -n "$NODE_LIST" ]] || { echo "ERROR: no running rtx-pro-6000 nodes found"; exit 1; }
NODE0_ZONE=""; NODE1_ZONE=""; NODE0_IP=""; NODE1_IP=""
while read -r name zone ip; do
  [[ -z "$name" ]] && continue
  clean_zone=$(awk -F/ '{print $NF}' <<<"$zone")
  [[ "$name" == "$GPU_NODE0_NAME" ]] && { NODE0_ZONE="$clean_zone"; NODE0_IP="$ip"; }
  [[ "$name" == "$GPU_NODE1_NAME" ]] && { NODE1_ZONE="$clean_zone"; NODE1_IP="$ip"; }
done <<<"$NODE_LIST"
[[ -n "$NODE0_IP" ]] || { echo "ERROR: primary node $GPU_NODE0_NAME not found"; exit 1; }

NODE0_REGION="${NODE0_ZONE%-*}"; NODE1_REGION="${NODE1_ZONE%-*}"
GCP_NETWORK_PROVENANCE="GCP_SINGLE_NODE"
if [[ -n "$NODE1_IP" ]]; then
  [[ "$NODE0_REGION" == "$NODE1_REGION" ]] || { echo "ERROR: cross-region nodes are not valid for this suite"; exit 1; }
  if [[ "$NODE0_ZONE" == "$NODE1_ZONE" ]]; then GCP_NETWORK_PROVENANCE="GCP_SAME_ZONE"; else GCP_NETWORK_PROVENANCE="GCP_CROSS_ZONE"; fi
fi

NCCL_TRANSPORT_PROVENANCE="NCCL_DEFAULT"
EXTRA_ENV=""
if [[ "$V5_FORCE_NCCL_SOCKET" == "1" ]]; then
  for ip in "$NODE0_IP" "$NODE1_IP"; do
    [[ -z "$ip" ]] && continue
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ip" \
      "mkdir -p /tmp/clean_nccl_libs && ln -sf /usr/local/gib/lib64/libnccl.so* /tmp/clean_nccl_libs/ && ln -sf /dev/null /tmp/clean_nccl_libs/libnccl-net.so" || true
  done
  NCCL_TRANSPORT_PROVENANCE="GCP_NCCL_SOCKET_NET_PLUGIN_DISABLED"
  EXTRA_ENV=$'export LD_LIBRARY_PATH=/tmp/clean_nccl_libs\nexport NCCL_NET=Socket'
fi

cat > RUN_CONFIG.env <<EOF
export PROJECT_ID="$PROJECT_ID"
export ZONE0="$NODE0_ZONE"
export ZONE1="$NODE1_ZONE"
export GPU_NODE0_NAME="$GPU_NODE0_NAME"
export GPU_NODE1_NAME="$GPU_NODE1_NAME"
export NODE0_IP="$NODE0_IP"
export NODE1_IP="$NODE1_IP"
export SSH_KEY="$SSH_KEY"
export BENCH_ROOT="\$HOME/rtx_g4_smoke"
export VENV_DIR="\$HOME/vllm_env"
export GCP_NETWORK_PROVENANCE="$GCP_NETWORK_PROVENANCE"
export NCCL_TRANSPORT_PROVENANCE="$NCCL_TRANSPORT_PROVENANCE"
$EXTRA_ENV
EOF
chmod 600 RUN_CONFIG.env

echo "Generated RUN_CONFIG.env"
echo "Node0: $GPU_NODE0_NAME $NODE0_ZONE $NODE0_IP"
echo "Node1: ${GPU_NODE1_NAME:-NA} ${NODE1_ZONE:-NA} ${NODE1_IP:-NA}"
echo "Network provenance: $GCP_NETWORK_PROVENANCE"
echo "NCCL provenance: $NCCL_TRANSPORT_PROVENANCE"
