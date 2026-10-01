from transformers import AutoConfig
import json

cfg = AutoConfig.from_pretrained('/data/models/deepseek-v4.1-flash', trust_remote_code=True)
d = cfg.to_dict()
for k, v in d.items():
    if "index" in k or "compress" in k or "state" in k or "token" in k:
        print(f"{k}: {v}")
