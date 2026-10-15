#!/usr/bin/env python3
"""Performance Intelligence Platform (PIP) - Static Suite Pre-Flight Validator.

Safe to execute on any machine or head-node without GPUs or active vLLM daemons.
Validates:
1. Python syntax compilation across all suite scripts (py_compile).
2. Shell script syntax integrity (bash -n where available).
3. JSON configuration parsing, case name uniqueness, and safety-gate ordering.
4. Token clamping invariants (1M benchmark inputs <= 1,000,000 tokens).
5. Environment sanity: no hardcoded personal home directories and no forbidden NCCL p2p/shm disables in local scripts.

Outputs results to STATIC_VALIDATION.json.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Static PIP Suite Validator")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent,
                        help="Root directory of PIP scripts to inspect")
    parser.add_argument("--out", type=Path, default=None,
                        help="Path to output STATIC_VALIDATION.json")
    parser.add_argument("--strict-exit", action="store_true",
                        help="Exit with non-zero status code if any check fails")
    args = parser.parse_args()

    root = args.root.resolve()
    out_file = (args.out or root / "STATIC_VALIDATION.json").resolve()

    checks: List[Dict[str, Any]] = []

    def record(name: str, ok: bool, category: str = "general", detail: str = ""):
        checks.append({
            "name": name,
            "category": category,
            "passed": bool(ok),
            "detail": str(detail)
        })

    print("=" * 80)
    print("  PERFORMANCE INTELLIGENCE PLATFORM — STATIC SUITE VALIDATION")
    print(f"  Target Root : {root}")
    print(f"  Report File : {out_file}")
    print("=" * 80)

    # 1. Python syntax compilation
    print("\n[1/5] Verifying Python compilation across all scripts...")
    py_files = sorted(root.rglob("*.py"))
    for py_p in py_files:
        rel = str(py_p.relative_to(root))
        try:
            py_compile.compile(str(py_p), doraise=True)
            record(f"py_compile:{rel}", True, category="python_syntax")
        except Exception as e:
            record(f"py_compile:{rel}", False, category="python_syntax", detail=repr(e))

    # 2. Shell script syntax (bash -n)
    print("[2/5] Verifying Shell script syntax integrity...")
    sh_files = sorted(root.rglob("*.sh"))
    bash_available = False
    try:
        r = subprocess.run(["bash", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        bash_available = (r.returncode == 0)
    except Exception:
        bash_available = False

    for sh_p in sh_files:
        rel = str(sh_p.relative_to(root))
        if bash_available:
            r = subprocess.run(["bash", "-n", str(sh_p)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ok = (r.returncode == 0)
            detail = r.stdout[-500:] if not ok else ""
            record(f"bash_syntax:{rel}", ok, category="shell_syntax", detail=detail)
        else:
            # Fallback syntax heuristic if running on native Windows without bash on PATH
            txt = sh_p.read_text(encoding="utf-8", errors="ignore")
            has_unmatched_quotes = (txt.count('"""') % 2 != 0)
            record(f"bash_syntax_heuristic:{rel}", not has_unmatched_quotes, category="shell_syntax")

    # 3. JSON Configuration, Case Uniqueness, and Gate Dependency Ordering
    print("[3/5] Verifying JSON schema, case uniqueness, and gate ordering...")
    json_files = sorted(root.rglob("*.json"))
    for j_p in json_files:
        if j_p.name in ("STATIC_VALIDATION.json", "CAMPAIGN_SUMMARY.json", "FINAL_VALIDATION.json"):
            continue
        rel = str(j_p.relative_to(root))
        try:
            data = json.loads(j_p.read_text(encoding="utf-8"))
            record(f"json_parse:{rel}", True, category="json_schema")
        except Exception as e:
            record(f"json_parse:{rel}", False, category="json_schema", detail=repr(e))
            continue

        if isinstance(data, dict) and isinstance(data.get("cases"), list):
            case_names = [c.get("name") for c in data["cases"] if isinstance(c, dict) and c.get("name")]
            unique_cases = (len(case_names) == len(set(case_names)))
            record(f"unique_cases:{rel}", unique_cases, category="case_integrity",
                   detail=f"{len(case_names)} cases defined")

            # Check gate ordering and token limits
            for c in data["cases"]:
                cname = c.get("name", "unknown")
                seen_benchmarks: List[str] = []
                for b in c.get("benchmarks", []):
                    bname = b.get("name", "unknown")
                    gate = b.get("gate") or {}
                    after = gate.get("after")
                    if after:
                        gate_ok = (after in seen_benchmarks)
                        record(f"gate_order:{rel}:{cname}:{bname}", gate_ok, category="gate_dependencies",
                               detail=f"depends_on={after}, seen={seen_benchmarks}")
                    seen_benchmarks.append(bname)

                    # Blocker 13 check: If 1m benchmark, input tokens must be <= 1,000,000
                    if "1m" in bname.lower() or "1000k" in bname.lower():
                        inp = b.get("input", 0)
                        inp_val = int(inp) if isinstance(inp, (int, str)) and str(inp).isdigit() else 0
                        clamped = (inp_val <= 1000000)
                        record(f"token_clamp_1m:{rel}:{cname}:{bname}", clamped, category="token_clamping",
                               detail=f"input_tokens={inp_val}")

    # 4. Environment & Security Invariants
    print("[4/5] Checking environment policies & non-hardcoded invariants...")
    all_scripts = list(py_files) + list(sh_files)
    forbidden_local_p2p = re.compile(r'\b(NCCL_P2P_DISABLE|NCCL_SHM_DISABLE)\s*=\s*1\b')
    hardcoded_home = re.compile(r'/home/(?:[a-zA-Z0-9_\-]+)/')

    for s_p in all_scripts:
        rel = str(s_p.relative_to(root))
        try:
            content = s_p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # In local scripts, NCCL_SHM_DISABLE=1 is completely forbidden.
        # NCCL_P2P_DISABLE=1 is only allowed in explicitly isolated sensitivity tests.
        if "single_node" in rel.lower() or "local" in rel.lower():
            for m in forbidden_local_p2p.finditer(content):
                flag = m.group(1)
                context_snippet = content[max(0, m.start() - 100):min(len(content), m.end() + 100)]
                if flag == "NCCL_SHM_DISABLE":
                    record(f"no_shm_disable:{rel}", False, category="nccl_invariants",
                           detail="NCCL_SHM_DISABLE=1 is strictly forbidden")
                elif flag == "NCCL_P2P_DISABLE":
                    is_sensitivity = "SENSITIVITY" in context_snippet.upper()
                    record(f"nccl_p2p_sensitivity_isolated:{rel}", is_sensitivity, category="nccl_invariants",
                           detail=f"isolated_sensitivity={is_sensitivity}")

        # Check for hardcoded /home/username
        user_matches = hardcoded_home.findall(content)
        # Filter out safe defaults like ${HOME:-/home/user} if properly handled or in comments
        real_user_matches = [m for m in user_matches if m not in ("user", "root", "$USER")]
        if real_user_matches:
            record(f"no_hardcoded_user_home:{rel}", False, category="path_portability",
                   detail=f"found hardcoded paths: {real_user_matches}")

    # 5. Summary and Output
    print("[5/5] Generating static validation report...")
    total = len(checks)
    passed = sum(1 for c in checks if c["passed"])
    failed = total - passed

    summary = {
        "timestamp": os.environ.get("TIMESTAMP", ""),
        "root_directory": str(root),
        "total_checks": total,
        "passed_checks": passed,
        "failed_checks": failed,
        "pass_rate_percent": round((passed / total * 100.0) if total > 0 else 0.0, 2),
        "checks": checks
    }

    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved Report: {out_file}")
    print(f"Total Checks : {total}")
    print(f"Passed Checks: {passed}")
    print(f"Failed Checks: {failed}")
    print(f"Pass Rate    : {summary['pass_rate_percent']}%")

    if failed > 0:
        print("\nFailed Checks:")
        for c in checks:
            if not c["passed"]:
                print(f"  [FAIL] {c['category']} -> {c['name']} ({c['detail']})")
        if args.strict_exit:
            sys.exit(1)
    else:
        print("\n[+] SUCCESS: All static pre-flight validations PASSED!")

if __name__ == "__main__":
    main()
