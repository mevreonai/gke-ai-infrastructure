import json

with open("/home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/V9_MATRIX.json") as f:
    m = json.load(f)

print("=== SCALEOUT CASES IN V9_MATRIX.JSON ===")
for c in m.get("scaleout_cases", []):
    print(f"Name: {c['name']}, TP: {c['tp']}, PP: {c['pp']}, Nodes: {c['nodes_required']}, ray_gpus: {c['ray_gpus_per_node']}")
