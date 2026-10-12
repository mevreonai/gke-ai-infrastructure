#!/usr/bin/env python3
"""NUMA socket pinning evaluation comparison tool."""
import json, sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: compare_numa_pinning.py <tp8_dir>", file=sys.stderr)
        sys.exit(1)
    pdir = Path(sys.argv[1])
    unpinned_file = pdir / "control/8k_c1_unpinned.json"
    pinned_file = pdir / "pinned/8k_c1_pinned.json"
    res = {"unpinned_mean_tpot_ms": None, "pinned_mean_tpot_ms": None, "delta_ms": None}
    if unpinned_file.exists():
        try:
            res["unpinned_mean_tpot_ms"] = json.load(open(unpinned_file)).get("mean_tpot_ms")
        except Exception:
            pass
    if pinned_file.exists():
        try:
            res["pinned_mean_tpot_ms"] = json.load(open(pinned_file)).get("mean_tpot_ms")
        except Exception:
            pass
    if res["unpinned_mean_tpot_ms"] and res["pinned_mean_tpot_ms"]:
        res["delta_ms"] = res["pinned_mean_tpot_ms"] - res["unpinned_mean_tpot_ms"]
    comp_file = pdir / "PINNING_COMPARISON.json"
    comp_file.write_text(json.dumps(res, indent=2))
    print("NUMA Pinning Summary:", json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
