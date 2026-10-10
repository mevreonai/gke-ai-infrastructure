import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html', 'r', encoding='utf-8') as f:
    v8 = f.read()

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    v9 = f.read()

print(f"V8 Dashboard size: {len(v8):,} bytes")
print(f"V9 Dashboard size: {len(v9):,} bytes")

# Check what panels exist in V9 that are not in V8 or vice versa
panels = ['executive', 'keyfinds', 'keydiscoveries', 'scaleup', 'scaleout', 'long', 'sched', 'profiler', 'evidence']
for p in panels:
    print(f"Panel '{p}' in V8: {f'id=\"{p}\"' in v8} | in V9: {f'id=\"{p}\"' in v9}")

# Check data objects in V9
import re
scripts_v9 = re.findall(r'<script>(.*?)</script>', v9, re.DOTALL)
print(f"Scripts count in V9: {len(scripts_v9)}")
for i, s in enumerate(scripts_v9):
    print(f"Script {i} length: {len(s)}")
    vars_found = re.findall(r'(?:window\.|var |let |const )([A-Z0-9_]{3,30})\s*=', s)
    if vars_found:
        print(f"   Variables defined: {vars_found[:10]}")
