import re, sys

# 1. Fix sparse_swa.py: set max_image_tokens = 0 when language_model_only is enabled or vision is disabled
swa_path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/sparse_swa.py'
with open(swa_path, 'r') as f:
    swa_code = f.read()

target_swa = """        self.max_image_tokens = (
            getattr(hf_config, "vision_max_n_token", 0)
            if getattr(hf_config, "vision_n_layers", 0) > 0
            else 0
        )"""

replacement_swa = """        is_lm_only = getattr(self.vllm_config.model_config, "language_model_only", False)
        self.max_image_tokens = (
            getattr(hf_config, "vision_max_n_token", 0)
            if getattr(hf_config, "vision_n_layers", 0) > 0 and not is_lm_only
            else 0
        )"""

if target_swa in swa_code:
    swa_code = swa_code.replace(target_swa, replacement_swa)
    with open(swa_path, 'w') as f:
        f.write(swa_code)
    print(f"Successfully patched {swa_path}")
else:
    print(f"Pattern already modified or not found in {swa_path}")

# 2. Restore model.py to DeepseekV4FlashInferSM120Attention
for model_path in [
    '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/nvidia/model.py',
    '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4/nvidia/model.py'
]:
    try:
        with open(model_path, 'r') as f:
            code = f.read()
        # Restore any DeepseekV4FlashInferMLAAttention back to DeepseekV4FlashInferSM120Attention if it was in _select_dsv4_attn_cls
        if 'return DeepseekV4FlashInferMLAAttention' in code and 'major == 12' in code:
            code = re.sub(
                r'if device_capability is not None and device_capability\.major == 12:\s*return DeepseekV4FlashInferMLAAttention',
                'if device_capability is not None and device_capability.major == 12:\n        return DeepseekV4FlashInferSM120Attention',
                code
            )
            with open(model_path, 'w') as f:
                f.write(code)
            print(f"Restored SM120 attention in {model_path}")
    except Exception as e:
        print(f"Error in {model_path}: {e}")
