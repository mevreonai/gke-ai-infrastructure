import re
import sys

def restore_sparse_mla():
    path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/sparse_mla.py"
    with open(path, "r") as f:
        content = f.read()

    # We want it to return [128] on SM120 (since SM90 is family 90, SM120 is not 90)
    target = "return [64 if (current_platform.is_device_capability_family(90) or current_platform.is_device_capability_family(120)) else 128]"
    replacement = "return [64 if current_platform.is_device_capability_family(90) else 128]"
    
    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w") as f:
            f.write(content)
        print(f"Restored {path}")
    else:
        print(f"Already restored or not found in {path}")
    return True

def restore_indexer():
    path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/indexer.py"
    with open(path, "r") as f:
        content = f.read()

    target = "return [64 if (current_platform.is_device_capability_family(90) or current_platform.is_device_capability_family(120)) else 128]"
    replacement = "return [64 if current_platform.is_device_capability_family(90) else 128]"
    
    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w") as f:
            f.write(content)
        print(f"Restored block sizes in {path}")
    else:
        print(f"Already restored or not found in {path}")
    return True

def restore_flashinfer_sparse():
    path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/nvidia/flashinfer_sparse.py"
    with open(path, "r") as f:
        content = f.read()

    target = "    @staticmethod\n    def get_supported_kernel_block_sizes() -> list[int | MultipleOf]:\n        return [64 if (current_platform.is_device_capability_family(90) or current_platform.is_device_capability_family(120)) else 128]"
    replacement = "    @staticmethod\n    def get_supported_kernel_block_sizes() -> list[int | MultipleOf]:\n        return [128]"

    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w") as f:
            f.write(content)
        print(f"Restored block size in {path}")
    else:
        print(f"Already restored or not found in {path}")
    return True

if __name__ == "__main__":
    restore_sparse_mla()
    restore_indexer()
    restore_flashinfer_sparse()
    print("All restored to 128 successfully!")
