#!/usr/bin/env bash
# Dedicated multi-node PyTorch profiler run for Tier 1 (16 GPUs) and Tier 2 (8 GPUs).
# Supports tp4_pp4_dist, tp8_pp2_dist, tp16_pp1_dist, and tp4_pp2_dist with CUDA graphs ON.
# Captures steady-state batched decode across all Ray worker processes on BOTH nodes.
# Automatically collects Chrome traces (*.pt.trace.json) from Node 0 and Node 1 via SCP.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CALLER_MODEL="${MODEL:-}"
CALLER_REVISION="${REVISION:-}"
CALLER_TOPOLOGY="${TOPOLOGY:-}"
CALLER_INPUT_LEN="${INPUT_LEN:-}"
CALLER_OUTPUT_LEN="${OUTPUT_LEN:-}"
CALLER_CONCURRENCY="${CONCURRENCY:-}"
CALLER_PORT="${PORT:-}"
CALLER_PROFILE_ROOT="${PROFILE_ROOT:-}"
CALLER_OUT_ROOT="${OUT_ROOT:-}"
CALLER_NODE0="${NODE0_IP:-}"
CALLER_NODE1="${NODE1_IP:-}"
CALLER_SSH_KEY="${SSH_KEY:-}"
CALLER_VENV_DIR="${VENV_DIR:-}"
CALLER_PP_SPLIT="${VLLM_PP_LAYER_PARTITION:-}"

for f in "$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env"; do [[ -f "$f" ]] && { source "$f"; break; }; done

[[ -n "$CALLER_MODEL" ]] && export MODEL="$CALLER_MODEL"
[[ -n "$CALLER_REVISION" ]] && export REVISION="$CALLER_REVISION"
[[ -n "$CALLER_TOPOLOGY" ]] && export TOPOLOGY="$CALLER_TOPOLOGY"
[[ -n "$CALLER_INPUT_LEN" ]] && export INPUT_LEN="$CALLER_INPUT_LEN"
[[ -n "$CALLER_OUTPUT_LEN" ]] && export OUTPUT_LEN="$CALLER_OUTPUT_LEN"
[[ -n "$CALLER_CONCURRENCY" ]] && export CONCURRENCY="$CALLER_CONCURRENCY"
[[ -n "$CALLER_PORT" ]] && export PORT="$CALLER_PORT"
[[ -n "$CALLER_PROFILE_ROOT" ]] && export PROFILE_ROOT="$CALLER_PROFILE_ROOT"
[[ -n "$CALLER_OUT_ROOT" ]] && export OUT_ROOT="$CALLER_OUT_ROOT"
[[ -n "$CALLER_NODE0" ]] && export NODE0_IP="$CALLER_NODE0"
[[ -n "$CALLER_NODE1" ]] && export NODE1_IP="$CALLER_NODE1"
[[ -n "$CALLER_SSH_KEY" ]] && export SSH_KEY="$CALLER_SSH_KEY"
[[ -n "$CALLER_VENV_DIR" ]] && export VENV_DIR="$CALLER_VENV_DIR"
unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL VLLM_PP_LAYER_PARTITION 2>/dev/null || true
[[ -n "$CALLER_PP_SPLIT" ]] && export VLLM_PP_LAYER_PARTITION="$CALLER_PP_SPLIT"

if [[ -f "$SCRIPT_DIR/20_nccl_policy.sh" ]]; then
  source "$SCRIPT_DIR/20_nccl_policy.sh"
  nccl_multi_node_v6_aligned_env
  REMOTE_V6_ENV="$(nccl_remote_v6_aligned_exports)"
else
  REMOTE_V6_ENV=""
fi

: "${MODEL:=moonshotai/Kimi-Linear-48B-A3B-Instruct}"
if [[ "$MODEL" == *"Kimi-Linear"* ]]; then
  : "${REVISION:=e1df551a447157d4658b573f9a695d57658590e9}"
else
  : "${REVISION:=}"
fi
: "${TOPOLOGY:=tp4_pp4_dist}"
: "${INPUT_LEN:=8192}"
: "${OUTPUT_LEN:=1024}"
: "${CONCURRENCY:=8}"
: "${PORT:=8025}"
: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"

case "$TOPOLOGY" in
  tp4_pp4*|tp4_pp4_dist)
    TP=4; PP=4; GPUS=8; TOPO_NAME="tp4_pp4_dist" ;;
  tp8_pp2*|tp8_pp2_dist)
    TP=8; PP=2; GPUS=8; TOPO_NAME="tp8_pp2_dist" ;;
  tp16_pp1*|tp16_pp1_dist)
    TP=16; PP=1; GPUS=8; TOPO_NAME="tp16_pp1_dist" ;;
  tp4_pp2*|tp4_pp2_dist)
    TP=4; PP=2; GPUS=4; TOPO_NAME="tp4_pp2_dist" ;;
  *)
    echo "Unknown or unsupported multi-node topology: $TOPOLOGY"
    exit 2 ;;
