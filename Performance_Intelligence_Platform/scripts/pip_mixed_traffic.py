#!/usr/bin/env python3
"""pip_mixed_traffic: analyze mixed traffic concurrent streams (short + long).

Reads two concurrent vllm bench serve runs aligned by clock pairs:
  1. Short stream (e.g. 1K prompts, 128-token answers)
  2. Long stream (e.g. 128K / 512K prompts)

Splits short requests into:
  - Arrived during an active long prefill
  - Arrived when no long prefill was active

Computes:
  - TTFT / first-token wait penalty under long prefill vs idle
  - Stall share during long prefill vs idle
  - Fraction of short requests arriving during long reads
  - Long prompt prefill duration dilation

Usage:
  python3 pip_mixed_traffic.py --short short_run.json --long long_run.json [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pip_waves as pw


def extract_prefill_intervals(long_data: dict, clock_wall: float = 0.0, clock_mono: float = 0.0) -> list:
    n = len(long_data["start_times"])
    intervals = []
    for i in range(n):
        s_mono = long_data["start_times"][i]
        ttft = long_data["ttfts"][i]
        # Wall start and end of prefill:
        start_wall = s_mono - clock_mono + clock_wall
        first_tok_wall = start_wall + ttft
        intervals.append((start_wall, first_tok_wall))
    return intervals


def is_during_long_prefill(t_wall: float, intervals: list) -> bool:
    return any(start <= t_wall <= end for start, end in intervals)


def analyze_mixed(short_path: str, long_path: str, short_meta: dict = None, long_meta: dict = None) -> dict:
    s_raw = json.load(open(short_path))
    l_raw = json.load(open(long_path))

    # Retrieve clock pairs
    s_wall = (short_meta or {}).get("clock_wall", min(s_raw["start_times"]))
    s_mono = (short_meta or {}).get("clock_mono", min(s_raw["start_times"]))
    l_wall = (long_meta or {}).get("clock_wall", min(l_raw["start_times"]))
    l_mono = (long_meta or {}).get("clock_mono", min(l_raw["start_times"]))

    long_intervals = extract_prefill_intervals(l_raw, l_wall, l_mono)

    short_during_long_ttfts = []
    short_idle_ttfts = []
    short_during_stalls = []
    short_idle_stalls = []

    s_n = len(s_raw["start_times"])
    for i in range(s_n):
        t_req_wall = s_raw["start_times"][i] - s_mono + s_wall
        ttft_s = s_raw["ttfts"][i]
        itls = s_raw["itls"][i]
        stall_time = sum(g for g in itls if g > 0.100)

        during = is_during_long_prefill(t_req_wall, long_intervals)
        if during:
            short_during_long_ttfts.append(ttft_s)
            short_during_stalls.append(stall_time)
        else:
            short_idle_ttfts.append(ttft_s)
            short_idle_stalls.append(stall_time)

    fraction_colliding = len(short_during_long_ttfts) / s_n if s_n > 0 else 0.0

    return {
        "short_requests_total": s_n,
        "long_requests_total": len(l_raw["start_times"]),
        "fraction_arriving_during_long_read": fraction_colliding,
        "short_colliding_count": len(short_during_long_ttfts),
        "short_idle_count": len(short_idle_ttfts),
        "ttft_mean_during_long_s": st.mean(short_during_long_ttfts) if short_during_long_ttfts else None,
        "ttft_mean_idle_s": st.mean(short_idle_ttfts) if short_idle_ttfts else None,
        "ttft_penalty_factor": (st.mean(short_during_long_ttfts) / st.mean(short_idle_ttfts)) if (short_during_long_ttfts and short_idle_ttfts and st.mean(short_idle_ttfts) > 0) else None,
        "stall_mean_during_long_s": st.mean(short_during_stalls) if short_during_stalls else 0.0,
        "stall_mean_idle_s": st.mean(short_idle_stalls) if short_idle_stalls else 0.0,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--short", required=True, help="Path to short stream result JSON")
    ap.add_argument("--long", required=True, help="Path to long stream result JSON")
    ap.add_argument("--json", help="Path to save output JSON")
    args = ap.parse_args()

    res = analyze_mixed(args.short, args.long)
    print(f"\nMixed Traffic Stream Analysis:")
    print(f"  Short Requests Total    : {res['short_requests_total']}")
    print(f"  Long Requests Total     : {res['long_requests_total']}")
    print(f"  Arrived During Long Read: {100 * res['fraction_arriving_during_long_read']:.1f}% ({res['short_colliding_count']} of {res['short_requests_total']})")
    if res["ttft_mean_during_long_s"] is not None:
        print(f"  Short TTFT (Colliding)  : {res['ttft_mean_during_long_s'] * 1000:.1f} ms")
    if res["ttft_mean_idle_s"] is not None:
        print(f"  Short TTFT (Idle)       : {res['ttft_mean_idle_s'] * 1000:.1f} ms")
    if res["ttft_penalty_factor"] is not None:
        print(f"  Collision Penalty       : {res['ttft_penalty_factor']:.2f}x slower TTFT")
    print(f"  Stall Time (Colliding)  : {res['stall_mean_during_long_s'] * 1000:.1f} ms")
    print(f"  Stall Time (Idle)       : {res['stall_mean_idle_s'] * 1000:.1f} ms\n")

    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=2)


if __name__ == "__main__":
    main()
