#!/usr/bin/env python3
"""pip_timeline: draw one run as the guide figure does. The engine on top (prompts being read; answers getting tokens
or stalled), then every request on one clock: in line (grey), its prompt being read (red, prefill), its answer being
written (blue, decode), its answer stalled while another prompt is read (grey with a blue thread). A pause is a pink
band; inside it every request is waiting.

Usage:  python3 pip_timeline.py <run.json> --out run.png [--budget 8192] [--title "TP4/PP2 · 8K · 8 in flight"]
Needs matplotlib. All numbers come from pip_waves."""
from __future__ import annotations

import argparse
import itertools
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.ticker import FixedLocator

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))     # find the sibling modules, also under python3 -I
import pip_waves as pw

# The note's palette: red and blue pass the colour-vision check all-pairs; grey is the neutral "waiting" state.
WAIT, RED, BLUE, PINK, INK, INK2, OX = "#C9C2B6", "#9b1c1c", "#1c4f95", "#F4E9E9", "#1A1A1A", "#4A4744", "#8B0000"
COL = {"line": WAIT, "stall": WAIT, "read": RED, "write": BLUE}
plt.rcParams.update({"font.size": 7.2, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#BDB7AE",
                     "axes.linewidth": 0.6, "xtick.labelsize": 6.6, "ytick.labelsize": 6.6, "savefig.dpi": 300})


def check_layout(fig):
    """Fail rather than overlap: text off the page or on other text."""
    fig.canvas.draw(); r = fig.canvas.get_renderer(); W, H = fig.get_size_inches() * fig.dpi; T = list(fig.texts)
    for ax in fig.axes:
        T += list(ax.texts) + ([ax.xaxis.label, ax.yaxis.label] if ax.axison else [])
    bb = [(t, t.get_window_extent(renderer=r)) for t in T if t.get_visible() and t.get_text().strip()]
    bad = [f"off the page: {t.get_text()[:40]!r}" for t, b in bb if b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1]
    bad += [f"overlap: {t1.get_text()[:30]!r} / {t2.get_text()[:30]!r}" for (t1, b1), (t2, b2) in itertools.combinations(bb, 2)
            if min(b1.x1, b2.x1) - max(b1.x0, b2.x0) > 1 and min(b1.y1, b2.y1) - max(b1.y0, b2.y0) > 1]
    if bad: raise SystemExit("layout: " + "; ".join(bad))


def draw(path, out, budget=8192, title=None):
    run = pw.load(path); a = pw.analyze(path, budget, with_engine=False); p = a["pause"]
    pi = (p["at_s"], p["at_s"] + p["silence_s"]) if p["is_pause"] else None
    rows = pw.phases(run, pi); e = pw.engine(rows, run["C"]); T = e["T"] * 1.01
    n = run["n"]; h = 2.4 + min(n, 40) * 0.075
    fig = plt.figure(figsize=(7.2, h))
    fig.text(0.01, 0.985, title or os.path.basename(path), fontsize=8.6, fontweight="bold", color=INK, va="top")
    sub = (f"{n} requests · {run['C']} in flight · {run['input_len']:,}-token prompts · {run['output_len']}-token answers · "
           f"answers stalled {100 * a['stalls']['stall_share']:.0f}% of their time · prompts read at once {e['reads_at_once']:.1f}"
           + (f" · PAUSE {p['silence_s']:.1f} s" if pi else ""))
    fig.text(0.01, 0.985 - 0.32 / h, sub, fontsize=6.3, color=INK2, va="top")
    x = 0.01; y = 0.985 - 0.58 / h
    for lab, k in (("in line", "line"), ("prompt being read (prefill)", "read"), ("answer being written (decode)", "write"),
                   ("answer stalled", "stall")) + ((("pause: nothing moves", "pause"),) if pi else ()):
        fig.add_artist(plt.Rectangle((x, y - 0.05 / h), 0.016, 0.1 / h, transform=fig.transFigure, color=PINK if k == "pause" else COL[k]))
        if k == "stall": fig.add_artist(plt.Line2D([x, x + 0.016], [y, y], transform=fig.transFigure, color=BLUE, linewidth=1.0))
        t = fig.text(x + 0.021, y, lab, fontsize=6.0, color=INK2, va="center"); fig.canvas.draw()
        x = t.get_window_extent(renderer=fig.canvas.get_renderer()).x1 / (7.2 * fig.dpi) + 0.018
    top = 1 - 0.85 / h; rows_h = top - 0.55 / h - 0.62 / h
    axr = fig.add_axes([0.1, top - 0.22 / h, 0.87, 0.2 / h]); axw = fig.add_axes([0.1, top - 0.55 / h, 0.87, 0.3 / h])
    ax = fig.add_axes([0.1, 0.42 / h, 0.87, rows_h])
    axr.fill_between(e["t"], e["reading"], step="post", color=RED, linewidth=0)
    axw.fill_between(e["t"], e["writing"], step="post", color=BLUE, linewidth=0)
    axw.fill_between(e["t"], e["writing"], [a_ + b_ for a_, b_ in zip(e["writing"], e["stalled"])], step="post", color=WAIT, linewidth=0)
    for axs, top_, lab in ((axr, max(1, e["max_reads"]), "read"), (axw, run["C"], "answers")):
        axs.set_xlim(0, T); axs.set_ylim(0, top_ * 1.08); axs.set_xticks([]); axs.spines["bottom"].set_visible(False)
        axs.yaxis.set_major_locator(FixedLocator([0, top_])); axs.tick_params(labelsize=5.4, length=1.5, pad=1)
        axs.set_ylabel(lab, rotation=0, ha="right", va="center", fontsize=5.6, labelpad=8)
        if pi: axs.axvspan(*pi, color=PINK, zorder=0)
    lw = max(1.2, min(6.5, 140 / max(n, 1)))
    for k, z in (("line", 2), ("stall", 2), ("read", 3), ("write", 3)):
        segs = [[(x0, i), (x1, i)] for i, r in enumerate(rows) for x0, x1, kk in r["seg"] if kk == k and x1 > x0]
        ax.add_collection(LineCollection(segs, colors=COL[k], linewidths=lw, capstyle="butt", zorder=z))
    thread = [[(x0, i), (x1, i)] for i, r in enumerate(rows) for x0, x1, kk in r["seg"] if kk == "stall" and x1 > x0]
    ax.add_collection(LineCollection(thread, colors=BLUE, linewidths=max(0.5, lw * 0.16), capstyle="butt", zorder=4))
    if pi: ax.axvspan(*pi, color=PINK, zorder=0)
    ax.set_xlim(0, T); ax.set_ylim(n - 0.4, -0.7); ax.set_yticks([]); ax.set_ylabel(f"{n} requests, in the order sent", fontsize=6.2)
    ax.set_xlabel("seconds from the first request", fontsize=6.4)
    check_layout(fig); fig.savefig(out, facecolor="white"); plt.close(fig)
    return a


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("--out", required=True)
    ap.add_argument("--budget", type=int, default=8192); ap.add_argument("--title")
    args = ap.parse_args(); a = draw(args.run, args.out, args.budget, args.title); print(f"wrote {args.out}")
