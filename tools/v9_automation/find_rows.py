import re

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'<tr class="ev-row" id="ev-row-EV-07[678]".*?</tr>', text, re.DOTALL)
import sys
for m in matches:
    sys.stdout.buffer.write(b"--- MATCH ---\n" + m.encode("utf-8") + b"\n")
