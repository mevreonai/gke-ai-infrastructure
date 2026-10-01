import subprocess

patch_code = '''
prefill_path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/flashinfer/data/csrc/sparse_mla_sm120_prefill.cu"
with open(prefill_path, "r") as f:
    code = f.read()

target = """  else if (topk == 1024)
    DISPATCH_BY_NH_CM(FP8, 1024);"""

replacement = """  else if (topk == 1024)
    DISPATCH_BY_NH_CM(FP8, 1024);
  else if (topk == 1152)
    DISPATCH_BY_NH_CM(FP8, 1152);"""

if target in code and "topk == 1152" not in code:
    code = code.replace(target, replacement, 1)
    with open(prefill_path, "w") as f:
        f.write(code)
    print("SUCCESS: Patched sparse_mla_sm120_prefill.cu with topk == 1152!")
else:
    print("Already patched or target not found")
'''

import base64
b64 = base64.b64encode(patch_code.encode()).decode()

cmd0 = f"echo '{b64}' | base64 -d > /tmp/patch_prefill.py && /home/ayu23/vllm_env/bin/python3 /tmp/patch_prefill.py"
res0 = subprocess.run(["python", "run_ssh.py", "kimi-node-0", cmd0], capture_output=True, text=True)
print("NODE 0 PATCH:\n", res0.stdout, res0.stderr)

cmd1 = f"echo '{b64}' | base64 -d > /tmp/patch_prefill.py && /home/ayu23/vllm_env/bin/python3 /tmp/patch_prefill.py"
res1 = subprocess.run(["python", "run_ssh.py", "kimi-node-1", cmd1], capture_output=True, text=True)
print("NODE 1 PATCH:\n", res1.stdout, res1.stderr)
