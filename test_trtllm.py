try:
    from flashinfer.prefill import trtllm_ragged_attention_deepseek
    print("TRTLLM_RAGGED AVAILABLE: True")
except Exception as e:
    print("TRTLLM_RAGGED AVAILABLE: False,", e)
