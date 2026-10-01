import json

path = "/home/ayu23/V9_FULL/configs/models/deepseek_v41_flash.json"
with open(path) as f:
    d = json.load(f)

d["model"] = "/data/models/deepseek-v4.1-flash"
d["trust_remote_code"] = True

with open(path, "w") as f:
    json.dump(d, f, indent=2)

print("CONFIG_UPDATED_SUCCESSFULLY")
