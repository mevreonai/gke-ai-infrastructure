# fix_stray_brace.py
import re

files = [
    'v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/dashboards/v4_dashboard/index.html',
    'v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/release_specs/index.html'
]

target = """// === KEY DISCOVERIES CONTROLLER (SIGNAL / ENGINEER / FORENSICS) ===

}

function focusKeyDiscovery"""

replacement = """// === KEY DISCOVERIES CONTROLLER ===

function focusKeyDiscovery"""

for fp in files:
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    if target in content:
        content = content.replace(target, replacement)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed stray brace in {fp}")
    else:
        # Try regex
        content = re.sub(r'// === KEY DISCOVERIES CONTROLLER.*?\n\s*\}\s*\n+function focusKeyDiscovery', '// === KEY DISCOVERIES CONTROLLER ===\n\nfunction focusKeyDiscovery', content)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Regex fixed in {fp}")
