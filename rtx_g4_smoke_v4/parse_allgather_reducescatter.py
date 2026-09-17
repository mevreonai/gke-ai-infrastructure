import re, os, csv
from collections import defaultdict

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results\network_allgather_reducescatter_sweep"
os.makedirs(base_dir, exist_ok=True)

tiers = [
    ("NATIVE", "175g_native", "GCP Native (173.58 Gbps)", 175),
    ("100", "100g", "Capped 100 Gbps", 100),
    ("50", "50g", "Capped 50 Gbps", 50),
    ("20", "20g", "Capped 20 Gbps", 20),
    ("10", "10g", "Capped 10 Gbps", 10),
]

def parse_collective(collective_name, busbw_factor):
    parsed_by_tier = {}
    
    for rate_key, suffix, label_text, cap_gbit in tiers:
        log_path = os.path.join(base_dir, f"{collective_name}_tp16_{rate_key}.log")
        if not os.path.exists(log_path):
            print(f"File not found: {log_path}")
            continue
            
        size_entries = defaultdict(list)
        with open(log_path, "r") as f:
            for line in f:
                m = re.search(r'^\s*(\d+)\s+\d+\s+float\s+sum\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)', line)
                if not m:
                    # Some collective tests omit float/sum
                    m = re.search(r'^\s*(\d+)\s+\d+\s+(?:[a-zA-Z0-9_\-]+)\s+(?:[a-zA-Z0-9_\-]+)\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)', line)
                if m:
                    size_b = int(m.group(1))
                    time_us = float(m.group(2))
                    size_entries[size_b].append(time_us)
                    
        parsed_by_tier[rate_key] = {}
        csv_rows = []
        for size_b in sorted(size_entries.keys()):
            if size_b < 8192:
                continue
            max_t = max(size_entries[size_b])
            algbw = (size_b / 1e9) / (max_t / 1e6)
            busbw = busbw_factor * algbw
            
            kb = size_b / 1024
            mb = size_b / (1024 * 1024)
            human_label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
            if size_b == 8192:
                human_label += " (Min Size 8KB)"
            elif size_b == 16384:
                human_label += " (Decode Token)"
            elif size_b == 134217728:
                human_label += " (8K Prefill)"
                
            parsed_by_tier[rate_key][size_b] = {
                'time_us': max_t,
                'algbw_gbs': algbw,
                'busbw_gbs': busbw,
                'label': human_label
            }
            
            csv_rows.append({
                "size_bytes": size_b,
                "payload_label": human_label,
                "elements": size_b // 4,
                "collective": collective_name.upper(),
                "network_tier": label_text,
                "bandwidth_cap_gbit": cap_gbit,
                "time_us": round(max_t, 2),
                "algbw_gb_s": round(algbw, 4),
                "busbw_gb_s": round(busbw, 4)
            })
            
        tier_csv = os.path.join(base_dir, f"{collective_name}_{suffix}.csv")
        if csv_rows:
            with open(tier_csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)
            print(f"Wrote {tier_csv}")
            
    # Write combined comparison CSV
    all_sizes = sorted(list(set(s for r in parsed_by_tier.values() for s in r.keys())))
    combined_rows = []
    for s in all_sizes:
        label = parsed_by_tier.get('NATIVE', {}).get(s, {}).get('label', f"{s} bytes")
        row = {
            'size_bytes': s,
            'payload_label': label,
            'collective': collective_name.upper(),
            'native_175g_time_us': round(parsed_by_tier.get('NATIVE', {}).get(s, {}).get('time_us', 0), 2),
            'capped_100g_time_us': round(parsed_by_tier.get('100', {}).get(s, {}).get('time_us', 0), 2),
            'capped_50g_time_us': round(parsed_by_tier.get('50', {}).get(s, {}).get('time_us', 0), 2),
            'capped_20g_time_us': round(parsed_by_tier.get('20', {}).get(s, {}).get('time_us', 0), 2),
            'capped_10g_time_us': round(parsed_by_tier.get('10', {}).get(s, {}).get('time_us', 0), 2),
        }
        combined_rows.append(row)
        
    combined_csv = os.path.join(base_dir, f"{collective_name}_network_bandwidth_sweep.csv")
    if combined_rows:
        with open(combined_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=combined_rows[0].keys())
            writer.writeheader()
            writer.writerows(combined_rows)
        print(f"Wrote Combined: {combined_csv}")

# For 16 ranks:
# AllGather: busbw = (16-1)/16 * algbw = 15/16 * algbw = 0.9375 * algbw
# ReduceScatter: busbw = (16-1)/16 * algbw = 0.9375 * algbw
parse_collective("allgather", 0.9375)
parse_collective("reducescatter", 0.9375)
