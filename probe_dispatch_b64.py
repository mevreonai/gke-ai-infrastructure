import subprocess
import base64

code = """
from vllm.utils.flashinfer import has_flashinfer_sparse_mla_sm120_config, has_flashinfer_sparse_mla_sm120, has_flashinfer
print("has_flashinfer:", has_flashinfer())
print("has_flashinfer_sparse_mla_sm120:", has_flashinfer_sparse_mla_sm120())
print("config(8, 128):", has_flashinfer_sparse_mla_sm120_config(8, 128))
print("config(16, 128):", has_flashinfer_sparse_mla_sm120_config(16, 128))

import flashinfer.mla._sparse_mla_sm120 as mod
print("dispatch len:", len(mod._DECODE_DSV4_DISPATCH))
print("(8, 128):", (8, 128) in mod._DECODE_DSV4_DISPATCH)
print("(16, 128):", (16, 128) in mod._DECODE_DSV4_DISPATCH)
"""
b64 = base64.b64encode(code.encode()).decode()

write_cmd = f"echo '{b64}' | base64 -d > /tmp/probe_dispatch.py && /home/ayu23/vllm_env/bin/python3 /tmp/probe_dispatch.py"
res = subprocess.run(["python", "run_ssh.py", "kimi-node-0", write_cmd], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
