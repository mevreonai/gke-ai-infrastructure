#!/usr/bin/env python3
"""
04_test_chat.py
Test inference against DeepSeek-V4.1-Flash on 8x H100
"""

import sys
import time
import json
import urllib.request

DEFAULT_HOST = "localhost"

def test_inference(host=DEFAULT_HOST, port=8000):
    url = f"http://{host}:{port}/v1/chat/completions"
    
    payload = {
        "model": "deepseek-ai/DeepSeek-V4.1-Flash",
        "messages": [
            {
                "role": "user",
                "content": "Explain the architecture of DeepSeek V4 in 2 concise sentences."
            }
        ],
        "max_tokens": 128,
        "temperature": 0.7
    }
    
    print(f"[*] Sending prompt to {url}...")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latency = time.time() - t0
            
            choice = data["choices"][0]["message"]["content"]
            tokens = data["usage"]["completion_tokens"]
            tok_per_sec = tokens / latency if latency > 0 else 0
            
            print(f"\n[+] Success! Latency: {latency:.2f}s ({tok_per_sec:.1f} tokens/s)")
            print("\n--- Model Response ---")
            print(choice.strip())
            print("----------------------\n")
            print(f"Usage: {data['usage']}")
            
    except Exception as e:
        print(f"[-] Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    target_host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    test_inference(target_host)
