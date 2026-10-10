#!/usr/bin/env python3
"""pip_step_cost: continuous batching step-cost model fitting.

Parses iteration lines in server.log:
  Iteration(N): X context requests, Y context tokens, Z generation requests, W generation tokens, iteration elapsed time: T ms, GPU KV cache usage: K%

Fits linear cost model per layout:
  T (ms) ≈ a + b * (generation_requests) + c * (context_tokens)

Reports:
  - Base step overhead: a (ms)
  - Marginal token decode cost: b (ms/answer)
  - Marginal prefill chunk cost: c (ms/prompt_token)
  - R² goodness of fit and RMSE error

Usage:
  python3 pip_step_cost.py <server.log> [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys


ITERATION_RE = re.compile(
    r"Iteration\(\d+\):\s*(\d+)\s*context\s*requests?,\s*(\d+)\s*context\s*tokens?,\s*(\d+)\s*generation\s*requests?,\s*(\d+)\s*generation\s*tokens?,\s*iteration\s*elapsed\s*time:\s*([\d\.]+)\s*ms",
    re.IGNORECASE
)


def parse_iterations(log_path: str):
    points = []
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = ITERATION_RE.search(line)
            if m:
                ctx_reqs = int(m.group(1))
                ctx_toks = int(m.group(2))
                gen_reqs = int(m.group(3))
                gen_toks = int(m.group(4))
                elapsed_ms = float(m.group(5))
                points.append({
                    "ctx_reqs": ctx_reqs,
                    "ctx_toks": ctx_toks,
                    "gen_reqs": gen_reqs,
                    "gen_toks": gen_toks,
                    "elapsed_ms": elapsed_ms
                })
    return points


def fit_linear_cost_model(points: list):
    n = len(points)
    if n < 5:
        return {"error": "Not enough iteration points (minimum 5 required)", "count": n}

    # Linear regression via least squares: Y = a + b*X1 + c*X2
    # Where Y = elapsed_ms, X1 = gen_reqs, X2 = ctx_toks
    # Normal equations: (X^T * X) * Beta = X^T * Y
    # Design matrix with column of 1s:
    X = [[1.0, float(p["gen_reqs"]), float(p["ctx_toks"])] for p in points]
    Y = [float(p["elapsed_ms"]) for p in points]

    # Compute X^T * X (3x3) and X^T * Y (3x1)
    XT_X = [[0.0] * 3 for _ in range(3)]
    XT_Y = [0.0] * 3

    for row_x, y in zip(X, Y):
        for i in range(3):
            XT_Y[i] += row_x[i] * y
            for j in range(3):
                XT_X[i][j] += row_x[i] * row_x[j]

    # Invert 3x3 matrix using Cramer's rule
    det = (
        XT_X[0][0] * (XT_X[1][1] * XT_X[2][2] - XT_X[1][2] * XT_X[2][1])
        - XT_X[0][1] * (XT_X[1][0] * XT_X[2][2] - XT_X[1][2] * XT_X[2][0])
        + XT_X[0][2] * (XT_X[1][0] * XT_X[2][1] - XT_X[1][1] * XT_X[2][0])
    )

    if abs(det) < 1e-12:
        return {"error": "Singular matrix (independent variables lack variance)", "count": n}

    inv = [
        [
            (XT_X[1][1] * XT_X[2][2] - XT_X[1][2] * XT_X[2][1]) / det,
            (XT_X[0][2] * XT_X[2][1] - XT_X[0][1] * XT_X[2][2]) / det,
            (XT_X[0][1] * XT_X[1][2] - XT_X[0][2] * XT_X[1][1]) / det,
        ],
        [
            (XT_X[1][2] * XT_X[2][0] - XT_X[1][0] * XT_X[2][2]) / det,
            (XT_X[0][0] * XT_X[2][2] - XT_X[0][2] * XT_X[2][0]) / det,
            (XT_X[0][2] * XT_X[1][0] - XT_X[0][0] * XT_X[1][2]) / det,
        ],
        [
            (XT_X[1][0] * XT_X[2][1] - XT_X[1][1] * XT_X[2][0]) / det,
            (XT_X[0][1] * XT_X[2][0] - XT_X[0][0] * XT_X[2][1]) / det,
            (XT_X[0][0] * XT_X[1][1] - XT_X[0][1] * XT_X[1][0]) / det,
        ]
    ]

    a = sum(inv[0][j] * XT_Y[j] for j in range(3))
    b = sum(inv[1][j] * XT_Y[j] for j in range(3))
    c = sum(inv[2][j] * XT_Y[j] for j in range(3))

    # Evaluate predictions, R^2, RMSE
    y_mean = sum(Y) / n
    ss_tot = sum((y - y_mean) ** 2 for y in Y)
    residuals = [y - (a + b * row[1] + c * row[2]) for row, y in zip(X, Y)]
    ss_res = sum(r ** 2 for r in residuals)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    rmse = math.sqrt(ss_res / n)

    return {
        "count": n,
        "a_base_overhead_ms": a,
        "b_decode_step_ms_per_ans": b,
        "c_prefill_ms_per_ctx_tok": c,
        "r2_score": r2,
        "rmse_ms": rmse,
        "formula": f"StepTime (ms) ≈ {a:.3f} + {b:.4f} * answers + {c:.6f} * prompt_tokens"
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("server_log", help="Path to server.log")
    ap.add_argument("--json", help="Path to save fit dictionary as JSON")
    args = ap.parse_args()

    points = parse_iterations(args.server_log)
    print(f"Extracted {len(points)} iteration data points from {args.server_log}")
    res = fit_linear_cost_model(points)
    if "error" in res:
        print(f"Fitting notice: {res['error']}")
    else:
        print(f"\nContinuous Batching Cost Model Fit (N={res['count']}):")
        print(f"  {res['formula']}")
        print(f"  Base step overhead (a) : {res['a_base_overhead_ms']:.3f} ms")
        print(f"  Decode step cost (b)   : {res['b_decode_step_ms_per_ans']:.4f} ms per answer in flight")
        print(f"  Prefill token cost (c) : {res['c_prefill_ms_per_ctx_tok'] * 1000:.4f} ms per 1K prompt tokens")
        print(f"  Goodness of Fit (R²)   : {res['r2_score']:.4f}")
        print(f"  RMSE Error             : {res['rmse_ms']:.3f} ms\n")

    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=2)


if __name__ == "__main__":
    main()
