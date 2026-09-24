import re
from collections import Counter

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
print(f"Total lines: {len(lines)}")

# Canvases
canvases = re.findall(r'<canvas[^>]*id=["\']([^"\']+)["\']', text)
canvas_counts = Counter(canvases)
duplicates_canvas = {k: v for k, v in canvas_counts.items() if v > 1}
print(f"Total canvases: {len(canvases)}")
print(f"Duplicate canvas IDs: {duplicates_canvas}")

# Script functions
funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', text)
func_counts = Counter(funcs)
duplicates_func = {k: v for k, v in func_counts.items() if v > 1}
print(f"Total function definitions: {len(funcs)}")
print(f"Duplicate functions: {duplicates_func}")

# Search for where charts are initialized
new_chart_calls = re.findall(r'new\s+Chart\s*\(\s*document\.getElementById\(\s*[\'"]([^\'"]+)[\'"]\s*\)', text)
print(f"new Chart calls: {len(new_chart_calls)}")
chart_counts = Counter(new_chart_calls)
print(f"Charts initialized multiple times: { {k: v for k, v in chart_counts.items() if v > 1} }")

# Check why line count grew
# Let's count lines per section
tab_divs = re.findall(r'<div\s+id=["\']tab-([^"\']+)["\']', text)
print(f"Tab divs: {tab_divs}")

script_blocks = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
print(f"Script blocks count: {len(script_blocks)}")
for i, sb in enumerate(script_blocks):
    print(f"  Script block {i+1} lines: {len(sb.splitlines())}")
