#!/usr/bin/env python3
"""
apply_v11_extensions.py
Applies all additions from §6 and §7 of Dashboard_Fix_Verification_v1.1.md to
MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html and syncs across all copies.
"""

import sys, os, re, json, shutil

sys.stdout.reconfigure(encoding='utf-8')

MASTER_FILE = "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html"

with open(MASTER_FILE, "r", encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)
print(f"Loaded master dashboard: {orig_len} characters")

# =========================================================================
# 1. Section 6: Scope Rail Labels for Concurrency / Load
# =========================================================================
print("\n--- 1. Section 6: Adding single-node scope labels to concurrency/load panels ---")

scope_label_html = '<div class="scope-note" style="margin:4px 0 8px;padding:4px 8px;background:rgba(255,200,87,0.06);border-left:3px solid var(--amber);font-size:9.5px;color:var(--text)"><strong>Campaign Scope:</strong> Single-node local execution (TP4/PP1 &amp; TP8/PP1). Distributed layouts (TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1) were run at c=1 only; concurrency / multi-request load not yet measured in this campaign.</div>'

# Long context waterfall / concurrency card
content = content.replace(
    '<div class="card-title">TP4/PP1 vs TP8/PP1 — 1M Concurrency</div>',
    '<div class="card-title">TP4/PP1 vs TP8/PP1 — 1M Concurrency</div>\n' + scope_label_html
)

# Stall budget card (§4.5)
content = content.replace(
    '<div class="card-title">🛑 Decode Stalls Behind Other Requests\' Prefill Chunks — How Much of Per-Token Wait is Interference (§4.5)</div>',
    '<div class="card-title">🛑 Decode Stalls Behind Other Requests\' Prefill Chunks — How Much of Per-Token Wait is Interference (§4.5)</div>\n' + scope_label_html
)

# Update KD_PAGES_DATA for KD#2, #4, #5, #7, #8 with scope and decode pointer
pos_kd = content.find('window.KD_PAGES_DATA = [')
end_kd = content.find('];\n', pos_kd)
if end_kd == -1: end_kd = content.find('];', pos_kd)
kd_json_str = content[pos_kd + len('window.KD_PAGES_DATA = '):end_kd+1]
kd_data = json.loads(kd_json_str)

for p in kd_data:
    pid = p.get('id')
    if pid == 2:
        p['scope_note'] = "Single node local execution (TP4/PP1 & TP8/PP1). Distributed layouts (TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1) were run at c=1 only; concurrency not yet measured."
    elif pid == 4:
        p['scope_note'] = "Single node local execution (TP4/PP1). Distributed layouts were run at c=1 only without prefix cache sweeps."
    elif pid == 5:
        p['scope_note'] = "Single node local execution (TP4/PP1). Open-loop admission sweeps executed on single node."
    elif pid == 7:
        # §6 Item 3: Add cross-node and pipeline decode costs pointer
        p['takeaways'].append(
            "Cross-Node & Pipeline Decode Pointer: Beyond single-node TP4 vs TP8, cross-node TP16 decode incurs an inferred 208–290 µs AllReduce barrier per call (~11–16 ms of 14.9–20.1 ms TPOT; see Scale-Out §4.8 Fabric α-β panel), while pipeline layouts add +0.3–0.5 ms stage-hop overhead per token on PP2/PP4 (see §4.17 Wall-Time Budget)."
        )
    elif pid == 8:
        p['scope_note'] = "Single node local execution (TP4/PP1). Runtime knobs swept on TP4/PP1."

new_kd_json_str = json.dumps(kd_data, indent=2, ensure_ascii=False)
content = content[:pos_kd + len('window.KD_PAGES_DATA = ')] + new_kd_json_str + content[end_kd+1:]
print("  ✓ Updated window.KD_PAGES_DATA with scope notes and KD#7 decode pointers")

# =========================================================================
# 2. Section 6 Item 2: §4.7 Stage Panel PP2 Independent Confirmation
# =========================================================================
print("\n--- 2. Section 6 Item 2: Adding PP2 Independent Confirmation to §4.7 Stage Panel ---")

pp2_check_html = """
  <div style="margin-top:8px;padding:8px;background:rgba(66,201,255,0.06);border:1px solid rgba(66,201,255,0.25);border-radius:6px;font-size:11px;color:var(--text);line-height:1.4">
    <b>Independent Confirmation (PP2 Check — §6.2):</b> The two PP2 128K captures independently confirm the 3:4 attention split predicted by the layer map: Stage 0 / Stage 1 flash attention time ratio is <b>0.77</b> on TP4/PP2 (8 usable ranks) and <b>0.77</b> on TP8/PP2 (15 usable ranks), exactly corroborating the <b>0.75</b> ratio expected from the 6 vs 8 full-attention layer distribution.
  </div>
"""

