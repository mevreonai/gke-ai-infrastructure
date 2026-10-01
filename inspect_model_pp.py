import json
import torch
import os
import sys

def inspect_config():
    cfg_path = '/data/models/deepseek-v4.1-flash/config.json'
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
        print("=== CONFIG.JSON ===")
        print("model_type:", cfg.get("model_type"))
        print("num_attention_heads:", cfg.get("num_attention_heads"))
        print("num_key_value_heads:", cfg.get("num_key_value_heads"))
        print("n_routed_experts:", cfg.get("n_routed_experts"))
        print("num_experts_per_tok:", cfg.get("num_experts_per_tok"))
        print("n_hash_cols (Engram):", cfg.get("n_hash_cols", cfg.get("engram_config", {}).get("n_hash_cols")))
        print("image_sentinel_lo:", cfg.get("image_sentinel_lo"))

def inspect_code_sentinel():
    import subprocess
    print("=== GREP IMAGE_SENTINEL_LO ===")
    res = subprocess.run(
        "grep -rn 'image_sentinel_lo' /home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/model_executor/layers/fused_moe",
        shell=True, capture_output=True, text=True
    )
    print(res.stdout)

def inspect_tid2eid():
    import subprocess
    print("=== GREP TID2EID IN MODEL LAYERS ===")
    res = subprocess.run(
        "grep -rn 'tid2eid' /home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4*",
        shell=True, capture_output=True, text=True
    )
    print(res.stdout)

if __name__ == '__main__':
    inspect_config()
    inspect_code_sentinel()
    inspect_tid2eid()
