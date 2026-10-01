import subprocess

code = '''
from vllm.config import VllmConfig, ModelConfig, ParallelConfig
import torch

try:
    from vllm.utils.flashinfer import has_flashinfer_sparse_mla_sm120_config, has_flashinfer_sparse_mla_sm120, has_flashinfer
    print("has_flashinfer:", has_flashinfer())
    print("has_flashinfer_sparse_mla_sm120:", has_flashinfer_sparse_mla_sm120())
    print("config(8, 128):", has_flashinfer_sparse_mla_sm120_config(8, 128))
    print("config(16, 128):", has_flashinfer_sparse_mla_sm120_config(16, 128))
    
    import flashinfer.mla._sparse_mla_sm120 as mod
    print("dispatch set len:", len(mod._DECODE_DSV4_DISPATCH))
    print("(8, 128) in dispatch:", (8, 128) in mod._DECODE_DSV4_DISPATCH)
    print("(16, 128) in dispatch:", (16, 128) in mod._DECODE_DSV4_DISPATCH)
except Exception as e:
    import traceback
    traceback.print_exc()
'''

cmd = ["python", "run_ssh.py", "kimi-node-0", f"/home/ayu23/vllm_env/bin/python3 -c '{code}' "]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
