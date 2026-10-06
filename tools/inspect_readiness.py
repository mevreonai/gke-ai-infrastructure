import sys, re
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("Cluster, Stack & Campaign Readiness Audit")
if idx == -1:
    idx = h.find("Readiness Audit")
if idx != -1:
    print(h[idx-100:idx+800])
else:
    print("Readiness panel not found by exact string")
