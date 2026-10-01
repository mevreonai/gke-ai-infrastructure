file_path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/utils/deep_gemm.py"
content = open(file_path).read()

target = "    return _get_paged_mqa_logits_metadata_impl("
replacement = """    if block_size not in (32, 64):
        print(f"[CLAMP_BLOCK_SIZE] Clamping block_size from {block_size} to 64 for DeepGEMM")
        block_size = 64
    return _get_paged_mqa_logits_metadata_impl("""

if target in content and "[CLAMP_BLOCK_SIZE]" not in content:
    content = content.replace(target, replacement, 1)
    open(file_path, "w").write(content)
    print("Patched deep_gemm clamping successfully!")
else:
    print("Already patched or target not found")
