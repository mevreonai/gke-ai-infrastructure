import torch
from vllm.platforms import current_platform
from vllm.utils.deep_gemm import get_num_sms
import vllm.third_party.deep_gemm._C as C

print("Testing DeepGEMM SM120 fp8_fp4_paged_mqa_logits adapter...")

device = torch.device("cuda:0")
num_sms = get_num_sms()
print(f"Detected num_sms: {num_sms}")

B = 1
next_n = 1
num_heads = 32
head_dim = 128
max_model_len = 512

# FP8 Q: [B, next_n, num_heads, head_dim] in float8_e4m3fn (MUST be 4D)
q_fp = torch.randn(B, next_n, num_heads, head_dim, device=device).to(torch.float8_e4m3fn)
q = (q_fp, None)

# Weights: [B * next_n, num_heads] float32
weights = torch.ones(B * next_n, num_heads, device=device, dtype=torch.float32)

# Context lens: [B, next_n] 2D tensor
context_lens = torch.tensor([[128]], device=device, dtype=torch.int32)

# 1. Test block_kv = 64 with 4D kv_cache [num_blocks, block_kv, 1, head_dim]
print("\n--- Test 1: block_kv = 64 ---")
num_blocks = 4
# KV cache FP8 has head_dim + 4 bytes scale = 132 bytes per token
kv_64 = torch.zeros(num_blocks, 64, 1, head_dim + 4, device=device, dtype=torch.uint8)
bt_64 = torch.tensor([[0, 1, -1, -1]], device=device, dtype=torch.int32)
sm_64 = C.get_paged_mqa_logits_metadata(context_lens, 64, num_sms, None)
out_64 = C.fp8_fp4_paged_mqa_logits(q, kv_64, weights, context_lens, bt_64, sm_64, max_model_len, False)
print("SUCCESS: block_kv=64 worked! Output shape:", out_64.shape)

# 2. Test block_kv = 128 adapted to 64
print("\n--- Test 2: block_kv = 128 with adapter ---")
kv_128 = torch.zeros(2, 128, 1, head_dim + 4, device=device, dtype=torch.uint8)
bt_128 = torch.tensor([[0, -1]], device=device, dtype=torch.int32)

# Adapter logic:
orig_shape = kv_128.shape
new_shape = (orig_shape[0] * 2, 64) + orig_shape[2:]
kv_adapted = kv_128.reshape(new_shape)

b0 = torch.where(bt_128 >= 0, bt_128 * 2, bt_128)
b1 = torch.where(bt_128 >= 0, bt_128 * 2 + 1, bt_128)
bt_adapted = torch.stack([b0, b1], dim=-1).flatten(-2).contiguous()

sm_adapted = C.get_paged_mqa_logits_metadata(context_lens, 64, num_sms, None)
out_adapted = C.fp8_fp4_paged_mqa_logits(q, kv_adapted, weights, context_lens, bt_adapted, sm_adapted, max_model_len, False)
print("SUCCESS: block_kv=128 adapted to 64 worked! Output shape:", out_adapted.shape)

print("\nALL ADAPTER TESTS PASSED 100%!")
