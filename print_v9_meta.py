import re
import json

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    c = f.read()

m = re.search(r'CANONICAL_DASHBOARD_DATA\s*=\s*(\{.*?\});\s*(?:window\.|var |let |const |\n)', c, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print("Model Metadata:")
    print(json.dumps(data.get('model_metadata', {}), indent=2))
    print("\nCampaign Summary:")
    print(json.dumps(data.get('campaign_summary', {}), indent=2))
