import base64
import subprocess

script = """
import json

# 1. Fix runner_lib.py
p = '/home/ayu23/V9_FULL/v9_core/runner_lib.py'
content = open(p).read()
old_resolved = '''def resolved(case, cfg, key, default=None):
    if key in case: return case[key]
    return cfg.get("server_defaults",{}).get(key,default)'''

new_resolved = '''def resolved(case, cfg, key, default=None):
    if key in case and case[key] is not None: return case[key]
    if key in cfg.get("server_defaults",{}) and cfg["server_defaults"][key] is not None:
        return cfg["server_defaults"][key]
    if key in cfg and cfg[key] is not None:
        return cfg[key]
    return default'''

if old_resolved in content:
    content = content.replace(old_resolved, new_resolved)
    print("Patched resolved()")
else:
    print("old_resolved not found")

old_cmd = '"--max-model-len",str(resolved(case,cfg,"max_model_len")),'
new_cmd = '"--max-model-len",str(resolved(case,cfg,"max_model_len",1048576)),'
if old_cmd in content:
    content = content.replace(old_cmd, new_cmd)
    print("Patched --max-model-len")
else:
    print("old_cmd not found")

open(p, 'w').write(content)

# 2. Fix model configs
for mpath in ['/home/ayu23/V9_FULL/configs/models/kimi_linear_48b.json', '/home/ayu23/V9_FULL/configs/models/deepseek_v41_flash.json']:
    try:
        d = json.load(open(mpath))
        if 'server_defaults' in d:
            d['server_defaults']['max_model_len'] = d.get('max_model_len', 1048576)
            json.dump(d, open(mpath, 'w'), indent=2)
            print(f'Updated {mpath}')
    except Exception as e:
        print(f'Error updating {mpath}: {e}')
"""

b64 = base64.b64encode(script.encode('utf-8')).decode('utf-8')
cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --command="echo {b64} | base64 -d | python3"'
print("Running patch on kimi-node-0...")
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
