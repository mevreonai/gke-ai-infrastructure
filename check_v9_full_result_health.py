import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("=== CHECKING V9_FULL_RESULT / MASTER_CHARACTERIZATION_DASHBOARD.HTML ===")

# 1. Check switchTab definition
has_switchTab = "function switchTab(" in html or "window.switchTab =" in html
print(f"1. switchTab defined: {has_switchTab}")

# 2. Check for onclick handlers calling undefined functions
onclicks = set(re.findall(r'onclick="([a-zA-Z0-9_]+)\(', html))
print(f"2. Functions called via onclick: {sorted(list(onclicks))}")
for fn in sorted(list(onclicks)):
    defined = f"function {fn}(" in html or f"window.{fn} =" in html or f"{fn} =" in html
    print(f"   - {fn}: {'DEFINED' if defined else 'MISSING / UNDEFINED'}")

# 3. Check Chart.js loading
has_chart_script = "chart.umd.js" in html
print(f"3. Chart.js local script present: {has_chart_script}")

# 4. Check TP16 representation
tp16_matches = re.findall(r'.{0,50}TP16.{0,100}', html)
print(f"4. Total TP16 occurrences: {len(tp16_matches)}")
blocked_tp16 = [m for m in tp16_matches if 'BLOCKED' in m or 'blocked' in m or 'CAPABILITY' in m]
print(f"   - Blocked/Constrained TP16 mentions: {len(blocked_tp16)}")

# 5. Check if Reviewer Audit Matrix (§4.16) is present
print(f"5. Reviewer Audit Matrix present: {'Reviewer Audit' in html}")

# 6. Check if Wall-Time Budget (§4.17) is present
print(f"6. Wall-Time Budget present: {'Wall-Time Budget' in html or 'wall_time_budget' in html}")

# 7. Check if Evidence registry is populated
has_ev_registry = "window.EVIDENCE_REGISTRY" in html or "const EVIDENCE_REGISTRY" in html or "EVIDENCE_DATA" in html
print(f"7. Evidence data object present: {has_ev_registry}")

# 8. Check if index.html matches
with open('v9_full_result/index.html', 'r', encoding='utf-8') as f:
    idx_html = f.read()
print(f"8. index.html matches MASTER_CHARACTERIZATION_DASHBOARD.html: {html == idx_html} (sizes: {len(html)} vs {len(idx_html)})")
