#!/usr/bin/env python3
"""Tests for pip_waves and pip_scan.

Synthetic tests always run: small runs built in a temp folder whose answer is known.
Data tests run when both archives are given:
  PIP_PILOT_ROOT   the pilot's real_data folder (holds final_validation/combined_vllm_runs.csv)
  PIP_SECOND_ROOT  the second campaign's raw_runs folder (holds stage1/ and stage2/)
They check every fixture in expected_values.json (skipping a file whose md5 differs) and the scan.

Run:  python3 test_pip_waves.py      (or: pytest test_pip_waves.py)"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pip_scan  # noqa: E402
import pip_waves as pw  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXT1M = "vllm_single_node_v" + "8_1m_extensions"


def write_run(starts, ttfts, itls, C, folder, name="run.json", budget_len=8192, out_len=None):
    n = len(ttfts); g = sorted(x for l in itls for x in l)
    d = dict(ttfts=ttfts, start_times=starts, itls=itls, input_lens=[budget_len] * n, output_lens=[out_len or (len(itls[0]) + 1)] * n,
             errors=[""] * n, max_concurrency=C, request_rate="inf", p99_itl_ms=1000 * g[int(0.99 * (len(g) - 1))] if g else 0.0,
             duration=max(s + t + sum(l) for s, t, l in zip(starts, ttfts, itls)), mean_ttft_ms=1000 * sum(ttfts) / n, date="20260101-000000")
    p = os.path.join(folder, name); json.dump(d, open(p, "w")); return p


def one_at_a_time(pause_s=0.0):
    """Four requests sent together; one 1 s read at a time; each answer stalls 1 s for every read after its own, then
    writes at 10 ms a token. With pause_s, nothing moves for pause_s seconds right after the first token."""
    ttfts = [1.0, 2.0 + pause_s, 3.0 + pause_s, 4.0 + pause_s]
    itls = [[1.0 + pause_s, 1.0, 1.0] + [0.01] * 6, [1.0, 1.0] + [0.01] * 7, [1.0] + [0.01] * 8, [0.01] * 9]
    return [0.0, 0.001, 0.002, 0.003], ttfts, itls


def test_first_wave_one_at_a_time():
    with tempfile.TemporaryDirectory() as t:
        p = write_run(*one_at_a_time(), C=4, folder=t); r = pw.load(p); w = pw.waves(r)
        assert [round(x, 2) for x in w["first_wave_reads"]] == [1.0, 2.0, 3.0, 4.0]
        assert abs(w["first_wave_mean_reads"] - 2.5) < 1e-9 and abs(w["step_reads"] - 1.0) < 1e-9 and w["one_at_a_time_mean"] == 2.5


def test_side_by_side_reads():
    with tempfile.TemporaryDirectory() as t:
        p = write_run([0.0] * 4, [1.0, 1.5, 2.0, 2.5], [[0.01] * 5] * 4, C=4, folder=t)
        assert abs(pw.waves(pw.load(p))["step_reads"] - 0.5) < 1e-9


def test_stalls_and_no_pause():
    with tempfile.TemporaryDirectory() as t:
        p = write_run(*one_at_a_time(), C=4, folder=t); a = pw.analyze(p)
        assert a["stalls"]["stalled_gaps"] == 6 and abs(a["stalls"]["step_ms"] - 10.0) < 1e-6
        # answering time: 3.06 + 2.07 + 1.08 + 0.09 s; stalled 3 + 2 + 1 s
        assert abs(a["stalls"]["stall_share"] - 6.0 / 6.30) < 1e-9
        assert not a["pause"]["is_pause"] and abs(a["pause"]["ratio"] - 1.0) < 1e-9   # a 1 s stall equals one 1 s read step


def test_pause_is_found():
    with tempfile.TemporaryDirectory() as t:
        p = write_run(*one_at_a_time(pause_s=4.0), C=4, folder=t); a = pw.analyze(p)
        assert a["pause"]["is_pause"] and abs(a["pause"]["silence_s"] - 5.0) < 1e-9 and abs(a["pause"]["at_s"] - 1.0) < 1e-9


def test_reads_back_to_back_and_engine():
    with tempfile.TemporaryDirectory() as t:
        p = write_run(*one_at_a_time(), C=4, folder=t); r = pw.load(p); rows = pw.phases(r)
        assert [(round(x["read_start"], 3), round(x["f"], 3)) for x in rows] == [(0.0, 1.0), (1.0, 2.001), (2.001, 3.002), (3.002, 4.003)]
        e = pw.engine(rows, r["C"]); assert e["max_reads"] == 1 and e["idle_share"] == 0.0, (e["max_reads"], e["idle_share"])


def test_pause_turns_everything_into_waiting():
    with tempfile.TemporaryDirectory() as t:
        p = write_run(*one_at_a_time(pause_s=4.0), C=4, folder=t); r = pw.load(p); a = pw.analyze(p)
        lo, hi = a["pause"]["at_s"], a["pause"]["at_s"] + a["pause"]["silence_s"]
        for row in pw.phases(r, (lo, hi)):
            assert all(k in ("line", "stall") for x0, x1, k in row["seg"] if x0 >= lo - 1e-9 and x1 <= hi + 1e-9)


def test_send_order_not_file_order():
    s, f, i = one_at_a_time(); perm = [2, 0, 3, 1]
    with tempfile.TemporaryDirectory() as t:
        p = write_run([s[k] for k in perm], [f[k] for k in perm], [i[k] for k in perm], C=4, folder=t); r = pw.load(p)
        assert not r["file_order_is_send_order"] and [round(x, 2) for x in pw.waves(r)["first_wave_reads"]] == [1.0, 2.0, 3.0, 4.0]


def test_scan_ranks_runs_on_a_server():
    with tempfile.TemporaryDirectory() as t:
        case = os.path.join(t, "case_a"); os.makedirs(os.path.join(case, "b1")); os.makedirs(os.path.join(case, "b2"))
        json.dump(dict(tp=4, pp=2, max_num_batched_tokens=8192), open(os.path.join(case, "case_manifest.json"), "w"))
        p1 = write_run(*one_at_a_time(pause_s=4.0), C=4, folder=os.path.join(case, "b1"), name="b1.json")
        p2 = write_run(*one_at_a_time(), C=4, folder=os.path.join(case, "b2"), name="b2.json")
        d = json.load(open(p2)); d["date"] = "20260101-000500"; json.dump(d, open(p2, "w"))
        rows = {os.path.basename(r["path"]): r for r in pip_scan.scan([t])}
        assert rows["b1.json"]["is_pause"] and rows["b1.json"]["rank_in_session"] == 0 and rows["b2.json"]["rank_in_session"] == 1
        assert rows["b1.json"]["layout"] == "TP4/PP2" and not rows["b2.json"]["is_pause"]


# ------------------------------------------------------------------ the two archives
def close(a, b, rel=0.005, ab=0.005):
    if isinstance(b, bool) or b is None or isinstance(a, bool): return a == b
    if isinstance(b, (int, float)) and isinstance(a, (int, float)): return abs(a - b) <= max(ab, rel * abs(b))
    if isinstance(b, list): return isinstance(a, list) and len(a) == len(b) and all(close(x, y, rel, ab) for x, y in zip(a, b))
    if isinstance(b, dict): return all(close(a.get(k), v, rel, ab) for k, v in b.items())
    return a == b


def test_archives():
    P, S = os.environ.get("PIP_PILOT_ROOT"), os.environ.get("PIP_SECOND_ROOT")
    if not (P and S):
        print("   (skipped: set PIP_PILOT_ROOT and PIP_SECOND_ROOT to check the archives)"); return
    E = json.load(open(os.path.join(HERE, "expected_values.json"))); roots = {"pilot": P, "second": S}; bad = []
    for fx in E["fixtures"]:
        p = os.path.join(roots[fx["root"]], fx["path"].format(ext1m=EXT1M))
        if not os.path.exists(p) or hashlib.md5(open(p, "rb").read()).hexdigest() != fx["md5"]:
            print(f"   (skipped, not the same file: {fx['path']})"); continue
        e = fx["expected"]; a = pw.analyze(p, fx["budget"], e["drawn"]["engine_queue_mean_s"], e["drawn"]["engine_prefill_mean_s"])
        for k, v in e.items():
            if not close(a.get(k), v): bad.append(f"{fx['path']}: {k} = {a.get(k)!r:.200}, expected {v!r:.200}")
    rows = pip_scan.scan([P, S]); got = sorted(r["path"] for r in rows if r["is_pause"])
    if got != sorted(x["path"] for x in E["scan"]["pauses"]): bad.append(f"scan pauses {got}")
    if sum(r["failed"] for r in rows) != E["scan"]["failed_requests"]: bad.append("failed requests differ")
    assert not bad, "\n".join(bad)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]; failed = 0
    for t in tests:
        try: t(); print(f"ok    {t.__name__}")
        except AssertionError as e: failed += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"{len(tests) - failed} of {len(tests)} passed"); sys.exit(1 if failed else 0)
