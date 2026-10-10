#!/usr/bin/env python3
"""run_continuous_batching: configurable runner for Task 2 continuous batching benchmark blocks.

Executes Blocks 1-7:
  1. Two long prompts at once (Chunk cap vs big step)
  2. Step budget sweep (4K, 8K, 16K, 32K on TP4/PP1 and TP4/PP2)
  3. Request cap binding (max-num-seqs 16, 32, 64)
  4. Mixed traffic concurrent streams (short + long)
  5. Memory pressure under load (KV cache limit)
  6. Long answers (1024, 2048 decode steps)
  7. Steady arrivals (Poisson / fixed-rate on two servers)

Usage:
  python3 run_continuous_batching.py --out <dir> [--blocks 1,2,3] [--dry-run] [--model <id>]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v5_runner_lib import *


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cases", default=str(Path(__file__).with_name("continuous_batching_cases.json")))
    ap.add_argument("--out", required=True)
    ap.add_argument("--blocks", default="all", help="Comma-separated block numbers (e.g. 1,2,3 or all)")
    ap.add_argument("--case", action="append", default=[], help="Run specific case by name")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--startup-timeout", type=int, default=3600)
    ap.add_argument("--seed-base", type=int, default=6000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(Path(args.cases).read_text())
    model = os.environ.get("MODEL", cfg["model"])
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    # Filter cases by block or name
    selected_blocks = set()
    if args.blocks != "all":
        selected_blocks = set(b.strip() for b in args.blocks.split(","))

    cases_to_run = []
    for c in cfg["cases"]:
        b_str = str(c.get("block", 0))
        if args.case and c["name"] in args.case:
            cases_to_run.append(c)
        elif not args.case and (args.blocks == "all" or b_str in selected_blocks):
            cases_to_run.append(c)

    if not cases_to_run:
        print(f"No cases matched selection (blocks: {args.blocks}, cases: {args.case})")
        sys.exit(0)

    print(f"\n================================================================================")
    print(f"  CONTINUOUS BATCHING BENCHMARK SUITE")
    print(f"  Cases selected : {len(cases_to_run)}")
    print(f"  Blocks filter  : {args.blocks}")
    print(f"  Model          : {model}")
    print(f"  Dry Run        : {args.dry_run}")
    print(f"================================================================================\n")

    vllm = shutil.which("vllm")
    if not vllm and not args.dry_run:
        raise SystemExit("vllm CLI binary not found on PATH")

    py = sys.executable
    sampler = str(Path(__file__).with_name("09_metrics_sampler.py").resolve())
    serve_help = cli_help(vllm, ["serve"]) if vllm else "--tensor-parallel-size --pipeline-parallel-size --max-model-len --max-num-batched-tokens --kv-cache-dtype --revision --distributed-executor-backend --gpu-memory-utilization --no-enable-prefix-caching --enable-prefix-caching --long-prefill-token-threshold --max-num-seqs --max-num-active-seqs --kv-cache-memory-bytes"
    bench_help = cli_help(vllm, ["bench", "serve"]) if vllm else "--dataset-name --num-prompts --max-concurrency --num-warmups --request-rate --burstiness --probe-request-rate --metadata"

    top_manifest = {
        "suite": "continuous_batching",
        "started": time.time(),
        "model": model,
        "blocks_selected": args.blocks,
        "cases": []
    }

    for ci, case in enumerate(cases_to_run):
        cdir = out / case["name"]
        cdir.mkdir(parents=True, exist_ok=True)
        print(f"\n[{ci+1}/{len(cases_to_run)}] Case: {case['name']} (Block {case.get('block')})")
        print(f"  Purpose: {case.get('purpose')}")

        server_cmd = build_server_cmd(vllm, serve_help, cfg, case, model, args.port, distributed=(case.get("pp", 1) > 1))
        # Add chunk cap if specified
        if case.get("long_prefill_token_threshold"):
            add_if_supported(server_cmd, serve_help, "--long-prefill-token-threshold", str(case["long_prefill_token_threshold"]))
        if case.get("scheduling_policy"):
            add_if_supported(server_cmd, serve_help, "--scheduling-policy", str(case["scheduling_policy"]))

        (cdir / "SERVER_COMMAND.txt").write_text(q(server_cmd) + "\n")
        case_rec = {
            "name": case["name"],
            "block": case.get("block"),
            "purpose": case.get("purpose"),
            "tp": case["tp"],
            "pp": case.get("pp", 1),
            "max_num_batched_tokens": case["max_num_batched_tokens"],
            "max_num_seqs": case.get("max_num_seqs"),
            "long_prefill_token_threshold": case.get("long_prefill_token_threshold"),
            "kv_cache_memory_bytes": case.get("kv_cache_memory_bytes"),
            "benchmarks": []
        }

        if args.dry_run:
            for b in case.get("benchmarks", []):
                case_rec["benchmarks"].append({**b, "status": "DRY_RUN_PLANNED"})
            top_manifest["cases"].append(case_rec)
            continue

        server_proc = None
        metrics_proc = None
        try:
            case_rec["server_start"] = time.time()
            server_proc = start_server_with_timestamp_logging(server_cmd, cdir / "server.log", os.environ.copy())
            models = wait_ready(f"http://127.0.0.1:{args.port}", server_proc, args.startup_timeout)
            case_rec["server_ready"] = time.time()
            (cdir / "resolved_models.json").write_text(json.dumps(models, indent=2))

            for bi, b in enumerate(case["benchmarks"]):
                bdir = cdir / b["name"]
                bdir.mkdir(exist_ok=True)
                
                # Check for Block 4 Mixed Traffic concurrent execution
                if case.get("mixed_traffic") and "short_stream" in b and "long_stream" in b:
                    print(f"  Executing Mixed Traffic streams concurrently...")
                    # Warmup on short stream
                    run_warmup(vllm, bench_help, model, args.port, b["short_stream"], bdir, args.seed_base + ci * 100 + bi * 10, os.environ.copy())
                    
                    s_cmd = build_bench_cmd(vllm, bench_help, model, args.port, b["short_stream"], bdir, "short_stream.json", args.seed_base + ci * 100 + 1, True)
                    l_cmd = build_bench_cmd(vllm, bench_help, model, args.port, b["long_stream"], bdir, "long_stream.json", args.seed_base + ci * 100 + 2, True)
                    
                    s_wall, s_mono = time.time(), time.monotonic()
                    with open(bdir / "short_stdout.log", "w") as s_log, open(bdir / "long_stdout.log", "w") as l_log:
                        p_short = subprocess.Popen(s_cmd, stdout=s_log, stderr=subprocess.STDOUT)
                        p_long = subprocess.Popen(l_cmd, stdout=l_log, stderr=subprocess.STDOUT)
                        p_short.wait()
                        p_long.wait()
                    
                    package_run_evidence(cdir, bdir, b["name"])
                    # Run mixed traffic analysis
                    mt_script = str(Path(__file__).with_name("pip_mixed_traffic.py"))
                    subprocess.call([py, mt_script, "--short", str(bdir / "short_stream.json"), "--long", str(bdir / "long_stream.json"), "--json", str(bdir / "mixed_analysis.json")])
                    case_rec["benchmarks"].append({**b, "status": "COMPLETED", "clock_wall": s_wall, "clock_mono": s_mono})
                    continue

                # Standard single-stream benchmark execution
                warm = run_warmup(vllm, bench_help, model, args.port, b, bdir, args.seed_base + ci * 1000 + bi * 10, os.environ.copy())
                (bdir / "warmup_manifest.json").write_text(json.dumps(warm, indent=2))
                
                # Metrics sampler
                metrics_cmd = [py, sampler, "--url", f"http://127.0.0.1:{args.port}/metrics", "--interval", "0.5",
                               "--out", str(bdir / "metrics_gpu.jsonl"), "--raw-prom", str(bdir / "metrics_raw.prom.log"), "--node-label", "node0"]
                metrics_proc = subprocess.Popen(metrics_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                time.sleep(1.0)

                result_file = f"{b['name']}.json"
                bench_cmd = build_bench_cmd(vllm, bench_help, model, args.port, b, bdir, result_file, args.seed_base + ci * 1000 + bi, True)
                (bdir / "COMMAND.txt").write_text(q(bench_cmd) + "\n")
                
                clock_wall, clock_mono = time.time(), time.monotonic()
                t0 = time.time()
                with open(bdir / "bench_stdout.log", "w") as log:
                    rc = subprocess.call(bench_cmd, stdout=log, stderr=subprocess.STDOUT)
                t1 = time.time()
                
                time.sleep(1.0)
                stop_proc(metrics_proc)
                metrics_proc = None

                package_run_evidence(cdir, bdir, b["name"])
                res_path = bdir / result_file
                result_data = parse_result(res_path)
                
                brec = {
                    **b,
                    "status": "COMPLETED" if rc == 0 else "FAILED",
                    "exit_code": rc,
                    "start": t0,
                    "end": t1,
                    "clock_wall": clock_wall,
                    "clock_mono": clock_mono,
                    "rank_in_session": bi,
                    "server_start": case_rec["server_start"],
                    "server_ready": case_rec["server_ready"],
                    "time_since_ready": t0 - case_rec["server_ready"],
                    "evidence_archive": str(bdir / f"evidence_{b['name']}.tar.gz")
                }
                case_rec["benchmarks"].append(brec)

        except Exception as e:
            case_rec["error"] = repr(e)
        finally:
            case_rec["server_end"] = time.time()
            if metrics_proc: stop_proc(metrics_proc)
            kill_process_group(server_proc)
            (cdir / "case_manifest.json").write_text(json.dumps(case_rec, indent=2))
            top_manifest["cases"].append(case_rec)

    top_manifest["ended"] = time.time()
    (out / "continuous_batching_manifest.json").write_text(json.dumps(top_manifest, indent=2))
    print(f"\nContinuous batching benchmark complete. Results written to: {out}")

    # Post-run scan and step-cost fit
    try:
        pip_scan_py = str(Path(__file__).with_name("pip_scan.py"))
        step_cost_py = str(Path(__file__).with_name("pip_step_cost.py"))
        subprocess.call([py, pip_scan_py, str(out), "--csv", str(out / "pause_scan.csv")])
        for cdir in out.glob("cb_*"):
            slog = cdir / "server.log"
            if slog.exists():
                subprocess.call([py, step_cost_py, str(slog), "--json", str(cdir / "step_cost_fit.json")])
    except Exception:
        pass


if __name__ == "__main__":
    main()
