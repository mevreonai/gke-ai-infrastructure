#!/usr/bin/env python3
"""pip_scan: the pause scan over every per-request file under one or more result folders.

For each `vllm bench serve --save-detailed` file found: its layout and step budget (from the nearest case_manifest.json,
else from the path), its place in its server session (0 = the first run that server served after its warmup), whether
a profiler was on (path names a profile), the longest stretch with no token to anyone while someone was mid-answer,
and whether that is a pause (3 normal steps or more; see pip_waves). Profiler captures are reported but never counted.

Usage:  python3 pip_scan.py <results dir> [<results dir> ...] [--csv scan.csv] [--json scan.json]"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import statistics as st

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))     # find the sibling modules, also under python3 -I
import pip_waves as pw


def manifest_for(path, root):
    q = os.path.dirname(path)
    while q.startswith(root):
        m = os.path.join(q, "case_manifest.json")
        if os.path.exists(m):
            try: return json.load(open(m))
            except Exception: return None
        if q == root: break
        q = os.path.dirname(q)
    return None


def is_profile(rel):
    """A profiler capture: its path names a profile, or the bench ran as the workload of a capture."""
    rl = rel.lower().replace("\\", "/")
    return "profile" in rl or "/workload/" in rl


def prompt_label(n):
    return f"{round(n / 1e6)}M" if n >= 1_000_000 else f"{n // 1024}K" if n and n % 1024 == 0 else str(n)


def scan(roots):
    rows = []
    for root in roots:
        root = os.path.abspath(root)
        for p in sorted(glob.glob(os.path.join(root, "**", "*.json"), recursive=True)):
            b = os.path.basename(p)
            if "warmup" in b or "manifest" in b: continue
            try: d = json.load(open(p))
            except Exception: continue
            if not isinstance(d, dict) or not all(k in d for k in ("ttfts", "start_times", "itls")) or not d["ttfts"]: continue
            m = manifest_for(p, root) or {}
            tp, pp = m.get("tp"), m.get("pp")
            if tp is None:
                toks = re.findall(r"(tp|pp)(\d+)", os.path.relpath(p, root).lower())
                tp = next((int(v) for k, v in toks if k == "tp"), None); pp = next((int(v) for k, v in toks if k == "pp"), 1)
            budget = int(m.get("max_num_batched_tokens") or 8192)
            run = pw.load(p); pz = pw.pause(run, budget); rel = os.path.relpath(p, root).replace("\\", "/")
            session = os.path.relpath(os.path.dirname(os.path.dirname(p)), root).replace("\\", "/")
            rows.append(dict(root=root, path=rel, session=session, date=d.get("date") or "",
                             layout=f"TP{tp}/PP{pp or 1}" if tp else "?", prompt=prompt_label(run["input_len"]), C=run["C"], n=run["n"],
                             closed=run["closed"], budget=budget, failed=run["n"] - sum(run["ok"]),
                             file_order_is_send_order=run["file_order_is_send_order"], profiled=is_profile(rel),
                             silence_s=pz["silence_s"], at_s=pz["at_s"], normal_step_s=pz["normal_step_s"], ratio=pz["ratio"],
                             is_pause=pz["is_pause"] and not is_profile(rel), summary_p99_itl_ms=pz["summary_p99_itl_ms"],
                             duration_s=run["duration"]))
    ses = {}
    for r in rows: ses.setdefault((r["root"], r["session"]), []).append(r)
    for v in ses.values():
        v.sort(key=lambda r: r["date"])
        for k, r in enumerate(v): r["rank_in_session"] = k; r["runs_in_session"] = len(v)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("roots", nargs="+"); ap.add_argument("--csv"); ap.add_argument("--json")
    args = ap.parse_args(); rows = scan(args.roots)
    prof = [r for r in rows if r["profiled"]]; live = [r for r in rows if not r["profiled"]]
    print(f"{len(rows)} runs ({len(prof)} profiler captures, not counted) · failed requests {sum(r['failed'] for r in rows)} · "
          f"file order = send order in {sum(r['file_order_is_send_order'] for r in rows)}")
    for r in sorted(live, key=lambda r: -(r["ratio"] or 0))[:8]:
        print(f"  {'PAUSE' if r['is_pause'] else '     '} {r['silence_s']:6.2f} s at {r['at_s'] or 0:7.2f} s = {r['ratio']:5.1f} steps · {r['layout']:9s} {r['prompt']:>5s} "
              f"{r['C']:>3d} in flight · run {r['rank_in_session'] + 1} of {r['runs_in_session']} on its server · p99 token gap {r['summary_p99_itl_ms'] or 0:.1f} ms · {r['path']}")
    if args.csv and rows:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    if args.json: json.dump(rows, open(args.json, "w"), indent=1)
