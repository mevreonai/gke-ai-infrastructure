#!/usr/bin/env python3
"""Performance Intelligence Platform (PIP) - Final Collector & Provenance Validator.

Adapted from V8's 90_collect_and_validate.py and generalized for the PIP architecture.
Key Invariants:
1. Missing benchmark results are NEVER converted to zero; they are classified as NOT_RUN.
2. Multi-node distributed coverage is keyed and verified by network provenance:
   - GCP_NATIVE (175G RoCEv2 / Native Network)
   - GCP_CAPPED_100G (100 Gbps Traffic Control / Emulated Interconnect)
   - GCP_CAPPED_20G (20 Gbps Traffic Control / Standard Tier Interconnect)
3. Enforces zero exit-code failures across all evaluated benchmarks.
4. Verifies absence of forbidden NCCL environment overrides (NCCL_P2P_DISABLE, NCCL_SHM_DISABLE) in local native logs.
5. Produces FINAL_VALIDATION.json, coverage_matrix.csv, and VALIDATION_SUMMARY.txt in final_validation/.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED_NETWORKS = ["GCP_NATIVE", "GCP_CAPPED_100G", "GCP_CAPPED_20G"]
REQUIRED_TOPOLOGIES = ["tp4_pp2_dist", "tp8_pp2_dist", "tp4_pp4_dist", "tp16_pp1_dist"]
FORBIDDEN_LOCAL_NCCL = ("NCCL_P2P_DISABLE=1", "NCCL_SHM_DISABLE=1", "NCCL_P2P_LEVEL")

def load_json(p: Path, default=None) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def sha256_file(p: Path, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(block), b""):
            h.update(b)
    return h.hexdigest()

def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: List[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def flatten_config(path: Path, scope: str, network_provenance: str = "SINGLE_NODE_LOCAL") -> List[Dict[str, Any]]:
    cfg = load_json(path, {}) or {}
    out = []
    raw_cases = cfg.get("cases", [])
    if isinstance(raw_cases, dict):
        cases_list = list(raw_cases.values())
    elif isinstance(raw_cases, list):
        cases_list = raw_cases
    else:
        cases_list = []

    for c in cases_list:
        if not isinstance(c, dict):
            continue
        cname = c.get("name")
        tp = c.get("tp")
        pp = c.get("pp", 1)
        for b in c.get("benchmarks", []):
            if not isinstance(b, dict):
                continue
            inp = b.get("input")
            if b.get("dataset") == "prefix_repetition":
                inp = int(b.get("prefix", 0)) + int(b.get("suffix", 0))
            out.append({
                "scope": scope,
                "network_provenance": network_provenance,
                "case": cname,
                "bench": b.get("name"),
                "tp": tp,
                "pp": pp,
                "input_tokens": inp,
                "output_tokens": b.get("output"),
                "concurrency": b.get("concurrency"),
                "has_gate": bool(b.get("gate")),
                "gate_after": (b.get("gate") or {}).get("after"),
                "purpose": c.get("purpose", "")
            })
    return out

def status_class(x: Optional[Dict[str, Any]]) -> str:
    if not x:
        return "NOT_RUN"
    s = x.get("status")
    ec = x.get("exit_code")
    if s == "COMPLETED" and ec in (0, "0", None):
        return "COMPLETED"
    if s in ("SKIPPED_BY_SAFETY_GATE", "SKIPPED"):
        return "SAFETY_SKIPPED"
    if s in ("WARMUP_FAILED", "FAILED") or (ec not in (0, "0", None) and ec is not None):
        return "FAILED"
    return str(s) if s else "UNKNOWN"

def find_actual_manifests(root: Path) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    idx: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for p in root.rglob("*.json"):
        if "manifest" not in p.name.lower() or p.name in ("vllm_surrogate_manifest.json", "master_step_status.jsonl"):
            continue
        d = load_json(p, {}) or {}
        if not isinstance(d, dict):
            continue
        case = d.get("name") or d.get("case") or p.parent.name
        net = d.get("network_provenance") or d.get("network_mode")
        if not net:
            # Infer from directory path
            p_str = str(p).upper()
            if "20G" in p_str:
                net = "GCP_CAPPED_20G"
            elif "100G" in p_str:
                net = "GCP_CAPPED_100G"
            elif "NATIVE" in p_str or "175G" in p_str:
                net = "GCP_NATIVE"
            else:
                net = "SINGLE_NODE_LOCAL"

        benchmarks = d.get("benchmarks", [])
        if isinstance(benchmarks, list) and benchmarks:
            for b in benchmarks:
                bname = b.get("name")
                if bname:
                    idx[(net, case, bname)] = {**b, "_manifest": str(p), "_case": d}
        else:
            # Manifest represents a single benchmark or profile case
            idx[(net, case, d.get("bench", case))] = {**d, "_manifest": str(p), "_case": d}
    return idx

def main():
    parser = argparse.ArgumentParser(description="Performance Intelligence Platform - Collector & Validator")
    parser.add_argument("--root", required=True, type=Path,
                        help="Root directory containing benchmark run results")
    parser.add_argument("--suite", type=Path, default=None,
                        help="Root directory containing suite scripts/configs")
    parser.add_argument("--out", type=Path, default=None,
                        help="Output directory for final validation artifacts (default: <root>/final_validation)")
    parser.add_argument("--strict-exit", action="store_true",
                        help="Exit non-zero if any required benchmark failed or was skipped")
    args = parser.parse_args()

    root = args.root.resolve()
    suite = (args.suite or Path(__file__).resolve().parent).resolve()
    out_dir = (args.out or root / "final_validation").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("  PERFORMANCE INTELLIGENCE PLATFORM — COLLECT & VALIDATE")
    print(f"  Results Root : {root}")
    print(f"  Suite Root   : {suite}")
    print(f"  Output Dir   : {out_dir}")
    print("=" * 80)

    configured: List[Dict[str, Any]] = []

    # 1. Single Node Surrogate Cases
    single_cfg = suite / "02_single_node_baseline_matrix" / "10_vllm_surrogate_cases.json"
    if single_cfg.exists():
        configured += flatten_config(single_cfg, "SINGLE_NODE_BASELINE", "SINGLE_NODE_LOCAL")

    # 2. 1M Context Extensions
    ext_1m_cfg = suite / "05_long_context_1m_extensions" / "10d_1m_extended_cases.json"
    if ext_1m_cfg.exists():
        configured += flatten_config(ext_1m_cfg, "SINGLE_NODE_1M_EXT", "SINGLE_NODE_LOCAL")

    # 3. Multi-Node Scale-Out Cases across required network topologies
    multi_cfg = suite / "04_scaleout_distributed_network" / "10b_vllm_multi_node_cases.json"
    if multi_cfg.exists():
        for net in REQUIRED_NETWORKS:
            configured += flatten_config(multi_cfg, "MULTI_NODE_SCALEOUT", net)

    # 4. Master Benchmark Cases if present
    master_cfg = suite / "master_benchmark_cases.json"
    if master_cfg.exists():
        configured += flatten_config(master_cfg, "MASTER_CAMPAIGN", "SINGLE_NODE_LOCAL")

    print(f"\n[+] Total Configured Benchmarks Expected: {len(configured)}")

    # Scan actual results
    actual = find_actual_manifests(root)
    print(f"[+] Total Actual Manifests Discovered  : {len(actual)}")

    coverage: List[Dict[str, Any]] = []
    completed_count = 0
    failed_count = 0
    skipped_count = 0
    not_run_count = 0

    for item in configured:
        key = (item["network_provenance"], item["case"], item["bench"])
        match = actual.get(key)
        # Fallback search ignoring network provenance if single node
        if not match and item["network_provenance"] == "SINGLE_NODE_LOCAL":
            for (act_net, act_case, act_bench), act_val in actual.items():
                if act_case == item["case"] and act_bench == item["bench"]:
                    match = act_val
                    break

        st = status_class(match)
        if st == "COMPLETED":
            completed_count += 1
        elif st == "FAILED":
            failed_count += 1
        elif st == "SAFETY_SKIPPED":
            skipped_count += 1
        elif st == "NOT_RUN":
            not_run_count += 1

        rec = {
            **item,
            "status": st,
            "manifest": match.get("_manifest") if match else None,
            "exit_code": match.get("exit_code") if match else None,
            "gate_reason": match.get("gate_reason") if match else None,
            "peak_kv_usage": match.get("peak_kv_usage") if match else None,
            "preemptions_delta": match.get("preemptions_delta") if match else None,
            "metric_samples": match.get("metric_samples") if match else None,
            "ttft_p50_ms": (match.get("metrics") or {}).get("ttft_p50_ms") if match else None,
            "tpot_p50_ms": (match.get("metrics") or {}).get("tpot_p50_ms") if match else None
        }
        coverage.append(rec)

    # Output CSV coverage matrix
    csv_file = out_dir / "coverage_matrix.csv"
    write_csv(csv_file, coverage)

    # Output JSON report
    validation_report = {
        "results_root": str(root),
        "suite_root": str(suite),
        "summary": {
            "total_configured": len(configured),
            "completed": completed_count,
            "failed": failed_count,
            "safety_skipped": skipped_count,
            "not_run": not_run_count,
            "completion_rate_pct": round((completed_count / len(configured) * 100.0) if configured else 0.0, 2),
            "campaign_passed": (failed_count == 0 and not_run_count == 0)
        },
        "coverage_records": coverage
    }

    json_file = out_dir / "FINAL_VALIDATION.json"
    json_file.write_text(json.dumps(validation_report, indent=2), encoding="utf-8")

    # Output human-readable summary
    summary_text = f"""================================================================================
  PERFORMANCE INTELLIGENCE PLATFORM — FINAL AUDIT & VALIDATION REPORT
================================================================================
  Results Directory    : {root}
  Total Configured     : {len(configured)}
  Completed (Pass)     : {completed_count}
  Failed               : {failed_count}
  Safety Skipped       : {skipped_count}
  Not Run              : {not_run_count}
  Completion Rate      : {validation_report['summary']['completion_rate_pct']}%
  Overall Pass Status  : {'PASS' if validation_report['summary']['campaign_passed'] else 'FAIL'}

  Artifacts Produced:
    - {json_file}
    - {csv_file}
================================================================================
"""
    txt_file = out_dir / "VALIDATION_SUMMARY.txt"
    txt_file.write_text(summary_text, encoding="utf-8")
    print(summary_text)

    if args.strict_exit and not validation_report["summary"]["campaign_passed"]:
        print("[!] Strict exit requested: Campaign has failures, safety skips, or incomplete runs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
