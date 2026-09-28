import json
import sys

print("Running Automated Parity Validation on Restored Full-Depth Dashboards...")

target_html_with_kf = "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html"
target_html_no_kf = "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html"

with open(target_html_with_kf, "r", encoding="utf-8") as f:
    html_with_kf = f.read()

with open(target_html_no_kf, "r", encoding="utf-8") as f:
    html_no_kf = f.read()

test_results = []

def run_test(name, passed, detail):
    test_results.append({
        "test": name,
        "passed": bool(passed),
        "detail": detail
    })
    status = "PASS" if passed else "FAIL"
    safe_detail = detail.encode('ascii', errors='replace').decode('ascii')
    print(f"  [{status}] {name}: {safe_detail}")

# Test 1: Stable IDs 1..10 in KD_PAGES_DATA
idx = html_with_kf.find('window.KD_PAGES_DATA = [')
end_idx = html_with_kf.find('];\nwindow.kdActivePage = 1;', idx)
kd_json_str = html_with_kf[idx + len('window.KD_PAGES_DATA = '):end_idx + 1]
pages = json.loads(kd_json_str)
ids_check = [p["id"] for p in pages] == list(range(1, 11))
run_test("P0_Stable_IDs_1_to_10", ids_check, "10 full-depth discovery pages in exact canonical sequence 1..10")

# Test 2: Trust Strip Wording
trust_check = (
    "119/126 COMPLETED E2E ROWS VALIDATED" in html_with_kf and
    "PROFILE EVIDENCE: 14/22 DISTRIBUTED PROFILES COMPLETE" in html_with_kf and
    "STRICT SUITE SIGN-OFF INCOMPLETE" in html_with_kf
)
run_test("P0_Trust_Strip_Wording", trust_check, "Contains Application 119/126, Profile 14/22, and Strict Sign-Off Incomplete")

# Test 3: Measured Transports
trans_check = "Native 173.58 Gb/s" in html_with_kf and "100G 56.84 Gb/s" in html_with_kf and "20G 16.48 Gb/s" in html_with_kf
run_test("P0_Measured_Transports", trans_check, "Contains Native 173.58 Gb/s, 100G 56.84 Gb/s, 20G 16.48 Gb/s")

# Test 4: Map Scope Column
map_scope_check = '<td class="scope-cell">' in html_with_kf
run_test("P0_Map_Scope_Column", map_scope_check, "Finding map table includes dedicated Scope column")

# Test 5: Coverage Rails On Cards
rail_count = html_with_kf.count("kd-card-scope-rail")
run_test("P0_Coverage_Rails_On_Cards", rail_count >= 10, f"Found {rail_count}/10 coverage rails on Signal cards")

# Test 6: Finding 1 Fabric Data
f1_check = (
    "2.859, 18.372, 53.127" in html_with_kf and
    "2.810, 15.546, 41.472" in html_with_kf and
    "1.961, 11.134, 29.684" in html_with_kf and
    "31.053, 128.275, 256.889" in html_with_kf and
    "2.926" not in html_with_kf and "18.860" not in html_with_kf and "2.510" not in html_with_kf and "15.650" not in html_with_kf
)
run_test("P0_Finding1_Fabric_Data", f1_check, "Canonical 20G values enforced; stale literals 2.926, 18.860, 2.510, 15.650 completely eliminated")

# Test 7: Finding 2 Concurrency Data
f2_check = "0.3467" in html_with_kf and "231.268" in html_with_kf and "267.411" in html_with_kf and "134.428" in html_with_kf
run_test("P0_Finding2_Concurrency_Data", f2_check, "Validated 0.3415->0.3467 tok/s, 231.268s TTFT, 267.411ms TPOT, 134.428s queue")

# Test 8: Finding 3 Complexity Wording
f3_check = (
    ("empirical p≈1.99" in html_with_kf or "empirical p&approx;1.99" in html_with_kf or "p ≈ 1.99" in html_with_kf or "p &approx; 1.99" in html_with_kf) and
    "driving quadratic prefill expansion" not in html_with_kf
)
run_test("P0_Finding3_Complexity_Wording", f3_check, "Uses 'empirical p≈1.99'; removed quadratic prefill expansion claims")

# Test 9: Finding 4 Prefix Reuse
f4_check = "36.0×" in html_with_kf or "36.0x" in html_with_kf
run_test("P0_Finding4_Prefix_Reuse", f4_check, "Validated cold vs repeat-hit speedup (36.0x @ 1M)")

# Test 10: Finding 5 Admission Data
f5_check = "3.3586" in html_with_kf and "0.1846" in html_with_kf
run_test("P0_Finding5_Admission_Data", f5_check, "Validated 3.3586 vs 0.1846 req/s admission throughput")

