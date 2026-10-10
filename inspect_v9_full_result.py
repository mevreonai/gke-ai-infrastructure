import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    c = f.read()

for m in re.finditer(r'data-tab="([^"]+)"', c):
    idx = m.start()
    print(m.group(0), 'at index', idx, 'snippet:', repr(c[max(0, idx-40):min(len(c), idx+60)]))
