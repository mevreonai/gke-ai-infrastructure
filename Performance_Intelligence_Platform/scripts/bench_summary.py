#!/usr/bin/env python3
"""bench_summary: summary aggregator with pause, burst, and stall indicators.

Prints run summary with flags:
- PAUSE x s at t s (n normal steps; run k on its server)
- BURST p% of waiting; steady wait w s
- STALLED q% of answering
- Max token gap (from detailed itls or p100)

Usage:
  python3 bench_summary.py <run.json or directory> [--budget 8192] [--csv out.csv]
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pip_scan
import pip_waves as pw


def summarize_file(path: str, budget: int = 8192, rank_in_session: int = 0) -> dict:
    d = json.load(open(path))
    if not isinstance(d, dict) or "ttfts" not in d or "itls" not in d:
        return {}
    
    a = pw.analyze(path, budget=budget, with_engine=False)
    p = a.get("pause", {})
    b = a.get("burst", {})
    s = a.get("stalls", {})
    
    # Calculate max token gap from itls
    itls = [g for sublist in d.get("itls", []) for g in sublist]
    max_token_gap_ms = (max(itls) * 1000) if itls else (d.get("p100_itl_ms") or d.get("p99_itl_ms") or 0.0)

    res = {
        "path": path,
        "n": a["n"],
        "C": a["C"],
        "input_len": a["input_len"],
        "output_len": a["output_len"],
        "mean_ttft_ms": d.get("mean_ttft_ms"),
        "mean_tpot_ms": d.get("mean_tpot_ms"),
        "max_token_gap_ms": max_token_gap_ms,
        "is_pause": p.get("is_pause", False),
        "silence_s": p.get("silence_s", 0.0),
        "pause_at_s": p.get("at_s", 0.0),
        "pause_ratio_steps": p.get("ratio", 0.0),
        "rank_in_session": rank_in_session,
        "burst_share": b.get("burst_share_of_waiting"),
        "steady_wait_s": b.get("later_mean_s"),
        "stall_share": s.get("stall_share", 0.0),
    }

    # Format flags
    flags = []
    if res["is_pause"]:
        flags.append(f"PAUSE {res['silence_s']:.2f} s at {res['pause_at_s']:.2f} s ({res['pause_ratio_steps']:.1f} normal steps; run {rank_in_session + 1} on server)")
    if res["burst_share"] is not None:
        steady_str = f"{res['steady_wait_s']:.3f} s" if res["steady_wait_s"] is not None else "N/A"
        flags.append(f"BURST {100 * res['burst_share']:.1f}% of waiting; steady wait {steady_str}")
    if res["stall_share"] > 0:
        flags.append(f"STALLED {100 * res['stall_share']:.1f}% of answering")
    flags.append(f"MAX_GAP {res['max_token_gap_ms']:.1f} ms")

    res["flags"] = " | ".join(flags)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target", help="Path to run.json or directory of runs")
    ap.add_argument("--budget", type=int, default=8192, help="Server max_num_batched_tokens")
    ap.add_argument("--csv", help="Optional CSV output file")
    args = ap.parse_args()

    files = []
    if os.path.isfile(args.target):
        files = [args.target]
    else:
        for root, _, filenames in os.walk(args.target):
            for fn in filenames:
                if fn.endswith(".json") and "manifest" not in fn and "warmup" not in fn:
                    files.append(os.path.join(root, fn))

    rows = []
    for f in sorted(files):
        try:
            r = summarize_file(f, budget=args.budget)
            if r:
                rows.append(r)
                print(f"[{os.path.basename(f)}] C={r['C']} ISL={r['input_len']} TTFT={r['mean_ttft_ms'] or 0:.1f}ms")
                print(f"  --> {r['flags']}")
        except Exception as e:
            pass

    if args.csv and rows:
        with open(args.csv, "w", newline="") as cf:
            w = csv.DictWriter(cf, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {args.csv}")


if __name__ == "__main__":
    main()
