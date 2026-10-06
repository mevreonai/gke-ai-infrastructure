import sys, os, re, base64

sys.stdout.reconfigure(encoding="utf-8")

dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
index_path = r"v8_full_results\dashboards\v4_dashboard\index.html"
base_dir = r"v8_full_results\dashboards\v4_dashboard"

print("Reading MASTER_CHARACTERIZATION_DASHBOARD.html...")
with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

# -------------------------------------------------------------
# FIX B1: Software Stack Invented
# -------------------------------------------------------------
old_stack = """        <b>vLLM Version:</b> <code>0.6.2</code><br/>
        <b>PyTorch:</b> <code>2.4.0+cu124</code><br/>
        <b>CUDA Toolkit:</b> <code>12.4</code> (Driver 550.54.15)<br/>
        <b>NCCL:</b> <code>2.20.5</code> (AWS-OFI-NCCL / GCP VPC tuned)<br/>
        <b>Ray Core:</b> <code>2.37.0</code> (All 12 worker audits clean)"""

new_stack = """        <b>vLLM Version:</b> <code>0.29.0</code> (Ray Core: <code>2.58.0</code>)<br/>
        <b>PyTorch / Triton:</b> <code>2.13.0</code> &middot; Triton <code>3.7.1</code> &middot; FlashInfer <code>0.6.18</code><br/>
        <b>CUDA / Driver:</b> CUDA <code>13.0</code> (Driver <code>580.173.02</code>; CUDA Runtime 13000)<br/>
        <b>NCCL:</b> <code>nvidia-nccl-cu13 2.29.7</code> (two-node worker lib: <code>libnccl.so.2.31.2</code> / 23102)<br/>
        <b>Transport:</b> <code>NCCL_NET=Socket</code> on ens3 (MTU 1460, GCP net plugin disabled)"""

if old_stack in h:
    h = h.replace(old_stack, new_stack)
    print("Fixed B1: Software Stack Provenance.")
else:
    print("Warning: old_stack string not matched exactly.")

# -------------------------------------------------------------
# FIX B2: Validator Defect 2 Invented
# -------------------------------------------------------------
old_defect = """        <b>2. FINAL_VALIDATION Duplicate Keys:</b> Manifest validator emitted duplicate metric keys across multi-node runs; reconciled against raw JSON logs."""
new_defect = """        <b>2. FINAL_VALIDATION Off-Cluster Path Defect:</b> <code>FINAL_VALIDATION.json</code> was computed off-cluster with Windows paths (<code>result_root: C:\\Users\\...</code>); its <code>ray_nccl_scaleout_audits: 0</code> sits beside 12 passing worker audits."""

if old_defect in h:
    h = h.replace(old_defect, new_defect)
    print("Fixed B2: Validator Defect 2.")
else:
    print("Warning: old_defect string not matched exactly.")

# -------------------------------------------------------------
# FIX B3: NOT_RUN and NOT_CAPTURED Reasons Invented
# -------------------------------------------------------------
old_notrun = """        <b>E2E Ledger:</b> 7 runs marked GUARDED_NOT_RUN (safety-gated configurations not executed).<br/>
        <b>Profiler Matrix:</b> 5 distributed points NOT_CAPTURED (workload horizons where per-worker nsys daemon was skipped); 3 native incomplete; 14 captured (7 with usable rank exports, all prefill; decode deferred)."""

new_notrun = """        <b>E2E Ledger:</b> 7 runs attempted; server stopped with <code>RuntimeError('server exited rc=1')</code> after 126–134s without writing server log (cause unlogged in pilot; resolved in Stage 2 as SM100 MLA architecture requirement &amp; 8.5 GiB KV floor).<br/>
        <b>Profiler Matrix:</b> 14 captured (8 with usable rank exports, all prefill); 8 missing (3 native decode dropped during teardown, 5 capped profiles uncaptured; no reason recorded)."""

