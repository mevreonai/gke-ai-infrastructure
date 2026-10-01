file_path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/utils/deep_gemm.py"
content = open(file_path).read()

target = "def get_paged_mqa_logits_metadata("
replacement = """def get_paged_mqa_logits_metadata(
    context_lens: torch.Tensor,
    block_size: int,
    num_sms: int,
    indices: torch.Tensor | None = None,
) -> torch.Tensor:
    print(f"[DEBUG_DEEP_GEMM] get_paged_mqa_logits_metadata called with block_size={block_size}")
"""

if target in content and "[DEBUG_DEEP_GEMM]" not in content:
    idx = content.find(target)
    # Find end of def line / signature
    end_sig = content.find("-> torch.Tensor:", idx)
    end_line = content.find("\n", end_sig)
    content = content[:end_line+1] + "    print(f'[DEBUG_DEEP_GEMM] get_paged_mqa_logits_metadata called with block_size={block_size}')\n" + content[end_line+1:]
    open(file_path, "w").write(content)
    print("Patched deep_gemm.py successfully!")
else:
    print("Target not found or already patched")
