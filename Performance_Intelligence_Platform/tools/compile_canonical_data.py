#!/usr/bin/env python3
import os
import sys
import json
import glob
import pandas as pd
import numpy as np
import re

def build_canonical_dataset(run_dir=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # N21: Determine target output location. If run_dir given, write into run_dir only.
    if run_dir and os.path.exists(run_dir):
        out_json = os.path.join(run_dir, "DASHBOARD_CANONICAL_DATA.json")
    else:
        out_json = os.path.join(base_dir, "dashboard", "DASHBOARD_CANONICAL_DATA.json")

    dfs = []
    if run_dir and os.path.exists(run_dir):
        # N21: Discover and join every step's summary/vllm_runs.csv, skipping empty ones
        candidate_csvs = glob.glob(os.path.join(run_dir, "**", "vllm_runs.csv"), recursive=True)
        if not candidate_csvs:
            candidate_csvs = glob.glob(os.path.join(run_dir, "**", "*.csv"), recursive=True)
            
        for cp in sorted(candidate_csvs):
            if os.path.exists(cp) and os.path.getsize(cp) > 0:
                try:
                    cdf = pd.read_csv(cp)
                    if not cdf.empty:
                        # Extract step identifier from path if not present in CSV
                        if "step_id" not in cdf.columns:
                            m = re.search(r'(step\d+[^/\\\s]*)', cp, re.I)
                            if m:
                                cdf["step_id"] = m.group(1)
                            elif "case" in cdf.columns:
                                cdf["step_id"] = cdf["case"]
                        dfs.append(cdf)
                except Exception as e:
                    print(f"DEBUG: Skipping unparseable or empty CSV {cp}: {e}", file=sys.stderr)

    if not dfs:
        # Fallback to repository empirical results
        default_csv = os.path.join(base_dir, "data", "results", "real_data", "combined_vllm_runs.csv")
        if os.path.exists(default_csv) and os.path.getsize(default_csv) > 0:
            try:
                cdf = pd.read_csv(default_csv)
                if not cdf.empty:
                    dfs.append(cdf)
            except Exception:
                pass

    if not dfs:
        # Search anywhere under data/results
        res_csvs = glob.glob(os.path.join(base_dir, "data", "results", "**", "vllm_runs.csv"), recursive=True)
        for cp in sorted(res_csvs):
            if os.path.exists(cp) and os.path.getsize(cp) > 0:
                try:
                    cdf = pd.read_csv(cp)
                    if not cdf.empty:
                        dfs.append(cdf)
                        break
                except Exception:
                    pass

    if not dfs:
        print(f"WARN: No empirical CSV data found. Writing baseline placeholder to {out_json}.", file=sys.stderr)
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({
                "schema_version": "Enterprise-Platform",
                "status": "PENDING_BENCHMARK_EXECUTION",
                "executive_kpis": {
                    "total_campaign_wall_time_seconds": 0.0,
                    "total_campaign_wall_time_hours": 0.0,
                    "total_requests_evaluated": 0,
                    "peak_token_throughput_tps": 0.0,
                    "lowest_p99_itl_ms": 0.0,
                    "cluster_gpus_active": 16,
                    "total_cluster_vram_gib": 1536
                },
                "step_summaries": {},
                "raw_records": []
            }, f, indent=2)
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(df)} empirical benchmark records across {df.get('step_id', pd.Series()).nunique()} steps.")

    # N21: Read summarizer's actual column names (mean_ttft_ms, mean_tpot_ms, output_throughput, duration, completed)
    duration_col = 'duration' if 'duration' in df.columns else ('duration_seconds' if 'duration_seconds' in df.columns else None)
    reqs_col = 'completed' if 'completed' in df.columns else ('prompts_requested' if 'prompts_requested' in df.columns else ('num_total_requests' if 'num_total_requests' in df.columns else None))
    tps_col = 'output_throughput' if 'output_throughput' in df.columns else ('total_token_throughput' if 'total_token_throughput' in df.columns else ('token_throughput_tps' if 'token_throughput_tps' in df.columns else None))
    rps_col = 'request_throughput' if 'request_throughput' in df.columns else ('request_throughput_rps' if 'request_throughput_rps' in df.columns else None)
    
    total_campaign_wall_time = float(df[duration_col].sum()) if duration_col and pd.api.types.is_numeric_dtype(df[duration_col]) else 0.0
    total_requests_served = int(df[reqs_col].sum()) if reqs_col and pd.api.types.is_numeric_dtype(df[reqs_col]) else 0
    peak_throughput_tps = float(df[tps_col].max()) if tps_col and pd.api.types.is_numeric_dtype(df[tps_col]) else 0.0
    
    itl_col = 'p99_tpot_ms' if 'p99_tpot_ms' in df.columns else ('p99_itl_ms' if 'p99_itl_ms' in df.columns else ('mean_itl_ms' if 'mean_itl_ms' in df.columns else ('itl_p99_ms' if 'itl_p99_ms' in df.columns else None)))
    lowest_p99_itl_ms = float(df[itl_col].min()) if itl_col and pd.api.types.is_numeric_dtype(df[itl_col]) else 0.0

    # N21: Dynamically determine active GPUs from step 0 environment or default
    active_gpus = 16
    if run_dir and os.path.exists(run_dir):
        readiness_file = os.path.join(run_dir, "env", "node0_readiness", "PLATFORM_READINESS.md")
        if os.path.exists(readiness_file):
            try:
                rtext = open(readiness_file, encoding="utf-8", errors="ignore").read()
                gm = re.search(r'(\d+)\s+total\s+GPUs', rtext, re.I)
                if gm:
                    active_gpus = int(gm.group(1))
            except Exception:
                pass

    # 2. Per-Step Statistical Groupings
    step_summaries = {}
    group_col = "step_id" if "step_id" in df.columns else ("case" if "case" in df.columns else None)
    if group_col:
        for step_id, group in df.groupby(group_col):
            step_summaries[str(step_id)] = {
                "step_name": str(step_id),
                "total_runs": len(group),
                "mean_rps": float(group[rps_col].mean()) if rps_col and rps_col in group else 0.0,
                "mean_tps": float(group[tps_col].mean()) if tps_col and tps_col in group else 0.0,
                "ttft_p50_ms": float(group["p50_ttft_ms"].mean()) if "p50_ttft_ms" in group else (float(group["mean_ttft_ms"].mean()) if "mean_ttft_ms" in group else 0.0),
                "ttft_p90_ms": float(group["p95_ttft_ms"].mean()) if "p95_ttft_ms" in group else 0.0,
                "ttft_p99_ms": float(group["p99_ttft_ms"].mean()) if "p99_ttft_ms" in group else 0.0,
                "itl_p50_ms": float(group["p50_tpot_ms"].mean()) if "p50_tpot_ms" in group else (float(group["mean_itl_ms"].mean()) if "mean_itl_ms" in group else 0.0),
                "itl_p90_ms": float(group["p95_tpot_ms"].mean()) if "p95_tpot_ms" in group else 0.0,
                "itl_p99_ms": float(group["p99_tpot_ms"].mean()) if "p99_tpot_ms" in group else 0.0,
                "e2e_p99_ms": float(group["mean_e2el_ms"].mean()) if "mean_e2el_ms" in group else 0.0,
                "gpu_memory_peak_gib": float(group["offload_gib_total"].max()) if "offload_gib_total" in group else 0.0,
                "gpu_utilization_mean": 0.0
            }

    canonical_payload = {
        "schema_version": "Enterprise-Platform",
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "executive_kpis": {
            "total_campaign_wall_time_seconds": total_campaign_wall_time,
            "total_campaign_wall_time_hours": round(total_campaign_wall_time / 3600.0, 2),
            "total_requests_evaluated": total_requests_served,
            "peak_token_throughput_tps": peak_throughput_tps,
            "lowest_p99_itl_ms": lowest_p99_itl_ms,
            "cluster_gpus_active": active_gpus,
            "total_cluster_vram_gib": active_gpus * 96
        },
        "step_summaries": step_summaries,
        "raw_records": df.to_dict(orient="records")
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(canonical_payload, f, indent=2)

    print(f"Successfully compiled canonical dataset to {out_json} ({os.path.getsize(out_json)} bytes).")

if __name__ == "__main__":
    target_dir = None
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--run-dir="):
            target_dir = sys.argv[1].split("=", 1)[1]
        elif sys.argv[1] == "--run-dir" and len(sys.argv) > 2:
            target_dir = sys.argv[2]
        else:
            target_dir = sys.argv[1]
    build_canonical_dataset(target_dir)
