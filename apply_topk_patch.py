import subprocess

patch_code = '''
cu_path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/flashinfer/data/csrc/sparse_mla_sm120_decode_dsv4.cu"
with open(cu_path, "r") as f:
    cu = f.read()

# Add DSV4_DISPATCH(H, 1152) for all H
for h in [8, 16, 32, 64, 128]:
    old_str = f"  DSV4_DISPATCH({h}, 1024)"
    new_str = f"  DSV4_DISPATCH({h}, 1024)\\n  DSV4_DISPATCH({h}, 1152)"
    if old_str in cu and f"DSV4_DISPATCH({h}, 1152)" not in cu:
        cu = cu.replace(old_str, new_str, 1)

with open(cu_path, "w") as f:
    f.write(cu)
print("SUCCESS: Updated sparse_mla_sm120_decode_dsv4.cu with TOPK=1152!")

py_path = "/home/ayu23/vllm_env/lib64/python3.12/site-packages/flashinfer/mla/_sparse_mla_sm120.py"
with open(py_path, "r") as f:
    py = f.read()

for h in [8, 16, 32, 64, 128]:
    old_py = f"({h}, 1024),"
    new_py = f"({h}, 1024),\\n        ({h}, 1152),"
    if old_py in py and f"({h}, 1152)" not in py:
        py = py.replace(old_py, new_py, 1)

with open(py_path, "w") as f:
    f.write(py)
print("SUCCESS: Updated _sparse_mla_sm120.py with (H, 1152) dispatch entries!")
'''

with open("c:/Users/ayu23/OneDrive/Desktop/tpu/patch_topk_1152.py", "w") as f:
    f.write(patch_code)

scp_cmd = 'gcloud compute scp c:/Users/ayu23/OneDrive/Desktop/tpu/patch_topk_1152.py kimi-node-0:/home/ayu23/patch_topk_1152.py --zone=us-central1-b --project=mevreon'
subprocess.run(scp_cmd, shell=True, check=True)

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', '/home/ayu23/vllm_env/bin/python3 /home/ayu23/patch_topk_1152.py && rm -rf /home/ayu23/.cache/flashinfer'], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
