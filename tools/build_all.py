import json
import csv
import os
import re
import datetime

print("Starting tools/build_all.py...")

# ==============================================================================
# 1. Authoritative Data Loading & Validation
# ==============================================================================
with open('rtx_g4_smoke_v5/03_dashboards/docs/audit/02_evidence_rows.json', 'r', encoding='utf-8') as f:
    full_ev = json.load(f)

meta = full_ev['meta']
rows = full_ev['rows']
missing = full_ev['missing_configured_cases']

# Join with vllm_runs.csv
with open('rtx_g4_smoke_v5/v6_suite/results/vllm_runs.csv', 'r', encoding='utf-8') as f:
    vllm_csv = list(csv.DictReader(f))

vllm_map = {(r['case'], r['bench']): r for r in vllm_csv}

for r in rows:
    key = (r['case'], r['bench'])
    if key not in vllm_map:
        raise KeyError(f"Missing row in vllm_runs.csv: {key}")
    vr = vllm_map[key]
    
    # Empty string maps to null (None), never 0.0
    r['metric_samples'] = int(vr['metric_samples']) if vr.get('metric_samples') not in [None, ''] else None
    r['completed'] = int(vr['completed']) if vr.get('completed') not in [None, ''] else None
    r['preemptions_delta'] = float(vr['preemptions_delta']) if vr.get('preemptions_delta') not in [None, ''] else None
    r['queue_mean_s_from_hist'] = float(vr['queue_mean_s_from_hist']) if vr.get('queue_mean_s_from_hist') not in [None, ''] else None
    r['source_file'] = 'vllm_runs.csv'

# Strict type validation
num_fields = ['tp', 'pp', 'input_tokens_displayed', 'concurrency', 'ttft_ms', 'tpot_ms', 'output_tok_s', 'kv_peak_pct', 'metric_samples', 'completed', 'preemptions_delta', 'queue_mean_s_from_hist']
for idx, r in enumerate(rows):
    for nf in num_fields:
        if r[nf] is not None and not isinstance(r[nf], (int, float)):
            raise TypeError(f"Row {idx} ({r['row_id']}) field {nf} invalid type: {r[nf]}")
    if r['run_id'] is not None:
        raise ValueError(f"Row {idx} run_id must be null")
    if r['sample_count_N'] is not None:
        raise ValueError(f"Row {idx} sample_count_N must be null")
    if not isinstance(r['extra_vs_archived_v6'], bool):
        raise TypeError(f"Row {idx} extra_vs_archived_v6 must be bool")

with open('data/evidence.json', 'w', encoding='utf-8') as f:
    json.dump(full_ev, f, indent=2)
print("Saved data/evidence.json with 59 validated rows.")

# Load scaleout.json
with open('data/scaleout.json', 'r', encoding='utf-8') as f:
    scaleout_data = json.load(f)['rows']

print(f"Loaded {len(scaleout_data)} scale-out rows.")
