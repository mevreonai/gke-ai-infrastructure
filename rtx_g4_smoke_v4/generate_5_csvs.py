import re, os, csv
from collections import defaultdict

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results\network_allreduce_sweep"

tiers = [
    ("NATIVE", "allreduce_175g_native.csv", "GCP Native (173.58 Gbps)", 175),
    ("100", "allreduce_100g.csv", "Capped 100 Gbps", 100),
    ("50", "allreduce_50g.csv", "Capped 50 Gbps", 50),
    ("20", "allreduce_20g.csv", "Capped 20 Gbps", 20),
    ("10", "allreduce_10g.csv", "Capped 10 Gbps", 10),
]

for rate_key, csv_name, label_text, cap_gbit in tiers:
    log_path = os.path.join(base_dir, f"allreduce_tp16_{rate_key}.log")
    if not os.path.exists(log_path):
        print(f"File not found: {log_path}")
        continue
    
    size_entries = defaultdict(list)
    with open(log_path, "r") as f:
        for line in f:
            m = re.search(r'^\s*(\d+)\s+\d+\s+float\s+sum\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)', line)
            if m:
                size_b = int(m.group(1))
                time_us = float(m.group(2))
                size_entries[size_b].append(time_us)
                
    rows = []
    for size_b in sorted(size_entries.keys()):
        if size_b < 8192:  # starting from 8 KiB
            continue
        max_t = max(size_entries[size_b])
        algbw = (size_b / 1e9) / (max_t / 1e6)
        busbw = 1.875 * algbw
        
        kb = size_b / 1024
        mb = size_b / (1024 * 1024)
        human_label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
        if size_b == 8192:
            human_label += " (Min Size 8KB)"
        elif size_b == 16384:
            human_label += " (Decode Token)"
        elif size_b == 134217728:
            human_label += " (8K Prefill)"
            
        rows.append({
            "size_bytes": size_b,
            "payload_label": human_label,
            "elements": size_b // 4,
            "network_tier": label_text,
            "bandwidth_cap_gbit": cap_gbit,
            "time_us": round(max_t, 2),
            "algbw_gb_s": round(algbw, 4),
            "busbw_gb_s": round(busbw, 4)
        })
        
    out_csv = os.path.join(base_dir, csv_name)
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated: {out_csv} ({len(rows)} rows)")
