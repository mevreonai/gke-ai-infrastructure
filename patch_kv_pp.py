import os
import sys

def patch_worker_utils():
    path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/worker/utils.py'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    target = """    for tensor in kv_cache_config.kv_cache_tensors:
        layer_name = tensor.layers[0]
        group_id, group = next(
            (group_id, group)
            for group_id, group in enumerate(kv_cache_config.kv_cache_groups)
            if layer_name in group.layer_names
        )"""

    replacement = """    for tensor in kv_cache_config.kv_cache_tensors:
        layer_name = tensor.layers[0]
        matching = [
            (group_id, group)
            for group_id, group in enumerate(kv_cache_config.kv_cache_groups)
            if layer_name in group.layer_names
        ]
        if not matching:
            continue
        group_id, group = matching[0]"""

    if target in c:
        c = c.replace(target, replacement)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print("vllm/v1/worker/utils.py patched successfully")
        return True
    elif "if not matching:" in c:
        print("vllm/v1/worker/utils.py already patched")
        return True
    else:
        print("Target block not found in utils.py")
        return False

def patch_attn_utils():
    path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/worker/gpu/attn_utils.py'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    target = """    for layer_name, target in get_shared_kv_cache_layers(vllm_config).items():
        kv_caches[layer_name] = kv_caches[target]"""

    replacement = """    for layer_name, target in get_shared_kv_cache_layers(vllm_config).items():
        if target in kv_caches:
            kv_caches[layer_name] = kv_caches[target]"""

    if target in c:
        c = c.replace(target, replacement)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print("vllm/v1/worker/gpu/attn_utils.py patched successfully")
        return True
    elif "if target in kv_caches:" in c:
        print("vllm/v1/worker/gpu/attn_utils.py already patched")
        return True
    else:
        print("Target block not found in attn_utils.py")
        return False

if __name__ == '__main__':
    r1 = patch_worker_utils()
    r2 = patch_attn_utils()
    if not (r1 and r2):
        sys.exit(1)
    print("All KV cache PP patches applied cleanly.")
