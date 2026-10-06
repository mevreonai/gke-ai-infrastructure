import sys, re
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

idx = h.find("function renderFindingHtmlClient")
if idx != -1:
    print(h[idx:idx+1500])
else:
    # search where renderFindingHtmlClient is defined
    m = re.search(r'renderFindingHtmlClient\s*=\s*function', h)
    if m:
        print(h[m.start():m.start()+1500])
