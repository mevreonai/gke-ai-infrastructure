import json, os

files = os.listdir('v9_full_result/final_validation')
print("Files in final_validation:", files)

with open('v9_full_result/final_validation/FINAL_VALIDATION.json') as f:
    v = json.load(f)

# check if there are other keys or nested dicts
for k in ['core_points', 'optional_capability_points', 'coverage_counts']:
    print(k, v.get(k))

# Let's inspect combined_vllm_runs.json vs configured suite
