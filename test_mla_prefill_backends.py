import torch
from vllm.platforms import current_platform
from vllm.v1.attention.backends.mla.prefill.selector import (
    _get_mla_prefill_backend_priorities,
    MLAPrefillBackendEnum,
    MLAPrefillSelectorConfig,
    MLADimensions,
)

cap = current_platform.get_device_capability()
print("Device capability:", cap)
print("Major:", cap.major, "Minor:", cap.minor)

dims = MLADimensions(
    qk_nope_head_dim=192,
    qk_rope_head_dim=64,
    v_head_dim=256,
)
sel_config = MLAPrefillSelectorConfig(
    dtype=torch.bfloat16,
    mla_dimensions=dims,
)

for b in [MLAPrefillBackendEnum.FLASHINFER, MLAPrefillBackendEnum.TRTLLM_RAGGED, MLAPrefillBackendEnum.FLASH_ATTN]:
    cls = b.get_class()
    reasons = cls.validate_configuration(cap, sel_config)
    print(f"Backend {b.name}: invalid_reasons = {reasons}")
