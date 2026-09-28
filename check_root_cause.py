import subprocess
import base64

script = """
import re

for name in ['tp4_kv_fp8_probe', 'tp4_offload_probe']:
    p = f'/home/ayu23/v9_full_results/v9_test2_20260927_163750/vllm_single_node_v9_matrix/{name}/server.log'
    print(f'=== ROOT CAUSE FOR {name} ===')
    try:
        lines = open(p).readlines()
        for l in lines:
            if 'Error' in l or 'Exception' in l or 'not supported' in l or 'unsupported' in l or 'ValueError' in l or 'TypeError' in l:
                print(l.strip())
    except Exception as e:
        print('Error:', e)
"""

b64 = base64.b64encode(script.encode('utf-8')).decode('utf-8')
cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --tunnel-through-iap --command="echo {b64} | base64 -d | python3"'
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
