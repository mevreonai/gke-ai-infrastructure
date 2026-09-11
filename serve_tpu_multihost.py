import os
import ray
from ray import serve
from ray.serve.llm import (
    LLMConfig,
    ModelLoadingConfig,
    LLMServingArgs,
    build_openai_app
)

# Read configurations from environment variables
MODEL_ID = os.environ.get("MODEL_ID", "google/gemma-2-27b-it")
MODEL_SOURCE = os.environ.get("MODEL_SOURCE", "/data/google/gemma-2-27b-it")

# TPU hardware options (TPU-V5LITEPOD, TPU-V6E, etc.)
ACCELERATOR_TYPE = os.environ.get("ACCELERATOR_TYPE", "TPU-V5LITEPOD")
TPU_TOPOLOGY = os.environ.get("TPU_TOPOLOGY", "2x4")

# vLLM engine parameters
TENSOR_PARALLEL_SIZE = int(os.environ.get("TENSOR_PARALLEL_SIZE", "8"))
MAX_MODEL_LEN = int(os.environ.get("MAX_MODEL_LEN", "8192"))
MAX_NUM_BATCHED_TOKENS = int(os.environ.get("MAX_NUM_BATCHED_TOKENS", "4096"))

# Patch initialize_node to use pre-downloaded weights in /data
try:
    import ray.llm._internal.serve.engines.vllm.vllm_engine as vllm_engine_module
    async def _direct_initialize_node(cfg):
        cfg.get_engine_config().hf_model_id = MODEL_SOURCE
    vllm_engine_module.initialize_node = _direct_initialize_node
except Exception as e:
    print(f"Notice: could not patch initialize_node: {e}")

# Define the multi-host TPU LLM config
llm_config = LLMConfig(
    model_loading_config=dict(
        model_id=MODEL_ID,
        model_source=MODEL_SOURCE
    ),
    accelerator_type=ACCELERATOR_TYPE,
    accelerator_config={"kind": "tpu", "topology": TPU_TOPOLOGY},
    placement_group_config={
        "bundles": [
            {"TPU": 4, "CPU": 1},
            {"TPU": 4, "CPU": 1}
        ],
        "strategy": "PACK"
    },
    engine_kwargs={
        "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
        "max_model_len": MAX_MODEL_LEN,
        "max_num_batched_tokens": MAX_NUM_BATCHED_TOKENS,
        "distributed_executor_backend": "ray",
    }
)

deployment = build_openai_app(LLMServingArgs(llm_configs=[llm_config]))
