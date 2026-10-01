
import re

path = "/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/utils/deep_gemm.py"
with open(path, "r") as f:
    content = f.read()

target = """    if block_tables.dim() >= 2 and block_tables.stride(-1) != 1:
        block_tables = block_tables.clone(memory_format=torch.contiguous_format)
    kwargs = {} if indices is None else {"indices": indices}
    return _fp8_fp4_paged_mqa_logits_impl("""

replacement = """    if kv_cache.dim() >= 2 and kv_cache.size(1) == 128:
        orig_shape = kv_cache.shape
        new_shape = (orig_shape[0] * 2, 64) + orig_shape[2:]
        kv_cache = kv_cache.reshape(new_shape)
        b0 = torch.where(block_tables >= 0, block_tables * 2, block_tables)
        b1 = torch.where(block_tables >= 0, block_tables * 2 + 1, block_tables)
        block_tables = torch.stack([b0, b1], dim=-1).flatten(-2).contiguous()
        num_sms = get_num_sms()
        schedule_metadata = get_paged_mqa_logits_metadata(context_lens, 64, num_sms, indices)

    if block_tables.dim() >= 2 and block_tables.stride(-1) != 1:
        block_tables = block_tables.clone(memory_format=torch.contiguous_format)
    kwargs = {} if indices is None else {"indices": indices}
    return _fp8_fp4_paged_mqa_logits_impl("""

if target in content:
    content = content.replace(target, replacement, 1)
    with open(path, "w") as f:
        f.write(content)
    print("SUCCESS: deep_gemm.py patched on node 0!")
else:
    print("WARNING: target not found, checking if already patched...")
    if "kv_cache.size(1) == 128" in content:
        print("ALREADY PATCHED!")
    else:
        print("ERROR: could not find target or patch!")
