target = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/prefill/selector.py'
content = open(target).read()

old_block = """    if device_capability.major in (10, 12):  # Blackwell
        if mla_dimensions == MLADimensions(
            qk_nope_head_dim=192,
            qk_rope_head_dim=64,
            v_head_dim=256,
        ):
            return [
                MLAPrefillBackendEnum.TRTLLM_RAGGED,
                MLAPrefillBackendEnum.FLASH_ATTN,
                MLAPrefillBackendEnum.FLASHINFER,
                MLAPrefillBackendEnum.TOKENSPEED_MLA,
            ]
        return [
            MLAPrefillBackendEnum.FLASH_ATTN,
            MLAPrefillBackendEnum.TRTLLM_RAGGED,
            MLAPrefillBackendEnum.FLASHINFER,
            MLAPrefillBackendEnum.TOKENSPEED_MLA,
        ]"""

new_block = """    if device_capability.major in (10, 12):  # Blackwell
        return [
            MLAPrefillBackendEnum.TRTLLM_RAGGED,
            MLAPrefillBackendEnum.FLASH_ATTN,
            MLAPrefillBackendEnum.FLASHINFER,
            MLAPrefillBackendEnum.TOKENSPEED_MLA,
        ]"""

if old_block in content:
    open(target, 'w').write(content.replace(old_block, new_block))
    print('SUCCESS: Updated selector.py priorities to place TRTLLM_RAGGED first on Blackwell')
else:
    print('Old block not found')
