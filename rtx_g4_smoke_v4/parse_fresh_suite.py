import re, os, json, csv
from collections import defaultdict

suite_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results\fresh_benchmark_suite"

collectives = ["allreduce", "allgather", "reducescatter"]
rates = ["NATIVE", "100", "50", "20", "10"]
rate_labels = {
    "NATIVE": "175G Native (173.6 Gbps)",
    "100": "100G Capped",
    "50": "50G Capped",
    "20": "20G Capped",
    "10": "10G Capped"
}

def parse_log(filepath):
    if not os.path.exists(filepath):
        print(f"Not found: {filepath}")
        return {}
    size_entries = defaultdict(list)
    with open(filepath, "r") as f:
        for line in f:
            m = re.search(r'^\s*(\d+)\s+\d+\s+(?:[a-zA-Z0-9_\-]+)\s+(?:[a-zA-Z0-9_\-]+)\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)', line)
            if m:
                size_b = int(m.group(1))
                time_us = float(m.group(2))
                size_entries[size_b].append(time_us)
    
    results = {}
    for size_b in sorted(size_entries.keys()):
        if size_b < 8192:
            continue
        max_t = max(size_entries[size_b])
        algbw = (size_b / 1e9) / (max_t / 1e6)
        results[size_b] = {
            "time_us": round(max_t, 2),
            "algbw_gb_s": round(algbw, 4)
        }
    return results

def run_parser():
    all_data = {}
    for coll in collectives:
        coll_dir = os.path.join(suite_dir, coll)
        all_data[coll] = {
            "tp4": parse_log(os.path.join(coll_dir, "tp4.log")),
            "tp8": parse_log(os.path.join(coll_dir, "tp8.log")),
            "tp16": {}
        }
        for r in rates:
            all_data[coll]["tp16"][r] = parse_log(os.path.join(coll_dir, f"tp16_{r}.log"))
            
            # Write individual rate CSV for TP=16
            r_rows = []
            for s, v in all_data[coll]["tp16"][r].items():
                kb = s / 1024
                mb = s / (1024 * 1024)
                label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
                r_rows.append({
                    "size_bytes": s,
                    "payload_label": label,
                    "collective": coll.upper(),
                    "tp": "TP=16",
                    "network_rate": rate_labels[r],
                    "time_us": v["time_us"],
                    "algbw_gb_s": v["algbw_gb_s"]
                })
            if r_rows:
                suffix = "175g_native" if r == "NATIVE" else f"{r}g"
                with open(os.path.join(coll_dir, f"{coll}_tp16_{suffix}.csv"), "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=r_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(r_rows)

        # Write CSV for TP=4
        tp4_rows = []
        for s, v in all_data[coll]["tp4"].items():
            kb = s / 1024
            mb = s / (1024 * 1024)
            label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
            tp4_rows.append({
                "size_bytes": s,
                "payload_label": label,
                "collective": coll.upper(),
                "tp": "TP=4 (Single-NUMA)",
                "time_us": v["time_us"],
                "algbw_gb_s": v["algbw_gb_s"]
            })
        if tp4_rows:
            with open(os.path.join(coll_dir, f"{coll}_tp4.csv"), "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=tp4_rows[0].keys())
                writer.writeheader()
                writer.writerows(tp4_rows)

        # Write CSV for TP=8
        tp8_rows = []
        for s, v in all_data[coll]["tp8"].items():
            kb = s / 1024
            mb = s / (1024 * 1024)
            label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
            tp8_rows.append({
                "size_bytes": s,
                "payload_label": label,
                "collective": coll.upper(),
                "tp": "TP=8 (Cross-Socket)",
                "time_us": v["time_us"],
                "algbw_gb_s": v["algbw_gb_s"]
            })
        if tp8_rows:
            with open(os.path.join(coll_dir, f"{coll}_tp8.csv"), "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=tp8_rows[0].keys())
                writer.writeheader()
                writer.writerows(tp8_rows)

        # Write combined CSV for TP=16
        tp16_sizes = sorted(list(set(s for r_data in all_data[coll]["tp16"].values() for s in r_data.keys())))
        tp16_rows = []
        for s in tp16_sizes:
            kb = s / 1024
            mb = s / (1024 * 1024)
            label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
            row = {
                "size_bytes": s,
                "payload_label": label,
                "collective": coll.upper(),
                "native_175g_time_us": all_data[coll]["tp16"].get("NATIVE", {}).get(s, {}).get("time_us", 0),
                "capped_100g_time_us": all_data[coll]["tp16"].get("100", {}).get(s, {}).get("time_us", 0),
                "capped_50g_time_us": all_data[coll]["tp16"].get("50", {}).get(s, {}).get("time_us", 0),
                "capped_20g_time_us": all_data[coll]["tp16"].get("20", {}).get(s, {}).get("time_us", 0),
                "capped_10g_time_us": all_data[coll]["tp16"].get("10", {}).get(s, {}).get("time_us", 0),
                "tp8_local_time_us": all_data[coll]["tp8"].get(s, {}).get("time_us", 0),
                "tp4_local_time_us": all_data[coll]["tp4"].get(s, {}).get("time_us", 0),
            }
            tp16_rows.append(row)
        if tp16_rows:
            with open(os.path.join(coll_dir, f"{coll}_tp16_sweep.csv"), "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=tp16_rows[0].keys())
                writer.writeheader()
                writer.writerows(tp16_rows)

    # Dump master JSON for dashboard
    json_path = os.path.join(suite_dir, "master_benchmarks.json")
    with open(json_path, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"Master benchmarks dumped to {json_path}")

if __name__ == "__main__":
    run_parser()
