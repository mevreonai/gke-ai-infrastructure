
from vllm.engine.arg_utils import EngineArgs
ea = EngineArgs(model='/data/models/deepseek-v4.1-flash', language_model_only=True, trust_remote_code=True)
vc = ea.create_engine_config()
mc = vc.model_config
mm = getattr(mc, 'multimodal_config', None)
print('model_config language_model_only:', getattr(mc, 'language_model_only', 'NOT_FOUND'))
print('mm_config:', mm)
if mm:
    print('mm_config.language_model_only:', getattr(mm, 'language_model_only', 'NOT_FOUND'))
