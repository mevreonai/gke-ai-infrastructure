import subprocess

cmd = ["python", "run_ssh.py", "kimi-node-0", "/home/ayu23/vllm_env/bin/python3 -c \"from flashinfer.decode import trtllm_batch_decode_sparse_mla_dsv4, trtllm_batch_decode_with_kv_cache_mla; print('imported successfully!')\" "]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
