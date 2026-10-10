from vllm.v1.attention.backends.flashinfer import FlashInferBackend
from vllm.platforms import current_platform
import torch

print("fp8 dtype:", FlashInferBackend.get_dtype_for_flashinfer("fp8"))
print("platform fp8 dtype:", current_platform.fp8_dtype())
print("is_family 120:", current_platform.is_device_capability_family(120))
