import subprocess

remote_code = '''
import os, sys
os.environ['CUDA_VISIBLE_DEVICES'] = '6'
import torch
print('CUDA available:', torch.cuda.is_available())
print('Device count:', torch.cuda.device_count())
if torch.cuda.is_available():
    print('Device name:', torch.cuda.get_device_name(0))
    print('Capability:', torch.cuda.get_device_capability(0))
from vllm.utils.flashinfer import has_flashinfer, has_flashinfer_sparse_mla_sm120, has_flashinfer_sparse_mla_sm120_config
print('has_flashinfer():', has_flashinfer())
print('has_flashinfer_sparse_mla_sm120():', has_flashinfer_sparse_mla_sm120())
print('has_flashinfer_sparse_mla_sm120_config(8, 128):', has_flashinfer_sparse_mla_sm120_config(8, 128))
'''

# Write to remote file
subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', f"cat << 'EOF' > /home/ayu23/test_tp6.py\n{remote_code}\nEOF"])
res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', '/home/ayu23/vllm_env/bin/python3 /home/ayu23/test_tp6.py'], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
