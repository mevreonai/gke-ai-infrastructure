#!/usr/bin/env python3
"""
DeepSeek-V4.1-Flash (TP=8) Inference & Prometheus Metrics Verification Client
"""

import sys
import time
import argparse
import requests
import json

def parse_prometheus_metrics(raw_text):
    metrics = {}
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            key, val = parts[0], parts[1]
            try:
                metrics[key] = float(val)
            except ValueError:
                metrics[key] = val
    return metrics

def check_health(base_url, timeout=300):
    health_url = f"{base_url}/health"
    print(f"Checking health at {health_url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(health_url, timeout=5)
            if resp.status_code == 200:
                print("Engine is HEALTHY and ready to serve!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)
        print(".", end="", flush=True)
    print("\nTimeout waiting for engine health.")
    return False

def get_metrics(base_url):
    metrics_url = f"{base_url}/metrics"
    try:
        resp = requests.get(metrics_url, timeout=5)
        if resp.status_code == 200:
            return parse_prometheus_metrics(resp.text)
    except Exception as e:
        print(f"Warning: Could not fetch metrics: {e}")
    return {}

def test_inference(base_url, prompt="Explain the core principles of Tensor Parallelism in 3 bullet points."):
    url = f"{base_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "/models/deepseek-ai/DeepSeek-V4.1-Flash",
        "messages": [
            {"role": "system", "content": "You are a helpful and concise technical assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 256,
        "stream": True
    }

    print("\n" + "="*50)
    print(f"Prompt: {prompt}")
    print("="*50)
    print("Streaming response:")

    start_time = time.time()
    ttft = None
    generated_text = ""
    token_count = 0

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        response.raise_for_status()

        for chunk in response.iter_lines():
            if not chunk:
                continue
            line = chunk.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        if ttft is None:
                            ttft = time.time() - start_time
                        print(delta, end="", flush=True)
                        generated_text += delta
                        token_count += 1
                except json.JSONDecodeError:
                    continue

        total_time = time.time() - start_time
        throughput = token_count / total_time if total_time > 0 else 0

        print("\n" + "="*50)
        print("Performance Benchmark Results:")
        print(f"Time to First Token (TTFT): {ttft:.4f}s" if ttft else "TTFT: N/A")
        print(f"Total Execution Time:        {total_time:.2f}s")
        print(f"Generated Tokens:            {token_count}")
        print(f"Throughput:                  {throughput:.2f} tokens/sec")
        print("="*50)

    except Exception as e:
        print(f"\nInference failed: {e}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Test DeepSeek TP=8 and Prometheus Metrics")
    parser.add_argument("--host", default="localhost", help="Host IP or hostname")
    parser.add_argument("--port", type=int, default=8000, help="vLLM port")
    parser.add_argument("--prompt", default="Explain the core principles of Tensor Parallelism in 3 bullet points.", help="Prompt to test")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    if not check_health(base_url):
        sys.exit(1)

    print("\n[Prometheus] Pre-inference cache stats:")
    pre_metrics = get_metrics(base_url)
    for k in ["vllm:gpu_cache_usage_factor", "vllm:num_requests_running"]:
        if k in pre_metrics:
            print(f"  {k}: {pre_metrics[k]}")

    success = test_inference(base_url, prompt=args.prompt)

    print("\n[Prometheus] Post-inference stats:")
    post_metrics = get_metrics(base_url)
    for k in ["vllm:gpu_cache_usage_factor", "vllm:num_prompt_tokens_total", "vllm:num_generation_tokens_total"]:
        if k in post_metrics:
            print(f"  {k}: {post_metrics[k]}")

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
