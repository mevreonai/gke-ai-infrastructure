import pandas as pd

df = pd.read_csv('v8_full_results/results/real_data/final_validation/combined_vllm_runs.csv')

topos = [
    ('TP4 / PP4 (Dist)', 'tp4_pp4_dist'),
    ('TP8 / PP2 (Dist)', 'tp8_pp2_dist'),
    ('TP4 / PP2 (Dist)', 'tp4_pp2_dist'),
    ('TP16 / PP1 (Dist)', 'tp16_pp1_dist')
]

benches = [
    ('128K', '128k_c1'),
    ('512K', '512k_c1'),
    ('1M', '1m_c1')
]

print("=== EXACT HEATMAP TTFT & DELTAS FROM CSV ===")
for label, case_id in topos:
    for ctx_label, bench_id in benches:
        nat = df[(df['case'] == case_id) & (df['bench'] == bench_id) & (df['network_provenance'] == 'GCP_NATIVE')]
        c100 = df[(df['case'] == case_id) & (df['bench'] == bench_id) & (df['network_provenance'] == 'GCP_CAPPED_100G')]
        c20 = df[(df['case'] == case_id) & (df['bench'] == bench_id) & (df['network_provenance'] == 'GCP_CAPPED_20G')]
        
        nat_ms = nat['mean_ttft_ms'].values[0]
        c100_ms = c100['mean_ttft_ms'].values[0]
        c20_ms = c20['mean_ttft_ms'].values[0]
        
        nat_s = nat_ms / 1000.0
        c100_s = c100_ms / 1000.0
        c20_s = c20_ms / 1000.0
        
        d100 = ((c100_ms - nat_ms) / nat_ms) * 100.0
        d20 = ((c20_ms - nat_ms) / nat_ms) * 100.0
        
        # Rule: <15% HIGH NETWORK RESILIENCE; 15-50% MODERATE; >50% HIGH CAP SENSITIVITY
        if d20 < 15.0:
            cls = "HIGH NETWORK RESILIENCE"
            badge = "s-completed"
        elif d20 <= 50.0:
            cls = "MODERATE NETWORK SENSITIVITY"
            badge = "s-running"
        else:
            cls = "HIGH CAP SENSITIVITY / EXPOSED"
            badge = "s-failed"
            
        print(f"<tr><td><b style=\"color:var(--purple)\">{label}</b></td><td>{ctx_label}</td><td>{nat_s:.3f}s</td><td>{c100_s:.3f}s</td><td><span class=\"badge b-green\">{d100:+.2f}%</span></td><td>{c20_s:.3f}s</td><td><span class=\"badge {'b-red' if d20 > 50 else 'b-green'}\">{d20:+.2f}%</span></td><td><span class=\"status {badge}\">{cls}</span></td></tr>")
