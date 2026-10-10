import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    c = f.read()

print("=== INSPECTING TP16, PP2, AND OFFLOAD IN V9_FULL_RESULT ===")

# Search for TP16 occurrences in tables
for m in re.finditer(r'<tr>.*?TP16.*?</tr>', c, re.DOTALL):
    snippet = re.sub(r'\s+', ' ', m.group(0))
    if any(k in snippet for k in ['BLOCKED', 'status', 'Scale-Out', 'Decision', 'Evidence', 'cap']):
        # Clean unicode characters that might fail terminal printing
        clean_snippet = snippet.encode('ascii', errors='replace').decode('ascii')
        print("TP16 row:", clean_snippet[:220])
        print("-" * 50)

# Search for PP2 occurrences
for m in re.finditer(r'<tr>.*?PP2.*?</tr>', c, re.DOTALL):
    snippet = re.sub(r'\s+', ' ', m.group(0))
    if any(k in snippet for k in ['partition', 'idle', 'stage', 'Scale-Out']):
        clean_snippet = snippet.encode('ascii', errors='replace').decode('ascii')
        print("PP2 row:", clean_snippet[:220])
        print("-" * 50)

# Search for offload occurrences
for m in re.finditer(r'<tr>.*?offload.*?</tr>', c, re.DOTALL | re.IGNORECASE):
    snippet = re.sub(r'\s+', ' ', m.group(0))
    clean_snippet = snippet.encode('ascii', errors='replace').decode('ascii')
    print("Offload row:", clean_snippet[:220])
    print("-" * 50)
