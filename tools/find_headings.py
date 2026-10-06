import sys, re
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

headings = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', h)
for hd in headings[:25]:
    clean = re.sub(r'<[^>]+>', '', hd).strip()
    if clean:
        print(f"  {clean}")
