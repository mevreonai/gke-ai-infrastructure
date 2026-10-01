import subprocess
cmd = ["python", "run_ssh.py", "kimi-node-0", "/home/ayu23/vllm_env/bin/python3 -c \"from vllm.utils.flashinfer import has_flashinfer_sparse_mla_sm120_config, has_flashinfer_sparse_mla_sm120; print('has_sm120:', has_flashinfer_sparse_mla_sm120()); print('has_16_128:', has_flashinfer_sparse_mla_sm120_config(16, 128))\" "]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
