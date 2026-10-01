import sys
from vllm import ModelRegistry
archs = ModelRegistry.get_supported_archs()
ds_archs = [a for a in archs if 'deepseek' in a.lower()]
print("Supported DeepSeek Architectures in installed vLLM:")
for a in ds_archs:
    print(" -", a)