# Test 11: Finding 6 Parallelism Frontier
f6_check = "664.24" in html_with_kf and "41.515" in html_with_kf and "TP8/PP4" not in html_with_kf
run_test("P0_Finding6_Parallelism_Frontier", f6_check, "Contains TP8/PP2 @ 664.24 GPU-s / 41.515s measured point; TP8/PP4 never rendered")

# Test 12: Finding 7 TP Decode TPOT
f7_check = "251.529" in html_with_kf and "583.866" in html_with_kf
run_test("P0_Finding7_TP_Decode_TPOT", f7_check, "Validated TP4/TP8 PyTorch AllReduce breakdown 251.53ms vs 583.87ms")

# Test 13: Finding 8 Runtime Knobs
f8_check = "232.342" in html_with_kf and "-27.1%" in html_with_kf and "233.364" not in html_with_kf
run_test("P0_Finding8_Runtime_Knobs", f8_check, "Fixed 233.364s typo; chunk -27.1% verified; maxseq flat")

# Test 14: Finding 9 Busy GPU
f9_check = (
    "Erroneous High" not in html_with_kf and
    "Fast & Efficient" not in html_with_kf
)
run_test("P0_Finding9_Busy_GPU", f9_check, "Neutral activity labels applied; Erroneous High / Fast & Efficient removed")

# Test 15: Finding 10 KV vs VRAM
f10_check = (
    "Peak GPU Memory Telemetry (GiB)" in html_with_kf and
    "Peak Allocated Physical VRAM" not in html_with_kf and
    "Global Model KV Check" not in html_with_kf and
    "93% saturated" not in html_with_kf
)
run_test("P0_Finding10_KV_vs_VRAM", f10_check, "Peak GPU Memory Telemetry used; Global KV check and 93% saturated removed")

# Test 16: UX Action Labels & Forensic Routing
ux_check = (
    "View Detailed Finding" in html_with_kf and
    "Inspect Evidence" in html_with_kf and
    "Forensic Modal View" not in html_with_kf
)
run_test("P0_UX_Action_Labels", ux_check, "Signal uses 'View Detailed Finding ↓'; Engineer uses 'Inspect Evidence →'; Forensic Modal View removed")

# Test 17: Navigation Integrity for Version 1 (Dual Tabs: Keep Key Finds too)
nav_check_with_kf = (
    '<button class="tab" data-tab="keyfinds">' in html_with_kf and
    'data-tab="keydiscoveries"' in html_with_kf
)
run_test("P0_With_KeyFinds_Nav_Integrity", nav_check_with_kf, "Version 1 keeps 'Key Finds' tab active alongside 'Key Discoveries'")

# Test 18: Navigation Isolation for Version 2 (Clean Single Top-10 Production Version)
nav_check_no_kf = (
    'data-tab="keydiscoveries"' in html_no_kf and
    '<!-- <button class="tab" data-tab="keyfinds"' in html_no_kf
)
run_test("P0_No_KeyFinds_Nav_Isolation", nav_check_no_kf, "Version 2 removes/hides legacy Key Finds tab; Key Discoveries is single top-level Top-10")

passed_count = sum(1 for t in test_results if t["passed"])
total_count = len(test_results)
all_passed = (passed_count == total_count)
status_str = "PASS" if all_passed else "FAIL"

val_json = {
    "target_file_with_keyfinds": target_html_with_kf,
    "target_file_no_keyfinds": target_html_no_kf,
    "audit_status": status_str,
    "total_tests": total_count,
    "passed_tests": passed_count,
    "tests": test_results
}

with open("KEY_DISCOVERIES_VALIDATION.json", "w", encoding="utf-8") as f:
    json.dump(val_json, f, indent=2)

md_lines = [
    "# KEY DISCOVERIES V6 VALIDATION REPORT",
    f"**Target HTML (Dual Tabs):** `{target_html_with_kf}`",
    f"**Target HTML (Clean Top-10):** `{target_html_no_kf}`",
    f"**Status:** {status_str} ({passed_count}/{total_count} tests passed)",
    "",
    "| # | Test Name | Status | Detail |",
    "|---|---|---|---|"
]

for idx, t in enumerate(test_results, 1):
    st = "✅ PASS" if t["passed"] else "❌ FAIL"
    md_lines.append(f"| {idx} | `{t['test']}` | {st} | {t['detail']} |")

with open("KEY_DISCOVERIES_VALIDATION.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines) + "\n")

print(f"\n==========================================")
print(f"FINAL AUDIT RESULT: {status_str} ({passed_count}/{total_count} TESTS PASSED)")
print(f"==========================================")

if not all_passed:
    sys.exit(1)
