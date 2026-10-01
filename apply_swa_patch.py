import sys

path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/sparse_swa.py'
with open(path, 'r') as f:
    content = f.read()

# Target block
old_block = '''        # Vision variant: image spans (up to vision_max_n_token tokens) are
        # visible bidirectionally, so prefill index rows widen from
        # window_size to window_size + max_image_tokens. Text-only models keep
        # max_image_tokens == 0 and take the original code paths everywhere.
        is_lm_only = getattr(self.vllm_config.model_config, "language_model_only", False)
        self.max_image_tokens = (
            getattr(hf_config, "vision_max_n_token", 0)
            if getattr(hf_config, "vision_n_layers", 0) > 0 and not is_lm_only
            else 0
        )
        self.prefill_index_width = self.window_size + self.max_image_tokens'''

new_block = '''        # Vision variant: image spans (up to vision_max_n_token tokens) are
        # visible bidirectionally, so prefill index rows widen from
        # window_size to window_size + max_image_tokens. Text-only models keep
        # max_image_tokens == 0 and take the original code paths everywhere.
        mm_cfg = getattr(self.vllm_config.model_config, "multimodal_config", None)
        is_lm_only = bool(getattr(mm_cfg, "language_model_only", False)) or bool(getattr(self.vllm_config.model_config, "language_model_only", False))
        self.max_image_tokens = (
            0
            if is_lm_only
            else (
                getattr(hf_config, "vision_max_n_token", 0)
                if getattr(hf_config, "vision_n_layers", 0) > 0
                else 0
            )
        )
        self.prefill_index_width = self.window_size + self.max_image_tokens
        if is_lm_only:
            assert self.prefill_index_width == 128, f"SM120 sparse MLA prefill requires topk=128 in text-only mode, got {self.prefill_index_width}"'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: Patched sparse_swa.py')
else:
    print('ERROR: Old block not found in sparse_swa.py')
    sys.exit(1)
