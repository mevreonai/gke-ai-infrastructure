import re
import sys

def patch_sparse_mla():
    path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/sparse_mla.py"
    with open(path, "r") as f:
        content = f.read()

    target = "return [64 if current_platform.is_device_capability_family(90) else 128]"
    replacement = "return [64 if (current_platform.is_device_capability_family(90) or current_platform.is_device_capability_family(120)) else 128]"
    
    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w") as f:
            f.write(content)
        print(f"Patched {path}")
    elif replacement in content:
        print(f"Already patched {path}")
    else:
        print(f"ERROR: Could not find target in {path}")
        return False
    return True

def patch_indexer():
    path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/indexer.py"
    with open(path, "r") as f:
        content = f.read()

    target = "return [64 if current_platform.is_device_capability_family(90) else 128]"
    replacement = "return [64 if (current_platform.is_device_capability_family(90) or current_platform.is_device_capability_family(120)) else 128]"
    
    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w") as f:
            f.write(content)
        print(f"Patched block sizes in {path}")
    elif replacement in content:
        print(f"Already patched block sizes in {path}")
    else:
        print(f"ERROR: Could not find target in {path}")
        return False

    target2 = "    if current_platform.is_device_capability_family(100):\n        return True"
    replacement2 = "    if current_platform.is_device_capability_family(100) or current_platform.is_device_capability_family(120):\n        return True"
    if target2 in content:
        content = content.replace(target2, replacement2)
        with open(path, "w") as f:
            f.write(content)
        print(f"Patched native decode in {path}")
    elif replacement2 in content:
        print(f"Already patched native decode in {path}")
    else:
        print(f"Note: target2 not found or already different in {path}")

    return True

def patch_flashinfer_sparse():
    path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/nvidia/flashinfer_sparse.py"
    with open(path, "r") as f:
        content = f.read()

    # Add current_platform import if needed
    if "from vllm.platforms import current_platform" not in content:
        content = "from vllm.platforms import current_platform\n" + content

    target = "    @staticmethod\n    def get_supported_kernel_block_sizes() -> list[int | MultipleOf]:\n        return [128]"
    replacement = "    @staticmethod\n    def get_supported_kernel_block_sizes() -> list[int | MultipleOf]:\n        return [64 if (current_platform.is_device_capability_family(90) or current_platform.is_device_capability_family(120)) else 128]"

    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w") as f:
            f.write(content)
        print(f"Patched block size in {path}")
    elif replacement in content:
        print(f"Already patched block size in {path}")
    else:
        print(f"ERROR: Could not find target in {path}")
        return False

    return True

if __name__ == "__main__":
    ok1 = patch_sparse_mla()
    ok2 = patch_indexer()
    ok3 = patch_flashinfer_sparse()
    if not (ok1 and ok2 and ok3):
        sys.exit(1)
    print("All vLLM SM120 patches applied successfully!")
