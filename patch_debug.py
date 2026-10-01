file_path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/worker/utils.py"
content = open(file_path).read()

target = "selected_kernel_size = select_common_block_size("
replacement = """print(f"[DEBUG_BLOCK_SIZE] gid={kv_cache_gid} block_size={kv_manager_block_size} backends={group_backends}")
            for b in group_backends:
                print(f"[DEBUG_BLOCK_SIZE] backend={b} supported={b.get_supported_kernel_block_sizes()}")
            selected_kernel_size = select_common_block_size("""

if target in content and "[DEBUG_BLOCK_SIZE]" not in content:
    content = content.replace(target, replacement, 1)
    open(file_path, "w").write(content)
    print("Patched successfully!")
else:
    print("Target not found or already patched")
