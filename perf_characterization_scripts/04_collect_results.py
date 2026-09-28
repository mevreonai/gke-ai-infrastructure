#!/usr/bin/env python3
"""
04_collect_results.py — Aggregate benchmark results into CSV + summary

Reads all result JSONs from the results/ directory and generates:
  - results/summary.csv       — One row per benchmark run
  - results/SUMMARY.md        — Markdown report with key findings
  - results/comparison.json   — Machine-readable cross-condition comparison

Usage:
    python3 04_collect_results.py
    python3 04_collect_results.py --results-dir ./results
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS = SCRIPT_DIR / "results"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_result_json(path: Path) -> dict | None:
    """Parse a single vLLM benchmark result JSON file."""
    try:
        data = json.loads(path.read_text())
        return data
    except Exception:
        return None


def extract_metrics(data: dict) -> dict:
    """Extract the key performance metrics from a result JSON."""
    keys = [
        "mean_ttft_ms", "median_ttft_ms", "p99_ttft_ms",
        "mean_tpot_ms", "median_tpot_ms", "p99_tpot_ms",
        "mean_itl_ms", "median_itl_ms", "p99_itl_ms",
        "mean_e2el_ms", "median_e2el_ms", "p99_e2el_ms",
        "request_throughput", "output_throughput", "total_token_throughput",
        "completed", "total_input", "total_output",
        "duration",
    ]
    return {k: data.get(k) for k in keys if data.get(k) is not None}


def discover_results(results_dir: Path) -> list[dict]:
    """Walk the results directory and discover all result JSON files."""
    records = []
    conditions = ["native", "100gbps", "20gbps"]

    for condition in conditions:
        cond_dir = results_dir / condition
        if not cond_dir.exists():
            continue
        for group_dir in sorted(cond_dir.iterdir()):
            if not group_dir.is_dir():
                continue
            group_name = group_dir.name
            for json_file in sorted(group_dir.glob("*.json")):
                # Skip non-result files
                if json_file.name.startswith("warmup") or json_file.name == "COMMAND.txt":
                    continue
                data = parse_result_json(json_file)
                if data is None:
                    continue

                metrics = extract_metrics(data)
                record = {
                    "condition": condition,
                    "group": group_name,
                    "case": json_file.stem,
                    "file": str(json_file),
                    **metrics,
                }
                records.append(record)

    return records


def build_comparison(records: list[dict]) -> dict:
    """Build a cross-condition comparison for each (group, case) pair."""
    comparison = {}
    for r in records:
        key = f"{r['group']}/{r['case']}"
        if key not in comparison:
            comparison[key] = {}
        comparison[key][r["condition"]] = {
            "output_throughput": r.get("output_throughput"),
            "median_ttft_ms": r.get("median_ttft_ms"),
            "median_tpot_ms": r.get("median_tpot_ms"),
            "p99_ttft_ms": r.get("p99_ttft_ms"),
            "p99_tpot_ms": r.get("p99_tpot_ms"),
            "request_throughput": r.get("request_throughput"),
        }
    return comparison


def write_csv(records: list[dict], path: Path):
    """Write records to CSV."""
    if not records:
        return

    fieldnames = [
        "condition", "group", "case",
        "output_throughput", "request_throughput", "total_token_throughput",
        "median_ttft_ms", "p99_ttft_ms",
        "median_tpot_ms", "p99_tpot_ms",
        "median_itl_ms", "p99_itl_ms",
        "median_e2el_ms", "p99_e2el_ms",
        "completed", "total_input", "total_output", "duration",
    ]

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_summary_md(records: list[dict], comparison: dict, path: Path):
    """Generate a Markdown summary report."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    lines = [
        "# DeepSeek V4.1 Flash — Performance Characterization Summary",
        "",
        f"> Generated: {ts}",
        f"> Total runs: {len(records)}",
        "",
        "## Results by Network Condition",
        "",
    ]

    for cond in ["native", "100gbps", "20gbps"]:
        cond_records = [r for r in records if r["condition"] == cond]
        if not cond_records:
            continue

        cond_label = {"native": "Native (Unrestricted)", "100gbps": "100 Gbps", "20gbps": "20 Gbps"}
        lines.append(f"### {cond_label.get(cond, cond)}")
        lines.append("")
        lines.append("| Group | Case | Output Tok/s | TTFT p50 (ms) | TTFT p99 (ms) | TPOT p50 (ms) | TPOT p99 (ms) |")
        lines.append("|-------|------|-------------|---------------|---------------|---------------|---------------|")

        for r in cond_records:
            ot = f"{r['output_throughput']:.1f}" if r.get("output_throughput") is not None else "—"
            ttft50 = f"{r['median_ttft_ms']:.1f}" if r.get("median_ttft_ms") is not None else "—"
            ttft99 = f"{r['p99_ttft_ms']:.1f}" if r.get("p99_ttft_ms") is not None else "—"
            tpot50 = f"{r['median_tpot_ms']:.1f}" if r.get("median_tpot_ms") is not None else "—"
            tpot99 = f"{r['p99_tpot_ms']:.1f}" if r.get("p99_tpot_ms") is not None else "—"
            lines.append(f"| {r['group']} | {r['case']} | {ot} | {ttft50} | {ttft99} | {tpot50} | {tpot99} |")

        lines.append("")

    # Cross-condition comparison
    lines.append("## Cross-Condition Comparison")
    lines.append("")
    lines.append("Shows the impact of network bandwidth restriction on output throughput (tok/s).")
    lines.append("")
    lines.append("| Case | Native | 100Gbps | 20Gbps | Δ Native→20G |")
    lines.append("|------|--------|---------|--------|-------------|")

    for key, conds in sorted(comparison.items()):
        native_tput = conds.get("native", {}).get("output_throughput")
        c100_tput = conds.get("100gbps", {}).get("output_throughput")
        c20_tput = conds.get("20gbps", {}).get("output_throughput")

        native_s = f"{native_tput:.1f}" if native_tput else "—"
        c100_s = f"{c100_tput:.1f}" if c100_tput else "—"
        c20_s = f"{c20_tput:.1f}" if c20_tput else "—"

        if native_tput and c20_tput and native_tput > 0:
            delta = ((c20_tput - native_tput) / native_tput) * 100
            delta_s = f"{delta:+.1f}%"
        else:
            delta_s = "—"

        lines.append(f"| {key} | {native_s} | {c100_s} | {c20_s} | {delta_s} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `04_collect_results.py` from the DeepSeek V4.1 Flash Performance Characterization Suite.*")

    path.write_text("\n".join(lines))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Collect and summarize benchmark results")
    parser.add_argument("--results-dir", default=str(DEFAULT_RESULTS),
                       help="Path to results directory")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"✘ Results directory not found: {results_dir}")
        print("  Run 03_run_benchmarks.py first.")
        sys.exit(1)

    print(f"Scanning results in: {results_dir}")
    records = discover_results(results_dir)

    if not records:
        print("✘ No result files found.")
        print("  Ensure benchmarks have been run and results are in the expected directory structure.")
        sys.exit(1)

    print(f"Found {len(records)} result(s)")

    # Build comparison
    comparison = build_comparison(records)

    # Write CSV
    csv_path = results_dir / "summary.csv"
    write_csv(records, csv_path)
    print(f"✔ CSV written: {csv_path}")

    # Write comparison JSON
    comp_path = results_dir / "comparison.json"
    comp_path.write_text(json.dumps(comparison, indent=2))
    print(f"✔ Comparison JSON written: {comp_path}")

    # Write summary markdown
    md_path = results_dir / "SUMMARY.md"
    write_summary_md(records, comparison, md_path)
    print(f"✔ Summary written: {md_path}")

    # Quick console summary
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    for cond in ["native", "100gbps", "20gbps"]:
        cond_recs = [r for r in records if r["condition"] == cond]
        if cond_recs:
            tputs = [r["output_throughput"] for r in cond_recs if r.get("output_throughput")]
            avg_tput = sum(tputs) / len(tputs) if tputs else 0
            print(f"  {cond:>8s}: {len(cond_recs)} runs, avg throughput = {avg_tput:.1f} tok/s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
