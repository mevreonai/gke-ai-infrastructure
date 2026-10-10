#!/usr/bin/env python3
"""Rebuild expected_values.json from the two result archives, with the reference implementation.
  PILOT  = the pilot's real_data folder (it holds final_validation/combined_vllm_runs.csv)
  SECOND = the second campaign's raw_runs folder (it holds stage1/ and stage2/)
Usage:  python3 build_expected_values.py <PILOT> <SECOND> [expected_values.json]"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))     # find the sibling modules, also under python3 -I
import pip_scan
import pip_waves as pw

EXT1M = "vllm_single_node_v" + "8_1m_extensions"          # the pilot's 1M extension runs
M6 = "vllm_single_node_v6_matrix"
L2 = "stage2/03_multi_node_load"
FIXTURES = [  # (root, path, case, bench, budget, what it shows)
    ("pilot", f"{M6}/tp4_closedloop_8k/c32/c32.json", "tp4_closedloop_8k", "c32", 8192, "the burst: the summary mean describes almost no request"),
    ("pilot", f"{M6}/tp4_closedloop_8k/c8/c8.json", "tp4_closedloop_8k", "c8", 8192, "first wave one prompt at a time at 8K, one stage"),
    ("pilot", f"{M6}/tp4_closedloop_128k/c4/c4.json", "tp4_closedloop_128k", "c4", 8192, "the guide figure: reads, stalls, no idle time"),
    ("pilot", f"{M6}/tp4_closedloop_128k/c8/c8.json", "tp4_closedloop_128k", "c8", 8192, "first wave at 128K, one stage"),
    ("pilot", f"{M6}/tp8_qualification/8k_c8/8k_c8.json", "tp8_qualification", "8k_c8", 8192, "TP8/PP1 at 8K"),
    ("pilot", "{ext1m}/tp4_1m_concurrency_extension/1m_c4/1m_c4.json", "tp4_1m_concurrency_extension", "1m_c4", 8192, "1M ladder, TP4/PP1"),
    ("pilot", "{ext1m}/tp8_1m_concurrency_extension/1m_c4/1m_c4.json", "tp8_1m_concurrency_extension", "1m_c4", 8192, "1M ladder, TP8/PP1"),
    ("second", "stage1/01_chunk_budget_ab/control/tp4_8k_chunk_control_8192/8k_c4/8k_c4.json", "tp4_8k_chunk_control_8192", "8k_c4", 8192, "A/B control: a 4 s pause in the first run"),
    ("second", "stage1/01_chunk_budget_ab/fix/tp4_8k_chunk_fix_8448/8k_c4/8k_c4.json", "tp4_8k_chunk_fix_8448", "8k_c4", 8448, "A/B other arm: same warmup, no pause"),
    ("second", "stage1/01_chunk_budget_ab/control/tp4_8k_chunk_control_8192/8k_c32/8k_c32.json", "tp4_8k_chunk_control_8192", "8k_c32", 8192, "8K: one prompt per step"),
    ("second", "stage1/05_short_prompts/tp4_short_prompts/1k_c32/1k_c32.json", "tp4_short_prompts", "1k_c32", 8192, "1K: up to 8 prompts per step"),
    ("second", "stage1/05_short_prompts/tp4_short_prompts/2k_c32/2k_c32.json", "tp4_short_prompts", "2k_c32", 8192, "2K: 4 prompts per step"),
] + [("second", f"{L2}/{c}/{c}/{b}/{b}.json", c, b, 8192, w) for c in ("tp4_pp2_dist_load", "tp8_pp2_dist_load", "tp4_pp4_dist_load", "tp16_pp1_dist_load")
     for b, w in (("8k_c8", "8K on two servers, the server's first run"), ("128k_c8", "128K on two servers"), ("1m_c4", "1M on two servers"))]


def engine_means(root_label, root, case, bench):
    files = [f"{root}/final_validation/combined_vllm_runs.csv"] if root_label == "pilot" else glob.glob(f"{root}/stage*/*/summary/vllm_runs.csv")
    for fn in files:
        for r in csv.DictReader(open(fn)):
            if r.get("case") == case and r.get("bench") == bench and r.get("status", "COMPLETED") == "COMPLETED" and r.get("network_mode", "local").lower() in ("local", "native"):
                return float(r["queue_mean_s_from_hist"]), float(r["prefill_mean_s_from_hist"])
    return None, None


def keep(a):
    out = {k: a[k] for k in ("n", "C", "failed", "file_order_is_send_order")}
    if "waves" in a:
        w = a["waves"]; out["waves"] = {k: w[k] for k in ("lone_read_s", "first_wave_reads", "first_wave_mean_reads", "one_at_a_time_mean", "step_reads", "later_mean_reads",
                                                          "later_wave_send_spread_reads")}
        out["burst"] = {k: a["burst"][k] for k in ("mean_s", "first_wave_mean_s", "later_mean_s", "burst_share_of_waiting", "within_20pct_of_mean")}
        out["prompts_per_step"] = a["prompts_per_step"]
    out["stalls"] = {k: a["stalls"][k] for k in ("gaps", "stalled_gaps", "ambiguous_gaps", "step_ms", "stall_ms", "stall_share")}
    out["pause"] = {k: a["pause"][k] for k in ("silence_s", "at_s", "ratio", "is_pause", "summary_p99_itl_ms")}
    out["drawn"] = a["drawn"]; out["engine"] = a["engine"]
    return out


if __name__ == "__main__":
    PILOT, SECOND = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); OUTF = sys.argv[3] if len(sys.argv) > 3 else "expected_values.json"
    roots = {"pilot": PILOT, "second": SECOND}; fx = []
    for lab, rel, case, bench, budget, why in FIXTURES:
        p = os.path.join(roots[lab], rel.format(ext1m=EXT1M)); q, pr = engine_means(lab, roots[lab], case, bench)
        a = pw.analyze(p, budget, q, pr)
        fx.append(dict(root=lab, path=rel, md5=hashlib.md5(open(p, "rb").read()).hexdigest(), budget=budget, shows=why, expected=keep(a)))
        print(f"{lab:6s} {rel.split('/')[-3]:32s} {bench:7s} pause {a['pause']['is_pause']!s:5s} stalled {100 * a['stalls']['stall_share']:5.1f}% "
              + (f"first wave {a['waves']['first_wave_mean_reads']:.2f} reads (rule {a['waves']['one_at_a_time_mean']:.1f}) step {a['waves']['step_reads']:.2f}" if "waves" in a else ""))
    rows = pip_scan.scan([PILOT, SECOND])
    lab_of = {PILOT: "pilot", SECOND: "second"}
    scan_exp = dict(files={lab_of[r]: sum(1 for x in rows if x["root"] == r) for r in (PILOT, SECOND)},
                    profiler_captures={lab_of[r]: sum(1 for x in rows if x["root"] == r and x["profiled"]) for r in (PILOT, SECOND)},
                    failed_requests=sum(x["failed"] for x in rows), file_order_is_send_order=all(x["file_order_is_send_order"] for x in rows),
                    pauses=[dict(root=lab_of[x["root"]], path=x["path"], silence_s=x["silence_s"], at_s=x["at_s"], ratio=x["ratio"], rank_in_session=x["rank_in_session"],
                                 summary_p99_itl_ms=x["summary_p99_itl_ms"]) for x in sorted(rows, key=lambda r: -r["ratio"]) if x["is_pause"]])
    json.dump(dict(about="Reference values from pip_waves.py and pip_scan.py on the two result archives. Paths are relative to the archive roots; "
                         "{ext1m} stands for the pilot's 1M extension folder (see build_expected_values.py). Each fixture names its input file's md5.",
                   thresholds=dict(stall_s=pw.STALL_S, pause_normal_steps=pw.PAUSE_STEPS, back_to_back_share_of_a_read=pw.BACK_TO_BACK),
                   fixtures=fx, scan=scan_exp), open(OUTF, "w"), indent=1)
    print(f"wrote {OUTF}: {len(fx)} fixtures; scan {scan_exp['files']} files, {len(scan_exp['pauses'])} pauses")
