import re

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

tabs = re.split(r'<div id="tab-([^"]+)" class="tab-content[^"]*">', text)
for i in range(1, len(tabs), 2):
    tab_name = tabs[i]
    tab_body = tabs[i+1]
    canvases = re.findall(r'<canvas id=["\']([^"\']+)["\']', tab_body)
    print(f"Tab [{tab_name}]: {len(canvases)} canvases -> {canvases}")
