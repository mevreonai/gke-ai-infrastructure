#!/usr/bin/env python3
"""Network resilience and bandwidth capping comparison tool.
Matches benchmark points by case name across conditions (native, 100g, 20g, impaired)
and compares both mean TTFT and TPOT.
"""
import json
import sys
from pathlib import Path


def collect_metrics_for_condition(cond_dir: Path):
    points = {}
    if not cond_dir.exists():
        return points
    for f in cond_dir.rglob("*.json"):
        fname_lower = f.name.lower()
        if (
            "warmup_manifest" in fname_lower
            or "audit" in fname_lower
            or "ray_nccl_env_audit" in fname_lower
            or f.name in (
                "summary.json",
                "manifest.json",
                "case_manifest.json",
                "resolved_models.json",
                "vllm_surrogate_manifest.json",
                "RESILIENCE_COMPARISON.json",
                "warmup_manifest.json",
            )
        ):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            ttft = d.get("mean_ttft_ms")
            if ttft is None and "ttfts" in d and len(d["ttfts"]) > 0:
                ttft = (sum(d["ttfts"]) / len(d["ttfts"])) * 1000.0
            tpot = d.get("mean_tpot_ms")
            # Require benchmark metrics so arbitrary JSONs are never treated as points
            if ttft is None and tpot is None and "median_itl_ms" not in d:
                continue

            case_name = d.get("case_name") or f.parent.name or f.stem
            points[case_name] = {
                "mean_ttft_ms": round(ttft, 2) if ttft is not None else None,
                "mean_tpot_ms": round(tpot, 2) if tpot is not None else None,
                "file": str(f.name),
            }
        except Exception:
            pass
    return points


def main():
    if len(sys.argv) < 2:
        print("Usage: compare_resilience_matrix.py <capped_dir>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1])
    conditions = ["native", "capped_100g", "capped_20g", "impaired_005pct_loss"]
    cond_data = {c: collect_metrics_for_condition(root / c) for c in conditions}

    all_cases = set()
    for c in conditions:
        all_cases.update(cond_data[c].keys())

    report = {}
    for case in sorted(all_cases):
        report[case] = {}
        for c in conditions:
            if case in cond_data[c]:
                report[case][c] = cond_data[c][case]

        nat = report[case].get("native", {})
        imp = report[case].get("impaired_005pct_loss", {})
        if nat.get("mean_ttft_ms") and imp.get("mean_ttft_ms"):
            n_ttft = nat["mean_ttft_ms"]
            i_ttft = imp["mean_ttft_ms"]
            report[case]["ttft_degradation_pct"] = round(((i_ttft - n_ttft) / n_ttft) * 100.0, 2)

        if nat.get("mean_tpot_ms") and imp.get("mean_tpot_ms"):
            n_tpot = nat["mean_tpot_ms"]
            i_tpot = imp["mean_tpot_ms"]
            report[case]["tpot_degradation_pct"] = round(((i_tpot - n_tpot) / n_tpot) * 100.0, 2)

        # Also calculate degradation for capped bandwidth conditions against native
        for c_name in ("capped_100g", "capped_20g"):
            c_data = report[case].get(c_name, {})
            if nat.get("mean_ttft_ms") and c_data.get("mean_ttft_ms"):
                report[case][f"ttft_{c_name}_degradation_pct"] = round(
                    ((c_data["mean_ttft_ms"] - nat["mean_ttft_ms"]) / nat["mean_ttft_ms"]) * 100.0, 2
                )
            if nat.get("mean_tpot_ms") and c_data.get("mean_tpot_ms"):
                report[case][f"tpot_{c_name}_degradation_pct"] = round(
                    ((c_data["mean_tpot_ms"] - nat["mean_tpot_ms"]) / nat["mean_tpot_ms"]) * 100.0, 2
                )

    out_file = root / "RESILIENCE_COMPARISON.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Resilience Comparison (Matched by Case Across Conditions):")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
