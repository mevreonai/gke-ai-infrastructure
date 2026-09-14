#!/usr/bin/env python3
"""
05_test_chat.py
Test chat completions against the Kimi-K3 vLLM Ray Server
Usage:
    python3 05_test_chat.py [--host HOST] [--port PORT]
"""

import argparse
import json
import time
import requests

def test_kimi_chat(host="localhost", port=8000):
    url = f"http://{host}:{port}/v1/chat/completions"
    model_name = "moonshotai/Kimi-K3"

    print("======================================================================")
    print(f" Testing Kimi-K3 Inference via vLLM Ray API Server")
    print(f" Target Endpoint: {url}")
    print(f" Target Model:    {model_name}")
    print("======================================================================\n")

    # 1. Health check
    try:
        health_url = f"http://{host}:{port}/health"
        res = requests.get(health_url, timeout=5)
        print(f"[*] Health Check status: {res.status_code}")
    except Exception as e:
        print(f"[-] Health Check failed: {e}")

    # 2. Prompt test
    prompt = (
        "Explain the key architectural innovations in Kimi-K3, particularly "
        "KDA (Kimi Delta Attention) and Gated MLA, in 3 concise bullet points."
    )
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are Kimi, an AI assistant developed by Moonshot AI."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 250,
        "temperature": 0.6,
        "stream": True
    }

    print(f"[*] Prompt: \"{prompt}\"\n")
    print("[*] Streaming response from 24 GPUs (3 Nodes x 8 GPUs):")
    print("----------------------------------------------------------------------")

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, stream=True, timeout=60)
        first_token_time = None
        full_response = ""

        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: ") and line_str != "data: [DONE]":
                    data = json.loads(line_str[6:])
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        if first_token_time is None:
                            first_token_time = time.time() - start_time
                        print(delta, end="", flush=True)
                        full_response += delta

        total_time = time.time() - start_time
        print("\n----------------------------------------------------------------------")
        print(f"[*] Success! Time to first token: {first_token_time:.2f}s | Total elapsed: {total_time:.2f}s")

    except Exception as e:
        print(f"\n[-] Error querying API: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="API server host")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    args = parser.parse_args()
    test_kimi_chat(args.host, args.port)
