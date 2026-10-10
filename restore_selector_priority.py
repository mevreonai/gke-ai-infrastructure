target = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/prefill/selector.py'
content = open(target).read()

old_block = """    if device_capability.major in (10, 12):  # Blackwell
        return [
            MLAPrefillBackendEnum.TRTLLM_RAGGED,
            MLAPrefillBackendEnum.FLASH_ATTN,
            MLAPrefillBackendEnum.FLASHINFER,
            MLAPrefillBackendEnum.TOKENSPEED_MLA,
        ]"""

new_block = """    if device_capability.major in (10, 12):  # Blackwell
        return [
            MLAPrefillBackendEnum.FLASH_ATTN,
            MLAPrefillBackendEnum.TRTLLM_RAGGED,
            MLAPrefillBackendEnum.FLASHINFER,
            MLAPrefillBackendEnum.TOKENSPEED_MLA,
        ]"""

if old_block in content:
    open(target, 'w').write(content.replace(old_block, new_block))
    print('SUCCESS: Restored FLASH_ATTN as top priority for SM120')
else:
    print('Old block not found')
