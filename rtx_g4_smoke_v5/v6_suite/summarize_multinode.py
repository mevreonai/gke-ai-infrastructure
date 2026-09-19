import json, glob

files = sorted(glob.glob('/home/ayu23/v5_profiling/results/20260919_215146/kimi-node-0/vllm_multi_node/*/*case_manifest*.json'))
for path in files:
    d = json.load(open(path))
    print('=== Case:', d.get('name'), '===')
    if 'error' in d:
        print('  Error:', d['error'])
    for b in d.get('benchmarks', []):
        print(f"  Bench: {b.get('name')} | Status: {b.get('status')} | Input: {b.get('input')} | Mean TTFT: {b.get('ttft_mean_ms')} | Mean TPOT: {b.get('tpot_mean_ms')}")
