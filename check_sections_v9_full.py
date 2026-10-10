import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html', 'r', encoding='utf-8') as f:
    v8 = f.read()

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    v9 = f.read()

print("=== CHECKING SECTIONS IN V9_FULL_RESULT DASHBOARD ===")

checks = [
    ("Wall-Time Budget (§4.17)", "Where the Time Goes — §4.17" in v9),
    ("btn-budget-first-single", "btn-budget-first-single" in v9),
    ("btn-budget-decode-single", "btn-budget-decode-single" in v9),
    ("btn-budget-first-load", "btn-budget-first-load" in v9),
    ("btn-budget-decode-load", "btn-budget-decode-load" in v9),
    ("Section 6 Layout Coverage", "Section 6" in v9 or "layout coverage" in v9.lower()),
    ("PP2 3:4 Check in Stage Panel", "0.77 on TP4/PP2 and 0.77 on TP8/PP2" in v9),
    ("Reviewer Audit Matrix (§4.16)", "Reviewer Audit" in v9),
    ("TP16 head divisibility note", "24 Engram" in v9 or "24 Heads" in v9),
    ("UVA offloader probe note", "UVA" in v9 or "offload probe" in v9.lower()),
    ("switchTab implementation", "function switchTab" in v9),
]

for name, res in checks:
    print(f"  {name:35} : {'YES' if res else 'NO'}")
