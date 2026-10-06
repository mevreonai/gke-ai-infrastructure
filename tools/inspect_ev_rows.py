import sys
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find('id="ev-row-EV-001"')
end_idx = h.find('</tr>', idx)
row1 = h[idx:end_idx+5]
tds = row1.count('<td>')
print(f"EV-001 has {tds} <td> cells under 16 headers:")
print(row1)

idx2 = h.find('id="ev-row-EV-050"')
end_idx2 = h.find('</tr>', idx2)
row2 = h[idx2:end_idx2+5]
tds2 = row2.count('<td>')
print(f"\nEV-050 has {tds2} <td> cells:")
print(row2)
