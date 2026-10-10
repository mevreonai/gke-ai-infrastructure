#!/usr/bin/env python3
"""Stage 1 Analysis Tool (Fixed per Review C5):
1. Audits GPU KV pool sizes and block allocations from server.log and vllm:cache_config_info.
2. Trims closed-loop burst/drain intervals using the exact E2E C/D definition:
   - Sort requests by start_times.
   - Drop the first `concurrency` requests from first-token (TTFT) statistics (ramp-up).
   - Drop the last `concurrency` requests from decode token (ITL/TPOT) statistics (drain).
3. Evaluates peak GPU KV cache usage from `vllm:kv_cache_usage_perc`.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def extract_kv_pool_from_server_log(log_path: Path) -> Dict[str, Any]:
    if not log_path.exists():
        return {"error": f"server log not found at {log_path}"}
    info = {}
    pattern = re.compile(r"GPU KV cache size:\s*([\d,]+)\s*tokens,\s*Maximum concurrency for\s*([\d,]+)\s*tokens per request:\s*([\d.]+)x")
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                info["gpu_kv_cache_size_tokens"] = int(m.group(1).replace(",", ""))
                info["tokens_per_request_baseline"] = int(m.group(2).replace(",", ""))
                info["max_concurrency_1m"] = float(m.group(3))
                break
    return info

def extract_kv_metrics_from_jsonl(jsonl_path: Path) -> Dict[str, Any]:
    if not jsonl_path.exists():
        return {"error": f"metrics jsonl not found at {jsonl_path}"}
    info = {"peak_kv_cache_usage_perc": 0.0, "cache_config": None}
    with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip(): continue
            try:
                rec = json.loads(line)
                if rec.get("kind") == "prometheus":
                    for m in rec.get("metrics", []):
                        name = m.get("name")
                        val = m.get("value")
                        if name == "vllm:kv_cache_usage_perc" and val is not None:
                            if float(val) > info["peak_kv_cache_usage_perc"]:
                                info["peak_kv_cache_usage_perc"] = float(val)
                        elif name == "vllm:cache_config_info" and info["cache_config"] is None:
                            info["cache_config"] = m.get("labels", {})
            except Exception: pass
    return info

def calc_percentiles(vals: List[float]) -> Dict[str, Optional[float]]:
    if not vals:
        return {"p50": None, "p90": None, "p95": None, "p99": None}
    s = sorted(vals)
    n = len(s)
    return {
        "p50": s[int(n * 0.50)],
        "p90": s[min(int(n * 0.90), n - 1)],
        "p95": s[min(int(n * 0.95), n - 1)],
        "p99": s[min(int(n * 0.99), n - 1)],
    }

def trim_benchmark_trace(bench_json_path: Path) -> Dict[str, Any]:
    if not bench_json_path.exists():
        return {"error": f"bench json not found at {bench_json_path}"}
    try:
        data = json.loads(bench_json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": str(e)}

    start_times = data.get("start_times", [])
    ttfts = data.get("ttfts", [])
    itls = data.get("itls", [])
    concurrency = int(data.get("max_concurrency") or 1)
    num_requests = len(start_times)

    if num_requests == 0 or len(ttfts) != num_requests:
        return {"error": "mismatched or empty trace arrays"}

    # Pair requests with their start time to sort chronologically
    paired = []
    for i in range(num_requests):
        paired.append({
            "start": start_times[i],
            "ttft": ttfts[i],
            "itls": itls[i] if i < len(itls) else []
        })
    paired.sort(key=lambda x: x["start"])

    # 1. First-token statistics: drop first `concurrency` requests (ramp-up burst)
    ttft_sample = paired[concurrency:] if num_requests > concurrency else paired
    valid_ttfts = [r["ttft"] for r in ttft_sample if r["ttft"] is not None]

    # 2. Token statistics: drop last `concurrency` requests (drain phase)
    token_sample = paired[:-concurrency] if num_requests > concurrency else paired
    flat_itls = []
    for r in token_sample:
        for itl in r.get("itls", []):
            if itl is not None: flat_itls.append(itl)

    # Flatten untrimmed for baseline comparison
    raw_ttfts = [r["ttft"] for r in paired if r["ttft"] is not None]
    raw_itls = [itl for r in paired for itl in r.get("itls", []) if itl is not None]

    wave1_ttfts = [r["ttft"] for r in paired[:concurrency] if r["ttft"] is not None]
    
    def mean(lst): return (sum(lst) / len(lst)) if lst else None

    return {
        "benchmark_name": data.get("bench"),
        "total_requests": num_requests,
        "concurrency": concurrency,
        "wave1_request_count": len(wave1_ttfts),
        "steady_state_request_count": len(valid_ttfts),
        "trimmed_first_token_requests": len(valid_ttfts),
        "trimmed_drain_requests": len(token_sample),
        "raw_untrimmed_ttft_mean_s": mean(raw_ttfts),
        "wave1_burst_ttft_mean_s": mean(wave1_ttfts),
        "steady_state_ttft_mean_s": mean(valid_ttfts),
        "raw_untrimmed_itl_mean_ms": (mean(raw_itls) * 1000.0) if mean(raw_itls) else None,
        "steady_state_itl_mean_ms": (mean(flat_itls) * 1000.0) if mean(flat_itls) else None,
        "raw_ttft_percentiles_s": calc_percentiles(raw_ttfts),
        "wave1_burst_ttft_percentiles_s": calc_percentiles(wave1_ttfts),
        "steady_state_ttft_percentiles_s": calc_percentiles(valid_ttfts),
        "raw_itl_percentiles_s": calc_percentiles(raw_itls),
        "steady_state_itl_percentiles_s": calc_percentiles(flat_itls),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server-log", help="Path to server.log")
    ap.add_argument("--metrics", help="Path to metrics_gpu.jsonl")
    ap.add_argument("--bench", help="Path to benchmark JSON (e.g. 8k_c4.json)")
    ap.add_argument("--scan-dir", help="Directory to scan recursively for closed-loop runs")
    ap.add_argument("--out", required=True, help="Output JSON path")
    args = ap.parse_args()

    result = {}
    if args.server_log:
        result["server_kv_pool"] = extract_kv_pool_from_server_log(Path(args.server_log))
    if args.metrics:
        result["metrics_kv_audit"] = extract_kv_metrics_from_jsonl(Path(args.metrics))
    if args.bench:
        result["steady_state_trace"] = trim_benchmark_trace(Path(args.bench))

    if args.scan_dir:
        scanned = {}
        for p in Path(args.scan_dir).rglob("*.json"):
            if p.name in ("summary.json", "resolved_models.json", "manifest.json"): continue
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if "ttfts" in d and "start_times" in d:
                    scanned[str(p)] = trim_benchmark_trace(p)
            except Exception: pass
        result["scanned_closedloop_runs"] = scanned

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"KV audit and trace analysis successfully written to {out_path}")

if __name__ == "__main__":
    main()
