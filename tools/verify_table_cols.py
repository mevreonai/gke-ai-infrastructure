import sys, re

dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

# Check headers count
idx = h.find("perf-evidence-table-container")
idx_th = h.find("<thead>", idx)
idx_th_end = h.find("</thead>", idx_th)
headers = re.findall(r'<th[^>]*>', h[idx_th:idx_th_end])
print(f"Total headers: {len(headers)}")

# Check cells count on rows
rows = re.findall(r'<tr class="ev-row"[^>]*>(.*?)</tr>', h, re.DOTALL)
print(f"Total rows: {len(rows)}")
cell_counts = set()
for r in rows:
    tds = re.findall(r'<td[^>]*>', r)
    cell_counts.add(len(tds))

print(f"Cell counts across rows: {cell_counts}")
