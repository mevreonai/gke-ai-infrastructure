import time
import sys
import os
import requests
from openai import OpenAI

BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")

print("=" * 60)
print(" 🚀 Disaggregated TPU Serving Benchmark (llm-d + vLLM)")
print("=" * 60)
print(f"Target URL: {BASE_URL}")
print(f"Model:      {MODEL_NAME}")

# 1. Health & Models API check
print("\n[Step 1] Checking Gateway Models Endpoint...")
try:
    resp = requests.get(f"{BASE_URL}/models", timeout=10)
    print(f"  Status Code: {resp.status_code}")
    print(f"  Available Models: {resp.json()}")
except Exception as e:
    print(f"  ⚠️ Warning connecting to /models: {e}")

# 2. Benchmark Streaming Latency (TTFT & TPOT)
client = OpenAI(base_url=BASE_URL, api_key="not-needed")

prompts = [
    "Explain the advantages of prefill and decode disaggregation in large language model inference in 3 bullet points.",
    "Write a short Python function implementing binary search with detailed comments."
]

print("\n[Step 2] Measuring Disaggregated TTFT and Token Generation...")

for idx, p in enumerate(prompts, 1):
    print(f"\n--- Test Prompt {idx} ---")
    print(f"Prompt: {p[:60]}...")
    
    start_time = time.time()
    first_token_time = None
    token_count = 0
    full_text = ""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": p}],
            stream=True,
            temperature=0.7,
            max_tokens=256
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                if first_token_time is None:
                    first_token_time = time.time()
                content = chunk.choices[0].delta.content
                full_text += content
                token_count += 1
                sys.stdout.write(content)
                sys.stdout.flush()

        end_time = time.time()
        print("\n")

        ttft = (first_token_time - start_time) * 1000 if first_token_time else 0
        total_time = end_time - start_time
        decode_time = end_time - first_token_time if first_token_time else 0
        tps = token_count / decode_time if decode_time > 0 else 0

        print(f"📊 Metrics:")
        print(f"   • Time-To-First-Token (TTFT): {ttft:.1f} ms (Prefill phase)")
        print(f"   • Total Response Time:        {total_time:.2f} s")
        print(f"   • Tokens Generated:           {token_count} tokens")
        print(f"   • Output Token Throughput:    {tps:.1f} tokens/sec (Decode phase)")

    except Exception as e:
        print(f"  ❌ Error during inference: {e}")

print("\n" + "=" * 60)
print(" ✅ Disaggregated Serving Benchmark Complete!")
print("=" * 60)
