import json

with open('/home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/V9_MATRIX.json') as f:
    m = json.load(f)

for c in m['scaleout_cases']:
    if c['name'] == 'tp8_pp2_dist':
        print("tp8_pp2_dist benchmarks:")
        for b in c['benchmarks']:
            print(" -", b['name'], b)
