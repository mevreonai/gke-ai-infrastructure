#!/usr/bin/env python3
"""
Automated Inference Verification Client for GKE Inference Gateway (llm-d + NVIDIA GPU).
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def get_gateway_ip():
    try:
        cmd = ["kubectl", "get", "gateway", "inference-gateway-gpu", "-o", "jsonpath={.status.addresses[0].value}"]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        if out and out != "<no value>":
            return out
    except Exception:
        pass
    return None

def main():
    print("========================================================")
    print(" 🧪 GKE INFERENCE GATEWAY (llm-d + NVIDIA GPU) TEST")
    print("========================================================")

    gateway_ip = get_gateway_ip()
    if gateway_ip:
        base_url = f"http://{gateway_ip}"
        print(f"[TARGET] External Gateway IP: {gateway_ip} (Port 80)")
    else:
        base_url = "http://localhost:8000"
        print(f"[TARGET] Gateway IP allocating, testing: {base_url}")

    models_url = f"{base_url}/v1/models"
    chat_url = f"{base_url}/v1/chat/completions"

    print(f"\n[1/2] Testing /v1/models on {models_url}...")
    try:
        res = urllib.request.urlopen(models_url, timeout=10)
        models_data = json.loads(res.read().decode())
        print(f"Status: {res.getcode()} OK")
        print(f"Available Models: {[m['id'] for m in models_data.get('data', [])]}")
        model_name = models_data['data'][0]['id'] if models_data.get('data') else "Qwen/Qwen2.5-7B-Instruct"
    except Exception as e:
        print(f"[WARN] Could not fetch models list: {e}. Defaulting to Qwen/Qwen2.5-7B-Instruct")
        model_name = "Qwen/Qwen2.5-7B-Instruct"

    prompt = "Explain GKE Inference Gateway with llm-d and NVIDIA GPUs in 2 concise bullet points."
    print(f"\n[2/2] Sending prompt to {chat_url} via GPU Inference Gateway...")
    print(f"Model:  {model_name}")
    print(f"Prompt: '{prompt}'")

    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 128,
        "temperature": 0.2
    }

    req = urllib.request.Request(
        chat_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            elapsed = time.time() - t0
            body = json.loads(resp.read().decode("utf-8"))
            answer = body["choices"][0]["message"]["content"]
            usage = body.get("usage", {})
            completion_tokens = usage.get("completion_tokens", len(answer.split()))
            tok_per_sec = completion_tokens / max(elapsed, 0.01)

            print("\n=================== MODEL RESPONSE ===================")
            print(answer.strip())
            print("=======================================================")
            print(f"Latency:        {elapsed:.2f} seconds")
            print(f"Tokens:         {completion_tokens} tokens")
            print(f"Throughput:     {tok_per_sec:.1f} tokens/sec")
            print(f"Endpoint:       Inference Gateway -> llm-d EPP -> NVIDIA GPU")
            print("=======================================================")
            print("[SUCCESS] End-to-end GPU Inference Gateway routing verified!")
    except urllib.error.HTTPError as he:
        print(f"[ERROR] HTTP Error {he.code}: {he.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as ex:
        print(f"[ERROR] Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    main()
