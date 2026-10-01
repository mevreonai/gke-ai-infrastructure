from transformers import AutoConfig
try:
    cfg = AutoConfig.from_pretrained("/data/models/deepseek-v4.1-flash", trust_remote_code=True)
    print("SUCCESS WITH LOCAL PATH:", type(cfg))
except Exception as e:
    print("FAILED LOCAL PATH:", repr(e))

try:
    cfg2 = AutoConfig.from_pretrained("deepseek-ai/DeepSeek-V4.1-Flash", trust_remote_code=True)
    print("SUCCESS WITH HF NAME:", type(cfg2))
except Exception as e:
    print("FAILED HF NAME:", repr(e))
