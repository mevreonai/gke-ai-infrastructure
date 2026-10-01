import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "/home/ayu23/vllm_env/bin/python3 -c \"from vllm.utils.flashinfer import has_flashinfer_sparse_mla_sm120_config; print('has_8_128:', has_flashinfer_sparse_mla_sm120_config(8, 128))\" "]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
