import subprocess

cmd = ["python", "run_ssh.py", "kimi-node-0", "python3 -c \\\"import json; m=json.load(open('/home/ayu23/v9_full_results/v9_full_production_20260930_090004/logs/V9_MATRIX.json')); print('Total profile specs:', len(m.get('distributed_profile_specs', []))); [print(i, s.get('name'), s.get('mode'), s.get('network_mode')) for i, s in enumerate(m.get('distributed_profile_specs', []))]\\\""]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
