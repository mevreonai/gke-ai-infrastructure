import sys
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("Cluster, Stack &amp; Campaign Readiness Audit")
end_idx = h.find("</table>", idx)
print(h[idx-100:idx+2500])
