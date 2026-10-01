from vllm.transformers_utils.config import get_config
try:
    cfg = get_config("/data/models/deepseek-v4.1-flash", trust_remote_code=True)
    print("VLLM GET_CONFIG SUCCESS:", type(cfg), getattr(cfg, 'model_type', None))
except Exception as e:
    print("VLLM GET_CONFIG FAILED:", repr(e))