esac

: "${PROFILE_ROOT:=${OUT_ROOT:-$HOME/v8_additional_runs/$(date +%Y%m%d_%H%M%S)/torch_profiles/${TOPO_NAME}_c${CONCURRENCY}}}"
mkdir -p "$PROFILE_ROOT/torch/node0" "$PROFILE_ROOT/torch/node1"
command -v vllm >/dev/null || exit 2
command -v ray >/dev/null || exit 2

if [[ -z "${NODE0_IP:-}" || -z "${NODE1_IP:-}" ]]; then
  echo "ERROR: NODE0_IP and NODE1_IP must be set for multi-node PyTorch profiling"
  exit 2
fi

SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
SCP=(scp -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)

GPU_LIST=$(python3 - <<PYG
print(','.join(str(i) for i in range(int('$GPUS'))))
PYG
)

stop_ray_both(){
  echo "Terminating Ray and vLLM processes on Node 0 and Node 1 for cold cache isolation..."
  kill "${SERVER_PID:-}" 2>/dev/null || true
  ray stop -f >/dev/null 2>&1 || true
  "${SSH[@]}" "$NODE1_IP" "$REMOTE_V6_ENV source '$VENV_DIR/bin/activate' 2>/dev/null || true; ray stop -f >/dev/null 2>&1 || true" || true
  sleep 3
  for _ in $(seq 1 30); do
    used_vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | awk '{s+=$1} END {print s}' || echo 0)
    if [[ "$used_vram" -lt 2500 ]]; then break; fi
    sleep 1
  done
}
trap stop_ray_both EXIT

echo "===== STARTING MULTI-NODE PYTORCH PROFILING: $TOPO_NAME (TP=$TP PP=$PP GPUs/node=$GPUS) ====="
stop_ray_both

