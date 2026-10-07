#!/usr/bin/env bash
# Dedicated high-overhead PyTorch profiler run. Keep separate from benchmark measurements.
set -euo pipefail
: "${MODEL:=moonshotai/Kimi-Linear-48B-A3B-Instruct}"
: "${REVISION:=e1df551a447157d4658b573f9a695d57658590e9}"
: "${TP:=4}"; : "${INPUT_LEN:=8192}"; : "${OUTPUT_LEN:=128}"; : "${CONCURRENCY:=1}"; : "${PORT:=8011}"
: "${PROFILE_ROOT:=$HOME/rtx_g4_smoke/v5_torch_profiles/$(date +%Y%m%d_%H%M%S)_tp${TP}}"
mkdir -p "$PROFILE_ROOT"; command -v vllm >/dev/null || exit 2
export CUDA_VISIBLE_DEVICES=$(python3 - <<PY
print(','.join(str(i) for i in range(int('$TP'))))
PY
)
PROF_JSON=$(python3 - <<PY
import json
print(json.dumps({"profiler":"torch","torch_profiler_dir":"$PROFILE_ROOT/torch","torch_profiler_record_shapes":True,"torch_profiler_with_memory":False,"torch_profiler_with_stack":True,"torch_profiler_with_flops":False}))
PY
)
vllm serve "$MODEL" --revision "$REVISION" --model-impl vllm --trust-remote-code --host 0.0.0.0 --port "$PORT" \
  --tensor-parallel-size "$TP" --max-model-len 1048576 --max-num-batched-tokens 8192 --max-num-seqs 16 \
  --no-enable-prefix-caching --enable-logging-iteration-details --profiler-config "$PROF_JSON" > "$PROFILE_ROOT/server.log" 2>&1 & PID=$!
cleanup(){ kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }; trap cleanup EXIT
for _ in $(seq 1 1800); do curl -fsS "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && break; kill -0 "$PID" 2>/dev/null || exit 3; sleep 2; done
vllm bench serve --backend openai --host 127.0.0.1 --port "$PORT" --endpoint /v1/completions --model "$MODEL" --trust-remote-code \
  --dataset-name random --random-input-len "$INPUT_LEN" --random-output-len "$OUTPUT_LEN" --random-range-ratio 0 \
  --num-prompts "$CONCURRENCY" --max-concurrency "$CONCURRENCY" --num-warmups 0 --ignore-eos --profile \
  --save-result --save-detailed --result-dir "$PROFILE_ROOT" --result-filename bench.json > "$PROFILE_ROOT/bench.log" 2>&1
cleanup; trap - EXIT
echo "Torch profile results: $PROFILE_ROOT"
