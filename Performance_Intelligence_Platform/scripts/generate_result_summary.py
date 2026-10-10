#!/usr/bin/env python3
"""generate_result_summary: Post-run Markdown report generator for the
Performance Intelligence Platform.

Reads the continuous_batching_manifest.json (or per-step manifest files)
and produces:
  1. Per-block BLOCK_<N>_SUMMARY.md files inside each case directory.
  2. A master RESULT_SUMMARY.md combining all blocks into a single report.

Usage:
  python3 generate_result_summary.py <run_output_dir>
  python3 generate_result_summary.py --manifest <path_to_manifest.json>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ts(epoch: float | None) -> str:
    if epoch is None:
        return "N/A"
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _dur(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "N/A"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _fmt(v, precision: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{precision}f}"
    return str(v)


def _safe_get(d: dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


# ---------------------------------------------------------------------------
# Result extraction from vLLM bench JSON
# ---------------------------------------------------------------------------
def _load_bench_result(case_dir: Path, bench_name: str) -> dict:
    """Try to load result JSON from a benchmark subdirectory."""
    bdir = case_dir / bench_name
    if not bdir.is_dir():
        return {}
    # Try common patterns
    for pattern in (f"{bench_name}.json", "result.json", "*.json"):
        for f in bdir.glob(pattern):
            try:
                return json.loads(f.read_text())
            except Exception:
                continue
    return {}


def _extract_metrics(result: dict) -> dict:
    """Extract key performance metrics from a vLLM bench serve result."""
    metrics = {}
    # Standard vLLM bench serve output keys
    for key in (
        "request_throughput", "output_throughput", "total_token_throughput",
        "mean_ttft_ms", "median_ttft_ms", "p99_ttft_ms",
        "mean_tpot_ms", "median_tpot_ms", "p99_tpot_ms",
        "mean_itl_ms", "median_itl_ms", "p99_itl_ms",
        "mean_e2el_ms", "median_e2el_ms", "p99_e2el_ms",
        "completed", "total_input", "total_output",
        "duration", "total_input_tokens", "total_output_tokens",
    ):
        if key in result:
            metrics[key] = result[key]
    return metrics


# ---------------------------------------------------------------------------
# Markdown generators
# ---------------------------------------------------------------------------
BLOCK_NAMES = {
    1: "Two Long Prompts Side-by-Side (Chunk Cap vs Big Step)",
    2: "Step Budget Sweep (4K, 8K, 16K, 32K)",
    3: "Request Cap Binding (max-num-seqs 16, 32, 64)",
    4: "Mixed Traffic Concurrent Streams",
    5: "Memory Pressure KV Limits",
    6: "Long Answers Decode Scaling",
    7: "Steady Arrivals (Poisson / Fixed-Rate)",
}


def _bench_metrics_table(bench: dict, result_metrics: dict) -> str:
    """Render a single benchmark's metrics as a Markdown table."""
    lines = []
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")

    # Config rows
    if bench.get("input"):
        lines.append(f"| Input Tokens | {bench['input']:,} |")
    if bench.get("output"):
        lines.append(f"| Output Tokens | {bench['output']:,} |")
    if bench.get("concurrency"):
        lines.append(f"| Concurrency | {bench['concurrency']} |")
    if bench.get("prompts"):
        lines.append(f"| Num Prompts | {bench['prompts']} |")
    if bench.get("request_rate"):
        lines.append(f"| Request Rate | {bench['request_rate']} rps |")

    # Result rows
    if result_metrics:
        lines.append(f"| **Request Throughput** | **{_fmt(result_metrics.get('request_throughput'))} req/s** |")
        lines.append(f"| **Output Throughput** | **{_fmt(result_metrics.get('output_throughput'))} tok/s** |")
        lines.append(f"| Total Token Throughput | {_fmt(result_metrics.get('total_token_throughput'))} tok/s |")
        lines.append(f"| Mean TTFT | {_fmt(result_metrics.get('mean_ttft_ms'))} ms |")
        lines.append(f"| P99 TTFT | {_fmt(result_metrics.get('p99_ttft_ms'))} ms |")
        lines.append(f"| Mean TPOT | {_fmt(result_metrics.get('mean_tpot_ms'))} ms |")
        lines.append(f"| P99 TPOT | {_fmt(result_metrics.get('p99_tpot_ms'))} ms |")
        lines.append(f"| Mean ITL | {_fmt(result_metrics.get('mean_itl_ms'))} ms |")
        lines.append(f"| P99 ITL | {_fmt(result_metrics.get('p99_itl_ms'))} ms |")
        lines.append(f"| Mean E2E Latency | {_fmt(result_metrics.get('mean_e2el_ms'))} ms |")
        lines.append(f"| P99 E2E Latency | {_fmt(result_metrics.get('p99_e2el_ms'))} ms |")
        lines.append(f"| Completed | {_fmt(result_metrics.get('completed'))} |")
    else:
        lines.append("| *Results* | *Not available (dry-run or not yet collected)* |")

    return "\n".join(lines)


