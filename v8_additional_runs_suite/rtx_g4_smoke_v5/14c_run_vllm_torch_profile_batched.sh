#!/usr/bin/env bash
# Dedicated PyTorch profiler run at batch (c8 and c32) with CUDA graphs ON.
# Captures a pure-decode window by triggering /start_profile and /stop_profile via HTTP
# AFTER all prefill first tokens have completed, eliminating prefill kernel contamination.
set -euo pipefail
: "${MODEL:=moonshotai/Kimi-Linear-48B-A3B-Instruct}"
: "${REVISION:=e1df551a447157d4658b573f9a695d57658590e9}"
: "${TP:=4}"; : "${INPUT_LEN:=8192}"; : "${OUTPUT_LEN:=1024}"; : "${CONCURRENCY:=8}"; : "${PORT:=8021}"
: "${PROFILE_ROOT:=$HOME/v8_additional_runs/torch_profiles/$(date +%Y%m%d_%H%M%S)_tp${TP}_c${CONCURRENCY}}"
mkdir -p "$PROFILE_ROOT"
command -v vllm >/dev/null || exit 2

export CUDA_VISIBLE_DEVICES=$(python3 - <<PY
print(','.join(str(i) for i in range(int('$TP'))))
PY
)

PROF_JSON=$(python3 - <<PY
import json
print(json.dumps({
  "profiler": "torch",
  "torch_profiler_dir": "$PROFILE_ROOT/torch",
  "torch_profiler_record_shapes": True,
  "torch_profiler_with_memory": False,
  "torch_profiler_with_stack": True,
  "torch_profiler_with_flops": False
}))
PY
)

echo "Starting vLLM server with full serving optimization flags..."
vllm serve "$MODEL" --revision "$REVISION" --model-impl vllm --trust-remote-code --host 0.0.0.0 --port "$PORT" \
  --tensor-parallel-size "$TP" --max-model-len 1048576 --max-num-batched-tokens 8192 --max-num-seqs 64 \
  --gpu-memory-utilization 0.9 --performance-mode balanced --optimization-level 2 \
  --no-enable-prefix-caching --enable-logging-iteration-details --profiler-config "$PROF_JSON" \
  > "$PROFILE_ROOT/server.log" 2>&1 & PID=$!

cleanup(){ kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT

for _ in $(seq 1 1800); do
  curl -fsS "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && break
  kill -0 "$PID" 2>/dev/null || exit 3
  sleep 2
done

echo "Launching benchmark load in background (input=$INPUT_LEN, output=$OUTPUT_LEN, concurrency=$CONCURRENCY)..."
vllm bench serve --backend openai --host 127.0.0.1 --port "$PORT" --endpoint /v1/completions --model "$MODEL" --trust-remote-code \
  --dataset-name random --random-input-len "$INPUT_LEN" --random-output-len "$OUTPUT_LEN" --random-range-ratio 0 \
  --num-prompts "$CONCURRENCY" --max-concurrency "$CONCURRENCY" --num-warmups 0 --ignore-eos \
  --save-result --save-detailed --result-dir "$PROFILE_ROOT" --result-filename bench.json > "$PROFILE_ROOT/bench.log" 2>&1 & BENCH_PID=$!

# Wait for prefill to complete so the profiler window captures pure decode
if [[ "$CONCURRENCY" -ge 32 ]]; then
  echo "Waiting 16 seconds for 32x 8K prefills to complete..."
  sleep 16
else
  echo "Waiting 6 seconds for ${CONCURRENCY}x 8K prefills to complete..."
  sleep 6
fi

echo "Triggering /start_profile for pure decode capture..."
curl -s -X POST "http://127.0.0.1:$PORT/start_profile" || true

echo "Capturing 3.5 seconds of steady-state batched decode..."
sleep 3.5

echo "Triggering /stop_profile..."
curl -s -X POST "http://127.0.0.1:$PORT/stop_profile" || true

echo "Waiting for benchmark client to finish..."
wait "$BENCH_PID" 2>/dev/null || true

cleanup
trap - EXIT

# Validate that trace exists and post-process
python3 - <<'PY' "$PROFILE_ROOT" "$CONCURRENCY"
import json, sys, glob
from pathlib import Path
root = Path(sys.argv[1]); conc = int(sys.argv[2])
traces = list(root.rglob("*.pt.trace.json*"))
target_step_ms = 7.7 if conc == 8 else 15.8
res = {
  "profile_dir": str(root),
  "concurrency": conc,
  "trace_files_found": [str(t) for t in traces],
  "target_serving_step_ms": target_step_ms,
  "status": "CAPTURED" if len(traces) > 0 else "NO_TRACES_FOUND"
}
(root / "TORCH_PROFILE_VALIDATION.json").write_text(json.dumps(res, indent=2))
print("Torch Profile Validation:\n", json.dumps(res, indent=2))
PY

echo "Batched Torch profile complete: $PROFILE_ROOT"
