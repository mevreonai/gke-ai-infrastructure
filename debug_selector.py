import torch
from vllm.config import get_current_vllm_config, VllmConfig, ModelConfig, CacheConfig, AttentionConfig
from vllm.platforms import current_platform
from vllm.v1.attention.backends.mla.prefill.selector import (
    _get_mla_prefill_backend_priorities,
    _auto_select_mla_prefill_backend,
    MLAPrefillBackendEnum,
    MLAPrefillSelectorConfig,
    MLADimensions,
)

cap = current_platform.get_device_capability()
print("Device capability:", cap)

for dims in [
    MLADimensions(qk_nope_head_dim=192, qk_rope_head_dim=64, v_head_dim=256),
    MLADimensions(qk_nope_head_dim=128, qk_rope_head_dim=64, v_head_dim=128),
    MLADimensions(qk_nope_head_dim=0, qk_rope_head_dim=0, v_head_dim=0)
]:
    print(f"\nTesting dims={dims}:")
    priorities = _get_mla_prefill_backend_priorities(cap, dims)
    print("Priorities:", [b.name for b in priorities])
    
    sel_config = MLAPrefillSelectorConfig(dtype=torch.bfloat16, mla_dimensions=dims)
    for b in priorities:
        cls = b.get_class()
        try:
            reasons = cls.validate_configuration(cap, sel_config)
            print(f"  {b.name}: invalid_reasons = {reasons}")
        except Exception as e:
            print(f"  {b.name}: exception = {e}")
            
    try:
        backend_cls = _auto_select_mla_prefill_backend(cap, sel_config)
        print(f"Selected for dims {dims}: {backend_cls.get_name()}")
    except Exception as e:
        print(f"Selected for dims {dims}: FAILED ({e})")
