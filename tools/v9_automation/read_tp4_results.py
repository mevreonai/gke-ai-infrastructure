import json, os, sys

base = 'v9_full_result/vllm_scaleout_network_matrix/NETWORK_NATIVE/results/tp4_pp2_dist'
benchmarks = ['1024_c1', '8192_c1', '8192_c4', '131072_c1', '131072_c4', '524288_c1', '1000000_c1']

all_results = {}
for b in benchmarks:
    fpath = os.path.join(base, b, f'{b}.json')
    with open(fpath, 'r') as f:
        data = json.load(f)
    summary = {}
    for k in ['mean_ttft_ms', 'median_ttft_ms', 'p99_ttft_ms',
              'mean_tpot_ms', 'median_tpot_ms', 'p99_tpot_ms',
              'mean_itl_ms', 'median_itl_ms', 'p99_itl_ms',
              'output_throughput', 'total_token_throughput',
              'request_throughput', 'input_throughput',
              'completed', 'total_input', 'total_output',
              'duration', 'mean_e2e_latency_ms', 'median_e2e_latency_ms']:
        if k in data:
            summary[k] = data[k]
    all_results[b] = summary

sys.stdout.buffer.write(json.dumps(all_results, indent=2).encode('utf-8'))
