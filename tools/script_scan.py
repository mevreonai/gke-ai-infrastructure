import re

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')

# Find line ranges of script tags
script_ranges = []
in_script = False
start_line = 0

for i, line in enumerate(lines):
    line_no = i + 1
    if '<script' in line and not in_script:
        in_script = True
        start_line = line_no
    if '</script>' in line and in_script:
        in_script = False
        script_ranges.append((start_line, line_no))

print(f"Script ranges in file: {script_ranges}")

# Regex for literal array with 2+ numbers: e.g. [1, 2] or [0.1, 0.2]
array_num_pattern = re.compile(r'\[\s*-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+\s*\]')
# Regex for object array with numbers: e.g. [ { ... 123 ... } ]
obj_num_pattern = re.compile(r'\[\s*\{\s*[^}]*\b[a-zA-Z_]+\s*:\s*-?\d+(?:\.\d+)?')

hits = []
for start, end in script_ranges:
    for l_idx in range(start - 1, end):
        line_str = lines[l_idx]
        file_line = l_idx + 1
        
        # Check if line is within EVIDENCE_DATA / SCALE_OUT_DATA definition
        if array_num_pattern.search(line_str):
            hits.append((file_line, "ARRAY_NUM", line_str.strip()))
        elif obj_num_pattern.search(line_str):
            hits.append((file_line, "OBJ_ARRAY_NUM", line_str.strip()))

print(f"Total script scan hits: {len(hits)}")
for h in hits:
    print(f"Line {h[0]}: [{h[1]}] -> {h[2][:100]}")
