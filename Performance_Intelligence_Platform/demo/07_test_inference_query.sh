#!/usr/bin/env bash
# ==============================================================================
# DEMO STEP 7: Test Live Inference Query Against the Served 48B Model
# ==============================================================================
set -euo pipefail

PORT="${PORT:-8000}"
MODEL_ID="${MODEL_ID:-moonshotai/Kimi-Linear-48B-A3B-Instruct}"

echo "======================================================================"
echo " [DEMO] Sending Live Chat Completion Request to 48B Model on Port $PORT"
echo "======================================================================"

curl -s "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"$MODEL_ID"'",
    "messages": [
      {"role": "system", "content": "You are an expert high-performance computing AI assistant."},
      {"role": "user", "content": "Explain in two sentences how tensor parallelism partitions a 48B model across 8 GPUs."}
    ],
    "max_tokens": 128,
    "temperature": 0.2
  }' | jq .
