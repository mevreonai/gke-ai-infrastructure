import sys, re
sys.stdout.reconfigure(encoding="utf-8")
dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("'PR-002': {")
idx_end = h.find("'PR-004': {", idx)
print(h[idx:idx_end])
