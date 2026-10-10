#!/usr/bin/env python3
"""pip_waves: who waited for whom in one `vllm bench serve --save-detailed` run.

Reference implementation for the platform's wave, stall and pause checks. It reads only the per-request file
(start_times, ttfts, itls, input_lens, output_lens, errors, max_concurrency, request_rate) and, where given, the
server's max-num-batched-tokens. Standard library only.

Definitions (keep them when porting):
  send order       requests sorted by start_times (in every file we checked this equals file order; warn if not)
  wave k           requests k*C .. k*C+C-1 in send order. The first wave is exact: they were sent together.
                   Later waves are approximate: each request goes out when an earlier one finishes.
  lone read R      the first wave's shortest wait for the first token: a prompt with nothing ahead of it.
  first wave       its waits sorted and divided by R. One prompt at a time gives 1, 2, 3 ... C, mean (C+1)/2.
  step             median spacing of that sorted list: 1.0 one at a time, 0.5 two side by side, under 1 with stages.
  burst share      the first wave's share of all waiting for first tokens in the run.
  token times      first token at start + ttft; each later token adds its itl.
  stall            a gap between two tokens of one answer above STALL_S (100 ms): the answer waited while the engine
                   read another prompt. Normal steps and stalls do not overlap in our runs; ambiguous() says so.
  decode silence   the longest stretch during which some request was mid-answer (had its first token, not its last)
                   and no request received a token.
  normal step      the longest a token can wait without a fault: one full prefill step, estimated as R*B/I (the
                   lone read scaled to a step of B tokens, B the server's --max-num-batched-tokens, I the prompt
                   length), or the run's p99 token gap where that is longer. One request at a time: the p99 gap.
  pause            a decode silence of PAUSE_STEPS (3) normal steps or more.
  drawn read       when a prompt was being read, from timestamps: one lone read before its first token, or from
                   the previous first token where reads run back to back (closer than BACK_TO_BACK of a read).
                   Check it against the engine's own queue and prefill histogram means for the run.
  segments         per request: line (waiting for its read), read (prefill), write (decode), stall; inside a
                   pause every request is waiting.
  engine strips    over time: prompts being read, answers getting tokens, answers stalled.

Usage:  python3 pip_waves.py <run.json> [--budget 8192] [--json out.json]
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import statistics as st
import sys

STALL_S = 0.100
PAUSE_STEPS = 3.0
BACK_TO_BACK = 0.10


# ------------------------------------------------------------------ loading
def load(path):
    d = json.load(open(path))
    if "ttfts" not in d or "start_times" not in d or "itls" not in d:
        raise ValueError(f"{path}: no per-request timings; rerun with --save-detailed")
    n = len(d["ttfts"])
    errors = d.get("errors") or [""] * n
    order = sorted(range(n), key=lambda i: d["start_times"][i])
    rr = d.get("request_rate")
    closed = rr in (None, "inf", float("inf")) or (isinstance(rr, str) and rr.lower() == "inf")
    t0 = min(d["start_times"])
    run = dict(path=path, n=n, C=int(d.get("max_concurrency") or 1), closed=closed, order=order,
               file_order_is_send_order=(order == list(range(n))),
               s=[d["start_times"][i] - t0 for i in order], ttft=[d["ttfts"][i] for i in order],
               itls=[list(d["itls"][i]) for i in order], ok=[not errors[i] for i in order],
               input_len=int(st.mean(d.get("input_lens") or [0])), output_len=int(st.mean(d.get("output_lens") or [0])),
               p99_itl_s=(d["p99_itl_ms"] / 1000) if d.get("p99_itl_ms") is not None else None,
               duration=d.get("duration"), mean_ttft_s=(d["mean_ttft_ms"] / 1000) if d.get("mean_ttft_ms") is not None else None,
               date=d.get("date"))
    run["f"] = [run["s"][k] + run["ttft"][k] for k in range(n)]
    run["e"] = [run["f"][k] + sum(run["itls"][k]) for k in range(n)]
    return run


def lone_read(run):
    C = run["C"] if run["closed"] else run["n"]
    w = [t for t, ok in zip(run["ttft"][:max(1, C)], run["ok"]) if ok]
    return min(w) if w else min(run["ttft"])


# ------------------------------------------------------------------ waves
def waves(run):
    C, n = run["C"], run["n"]
    R = lone_read(run)
    fw = sorted(run["ttft"][:C]); reads = [x / R for x in fw]
    steps = [b - a for a, b in zip(reads, reads[1:])]
    later = run["ttft"][C:]
    per_wave = [st.mean(run["ttft"][k:k + C]) for k in range(0, n, C)]
    send_spread = [max(run["s"][k:k + C]) - min(run["s"][k:k + C]) for k in range(C, n, C)]
    return dict(C=C, lone_read_s=R, first_wave_reads=reads, first_wave_mean_reads=st.mean(reads),
                one_at_a_time_mean=(C + 1) / 2, step_reads=(st.median(steps) if steps else None),
                later_mean_reads=(st.mean(later) / R if later else None), per_wave_mean_s=per_wave,
                later_wave_send_spread_reads=[x / R for x in send_spread])


def burst(run):
    C, t = run["C"], run["ttft"]
    m = st.mean(t)
    return dict(mean_s=m, first_wave_mean_s=st.mean(t[:C]), later_mean_s=(st.mean(t[C:]) if len(t) > C else None),
                burst_share_of_waiting=sum(t[:C]) / sum(t), within_20pct_of_mean=sum(0.8 * m <= x <= 1.2 * m for x in t))


def prompts_per_step(run, tol_s=0.012):
    """First-wave first tokens that land within tol_s of each other came out of the same step."""
    groups = []
    for x in sorted(run["ttft"][:run["C"]]):
        if groups and x - groups[-1][-1] < tol_s: groups[-1].append(x)
        else: groups.append([x])
    return [len(g) for g in groups]


# ------------------------------------------------------------------ tokens, stalls, silence, pause
def token_times(run):
    out = []
    for k in range(run["n"]):
        t = run["f"][k]; ts = [t]
        for g in run["itls"][k]:
            t += g; ts.append(t)
        out.append(ts)
    return out


def stalls(run, thr=STALL_S):
    gaps = [g for l in run["itls"] for g in l]
    lo = [g for g in gaps if g <= thr]; hi = [g for g in gaps if g > thr]
    per = []
    for k in range(run["n"]):
        a = run["e"][k] - run["f"][k]
        per.append(sum(g for g in run["itls"][k] if g > thr) / a if a > 0 else 0.0)
    ans = sum(run["e"][k] - run["f"][k] for k in range(run["n"]))
    return dict(threshold_s=thr, gaps=len(gaps), stalled_gaps=len(hi),
                step_ms=(1000 * st.median(lo) if lo else None), stall_ms=(1000 * st.median(hi) if hi else None),
                ambiguous_gaps=sum(0.06 < g <= 0.15 for g in gaps),
                stall_share=(sum(hi) / ans if ans > 0 else 0.0), stall_share_per_request=per)


def decode_silence(run):
    ev = sorted(t for ts in token_times(run) for t in ts)
    dec = sorted((run["f"][k], run["e"][k]) for k in range(run["n"]) if run["ok"][k])
    fs = [a for a, _ in dec]; pm, m = [], float("-inf")
    for _, b in dec:
        m = max(m, b); pm.append(m)
    best = (0.0, None)
    for a, b in zip(ev, ev[1:]):
        j = bisect.bisect_right(fs, a) - 1
        if j >= 0 and pm[j] >= b and b - a > best[0]:
            best = (b - a, a)
    return best


def normal_step(run, budget=8192):
    p99 = run["p99_itl_s"]
    if p99 is None:
        g = sorted(x for l in run["itls"] for x in l); p99 = g[int(0.99 * (len(g) - 1))] if g else 0.0
    if run["closed"] and run["C"] <= 1:
        return p99
    R, I, B = lone_read(run), max(1, run["input_len"]), budget
    return max(p99, R * B / I)


def pause(run, budget=8192):
    sil, at = decode_silence(run); ns = normal_step(run, budget)
    ratio = sil / ns if ns else None
    return dict(silence_s=sil, at_s=at, normal_step_s=ns, ratio=ratio, is_pause=bool(ratio is not None and ratio >= PAUSE_STEPS),
                summary_p99_itl_ms=None if run["p99_itl_s"] is None else 1000 * run["p99_itl_s"])


# ------------------------------------------------------------------ phases and the engine strips
def phases(run, pause_interval=None, thr=STALL_S):
    R = lone_read(run); n = run["n"]
    served = sorted(range(n), key=lambda k: run["f"][k]); rs = {}; fprev = float("-inf")
    for k in served:
        cand = run["f"][k] - R
        rs[k] = max(run["s"][k], cand if cand < fprev - BACK_TO_BACK * R else fprev); fprev = run["f"][k]
    rows = []
    for k in range(n):
        seg = []
        if rs[k] > run["s"][k]: seg.append([run["s"][k], rs[k], "line"])
        seg.append([rs[k], run["f"][k], "read"])
        t = run["f"][k]
        for g in run["itls"][k]:
            kind = "stall" if g > thr else "write"
            if seg[-1][2] == kind and abs(seg[-1][1] - t) < 1e-9: seg[-1][1] = t + g
            else: seg.append([t, t + g, kind])
            t += g
        if pause_interval:
            a0, b0 = pause_interval; out = []
            for a, b, kind in seg:
                for x, y, inside in ((a, min(b, a0), False), (max(a, a0), min(b, b0), True), (max(a, b0), b, False)):
                    if y > x: out.append([x, y, {"read": "line", "write": "stall"}.get(kind, kind) if inside else kind])
            seg = out
        rows.append(dict(k=k, s=run["s"][k], read_start=rs[k], f=run["f"][k], e=run["e"][k], seg=seg))
    return rows


def engine(rows, C, samples=3000):
    T = max(r["e"] for r in rows); ts = [T * j / samples for j in range(samples)]; rd, wr, sl = [], [], []    # [0, T): the end is not a moment of the run
    for t in ts:
        a = b = c = 0
        for r in rows:
            if any(kind == "read" and x0 <= t < x1 for x0, x1, kind in r["seg"]): a += 1
            if r["f"] <= t < r["e"]:
                if any(kind == "stall" and x0 <= t < x1 for x0, x1, kind in r["seg"]): c += 1
                else: b += 1
        rd.append(a); wr.append(b); sl.append(c)
    busy = [x for x in rd if x > 0]
    return dict(t=ts, reading=rd, writing=wr, stalled=sl, reads_at_once=(st.mean(busy) if busy else 0.0), max_reads=max(rd),
                idle_share=sum(1 for a, b, c in zip(rd, wr, sl) if a == b == c == 0) / samples, C=C, T=T)


# ------------------------------------------------------------------ one call for everything
def analyze(path, budget=8192, engine_queue_s=None, engine_prefill_s=None, with_engine=True):
    run = load(path)
    out = dict(path=path, n=run["n"], C=run["C"], closed=run["closed"], input_len=run["input_len"], output_len=run["output_len"],
               file_order_is_send_order=run["file_order_is_send_order"], failed=run["n"] - sum(run["ok"]), duration_s=run["duration"])
    if run["closed"] and run["C"] > 1:
        out["waves"] = waves(run); out["burst"] = burst(run); out["prompts_per_step"] = prompts_per_step(run)
    out["stalls"] = {k: v for k, v in stalls(run).items() if k != "stall_share_per_request"}
    out["pause"] = pause(run, budget)
    pi = (out["pause"]["at_s"], out["pause"]["at_s"] + out["pause"]["silence_s"]) if out["pause"]["is_pause"] else None
    rows = phases(run, pi)
    out["drawn"] = dict(queue_mean_s=st.mean(r["read_start"] - r["s"] for r in rows), read_mean_s=st.mean(r["f"] - r["read_start"] for r in rows),
                        engine_queue_mean_s=engine_queue_s, engine_prefill_mean_s=engine_prefill_s)
    if with_engine:
        e = engine(rows, run["C"]); out["engine"] = {k: e[k] for k in ("reads_at_once", "max_reads", "idle_share")}
    return out


def report(a):
    L = [f"{a['path']}", f"n={a['n']} C={a['C']} ISL {a['input_len']} OSL {a['output_len']} failed {a['failed']} | "
         + ("file order = send order" if a["file_order_is_send_order"] else "WARNING: file order differs from send order")]
    if "waves" in a:
        w, b = a["waves"], a["burst"]
        L.append(f"first wave: lone read {w['lone_read_s']:.3f} s; in reads " + " ".join(f"{x:.2f}" for x in w["first_wave_reads"])
                 + f" | mean {w['first_wave_mean_reads']:.2f} (one at a time: {w['one_at_a_time_mean']:.1f}); a prompt every {w['step_reads']:.2f} reads")
        if w["later_mean_reads"] is not None:
            L.append(f"later requests: {w['later_mean_reads']:.2f} reads on average; the first wave is {100 * b['burst_share_of_waiting']:.0f}% of all waiting")
        L.append("first-wave prompts per step: " + " ".join(map(str, a["prompts_per_step"])))
    s = a["stalls"]
    L.append(f"tokens: normal step {s['step_ms']:.1f} ms" + (f", stall {s['stall_ms']:.0f} ms" if s["stall_ms"] else "")
             + f" ({s['stalled_gaps']} of {s['gaps']} gaps over {1000 * s['threshold_s']:.0f} ms; {s['ambiguous_gaps']} between 60 and 150 ms);"
             + f" answers stalled {100 * s['stall_share']:.0f}% of their time")
    p = a["pause"]
    L.append((f"PAUSE: {p['silence_s']:.2f} s with no token to anyone at {p['at_s']:.2f} s ({p['ratio']:.1f} normal steps; summary p99 token gap "
              f"{p['summary_p99_itl_ms']:.1f} ms)") if p["is_pause"] else f"no pause: longest stretch without a token {p['silence_s']:.2f} s = {p['ratio']:.1f} normal steps")
    dr = a["drawn"]
    L.append(f"drawn read {dr['read_mean_s']:.2f} s, in line {dr['queue_mean_s']:.2f} s"
             + (f" (engine: read {dr['engine_prefill_mean_s']:.2f} s, queue {dr['engine_queue_mean_s']:.2f} s)" if dr["engine_prefill_mean_s"] is not None else ""))
    if "engine" in a:
        L.append(f"engine: {a['engine']['reads_at_once']:.2f} prompts read at once while reading (max {a['engine']['max_reads']}); idle {100 * a['engine']['idle_share']:.1f}% of the run")
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run"); ap.add_argument("--budget", type=int, default=8192, help="the server's --max-num-batched-tokens")
    ap.add_argument("--engine-queue", type=float); ap.add_argument("--engine-prefill", type=float)
    ap.add_argument("--json"); ap.add_argument("--no-engine", action="store_true")
    args = ap.parse_args()
    a = analyze(args.run, args.budget, args.engine_queue, args.engine_prefill, not args.no_engine)
    print(report(a))
    if args.json: json.dump(a, open(args.json, "w"), indent=1)
