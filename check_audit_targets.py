import re
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open('v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

print('=== 1. exactMap prefix matches ===')
for m in re.finditer(r'[\'"]tp4_prefix[^\n]+', text):
    print('  ', m.group(0))

print('\n=== 2. Lines with EV-073, EV-074, EV-075 around prefix ===')
for i, line in enumerate(text.splitlines(), 1):
    if 'prefix' in line.lower() and ('ev-073' in line.lower() or 'ev-074' in line.lower() or 'ev-075' in line.lower()):
        print(f"  Line {i}: {line[:120]}")

print('\n=== 3. C2 Decision Output row (NUMA) ===')
for i, line in enumerate(text.splitlines(), 1):
    if 'Single-NUMA ring avoids' in line:
        print(f"  Line {i}: {line[:140]}")

print('\n=== 4. H5 AllReduce collective stalls ===')
for i, line in enumerate(text.splitlines(), 1):
    if 'AllReduce collective stalls' in line:
        print(f"  Line {i}: {line[:140]}")

print('\n=== 5. Profiler 22 layers / barrier ===')
for i, line in enumerate(text.splitlines(), 1):
    if '22 layers' in line or 'ring barriers' in line or 'due to cross-NUMA' in line:
        print(f"  Line {i}: {line[:140]}")

print('\n=== 6. chart_long_fp8 check ===')
for i, line in enumerate(text.splitlines(), 1):
    if 'chart_long_fp8' in line:
        print(f"  Line {i}: {line[:140]}")

print('\n=== 7. Line 6085 check (ids) ===')
lines = text.splitlines()
for i in range(max(0, 6080), min(len(lines), 6095)):
    print(f"  Line {i+1}: {lines[i]}")
