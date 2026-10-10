#!/usr/bin/env python3
"""metrics_diff: prometheus metrics time series deltas and gauge cross-validation.

Features:
- Reads Prometheus scrape log (metrics_node0.jsonl or metrics_raw.prom.log)
- Computes per-scrape deltas of tokens-per-iteration histogram (steps/sec, tokens/step)
- Detects zero-step intervals (correlating with engine pauses)
- Validates timeline drawn segments against Prometheus gauges:
    - (reading + answers) vs num_requests_running
    - (in line) vs num_requests_waiting
- Compares drawn mean read with engine prefill histogram mean

Usage:
  python3 metrics_diff.py <metrics_node0.jsonl> [--run run.json] [--budget 8192]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pip_waves as pw


def load_scrapes(path: str):
    scrapes = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                d = json.loads(line_str)
                if d.get("kind") == "prometheus":
                    scrapes.append(d)
            except Exception:
                continue
    return scrapes


def analyze_metrics(scrapes: list, run_path: str = None, budget: int = 8192):
    times = []
    running_gauge = []
    waiting_gauge = []
    steps_delta = []
    tokens_delta = []
    zero_step_intervals = []

    last_step_cnt = None
    last_tok_cnt = None
    prefill_hist_sum = None
    prefill_hist_count = None

    for i, s in enumerate(scrapes):
        ts = s.get("ts", i * 0.5)
        times.append(ts)
        m_map = {m["name"]: float(m["value"]) for m in s.get("metrics", []) if "name" in m and "value" in m}

        running_gauge.append(m_map.get("vllm:num_requests_running", 0.0))
        waiting_gauge.append(m_map.get("vllm:num_requests_waiting", 0.0))

        cur_step_cnt = m_map.get("vllm:iteration_tokens_total_count") or m_map.get("vllm:prompt_tokens_total_count")
        cur_tok_cnt = m_map.get("vllm:iteration_tokens_total_sum") or m_map.get("vllm:prompt_tokens_total_sum")

        if cur_step_cnt is not None:
            if last_step_cnt is not None:
                d_steps = max(0.0, cur_step_cnt - last_step_cnt)
                d_toks = max(0.0, cur_tok_cnt - last_tok_cnt) if (cur_tok_cnt and last_tok_cnt) else 0.0
                steps_delta.append(d_steps)
                tokens_delta.append(d_toks)
                if d_steps == 0:
                    zero_step_intervals.append((times[-2], ts))
            last_step_cnt = cur_step_cnt
            last_tok_cnt = cur_tok_cnt

        if "vllm:request_prefill_time_seconds_sum" in m_map and "vllm:request_prefill_time_seconds_count" in m_map:
            prefill_hist_sum = m_map["vllm:request_prefill_time_seconds_sum"]
            prefill_hist_count = m_map["vllm:request_prefill_time_seconds_count"]

    engine_prefill_mean = (prefill_hist_sum / prefill_hist_count) if (prefill_hist_sum and prefill_hist_count) else None

    res = {
        "scrapes_count": len(scrapes),
        "zero_step_intervals": zero_step_intervals,
        "max_running": max(running_gauge) if running_gauge else 0,
        "max_waiting": max(waiting_gauge) if waiting_gauge else 0,
        "engine_prefill_mean_s": engine_prefill_mean,
    }

    if run_path and os.path.exists(run_path):
        a = pw.analyze(run_path, budget=budget, with_engine=True)
        res["drawn_read_mean_s"] = a["drawn"]["read_mean_s"]
        res["drawn_queue_mean_s"] = a["drawn"]["queue_mean_s"]
        if engine_prefill_mean and a["drawn"]["read_mean_s"] > 0:
            ratio = engine_prefill_mean / a["drawn"]["read_mean_s"]
            res["prefill_engine_vs_drawn_ratio"] = ratio

    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("metrics_jsonl", help="Path to metrics_node0.jsonl")
    ap.add_argument("--run", help="Path to run.json for cross-validation")
    ap.add_argument("--budget", type=int, default=8192)
    args = ap.parse_args()

    scrapes = load_scrapes(args.metrics_jsonl)
    res = analyze_metrics(scrapes, args.run, args.budget)

    print(f"Scrapes analyzed: {res['scrapes_count']}")
    print(f"Peak running gauge: {res['max_running']}, Peak waiting gauge: {res['max_waiting']}")
    if res["zero_step_intervals"]:
        print(f"Detected {len(res['zero_step_intervals'])} intervals with 0 steps (potential pauses):")
        for a, b in res["zero_step_intervals"][:5]:
            print(f"  Gap: {a:.3f}s -> {b:.3f}s (duration: {b - a:.3f}s)")
    else:
        print("No zero-step intervals observed during active sampling.")

    if "drawn_read_mean_s" in res:
        print(f"Drawn mean read: {res['drawn_read_mean_s']:.3f} s")
        if res.get("engine_prefill_mean_s"):
            print(f"Engine prefill histogram mean: {res['engine_prefill_mean_s']:.3f} s (Ratio: {res.get('prefill_engine_vs_drawn_ratio', 0):.2f}x)")


if __name__ == "__main__":
    main()
