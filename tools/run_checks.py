import re

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("================================================================")
print("(1) GREP FOR ada|48 ?gb|gen ?4:")
p1 = re.compile(r'ada|48\s?gb|gen\s?4', re.IGNORECASE)
m1 = p1.findall(text)
print(f"Total occurrences: {len(m1)}")
if m1:
    print("Matches:", m1)
else:
    print("PASS: 0 matches found.")

print("\n================================================================")
print("(2) GREP FOR 'data: [' / 'const .* = [0-9' LITERAL ARRAYS IN <script>:")
script_match = re.search(r'<script>(.*?)</script>', text, re.DOTALL)
if script_match:
    script_text = script_match.group(1)
    lines = script_text.split('\n')
    p2_data = re.compile(r'data:\s*\[[0-9]')
    p2_const = re.compile(r'const\s+\w+\s*=\s*\[[0-9]')
    m2_data = [(i+1, l.strip()) for i, l in enumerate(lines) if p2_data.search(l)]
    m2_const = [(i+1, l.strip()) for i, l in enumerate(lines) if p2_const.search(l)]
    print(f"data: [0-9 matches in <script>: {len(m2_data)}")
    for ln, l in m2_data:
        print(f"  Line {ln}: {l[:110]}")
    print(f"const .* = [0-9 matches in <script>: {len(m2_const)}")
    for ln, l in m2_const:
        print(f"  Line {ln}: {l[:110]}")
    if len(m2_data) == 0 and len(m2_const) == 0:
        print("PASS: 0 literal numeric arrays found in <script>.")

print("\n================================================================")
print("(3) GREP FOR proves|superiority|recommended|sweet spot|100% passed|49.2|0.04 ms|1.8%|14.38|~350K:")
p3 = re.compile(r'proves|superiority|recommended|sweet spot|100% passed|49\.2|0\.04\s*ms|1\.8%|14\.38|~350K', re.IGNORECASE)
lines_all = text.split('\n')
m3 = [(i+1, l.strip()) for i, l in enumerate(lines_all) if p3.search(l)]
print(f"Total occurrences across dashboard: {len(m3)}")
for ln, l in m3:
    print(f"  Line {ln}: {l[:110]}")
if len(m3) == 0:
    print("PASS: 0 matches found.")

print("\n================================================================")
print("(4) COUNT OF EVIDENCE ROWS RENDERED:")
p4 = re.compile(r'"row_id":\s*"([^"]+)"')
m4 = p4.findall(text)
print(f"Count of evidence rows rendered in EVIDENCE_DATA: {len(m4)}")
if len(m4) == 59:
    print("PASS: Exactly 59 evidence rows rendered.")
else:
    print(f"FAIL: Expected 59, got {len(m4)}")
print("================================================================")
