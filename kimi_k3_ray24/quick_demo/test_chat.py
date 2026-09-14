#!/usr/bin/env python3
"""
test_chat.py - Live Interactive & Benchmark Client for Kimi-K3
Tests streaming chat completions against the 24-GPU vLLM Ray Cluster.

Usage:
    python test_chat.py [--host HOST] [--port PORT] [--prompt PROMPT]
"""

import argparse
import json
import time
import requests
import sys

def test_kimi_chat(host="localhost", port=8000, prompt=None):
    url = f"http://{host}:{port}/v1/chat/completions"
    model_name = "moonshotai/Kimi-K3"

    print("======================================================================")
    print(" Kimi-K3 Live 24-GPU Cluster Interactive Client")
    print(f" Target Endpoint: {url}")
    print(f" Target Model:    {model_name}")
    print("======================================================================\n")

    # 1. Health check
    try:
        health_url = f"http://{host}:{port}/health"
        res = requests.get(health_url, timeout=5)
        print(f"[*] Health Check Status: HTTP {res.status_code}")
    except Exception as e:
        print(f"[-] Health Check Warning (API may still be initializing): {e}")

    # 2. Prompt test
    if not prompt:
        prompt = (
            "Explain the architecture of Kimi-K3, focusing on KDA (Kimi Delta Attention) "
            "and Gated MLA, and why running this 1.45 TB MoE model requires a 24-GPU cluster."
        )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are Moonshot AI Kimi-K3, a 1.45 TB MoE foundation model running on a 24-GPU cluster."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 350,
        "temperature": 0.6,
        "stream": True
    }

    print(f"[*] Prompt: \"{prompt}\"\n")
    print("[*] Streaming response from 24 GPUs (TP=8 x PP=3):")
    print("----------------------------------------------------------------------")

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, stream=True, timeout=90)
        first_token_time = None
        full_response = ""
        token_count = 0

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
                        token_count += 1

        total_time = time.time() - start_time
        gen_time = max(0.001, total_time - (first_token_time or 0))
        tps = token_count / gen_time if token_count > 0 else 0

        print("\n----------------------------------------------------------------------")
        print(f"[*] TTFT (Time To First Token): {first_token_time:.2f}s" if first_token_time else "[*] TTFT: N/A")
        print(f"[*] Total Inference Time:      {total_time:.2f}s")
        print(f"[*] Estimated Output Speed:     {tps:.2f} tokens/s ({token_count} tokens)")
        print("======================================================================")

    except Exception as e:
        print(f"\n[-] Error querying API endpoint: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Kimi-K3 24-GPU Cluster")
    parser.add_argument("--host", default="localhost", help="API server IP / Hostname")
    parser.add_argument("--port", type=int, default=8000, help="API server Port (default: 8000)")
    parser.add_argument("--prompt", type=str, default=None, help="Custom prompt string")
    args = parser.parse_args()
    test_kimi_chat(args.host, args.port, args.prompt)
