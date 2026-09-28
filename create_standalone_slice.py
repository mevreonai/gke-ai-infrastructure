import re
import os

print("Extracting exact Key Discoveries slice from master dashboard...")

with open("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html", "r", encoding="utf-8") as f:
    c = f.read()

# 1. Styles
style_start = c.find('<style>')
style_end = c.find('</style>') + len('</style>')
styles = c[style_start:style_end]

# 2. Key Discoveries section
kd_start = c.find('<section class="tabpage" id="keydiscoveries">')
kd_end = c.find('</section>', kd_start) + len('</section>')
kd_section = c[kd_start:kd_end]

# Ensure section is displayed in standalone mode
kd_section = kd_section.replace('<section class="tabpage" id="keydiscoveries">', '<section class="tabpage active" id="keydiscoveries" style="display:block !important">')

# In standalone mode, fold 60-sec map list by default
kd_section = kd_section.replace('<details class="kd-map-card" id="kd-map-details" open>', '<details class="kd-map-card" id="kd-map-details">')
kd_section = kd_section.replace('Fold 60-sec Map ▲', 'Unfold 60-sec Map ▼')

# 3. Evidence popup modal & Subpage modal
modal_backdrop_start = c.find('<div id="evidence-popup-backdrop"')
modal_modal_start = c.find('<div id="evidence-popup-modal"')
modal_end = c.find('<!-- END EVIDENCE POPUP MODAL -->')
if modal_end != -1:
    evidence_modal_html = c[modal_backdrop_start:modal_end]
else:
    # find closing div for evidence-popup-modal
    close_div = c.find('</div>\n  </div>', modal_modal_start) + len('</div>\n  </div>')
    evidence_modal_html = c[modal_backdrop_start:close_div]

# Deep subpage modal (already inside kd_section or check)
subpage_modal_needed = ""
if 'id="kd-deep-subpage-modal"' not in kd_section:
    sub_start = c.find('<div id="kd-deep-subpage-backdrop"')
    if sub_start != -1:
        sub_end = c.find('</div>\n  </div>', sub_start) + len('</div>\n  </div>')
        subpage_modal_needed = c[sub_start:sub_end]

# 4. JavaScript dependencies
# PROFILER_REGISTRY (start to before openEvidencePopup)
p_reg_start = c.find('window.PROFILER_REGISTRY = {')
open_ev_start = c.find('window.openEvidencePopup = function')
p_reg_js = c[p_reg_start:open_ev_start]

# openEvidencePopup & closeEvidencePopup
close_ev_start = c.find('window.closeEvidencePopup = function')
close_ev_end = c.find('};\n\n// Universal Copy JSON Helper', close_ev_start)
if close_ev_end == -1:
    close_ev_end = c.find('};', close_ev_start + 100) + 2
ev_popup_js = c[open_ev_start:close_ev_end]

# CANONICAL_DASHBOARD_DATA
canon_start = c.find('window.CANONICAL_DASHBOARD_DATA = {')
canon_end = c.find('};\nwindow.EXECUTIVE_DISCOVERIES', canon_start)
if canon_end == -1:
    canon_end = c.find('};\n', canon_start) + 2
else:
    canon_end += 2
canon_data_js = c[canon_start:canon_end]

# KD_PAGES_DATA & Controller JS
kd_data_start = c.find('window.KD_PAGES_DATA = [')
kd_data_end = c.find('</script>', kd_data_start)
kd_ctrl_js = c[kd_data_start:kd_data_end]

# Compose Standalone HTML Document
standalone_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>V8 Key Discoveries — MoonshotAI Kimi-K1.5-Preview Characterization</title>
  
  <!-- Chart.js Engine -->
  <script src="chart.umd.js"></script>
  <script>
    if (typeof Chart === 'undefined') {{
      document.write('<script src="https://cdn.jsdelivr.net/npm/chart.js"><\\/script>');
    }}
  </script>

  {styles}

  <style>
    /* Standalone display overrides */
    body {{
      background: var(--bg, #0b0f19);
      color: var(--text, #e2e8f0);
      margin: 0;
      padding: 0 0 80px 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    section.tabpage {{
      display: block !important;
      padding-top: 10px;
    }}
    .kd-standalone-banner {{
      background: linear-gradient(90deg, #1e1b4b 0%, #0f172a 100%);
      border-bottom: 1px solid rgba(99, 102, 241, 0.3);
      padding: 10px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: #94a3b8;
    }}
    .kd-standalone-banner b {{
      color: #c7d2fe;
    }}
  </style>
</head>
<body>

  <!-- Top Standalone Header Banner -->
  <div class="kd-standalone-banner">
    <div>
      <b>Performance Characterization Suite</b> &middot; Exact Standalone Slice: <b>Key Discoveries V6</b>
    </div>
    <div style="display:flex;gap:12px;align-items:center">
      <span class="badge b-purple">10 Key Findings</span>
      <span class="badge b-green">Full 10-Page Explorer</span>
      <span class="badge b-cyan">20 Dynamic Charts</span>
    </div>
  </div>

  <!-- EXACT KEY DISCOVERIES TAB CONTENT SLICE -->
  {kd_section}

  <!-- EXACT EVIDENCE POPUP MODAL -->
  {evidence_modal_html}

  {subpage_modal_needed}

  <!-- CONTROLLER & RUNTIME TELEMETRY SCRIPTS -->
  <script>
  {p_reg_js}

  {ev_popup_js}

  {canon_data_js}

  {kd_ctrl_js}

  // Standalone Auto-Render on DOM Load
  document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
      if (typeof window.openFindingSubPage === 'function') {{
        window.openFindingSubPage(1, '');
      }}
    }}, 60);
  }});
  </script>
</body>
</html>
"""

# Save standalone dashboard
out_file_root = "KEY_DISCOVERIES_STANDALONE_DASHBOARD.html"
with open(out_file_root, "w", encoding="utf-8") as f:
    f.write(standalone_html)
print(f"Created standalone dashboard: {out_file_root} ({len(standalone_html):,} bytes)")

out_file_v4 = "v8_full_results/dashboards/v4_dashboard/KEY_DISCOVERIES_STANDALONE_DASHBOARD.html"
with open(out_file_v4, "w", encoding="utf-8") as f:
    f.write(standalone_html)
print(f"Synchronized: {out_file_v4}")

out_file_release = "v8_full_results/release_specs/KEY_DISCOVERIES_STANDALONE_DASHBOARD.html"
with open(out_file_release, "w", encoding="utf-8") as f:
    f.write(standalone_html)
print(f"Synchronized: {out_file_release}")

print("\nSUCCESS: Standalone Key Discoveries dashboard slice created cleanly without altering original dashboards!")
