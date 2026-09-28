import subprocess
import base64

script = """
import json
print('=== KV FP8 ===')
try:
    p1 = json.load(open('/home/ayu23/v9_full_results/v9_test2_20260927_163750/vllm_single_node_v9_matrix/tp4_kv_fp8_probe/case_manifest.json'))
    print('Status:', p1.get('status'))
    print('Error:', p1.get('error'))
    print('Server log:')
    try:
        print(open('/home/ayu23/v9_full_results/v9_test2_20260927_163750/vllm_single_node_v9_matrix/tp4_kv_fp8_probe/server.log').read()[-800:])
    except Exception as e:
        print('no server.log:', e)
except Exception as e:
    print('Failed p1:', e)

print('=== OFFLOAD ===')
try:
    p2 = json.load(open('/home/ayu23/v9_full_results/v9_test2_20260927_163750/vllm_single_node_v9_matrix/tp4_offload_probe/case_manifest.json'))
    print('Status:', p2.get('status'))
    print('Error:', p2.get('error'))
    print('Server log:')
    try:
        print(open('/home/ayu23/v9_full_results/v9_test2_20260927_163750/vllm_single_node_v9_matrix/tp4_offload_probe/server.log').read()[-800:])
    except Exception as e:
        print('no server.log:', e)
except Exception as e:
    print('Failed p2:', e)
"""

b64 = base64.b64encode(script.encode('utf-8')).decode('utf-8')
cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --tunnel-through-iap --command="echo {b64} | base64 -d | python3"'
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
