import subprocess

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'wc -l $HOME/vllm_env/lib64/python3.12/site-packages/flashinfer/data/csrc/sparse_mla_sm120_decode_dsv4.cu'], capture_output=True, text=True)
print(res.stdout)
res2 = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'grep -n "DSV4_DISPATCH" $HOME/vllm_env/lib64/python3.12/site-packages/flashinfer/data/csrc/sparse_mla_sm120_decode_dsv4.cu'], capture_output=True, text=True)
print(res2.stdout)
