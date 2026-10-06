import pandas as pd

df = pd.read_csv('v8_full_results/results/real_data/final_validation/combined_vllm_runs.csv')

topos = [
    ('TP4 / PP4 (Dist)', 'tp4_pp4_dist'),
    ('TP8 / PP2 (Dist)', 'tp8_pp2_dist'),
    ('TP4 / PP2 (Dist)', 'tp4_pp2_dist'),
    ('TP16 / PP1 (Dist)', 'tp16_pp1_dist')
]

ctxs = [
    ('128K', 131072),
    ('512K', 524288),
    ('1M', 1048576)
]

print("Topology | Context | Native TTFT | 100G TTFT | 100G Delta | 20G TTFT | 20G Delta")
for label, case_id in topos:
    for ctx_label, ctx_val in ctxs:
        nat = df[(df['case'] == case_id) & (df['requested_input_tokens'] == ctx_val) & (df['network_provenance'] == 'GCP_NATIVE')]
        c100 = df[(df['case'] == case_id) & (df['requested_input_tokens'] == ctx_val) & (df['network_provenance'] == 'CAPPED_100G')]
        c20 = df[(df['case'] == case_id) & (df['requested_input_tokens'] == ctx_val) & (df['network_provenance'] == 'CAPPED_20G')]
        
        nat_ttft = nat['mean_ttft_ms'].values[0] / 1000.0 if len(nat) > 0 else 0.0
        c100_ttft = c100['mean_ttft_ms'].values[0] / 1000.0 if len(c100) > 0 else 0.0
        c20_ttft = c20['mean_ttft_ms'].values[0] / 1000.0 if len(c20) > 0 else 0.0
        
        d100 = ((c100_ttft - nat_ttft) / nat_ttft) * 100.0 if nat_ttft > 0 else 0.0
        d20 = ((c20_ttft - nat_ttft) / nat_ttft) * 100.0 if nat_ttft > 0 else 0.0
        
        print(f"{label} | {ctx_label} | {nat_ttft:.3f}s | {c100_ttft:.3f}s | {d100:+.2f}% | {c20_ttft:.3f}s | {d20:+.2f}%")
