import sys, re
dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("perf-evidence-table-container")
idx_th = h.find("<thead>", idx)
idx_th_end = h.find("</thead>", idx_th)
th_texts = re.findall(r'<th[^>]*>(.*?)</th>', h[idx_th:idx_th_end], re.DOTALL)
for i, t in enumerate(th_texts):
    print(f"{i+1}: {t.strip()}")
