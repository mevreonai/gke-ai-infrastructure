#!/usr/bin/env python3
"""
03_run_benchmarks.py — DeepSeek V4.1 Flash Performance Characterization Runner

Executes all benchmark cases from config.json across network conditions
(Native, 100Gbps, 20Gbps) on kimi-node-0.

Model:  deepseek-ai/DeepSeek-V4.1-Flash
Server: Already running on localhost:8000 (started by 02_start_vllm_server.sh)

Usage:
    sudo python3 03_run_benchmarks.py                # Run all conditions + all cases
    sudo python3 03_run_benchmarks.py --condition native  # Run only native
    sudo python3 03_run_benchmarks.py --group tp8_context_baseline  # Run only one group
    sudo python3 03_run_benchmarks.py --dry-run      # Print commands without executing
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

# ─── Constants ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
RESULTS_DIR = SCRIPT_DIR / "results"
PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"
MODEL_NAME = "deepseek-ai/DeepSeek-V4.1-Flash"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def log(msg: str, level: str = "INFO"):
    """Timestamped log output."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    prefix = {"INFO": "ℹ", "OK": "✔", "WARN": "⚠", "FAIL": "✘", "RUN": "▶"}.get(level, "·")
    print(f"[{ts}] {prefix} {msg}", flush=True)


def check_server_ready() -> bool:
    """Verify the vLLM server is up and serving the model."""
    try:
        with urlopen(f"{BASE_URL}/v1/models", timeout=10) as r:
            if r.status == 200:
                data = json.loads(r.read().decode("utf-8", "replace"))
                models = [m.get("id", "") for m in data.get("data", [])]
                if MODEL_NAME in models:
                    return True
                log(f"Server is up but model '{MODEL_NAME}' not found. Available: {models}", "WARN")
                return False
    except Exception as e:
        log(f"Server not reachable: {e}", "FAIL")
        return False
    return False


def apply_network_condition(condition: dict):
    """Apply or clear network shaping via tc."""
    name = condition["name"]
    tc_cmd = condition.get("tc_command")

    # Always clear first
    subprocess.run(["tc", "qdisc", "del", "dev", "eth0", "root"],
                   capture_output=True, text=True)
    time.sleep(1)

    if tc_cmd is None:
        log(f"Network condition: {name} — no shaping applied (native)", "OK")
    else:
        log(f"Network condition: {name} — applying: {tc_cmd}", "RUN")
        result = subprocess.run(tc_cmd.split(), capture_output=True, text=True)
        if result.returncode != 0:
            log(f"tc command failed: {result.stderr.strip()}", "WARN")
            # Try to detect the correct interface
            iface_result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True
            )
            if iface_result.returncode == 0:
                parts = iface_result.stdout.strip().split()
                if "dev" in parts:
                    real_iface = parts[parts.index("dev") + 1]
                    log(f"Retrying with detected interface: {real_iface}", "RUN")
                    adjusted_cmd = tc_cmd.replace("eth0", real_iface)
                    subprocess.run(adjusted_cmd.split(), capture_output=True, text=True)
        else:
            log(f"Network shaping applied successfully", "OK")


