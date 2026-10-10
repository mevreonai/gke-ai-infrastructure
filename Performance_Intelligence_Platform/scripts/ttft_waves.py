#!/usr/bin/env python3
"""ttft_waves: wave decomposition and first-wave analysis for vllm bench serve runs.

Prints:
- The first wave in reads
- The first-wave mean against the one-at-a-time rule: (C+1)/2
- The spacing between consecutive reads ("a prompt every X reads")
- The later mean in reads
- The burst's share of all waiting for first tokens
- First-wave prompts per step

Usage:
  python3 ttft_waves.py <run.json> [--budget 8192] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pip_waves as pw


def format_waves(a: dict) -> str:
    lines = []
    lines.append(f"Run: {a['path']}")
    lines.append(f"Requests: n={a['n']} C={a['C']} ISL={a['input_len']} OSL={a['output_len']} failed={a['failed']}")
    if not a.get("file_order_is_send_order", True):
        lines.append("WARNING: file order differs from send order")
    
    if "waves" in a and a["waves"]:
        w = a["waves"]
        b = a.get("burst", {})
        fw_reads_str = " ".join(f"{x:.2f}" for x in w["first_wave_reads"])
        lines.append(f"First wave (reads): lone read R={w['lone_read_s']:.3f} s; [{fw_reads_str}]")
        lines.append(f"First-wave mean: {w['first_wave_mean_reads']:.2f} reads (one-at-a-time predicted: {w['one_at_a_time_mean']:.1f})")
        if w.get("step_reads") is not None:
            lines.append(f"Spacing: a prompt every {w['step_reads']:.2f} reads")
        if w.get("later_mean_reads") is not None:
            lines.append(f"Later requests: {w['later_mean_reads']:.2f} reads on average")
        if "burst_share_of_waiting" in b:
            lines.append(f"Burst share: the opening burst is {100 * b['burst_share_of_waiting']:.1f}% of all waiting")
        if "prompts_per_step" in a:
            lines.append("First-wave prompts per step: " + " ".join(map(str, a["prompts_per_step"])))
    else:
        lines.append("Single concurrency or open-loop run: waves decomposition not applicable.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run", help="Path to vllm bench serve result JSON")
    ap.add_argument("--budget", type=int, default=8192, help="Server max_num_batched_tokens")
    ap.add_argument("--json", help="Save output dictionary as JSON")
    args = ap.parse_args()

    a = pw.analyze(args.run, budget=args.budget, with_engine=False)
    print(format_waves(a))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(a, f, indent=2)


if __name__ == "__main__":
    main()