if "PP2 Check — §6.2" not in content:
    content = content.replace(
        "cuts stage-0 idle 10% → 3% and shortens 512K TTFT by 3.5% on TP4/PP2!\n  </div>\n</div>",
        "cuts stage-0 idle 10% → 3% and shortens 512K TTFT by 3.5% on TP4/PP2!\n  </div>\n" + pp2_check_html + "\n</div>"
    )
    print("  ✓ Added PP2 Independent Confirmation box to §4.7 panel")

# =========================================================================
# 3. Section 6 Item 1: Profiler Kernel-Composition Card TP4/PP2 & TP8/PP2
# =========================================================================
print("\n--- 3. Section 6 Item 1: Adding TP4/PP2 and TP8/PP2 to Profiler Kernel Composition ---")

# Add chips
old_chips = '<span class="chip prof-scenario-chip" data-scenario="tp16_pp1_dist" style="cursor:pointer">TP16/PP1 Dist Prefill (128K Native)</span>'
new_chips = '<span class="chip prof-scenario-chip" data-scenario="tp4_pp2_dist" style="cursor:pointer">TP4/PP2 Dist Prefill (128K Native)</span>\n    <span class="chip prof-scenario-chip" data-scenario="tp8_pp2_dist" style="cursor:pointer">TP8/PP2 Dist Prefill (128K Native)</span>\n    <span class="chip prof-scenario-chip" data-scenario="tp16_pp1_dist" style="cursor:pointer">TP16/PP1 Dist Prefill (128K Native)</span>'

if old_chips in content:
    content = content.replace(old_chips, new_chips)
    print("  ✓ Added TP4/PP2 and TP8/PP2 scenario chips")

# Add the 6-layout prefill composition comparison table into the Kernel Composition card
comp_table_html = """
    <div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.08)">
      <div style="font-weight:700;font-size:11px;color:var(--cyan);margin-bottom:4px">📋 128K Prefill Kernel Composition Across All 6 Layouts (§6.1)</div>
      <div style="font-size:9.5px;color:var(--muted);margin-bottom:6px">Recomputed from usable per-rank exports (start-up Broadcast excluded; eager-mode prefill). Source: <code>time_budget/prefill_composition_128k_by_layout.csv</code></div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>128K Prefill Layout</th><th>Ranks</th><th>Full Attention</th><th>GEMM</th><th>MoE</th><th>KDA</th><th>AllReduce</th><th>SendRecv</th><th>Other</th></tr>
          </thead>
          <tbody>
            <tr><td><b>TP4 / PP1</b></td><td>1</td><td>23.4 %</td><td>7.8 %</td><td>14.3 %</td><td>3.2 %</td><td>46.0 %</td><td>—</td><td>5.2 %</td></tr>
            <tr><td><b>TP8 / PP1</b></td><td>1</td><td>16.2 %</td><td>5.1 %</td><td>14.6 %</td><td>2.2 %</td><td>58.0 %</td><td>—</td><td>3.9 %</td></tr>
            <tr><td><b>TP4 / PP2</b></td><td>8</td><td>19.5 %</td><td>7.0 %</td><td>12.5 %</td><td>2.9 %</td><td>43.8 %</td><td>5.5 %</td><td>8.8 %</td></tr>
            <tr><td><b>TP8 / PP2</b></td><td>15</td><td>12.5 %</td><td>4.2 %</td><td>11.9 %</td><td>1.7 %</td><td>54.8 %</td><td>5.1 %</td><td>9.9 %</td></tr>
            <tr><td><b>TP4 / PP4</b></td><td>16</td><td>14.7 %</td><td>5.3 %</td><td>9.5 %</td><td>2.2 %</td><td>43.1 %</td><td>14.9 %</td><td>10.2 %</td></tr>
            <tr><td><b>TP16 / PP1</b></td><td>12</td><td>4.8 %</td><td>2.1 %</td><td>8.9 %</td><td>1.1 %</td><td>77.6 %</td><td>—</td><td>5.4 %</td></tr>
            <tr style="background:rgba(255,255,255,0.02)"><td><b>TP4 / PP4 · 512K</b></td><td>16</td><td>43.8 %</td><td>5.3 %</td><td>6.9 %</td><td>1.7 %</td><td>22.4 %</td><td>12.8 %</td><td>7.2 %</td></tr>
          </tbody>
        </table>
      </div>
      <div style="font-size:10px;color:var(--text);margin-top:6px;line-height:1.4">
        <b>Reading:</b> Stage width dictates the AllReduce share (43–46% on 4-wide stages, 55–58% on 8-wide stages, 78% across nodes); stage count dictates SendRecv P2P share (5% at 1 boundary, 15% at 3 boundaries); Attention share is the direct inverse of both.
      </div>
    </div>
"""

