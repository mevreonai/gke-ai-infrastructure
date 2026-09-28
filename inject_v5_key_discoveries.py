# inject_v5_key_discoveries.py
import re
import sys
import os

with open("scratch/kd_bundle.py", "r", encoding="utf-8") as f:
    code = f.read()

ns = {}
exec(code, ns)
CSS_EXTRA = ns["CSS_EXTRA"]
TAB_HTML = ns["TAB_HTML"]
FULL_JS = ns["FULL_JS"]

files = [
    'v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/dashboards/v4_dashboard/index.html',
    'v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/release_specs/index.html'
]

for file_path in files:
    print(f"Processing {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update CSS
    # Look for /* === KEY DISCOVERIES TAB STYLING === */ ...
    css_start = content.find("/* === KEY DISCOVERIES TAB STYLING === */")
    if css_start == -1:
        print(f"  Warning: CSS marker not found in {file_path}")
        continue
    
    # Check if CSS_EXTRA is already present
    if "/* === 10-FINDING DEEP EXPLORER (V5 MULTI-PAGE ARCHITECTURE) === */" not in content:
        # Insert CSS_EXTRA after the existing CSS section before the closing </style>
        style_close = content.find("</style>", css_start)
        if style_close != -1:
            content = content[:style_close] + "\n" + CSS_EXTRA + "\n" + content[style_close:]
            print("  CSS injected successfully.")
    else:
        # Replace existing CSS_EXTRA
        p_start = content.find("/* === 10-FINDING DEEP EXPLORER (V5 MULTI-PAGE ARCHITECTURE) === */")
        style_close = content.find("</style>", p_start)
        content = content[:p_start] + CSS_EXTRA + "\n" + content[style_close:]
        print("  CSS replaced successfully.")

    # 2. Update HTML
    # We want to replace <section class="tabpage" id="keydiscoveries"> ... </section> and any deep modal following it up to <section class="tabpage" id="scaleup">
    html_pattern = re.compile(r'(<!--\s*KEY DISCOVERIES TAB.*?-->\s*<section class="tabpage" id="keydiscoveries">.*?</section>)(.*?)(?=<section class="tabpage" id="scaleup">)', re.DOTALL)
    m = html_pattern.search(content)
    if not m:
        # Try finding id="keydiscoveries" directly
        sec_start = content.find('<section class="tabpage" id="keydiscoveries">')
        scaleup_start = content.find('<section class="tabpage" id="scaleup">')
        if sec_start != -1 and scaleup_start != -1:
            content = content[:sec_start] + TAB_HTML + "\n\n" + content[scaleup_start:]
            print("  HTML replaced using index search.")
        else:
            print("  Error: Could not locate keydiscoveries section in HTML!")
            continue
    else:
        content = content[:m.start()] + TAB_HTML + "\n\n" + content[m.end():]
        print("  HTML replaced using regex.")

    # 3. Update JS
    # Replace KD_DETAILS_STORE and modal handlers with FULL_JS
    # Find where KD_DETAILS_STORE starts
    js_start = content.find("// Deep Detail Modal Handler")
    if js_start == -1:
        js_start = content.find("const KD_DETAILS_STORE =")
    if js_start == -1:
        js_start = content.find("// === 10-FINDING MULTI-PAGE & SUB-POPUP CONTROLLER (V5 ARCHITECTURE) ===")
    
    if js_start != -1:
        script_close = content.find("</script>", js_start)
        if script_close != -1:
            content = content[:js_start] + FULL_JS + "\n" + content[script_close:]
            print("  JS updated successfully.")
        else:
            print("  Error: Could not find </script> after JS start!")
    else:
        # Fallback: insert before </script></body>
        script_close = content.rfind("</script>")
        if script_close != -1:
            content = content[:script_close] + "\n" + FULL_JS + "\n" + content[script_close:]
            print("  JS inserted before </script>.")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Saved {file_path} (new size: {len(content)} bytes)")

print("All files updated successfully.")