if old_notrun in h:
    h = h.replace(old_notrun, new_notrun)
    print("Fixed B3: NOT_RUN and NOT_CAPTURED reconciliation text.")
else:
    print("Warning: old_notrun string not matched exactly.")

# Also fix the global banner & other references to "safety-gated" / "guarded"
h = re.sub(r'7\s*Safety-Guarded\s*NOT_RUN', '7 Pilot Startup Rejections (rc=1; Resolved in Stage 2)', h, flags=re.IGNORECASE)
h = re.sub(r'safety-gated configurations not executed', 'server exited rc=1 at startup; resolved in Stage 2', h, flags=re.IGNORECASE)

# -------------------------------------------------------------
# FIX B4: Restore missing <div class="card mb8" id="perf-evidence-table-container">
# -------------------------------------------------------------
stray_tag = """id="perf-evidence-table-container">
<div class="header-row">"""
correct_tag = """<div class="card mb8" id="perf-evidence-table-container">
<div class="header-row">"""

if stray_tag in h:
    h = h.replace(stray_tag, correct_tag)
    print("Fixed B4: Restored <div class=\"card mb8\" id=\"perf-evidence-table-container\"> card opening tag.")
else:
    print("Notice: stray_tag already fixed or not matched.")

# -------------------------------------------------------------
# FIX B5: Time-budget charts are broken images -> embed base64
# -------------------------------------------------------------
img_names = [
    "wall_time_budget_first_token.png",
    "wall_time_budget_decode_token.png",
    "wall_time_budget_first_token_under_load.png",
    "wall_time_budget_decode_token_under_load.png"
]

for img_name in img_names:
    img_file = os.path.join(base_dir, img_name)
    if os.path.exists(img_file):
        with open(img_file, "rb") as f_img:
            b64_data = base64.b64encode(f_img.read()).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64_data}"
        # replace src="img_name"
        old_src = f'src="{img_name}"'
        new_src = f'src="{data_uri}"'
        if old_src in h:
            h = h.replace(old_src, new_src)
            print(f"Fixed B5: Embedded {img_name} as self-contained base64 data URI.")
        else:
            print(f"Notice: {old_src} not found in HTML (already embedded?).")

# -------------------------------------------------------------
# FIX B6: Key Discoveries renderer (renderFindingHtmlClient)
# -------------------------------------------------------------
# Ensure confidence_note and scope_note are rendered
old_conf_render = "'<div class=\"kd-conf-note\">' + p.confidence.notes + '</div>'"
new_conf_render = "'<div class=\"kd-conf-note\">' + (p.confidence_note || p.confidence.notes) + '</div>'"
if old_conf_render in h:
    h = h.replace(old_conf_render, new_conf_render)
    print("Fixed B6: renderFindingHtmlClient now renders confidence_note.")

old_scope_render = """'<div style="font-size:9.5px;color:#94a3b8;border-top:1px dashed #16263e;padding-top:6px;display:flex;flex-direction:column;gap:3px">' +
          '<div>Topologies: ' + topoPills + '</div>'"""
new_scope_render = """'<div style="font-size:9.5px;color:#94a3b8;border-top:1px dashed #16263e;padding-top:6px;display:flex;flex-direction:column;gap:3px">' +
          (p.scope_note ? '<div style="color:var(--amber);margin-bottom:3px"><b>Note:</b> ' + p.scope_note + '</div>' : '') +
          '<div>Topologies: ' + topoPills + '</div>'"""
if old_scope_render in h:
    h = h.replace(old_scope_render, new_scope_render)
    print("Fixed B6: renderFindingHtmlClient now renders scope_note.")

# Fix KD#6 "6 scale-out topologies at 1M" -> "4 scale-out + 2 scale-up topologies evaluated at 1M"
h = h.replace("6 scale-out topologies at 1M", "4 scale-out + 2 scale-up topologies evaluated at 1M")
# Fix KD#9 telemetry source
h = h.replace("Prometheus GPU SM utilization telemetry", "Telemetry sourced from nvidia-smi background sampler (0.5s interval)")
h = h.replace("Reported GPU SM Util (%)", "Reported GPU Util (%) [nvidia-smi]")

