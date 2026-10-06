import json, re

combined_runs = json.load(open(r"v8_full_results\results\real_data\final_validation\combined_vllm_runs.json", encoding="utf-8"))
print(f"Total runs in combined_vllm_runs: {len(combined_runs)}")

run_dict = {}
for r in combined_runs:
    key = (r.get("case"), r.get("bench"))
    run_dict[key] = r

sample = list(run_dict.items())[:5]
for k, v in sample:
    print(k, "warmups:", v.get("warmups"), "prompts:", v.get("prompts_requested"))
