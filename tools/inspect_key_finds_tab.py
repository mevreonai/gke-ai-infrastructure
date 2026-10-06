import sys, re
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("tab-key-finds")
if idx == -1:
    idx = h.find("Key Finds")
if idx != -1:
    print(h[idx-50:idx+800])
