import difflib
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html', 'r', encoding='utf-8') as f:
    v8_lines = f.readlines()

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    v9_lines = f.readlines()

print(f"V8 lines: {len(v8_lines)}")
print(f"V9 lines: {len(v9_lines)}")

# Look at header/title differences
for i in range(min(50, len(v8_lines), len(v9_lines))):
    if v8_lines[i] != v9_lines[i]:
        print(f"Line {i+1} diff:")
        print("  V8:", repr(v8_lines[i].strip()))
        print("  V9:", repr(v9_lines[i].strip()))
