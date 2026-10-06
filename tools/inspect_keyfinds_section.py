import sys
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find('id="keyfinds"')
if idx != -1:
    print(h[idx-30:idx+1200])
else:
    print("id=keyfinds not found")
