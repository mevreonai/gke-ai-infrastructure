import re

tokens = [
    "312.0", "485.0", "840.0", "1120.0", "1.15", "2.14", "2.45", "7.90", "10.45",
    "19.8", "29.5", "71.20", "48.20", "26.50", "58.88", "29.44", "1.84", "7.36",
    "14.72", "49.20", "2.80", "0.12", "0.42", "1.58", "3.12", "0.28", "0.98",
    "3.75", "7.42", "74.2", "28.4", "43.8", "94.8", "21.8", "21.9", "38.0",
    "12.6", "8.2", "22.4", "24.2", "12.3", "3.8", "7.7", "28.5", "COMM_DERIVED",
    "Degradation", "Scaling"
]

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Scanning {len(lines)} lines for {len(tokens)} tokens...")
hits = []
for idx, line in enumerate(lines):
    line_no = idx + 1
    for t in tokens:
        if t in ["COMM_DERIVED", "Degradation", "Scaling"]:
            pattern = re.compile(re.escape(t))
        else:
            # Word/numeric boundary for numbers
            pattern = re.compile(r'(?<![0-9.])' + re.escape(t) + r'(?![0-9.])')
        if pattern.search(line):
            hits.append((line_no, t, line.strip()))

print(f"Total hits: {len(hits)}")
for h in hits:
    safe_text = h[2][:110].encode('ascii', 'replace').decode()
    print(f"Line {h[0]}: [{h[1]}] -> {safe_text}")
