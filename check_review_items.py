import json
import torch

print("=== CHECK 1: CONFIG.JSON ===")
with open("/data/models/deepseek-v4.1-flash/config.json") as f:
    cfg = json.load(f)
print(json.dumps(cfg, indent=2))



print("\n=== CHECK 2: ROUTER & IMAGE_SENTINEL_LO ===")
try:
    from vllm.models.deepseek_v4_1.common.mm_preprocess import IMAGE_SENTINEL_BASE_ID
    print("IMAGE_SENTINEL_BASE_ID:", IMAGE_SENTINEL_BASE_ID)
except Exception as e:
    print("Error importing IMAGE_SENTINEL_BASE_ID:", e)

with open("/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/models/deepseek_v4_1/nvidia/model.py") as f:
    lines = f.readlines()
    print("deepseek_v4_1 lines 105-135:")
    for i in range(105, min(135, len(lines))):
        print(f"  {i+1}: {lines[i].strip()}")





print("\n=== CHECK 3: TID2EID HASH ROUTING LAYERS ===")
# Check safetensors or config to see which layers have tid2eid
import glob
from safetensors import safe_open

tid2eid_layers = []
bias_vl_layers = []
image_sentinel_layers = []

st_files = sorted(glob.glob("/data/models/deepseek-v4.1-flash/*.safetensors"))
print(f"Scanning {len(st_files)} safetensors files for tid2eid, bias_vl...")
for sf in st_files:
    with safe_open(sf, framework="pt", device="cpu") as f:
        for k in f.keys():
            if "tid2eid" in k:
                tid2eid_layers.append(k)
            if "bias_vl" in k:
                bias_vl_layers.append(k)

print(f"Found {len(tid2eid_layers)} tid2eid tensors: {tid2eid_layers}")
print(f"Found {len(bias_vl_layers)} bias_vl tensors: {bias_vl_layers}")
