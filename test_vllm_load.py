import sys
try:
    from vllm import LLM
    print("Testing vLLM LLM initialization...")
    llm = LLM(
        model="/data/models/deepseek-v4.1-flash",
        tensor_parallel_size=8,
        trust_remote_code=True,
        gpu_memory_utilization=0.9,
    )
    print("Successfully initialized vLLM!")
except Exception as e:
    print(f"vLLM initialization error: {type(e).__name__}: {e}")
