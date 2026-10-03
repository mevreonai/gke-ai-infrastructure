import re, json

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = '"evidence_registry": {'
idx_start = text.index(start_marker) + len('"evidence_registry": ')
depth = 0
idx = idx_start
while idx < len(text):
    if text[idx] == '{':
        depth += 1
    elif text[idx] == '}':
        depth -= 1
        if depth == 0:
            break
    idx += 1

registry_json = text[idx_start:idx+1]
registry = json.loads(registry_json)

# Find all tp4_pp2_dist entries
for ev_id, entry in sorted(registry.items()):
    case = entry.get('case', '')
    if 'tp4_pp2' in case.lower():
        print(f"{ev_id}: case={case}, bench={entry.get('bench')}, status={entry.get('status')}")
        for k, v in entry.items():
            print(f"  {k}: {v}")
        print()