if "128K Prefill Kernel Composition Across All 6 Layouts" not in content:
    content = content.replace(
        "<div><b>Pipeline Parallelism</b><span style=\"color:var(--purple)\">TP4/PP4 P2P SendRecv represents 8.3% of captured stage work; pipelining shifts traffic to stage boundaries</span></div>\n    </div>",
        "<div><b>Pipeline Parallelism</b><span style=\"color:var(--purple)\">TP4/PP4 P2P SendRecv represents 8.3% of captured stage work (Stage 0); pipelining shifts traffic to stage boundaries</span></div>\n    </div>\n" + comp_table_html
    )
    print("  ✓ Added 6-layout prefill composition comparison table")

# Add datasets to chart_prof_kernel_categories in JS
old_datasets_end = "{ label: 'TP4/PP4 Dist Prefill [Selected Stage: Stage 0 Rank 0 (40.0% AllReduce, 8.3% P2P); Pipeline Range Across Stages 38.2–42.1%] (%)', data: [40.0, 22.8, 13.2, 8.5, 2.6, 4.6, 8.3], backgroundColor: 'rgba(179,136,255,0.85)' }\n            ]"
new_datasets_end = """{ label: 'TP4/PP2 Dist Prefill [8 Usable Ranks Mean; AllReduce 43.8%, SendRecv 5.5%] (%)', data: [43.8, 19.5, 12.5, 7.0, 2.9, 3.5, 10.8], backgroundColor: 'rgba(66,201,255,0.75)' },
                { label: 'TP8/PP2 Dist Prefill [15 Usable Ranks Mean; AllReduce 54.8%, SendRecv 5.1%] (%)', data: [54.8, 12.5, 11.9, 4.2, 1.7, 3.0, 11.9], backgroundColor: 'rgba(255,200,87,0.75)' },
                { label: 'TP4/PP4 Dist Prefill [16 Usable Ranks; Stage 0: 40.0% AR, 8.3% P2P; Stages 1-3 P2P wait 17-22%] (%)', data: [43.1, 14.7, 9.5, 5.3, 2.2, 4.6, 20.6], backgroundColor: 'rgba(179,136,255,0.85)' }
            ]"""

if old_datasets_end in content:
    content = content.replace(old_datasets_end, new_datasets_end)
    print("  ✓ Added TP4/PP2 and TP8/PP2 datasets to chart_prof_kernel_categories")

# =========================================================================
# 4. Section 7: Profiler Tab Unified "Where the Time Goes" Bar Chart Panel
# =========================================================================
print("\n--- 4. Section 7: Adding Unified 'Where the Time Goes' Bar Chart Panel to Profiler Tab ---")

