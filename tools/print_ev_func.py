import sys
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("window.openEvidenceForFinding = function")
end_idx = h.find("};", idx)
print(h[idx:end_idx+2])