def _mixed_traffic_table(case_dir: Path, bench_name: str) -> str:
    """Render mixed traffic analysis results if available."""
    bdir = case_dir / bench_name
    analysis_path = bdir / "mixed_analysis.json"
    if not analysis_path.exists():
        return "> Mixed traffic analysis file not found.\n"

    try:
        data = json.loads(analysis_path.read_text())
    except Exception:
        return "> Failed to parse mixed_analysis.json.\n"

    lines = []
    lines.append("| Stream | Metric | Value |")
    lines.append("|--------|--------|-------|")
    for stream_key in ("short", "long"):
        s = data.get(stream_key, {})
        label = stream_key.capitalize()
        lines.append(f"| {label} | Throughput | {_fmt(s.get('request_throughput'))} req/s |")
        lines.append(f"| {label} | Mean TTFT | {_fmt(s.get('mean_ttft_ms'))} ms |")
        lines.append(f"| {label} | P99 TTFT | {_fmt(s.get('p99_ttft_ms'))} ms |")
        lines.append(f"| {label} | Mean TPOT | {_fmt(s.get('mean_tpot_ms'))} ms |")

    if "ttft_penalty_pct" in data:
        lines.append(f"| **Penalty** | TTFT Short Penalty | **{_fmt(data['ttft_penalty_pct'])}%** |")
    if "stall_detected" in data:
        lines.append(f"| **Stall** | Stall Detected | **{data['stall_detected']}** |")

    return "\n".join(lines)


def generate_case_block(case: dict, case_dir: Path, is_dry_run: bool = False) -> str:
    """Generate Markdown content for a single case."""
    md = []
    md.append(f"### Case: `{case['name']}`")
    md.append(f"**Purpose:** {case.get('purpose', 'N/A')}")
    md.append("")

    # Server config table
    md.append("**Server Configuration:**")
    md.append("")
    md.append("| Parameter | Value |")
    md.append("|-----------|-------|")
    md.append(f"| TP | {case.get('tp', '—')} |")
    md.append(f"| PP | {case.get('pp', 1)} |")
    md.append(f"| max_num_batched_tokens | {case.get('max_num_batched_tokens', '—'):,} |")
    if case.get("max_num_seqs"):
        md.append(f"| max_num_seqs | {case['max_num_seqs']} |")
    if case.get("long_prefill_token_threshold"):
        md.append(f"| long_prefill_token_threshold | {case['long_prefill_token_threshold']:,} |")
    if case.get("kv_cache_memory_bytes"):
        gib = case["kv_cache_memory_bytes"] / (1024 ** 3)
        md.append(f"| kv_cache_memory_bytes | {case['kv_cache_memory_bytes']:,} ({gib:.1f} GiB) |")
    md.append("")

    # Timing
    server_start = case.get("server_start")
    server_ready = case.get("server_ready")
    server_end = case.get("server_end")
    if server_start and server_ready:
        md.append(f"**Server startup time:** {_dur(server_ready - server_start)}")
    if server_start and server_end:
        md.append(f"**Total case wall time:** {_dur(server_end - server_start)}")
    md.append("")

    if case.get("error"):
        md.append(f"> ⚠️ **Error:** `{case['error']}`")
        md.append("")

    # Benchmarks
    benchmarks = case.get("benchmarks", [])
    if not benchmarks:
        md.append("*No benchmarks executed.*")
        return "\n".join(md)

    for bi, bench in enumerate(benchmarks):
        bench_name = bench.get("name", f"bench_{bi}")
        status = bench.get("status", "UNKNOWN")
        status_icon = "✅" if status == "COMPLETED" else ("📝" if status == "DRY_RUN_PLANNED" else "❌")
        md.append(f"#### {status_icon} Benchmark: `{bench_name}` — {status}")
        md.append("")

        if bench.get("start") and bench.get("end"):
            md.append(f"*Duration: {_dur(bench['end'] - bench['start'])}*")
            md.append("")

        # Mixed traffic special handling
        if case.get("mixed_traffic"):
            md.append(_mixed_traffic_table(case_dir, bench_name))
        else:
            result_data = _load_bench_result(case_dir, bench_name)
            result_metrics = _extract_metrics(result_data)
            md.append(_bench_metrics_table(bench, result_metrics))

        md.append("")

    return "\n".join(md)


