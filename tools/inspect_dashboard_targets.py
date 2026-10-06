import json
import re
import os

dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
with open(dash_path, "r", encoding="utf-8") as f:
    html = f.read()

print(f"Total HTML length: {len(html):,} bytes")

banner_pattern = re.compile(r'<div class="preview-banner">.*?</div>\s*</div>', re.DOTALL)
banners = banner_pattern.findall(html)
print(f"\nFound {len(banners)} preview banners:")
for i, b in enumerate(banners):
    print(f"--- Banner {i} ---")
    print(b.strip()[:300])

coverage_matches = re.findall(r"\b(?:119|126)\s*(?:/|of)\s*126\b", html, re.IGNORECASE)
print(f"\nCoverage text matches: {coverage_matches}")

prof_matches = re.findall(r"14\s*/\s*22", html)
print(f"Profiler 14/22 matches: {len(prof_matches)}")
