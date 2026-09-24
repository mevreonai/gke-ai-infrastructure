import os
import re
import sys
import io
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

html_path = 'MASTER_CHARACTERIZATION_DASHBOARD.html'
with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

search_terms = [
    '0.04', '1.8%', '49.2', '22.4', '74.2', '21.8', '11.2', '12.6', '8.2', 
    '14.38', '32K', '64K', '256K', 'within node', 'TCP', 'saturat', '1,048,576'
]

print("=== 1. GREP INVENTORY ===")
for term in search_terms:
    matches = []
    for idx, l in enumerate(lines, 1):
        if term.lower() in l.lower():
            matches.append((idx, l.strip()))
    print(f"\n--- Term '{term}' ({len(matches)} matches) ---")
    for m in matches:
        print(f"  L{m[0]}: {m[1]}")

print("\n=== 2. STRUCTURAL ELEMENTS INVENTORY ===")
# Diagrams: TP16/PP1 and forced TP4/PP2
for idx, l in enumerate(lines, 1):
    if 'TP16 / PP1' in l or 'Forced cross-node' in l or 'Forced TP4' in l:
        print(f"  Topology Header L{idx}: {l.strip()}")
    if 'Serving Envelope' in l:
        print(f"  Serving Envelope L{idx}: {l.strip()}")
    if 'Runtime Reserve & vLLM Breakdown' in l:
        print(f"  Runtime Reserve Bar L{idx}: {l.strip()}")
    if '8/8 Passed' in l:
        print(f"  8/8 Status Card L{idx}: {l.strip()}")
    if 'evidenceBenchFilter' in l:
        print(f"  Evidence Bench Filter L{idx}: {l.strip()}")

# Search for variable arrays (const/let/var x = [...])
print("\n=== 3. VARIABLE ARRAYS IN SCRIPT ===")
in_script = False
for idx, l in enumerate(lines, 1):
    if '<script' in l: in_script = True
    if '</script>' in l: in_script = False
    if in_script:
        if re.search(r'(const|let|var)\s+\w+\s*=\s*\[', l):
            print(f"  L{idx}: {l.strip()}")

# Item 4: Check where queue_mean_s_from_hist came from
print("\n=== 4. QUEUE_MEAN_S_FROM_HIST SEARCH ===")
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.py') or f.endswith('.csv') or f.endswith('.json') or f.endswith('.html'):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
                    if 'queue_mean_s_from_hist' in content:
                        print(f"  Found queue_mean_s_from_hist in: {p}")
            except Exception as e:
                pass

# Item 5: Check 14.38s prefix formula in HTML
print("\n=== 5. PREFIX 14.38s CHECK ===")
for idx, l in enumerate(lines, 1):
    if '14.38' in l:
        print(f"  L{idx}: {l.strip()}")
    if 'canvasLongCtxPrefix' in l:
        print(f"  Prefix Canvas L{idx}: {l.strip()}")

# Item 6: Count copies of MASTER_CHARACTERIZATION_DASHBOARD.html in workspace
print("\n=== 6. MASTER_CHARACTERIZATION_DASHBOARD.HTML SEARCH ===")
for root, dirs, files in os.walk('.'):
    for f in files:
        if f == 'MASTER_CHARACTERIZATION_DASHBOARD.html':
            full_p = os.path.abspath(os.path.join(root, f))
            print(f"  Found dashboard copy: {full_p}")
