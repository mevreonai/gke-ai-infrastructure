import re, os, csv
from collections import defaultdict

rates = ['NATIVE', '100', '50', '20', '10']
rate_labels = {
    'NATIVE': 'GCP Native (173/175 Gbps)',
    '100': 'Capped 100 Gbps',
    '50': 'Capped 50 Gbps',
    '20': 'Capped 20 Gbps',
    '10': 'Capped 10 Gbps'
}

base_dir = '/home/ayu23/rtx_g4_smoke/allreduce_network_sweep'
parsed_data = {}

for rate in rates:
    log_file = os.path.join(base_dir, f'allreduce_tp16_{rate}.log')
    if not os.path.exists(log_file):
        print(f"Warning: {log_file} does not exist")
        continue
    
    size_entries = defaultdict(list)
    with open(log_file) as f:
        for line in f:
            m = re.search(r'^\s*(\d+)\s+\d+\s+float\s+sum\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)', line)
            if m:
                size_b = int(m.group(1))
                time_us = float(m.group(2))
                size_entries[size_b].append(time_us)
    
    parsed_data[rate] = {}
    for size_b, times in size_entries.items():
        max_t = max(times)
        algbw = (size_b / 1e9) / (max_t / 1e6)
        busbw = 1.875 * algbw
        parsed_data[rate][size_b] = {
            'time_us': max_t,
            'algbw_gbs': algbw,
            'busbw_gbs': busbw
        }

# All unique sizes
all_sizes = sorted(list(set(s for r in parsed_data.values() for s in r.keys())))

# Filter to key payload sizes starting from 8 KiB (8192)
key_sizes = [s for s in all_sizes if s >= 8192]

# Build CSV
csv_rows = []
for s in key_sizes:
    kb = s / 1024
    mb = s / (1024 * 1024)
    label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
    if s == 8192:
        label += " (Min Size 8KB)"
    elif s == 16384:
        label += " (Decode Token)"
    elif s == 134217728:
        label += " (8K Prefill)"
        
    row = {
        'size_bytes': s,
        'payload_label': label,
        'native_175g_time_us': round(parsed_data.get('NATIVE', {}).get(s, {}).get('time_us', 0), 2),
        'native_175g_algbw_gbs': round(parsed_data.get('NATIVE', {}).get(s, {}).get('algbw_gbs', 0), 2),
        'capped_100g_time_us': round(parsed_data.get('100', {}).get(s, {}).get('time_us', 0), 2),
        'capped_100g_algbw_gbs': round(parsed_data.get('100', {}).get(s, {}).get('algbw_gbs', 0), 2),
        'capped_50g_time_us': round(parsed_data.get('50', {}).get(s, {}).get('time_us', 0), 2),
        'capped_50g_algbw_gbs': round(parsed_data.get('50', {}).get(s, {}).get('algbw_gbs', 0), 2),
        'capped_20g_time_us': round(parsed_data.get('20', {}).get(s, {}).get('time_us', 0), 2),
        'capped_20g_algbw_gbs': round(parsed_data.get('20', {}).get(s, {}).get('algbw_gbs', 0), 2),
        'capped_10g_time_us': round(parsed_data.get('10', {}).get(s, {}).get('time_us', 0), 2),
        'capped_10g_algbw_gbs': round(parsed_data.get('10', {}).get(s, {}).get('algbw_gbs', 0), 2),
    }
    csv_rows.append(row)

out_csv = os.path.join(base_dir, 'allreduce_network_bandwidth_sweep.csv')
with open(out_csv, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"Wrote CSV to {out_csv}")

# Build Markdown
md = []
md.append("# Multi-Node AllReduce (TP=16) Across Network Bandwidths: 10G, 20G, 50G, 100G, 175G")
md.append("Empirically measured across 2 nodes x 8x NVIDIA RTX PRO 6000 Ada Blackwell GPUs on GCP.\n")
md.append("Test command: `all_reduce_perf_docker -b 8K -e 256M -f 2 -g 1` across 16 ranks.\n")

md.append("| Payload Size | Native 175G (173 Gbps) | Capped 100G | Capped 50G | Capped 20G | Capped 10G | 100G vs Nat | 20G vs Nat | 10G vs Nat Penalty |")
md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in csv_rows:
    t_nat = r['native_175g_time_us']
    t_100 = r['capped_100g_time_us']
    t_50 = r['capped_50g_time_us']
    t_20 = r['capped_20g_time_us']
    t_10 = r['capped_10g_time_us']
    r_100 = f"{t_100 / t_nat:.2f}x" if t_nat > 0 else "N/A"
    r_20 = f"{t_20 / t_nat:.2f}x" if t_nat > 0 else "N/A"
    r_10 = f"{t_10 / t_nat:.2f}x" if t_nat > 0 else "N/A"
    md.append(f"| **{r['payload_label']}** | {t_nat:.2f} µs | {t_100:.2f} µs | {t_50:.2f} µs | {t_20:.2f} µs | {t_10:.2f} µs | {r_100} | {r_20} | **{r_10}** |")

out_md = os.path.join(base_dir, 'ALLREDUCE_NETWORK_SWEEP_REPORT.md')
with open(out_md, 'w') as f:
    f.write('\n'.join(md) + '\n')

print(f"Wrote Report to {out_md}")
