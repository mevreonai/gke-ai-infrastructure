"""
Test inference client for Multi-Host TPU Ray Service (OpenAI-compatible API)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/v1"

def get_active_model_id():
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            data = response.json().get("data", [])
            if data:
                return data[0]["id"]
    except Exception as e:
        print(f"Failed to query models: {e}")
    return "google/gemma-2-27b-it"

def test_health():
    print("Checking models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        print(f"Status Code: {response.status_code}")
        print("Models:", json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to connect to {BASE_URL}: {e}")
        return False

def test_chat_completion(prompt="Explain why multi-host TPU serving on GKE is ideal for Gemma 2 27B in 3 concise bullet points."):
    model_id = get_active_model_id()
    print(f"\nSending inference request using model '{model_id}'...")
    print(f"Prompt: '{prompt}'")
    start_time = time.time()
    
    # Gemma models require user role without system prompt in chat templates
    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 256
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat/completions", json=payload)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            print("\n=================== MODEL RESPONSE ===================")
            print(reply.strip())
            print("=======================================================")
            print(f"Inference Latency: {elapsed:.2f} seconds")
            if "usage" in result:
                print(f"Token Usage: {result['usage']}")
            return True
        else:
            print(f"Error ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    if test_health():
        test_chat_completion()
