import base64
import subprocess

script = """
import json
from v9_core.runner_lib import build_server_cmd, run_capture
cfg = json.load(open('configs/models/kimi_linear_48b.json'))
case = {'tp': 4, 'pp': 1, 'max_num_batched_tokens': 8192}
help_txt = run_capture(['vllm', 'serve', '--help'])['out']
cmd = build_server_cmd('vllm', help_txt, cfg, case, 'moonshotai/Kimi-Linear-48B-A3B-Instruct', 8000)
print('GENERATED COMMAND:')
print(' '.join(cmd))
"""

b64 = base64.b64encode(script.encode('utf-8')).decode('utf-8')
cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --command="cd /home/ayu23/V9_FULL && source /home/ayu23/vllm_env/bin/activate && echo {b64} | base64 -d | python3"'
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
