import sys

print("=== INSPECTING MODEL.PY ===")
with open("/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/models/deepseek_v4/nvidia/model.py") as f:
    lines = f.readlines()
for i in range(800, 1060):
    if any(k in lines[i] for k in ["class DeepseekV4MoE", "class DeepseekV4", "def __init__", "def forward", "bias_vl", "input_tokens", "tid2eid"]):
        print(f"L{i+1}: {lines[i].strip()}")

print("\n=== INSPECTING MULTIMODAL CONFIG IN VLLM ===")
from vllm.config import VllmConfig, ModelConfig
print("ModelConfig attributes with multimodal/language:")
print([a for a in dir(ModelConfig) if "multimodal" in a or "language" in a])

print("\n=== INSPECTING UTILS.PY ALLOCATE_KV_CACHE ===")
with open("/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/v1/worker/utils.py") as f:
    lines = f.readlines()
for i in range(410, 460):
    print(f"L{i+1}: {lines[i]}", end="")

print("\n=== INSPECTING ATTN_UTILS.PY ===")
with open("/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/v1/attention/backends/mla/attn_utils.py") as f:
    lines = f.readlines()
for i in range(210, 235):
    print(f"L{i+1}: {lines[i]}", end="")
