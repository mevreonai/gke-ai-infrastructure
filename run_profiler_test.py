import time
import subprocess
import json
import os
import sys

remote_runner = """#!/usr/bin/env bash
set -e
export PATH=/home/ayu23/vllm_env/bin:$PATH
export VLLM_LOGGING_LEVEL=INFO

# Cleanup old traces and logs
rm -rf /tmp/torch_traces
mkdir -p /tmp/torch_traces /tmp/prof_run

# Kill any lingering vllm
pkill -9 -f vllm || true
sleep 2

echo "Starting vLLM server with profiler enabled on TP=8..."
/home/ayu23/vllm_env/bin/python3 -m vllm.entrypoints.openai.api_server \
    --model /data/models/deepseek-v4.1-flash \
    --tensor-parallel-size 8 \
    --enforce-eager \
    --host 0.0.0.0 \
    --port 8000 \
    --profiler-config.profiler torch \
    --profiler-config.torch_profiler_dir /tmp/torch_traces \
    --profiler-config.torch_profiler_with_stack False \
    --profiler-config.torch_profiler_with_flops False \
    --profiler-config.torch_profiler_record_shapes True \
    > /tmp/prof_run/server.log 2>&1 &

SERVER_PID=$!
echo "Server started with PID $SERVER_PID. Waiting for health check..."

for i in {1..120}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "Server is HEALTHY after ${i} seconds!"
        break
    fi
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "Server process DIED prematurely!"
        cat /tmp/prof_run/server.log | tail -n 40
        exit 1
    fi
    sleep 2
done

echo "Running warmup inference..."
curl -s -X POST http://127.0.0.1:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "/data/models/deepseek-v4.1-flash",
        "prompt": "Explain the architectural advantages of DeepSeek sparse Multi-Head Latent Attention.",
        "max_tokens": 32,
        "temperature": 0.0
    }' > /tmp/prof_run/warmup.json

echo "Warmup response:"
cat /tmp/prof_run/warmup.json
echo ""

echo "Triggering POST /start_profile..."
START_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://127.0.0.1:8000/start_profile)
echo "Start profile response: $START_RESP"

echo "Sending profiled benchmark request (Long Prefill 4096 tokens + 128 decode tokens)..."
/home/ayu23/vllm_env/bin/python3 - << 'EOF'
import requests, json, time

# Generate a prompt of ~4096 tokens
words = "Blackwell SM120 tensor core architecture FP8 matrix acceleration " * 600
payload = {
    "model": "/data/models/deepseek-v4.1-flash",
    "prompt": words,
    "max_tokens": 64,
    "temperature": 0.0,
    "stream": False
}

t0 = time.time()
res = requests.post("http://127.0.0.1:8000/v1/completions", json=payload, timeout=300)
elapsed = time.time() - t0
print(f"Request status: {res.status_code}, Latency: {elapsed*1000:.2f} ms")
try:
    data = res.json()
    usage = data.get("usage", {})
    print(f"Prompt tokens: {usage.get('prompt_tokens')}, Completion tokens: {usage.get('completion_tokens')}")
except Exception as e:
    print(f"Error parsing response: {e}, text: {res.text[:200]}")
EOF

echo "Triggering POST /stop_profile..."
STOP_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://127.0.0.1:8000/stop_profile)
echo "Stop profile response: $STOP_RESP"

sleep 3
echo "Checking generated traces in /tmp/torch_traces:"
ls -lah /tmp/torch_traces

# Shut down server cleanly
kill -15 $SERVER_PID || true
sleep 3
"""

from exec_node import run_on_node

print("Starting profiler capture test on kimi-node-0...")
rc, out, err = run_on_node("kimi-node-0", remote_runner)
print(f"rc = {rc}")
print("STDOUT:")
print(out)
if err:
    print("STDERR:")
    print(err)
