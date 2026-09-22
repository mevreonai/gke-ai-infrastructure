import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open(r'c:\Users\ayu23\OneDrive\Desktop\tpu\MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    html = f.read()

print(f"Total HTML size: {len(html)} bytes")

# 1. Tabs
tabs = ['executive', 'scaleup', 'scaleout', 'long', 'sched', 'profiler', 'evidence']
for t in tabs:
    m = re.search(r'<section[^>]*id=["\']' + t + r'["\']', html)
    print(f"Tab [{t:10s}]: {'FOUND' if m else 'MISSING'}")

# 2. Canvases
canvases = re.findall(r'<canvas id=["\']([^"\']+)["\']', html)
print(f"\nTotal Chart Canvases: {len(canvases)} / 26")
for i, c in enumerate(canvases):
    print(f"  Canvas {i+1:02d}: {c}")

# 3. Evidence rows
ev_rows = re.findall(r'<tr class=["\']ev-row["\']', html)
print(f"\nEvidence Rows: {len(ev_rows)} / 126")

# 4. Check for placeholders
placeholders = re.findall(r'<span class=["\']placeholder["\']>(.*?)</span>', html)
print(f"\nRemaining span.placeholder: {len(placeholders)}")
for p in placeholders:
    print("  Remaining placeholder:", p)

post_run_cells = re.findall(r'<td>post-run</td>', html)
print(f"Remaining <td>post-run</td>: {len(post_run_cells)}")

unknown_cells = re.findall(r'<span class=["\']status s-unknown["\']>UNKNOWN</span>', html)
print(f"Remaining s-unknown badges: {len(unknown_cells)}")

# 5. Section titles
sec_titles = re.findall(r'<div class=["\']section-title["\']>(.*?)</div>', html)
print(f"\nSection Titles ({len(sec_titles)}):")
for st in sec_titles:
    print("  Title:", re.sub(r'<[^>]+>', '', st).strip())

# 6. Cards
cards = re.findall(r'<div class=["\']card(?:\s+[^"\']*)?["\']', html)
print(f"\nTotal Cards in Dashboard: {len(cards)}")