# -------------------------------------------------------------
# FIX P1: openEvidenceForFinding ID mapping
# -------------------------------------------------------------
old_ev_map = """window.openEvidenceForFinding = function(pageId) {
    const findingToEv = {
        1: 'EV-030', // TP16/PP1 20G TTFT 256.889s
        2: 'EV-034', // Concurrency 1M c4 TTFT 231.268s
        3: 'PR-007', // TP4/PP4 512K Nsight trace
        4: 'EV-038', // Prefix caching hit rate
        5: 'EV-040', // Max num seqs throughput knee
        6: 'EV-044', // TP16/PP1 efficiency
        7: 'PR-003', // TP8 8K Decode AllReduce overhead
        8: 'EV-048', // 16K chunk Pareto frontier
        9: 'EV-050', // SM util vs throughput decouple
        10: 'EV-054' // KV cache memory limit
    };"""

new_ev_map = """window.openEvidenceForFinding = function(pageId) {
    const findingToEv = {
        1: 'EV-111', // TP16/PP1 20G TTFT 256.889s
        2: 'EV-067', // Concurrency 1M c4 TTFT 231.268s
        3: 'PR-007', // TP4/PP4 512K Nsight trace
        4: 'EV-075', // Prefix caching hit rate
        5: 'EV-116', // Max num seqs throughput knee
        6: 'EV-081', // TP16/PP1 efficiency
        7: 'PR-003', // TP8 8K Decode AllReduce overhead
        8: 'EV-027', // 16K chunk Pareto frontier
        9: 'EV-084', // SM util vs throughput decouple
        10: 'EV-084' // KV cache memory limit
    };"""

if old_ev_map in h:
    h = h.replace(old_ev_map, new_ev_map)
    print("Fixed P1: openEvidenceForFinding ID map routed to exact evidence runs.")
else:
    print("Notice: openEvidenceForFinding map checked.")

# -------------------------------------------------------------
# FIX N5: "Stages 1-3 wait 17-22%" -> Stage 3 waits 17.2-21.9%
# -------------------------------------------------------------
h = h.replace("Stages 1-3 wait 17-22%", "Stage 3 waits 17.2–21.9% (Stages 0–2 wait 8.0–11.2%)")
h = h.replace("Stages 1-3 P2P wait 17-22%", "Stage 3 P2P wait 17.2–21.9% (Stages 0–2: 8.0–11.2%)")

# -------------------------------------------------------------
# FIX N6: KD#6 Energy Line
# -------------------------------------------------------------
old_energy = "TP4/PP4 consumes 143.1 J/1K tokens (310 W) vs TP16 134.8 J/1K tokens (150 W) and TP4/PP2 179.7 J/1K tokens (268 W)"
new_energy = "TP4/PP4 consumes 143.1 J/1K tokens (310 W) vs TP4/PP2 160.2 J/1K tokens (379 W), TP8/PP2 179.7 J/1K tokens (268 W), and TP16 247.2 J/1K tokens (225 W at 1M; 134.8 J at 128K)"
if old_energy in h:
    h = h.replace(old_energy, new_energy)
    print("Fixed N6: KD#6 energy line updated with verified 1M c1 numbers.")

# -------------------------------------------------------------
# FIX N7: KD#1 Boundary and Transport Fact
# -------------------------------------------------------------
old_kd1_bound = "PP point-to-point boundaries operate without penalty down to 20G cap; cross-node TP should not be deployed across VPC without NVLink"
new_kd1_bound = "Cross-node NCCL transport operated over plain TCP sockets (NCCL_NET=Socket on ens3, MTU 1460, provider plugin disabled); inter-node SendRecv bandwidth drops from 7.11 to 2.04 GB/s under 20G cap while small-message AllReduce latency is 227–290 µs"
if old_kd1_bound in h:
    h = h.replace(old_kd1_bound, new_kd1_bound)
    print("Fixed N7: KD#1 transport boundary text.")

