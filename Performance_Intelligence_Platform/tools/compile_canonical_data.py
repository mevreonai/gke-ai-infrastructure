#!/usr/bin/env python3
import os
import sys
import json
import glob
import pandas as pd
import numpy as np

def build_canonical_dataset(run_dir=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_json = os.path.join(base_dir, "dashboard", "DASHBOARD_CANONICAL_DATA.json")
    
    csv_path = None
    if run_dir and os.path.exists(run_dir):
        run_csvs = glob.glob(os.path.join(run_dir, "**", "*.csv"), recursive=True)
        if run_csvs:
            csv_path = run_csvs[0]
            
    if not csv_path:
        csv_path = os.path.join(base_dir, "data", "results", "real_data", "combined_vllm_runs.csv")
    
    if not os.path.exists(csv_path):
        # Fall back to any csv found in results
        csv_candidates = glob.glob(os.path.join(base_dir, "data", "results", "**", "*.csv"), recursive=True)
        if csv_candidates:
            csv_path = csv_candidates[0]
        else:
            print(f"WARN: Empirical CSV file not found at {csv_path}. Creating stub structure.", file=sys.stderr)
            os.makedirs(os.path.dirname(out_json), exist_ok=True)
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump({"schema_version": "Enterprise-Platform", "status": "PENDING_BENCHMARK_EXECUTION"}, f, indent=2)
            return
        
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} empirical benchmark records across {df.get('step_id', pd.Series()).nunique()} steps.")
    
    # 1. Executive Summary Rollups
    total_campaign_wall_time = float(df['duration_seconds'].sum()) if 'duration_seconds' in df.columns else 0.0
    total_requests_served = int(df['num_total_requests'].sum()) if 'num_total_requests' in df.columns else 0
    peak_throughput_tps = float(df['token_throughput_tps'].max()) if 'token_throughput_tps' in df.columns else 0.0
    lowest_p99_itl_ms = float(df['itl_p99_ms'].min()) if 'itl_p99_ms' in df.columns else 0.0
    
    # 2. Per-Step Statistical Groupings
    step_summaries = {}
    if "step_id" in df.columns:
        for step_id, group in df.groupby("step_id"):
            step_summaries[str(step_id)] = {
                "step_name": str(step_id),
                "total_runs": len(group),
                "mean_rps": float(group["request_throughput_rps"].mean()) if "request_throughput_rps" in group else 0.0,
                "mean_tps": float(group["token_throughput_tps"].mean()) if "token_throughput_tps" in group else 0.0,
                "ttft_p50_ms": float(group["ttft_median_ms"].mean()) if "ttft_median_ms" in group else 0.0,
                "ttft_p90_ms": float(group["ttft_p90_ms"].mean()) if "ttft_p90_ms" in group else 0.0,
                "ttft_p99_ms": float(group["ttft_p99_ms"].mean()) if "ttft_p99_ms" in group else 0.0,
                "itl_p50_ms": float(group["itl_median_ms"].mean()) if "itl_median_ms" in group else 0.0,
                "itl_p90_ms": float(group["itl_p90_ms"].mean()) if "itl_p90_ms" in group else 0.0,
                "itl_p99_ms": float(group["itl_p99_ms"].mean()) if "itl_p99_ms" in group else 0.0,
                "e2e_p99_ms": float(group["e2e_latency_p99_ms"].mean()) if "e2e_latency_p99_ms" in group else 0.0,
                "gpu_memory_peak_gib": float(group["gpu_memory_peak_gib"].max()) if "gpu_memory_peak_gib" in group else 0.0,
                "gpu_utilization_mean": float(group["gpu_utilization_mean"].mean()) if "gpu_utilization_mean" in group else 0.0
            }
        
    # 3. Canonical Schema Construction
    canonical_payload = {
        "schema_version": "Enterprise-Platform",
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "executive_kpis": {
            "total_campaign_wall_time_seconds": total_campaign_wall_time,
            "total_campaign_wall_time_hours": round(total_campaign_wall_time / 3600.0, 2),
            "total_requests_evaluated": total_requests_served,
            "peak_token_throughput_tps": peak_throughput_tps,
            "lowest_p99_itl_ms": lowest_p99_itl_ms,
            "cluster_gpus_active": 16,
            "total_cluster_vram_gib": 1536
        },
        "step_summaries": step_summaries,
        "raw_records": df.to_dict(orient="records")
    }
    
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(canonical_payload, f, indent=2)
    if run_dir and os.path.exists(run_dir):
        run_out = os.path.join(run_dir, "DASHBOARD_CANONICAL_DATA.json")
        with open(run_out, "w", encoding="utf-8") as f:
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
