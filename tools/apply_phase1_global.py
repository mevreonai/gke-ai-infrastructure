import json
import re

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('data/evidence.json', 'r', encoding='utf-8') as f:
    evidence_data = json.load(f)

print(f"Loaded {len(evidence_data)} evidence rows.")

# 1. Hardware string replacements
html = html.replace("RTX PRO 6000 — architect-grade", "NVIDIA RTX PRO 6000 Blackwell Server Edition (96GB GDDR7, PCIe Gen5) — architect-grade")
html = html.replace("61.7% of 48GB VRAM allocated (18.4GB free)", "30.8% of 96GB GDDR7 allocated (66.4GB free)")
html = html.replace("Single-Node Empirical Benchmark Matrix (Kimi 48B on RTX 6000 Ada)", "Single-Node Empirical Benchmark Matrix (Kimi-Linear-48B on RTX PRO 6000 Blackwell Server Edition)")
html = html.replace("Node 0 & Node 1 uniform load across 16x RTX 6000 Ada", "Node 0 & Node 1 uniform load across 16x RTX PRO 6000 Blackwell")
html = html.replace("leaving ample headroom on 48GB Ada GPUs.", "leaving ample headroom on 96GB GDDR7 Blackwell GPUs.")
html = html.replace("48GB GPU VRAM Memory Pool Allocation", "96GB GPU VRAM Memory Pool Allocation")
html = html.replace("PCIe Gen4 x16 Transfer Latency vs Tensor Size", "PCIe Gen5 x16 Transfer Latency vs Tensor Size")
html = html.replace("Total VRAM (48 GB)", "Total VRAM (96 GB)")
html = html.replace("max: 48", "max: 96")
html = html.replace("PCIe Gen4 x16 Transfer Rate (GB/s)", "PCIe Gen5 x16 Transfer Rate (GB/s)")
html = html.replace("GCP Blackwell RTX PRO 6000", "GCP Blackwell RTX PRO 6000 Server Edition")
html = html.replace("16x RTX 6000 Ada", "16x RTX PRO 6000 Blackwell")

# 2. Badge Taxonomy in Header: Replace MODELED-K3 with DERIVED
html = html.replace(
    '<span class="pill-badge badge-k3"><span class="dot"></span>MODELED-K3</span>',
    '<span class="pill-badge badge-derived"><span class="dot"></span>DERIVED</span>'
)

# Also ensure .badge-derived styling is in CSS
badge_derived_css = """
  .badge-derived { background: #3b0764; color: #c084fc; border: 1px solid #7e22ce; }
  .badge-derived .dot { background: #a855f7; }
"""
if ".badge-derived" not in html:
    html = html.replace(".badge-k3 .dot { background: #a855f7; }", ".badge-k3 .dot { background: #a855f7; }\n" + badge_derived_css)

# 3. Header Timestamps & Live status
old_time_header = """    <div class="time-live-badge">
      <span>Apr 27, 2025 14:32</span>
      <span><span class="live-dot"></span> Live</span>
    </div>
    <div class="disclaimer-sub">
      Do not scale absolute 48B latency to Kimi K3. GCP network results are not local 10GbE measurements.
    </div>"""

new_time_header = """    <div class="time-live-badge">
      <span>Latest Run: Apr 27, 2025 14:32 (pending re-validation)</span>
      <span style="color:#64748b;">|</span>
      <span>Build: 21 Sep 2026</span>
      <span style="color:#64748b;">|</span>
      <span style="color:#94a3b8;"><span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#64748b;"></span> Snapshot (Static)</span>
    </div>
    <div style="font-size:8.5px; color:#cbd5e1; display:flex; gap:10px; margin-top:2px;">
      <span>Suite: <strong style="color:#38bdf8;">v6</strong></span>
      <span>Git SHA: <strong style="color:#fbbf24;">NOT CAPTURED</strong></span>
      <span>Manifest Hash: <strong style="color:#fbbf24;">NOT CAPTURED</strong></span>
      <span>Coverage: <strong style="color:#34d399;">59/64 Configured</strong> (6 absent, 1 extra)</span>
    </div>
    <div class="disclaimer-sub" style="margin-top:2px;">
      Do not scale absolute 48B surrogate latency to Kimi K3. GCP network results are not local 10GbE measurements. 51/59 rows pending raw production re-validation (qualification 8/8 validated).
    </div>"""

html = html.replace(old_time_header, new_time_header)

# 4. Inject Single Evidence Data Layer right after <script> opening
evidence_json_str = json.dumps(evidence_data, indent=2)
data_layer_code = f"""
<script>
// Authoritative Evidence Data Layer (Loaded from data/evidence.json - 59 rows)
const EVIDENCE_DATA = {evidence_json_str};

// Scale-Out Dataset (Current UI values pending raw production validation)
const SCALE_OUT_DATA = [
  {{ topology: 'TP4 / PP4', ttft_128k_ms: 1723.7, tpot_ms: 5.53, output_tok_s: 30.9, traffic_gb_s: 1.2, provenance: 'current UI value pending raw re-validation', evidence_class: 'MEASURED-48B' }},
  {{ topology: 'Forced TP4 / PP2', ttft_128k_ms: 2646.6, tpot_ms: 5.43, output_tok_s: 21.4, traffic_gb_s: 8.6, provenance: 'current UI value pending raw re-validation', evidence_class: 'MEASURED-48B' }},
  {{ topology: 'TP8 / PP2', ttft_128k_ms: 2817.6, tpot_ms: 7.47, output_tok_s: 19.5, traffic_gb_s: 2.4, provenance: 'current UI value pending raw re-validation', evidence_class: 'MEASURED-48B' }},
  {{ topology: 'TP16 / PP1', ttft_128k_ms: 6024.9, tpot_ms: 11.35, output_tok_s: 9.5, traffic_gb_s: 22.4, provenance: 'current UI value pending raw re-validation', evidence_class: 'MEASURED-48B' }}
];

// Helper Query Functions
function getEvidenceRow(caseName, bench) {{
  return EVIDENCE_DATA.find(r => r.case === caseName && r.bench === bench);
}}

function getCaseRows(caseName) {{
  return EVIDENCE_DATA.filter(r => r.case === caseName);
}}
"""

html = html.replace("<script>\n// Tab Switching Controller", data_layer_code + "\n// Tab Switching Controller")

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Phase 1 Global P0 applied to MASTER_CHARACTERIZATION_DASHBOARD.html successfully.")