# -------------------------------------------------------------
# FIX N8: PP2 Layers Distribution (3 vs 4 of 7 full-attention layers)
# -------------------------------------------------------------
h = h.replace("6 vs 8 full-attention layer distribution", "3 vs 4 full-attention layer distribution (of 7 total layers: #3, #7, #11 vs #15, #19, #23, #26)")
h = h.replace("exactly corroborating", "closely corroborating (within 3% of 0.75)")

# -------------------------------------------------------------
# FIX N11: Duplicate mode badge in drawer
# -------------------------------------------------------------
old_mode_badge = """    if (d.mode) {
        badgesHtml += '<span class="badge b-blue">' + d.mode + '</span>';
        badgesHtml += '<span class="badge b-blue">' + d.mode + '</span>';
    }"""
new_mode_badge = """    if (d.mode) {
        badgesHtml += '<span class="badge b-blue">' + d.mode + '</span>';
    }"""
if old_mode_badge in h:
    h = h.replace(old_mode_badge, new_mode_badge)
    print("Fixed N11: Removed duplicate mode badge.")

# -------------------------------------------------------------
# FIX N13: Duplicate KD#7 pointer
# -------------------------------------------------------------
pointer_str = "For cross-node and pipeline decode, inter-node barrier latency contributes 11–16 ms of 14.9–20.1 ms TPOT, plus 0.3–0.5 ms per PP hop."
if h.count(pointer_str) > 1:
    first_idx = h.find(pointer_str)
    second_idx = h.find(pointer_str, first_idx + len(pointer_str))
    if second_idx != -1:
        # remove second occurrence and surrounding li if applicable
        li_start = h.rfind('<li>', 0, second_idx)
        li_end = h.find('</li>', second_idx)
        if li_start != -1 and li_end != -1:
            h = h[:li_start] + h[li_end+5:]
            print("Fixed N13: Removed duplicate KD#7 pointer takeaway.")

# -------------------------------------------------------------
# FIX N14: Duplicate chips in profiler
# -------------------------------------------------------------
h = re.sub(r'(<button[^>]*data-prof-chip="tp4_pp2"[^>]*>.*?</button>\s*){2,}', r'\1', h)
h = re.sub(r'(<button[^>]*data-prof-chip="tp8_pp2"[^>]*>.*?</button>\s*){2,}', r'\1', h)

# -------------------------------------------------------------
# FIX N17: Pattern-filled Queue column in Scheduler scaleout ledger
# -------------------------------------------------------------
# Replace pattern 0.012 ms / 0.020 ms on specific rows
h = h.replace('<td>TP4/PP4</td><td>512K</td><td class="mono">0.020 ms</td>', '<td>TP4/PP4</td><td>512K</td><td class="mono">0.016 ms</td>')
h = h.replace('<td>TP4/PP2</td><td>512K</td><td class="mono">0.020 ms</td>', '<td>TP4/PP2</td><td>512K</td><td class="mono">0.023 ms</td>')
h = h.replace('<td>TP4/PP2</td><td>1M</td><td class="mono">0.020 ms</td>', '<td>TP4/PP2</td><td>1M</td><td class="mono">0.021 ms</td>')
h = h.replace('<td>TP8/PP2</td><td>1M</td><td class="mono">0.020 ms</td>', '<td>TP8/PP2</td><td>1M</td><td class="mono">0.038 ms</td>')
h = h.replace('<td>TP16</td><td>128K</td><td class="mono">0.012 ms</td>', '<td>TP16</td><td>128K</td><td class="mono">0.019 ms</td>')

# Save updated HTML to both MASTER_CHARACTERIZATION_DASHBOARD.html and index.html
with open(dash_path, "w", encoding="utf-8") as f:
    f.write(h)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(h)

print(f"Successfully applied all fixes to {dash_path} and {index_path} ({len(h):,} bytes).")
