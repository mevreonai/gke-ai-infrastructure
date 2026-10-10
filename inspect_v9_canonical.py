import re
import json

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    c = f.read()

m = re.search(r'CANONICAL_DASHBOARD_DATA\s*=\s*(\{.*?\});\s*(?:window\.|var |let |const |\n)', c, re.DOTALL)
if m:
    raw_json = m.group(1)
    print("Found raw JSON, length:", len(raw_json))
    try:
        data = json.loads(raw_json)
        print("Keys in CANONICAL_DASHBOARD_DATA:", list(data.keys()))
        for k in data.keys():
            if isinstance(data[k], dict):
                print(f"  {k}: dict with {len(data[k])} keys -> {list(data[k].keys())[:5]}")
            elif isinstance(data[k], list):
                print(f"  {k}: list with {len(data[k])} items")
            else:
                print(f"  {k}: {type(data[k])}")
    except Exception as e:
        print("JSON parse error:", e)
else:
    print("Regex match failed for CANONICAL_DASHBOARD_DATA")
