#!/bin/bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-V4.1-Flash",
    "messages": [
      {"role": "user", "content": "what is on the 25 sept"}
    ],
    "temperature": 0.6,
    "max_tokens": 300
  }'
echo ""
