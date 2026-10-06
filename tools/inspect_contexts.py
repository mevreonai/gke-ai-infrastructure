with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    html = f.read()
import re
for m in re.finditer(r"119/126", html):
    idx = m.start()
    print("--- 119/126 Context ---")
    print(html[max(0, idx-100):min(len(html), idx+200)])

for m in re.finditer(r"14\s*/\s*22", html):
    idx = m.start()
    print("--- 14/22 Context ---")
    print(html[max(0, idx-100):min(len(html), idx+200)])