wall_time_panel_profiler = """
<!-- UNIFIED WHERE THE TIME GOES (WALL-TIME BUDGET) PANEL (§4.17 & §7) -->
<div class="card mb8" id="profiler-wall-time-budget-card" style="border:1px solid rgba(66,201,255,0.3);background:linear-gradient(180deg,rgba(15,23,42,0.95),rgba(20,30,55,0.98))">
  <div class="header-row">
    <div>
      <div class="card-title" style="color:var(--cyan);font-size:15px">⏱️ End-to-End Wall-Time Budget (Where the Time Goes — §4.17 / §7)</div>
      <div class="card-sub">Unified 100%-stacked horizontal breakdown of First Token (TTFT) and Inter-Token Decode (TPOT) across all 24 operating points (6 layouts × contexts + loaded points). † indicates modelled rows.</div>
    </div>
    <div style="display:flex;gap:6px;align-items:center">
      <span class="badge b-cyan"><span class="dot"></span>UNIFIED PROFILER VIEW</span>
      <span class="badge b-purple">24 OPERATING POINTS</span>
    </div>
  </div>

  <!-- Interactive Controls & Tabs -->
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0;padding:6px;background:rgba(0,0,0,0.25);border-radius:6px">
    <span style="font-size:10px;font-weight:700;color:var(--muted)">SELECT VIEW:</span>
    <button class="chip active" id="btn-budget-first" onclick="toggleBudgetView('first')" style="cursor:pointer;padding:4px 10px;font-size:10px;font-weight:700">First Token Budget (TTFT)</button>
    <button class="chip" id="btn-budget-decode" onclick="toggleBudgetView('decode')" style="cursor:pointer;padding:4px 10px;font-size:10px;font-weight:700">Decode Token Budget (TPOT)</button>
    <span style="margin-left:auto;font-size:9.5px;color:var(--dim)">Data sources: <code>time_budget/wall_time_budget_first_token.csv</code> &amp; <code>decode_token.csv</code></span>
  </div>

  <!-- Image & Interactive Stacked Charts Container -->
  <div id="budget-first-container" style="display:block">
    <div style="text-align:center;background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">
      <img src="wall_time_budget_first_token.png" alt="First Token Wall Time Budget" style="max-width:100%;height:auto;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.5)"/>
      <div style="font-size:9px;color:var(--muted);margin-top:4px">Figure E2E·A: First-Token Time Decomposition (Queue · Prefill Collectives · Pipeline Waits · Prefill Kernels · Shared Step · Overhead). Totals at right.</div>
    </div>
  </div>

  <div id="budget-decode-container" style="display:none">
    <div style="text-align:center;background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">
      <img src="wall_time_budget_decode_token.png" alt="Decode Token Wall Time Budget" style="max-width:100%;height:auto;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.5)"/>
      <div style="font-size:9px;color:var(--muted);margin-top:4px">Figure E2E·B: Decode Inter-Token Time Decomposition (Collectives · Pipeline Hops · Memory-Speed Floor · Kernels Above Floor · Waiting Behind Prefills). Totals at right.</div>
    </div>
  </div>

  <!-- Methodological Disclosures & Wave Note -->
  <div class="grid2" style="gap:8px;margin-top:8px">
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);padding:8px;border-radius:6px;font-size:10px;line-height:1.4">
      <div style="font-weight:700;color:var(--cyan);margin-bottom:3px">🔍 Measurement &amp; Model Bounds</div>
      <b>Totals are measured on every row:</b> client first-token / inter-token time, engine queue, and prefill duration histograms.<br/>
      <b>Splits:</b> Measured where per-rank export or graphs-on torch profile exists; modelled (†) from measured per-call costs elsewhere.<br/>
      <b>Pre-Execution Remainder (1–7%):</b> 14 ms at 8K to 1.4 s at 1M covers prompt tokenization, TCP transfer to host, scheduler bookkeeping, and initial sampling. Isolating scheduling requires per-request phase timestamps.
    </div>

    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);padding:8px;border-radius:6px;font-size:10px;line-height:1.4">
      <div style="font-weight:700;color:var(--amber);margin-bottom:3px">🌊 Technical Clarification on "Waves" (§7)</div>
      <b>1. vLLM V1 Engine Waves (DP/EP Coordination):</b> In vLLM V1, a wave coordinates data-parallel workers with expert parallelism via lockstep steps and dummy forward passes. This campaign ran <b>DP = 1, EP = 1</b> (see Evidence tab), so no dummy-step or lockstep waves existed.<br/>
      <b>2. GPU Kernel SM Wave Quantization:</b> Tail wave SM under-utilization at small batch (e.g. GEMV running at 43% memory bandwidth) lives <i>inside</i> the "kernels above memory floor" segment, not beside it (requires NCU targeted profiling).
    </div>
  </div>
</div>

<script>
function toggleBudgetView(view) {
    const firstContainer = document.getElementById('budget-first-container');
    const decodeContainer = document.getElementById('budget-decode-container');
    const btnFirst = document.getElementById('btn-budget-first');
    const btnDecode = document.getElementById('btn-budget-decode');
    if (view === 'first') {
        if (firstContainer) firstContainer.style.display = 'block';
        if (decodeContainer) decodeContainer.style.display = 'none';
        if (btnFirst) btnFirst.classList.add('active');
        if (btnDecode) btnDecode.classList.remove('active');
    } else {
        if (firstContainer) firstContainer.style.display = 'none';
        if (decodeContainer) decodeContainer.style.display = 'block';
        if (btnFirst) btnFirst.classList.remove('active');
        if (btnDecode) btnDecode.classList.add('active');
    }
}
</script>
"""

# Place the card directly under KEY EMPIRICAL PROFILER KPIS, above CHARTS ROW 1
marker = "<!-- CHARTS ROW 1: KERNEL COMPOSITION & PYTORCH OPERATOR BREAKDOWN -->"
if "profiler-wall-time-budget-card" not in content and marker in content:
    content = content.replace(marker, wall_time_panel_profiler + "\n" + marker)
    print("  ✓ Added Unified 'Where the Time Goes' Bar Chart Panel to Profiler tab")

# Write out updated file
with open(MASTER_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nSuccessfully wrote updated master dashboard to {MASTER_FILE} ({len(content)} characters, delta: {len(content) - orig_len})")

# Write out MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html
TARGET_OCT4 = "MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html"
shutil.copy2(MASTER_FILE, TARGET_OCT4)
print(f"Created/updated {TARGET_OCT4}")

# Sync to all other identical copies in workspace
SYNC_TARGETS = [
    "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_WITH_KEYFINDS.html",
    "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html",
    "v8_full_results/dashboards/v4_dashboard/index.html",
    "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html",
    "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html",
    "v8_full_results/release_specs/index.html",
    "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html",
    "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html",
]

for tgt in SYNC_TARGETS:
    if os.path.exists(tgt):
        shutil.copy2(MASTER_FILE, tgt)
        print(f"Synced to {tgt}")
