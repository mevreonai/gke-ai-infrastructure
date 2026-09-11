"""
Test inference client for Multi-Host TPU Ray Service (OpenAI-compatible API)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/v1"

def test_health():
    print("Checking models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        print(f"Status Code: {response.status_code}")
        print("Models:", json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"Failed to connect to {BASE_URL}: {e}")
        return False

def test_chat_completion(prompt="Explain the architecture of Multi-Host Google Cloud TPUs in 3 concise bullet points."):
    print(f"\nSending inference request: '{prompt}'...")
    start_time = time.time()
    
    payload = {
        "model": "google/gemma-2-27b-it",
        "messages": [
            {"role": "system", "content": "You are a helpful and expert AI assistant running on Google Cloud TPU v5e multi-host infrastructure."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat/completions", json=payload)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            print("\n=================== MODEL RESPONSE ===================")
            print(reply)
            print("=======================================================")
            print(f"Inference Time: {elapsed:.2f} seconds")
            if "usage" in result:
                print(f"Token Usage: {result['usage']}")
        else:
            print(f"Error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    if test_health():
        test_chat_completion()