def generate_block_summary(block_num: int, cases: list[dict], out_dir: Path, is_dry_run: bool = False) -> str:
    """Generate a full block summary and write BLOCK_<N>_SUMMARY.md."""
    block_name = BLOCK_NAMES.get(block_num, f"Block {block_num}")

    md = []
    md.append(f"## Block {block_num}: {block_name}")
    md.append("")
    md.append(f"*{len(cases)} case(s) executed*")
    md.append("")

    for case in cases:
        case_dir = out_dir / case["name"]
        md.append(generate_case_block(case, case_dir, is_dry_run))
        md.append("")
        md.append("---")
        md.append("")

    block_md = "\n".join(md)

    # Write per-block summary
    block_file = out_dir / f"BLOCK_{block_num}_SUMMARY.md"
    block_file.write_text(block_md, encoding="utf-8")
    print(f"  Written: {block_file}")

    return block_md


def generate_master_summary(manifest: dict, out_dir: Path) -> Path:
    """Generate the master RESULT_SUMMARY.md from a full manifest."""
    model = manifest.get("model", "unknown")
    started = manifest.get("started")
    ended = manifest.get("ended")
    blocks_selected = manifest.get("blocks_selected", "all")
    cases = manifest.get("cases", [])

    is_dry = all(
        b.get("status") == "DRY_RUN_PLANNED"
        for c in cases
        for b in c.get("benchmarks", [])
    ) if cases else False

    # Group cases by block
    blocks: dict[int, list[dict]] = {}
    for c in cases:
        bnum = c.get("block", 0)
        blocks.setdefault(bnum, []).append(c)

    # Header
    md = []
    md.append("# 📊 Continuous Batching Benchmark — Result Summary")
    md.append("")
    md.append("| Property | Value |")
    md.append("|----------|-------|")
    md.append(f"| Model | `{model}` |")
    md.append(f"| Blocks Selected | `{blocks_selected}` |")
    md.append(f"| Total Cases | {len(cases)} |")
    md.append(f"| Total Benchmarks | {sum(len(c.get('benchmarks', [])) for c in cases)} |")
    md.append(f"| Started | {_ts(started)} |")
    md.append(f"| Ended | {_ts(ended)} |")
    if started and ended:
        md.append(f"| Total Duration | {_dur(ended - started)} |")
    if is_dry:
        md.append(f"| Mode | 📝 **DRY RUN** (no GPU workloads launched) |")
    md.append("")

    # Status summary
    completed = sum(1 for c in cases for b in c.get("benchmarks", []) if b.get("status") == "COMPLETED")
    failed = sum(1 for c in cases for b in c.get("benchmarks", []) if b.get("status") == "FAILED")
    planned = sum(1 for c in cases for b in c.get("benchmarks", []) if b.get("status") == "DRY_RUN_PLANNED")
    total = completed + failed + planned

    if total > 0:
        md.append("### Execution Summary")
        md.append("")
        md.append(f"- ✅ Completed: **{completed}** / {total}")
        if failed:
            md.append(f"- ❌ Failed: **{failed}** / {total}")
        if planned:
            md.append(f"- 📝 Planned (dry-run): **{planned}** / {total}")
        md.append("")

    # Errors
    errors = [(c["name"], c["error"]) for c in cases if c.get("error")]
    if errors:
        md.append("### ⚠️ Errors")
        md.append("")
        for name, err in errors:
            md.append(f"- **{name}**: `{err}`")
        md.append("")

    md.append("---")
    md.append("")

    # Per-block detail
    for bnum in sorted(blocks.keys()):
        block_md = generate_block_summary(bnum, blocks[bnum], out_dir, is_dry)
        md.append(block_md)
        md.append("")

    # Footer
    md.append("---")
    md.append("")
    md.append(f"*Generated by Performance Intelligence Platform at {_ts(time.time())}*")
    md.append(f"*Artifacts directory: `{out_dir}`*")
    md.append("")

    out_path = out_dir / "RESULT_SUMMARY.md"
    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"\n[OK] Master summary written: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Generate Markdown result summaries from benchmark manifests.")
    ap.add_argument("run_dir", nargs="?", help="Path to the run output directory containing continuous_batching_manifest.json")
    ap.add_argument("--manifest", help="Explicit path to a manifest JSON file (overrides run_dir auto-discovery)")
    args = ap.parse_args()

    if args.manifest:
        manifest_path = Path(args.manifest)
    elif args.run_dir:
        manifest_path = Path(args.run_dir) / "continuous_batching_manifest.json"
    else:
        print("Error: Provide either a run directory or --manifest path.", file=sys.stderr)
        sys.exit(1)

    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    out_dir = manifest_path.parent
    generate_master_summary(manifest, out_dir)


if __name__ == "__main__":
    main()
