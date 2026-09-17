import csv, json, os, re
from collections import defaultdict

# 1. Load TP4 and TP8 from existing summary
tp4_data = {}
tp8_data = {}

summary_path = '/home/ayu23/rtx_g4_smoke/results/20260915_smoke_v4/summary/nccl_points.csv'
if os.path.exists(summary_path):
    with open(summary_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['kind'] == 'ALLREDUCE':
                tp = int(row['tp'])
                b = int(row['size_bytes'])
                entry = {
                    'time_us': float(row['time_us']),
                    'algbw_gbs': float(row['algbw_GBs']),
                    'busbw_gbs': float(row['busbw_GBs'])
                }
                if tp == 4:
                    tp4_data[b] = entry
                elif tp == 8:
                    tp8_data[b] = entry

# 2. Load TP2
tp2_data = {}
tp2_log = '/home/ayu23/rtx_g4_smoke/pair_results/tp2.log'
if os.path.exists(tp2_log):
    with open(tp2_log) as f:
        for line in f:
            m = re.search(r'^\s*(\d+)\s+\d+\s+float\s+sum\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)', line)
            if m:
                b = int(m.group(1))
                tp2_data[b] = {
                    'time_us': float(m.group(2)),
                    'algbw_gbs': float(m.group(3)),
                    'busbw_gbs': float(m.group(4))
                }

# 3. Load TP16
tp16_raw = defaultdict(list)
tp16_log = '/home/ayu23/rtx_g4_smoke/pair_results/tp16.log'
if os.path.exists(tp16_log):
    with open(tp16_log) as f:
        for line in f:
            m = re.search(r'^\s*(\d+)\s+\d+\s+float\s+sum\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)', line)
            if m:
                b = int(m.group(1))
                tp16_raw[b].append(float(m.group(2)))

tp16_data = {}
for b, times in tp16_raw.items():
    max_t = max(times)
    algbw = (b / 1e9) / (max_t / 1e6)
    busbw = 1.875 * algbw
    tp16_data[b] = {
        'time_us': max_t,
        'algbw_gbs': algbw,
        'busbw_gbs': busbw
    }

# Sizes of interest
sizes = [16384, 131072, 524288, 67108864, 134217728, 268435456]
size_labels = {
    16384: '16 KiB (Decode Proxy)',
    131072: '128 KiB',
    524288: '512 KiB',
    67108864: '64 MiB',
    134217728: '128 MiB (8K Prefill Proxy)',
    268435456: '256 MiB'
}

# Generate Consolidated CSV
csv_rows = []
for s in sizes:
    csv_rows.append({
        'size_bytes': s,
        'payload_label': size_labels.get(s, str(s)),
        # Pair 1: TP16/PP1 vs TP8/PP2 vs TP4/PP4
        'pair1_tp16_time_us': round(tp16_data.get(s, {}).get('time_us', 0), 2),
        'pair1_tp16_algbw_gbs': round(tp16_data.get(s, {}).get('algbw_gbs', 0), 2),
        'pair1_tp8_time_us': round(tp8_data.get(s, {}).get('time_us', 0), 2),
        'pair1_tp8_algbw_gbs': round(tp8_data.get(s, {}).get('algbw_gbs', 0), 2),
        'pair1_tp4_time_us': round(tp4_data.get(s, {}).get('time_us', 0), 2),
        'pair1_tp4_algbw_gbs': round(tp4_data.get(s, {}).get('algbw_gbs', 0), 2),
        # Pair 2: TP8 vs TP2
        'pair2_tp8_time_us': round(tp8_data.get(s, {}).get('time_us', 0), 2),
        'pair2_tp8_algbw_gbs': round(tp8_data.get(s, {}).get('algbw_gbs', 0), 2),
        'pair2_tp2_time_us': round(tp2_data.get(s, {}).get('time_us', 0), 2),
        'pair2_tp2_algbw_gbs': round(tp2_data.get(s, {}).get('algbw_gbs', 0), 2),
        # Pair 3: TP16 vs TP1
        'pair3_tp16_time_us': round(tp16_data.get(s, {}).get('time_us', 0), 2),
        'pair3_tp16_algbw_gbs': round(tp16_data.get(s, {}).get('algbw_gbs', 0), 2),
        'pair3_tp1_time_us': 0.0,
        'pair3_tp1_algbw_gbs': 0.0
    })

out_dir = '/home/ayu23/rtx_g4_smoke/pair_results'
os.makedirs(out_dir, exist_ok=True)
out_csv = os.path.join(out_dir, 'three_pair_results.csv')
with open(out_csv, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
    writer.writeheader()
    writer.writerows(csv_rows)

print(f'Wrote CSV to {out_csv}')

# Generate Markdown Report
md = []
md.append('# Empirical 3-Pair AllReduce Benchmark Report')
md.append('Tested on 2x GCP G4 nodes (16x NVIDIA RTX PRO 6000 Ada Blackwell Server Edition GPUs).\n')

md.append('## Pair 1: (TP=16, PP=1) vs (TP=8, PP=2) vs (TP=4, PP=4)')
md.append('| Payload Size | TP=16, PP=1 Time (µs) | TP=16 AlgBW | TP=8, PP=2 Time (µs) | TP=8 AlgBW | TP=4, PP=4 Time (µs) | TP=4 AlgBW | Optimal Config |')
md.append('|---|---:|---:|---:|---:|---:|---:|:---:|')
for r in csv_rows:
    p16_t = r['pair1_tp16_time_us']
    p16_bw = r['pair1_tp16_algbw_gbs']
    p8_t = r['pair1_tp8_time_us']
    p8_bw = r['pair1_tp8_algbw_gbs']
    p4_t = r['pair1_tp4_time_us']
    p4_bw = r['pair1_tp4_algbw_gbs']
    opt = 'TP=4' if p4_t < p8_t and p4_t < p16_t else 'TP=8'
    md.append(f"| **{r['payload_label']}** | {p16_t:.2f} µs | {p16_bw:.2f} GB/s | {p8_t:.2f} µs | {p8_bw:.2f} GB/s | {p4_t:.2f} µs | {p4_bw:.2f} GB/s | **{opt}** |")

md.append('\n## Pair 2: TP=8 vs TP=2 (Cross-Socket vs Single-Switch)')
md.append('| Payload Size | TP=8 Time (µs) | TP=8 AlgBW | TP=2 Time (µs) | TP=2 AlgBW | TP=2 Speedup |')
md.append('|---|---:|---:|---:|---:|---:|')
for r in csv_rows:
    p8_t = r['pair2_tp8_time_us']
    p8_bw = r['pair2_tp8_algbw_gbs']
    p2_t = r['pair2_tp2_time_us']
    p2_bw = r['pair2_tp2_algbw_gbs']
    speedup = f"{p8_t / p2_t:.2f}x" if p2_t > 0 else "N/A"
    md.append(f"| **{r['payload_label']}** | {p8_t:.2f} µs | {p8_bw:.2f} GB/s | {p2_t:.2f} µs | {p2_bw:.2f} GB/s | **{speedup}** |")

md.append('\n## Pair 3: TP=16 vs TP=1 (Network Scaling vs Zero-Comm Baseline)')
md.append('| Payload Size | TP=16 Time (µs) | TP=16 AlgBW | TP=1 Time (µs) | TP=1 Overhead | Trade-off Description |')
md.append('|---|---:|---:|---:|---:|---|')
for r in csv_rows:
    p16_t = r['pair3_tp16_time_us']
    p16_bw = r['pair3_tp16_algbw_gbs']
    md.append(f"| **{r['payload_label']}** | {p16_t:.2f} µs | {p16_bw:.2f} GB/s | **0.00 µs** | 0 B | TP=1 eliminates {p16_t:.2f} µs collective sync per layer. |")

out_md = os.path.join(out_dir, 'THREE_PAIR_ANALYSIS.md')
with open(out_md, 'w') as f:
    f.write('\n'.join(md) + '\n')

print(f'Wrote Report to {out_md}')
