#!/usr/bin/env bash
# Focused vLLM layer/kernel trace using Kimi-Linear 48B.
# Intended for 8K/128K profile probes, not 1M production benchmarking.
set -euo pipefail

: "${MODEL:=moonshotai/Kimi-Linear-48B-A3B-Instruct}"
: "${TP:=4}"
: "${INPUT_LEN:=131072}"
: "${OUTPUT_LEN:=32}"
: "${PORT:=8010}"
: "${PROFILE_ROOT:=$HOME/rtx_g4_smoke/v5_profiles/$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$PROFILE_ROOT"

command -v nsys >/dev/null || { echo "nsys not installed; see vLLM profiling docs."; exit 2; }
command -v vllm >/dev/null || { echo "vllm CLI missing; activate V5 venv."; exit 2; }

export VLLM_WORKER_MULTIPROC_METHOD=spawn

SERVER_CMD=(
  vllm serve "$MODEL"
  --model-impl vllm
  --trust-remote-code
  --host 0.0.0.0 --port "$PORT"
  --tensor-parallel-size "$TP"
  --max-model-len 1048576
  --max-num-batched-tokens 8192
  --no-enable-prefix-caching
  --no-enable-flashinfer-autotune
  --enforce-eager
  --enable-layerwise-nvtx-tracing
  --enable-logging-iteration-details
  --profiler-config.profiler cuda
)

printf '%q ' "${SERVER_CMD[@]}" > "$PROFILE_ROOT/server_command.txt"; echo >> "$PROFILE_ROOT/server_command.txt"

nsys profile \
  --trace-fork-before-exec=true \
  --cuda-graph-trace=node \
  --trace=cuda,cudnn,cublas,osrt,nvtx \
  --capture-range=cudaProfilerApi \
  --capture-range-end=repeat \
  -o "$PROFILE_ROOT/vllm_profile" \
  "${SERVER_CMD[@]}" \
  > "$PROFILE_ROOT/server.log" 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "Waiting for server..."
for i in $(seq 1 1800); do
  if curl -fsS "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Server exited. See $PROFILE_ROOT/server.log"; exit 3
  fi
  sleep 2
done

vllm bench serve \
  --backend openai \
  --host 127.0.0.1 --port "$PORT" \
  --endpoint /v1/completions \
  --model "$MODEL" --trust-remote-code \
  --dataset-name random \
  --random-input-len "$INPUT_LEN" \
  --random-output-len "$OUTPUT_LEN" \
  --random-range-ratio 0 \
  --num-prompts 1 \
  --max-concurrency 1 \
  --ignore-eos \
  --profile \
  --save-result --save-detailed \
  --result-dir "$PROFILE_ROOT" \
  --result-filename bench.json \
  > "$PROFILE_ROOT/bench.log" 2>&1

cleanup
trap - EXIT

REP=$(find "$PROFILE_ROOT" -name '*.nsys-rep' | head -1 || true)
if [ -n "$REP" ]; then
  nsys stats --report cuda_gpu_kern_sum,cuda_api_sum,nvtx_pushpop_sum "$REP" \
    > "$PROFILE_ROOT/nsys_stats.txt" 2>&1 || true

  # Machine-readable reports for V5 team summary. If a report is unsupported,
  # keep the failure log and leave the corresponding chart unresolved.
  nsys stats --format csv --report cuda_gpu_kern_sum "$REP" \
    > "$PROFILE_ROOT/cuda_gpu_kern_sum.csv" 2> "$PROFILE_ROOT/cuda_gpu_kern_sum.err" || true
  nsys stats --format csv --report cuda_api_sum "$REP" \
    > "$PROFILE_ROOT/cuda_api_sum.csv" 2> "$PROFILE_ROOT/cuda_api_sum.err" || true
  nsys stats --format csv --report nvtx_pushpop_sum "$REP" \
    > "$PROFILE_ROOT/nvtx_pushpop_sum.csv" 2> "$PROFILE_ROOT/nvtx_pushpop_sum.err" || true
else
  echo "No .nsys-rep found; inspect server.log."
fi

cat > "$PROFILE_ROOT/INTERPRETATION.txt" <<'EOF'
This trace measures the real Kimi-Linear vLLM KDA/MLA/MoE/runtime path on RTX PRO.
Use it to identify:
- kernel names/backends actually selected
- KDA vs full-attention/MLA layer time
- NCCL/custom collective frequency
- launch gaps / CPU scheduling gaps
- overlap patterns

Do NOT scale absolute layer times from 48B to K3.
Exact K3 collective count and K3 kernel dimensions still require the real K3 trace.
EOF

echo "Profile results: $PROFILE_ROOT"
