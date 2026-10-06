import sys
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("perf-evidence-table-container")
idx_th = h.find("<thead>", idx)
idx_th_end = h.find("</thead>", idx_th)
print("Headers:")
print(h[idx_th:idx_th_end+8])
