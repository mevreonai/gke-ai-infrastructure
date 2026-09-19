#!/usr/bin/env bash
# Phase-specific Nsight Systems profiling. Not intended for throughput benchmarking.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${MODEL:=moonshotai/Kimi-Linear-48B-A3B-Instruct}"
: "${REVISION:=e1df551a447157d4658b573f9a695d57658590e9}"
: "${TP:=4}"
: "${PROFILE_MODE:=prefill}"   # prefill | decode | batched_decode
: "${PORT:=8010}"
: "${PROFILE_ROOT:=$HOME/rtx_g4_smoke/v5_profiles/$(date +%Y%m%d_%H%M%S)_${PROFILE_MODE}_tp${TP}}"
mkdir -p "$PROFILE_ROOT"
command -v nsys >/dev/null || { echo "nsys not installed"; exit 2; }
command -v vllm >/dev/null || { echo "vllm CLI missing; activate vllm_env"; exit 2; }

case "$PROFILE_MODE" in
  prefill) INPUT_LEN=${INPUT_LEN:-131072}; OUTPUT_LEN=${OUTPUT_LEN:-8}; CONCURRENCY=${CONCURRENCY:-1}; PROMPTS=${PROMPTS:-1} ;;
  decode) INPUT_LEN=${INPUT_LEN:-8192}; OUTPUT_LEN=${OUTPUT_LEN:-512}; CONCURRENCY=${CONCURRENCY:-1}; PROMPTS=${PROMPTS:-1} ;;
  batched_decode) INPUT_LEN=${INPUT_LEN:-8192}; OUTPUT_LEN=${OUTPUT_LEN:-512}; CONCURRENCY=${CONCURRENCY:-8}; PROMPTS=${PROMPTS:-8} ;;
  *) echo "Unknown PROFILE_MODE=$PROFILE_MODE"; exit 2 ;;
esac

export CUDA_VISIBLE_DEVICES=$(python3 - <<PY
print(','.join(str(i) for i in range(int('$TP'))))
PY
)
export VLLM_WORKER_MULTIPROC_METHOD=spawn

SERVER_CMD=(vllm serve "$MODEL" --revision "$REVISION" --model-impl vllm --trust-remote-code --host 0.0.0.0 --port "$PORT"
  --tensor-parallel-size "$TP" --max-model-len 1048576 --max-num-batched-tokens 8192 --max-num-seqs 32
  --no-enable-prefix-caching --enforce-eager --enable-layerwise-nvtx-tracing --enable-logging-iteration-details
  --profiler-config.profiler cuda)
printf '%q ' "${SERVER_CMD[@]}" > "$PROFILE_ROOT/server_command.txt"; echo >> "$PROFILE_ROOT/server_command.txt"

NSYS_ARGS=(profile --trace-fork-before-exec=true --cuda-graph-trace=node --trace=cuda,nvtx,nccl,cublas,osrt
  --capture-range=cudaProfilerApi --capture-range-end=repeat -o "$PROFILE_ROOT/vllm_profile")
if nsys profile --help 2>&1 | grep -q -- '--nccl-trace'; then NSYS_ARGS+=(--nccl-trace=default); fi

nsys "${NSYS_ARGS[@]}" "${SERVER_CMD[@]}" > "$PROFILE_ROOT/server.log" 2>&1 & SERVER_PID=$!
cleanup(){ kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 1800); do
  curl -fsS "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1 && break
  kill -0 "$SERVER_PID" 2>/dev/null || { echo "Server exited; see server.log"; exit 3; }
  sleep 2
done

vllm bench serve --backend openai --host 127.0.0.1 --port "$PORT" --endpoint /v1/completions --model "$MODEL" --trust-remote-code \
  --dataset-name random --random-input-len "$INPUT_LEN" --random-output-len "$OUTPUT_LEN" --random-range-ratio 0 \
  --num-prompts "$PROMPTS" --max-concurrency "$CONCURRENCY" --ignore-eos --num-warmups 0 --profile \
  --save-result --save-detailed --result-dir "$PROFILE_ROOT" --result-filename bench.json > "$PROFILE_ROOT/bench.log" 2>&1
cleanup; trap - EXIT

REP=$(find "$PROFILE_ROOT" -name '*.nsys-rep' | head -1 || true)
if [[ -n "$REP" ]]; then
  nsys stats --report cuda_gpu_kern_sum,cuda_api_sum,nvtx_pushpop_sum "$REP" > "$PROFILE_ROOT/nsys_stats.txt" 2>&1 || true
  for r in cuda_gpu_kern_sum cuda_api_sum nvtx_pushpop_sum; do nsys stats --format csv --report "$r" "$REP" > "$PROFILE_ROOT/${r}.csv" 2> "$PROFILE_ROOT/${r}.err" || true; done
  nsys export --type sqlite --output "$PROFILE_ROOT/vllm_profile.sqlite" "$REP" > "$PROFILE_ROOT/nsys_export.log" 2>&1 || true
fi
cat > "$PROFILE_ROOT/PROFILE_METADATA.json" <<EOF
{"profile_mode":"$PROFILE_MODE","model":"$MODEL","revision":"$REVISION","tp":$TP,"input":$INPUT_LEN,"output":$OUTPUT_LEN,"concurrency":$CONCURRENCY,"prompts":$PROMPTS,"evidence_class":"MEASURED-48B-PROFILE","warning":"Aggregate kernel sums are GPU work, not wall-clock critical path. KDA/MLA/MoE attribution requires NVTX correlation; absolute times do not scale to K3."}
EOF
echo "Profile results: $PROFILE_ROOT"
