import json

with open('data/evidence.json', 'r', encoding='utf-8') as f:
    rows = json.load(f)['rows']

for r in rows:
    if r['case'] in ['tp4_closedloop_8k', 'tp8_qualification', 'tp4_qualification']:
        print(f"{r['case']} {r['bench']}: row_id={r['row_id']} TTFT={r['ttft_ms']} TPOT={r['tpot_ms']} tok/s={r['output_tok_s']} metric_samples={r.get('metric_samples')} completed={r.get('completed')}")
