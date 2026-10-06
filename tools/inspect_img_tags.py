import sys, re
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

for m in re.finditer(r'<img[^>]*wall_time_budget[^>]*>', h):
    print(m.group(0))
