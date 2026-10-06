import sys, re
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

for target in ["scaleout-matrix-table", "network-layer-bandwidth-panel", "wall-time-budget-panel"]:
    idx = h.find(target)
    print(f"--- {target} ---")
    if idx != -1:
        print(h[idx-50:idx+250])
