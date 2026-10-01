#!/usr/bin/env bash
set -e
export CUDA_HOME=/usr/local/cuda
export PATH=/usr/local/cuda/bin:$PATH
export CPATH=/usr/local/cuda/include:${CPATH:-}
export LIBRARY_PATH=/usr/local/cuda/lib64:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}

source /etc/profile.d/cuda.sh 2>/dev/null || true
source /home/ayu23/vllm_env/bin/activate

echo "=== Starting Clean Live Token Smoke Test with --block-size 128 ==="

# Clean any previous processes
sudo pkill -9 -f "Worker_TP" 2>/dev/null || true
sudo pkill -9 -f "vllm" 2>/dev/null || true
sleep 4

PORT=8999
LOG=/tmp/vllm_live_smoke.log
rm -f "$LOG"

echo "Launching vLLM server on TP=8, port $PORT with --block-size 128..."
nohup python3 -m vllm.entrypoints.openai.api_server \
  --model /data/models/deepseek-v4.1-flash \
  --model-impl vllm \
  --host 0.0.0.0 \
  --port $PORT \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 1 \
  --block-size 128 \
  --max-model-len 8192 \
  --max-num-batched-tokens 4096 \
  --kv-cache-dtype auto \
  --gpu-memory-utilization 0.85 \
  --trust-remote-code \
  --language-model-only > "$LOG" 2>&1 &

SERVER_PID=$!
echo "Server PID: $SERVER_PID. Waiting for /health..."

HEALTHY=0
for i in $(seq 1 120); do
    sleep 5
    if curl -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
        echo "=== Server is HEALTHY after $((i * 5)) seconds! ==="
        HEALTHY=1
        break
    fi
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "ERROR: Server process exited! Tailing log:"
        tail -n 40 "$LOG"
        exit 1
    fi
    if [ $((i % 6)) -eq 0 ]; then
        echo "[$((i * 5))s] Loading weights / JIT compiling... (PID $SERVER_PID alive)"
    fi
done

if [ "$HEALTHY" -ne 1 ]; then
    echo "ERROR: Timed out waiting for /health! Tailing log:"
    tail -n 40 "$LOG"
    kill -9 $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "Sending completion request..."
RESPONSE=$(curl -s "http://127.0.0.1:$PORT/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/data/models/deepseek-v4.1-flash",
    "prompt": "Artificial intelligence infrastructure on NVIDIA Blackwell",
    "max_tokens": 32,
    "temperature": 0.0
  }')

echo "=== RAW COMPLETION RESPONSE ==="
echo "$RESPONSE"

echo "Cleaning up test server..."
kill -9 $SERVER_PID 2>/dev/null || true
sudo pkill -9 -f "Worker_TP" 2>/dev/null || true

if echo "$RESPONSE" | grep -q '"text"'; then
    echo "=== SUCCESS: REAL TOKENS GENERATED AND VERIFIED! ==="
    exit 0
else
    echo "ERROR: Completion did not contain text field!"
    exit 2
fi
