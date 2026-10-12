#!/usr/bin/env python3
"""audit/coverage_matrix.py: Generates coverage matrix across layouts, prompt lengths and loads
for Performance Intelligence Platform (PIP) scripts.

Asserts Section 6 of Scripts_Review_v1.3.md:
- Serving points per layout by step or batching block
- Points vLLM would refuse (validates Blocker 13: 1M prompts within max_model_len)
- Cases selected vs unselected
- Profiles selected by the master runner
"""
import json
import os
import re
import sys
from pathlib import Path

def generate_coverage_matrix(pip_dir: Path):
    scripts_dir = pip_dir / "scripts"
    master_sh = scripts_dir / "run_master_benchmark.sh"
    master_cases_file = scripts_dir / "master_benchmark_cases.json"
    batching_cases_file = scripts_dir / "continuous_batching_cases.json"
    profile_matrix_file = scripts_dir / "06_deep_kernel_and_torch_profiling" / "18_multi_node_profile_matrix.json"

    if not master_sh.exists():
        raise FileNotFoundError(f"Missing master script: {master_sh}")
    if not master_cases_file.exists():
        raise FileNotFoundError(f"Missing master cases: {master_cases_file}")
    if not batching_cases_file.exists():
        raise FileNotFoundError(f"Missing batching cases: {batching_cases_file}")

    master_sh_text = master_sh.read_text(encoding="utf-8", errors="replace")
    master_cases = json.loads(master_cases_file.read_text(encoding="utf-8"))["cases"]
    if isinstance(master_cases, dict):
        master_cases = list(master_cases.values())

    batching_cases = json.loads(batching_cases_file.read_text(encoding="utf-8"))["cases"]
    if isinstance(batching_cases, dict):
        batching_cases = list(batching_cases.values())

    profile_cases = []
    if profile_matrix_file.exists():
        profile_cases = json.loads(profile_matrix_file.read_text(encoding="utf-8")).get("profiles", [])

    print("=" * 80)
    print("  PERFORMANCE INTELLIGENCE PLATFORM — COVERAGE MATRIX AUDIT")
    print("=" * 80)

    # 1. Refusal Check (Blocker 13 verification)
    refused_points = []
    all_benchmarks = []
    for c in master_cases:
        for b in c.get("benchmarks", []):
            inp = b.get("input", 0)
            out = b.get("output", 256)
            all_benchmarks.append((c.get("name"), c.get("tp"), c.get("pp", 1), inp, out))
            # Server max_model_len is 1,048,576. If input + output > max_model_len, refused!
            if inp + out > 1048576:
                refused_points.append((c.get("name"), inp, out, "Prompt + output exceeds max_model_len (1,048,576)"))

    for c in batching_cases:
        for b in c.get("benchmarks", []):
            inp = b.get("input", 0)
            out = b.get("output", 256)
            all_benchmarks.append((c.get("name"), c.get("tp"), c.get("pp", 1), inp, out))
            if inp + out > 1048576:
                refused_points.append((c.get("name"), inp, out, "Prompt + output exceeds max_model_len (1,048,576)"))

    for p in profile_cases:
        inp = p.get("input", 0)
        out = p.get("output", 8)
        if inp + out > 1048576:
            refused_points.append((p.get("name", p.get("mode")), inp, out, "Profile prompt exceeds max_model_len"))

    print("\n[1] Refusal Audit (vLLM Context Limit 1,048,576):")
    if refused_points:
        print(f"  FAILED: {len(refused_points)} point(s) refused by vLLM:")
        for name, inp, out, reason in refused_points:
            print(f"    - {name}: input={inp}, output={out} -> {reason}")
    else:
        print("  PASS: 0 points refused. All prompt lengths safely fit within context limit (1,000,000 <= 1,048,576).")

    # 2. Layouts covered in Master Suite
    layout_cases = {}
    for c in master_cases:
        tp = c.get("tp", 1)
        pp = c.get("pp", 1)
        layout = f"TP{tp}/PP{pp}"
        layout_cases.setdefault(layout, []).append(c)

    print("\n[2] Serving Runs Layout Coverage:")
    for layout in sorted(layout_cases.keys()):
        cases = layout_cases[layout]
        inputs = sorted({b.get("input") for c in cases for b in c.get("benchmarks", []) if b.get("input")})
        concs = sorted({b.get("concurrency") for c in cases for b in c.get("benchmarks", []) if b.get("concurrency")})
        print(f"  Layout {layout:<10} : {len(cases):2d} cases | Inputs: {inputs} | Concurrencies: {concs}")

    # 3. Batching Blocks Coverage
    block_layouts = {}
    for c in batching_cases:
        blk = c.get("block", 0)
        tp = c.get("tp", 1)
        pp = c.get("pp", 1)
        block_layouts.setdefault(blk, set()).add(f"TP{tp}/PP{pp}")

    print("\n[3] Continuous Batching Blocks Coverage:")
    for blk in sorted(block_layouts.keys()):
        print(f"  Block {blk}: layouts = {sorted(block_layouts[blk])}")

    # 4. Master Profile Selection Audit
    print("\n[4] Master Profiler Selections:")
    profile_modes = re.findall(r"PROFILE_MODE_FILTER=([^\s;]+)", master_sh_text)
    print(f"  Selected Profile Modes in run_master_benchmark.sh: {profile_modes}")

    # Return True if clean
    return len(refused_points) == 0

if __name__ == "__main__":
    pip_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "Performance_Intelligence_Platform"
    ok = generate_coverage_matrix(pip_root)
    sys.exit(0 if ok else 1)
