import subprocess

code = '''
import json, glob, os

def check_dir(title, path):
    print(f"=== {title}: {path} ===")
    files = sorted(glob.glob(f"{path}/*"))
    if not files:
        print("  NO FILES FOUND!")
        return
    for f in files:
        sz = os.path.getsize(f)
        basename = os.path.basename(f)
        if f.endswith('.json'):
            try:
                data = json.load(open(f))
                if isinstance(data, list):
                    sample = f"List of {len(data)} items"
                elif isinstance(data, dict):
                    keys = list(data.keys())[:5]
                    sample = f"Dict with keys {keys}"
                else:
                    sample = "Valid JSON"
                print(f"  {basename} ({sz} bytes) - REAL JSON: {sample}")
            except Exception as e:
                print(f"  {basename} ({sz} bytes) - JSON ERROR: {e}")
        elif f.endswith('.csv'):
            lines = open(f).readlines()
            print(f"  {basename} ({sz} bytes) - REAL CSV: {len(lines)} lines (header: {lines[0].strip() if lines else 'empty'})")
        elif f.endswith('.txt') or f.endswith('.log'):
            lines = open(f, errors='ignore').readlines()
            print(f"  {basename} ({sz} bytes) - TEXT/LOG: {len(lines)} lines")
        else:
            print(f"  {basename} ({sz} bytes)")

check_dir("1. HARDWARE RAW NODE 0", "/home/ayu23/v9_full_results/v9_full_production_20260930_090004/hardware_raw/node0")
check_dir("2. HARDWARE RAW NODE 1", "/home/ayu23/v9_full_results/v9_full_production_20260930_090004/hardware_raw/node1")
check_dir("3. NETWORK RAW NODE 0", "/home/ayu23/v9_full_results/v9_full_production_20260930_090004/hardware_raw/network_node0")
check_dir("4. HARDWARE PROCESSED", "/home/ayu23/v9_full_results/v9_full_production_20260930_090004/hardware_processed")
'''

import base64
b64 = base64.b64encode(code.encode()).decode()
write_cmd = f"echo '{b64}' | base64 -d > /tmp/audit_script.py && /home/ayu23/vllm_env/bin/python3 /tmp/audit_script.py"
res = subprocess.run(["python", "run_ssh.py", "kimi-node-0", write_cmd], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
