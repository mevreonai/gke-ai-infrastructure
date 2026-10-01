import os
import sys

def patch_attn_utils():
    path = "/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/v1/worker/gpu/attn_utils.py"
    with open(path, "r") as f:
        content = f.read()

    old_target = """    for layer_name, target in get_shared_kv_cache_layers(vllm_config).items():
        if target in kv_caches:
            kv_caches[layer_name] = kv_caches[target]"""

    new_target = """    local_layers = {n for g in kv_cache_config.kv_cache_groups for n in g.layer_names}
    for layer_name, target in get_shared_kv_cache_layers(vllm_config).items():
        if target in kv_caches:
            kv_caches[layer_name] = kv_caches[target]
        elif layer_name in local_layers:
            raise RuntimeError(
                f"{layer_name} shares KV cache with {target}, which is not allocated on this PP stage"
            )"""

    if old_target in content:
        content = content.replace(old_target, new_target)
        with open(path, "w") as f:
            f.write(content)
        print("Successfully patched attn_utils.py")
    elif "shares KV cache with" in content:
        print("attn_utils.py already patched")
    else:
        print("WARNING: Could not find target in attn_utils.py")

def patch_utils():
    path = "/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/v1/worker/utils.py"
    with open(path, "r") as f:
        content = f.read()

    old_code = """    kv_caches: dict[str, torch.Tensor] = {}
    for tensor in kv_cache_config.kv_cache_tensors:
        layer_name = tensor.layers[0]
        matching = [
            (group_id, group)
            for group_id, group in enumerate(kv_cache_config.kv_cache_groups)
            if layer_name in group.layer_names
        ]
        if not matching:
            continue
        group_id, group = matching[0]
        spec = group.kv_cache_spec
        if isinstance(spec, UniformTypeKVCacheSpecs):
            spec = spec.kv_cache_specs[layer_name]

        num_blocks = kv_cache_config.num_blocks
        kernel_block_size = None
        if kernel_block_sizes is not None and group_id < len(kernel_block_sizes):
            kernel_block_size = kernel_block_sizes[group_id]
        if isinstance(spec, MLAAttentionSpec) and spec.storage_block_size is not None:
            kernel_block_size = spec.storage_block_size

        views = create_kv_cache_views(
            buf,
            spec,
            num_blocks,
            layout,
            tensor,
            kernel_block_size=kernel_block_size,
        )
        kv_caches.update(zip(tensor.layers, views))
    return kv_caches"""

    new_code = """    kv_caches: dict[str, torch.Tensor] = {}
    local_layers = {n for g in kv_cache_config.kv_cache_groups for n in g.layer_names}
    layer_to_group = {
        n: (gid, g)
        for gid, g in enumerate(kv_cache_config.kv_cache_groups)
        for n in g.layer_names
    }

    for tensor in kv_cache_config.kv_cache_tensors:
        flags = [l in local_layers for l in tensor.layers]
        if not any(flags):
            continue
        assert all(flags), f"KV tensor straddles PP stages: {tensor.layers}"
        layer_name = tensor.layers[0]
        group_id, group = layer_to_group[layer_name]
        spec = group.kv_cache_spec
        if isinstance(spec, UniformTypeKVCacheSpecs):
            spec = spec.kv_cache_specs[layer_name]

        num_blocks = kv_cache_config.num_blocks
        kernel_block_size = None
        if kernel_block_sizes is not None and group_id < len(kernel_block_sizes):
            kernel_block_size = kernel_block_sizes[group_id]
        if isinstance(spec, MLAAttentionSpec) and spec.storage_block_size is not None:
            kernel_block_size = spec.storage_block_size

        views = create_kv_cache_views(
            buf,
            spec,
            num_blocks,
            layout,
            tensor,
            kernel_block_size=kernel_block_size,
        )
        kv_caches.update(zip(tensor.layers, views))

    logger.info(
        "KV alloc: local_tensors=%d/%d num_blocks=%d buf=%.2f GiB free=%.2f GiB",
        sum(any(l in local_layers for l in t.layers) for t in kv_cache_config.kv_cache_tensors),
        len(kv_cache_config.kv_cache_tensors),
        kv_cache_config.num_blocks,
        buf_size / 2**30,
        torch.cuda.mem_get_info(device)[0] / 2**30,
    )

    return kv_caches"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(path, "w") as f:
            f.write(content)
        print("Successfully patched allocate_kv_cache in utils.py")
    elif "assert all(flags), f\"KV tensor straddles PP stages" in content:
        print("allocate_kv_cache in utils.py already patched")
    else:
        print("WARNING: Could not find old allocate_kv_cache in utils.py")

def patch_model_moe_init():
    path = "/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/models/deepseek_v4/nvidia/model.py"
    with open(path, "r") as f:
        content = f.read()

    target_snippet = """        if getattr(config, "vision_n_layers", 0) > 0:
            # Vision checkpoints route image sentinel tokens with bias_vl
            # instead of e_score_correction_bias / the hash table. Created on
            # every MoE layer, hash layers included.
            self.gate.bias_vl = nn.Parameter(
                torch.empty(self.n_routed_experts, dtype=torch.float32),
                requires_grad=False,
            )"""

    new_snippet = """        if getattr(config, "vision_n_layers", 0) > 0:
            # Vision checkpoints route image sentinel tokens with bias_vl
            # instead of e_score_correction_bias / the hash table. Created on
            # every MoE layer, hash layers included.
            self.gate.bias_vl = nn.Parameter(
                torch.empty(self.n_routed_experts, dtype=torch.float32),
                requires_grad=False,
            )
        if getattr(self.gate, "bias_vl", None) is not None:
            pp = vllm_config.parallel_config.pipeline_parallel_size
            text_only = bool(
                getattr(vllm_config.model_config, "language_model_only", False)
                or getattr(getattr(vllm_config.model_config, "multimodal_config", None), "language_model_only", False)
            )
            if pp > 1 and not text_only:
                raise NotImplementedError(
                    "bias_vl routing with PP>1 requires --language-model-only"
                )"""

    if target_snippet in content:
        content = content.replace(target_snippet, new_snippet)
        with open(path, "w") as f:
            f.write(content)
        print("Successfully patched DeepseekV4MoE.__init__ in model.py")
    elif "bias_vl routing with PP>1 requires --language-model-only" in content:
        print("model.py already has MoE __init__ guard")
    else:
        print("WARNING: Could not find bias_vl init snippet in model.py")

def patch_fused_topk_collapse():
    path = "/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/model_executor/layers/fused_moe/router/fused_topk_bias_router.py"
    with open(path, "r") as f:
        content = f.read()

    old_check = """    image_mask = None
    if bias_vl is not None and image_sentinel_lo > 0:
        # Image tokens (five consecutive sentinel ids starting at
        # image_sentinel_lo) select experts with bias_vl instead of
        # e_score_correction_bias / the hash table. Ids above the sentinel
        # block are regular special tokens and must not match.
        if input_tokens is None:
            bias_vl = None
        image_mask = ("""

    new_check = """    image_mask = None
    if input_tokens is None:
        bias_vl = None
    if bias_vl is not None and image_sentinel_lo > 0:
        # Image tokens (five consecutive sentinel ids starting at
        # image_sentinel_lo) select experts with bias_vl instead of
        # e_score_correction_bias / the hash table. Ids above the sentinel
        # block are regular special tokens and must not match.
        image_mask = ("""

    if old_check in content:
        content = content.replace(old_check, new_check)
        with open(path, "w") as f:
            f.write(content)
        print("Successfully collapsed input_tokens check in fused_topk_bias_router.py")
    elif new_check in content:
        print("fused_topk_bias_router.py already has collapsed check")
    else:
        print("WARNING: old check not found verbatim in fused_topk_bias_router.py")

if __name__ == "__main__":
    patch_attn_utils()
    patch_utils()
    patch_model_moe_init()
    patch_fused_topk_collapse()
