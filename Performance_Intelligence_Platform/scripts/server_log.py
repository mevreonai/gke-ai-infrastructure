#!/usr/bin/env python3
"""server_log: parse timestamped server.log and correlate with bench runs.

Features:
- Parses microsecond timestamped lines: "<timestamp> <line>"
- Extracts engine stats lines: running, waiting, swapped, KV usage
- Extracts iteration details: chunk sizes, active seqs, decode steps
- Detects compilation, CUDA graph capture, autotune, NCCL, and warning events
- Aligns bench requests to server log via clock pair:
    request_wall = start_time - clock_mono + clock_wall
- For any pause in the run, prints all log lines from 2s before to 1s after the pause
- Computes the longest time gap between consecutive iteration lines

Usage:
  python3 server_log.py <server.log> [--run run.json] [--manifest case_manifest.json] [--bench-name 8k_c4]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pip_waves as pw


TIMESTAMP_RE = re.compile(r"^(\d+\.\d{3,6})\s+(.*)$")
STATS_RE = re.compile(r"Avg prompt throughput:\s*([\d\.]+)\s*tokens/s.*Avg generation throughput:\s*([\d\.]+)\s*tokens/s.*Running:\s*(\d+)\s*reqs,\s*Swapped:\s*(\d+)\s*reqs,\s*Pending:\s*(\d+)\s*reqs,\s*GPU KV cache usage:\s*([\d\.]+)%", re.IGNORECASE)
KEYWORD_RE = re.compile(r"(compile|cuda\s*graph|autotune|nccl|warn|recompile|dynamo|triton)", re.IGNORECASE)


def parse_server_log(log_path: str):
    events = []
    stats_series = []
    iteration_lines = []
    diagnostics = []

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            m = TIMESTAMP_RE.match(line_str)
            if m:
                ts = float(m.group(1))
                content = m.group(2)
            else:
                ts = None
                content = line_str

            entry = {"ts": ts, "content": content}
            events.append(entry)

            # Check stats
            sm = STATS_RE.search(content)
            if sm and ts is not None:
                stats_series.append({
                    "ts": ts,
                    "prompt_tok_s": float(sm.group(1)),
                    "gen_tok_s": float(sm.group(2)),
                    "running": int(sm.group(3)),
                    "swapped": int(sm.group(4)),
                    "pending": int(sm.group(5)),
                    "kv_pct": float(sm.group(6)),
                })

            # Check iteration details
            if "iteration" in content.lower():
                if ts is not None:
                    iteration_lines.append((ts, content))

            # Check compilation / graph / autotune / NCCL / warning
            if KEYWORD_RE.search(content):
                diagnostics.append(entry)

    # Calculate longest gap between iteration lines
    longest_iter_gap_s = 0.0
    iter_gap_window = None
    for i in range(len(iteration_lines) - 1):
        gap = iteration_lines[i + 1][0] - iteration_lines[i][0]
        if gap > longest_iter_gap_s:
            longest_iter_gap_s = gap
            iter_gap_window = (iteration_lines[i][0], iteration_lines[i + 1][0])

    return {
        "events": events,
        "stats_series": stats_series,
        "iteration_count": len(iteration_lines),
        "longest_iter_gap_s": longest_iter_gap_s,
        "iter_gap_window": iter_gap_window,
        "diagnostics": diagnostics,
    }


def find_pause_window(run_path: str, manifest_path: str = None, bench_name: str = None):
    run_data = json.load(open(run_path))
    a = pw.analyze(run_path, with_engine=False)
    p = a.get("pause", {})
    if not p.get("is_pause"):
        return None, p

    # Find clock pair
    clock_wall = None
    clock_mono = None

    if manifest_path and os.path.exists(manifest_path):
        m = json.load(open(manifest_path))
        for b in m.get("benchmarks", []):
            if bench_name and b.get("name") != bench_name:
                continue
            clock_wall = b.get("clock_wall")
            clock_mono = b.get("clock_mono")
            if clock_wall and clock_mono:
                break

    if clock_wall is None or clock_mono is None:
        # Fallback to date or start_time if clock pair not present
        clock_wall = min(run_data["start_times"])
        clock_mono = min(run_data["start_times"])

    pause_at_run_s = p["at_s"]
    silence_s = p["silence_s"]
    first_req_start = min(run_data["start_times"])
    pause_wall_start = (first_req_start + pause_at_run_s) - clock_mono + clock_wall
    pause_wall_end = pause_wall_start + silence_s

    return (pause_wall_start, pause_wall_end), p


def inspect_log_around_pause(parsed_log, wall_start, wall_end):
    win_start = wall_start - 2.0
    win_end = wall_end + 1.0

    print(f"\n{'='*78}")
    print(f"PAUSE WINDOW AUDIT: [{win_start:.3f} s  -->  {win_end:.3f} s] (Pause: {wall_start:.3f} to {wall_end:.3f})")
    print(f"{'='*78}")

    lines_in_window = [e for e in parsed_log["events"] if e["ts"] is not None and win_start <= e["ts"] <= win_end]
    if not lines_in_window:
        print("No timestamped lines in log within this window.")
        return

    for e in lines_in_window:
        marker = ">>> PAUSE GAP >>>" if wall_start <= e["ts"] <= wall_end else "                 "
        print(f"[{e['ts']:.6f}] {marker} {e['content']}")
    print(f"{'='*78}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("server_log", help="Path to server.log")
    ap.add_argument("--run", help="Path to bench run.json")
    ap.add_argument("--manifest", help="Path to case_manifest.json")
    ap.add_argument("--bench-name", help="Bench case name")
    args = ap.parse_args()

    parsed = parse_server_log(args.server_log)
    print(f"Parsed {len(parsed['events'])} lines ({parsed['iteration_count']} iteration lines, {len(parsed['stats_series'])} stats snapshots)")
    if parsed["longest_iter_gap_s"] > 0:
        print(f"Longest gap between iteration lines: {parsed['longest_iter_gap_s']:.3f} s")
        if parsed["iter_gap_window"]:
            print(f"  Gap occurred from {parsed['iter_gap_window'][0]:.3f} to {parsed['iter_gap_window'][1]:.3f}")

    if args.run:
        window, p = find_pause_window(args.run, args.manifest, args.bench_name)
        if window:
            print(f"Detected PAUSE: {p['silence_s']:.2f}s silence at {p['at_s']:.2f}s ({p['ratio']:.1f} normal steps)")
            inspect_log_around_pause(parsed, window[0], window[1])
        else:
            print(f"No pause in run {args.run} (max silence {p.get('silence_s', 0):.2f}s = {p.get('ratio', 0):.1f} steps)")


if __name__ == "__main__":
    main()
