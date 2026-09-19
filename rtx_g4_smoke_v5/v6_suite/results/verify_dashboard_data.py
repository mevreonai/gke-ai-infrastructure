import os
import json
import csv
import re

print("Building Characterization Dashboard Data...")

# 1. Load single-node CSV data
runs_csv_path = "rtx_g4_smoke_v5/v6_suite/results/vllm_runs.csv"
single_node_runs = []
if os.path.exists(runs_csv_path):
    with open(runs_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            single_node_runs.append(row)
print(f"Loaded {len(single_node_runs)} single-node runs.")

# 2. Load multi-node data
multi_node_dir = "rtx_g4_smoke_v5/v6_suite/results/multi_node"
multi_node_runs = []
topologies = ["tp4_pp4_dist", "tp4_pp2_dist", "tp8_pp2_dist", "tp16_pp1_dist"]

for topo in topologies:
    t_dir = os.path.join(multi_node_dir, topo, topo)
    if not os.path.exists(t_dir):
        continue
    bench_dirs = [d for d in os.listdir(t_dir) if os.path.isdir(os.path.join(t_dir, d))]
    for bd in bench_dirs:
        j_file = os.path.join(t_dir, bd, f"{bd}.json")
        if os.path.exists(j_file):
            with open(j_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            multi_node_runs.append({
                "topology": topo,
                "bench": bd,
                "data": d
            })
print(f"Loaded {len(multi_node_runs)} multi-node runs.")

# Let's verify data points
print("Data check complete.")
