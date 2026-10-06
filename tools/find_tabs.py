import sys, re
sys.stdout.reconfigure(encoding="utf-8")
with open(r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html", "r", encoding="utf-8") as f:
    h = f.read()

tabs = re.findall(r'<div[^>]*class="[^"]*tab-content[^"]*"[^>]*id="([^"]+)"', h)
if not tabs:
    tabs = re.findall(r'id="([a-zA-Z0-9_-]*(?:tab|page|panel)[a-zA-Z0-9_-]*)"', h, re.IGNORECASE)
print("Detected panels/tabs:", tabs[:20])

nav_buttons = re.findall(r'<button[^>]*onclick="[^"]*switchTab\([^)]*\)[^"]*"[^>]*>.*?</button>', h)
print("Nav buttons:", nav_buttons[:10])