def clear_network_shaping():
    """Remove all tc shaping rules."""
    subprocess.run(["tc", "qdisc", "del", "dev", "eth0", "root"],
                   capture_output=True, text=True)
    # Also try to detect and clear on real interface
    try:
        result = subprocess.run(["ip", "route", "show", "default"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if "dev" in parts:
                real_iface = parts[parts.index("dev") + 1]
                if real_iface != "eth0":
                    subprocess.run(["tc", "qdisc", "del", "dev", real_iface, "root"],
                                 capture_output=True, text=True)
    except Exception:
        pass


def run_warmup(case: dict, case_dir: Path) -> dict:
    """Run warmup requests before the measured benchmark."""
    n = int(case.get("warmups", 0))
    if n <= 0:
        return {"ran": False}

    log(f"  Running {n} warmup request(s)...", "RUN")
    cmd = build_bench_command(case, case_dir, "warmup.json", measured=False, num_prompts=n)
    warmup_log = case_dir / "warmup_stdout.log"

    t0 = time.time()
    with warmup_log.open("w") as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
    t1 = time.time()

    return {"ran": True, "exit_code": rc, "duration_s": round(t1 - t0, 2)}


def build_bench_command(case: dict, outdir: Path, result_file: str,
                         measured: bool = True, num_prompts: int | None = None) -> list:
    """Build the vllm bench serve command for a single case."""
    prompts = num_prompts if num_prompts is not None else case["prompts"]
    concurrency = min(case["concurrency"], prompts)

    cmd = [
        "docker", "exec", "vllm-deepseek-perf",
        "vllm", "bench", "serve",
        "--backend", "openai",
        "--host", "127.0.0.1",
        "--port", str(PORT),
        "--endpoint", "/v1/completions",
        "--model", MODEL_NAME,
        "--trust-remote-code",
        "--dataset-name", "random",
        "--random-input-len", str(case["input"]),
        "--random-output-len", str(case["output"]),
        "--random-range-ratio", "0",
        "--num-prompts", str(prompts),
        "--max-concurrency", str(concurrency),
        "--ignore-eos",
        "--num-warmups", "0",
        "--percentile-metrics", "ttft,tpot,itl,e2el",
        "--metric-percentiles", "50,95,99",
        "--seed", str(hash(case["name"]) % 100000),
    ]

    if measured:
        # Save results inside the container then copy out
        cmd += [
            "--save-result",
            "--save-detailed",
            "--result-dir", "/tmp/bench_results",
            "--result-filename", result_file,
        ]

    return cmd


def run_single_case(case: dict, group_name: str, condition_name: str,
                     results_base: Path, dry_run: bool = False) -> dict:
    """Run a single benchmark case and return the result record."""
    case_dir = results_base / condition_name / group_name
    case_dir.mkdir(parents=True, exist_ok=True)

    case_name = case["name"]
    result_file = f"{case_name}.json"

    record = {
        "name": case_name,
        "group": group_name,
        "condition": condition_name,
        "input_tokens": case["input"],
        "output_tokens": case["output"],
        "concurrency": case["concurrency"],
        "prompts": case["prompts"],
    }

    if dry_run:
        cmd = build_bench_command(case, case_dir, result_file)
        record["command"] = " ".join(cmd)
        record["status"] = "DRY_RUN"
        log(f"  [DRY RUN] {case_name}: {' '.join(cmd[:15])}...", "INFO")
        return record

    # Run warmup
    warmup = run_warmup(case, case_dir)
    record["warmup"] = warmup
    time.sleep(1)

    # Run benchmark
    log(f"  Benchmarking: {case_name} (input={case['input']}, output={case['output']}, "
        f"concurrency={case['concurrency']}, prompts={case['prompts']})", "RUN")

    cmd = build_bench_command(case, case_dir, result_file, measured=True)
    stdout_log = case_dir / f"{case_name}_stdout.log"
    (case_dir / "COMMAND.txt").write_text(" ".join(cmd) + "\n")

    t0 = time.time()
    with stdout_log.open("w") as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
    t1 = time.time()

    record["exit_code"] = rc
    record["duration_s"] = round(t1 - t0, 2)
    record["status"] = "COMPLETED" if rc == 0 else "FAILED"

    # Copy result from container
    if rc == 0:
        copy_cmd = [
            "docker", "cp",
            f"vllm-deepseek-perf:/tmp/bench_results/{result_file}",
            str(case_dir / result_file),
        ]
        subprocess.run(copy_cmd, capture_output=True)

        result_path = case_dir / result_file
        if result_path.exists():
            try:
                result_data = json.loads(result_path.read_text())
                # Extract key metrics
                for key in ("mean_ttft_ms", "median_ttft_ms", "p99_ttft_ms",
                           "mean_tpot_ms", "median_tpot_ms", "p99_tpot_ms",
                           "mean_itl_ms", "median_itl_ms", "p99_itl_ms",
                           "mean_e2el_ms",
                           "request_throughput", "output_throughput",
                           "total_input", "total_output",
                           "completed", "total_token_throughput"):
                    if key in result_data:
                        record[key] = result_data[key]
                log(f"  Result: throughput={result_data.get('output_throughput', '?'):.1f} tok/s, "
                    f"TTFT_p50={result_data.get('median_ttft_ms', '?'):.1f}ms, "
                    f"TPOT_p50={result_data.get('median_tpot_ms', '?'):.1f}ms", "OK")
            except Exception as e:
                log(f"  Could not parse result JSON: {e}", "WARN")
        else:
            log(f"  Result file not found after copy", "WARN")
    else:
        log(f"  Benchmark FAILED with exit code {rc}", "FAIL")
        log(f"  Check: {stdout_log}", "INFO")

    return record


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DeepSeek V4.1 Flash — Performance Benchmark Runner")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Path to config.json")
    parser.add_argument("--condition", action="append", default=[],
                       help="Run only specific network condition(s): native, 100gbps, 20gbps")
    parser.add_argument("--group", action="append", default=[],
                       help="Run only specific benchmark group(s)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print commands without executing")
    parser.add_argument("--output", default=str(RESULTS_DIR),
                       help="Output directory for results")
    args = parser.parse_args()

    # Load config
    cfg = json.loads(Path(args.config).read_text())
    log(f"Loaded config: {Path(args.config).name}")
    log(f"Model: {cfg['model']}")

    # Filter conditions
    conditions = cfg["network_conditions"]
    if args.condition:
        conditions = [c for c in conditions if c["name"] in args.condition]
        if not conditions:
            log(f"No matching conditions for: {args.condition}", "FAIL")
            sys.exit(1)

    # Filter groups
    groups = cfg["benchmark_groups"]
    if args.group:
        groups = [g for g in groups if g["name"] in args.group]
        if not groups:
            log(f"No matching groups for: {args.group}", "FAIL")
            sys.exit(1)

    total_cases = sum(len(g["cases"]) for g in groups) * len(conditions)
    log(f"Plan: {len(groups)} group(s) × {len(conditions)} condition(s) = {total_cases} total runs")

    # Verify server
    if not args.dry_run:
        if not check_server_ready():
            log("vLLM server is not ready. Run 02_start_vllm_server.sh first.", "FAIL")
            sys.exit(1)
        log("vLLM server is ready", "OK")

    results_base = Path(args.output)
    results_base.mkdir(parents=True, exist_ok=True)
    all_records = []
    run_count = 0

    manifest = {
        "schema_version": 1,
        "model": cfg["model"],
        "evidence_class": cfg["evidence_class"],
        "target_node": cfg["target_node"],
        "started": time.time(),
        "conditions_run": [c["name"] for c in conditions],
        "groups_run": [g["name"] for g in groups],
        "records": [],
    }

    try:
        for ci, condition in enumerate(conditions):
            cond_name = condition["name"]
            cond_label = condition["label"]

            log(f"\n{'='*60}")
            log(f"NETWORK CONDITION [{ci+1}/{len(conditions)}]: {cond_label}")
            log(f"{'='*60}")

            if not args.dry_run:
                apply_network_condition(condition)
                time.sleep(3)  # Let shaping settle

            for gi, group in enumerate(groups):
                group_name = group["name"]
                log(f"\n  Group [{gi+1}/{len(groups)}]: {group_name}")
                log(f"  Purpose: {group['purpose']}")

                for case in group["cases"]:
                    run_count += 1
                    log(f"\n  ── Run {run_count}/{total_cases} ──")

                    record = run_single_case(
                        case, group_name, cond_name, results_base, args.dry_run
                    )
                    all_records.append(record)
                    manifest["records"].append(record)

                    # Small pause between cases
                    if not args.dry_run:
                        time.sleep(2)

    except KeyboardInterrupt:
        log("\nInterrupted by user!", "WARN")
    finally:
        # Always clean up network shaping
        if not args.dry_run:
            log("\nClearing network shaping...", "RUN")
            clear_network_shaping()
            log("Network shaping cleared", "OK")

    # Save manifest
    manifest["ended"] = time.time()
    manifest["total_duration_s"] = round(manifest["ended"] - manifest["started"], 2)
    manifest["total_runs"] = len(all_records)
    manifest["completed_runs"] = sum(1 for r in all_records if r.get("status") == "COMPLETED")
    manifest["failed_runs"] = sum(1 for r in all_records if r.get("status") == "FAILED")

    manifest_path = results_base / "benchmark_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    log(f"\n{'='*60}")
    log(f"BENCHMARK COMPLETE")
    log(f"  Total runs:     {manifest['total_runs']}")
    log(f"  Completed:      {manifest['completed_runs']}")
    log(f"  Failed:         {manifest['failed_runs']}")
    log(f"  Total duration: {manifest['total_duration_s']:.1f}s")
    log(f"  Manifest:       {manifest_path}")
    log(f"{'='*60}")


if __name__ == "__main__":
    main()
