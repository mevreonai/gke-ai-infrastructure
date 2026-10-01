
path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/attention.py"
with open(path, "r") as f:
    c = f.read()

target = """        self.swa_cache_layer = DeepseekV4SWACache(
            head_dim=self.head_dim,
            window_size=self.window_size,
            dtype=self.kv_cache_torch_dtype,
            prefix=f"{prefix}.swa_cache",
            cache_config=cache_config,
            backend_cls=self.swa_backend_cls,
            block_size=32,
        )"""

replacement = """        self.swa_cache_layer = DeepseekV4SWACache(
            head_dim=self.head_dim,
            window_size=self.window_size,
            dtype=self.kv_cache_torch_dtype,
            prefix=f"{prefix}.swa_cache",
            cache_config=cache_config,
            backend_cls=self.swa_backend_cls,
            block_size=64,
        )"""

if target in c:
    c = c.replace(target, replacement, 1)
    with open(path, "w") as f:
        f.write(c)
    print("SUCCESS: Patched swa_cache_layer block_size to 64 in attention.py!")
else:
    print("Target not found or already patched!")
