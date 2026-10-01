#!/usr/bin/env python3
import argparse, json, os, subprocess, sys, time
from pathlib import Path

# Add v9_core to path
sys.path.insert(0, "/home/ayu23/V9_FULL/v9_core")
from config import load_json, normalize_cluster
from cluster import start_ray, stop_ray

def main():
    case_name = sys.argv[1] if len(sys.argv) > 1 else "tp8_pp2_dist"
    mode = sys.argv[2] if len(sys.argv) > 2 else "native"
    
    model_profile_path = "/home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/MODEL_PROFILE.json"
    matrix_path = "/home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/V9_MATRIX.json"
    cluster_path = "/home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/CLUSTER_CONFIG.json"
    out_root = Path("/home/ayu23/v9_full_results/v9_full_production_20260930_143117/vllm_scaleout_network_matrix/NETWORK_NATIVE/results").resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    profile, _ = load_json(model_profile_path)
    matrix, _ = load_json(matrix_path)
    cluster, _ = load_json(cluster_path)
    cluster = normalize_cluster(cluster)

    matching_cases = [c for c in matrix['scaleout_cases'] if c['name'] == case_name]
    if not matching_cases:
        print(f"Error: case {case_name} not found in matrix")
        sys.exit(1)
    case = matching_cases[0]

    nodes = cluster['nodes'][:int(case['nodes_required'])]
    print(f"=== Starting case {case_name}: TP={case['tp']}, PP={case['pp']}, Nodes={len(nodes)}, ray_gpus={case['ray_gpus_per_node']} ===")
    
    stop_ray(cluster, nodes)
    time.sleep(2)
    start_ray(cluster, nodes, int(case['ray_gpus_per_node']), extra_env=profile.get('server_env') or {})

    cmd = [
        "/home/ayu23/vllm_env/bin/python3",
        "/home/ayu23/V9_FULL/v9_core/run_multi.py",
        "--model-profile", model_profile_path,
        "--matrix", matrix_path,
        "--cluster", cluster_path,
        "--out", str(out_root),
        "--case", case_name,
        "--network-mode", mode
    ]
    print("+ " + " ".join(cmd))
    p = subprocess.run(cmd)
    print(f"Case {case_name} exited with code {p.returncode}")
    stop_ray(cluster, nodes)
    sys.exit(p.returncode)

if __name__ == "__main__":
    main()
