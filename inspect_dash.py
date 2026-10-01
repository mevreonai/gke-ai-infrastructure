import re

html_path = r'c:\Users\ayu23\OneDrive\Desktop\tpu\v9_runs\dashboard\MASTER_CHARACTERIZATION_DASHBOARD_V9.html'
with open(html_path, 'r', encoding='utf-8') as f:
    text = f.read()

sections = re.findall(r'<section[^>]*id="([^"]+)"[^>]*>', text)
print("Sections found:", sections)

for s in sections:
    pos = text.find(f'id="{s}"')
    snippet = text[pos:pos+300]
    first_line = snippet.split('\n')[0]
    print(f"[{s}] -> {first_line[:80]}")
