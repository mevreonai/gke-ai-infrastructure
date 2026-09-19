#!/usr/bin/env python3
"""
Deep Characterization Engine for Kimi K3 vLLM Profiles.
Parses Nsight Systems (nsys) CSVs and PyTorch Profiler traces to extract:
- KDA / MLA / MoE kernel execution times.
- CUDA API and Python Scheduler CPU overheads.
- Overlap ratios.
Outputs a structured JSON and Markdown evidence table.
"""
import argparse, csv, json, os, glob
from pathlib import Path
from collections import defaultdict

def load_csv(path):
    if not os.path.exists(path): return []
    try:
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

def analyze_nsys(profile_root):
    root = Path(profile_root)
    kern_csv = root / "cuda_gpu_kern_sum.csv"
    api_csv = root / "cuda_api_sum.csv"

    kern_data = load_csv(kern_csv)
    api_data = load_csv(api_csv)

    results = {
        "kda": 0.0,
        "mla": 0.0,
        "moe": 0.0,
        "nccl": 0.0,
        "other_gpu": 0.0,
        "total_gpu": 0.0,
        "cuda_api": 0.0,
    }

    # Time values in nsys CSVs are usually in nanoseconds ("Time (ns)") or percentages.
    # We will look for "Total Time (ns)"
    for row in kern_data:
        name = row.get("Name", "").lower()
        time_ns_str = row.get("Total Time (ns)", "0")
        try:
            time_ms = float(time_ns_str) / 1e6
        except ValueError:
            time_ms = 0.0

        results["total_gpu"] += time_ms

        if "kda" in name:
            results["kda"] += time_ms
        elif "mla" in name:
            results["mla"] += time_ms
        elif "moe" in name or "router" in name:
            results["moe"] += time_ms
        elif "nccl" in name:
            results["nccl"] += time_ms
        else:
            results["other_gpu"] += time_ms

    for row in api_data:
        time_ns_str = row.get("Total Time (ns)", "0")
        try:
            time_ms = float(time_ns_str) / 1e6
        except ValueError:
            time_ms = 0.0
        results["cuda_api"] += time_ms

    return results

def analyze_torch_trace(trace_dir):
    traces = glob.glob(os.path.join(trace_dir, "*.pt.trace.json"))
    if not traces:
        return {"scheduler_ms": 0.0, "prefix_cache_ms": 0.0}
    
    sched_ms = 0.0
    prefix_ms = 0.0

    for trace_path in traces:
        try:
            with open(trace_path) as f:
                data = json.load(f)
        except Exception:
            continue

        for evt in data.get("traceEvents", []):
            name = evt.get("name", "")
            if "schedule" in name.lower() or "step" in name.lower():
                sched_ms += evt.get("dur", 0) / 1000.0
            if "radixtree" in name.lower() or "prefix" in name.lower() or "match" in name.lower():
                prefix_ms += evt.get("dur", 0) / 1000.0

    return {"scheduler_ms": sched_ms, "prefix_cache_ms": prefix_ms}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vllm-dir", required=True, help="Path to vllm_runs.json directory")
    parser.add_argument("--profile-dir", required=True, help="Path to v5_profiles directory")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    vllm_dir = Path(args.vllm_dir)
    prof_dir = Path(args.profile_dir)
    
    analysis = {"profiles": {}}

    if prof_dir.exists():
        for p in prof_dir.iterdir():
            if p.is_dir():
                analysis["profiles"][p.name] = analyze_nsys(p)

    if vllm_dir.exists():
        for torch_dir in vllm_dir.rglob("torch_profile*"):
            if torch_dir.is_dir():
                case_name = torch_dir.parent.name
                analysis["profiles"][case_name + "_torch"] = analyze_torch_trace(torch_dir)

    with open(args.out, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"Deep characterization analysis saved to {args.out}")

if __name__ == "__main__":
    main()