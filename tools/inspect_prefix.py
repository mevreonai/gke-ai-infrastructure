import csv

with open('rtx_g4_smoke_v5/v6_suite/results/vllm_runs.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

for r in rows:
    if 'prefix' in r['case'] or 'prefix' in r['bench']:
        print(f"{r['case']} {r['bench']}: TTFT={r['mean_ttft_ms']} first_ttft={r.get('prefix_first_ttft_ms')} repeat_ttft={r.get('prefix_repeat_ttft_median_ms')} hits={r.get('prefix_hits_delta')} queries={r.get('prefix_queries_delta')}")
