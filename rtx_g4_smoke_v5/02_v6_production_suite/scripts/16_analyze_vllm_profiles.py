#!/usr/bin/env python3
"""Conservative profile analyzer.
Does NOT label substring-based kernel groups as exact semantic attribution and does NOT sum GPU work as wall-clock critical path.
"""
from __future__ import annotations
import argparse, csv, json, os, glob
from pathlib import Path

def load_csv(path):
    if not Path(path).exists(): return []
    try:
        with open(path,newline='') as f: return list(csv.DictReader(f))
    except Exception: return []

def ns_to_ms(v):
    try: return float(v)/1e6
    except Exception: return 0.0

def analyze_nsys(root):
    root=Path(root); kernels=load_csv(root/"cuda_gpu_kern_sum.csv"); apis=load_csv(root/"cuda_api_sum.csv"); nvtx=load_csv(root/"nvtx_pushpop_sum.csv")
    groups={k:{"aggregate_gpu_work_ms":0.0,"calls":0,"examples":[]} for k in ("kda_name_heuristic","mla_name_heuristic","moe_name_heuristic","nccl_name_heuristic","other")}
    total=0.0
    for r in kernels:
        name=(r.get("Name") or "").strip(); low=name.lower(); t=ns_to_ms(r.get("Total Time (ns)",0)); total+=t
        if "kda" in low: g="kda_name_heuristic"
        elif "mla" in low: g="mla_name_heuristic"
        elif "moe" in low or "router" in low or "grouped_gemm" in low: g="moe_name_heuristic"
        elif "nccl" in low: g="nccl_name_heuristic"
        else: g="other"
        groups[g]["aggregate_gpu_work_ms"]+=t
        try: groups[g]["calls"]+=int(float(r.get("Instances",r.get("Calls",1)) or 1))
        except Exception: groups[g]["calls"]+=1
        if name and len(groups[g]["examples"])<8: groups[g]["examples"].append(name)
    cuda_api=sum(ns_to_ms(r.get("Total Time (ns)",0)) for r in apis)
    return {
      "profile_dir":str(root),"kernel_csv_present":bool(kernels),"nvtx_csv_present":bool(nvtx),
      "aggregate_gpu_work_ms":total,"cuda_api_aggregate_ms":cuda_api,"name_heuristic_groups":groups,
      "semantic_attribution_status":"HEURISTIC_ONLY unless correlated with layerwise NVTX ranges",
      "critical_path_warning":"aggregate_gpu_work_ms sums GPU kernel work across devices/streams and is NOT wall-clock critical-path time",
      "nsys_rep_present":bool(list(root.glob("*.nsys-rep"))),"sqlite_present":bool(list(root.glob("*.sqlite")))
    }

def torch_profile_inventory(root):
    files=list(Path(root).rglob("*.pt.trace.json"))+list(Path(root).rglob("*.pt.trace.json.gz"))
    return {"trace_count":len(files),"files":[str(x) for x in files[:50]],
            "scheduler_attribution":"NOT_AUTOMATICALLY_SUMMED; generic 'step/schedule' substring accounting was intentionally removed because it double-counts nested/unrelated ranges."}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--profile-dir",required=True); ap.add_argument("--torch-dir",default=None); ap.add_argument("--out",required=True); args=ap.parse_args()
    root=Path(args.profile_dir); profiles={}
    candidates=[root] if (root/"cuda_gpu_kern_sum.csv").exists() else [p for p in root.iterdir() if p.is_dir()] if root.exists() else []
    for p in candidates: profiles[p.name]=analyze_nsys(p)
    out={"profiles":profiles,"torch_profiles":torch_profile_inventory(args.torch_dir) if args.torch_dir else None,
         "evidence_guardrail":"KDA/MLA/MoE name groups are heuristic. Exact attribution requires NVTX/timeline correlation. 48B absolute times do not transfer to K3."}
    Path(args.out).write_text(json.dumps(out,indent=2)); print(f"Wrote {args.out}")
if __name__=="__main__": main()
