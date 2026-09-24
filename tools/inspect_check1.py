import re

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

p = re.compile(r'ada|48\s?gb|gen\s?4', re.IGNORECASE)
for idx, l in enumerate(lines):
    m = p.findall(l)
    if m:
        safe_l = l.strip()[:100].encode('ascii', 'replace').decode()
        print(f"Line {idx+1}: {m} -> {safe_l}")
