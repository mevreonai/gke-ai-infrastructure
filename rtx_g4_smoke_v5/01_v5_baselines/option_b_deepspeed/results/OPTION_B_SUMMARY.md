# Option B: Nsys CUDA Kernel Profiling Results

Kernel-level profiling executed using NVIDIA Nsight Systems (`nsys`) with `--enforce-eager` and `--enable-layerwise-nvtx-tracing` across 80 layers of `Kimi-Linear-48B-A3B-Instruct` on Blackwell RTX PRO 6000 GPUs.

## 1. Context Probe Benchmark Metrics

| Metric | 8K Context Probe | 128K Context Probe |
| :--- | :---: | :---: |
| **Input Tokens** | 8,192 | 131,072 |
| **Generated Output Tokens** | 32 (1 prefill + 31 decode) | 32 (1 prefill + 31 decode) |
| **Time to First Token (TTFT)** | **447.28 ms** | **4,970.15 ms** |
| **Median Inter-Token Latency (ITL)** | **31.26 ms** | **31.46 ms** |
| **Mean ITL** | 50.24 ms | 46.52 ms |

> [!NOTE]
> **Why ITL is 31 ms in Option B vs 5 ms in Option A:**
> Option B was run with `--enforce-eager` (CUDA Graphs disabled to trace discrete kernel calls) and `--enable-layerwise-nvtx-tracing` with OS runtime event interception. Across 80 model layers, intercepting each kernel launch adds ~25 ms CPU-GPU synchronization overhead per token.

## 2. Kernel Invocations Verification
- **Model Architecture:** 80 layers (hybrid linear attention + MoE).
- **Decode Steps:** 31 steps.
- **Kernel Count Exact Match:**
  - `fused_recurrent_kda_packed_decode_kernel`: **exactly 2,480 instances** ($31 \times 80 = 2,480$).
  - `_causal_conv1d_update_kernel`: **exactly 2,480 instances** ($31 \times 80 = 2,480$).

## 3. Discovered Blackwell Kernel Signatures
- **CUTLASS Blackwell MoE:** `cutlass::gemm::kernel::MoeFCGemm` & `fused_moe::run_global`
- **Kimi Delta Attention (KDA):** `chunk_gated_delta_rule_fwd_kernel_h_blockdim64` & `chunk_kda_fwd_kernel_intra_token_parallel`
- **MLA KV Packing:** `vllm::kimi_k3_fused_ops::fusedKimiK3MLAKVConcatPackKernel`
- **FlashAttention:** `flash::flash_fwd_kernel`
