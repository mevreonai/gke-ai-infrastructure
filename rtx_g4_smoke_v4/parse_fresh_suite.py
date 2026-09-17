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
            "tp4_local": parse_log(os.path.join(coll_dir, "tp4.log")),
            "tp8_local": parse_log(os.path.join(coll_dir, "tp8.log")),
            "tp4": {},
            "tp8": {},
            "tp16": {}
        }
        
        # Parse all topologies across all 5 network rates
        for r in rates:
            all_data[coll]["tp16"][r] = parse_log(os.path.join(coll_dir, f"tp16_{r}.log"))
            all_data[coll]["tp8"][r] = parse_log(os.path.join(coll_dir, f"tp8_{r}.log"))
            all_data[coll]["tp4"][r] = parse_log(os.path.join(coll_dir, f"tp4_{r}.log"))

            suffix = "175g_native" if r == "NATIVE" else f"{r}g"

            # Write individual CSVs for each topology and rate
            for tp_name, tp_key in [("TP=16", "tp16"), ("TP=8 Multi-Node", "tp8"), ("TP=4 Multi-Node", "tp4")]:
                tp_prefix = tp_key
                rows = []
                for s, v in all_data[coll][tp_key][r].items():
                    kb = s / 1024
                    mb = s / (1024 * 1024)
                    label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
                    rows.append({
                        "size_bytes": s,
                        "payload_label": label,
                        "collective": coll.upper(),
                        "tp": tp_name,
                        "network_rate": rate_labels[r],
                        "time_us": v["time_us"],
                        "algbw_gb_s": v["algbw_gb_s"]
                    })
                if rows:
                    with open(os.path.join(coll_dir, f"{coll}_{tp_prefix}_{suffix}.csv"), "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)

        # Write unified sweep CSV for TP=16, TP=8, TP=4
        for tp_name, tp_key in [("TP=16", "tp16"), ("TP=8 Multi-Node", "tp8"), ("TP=4 Multi-Node", "tp4")]:
            sweep_rows = []
            sizes = sorted(all_data[coll][tp_key]["NATIVE"].keys())
            for s in sizes:
                kb = s / 1024
                mb = s / (1024 * 1024)
                label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
                row = {
                    "size_bytes": s,
                    "payload_label": label,
                    "collective": coll.upper(),
                    "tp": tp_name
                }
                for r in rates:
                    v = all_data[coll][tp_key][r].get(s, {"time_us": 0, "algbw_gb_s": 0})
                    row[f"time_us_{r}"] = v["time_us"]
                    row[f"algbw_gb_s_{r}"] = v["algbw_gb_s"]
                sweep_rows.append(row)
            if sweep_rows:
                with open(os.path.join(coll_dir, f"{coll}_{tp_key}_sweep.csv"), "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=sweep_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(sweep_rows)

        # Write node-local / socket-local baselines
        for tp_name, tp_key, filename in [
            ("TP=8 (Node-Local PCIe)", "tp8_local", f"{coll}_tp8_node_local.csv"),
            ("TP=4 (Socket-Local Single-NUMA)", "tp4_local", f"{coll}_tp4_socket_local.csv")
        ]:
            local_rows = []
            for s, v in all_data[coll][tp_key].items():
                kb = s / 1024
                mb = s / (1024 * 1024)
                label = f"{int(kb)} KiB" if mb < 1 else f"{int(mb)} MiB"
                local_rows.append({
                    "size_bytes": s,
                    "payload_label": label,
                    "collective": coll.upper(),
                    "topology": tp_name,
                    "time_us": v["time_us"],
                    "algbw_gb_s": v["algbw_gb_s"]
                })
            if local_rows:
                with open(os.path.join(coll_dir, filename), "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=local_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(local_rows)

    with open(os.path.join(suite_dir, "master_benchmarks.json"), "w") as f:
        json.dump(all_data, f, indent=2)
    print("Successfully generated all CSVs and master_benchmarks.json!")

if __name__ == "__main__":
    run_parser()