# Clean up stale traces from /tmp on both nodes
rm -f /tmp/*.pt.trace.json* /tmp/vllm_torch_traces/*.pt.trace.json* 2>/dev/null || true
"${SSH[@]}" "$NODE1_IP" "rm -f /tmp/*.pt.trace.json* /tmp/vllm_torch_traces/*.pt.trace.json* 2>/dev/null || true" || true

# Start Ray Cluster
echo "Starting Ray head on node0 ($NODE0_IP) with $GPUS GPUs..."
CUDA_VISIBLE_DEVICES="$GPU_LIST" ray start --head --node-ip-address="$NODE0_IP" --port=6379 --num-gpus="$GPUS" > "$PROFILE_ROOT/ray_start_node0.log" 2>&1

echo "Starting Ray worker on node1 ($NODE1_IP) with $GPUS GPUs..."
"${SSH[@]}" "$NODE1_IP" "$REMOTE_V6_ENV source '$VENV_DIR/bin/activate'; CUDA_VISIBLE_DEVICES='$GPU_LIST' ray start --address='$NODE0_IP:6379' --num-gpus='$GPUS'" > "$PROFILE_ROOT/ray_start_node1.log" 2>&1
sleep 6

ray status > "$PROFILE_ROOT/ray_status.log" 2>&1 || { echo "Ray status failed"; exit 3; }

export VLLM_TORCH_PROFILER_DIR="/tmp/vllm_torch_traces"
export TORCH_PROFILER_OUTPUT_DIR="/tmp/vllm_torch_traces"
mkdir -p "$VLLM_TORCH_PROFILER_DIR"
"${SSH[@]}" "$NODE1_IP" "mkdir -p /tmp/vllm_torch_traces" || true

PROF_JSON=$(python3 - <<PY
import json
print(json.dumps({
  "profiler": "torch",
  "torch_profiler_dir": "/tmp/vllm_torch_traces",
  "torch_profiler_record_shapes": True,
  "torch_profiler_with_memory": False,
  "torch_profiler_with_stack": True,
  "torch_profiler_with_flops": False
}))
PY
)

echo "Starting distributed vLLM server ($TOPO_NAME)..."
vllm serve "$MODEL" --revision "$REVISION" --model-impl vllm --trust-remote-code --host 0.0.0.0 --port "$PORT" \
  --tensor-parallel-size "$TP" --pipeline-parallel-size "$PP" --distributed-executor-backend ray \
  --max-model-len 1048576 --max-num-batched-tokens 8192 --max-num-seqs 64 \
  --gpu-memory-utilization 0.9 --performance-mode balanced --optimization-level 2 \
  --moe-backend flashinfer_cutlass --enable-flashinfer-autotune \
  --no-enable-prefix-caching --enable-logging-iteration-details --profiler-config "$PROF_JSON" \
  > "$PROFILE_ROOT/server.log" 2>&1 & SERVER_PID=$!

cleanup_all(){
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  stop_ray_both
}
trap cleanup_all EXIT

for _ in $(seq 1 1800); do
  curl -fsS "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && break
  kill -0 "$SERVER_PID" 2>/dev/null || { echo "Server failed to launch; check server.log"; exit 3; }
  sleep 2
done

echo "Launching benchmark load in background (input=$INPUT_LEN, output=$OUTPUT_LEN, concurrency=$CONCURRENCY)..."
vllm bench serve --backend openai --host 127.0.0.1 --port "$PORT" --endpoint /v1/completions --model "$MODEL" --trust-remote-code \
  --dataset-name random --random-input-len "$INPUT_LEN" --random-output-len "$OUTPUT_LEN" --random-range-ratio 0 \
  --num-prompts "$CONCURRENCY" --max-concurrency "$CONCURRENCY" --num-warmups 0 --ignore-eos \
  --save-result --save-detailed --result-dir "$PROFILE_ROOT" --result-filename bench.json > "$PROFILE_ROOT/bench.log" 2>&1 & BENCH_PID=$!

# Wait for prefill to complete so the profiler captures steady-state batched decode
if [[ "$CONCURRENCY" -ge 32 ]]; then
  echo "Waiting 18 seconds for 32x 8K prefills to complete across pipeline..."
  sleep 18
else
  echo "Waiting 8 seconds for ${CONCURRENCY}x 8K prefills to complete across pipeline..."
  sleep 8
fi

echo "Triggering /start_profile for pure decode capture across all ranks..."
curl -s -X POST "http://127.0.0.1:$PORT/start_profile" || true

echo "Capturing 4.0 seconds of steady-state distributed batched decode..."
sleep 4.0

echo "Triggering /stop_profile..."
curl -s -X POST "http://127.0.0.1:$PORT/stop_profile" || true

echo "Waiting for benchmark client to finish..."
wait "$BENCH_PID" 2>/dev/null || true

cleanup_all
trap - EXIT

# Collect traces from Node 0
find /tmp -maxdepth 2 -name '*.pt.trace.json*' -exec mv -f {} "$PROFILE_ROOT/torch/node0/" \; 2>/dev/null || true
find "$PWD" -maxdepth 2 -name '*.pt.trace.json*' -exec mv -f {} "$PROFILE_ROOT/torch/node0/" \; 2>/dev/null || true

# Collect traces from Node 1 via SCP
echo "Collecting PyTorch traces from Node 1 ($NODE1_IP)..."
"${SCP[@]}" "$NODE1_IP:/tmp/vllm_torch_traces/*.pt.trace.json*" "$PROFILE_ROOT/torch/node1/" 2>/dev/null || true
"${SCP[@]}" "$NODE1_IP:/tmp/*.pt.trace.json*" "$PROFILE_ROOT/torch/node1/" 2>/dev/null || true

# Validate captured multi-node traces
python3 - <<'PY' "$PROFILE_ROOT" "$TOPO_NAME" "$CONCURRENCY" "$TP" "$PP"
import json, sys, glob
from pathlib import Path
root = Path(sys.argv[1]); topo = sys.argv[2]; conc = int(sys.argv[3])
tp = int(sys.argv[4]); pp = int(sys.argv[5])
expected_ranks = tp * pp

traces_node0 = list((root / "torch" / "node0").rglob("*.pt.trace.json*"))
traces_node1 = list((root / "torch" / "node1").rglob("*.pt.trace.json*"))
total_traces = traces_node0 + traces_node1

res = {
  "profile_dir": str(root),
  "topology": topo,
  "tp": tp,
  "pp": pp,
  "total_expected_ranks": expected_ranks,
  "traces_found_node0": len(traces_node0),
  "traces_found_node1": len(traces_node1),
  "total_trace_files": len(total_traces),
  "node0_files": [t.name for t in traces_node0],
  "node1_files": [t.name for t in traces_node1],
  "concurrency": conc,
  "status": "CAPTURED" if len(total_traces) > 0 else "NO_TRACES_FOUND"
}
(root / "TORCH_MULTI_NODE_PROFILE_VALIDATION.json").write_text(json.dumps(res, indent=2))
print("Torch Multi-Node Profile Validation:\n", json.dumps(res, indent=2))
PY

echo "Distributed Torch Profile completed: $PROFILE_ROOT"
