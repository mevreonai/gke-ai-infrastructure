import subprocess
import json

script = """
import subprocess

p = subprocess.run(['tail', '-n', '15', '/home/ayu23/v9_full_production_execution.log'], capture_output=True, text=True)
print(p.stdout)

"""

with open('temp_audit.py', 'w') as f:
    f.write(script.strip())

subprocess.run('gcloud.cmd compute scp temp_audit.py kimi-node-0:/home/ayu23/audit_node.py --zone=us-central1-b --project=mevreon', shell=True)
res = subprocess.run('gcloud.cmd compute ssh kimi-node-0 --zone=us-central1-b --project=mevreon --command="/home/ayu23/vllm_env/bin/python3 /home/ayu23/audit_node.py"', shell=True, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
if res.stderr:
    print("STDERR:")
    print(res.stderr)

