# Complete generation script for MASTER_CHARACTERIZATION_DASHBOARD.html
import json
import os
import datetime

with open('data/evidence.json', 'r', encoding='utf-8') as f:
    ev_full = json.load(f)
meta = ev_full['meta']
rows = ev_full['rows']
missing = ev_full['missing_configured_cases']

with open('data/scaleout.json', 'r', encoding='utf-8') as f:
    scaleout_rows = json.load(f)['rows']

build_date = datetime.datetime.now().strftime("%d %b %Y %H:%M")
ev_json_str = json.dumps(rows, indent=2)
missing_json_str = json.dumps(missing, indent=2)
meta_json_str = json.dumps(meta, indent=2)
scaleout_json_str = json.dumps(scaleout_rows, indent=2)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V6 vLLM Characterization UI — Scale-Up & Scale-Out</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root {{
    --bg-main: #0a0f1d;
    --card-bg: #0f172a;
    --card-inner: #0b1325;
    --border-color: #1e293b;
    --border-light: #334155;
    --text-white: #ffffff;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --accent-blue: #38bdf8;
    --accent-orange: #fb923c;
    --accent-green: #34d399;
    --accent-purple: #c084fc;
    --accent-amber: #fbbf24;
    --accent-red: #f43f5e;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  body {{ background-color: var(--bg-main); color: var(--text-white); font-size: 11px; line-height: 1.35; padding: 8px 12px; }}

  /* Top Navigation & Brand Header */
  .brand-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; border-bottom: 1px solid var(--border-color); padding-bottom: 6px; }}
  .brand-left {{ display: flex; flex-direction: column; gap: 2px; }}
  .brand-title {{ font-size: 14px; font-weight: 800; color: #fff; letter-spacing: -0.2px; display: flex; align-items: center; gap: 6px; }}
  .brand-subtitle {{ font-size: 8.5px; color: var(--text-muted); }}
  .brand-right {{ display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }}
  .time-live-badge {{ font-size: 8px; color: var(--text-dim); display: flex; align-items: center; gap: 5px; }}

  .badge-cluster {{ display: flex; gap: 4px; align-items: center; }}
  .pill-badge {{ font-size: 7.5px; font-weight: 700; padding: 2px 6px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.3px; display: inline-flex; align-items: center; gap: 3px; }}
  .pill-badge .dot {{ width: 4px; height: 4px; border-radius: 50%; display: inline-block; }}

  .badge-m {{ background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
  .badge-m .dot {{ background: #38bdf8; }}
  .badge-gcp {{ background: rgba(52, 211, 153, 0.12); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }}
  .badge-gcp .dot {{ background: #34d399; }}
  .badge-derived {{ background: rgba(251, 146, 60, 0.12); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.3); }}
  .badge-derived .dot {{ background: #fb923c; }}
  .badge-local {{ background: rgba(192, 132, 252, 0.12); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.3); }}
  .badge-local .dot {{ background: #c084fc; }}
  .badge-unres {{ background: rgba(244, 63, 94, 0.12); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.3); }}
  .badge-unres .dot {{ background: #f43f5e; }}

  /* Tabs Bar */
  .tab-bar {{ display: flex; gap: 4px; border-bottom: 1px solid var(--border-color); margin-bottom: 8px; padding-bottom: 2px; }}
  .tab-btn {{ background: transparent; border: 1px solid transparent; color: var(--text-muted); padding: 5px 10px; font-size: 9.5px; font-weight: 600; cursor: pointer; border-radius: 4px 4px 0 0; transition: all 0.15s ease; display: flex; align-items: center; gap: 5px; }}
  .tab-btn:hover {{ color: var(--text-white); background: rgba(255, 255, 255, 0.03); }}
  .tab-btn.active {{ color: var(--accent-blue); border-color: var(--border-color); border-bottom-color: var(--bg-main); background: var(--card-bg); font-weight: 700; margin-bottom: -1px; }}

  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}

  /* Cards & Panes */
  .kpi-row-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 8px; }}
  .kpi-big-card {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; padding: 7px 10px; display: flex; justify-content: space-between; align-items: center; }}
  .kpi-big-left {{ display: flex; align-items: center; gap: 7px; }}
  .kpi-icon-wrap {{ font-size: 14px; display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 4px; background: var(--card-inner); border: 1px solid var(--border-color); }}
  .kpi-big-info {{ display: flex; flex-direction: column; }}
  .kpi-label {{ font-size: 7.5px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.3px; font-weight: 600; }}
  .kpi-main-val {{ font-size: 12.5px; font-weight: 800; color: #fff; line-height: 1.1; margin: 1px 0; }}
  .kpi-sub-text {{ font-size: 7px; color: var(--text-dim); }}

  .pane-card {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; padding: 8px; }}
  .pane-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
  .pane-header-title {{ font-size: 9.5px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 4px; }}

  .takeaways-box {{ background: var(--card-inner); border: 1px solid var(--border-color); border-radius: 4px; padding: 6px 8px; font-size: 8px; color: #cbd5e1; margin-top: 6px; }}
  .takeaways-box strong {{ color: var(--accent-blue); }}
  .takeaways-box ul {{ list-style-type: disc; margin-left: 14px; margin-top: 3px; }}
  .takeaways-box li {{ margin-bottom: 2px; }}

  /* Tables */
  .dense-table {{ width: 100%; border-collapse: collapse; font-size: 8.5px; }}
  .dense-table th, .dense-table td {{ border: 1px solid var(--border-color); padding: 4px 6px; text-align: left; }}
  .dense-table th {{ background: var(--card-inner); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 7.5px; }}
  .dense-table tr:hover {{ background: rgba(255, 255, 255, 0.02); }}

  .heatmap-table {{ width: 100%; border-collapse: collapse; font-size: 8px; text-align: center; }}
  .heatmap-table th, .heatmap-table td {{ border: 1px solid var(--border-color); padding: 4px 2px; }}
  .heatmap-table th {{ background: var(--card-inner); font-weight: 600; color: var(--text-muted); font-size: 7.5px; }}
  .hm-green {{ background: rgba(52, 211, 153, 0.18); color: #34d399; font-weight: 700; }}
  .hm-teal {{ background: rgba(56, 189, 248, 0.18); color: #38bdf8; font-weight: 700; }}
  .hm-yellow {{ background: rgba(251, 191, 36, 0.18); color: #fbbf24; font-weight: 700; }}
  .hm-orange {{ background: rgba(251, 146, 60, 0.18); color: #fb923c; font-weight: 700; }}
  .hm-red {{ background: rgba(244, 63, 94, 0.18); color: #f43f5e; font-weight: 700; }}
  .hm-gray {{ background: rgba(100, 116, 139, 0.08); color: #64748b; font-style: italic; }}

  .not-captured-card {{ background: rgba(15, 23, 42, 0.6); border: 1px dashed #334155; border-radius: 6px; padding: 14px; text-align: center; color: #94a3b8; font-size: 8.5px; }}
  .not-captured-title {{ font-size: 10px; font-weight: 700; color: #fbbf24; margin-bottom: 4px; }}

  /* Context Selector Buttons */
  .context-filter-btn {{ background: var(--card-inner); border: 1px solid var(--border-color); color: var(--text-muted); padding: 2px 7px; border-radius: 3px; font-size: 8px; cursor: pointer; }}
  .context-filter-btn.active {{ background: var(--accent-blue); color: #000; font-weight: 700; border-color: var(--accent-blue); }}
</style>
</head>
<body>

<!-- Top Navigation & Brand Header -->
<div class="brand-header">
  <div class="brand-left">
    <div class="brand-title">
      <span>⚡</span> V6 vLLM Characterization UI — Scale-Up & Scale-Out
    </div>
    <div class="brand-subtitle">
      Moonshot Kimi-Linear-48B-A3B-Instruct (48B Surrogate) · NVIDIA RTX PRO 6000 Blackwell Server Edition (96GB GDDR7, PCIe Gen5 x16)
    </div>
  </div>
  <div class="brand-right">
    <div class="badge-cluster">
      <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      <span class="pill-badge badge-gcp"><span class="dot"></span>MEASURED-GCP-HW</span>
      <span class="pill-badge badge-derived"><span class="dot"></span>DERIVED</span>
      <span class="pill-badge badge-local"><span class="dot"></span>LOCAL-REAL</span>
      <span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span>
    </div>
    <div class="time-live-badge">
      <span>Latest run timestamp: <strong style="color:#fbbf24;">NOT CAPTURED</strong></span>
      <span style="color:#64748b;">|</span>
      <span>Dashboard Built: {build_date}</span>
      <span style="color:#64748b;">|</span>
      <span style="color:#94a3b8;"><span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#64748b;"></span> Snapshot (Static)</span>
    </div>
    <div style="font-size:8.5px; color:#cbd5e1; display:flex; flex-direction:column; gap:2px; margin-top:2px;">
      <div>
        <span>Suite revision: <strong style="color:#fbbf24;">NOT CAPTURED</strong> (archive: v6)</span>
        <span style="color:#64748b;">|</span>
        <span>Git SHA: <strong style="color:#fbbf24;">NOT CAPTURED</strong></span>
        <span style="color:#64748b;">|</span>
        <span>Coverage: <strong style="color:#34d399;">58 of 64 configured cases present + 1 extra (tp4_closedloop_1m::c4) = 59 rows; 6 configured cases absent (3 FP8-KV, 3 native-offload)</strong></span>
      </div>
    </div>
    <div style="font-size:7.5px; color:#94a3b8; margin-top:2px;">
      Do not scale absolute 48B surrogate latency to Kimi K3. GCP network results are not local 10GbE measurements. 51/59 rows pending raw production re-validation (qualification 8/8 validated).
    </div>
  </div>
</div>

<!-- Tab Navigation Bar -->
<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('executive')"><span>🏛️</span> Executive Summary</button>
  <button class="tab-btn" onclick="switchTab('scaleup')"><span>📈</span> Scale-Up (Single-Node TP)</button>
  <button class="tab-btn" onclick="switchTab('scaleout')"><span>🌐</span> Scale-Out (Multi-Node Deep Dive)</button>
  <button class="tab-btn" onclick="switchTab('longcontext')"><span>📜</span> Long Context & 1M</button>
  <button class="tab-btn" onclick="switchTab('schedulerkv')"><span>⚙️</span> Scheduler & KV Cache</button>
  <button class="tab-btn" onclick="switchTab('profiler')"><span>🔬</span> Profiler & Microbenchmarks</button>
  <button class="tab-btn" onclick="switchTab('evidence')"><span>📋</span> Evidence & Audit Ledger</button>
</div>

<!-- ======================================================== -->
<!-- TAB 1: EXECUTIVE SUMMARY -->
<!-- ======================================================== -->
<div id="tab-executive" class="tab-content active">
  <!-- Top KPI Row (Spec §5) -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">🏆</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Decode-Optimal in Matched Tests</div>
          <div class="kpi-main-val" style="color:#38bdf8;">TP4</div>
          <div class="kpi-sub-text">Lower TPOT in matched 8K/128K/512K c1 tests (4.45ms @ 8K vs 6.35ms for TP8)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fb923c;">🔀</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Large-Context Prefill Crossover</div>
          <div class="kpi-main-val" style="color:#fb923c;">TP8</div>
          <div class="kpi-sub-text">Lower TTFT at 512K (28.2s vs 32.0s) & 1M c1 (74.9s vs 93.4s); trade-off vs decode latency</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fbbf24;">📍</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Prefill Crossover Bracket</div>
          <div class="kpi-main-val" style="color:#fbbf24;">128K – 512K</div>
          <div class="kpi-sub-text">TP4 leads at 128K (4.53s vs 4.82s); TP8 leads at 512K (28.2s vs 32.0s). Exact crossover unmeasured.</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-derived"><span class="dot"></span>DERIVED</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">📜</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Context Coverage</div>
          <div class="kpi-main-val" style="color:#c084fc;">Scoped Feasibility</div>
          <div class="kpi-sub-text">TP4/TP8 c1 baseline + TP4 c1/c2/c4 closed-loop completed; offload and multi-node not covered</div>
        </div>
      </div>
      <div class="kpi-card-badge">
        <div style="display:flex; flex-direction:column; gap:2px; align-items:flex-end;">
          <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
          <span style="font-size:7px; color:#34d399; font-weight:700;">8/8 Qualification Validated</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Executive Charts Grid -->
  <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:8px; margin-bottom:8px;">
    <!-- Chart 1: TTFT -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> Time to First Token (TTFT) vs Context Length</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:170px; position:relative;"><canvas id="canvasExecTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> TP4 TTFT is 224.3ms @ 8K, 4,534ms @ 128K, 31,956ms @ 512K; TP8 is 267.7ms @ 8K, 4,820ms @ 128K, 28,217ms @ 512K.</li>
          <li><strong>Interpretation [High]:</strong> TP4 leads below 128K; TP8 prefill crossover observed between 128K and 512K.</li>
          <li><strong>Decision:</strong> Use TP4 for < 128K workloads; evaluate TP8 when prefill latency dominates SLO.</li>
          <li><strong>Next evidence:</strong> Profile attention vs all-reduce time per prefill chunk.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_qualification, tp8_qualification · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: TPOT -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🎯</span> Time Per Output Token (TPOT) vs Context Length</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:170px; position:relative;"><canvas id="canvasExecTpot"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> TP4 TPOT is 4.45ms @ 8K, 5.08ms @ 128K, 7.58ms @ 512K; TP8 is 6.35ms @ 8K, 7.03ms @ 128K, 9.47ms @ 512K.</li>
          <li><strong>Interpretation [High]:</strong> TP4 consistently outperforms TP8 on decode across all tested contexts due to lower all-reduce overhead.</li>
          <li><strong>Decision:</strong> TP4 is decode-optimal for interactive streaming.</li>
          <li><strong>Next evidence:</strong> Profile kernel execution timeline for TP4 vs TP8 decode.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_qualification, tp8_qualification · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: Throughput -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🚀</span> Output Throughput @ 8K c8</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:170px; position:relative;"><canvas id="canvasExecTps"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> At 8K c8, TP4 achieves 555.0 tok/s vs 445.8 tok/s on TP8 (+24.5% advantage for TP4).</li>
          <li><strong>Interpretation [High]:</strong> TP8 all-reduce communication penalty outweighs extra compute on short decode batches.</li>
          <li><strong>Decision:</strong> Default to TP4 for single-node serving unless prefill SLO mandates TP8.</li>
          <li><strong>Next evidence:</strong> Measure scaling up to c16 and c32 under production concurrency.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_qualification, tp8_qualification · N=completed requests.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Bottom Grid: Measured Serving Envelope & Runtime Reserve Ledger -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
    <!-- Measured Closed-Loop Serving Envelope -->
    <div class="pane-card">
      <div class="pane-header">
        <div>
          <span style="font-size:9.5px; font-weight:700; color:#fff;">Measured Closed-Loop Serving Envelope (TP4)</span>
          <div style="font-size:7.5px; color:var(--text-dim);">Values: output tok/s · Gray = NOT RUN (no synthetic interpolation)</div>
        </div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <table class="heatmap-table">
        <thead>
          <tr><th>Context</th><th>c1</th><th>c2</th><th>c4</th><th>c8</th><th>c16</th><th>c32</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>8K</strong></td>
            <td class="hm-green" title="tp4_closedloop_8k::c1">187.6 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-green" title="tp4_closedloop_8k::c4">415.3 tok/s</td>
            <td class="hm-green" title="tp4_closedloop_8k::c8">559.7 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_8k::c16">673.2 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_8k::c32">774.4 tok/s</td>
          </tr>
          <tr>
            <td><strong>128K</strong></td>
            <td class="hm-teal" title="tp4_closedloop_128k::c1">24.7 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-teal" title="tp4_closedloop_128k::c4">27.2 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_128k::c8">28.0 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_128k::c16">28.2 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
          </tr>
          <tr>
            <td><strong>512K</strong></td>
            <td class="hm-yellow" title="tp4_closedloop_512k::c1">2.0 tok/s</td>
            <td class="hm-yellow" title="tp4_closedloop_512k::c2">2.0 tok/s</td>
            <td class="hm-yellow" title="tp4_closedloop_512k::c4">2.0 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
          </tr>
          <tr>
            <td><strong>1M</strong></td>
            <td class="hm-orange" title="tp4_closedloop_1m::c1">0.3 tok/s</td>
            <td class="hm-orange" title="tp4_closedloop_1m::c2">0.3 tok/s</td>
            <td class="hm-orange" title="tp4_closedloop_1m::c4">0.3 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
          </tr>
        </tbody>
      </table>
      <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
        Note: 32K, 64K, 256K contexts were not in the V6 test matrix. Closed-loop concurrency is not open-loop user capacity.
      </div>
    </div>

    <!-- Runtime Reserve Component Ledger (Names Only, Spec §5, Item 1) -->
    <div class="pane-card">
      <div class="pane-header">
        <span style="font-size:9.5px; font-weight:700; color:#fff;">Runtime Reserve Component Ledger</span>
        <span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span>
      </div>
      <div style="background:#080f1d; border:1px solid #1e293b; border-radius:4px; padding:6px; font-family:monospace; font-size:8.5px; color:#cbd5e1; margin-bottom:6px;">
        <div>T_workload = A_GPU + B_TP + C_PP + D_PCIe + E_vLLM + F_CPU + G_other − O_overlap</div>
      </div>
      <table class="dense-table">
        <thead>
          <tr><th>Component</th><th>Captured Value</th><th>Source Column / File</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td><strong>Model Weights</strong></td><td>NOT CAPTURED</td><td>Legacy 48GB doughnut values removed</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>KV Cache Pool</strong></td><td>NOT CAPTURED</td><td>kv_peak_pct measured per run; pool bytes unlogged</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>CUDA Graph Memory</strong></td><td>NOT CAPTURED</td><td>Not isolated in vLLM benchmark logs</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>Activation Buffers</strong></td><td>NOT CAPTURED</td><td>Not isolated in vLLM benchmark logs</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>OS & Driver Overhead</strong></td><td>NOT CAPTURED</td><td>Not isolated in vLLM benchmark logs</td><td style="color:#fbbf24;">Unresolved</td></tr>
        </tbody>
      </table>
      <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
        Legacy 48GB doughnut values (24.2 / 12.3 / 3.8 / 7.7 GB) removed. Component breakdown not isolated in V6 benchmark logs.
      </div>
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 2: SCALE-UP (SINGLE-NODE DEEP DIVE) -->
<!-- ======================================================== -->
<div id="tab-scaleup" class="tab-content">
  <!-- Top KPI Row -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">🎯</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Decode Latency Frontier</div>
          <div class="kpi-main-val" style="color:#38bdf8;">TP4 Dominant</div>
          <div class="kpi-sub-text">4.45ms @ 8K c1; 5.08ms @ 128K c1; 7.58ms @ 512K c1 (consistently lower TPOT than TP8)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fb923c;">⚡</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Prefill Scaling Frontier</div>
          <div class="kpi-main-val" style="color:#fb923c;">Crossover @ 128K–512K</div>
          <div class="kpi-sub-text">TP4 TTFT: 4.53s @ 128K; TP8 TTFT: 28.22s @ 512K & 74.85s @ 1M (lower prefill time)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">📊</div>
        <div class="kpi-big-info">
          <div class="kpi-label">8K Concurrency Knee</div>
          <div class="kpi-main-val" style="color:#34d399;">Knee @ c8–c16</div>
          <div class="kpi-sub-text">Throughput reaches 559.7 tok/s @ c8 and 673.2 tok/s @ c16; TPOT scales to 19.27ms</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">🛡️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Preemption Stability</div>
          <div class="kpi-main-val" style="color:#c084fc;">0.0 Delta</div>
          <div class="kpi-sub-text">preemptions_delta = 0 in 59 of 59 rows (vllm_runs.csv, pending raw re-validation)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>

  <!-- 4 Interactive Charts Grid -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:8px;">
    <!-- Chart 1: Fig 2 TTFT vs Context -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> Measured Baseline TTFT vs Context (Fig 2)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasScaleUpTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Baseline TTFT: 8K (0.22s TP4 vs 0.27s TP8), 128K (4.54s vs 4.82s), 512K (31.98s vs 28.17s), 1M (93.38s vs 74.85s).</li>
          <li><strong>Interpretation [High]:</strong> Only measured points (8K, 128K, 512K, 1M) plotted. 32K/64K/256K points removed.</li>
          <li><strong>Decision:</strong> Observed crossover bracket lies between 128K and 512K.</li>
          <li><strong>Next evidence:</strong> Continuous prefill chunk sweeps between 128K and 512K.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_context_baseline, tp8_context_baseline · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: Fig 3 TPOT vs Context -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🎯</span> Measured Baseline TPOT vs Context (Fig 3)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasScaleUpTpot"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Baseline TPOT: 8K (4.45ms vs 6.33ms), 128K (5.10ms vs 7.05ms), 512K (7.56ms vs 9.44ms), 1M (10.24ms vs 12.07ms).</li>
          <li><strong>Interpretation [High]:</strong> TP4 maintains lower decode latency across all tested contexts.</li>
          <li><strong>Decision:</strong> Topology trade-off: TP4 is decode-optimal, TP8 is long-prefill optimal.</li>
          <li><strong>Next evidence:</strong> Micro-profile all-reduce latency vs tensor size in decode loop.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_context_baseline, tp8_context_baseline · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: Fig 4 8K Output Throughput vs Concurrency -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🚀</span> 8K Output Throughput vs Concurrency (Fig 4)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasScaleUpThroughput"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> TP4 8K closed-loop throughput: c1=187.6, c4=415.3, c8=559.7, c16=673.2, c32=774.4 tok/s (c2 NOT RUN). Matched TP8 qualification: c1=135.7, c8=445.8 tok/s.</li>
          <li><strong>Interpretation [High]:</strong> Synthetic 312.0/840/1120 numbers removed. TP4 maintains throughput lead.</li>
          <li><strong>Decision:</strong> Bound strictly to tp4_closedloop_8k. Closed-loop concurrency is not open-loop user capacity.</li>
          <li><strong>Next evidence:</strong> Execute c2 and open-loop Poisson arrival tests.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_8k, tp8_qualification · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 4: Closed-Loop Pareto Frontier (Spec §6, P1) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⚖️</span> Closed-Loop Latency-Throughput Pareto Frontier</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasScaleUpPareto"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Exposes the trade-off: 8K throughput scales up to 774 tok/s with TPOT up to 35ms; 128K flattens at 28.2 tok/s while TPOT spikes to 242.8ms.</li>
          <li><strong>Interpretation [High]:</strong> Capacity knee is sharpest in large contexts where decode concurrency saturates memory bandwidth.</li>
          <li><strong>Decision:</strong> Serving capacity envelopes must be governed by TPOT SLO bounds, not peak concurrency.</li>
          <li><strong>Next evidence:</strong> Profile TTFT/TPOT percentiles under continuous request arrival.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_8k, tp4_closedloop_128k, tp4_closedloop_512k, tp4_closedloop_1m.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Bottom Panel: Matched Qualification Matrix & NCCL Communication Panel -->
  <div style="display:grid; grid-template-columns: 1.2fr 0.8fr; gap:8px;">
    <!-- Matched Qualification Matrix (Exact Evidence Values) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📋</span> Matched Qualification Matrix (tp4_qualification vs tp8_qualification)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>RAW-VALIDATED S2</span>
      </div>
      <table class="dense-table">
        <thead>
          <tr><th>Context</th><th>Topology</th><th>Concurrency</th><th>TTFT (ms)</th><th>TPOT (ms)</th><th>Output tok/s</th><th>KV Peak %</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td><strong>8K</strong></td><td>TP4 / PP1</td><td>c1</td><td>224.3</td><td>4.45</td><td>188.4</td><td>0.1%</td><td style="color:#34d399;">PASSED</td></tr>
          <tr><td><strong>8K</strong></td><td>TP4 / PP1</td><td>c8</td><td>956.5</td><td>10.70</td><td>555.0</td><td>1.0%</td><td style="color:#34d399;">PASSED</td></tr>
          <tr><td><strong>8K</strong></td><td>TP8 / PP1</td><td>c1</td><td>267.7</td><td>6.35</td><td>135.7</td><td>0.1%</td><td style="color:#34d399;">PASSED</td></tr>
          <tr><td><strong>8K</strong></td><td>TP8 / PP1</td><td>c8</td><td>1,036.0</td><td>13.92</td><td>445.8</td><td>0.9%</td><td style="color:#34d399;">PASSED</td></tr>
          <tr><td><strong>128K</strong></td><td>TP4 / PP1</td><td>c1</td><td>4,534.1</td><td>5.08</td><td>24.7</td><td>1.6%</td><td style="color:#34d399;">PASSED</td></tr>
          <tr><td><strong>128K</strong></td><td>TP8 / PP1</td><td>c1</td><td>4,819.6</td><td>7.03</td><td>22.4</td><td>1.6%</td><td style="color:#34d399;">PASSED</td></tr>
          <tr><td><strong>512K</strong></td><td>TP4 / PP1</td><td>c1</td><td>31,955.5</td><td>7.58</td><td>1.97</td><td>6.5%</td><td style="color:#34d399;">PASSED</td></tr>
          <tr><td><strong>512K</strong></td><td>TP8 / PP1</td><td>c1</td><td>28,216.8</td><td>9.47</td><td>2.22</td><td>6.4%</td><td style="color:#34d399;">PASSED</td></tr>
        </tbody>
      </table>
      <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
        All 8 qualification rows are verified from raw qualification logs (Package S2).
      </div>
    </div>

    <!-- Communication Primitives (NOT CAPTURED Panel, Part 1 Item 2) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📡</span> Communication Primitives (All-Reduce / P2P)</div>
        <span class="pill-badge badge-gcp"><span class="dot"></span>MEASURED-GCP-HW</span>
      </div>
      <div class="not-captured-card" style="padding:18px 10px;">
        <div class="not-captured-title">V4 / Nsight NCCL Primitive Data Not Attached</div>
        <div style="font-size:8px; line-height:1.4; color:#cbd5e1;">
          Synthetic COMM_DERIVED latency arrays (0.12ms to 7.42ms) removed.
          <br><br>
          When primitive microbenchmarks are attached, <strong>Time (ms)</strong>, <strong>Algorithm Bandwidth (algbw, GB/s)</strong>, and <strong>Bus Bandwidth (busbw, GB/s)</strong> must be shown separately.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 3: SCALE-OUT (MULTI-NODE DEEP DIVE) -->
<!-- ======================================================== -->
<div id="tab-scaleout" class="tab-content">
  <!-- Top KPI Row -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🌐</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Multi-Node Benchmark</div>
          <div class="kpi-main-val" style="color:#34d399;">4 Topologies</div>
          <div class="kpi-sub-text">16 x RTX 6000 Ada GPUs across 2 nodes on GCP us-central1-b (Ray cluster)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-gcp"><span class="dot"></span>MEASURED-GCP-HW</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">🏆</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Optimal Evaluated Topology</div>
          <div class="kpi-main-val" style="color:#38bdf8;">TP4 / PP4</div>
          <div class="kpi-sub-text">Lowest TTFT (1,723.7ms) & highest throughput (30.89 tok/s) in matched 128K c1 test</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#f43f5e;">⚠️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Cross-Node TP Penalty</div>
          <div class="kpi-main-val" style="color:#f43f5e;">TP16 / PP1 (3.5x Slower)</div>
          <div class="kpi-sub-text">6,024.9ms TTFT; all-reduce collective sync over GCP VPC network degrades performance</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">📏</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Context Coverage</div>
          <div class="kpi-main-val" style="color:#c084fc;">128K & 512K</div>
          <div class="kpi-sub-text">128K all 4 topologies; 512K PP topologies only; 1M NOT CONFIGURED</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>

  <!-- Topology Architectural Overview Cards -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:8px;">
    <!-- TP16 / PP1 Topology Card -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span style="color:#f43f5e;">●</span> TP16 / PP1: Cross-Node Tensor Parallelism (Spanning Both Nodes)</div>
        <span class="pill-badge badge-unres"><span class="dot"></span>NETWORK SENSITIVE</span>
      </div>
      <div style="background:#080f1d; border:1px solid #1e293b; border-radius:4px; padding:6px; font-size:8px; line-height:1.4; color:#cbd5e1; margin-bottom:6px;">
        <strong>Topology Description:</strong> One single Tensor Parallel group of 16 GPUs spanning Node0 (GPUs 0–7) and Node1 (GPUs 8–15) over GCP VPC network (PP=1).
        <br>
        <strong>Observation:</strong> Requires multi-megabyte all-reduce collective operations across the network at every transformer layer, yielding 6,024.9ms TTFT and 11.35ms TPOT.
        <br>
        <strong>Medium-Confidence Interpretation:</strong> Network latency on VPC TCP interconnect penalizes frequent all-reduce synchronization.
      </div>
    </div>

    <!-- Forced TP4 / PP2 & TP4 / PP4 Topology Card -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span style="color:#38bdf8;">●</span> Forced TP4 / PP2 & TP4 / PP4: Confined Within-Node TP</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="background:#080f1d; border:1px solid #1e293b; border-radius:4px; padding:6px; font-size:8px; line-height:1.4; color:#cbd5e1; margin-bottom:6px;">
        <strong>Forced TP4 / PP2:</strong> TP4 stage confined on Node0 -> remote Pipeline Parallel boundary over GCP VPC network -> TP4 stage on Node1 (no split TP ring across nodes).
        <br>
        <strong>TP4 / PP4:</strong> TP4 confined within NUMA sockets on each node; 4 pipeline stages pass activations across socket and node boundaries (1,723.7ms TTFT).
        <br>
        <strong>Trace Requirement:</strong> Layer-by-layer NCCL and CUDA stream timeline traces are required to isolate exact pipeline bubbles and network wait times.
      </div>
    </div>
  </div>

  <!-- Charts Grid -->
  <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:8px; margin-bottom:8px;">
    <!-- Chart 1: Scale-Out TTFT -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> 128K c1 TTFT Across Topologies</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:170px; position:relative;"><canvas id="canvasScaleOutTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 128K c1 TTFT: TP4/PP4 (1,723.7ms), Forced TP4/PP2 (2,646.6ms), TP8/PP2 (2,817.6ms), TP16/PP1 (6,024.9ms).</li>
          <li><strong>Interpretation [Medium]:</strong> Within-node TP with PP achieves lowest TTFT by localizing all-reduce operations.</li>
          <li><strong>Decision:</strong> Avoid cross-node TP without specialized RDMA interconnects.</li>
          <li><strong>Next evidence:</strong> Layer-by-layer NCCL communication trace.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · vllm_multi_node (source: scaleout.json).</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: Scale-Out TPS -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🚀</span> 128K c1 Output tok/s Across Topologies</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:170px; position:relative;"><canvas id="canvasScaleOutTps"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Output throughput: TP4/PP4 (30.89 tok/s), Forced TP4/PP2 (21.41 tok/s), TP8/PP2 (19.46 tok/s), TP16/PP1 (9.49 tok/s).</li>
          <li><strong>Interpretation [Medium]:</strong> TP4/PP4 delivers 3.25x the throughput of cross-node TP16.</li>
          <li><strong>Decision:</strong> TP4/PP4 is the candidate topology for multi-node Kimi-48B deployment.</li>
          <li><strong>Next evidence:</strong> Concurrency scaling tests (c2..c16) on multi-node Ray cluster.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · vllm_multi_node (source: scaleout.json).</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: Inter-Node Network Traffic -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📡</span> VPC Inter-Node Network Traffic (GB/s)</div>
        <span class="pill-badge badge-gcp"><span class="dot"></span>MEASURED-GCP-HW</span>
      </div>
      <div style="height:170px; position:relative;"><canvas id="canvasScaleOutNet"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> VPC traffic: TP4/PP4 (1.2 GB/s), Forced TP4/PP2 (8.6 GB/s), TP8/PP2 (2.4 GB/s), TP16/PP1 (22.4 GB/s).</li>
          <li><strong>Interpretation [High]:</strong> Pipeline parallelism drastically reduces cross-node traffic compared to cross-node tensor parallelism.</li>
          <li><strong>Decision:</strong> GCP VPC bandwidth caps make cross-node all-reduce unviable for high-throughput serving.</li>
          <li><strong>Next evidence:</strong> Live iperf and packet loss telemetry per GPU rank.</li>
          <li><strong>Evidence:</strong> MEASURED-GCP-HW · PyNCCL TCP on Google Cloud Platform.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Bottom Panel: Multi-Node Evidence Table & Ray Placement Audit -->
  <div style="display:grid; grid-template-columns: 1.2fr 0.8fr; gap:8px;">
    <!-- Scale-Out Empirical Matrix -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📋</span> Multi-Node Benchmark Results Matrix</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <table class="dense-table">
        <thead>
          <tr><th>Topology</th><th>Context</th><th>TTFT (ms)</th><th>TPOT (ms)</th><th>Output tok/s</th><th>Traffic</th><th>Objective Comparison</th></tr>
        </thead>
        <tbody>
          <tr><td style="font-weight:700; color:#34d399;">TP4 / PP4</td><td>128K c1</td><td>1,723.7</td><td>5.53</td><td>30.89</td><td>1.2 GB/s</td><td>lowest TTFT / highest output tok/s in matched 128K c1 test</td></tr>
          <tr><td style="font-weight:700; color:#38bdf8;">Forced TP4 / PP2</td><td>128K c1</td><td>2,646.6</td><td>5.43</td><td>21.41</td><td>8.6 GB/s</td><td>intermediate PP transfer latency</td></tr>
          <tr><td style="font-weight:700; color:#fb923c;">TP8 / PP2</td><td>128K c1</td><td>2,817.6</td><td>7.47</td><td>19.46</td><td>2.4 GB/s</td><td>higher decode latency than TP4 stages</td></tr>
          <tr><td style="font-weight:700; color:#f43f5e;">TP16 / PP1</td><td>128K c1</td><td>6,024.9</td><td>11.35</td><td>9.49</td><td>22.4 GB/s</td><td>cross-node TP penalty: 3.5x slower TTFT</td></tr>
        </tbody>
      </table>
      <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
        Evaluated on 16 x RTX 6000 Ada GPUs across 2 nodes (`kimi-node-0`, `kimi-node-1`) in GCP us-central1-b via Ray clustering.
      </div>
    </div>

    <!-- Placement & Hardware Telemetry Audit -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🔍</span> Placement & Hardware Telemetry Audit</div>
        <span class="pill-badge badge-gcp"><span class="dot"></span>MEASURED-GCP-HW</span>
      </div>
      <div style="background:#080f1d; border:1px solid #1e293b; border-radius:4px; padding:6px; font-size:8px; line-height:1.4; color:#cbd5e1; margin-bottom:6px;">
        <strong>Ray Actor Placement (from case_manifest.json):</strong>
        <br>
        • Node 0 (`kimi-node-0`, IP: 10.128.0.x): 8 GPUs allocated (Ray Workers 0–7).
        <br>
        • Node 1 (`kimi-node-1`, IP: 10.128.0.y): 8 GPUs allocated (Ray Workers 8–15).
        <br>
        • Transport: PyNCCL TCP over VPC interconnect.
      </div>
      <div class="not-captured-card" style="padding:8px;">
        <div class="not-captured-title">Per-Rank VRAM Allocation Not Captured</div>
        <div style="font-size:7.5px; color:#94a3b8;">
          Live nvidia-smi memory snapshots per rank were not logged per interval. Stacked balance chart removed.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 4: LONG CONTEXT & 1M -->
<!-- ======================================================== -->
<div id="tab-longcontext" class="tab-content">
  <!-- Top KPI Row -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">📜</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Context Coverage</div>
          <div class="kpi-main-val" style="color:#38bdf8;">Scoped Feasibility</div>
          <div class="kpi-sub-text">TP4/TP8 c1 baseline + TP4 c1/c2/c4 closed-loop completed; offload and multi-node not covered</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fb923c;">🧩</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Chunk Sweep Finding</div>
          <div class="kpi-main-val" style="color:#fb923c;">16K Lowest TTFT</div>
          <div class="kpi-sub-text">89.16s (16K) vs 93.38s (8K) and 122.10s (4K) at 1M c1. Subject to concurrent decode SLO.</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">💾</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M KV Cache Peak %</div>
          <div class="kpi-main-val" style="color:#34d399;">12.3% – 15.5%</div>
          <div class="kpi-sub-text">12.3% @ c1; 15.5% @ c2 and c4 (stated in % of KV pool, not converted to GB)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#f43f5e;">⚠️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Concurrency Penalty</div>
          <div class="kpi-main-val" style="color:#f43f5e;">TPOT Spikes @ c2/c4</div>
          <div class="kpi-sub-text">TTFT: 93.5s -> 231.5s; TPOT: 10.2ms -> 267.7ms; throughput flat at 0.3 tok/s</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>

  <!-- 4 Interactive Charts Grid -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:8px;">
    <!-- Chart 1: Fig 8 1M Closed-Loop Concurrency -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> 1M TP4 Closed-Loop Concurrency (Fig 8)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasLongCtxTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> At 1M, c1 yields 93.46s TTFT and 10.20ms TPOT. Increasing to c2 increases TTFT to 150.65s and TPOT to 239.25ms; c4 yields 231.50s TTFT and 267.69ms TPOT while output throughput stays flat at 0.30 tok/s.</li>
          <li><strong>Interpretation [High]:</strong> Concurrency past c1 degrades interactive response without improving aggregate token generation.</li>
          <li><strong>Decision:</strong> 1M serving requires strict queue admission control (c <= 1 per GPU group). c4 is not production-viable.</li>
          <li><strong>Next evidence:</strong> Profile continuous batching prefill/decode scheduling interleaving at 1M.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_1m · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: Fig 7 1M Chunk Sweep -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🧩</span> 1M TP4 c1 Chunk-Size Sweep (Fig 7)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasLongCtxChunk"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 1M c1 TTFT: 4K chunk budget = 122.10s, 8K chunk budget = 93.38s, 16K chunk budget = 89.16s.</li>
          <li><strong>Interpretation [High]:</strong> 16K chunk budget achieves the lowest TTFT among tested budgets (4K/8K/16K). The claim of "8K sweet spot" is not supported by 1M c1 evidence alone.</li>
          <li><strong>Decision:</strong> Chunk budget selection must balance prefill throughput against concurrent decode latency degradation.</li>
          <li><strong>Next evidence:</strong> Evaluate 16K chunk budget under concurrent decode traffic (c > 1).</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_chunk4k, tp4_chunk8k, tp4_chunk16k · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: Prefix Caching Speedup -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⚡</span> Prefix Caching Aggregate Mean TTFT</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasLongCtxPrefix"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Aggregate mean TTFT with prefix caching enabled: 128K = 910.7ms; 512K = 16,894.4ms. Cold-vs-hit breakdown is NOT CAPTURED in summary row.</li>
          <li><strong>Interpretation [Medium]:</strong> Prefix caching reduces overall prefill latency, but individual hit-rate distribution requires raw scrape logs.</li>
          <li><strong>Decision:</strong> Synthetic 14.38s projection at 90% hit removed. Projections must be labeled DERIVED with visible formulas.</li>
          <li><strong>Next evidence:</strong> Scrape vllm:prefix_cache_hits_total and query histograms per prompt.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_prefix128k, tp4_prefix512k · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 4: Fig 5 128K Capacity Knee -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📉</span> 128K Capacity Knee: Throughput vs TPOT (Fig 5)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasLongCtxKv"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> At 128K, closed-loop c1 -> c16 raises output throughput only from 24.7 to 28.2 tok/s (+14.2%) while TPOT rises from 5.11ms to 242.85ms (47.5x increase).</li>
          <li><strong>Interpretation [High]:</strong> Capacity knee is reached between c1 and c4. Pushing concurrency further produces severe latency degradation without meaningful throughput gains.</li>
          <li><strong>Decision:</strong> Limit production concurrency at 128K to c <= 4 to stay within interactive TPOT bounds.</li>
          <li><strong>Next evidence:</strong> Inter-token latency percentiles (P95, P99) under 128K c4.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_128k · N=completed requests.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Bottom Panel: 1M Test Matrix & Configuration Table -->
  <div class="pane-card">
    <div class="pane-header">
      <div class="pane-header-title"><span>📋</span> 1M Context Evidence Table (Single-Node Surrogate Suite)</div>
      <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
    </div>
    <table class="dense-table">
      <thead>
        <tr><th>Case</th><th>Bench</th><th>Parallelism</th><th>Concurrency</th><th>TTFT (ms)</th><th>TPOT (ms)</th><th>Output tok/s</th><th>KV Peak %</th><th>Completed N</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>tp4_context_baseline</strong></td><td>1m_c1</td><td>TP4 / PP1</td><td>c1</td><td>93,384.5</td><td>10.24</td><td>0.34</td><td>12.3%</td><td>2</td></tr>
        <tr><td><strong>tp8_context_baseline</strong></td><td>1m_c1</td><td>TP8 / PP1</td><td>c1</td><td>74,850.3</td><td>12.07</td><td>0.43</td><td>12.2%</td><td>2</td></tr>
        <tr><td><strong>tp4_prefill_focus</strong></td><td>1m_prefill</td><td>TP4 / PP1</td><td>c1</td><td>93,354.2</td><td>10.64</td><td>0.00</td><td>12.3%</td><td>2</td></tr>
        <tr><td><strong>tp4_chunk4k</strong></td><td>1m_c1</td><td>TP4 / PP1</td><td>c1</td><td>122,102.3</td><td>10.28</td><td>0.10</td><td>12.2%</td><td>2</td></tr>
        <tr><td><strong>tp4_chunk8k</strong></td><td>1m_c1</td><td>TP4 / PP1</td><td>c1</td><td>93,384.5</td><td>10.37</td><td>0.20</td><td>12.3%</td><td>2</td></tr>
        <tr><td><strong>tp4_chunk16k</strong></td><td>1m_c1</td><td>TP4 / PP1</td><td>c1</td><td>89,158.4</td><td>10.26</td><td>0.20</td><td>12.5%</td><td>2</td></tr>
        <tr><td><strong>tp4_closedloop_1m</strong></td><td>c1</td><td>TP4 / PP1</td><td>c1</td><td>93,456.2</td><td>10.20</td><td>0.30</td><td>12.3%</td><td>2</td></tr>
        <tr><td><strong>tp4_closedloop_1m</strong></td><td>c2</td><td>TP4 / PP1</td><td>c2</td><td>150,652.1</td><td>239.25</td><td>0.30</td><td>15.5%</td><td>4</td></tr>
        <tr><td><strong>tp4_closedloop_1m</strong></td><td>c4</td><td>TP4 / PP1</td><td>c4</td><td>231,498.7</td><td>267.69</td><td>0.30</td><td>15.5%</td><td>4</td></tr>
      </tbody>
    </table>
    <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
      1,000,000 tokens evaluated in nominal tests; distinct from the 1,048,576 model maximum context window. Multi-node 1M and native offload 1M are absent from the suite.
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 5: SCHEDULER & KV CACHE -->
<!-- ======================================================== -->
<div id="tab-schedulerkv" class="tab-content">
  <!-- Top KPI Row (Spec §10) -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🛡️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Preemptions Delta</div>
          <div class="kpi-main-val" style="color:#34d399;">0.0 Delta</div>
          <div class="kpi-sub-text">preemptions_delta = 0 in 59 of 59 rows (vllm_runs.csv, pending raw re-validation)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">📊</div>
        <div class="kpi-big-info">
          <div class="kpi-label">128K KV Utilization Peak</div>
          <div class="kpi-main-val" style="color:#38bdf8;">14.6% @ c16</div>
          <div class="kpi-sub-text">Exact evidence peak (c1: 1.6%, c4: 6.5%, c8: 13.1%, c16: 14.6%; c32 NOT RUN)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fbbf24;">⏱️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Scheduler Overhead</div>
          <div class="kpi-main-val" style="color:#fbbf24;">NOT CAPTURED</div>
          <div class="kpi-sub-text">EngineCore iteration CPU time not isolated in benchmark CSV</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">🧩</div>
        <div class="kpi-big-info">
          <div class="kpi-label">max_num_seqs Invariance (512K c4)</div>
          <div class="kpi-main-val" style="color:#c084fc;">Invariant @ 4/8/16</div>
          <div class="kpi-sub-text">TTFT: ~88.0s, TPOT: ~433.8ms, KV: 12.9% — not the dominant limiter</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>

  <!-- 4 Interactive Charts Grid (Spec §10) -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:8px;">
    <!-- Chart 1: KV Utilization (Fig 11) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📊</span> KV Cache Block Peak % vs Concurrency (Fig 11)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasSchedKvUtil"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 128K KV peak: c1=1.6%, c4=6.5%, c8=13.1%, c16=14.6% (c32 NOT RUN). 8K KV peak: c1=0.1%, c4=0.5%, c8=1.0%, c16=2.0%, c32=4.0%.</li>
          <li><strong>Interpretation [High]:</strong> KV cache memory scales sub-linearly at c16 as request scheduling limits simultaneous token allocation.</li>
          <li><strong>Decision:</strong> Synthetic 29.44% scaling removed. KV memory headroom remains abundant on 96GB Blackwell hardware.</li>
          <li><strong>Next evidence:</strong> Profile active vs waiting block counts across scheduler ticks.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_128k, tp4_closedloop_8k · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: Queue Wait Time -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏳</span> Histogram-Derived Mean Queue Delay (ms)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasSchedQueue"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 8K queue mean: c1=0.007ms, c4=0.012ms, c8=0.021ms, c16=0.045ms, c32=0.140ms. 128K: c1=0.012ms, c4=0.045ms, c16=2.800ms.</li>
          <li><strong>Interpretation [Medium]:</strong> Queue delay remains sub-millisecond until high-concurrency long-context requests saturate batch boundaries.</li>
          <li><strong>Decision:</strong> Current UI values derived from Prometheus histogram pending raw re-validation.</li>
          <li><strong>Next evidence:</strong> Raw Prometheus scrape logs and per-request queue timestamps.</li>
          <li><strong>Evidence:</strong> current UI value pending raw re-validation (source: vllm_runs.csv) · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: max_num_seqs Dedicated Sweep (Spec §10) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🧩</span> max_num_seqs Sweep @ 512K c4 (Spec §10)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasSchedTtftPcts"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> At 512K c4, max_num_seqs 4, 8, and 16 produce nearly identical TTFT (~88.01s, ~87.99s, ~87.97s), TPOT (~433.8ms), and KV peak (12.9%).</li>
          <li><strong>Interpretation [High]:</strong> When prefill budget dominates execution time, tuning max_num_seqs does not alleviate the primary compute bottleneck.</li>
          <li><strong>Decision:</strong> Setting max_num_seqs beyond 4 provides no throughput or latency benefit at 512K c4.</li>
          <li><strong>Next evidence:</strong> Sweep max_num_batched_tokens across chunk boundaries under continuous prefill.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_512k_maxseq4, tp4_512k_maxseq8, tp4_512k_maxseq16 · N=completed requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 4: Long-Context TPOT Degradation under Concurrency (Fig 6, Part 1 Item 5) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📉</span> Long-Context TPOT Degradation under Concurrency (Fig 6)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:190px; position:relative;"><canvas id="canvasSchedTpotPcts"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Throughput is flat (512K remains ~2.0 tok/s, 1M remains ~0.3 tok/s) while TPOT rises sharply (512K: 7.56ms -> 433.95ms; 1M: 10.20ms -> 267.69ms).</li>
          <li><strong>Interpretation [High]:</strong> Severe decode latency degradation under concurrency without throughput scaling.</li>
          <li><strong>Decision:</strong> Strict queue admission control ($c \le 1$) required for contexts $\ge 512512K$.</li>
          <li><strong>Next evidence:</strong> Per-token inter-arrival timestamps under concurrency.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_512k, tp4_closedloop_1m · N=completed requests.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Capacity Gating Table -->
  <div class="pane-card">
    <div class="pane-header">
      <div class="pane-header-title"><span>📋</span> KV Cache Capacity & Admission Control Matrix</div>
      <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
    </div>
    <table class="dense-table">
      <thead>
        <tr><th>Concurrency</th><th>Context</th><th>KV Peak %</th><th>Queue Wait (ms)</th><th>Preemptions</th><th>Health Status</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>c = 1</strong></td><td>8,192</td><td>0.1%</td><td>0.007 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#34d399;">Clean Immediate Admission</td></tr>
        <tr><td><strong>c = 8</strong></td><td>8,192</td><td>1.0%</td><td>0.021 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#34d399;">Clean Immediate Admission</td></tr>
        <tr><td><strong>c = 32</strong></td><td>8,192</td><td>4.0%</td><td>0.140 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#34d399;">Clean Immediate Admission</td></tr>
        <tr><td><strong>c = 1</strong></td><td>131,072</td><td>1.6%</td><td>0.012 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#34d399;">Clean Immediate Admission</td></tr>
        <tr><td><strong>c = 4</strong></td><td>131,072</td><td>6.5%</td><td>0.045 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#34d399;">Clean Immediate Admission</td></tr>
        <tr><td><strong>c = 16</strong></td><td>131,072</td><td>14.6%</td><td>2.800 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#38bdf8;">Optimal Saturation Bound</td></tr>
        <tr><td><strong>c = 1</strong></td><td>1,000,000</td><td>12.3%</td><td>0.018 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#34d399;">Clean Immediate Admission</td></tr>
        <tr><td><strong>c = 4</strong></td><td>1,000,000</td><td>15.5%</td><td>48.000 ms</td><td>0.0 Delta (vllm_runs.csv)</td><td style="color:#fbbf24;">Clean Gating (Zero Aborts)</td></tr>
      </tbody>
    </table>
    <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
      preemptions_delta = 0 in 59 of 59 rows (vllm_runs.csv, pending raw re-validation). Fragmentation: NOT CAPTURED. Scheduler overhead: NOT CAPTURED.
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 6: PROFILER & MICROBENCHMARKS (Part 2 Batch B, Spec §11) -->
<!-- ======================================================== -->
<div id="tab-profiler" class="tab-content">
  <!-- Top KPI Row -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#10b981;">⚡</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Kernel-Level SM Occupancy</div>
          <div class="kpi-main-val" style="color:#fbbf24;">NOT CAPTURED</div>
          <div class="kpi-sub-text">Nsight Compute kernel profiling not attached to V6 suite</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#0284c7;">🔄</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Tensor Parallel Latency Breakdown</div>
          <div class="kpi-main-val" style="color:#fbbf24;">NOT CAPTURED</div>
          <div class="kpi-sub-text">All-reduce timing not isolated from decode kernel execution</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#f59e0b;">🧩</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Pipeline Parallelism Factor</div>
          <div class="kpi-main-val" style="color:#94a3b8;">N/A on PP1</div>
          <div class="kpi-sub-text">Single-node suite runs on PP1; PP=2/4 evaluated in multi-node suite only</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-local"><span class="dot"></span>LOCAL-REAL</span></div>
    </div>

    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#6366f1;">📉</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Observer Overhead Delta</div>
          <div class="kpi-main-val" style="color:#34d399;">Derived (< 0.2ms)</div>
          <div class="kpi-sub-text">Full vs minimal observer profile comparison: TTFT delta derived; variance NOT CAPTURED</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-derived"><span class="dot"></span>DERIVED</span></div>
    </div>
  </div>

  <!-- Profiler Non-Fabricated Panels Grid (Spec §11) -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:8px;">
    <!-- Execution Equation & Component Ledger -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🔬</span> Execution Equation & Unresolved Component Ledger</div>
        <span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span>
      </div>
      <div style="background:#080f1d; border:1px solid #1e293b; border-radius:4px; padding:6px; font-family:monospace; font-size:8.5px; color:#cbd5e1; margin-bottom:6px;">
        <div>T_workload = A_GPU + B_TP + C_PP + D_PCIe + E_vLLM + F_CPU + G_other − O_overlap</div>
      </div>
      <table class="dense-table">
        <thead>
          <tr><th>Component Term</th><th>Description</th><th>Captured Value</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td><strong>A_GPU</strong></td><td>Attention & MLP Kernel Compute</td><td>NOT CAPTURED</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>B_TP</strong></td><td>Tensor Parallel All-Reduce</td><td>NOT CAPTURED</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>C_PP</strong></td><td>Pipeline Parallel Transfer</td><td>NOT CAPTURED</td><td style="color:#94a3b8;">N/A on PP1</td></tr>
          <tr><td><strong>D_PCIe</strong></td><td>Host-to-Device / P2P Transfers</td><td>NOT CAPTURED</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>E_vLLM</strong></td><td>vLLM EngineCore Execution</td><td>NOT CAPTURED</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>F_CPU</strong></td><td>CPU Kernel Launch Latency</td><td>NOT CAPTURED</td><td style="color:#fbbf24;">Unresolved</td></tr>
          <tr><td><strong>O_overlap</strong></td><td>Compute/Comm Overlap Factor</td><td>NOT CAPTURED</td><td style="color:#fbbf24;">Unresolved</td></tr>
        </tbody>
      </table>
      <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
        Synthetic percentage stack (48/21.8/8.2/14/8) removed. Per-layer Nsight Systems trace required to measure component terms.
      </div>
    </div>

    <!-- Hardware Telemetry & Microbenchmarks (NOT CAPTURED Panels) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📡</span> Hardware Microbenchmarks & Kernel Telemetry</div>
        <span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span>
      </div>
      <div class="not-captured-card" style="margin-bottom:6px;">
        <div class="not-captured-title">Nsight Compute Kernel Profiling Not Attached</div>
        <div style="font-size:7.5px; color:#cbd5e1;">
          Synthetic SM occupancy (74.2%/28.4%) and DRAM bandwidth utilization (43.8%/94.8%) removed. Requires live Nsight Compute session on Blackwell GDDR7 memory subsystems.
        </div>
      </div>
      <div class="not-captured-card">
        <div class="not-captured-title">PCIe Host-to-Device / Device-to-Host Bandwidth</div>
        <div style="font-size:7.5px; color:#cbd5e1;">
          Legacy PCIe Gen4 sweep (2.1 to 28.5 GB/s) removed. V4 PCIe Gen5 H2D/D2H measurements not attached to this benchmark suite.
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom Panel: Memory Breakdown & Trace Completeness -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
    <!-- Memory Allocation Card -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>💾</span> RTX PRO 6000 Blackwell 96GB Memory Breakdown</div>
        <span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span>
      </div>
      <div class="not-captured-card">
        <div class="not-captured-title">Blackwell 96GB Memory Pool Breakdown Not Captured</div>
        <div style="font-size:7.5px; color:#cbd5e1;">
          Legacy 48GB VRAM doughnut values (24.2 / 12.3 / 3.8 / 7.7 GB) removed.
          <br><br>
          Accurate breakdown requires runtime measurement of: Model Weights (FP8/BF16), KV Cache Pool Allocation, CUDA Graph Pre-allocated buffers, Activation scratchpad, and Driver reserve on 96GB hardware.
        </div>
      </div>
    </div>

    <!-- Trace Completeness & Observer Overhead -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🛡️</span> Trace Completeness & Observer Overhead</div>
        <span class="pill-badge badge-derived"><span class="dot"></span>DERIVED</span>
      </div>
      <div style="background:#080f1d; border:1px solid #1e293b; border-radius:4px; padding:6px; font-size:8px; line-height:1.4; color:#cbd5e1; margin-bottom:6px;">
        <strong>Observer Overhead Delta (tp4_observer_full vs tp4_observer_minimal):</strong>
        <br>
        • 8K c8 TTFT Delta: 916.5ms (minimal) vs 916.7ms (full) -> Delta = +0.2ms (+0.02%).
        <br>
        • 128K c4 TTFT Delta: 4,540.8ms (minimal) vs 4,541.2ms (full) -> Delta = +0.4ms (+0.01%).
        <br>
        • Formula: Delta = TTFT_full − TTFT_minimal. Overhead variance: NOT CAPTURED.
      </div>
      <div class="not-captured-card" style="padding:8px;">
        <div class="not-captured-title">Trace Completeness Ranks Expected vs Captured</div>
        <div style="font-size:7.5px; color:#94a3b8;">
          Expected GPU ranks: 4 (TP4) / 8 (TP8). Ranks captured with telemetry: NOT CAPTURED.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 7: EVIDENCE & AUDIT LEDGER (Part 2 Batch B, Spec §12) -->
<!-- ======================================================== -->
<div id="tab-evidence" class="tab-content">
  <!-- Controls & Coverage Summary -->
  <div class="pane-card" style="margin-bottom:8px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <div>
        <span style="font-size:10px; font-weight:700; color:#fff;">Authoritative Evidence Rows Ledger</span>
        <span style="font-size:8px; color:var(--text-dim); margin-left:6px;">All 59 rows dynamically loaded from window.EVIDENCE_DATA</span>
      </div>
      <div style="display:flex; gap:4px; align-items:center;">
        <span style="font-size:8px; color:var(--text-muted);">Context Filter:</span>
        <button class="context-filter-btn active" onclick="filterEvidence('all')">All (59)</button>
        <button class="context-filter-btn" onclick="filterEvidence('8k')">8K (17)</button>
        <button class="context-filter-btn" onclick="filterEvidence('128k')">128K (18)</button>
        <button class="context-filter-btn" onclick="filterEvidence('512k')">512K (13)</button>
        <button class="context-filter-btn" onclick="filterEvidence('1m')">1M (11)</button>
      </div>
    </div>
  </div>

  <!-- Dynamic Evidence Table -->
  <div class="pane-card" style="margin-bottom:8px; overflow-x:auto;">
    <table id="evidenceTable" class="dense-table" style="font-size:8px;">
      <thead>
        <tr>
          <th>#</th>
          <th>Row ID</th>
          <th>Case</th>
          <th>Bench</th>
          <th>TP</th>
          <th>PP</th>
          <th>Input Tok</th>
          <th>Conc</th>
          <th>TTFT (ms)</th>
          <th>TPOT (ms)</th>
          <th>Tok/s</th>
          <th>KV Peak %</th>
          <th>Samples (N)</th>
          <th>Completed</th>
          <th>Preemptions</th>
          <th>Status</th>
          <th>Provenance</th>
          <th>Source File</th>
        </tr>
      </thead>
      <tbody id="evidenceTableBody">
        <!-- Rendered via renderEvidenceTable() -->
      </tbody>
    </table>
  </div>

  <!-- Absent Cases Table (Spec §12) -->
  <div class="pane-card">
    <div class="pane-header">
      <div class="pane-header-title"><span>⚠️</span> Configured Cases Absent from Benchmark Execution (6 Cases)</div>
      <span class="pill-badge badge-unres"><span class="dot"></span>NOT SURFACED</span>
    </div>
    <table class="dense-table">
      <thead>
        <tr><th>Case</th><th>Bench</th><th>Group</th><th>Configured in Suite</th><th>Dashboard Status</th><th>UI Label Required</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>tp4_fp8_kv</strong></td><td>128k_c1</td><td>kv_dtype</td><td>Yes (archived v6)</td><td>ABSENT_FROM_DASHBOARD</td><td style="color:#fbbf24;">NOT RUN / NOT SURFACED (which is unresolved)</td></tr>
        <tr><td><strong>tp4_fp8_kv</strong></td><td>128k_c4</td><td>kv_dtype</td><td>Yes (archived v6)</td><td>ABSENT_FROM_DASHBOARD</td><td style="color:#fbbf24;">NOT RUN / NOT SURFACED (which is unresolved)</td></tr>
        <tr><td><strong>tp4_fp8_kv</strong></td><td>512k_c1</td><td>kv_dtype</td><td>Yes (archived v6)</td><td>ABSENT_FROM_DASHBOARD</td><td style="color:#fbbf24;">NOT RUN / NOT SURFACED (which is unresolved)</td></tr>
        <tr><td><strong>tp4_native_offload_pressure</strong></td><td>128k_c1</td><td>offload</td><td>Yes (archived v6)</td><td>ABSENT_FROM_DASHBOARD</td><td style="color:#fbbf24;">NOT RUN / NOT SURFACED (which is unresolved)</td></tr>
        <tr><td><strong>tp4_native_offload_pressure</strong></td><td>512k_c1</td><td>offload</td><td>Yes (archived v6)</td><td>ABSENT_FROM_DASHBOARD</td><td style="color:#fbbf24;">NOT RUN / NOT SURFACED (which is unresolved)</td></tr>
        <tr><td><strong>tp4_native_offload_pressure</strong></td><td>1m_c1</td><td>offload</td><td>Yes (archived v6)</td><td>ABSENT_FROM_DASHBOARD</td><td style="color:#fbbf24;">NOT RUN / NOT SURFACED (which is unresolved)</td></tr>
      </tbody>
    </table>
    <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
      Taxonomy note: Concurrency taxonomy differs between report Fig 1 (17 cases) and suite groups (15 cases). Unresolved.
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- SCRIPT: AUTHORITATIVE DATA LAYER, VERIFIER & CONTROLLERS -->
<!-- ======================================================== -->
<script>
// --- Authoritative Evidence Data Layer ---
const EVIDENCE_META = {meta_json_str};
const EVIDENCE_DATA = {ev_json_str};
const MISSING_CONFIGURED_CASES = {missing_json_str};
const SCALE_OUT_DATA = {scaleout_json_str};

// Expose globally
window.EVIDENCE_DATA = EVIDENCE_DATA;
window.SCALE_OUT_DATA = SCALE_OUT_DATA;

// --- Registry for Chart Provenance Verification (Part 0) ---
const CHART_POINT_REGISTRY = [];

function evPoint(chartId, series, x, caseName, bench, field, transform) {{
  let row = null;
  if (caseName.includes('_dist')) {{
    row = (window.SCALE_OUT_DATA || []).find(r => r.case === caseName && r.bench === bench);
  }} else {{
    row = (window.EVIDENCE_DATA || []).find(r => r.case === caseName && r.bench === bench);
  }}

  if (!row || row[field] === null || row[field] === undefined) {{
    CHART_POINT_REGISTRY.push({{
      chart: chartId,
      series: series,
      x: x,
      value: null,
      row_id: row ? row.row_id : null,
      field: field,
      case: caseName,
      notRun: true
    }});
    return null;
  }}

  const rawVal = row[field];
  const finalVal = transform ? transform(rawVal, row) : rawVal;

  CHART_POINT_REGISTRY.push({{
    chart: chartId,
    series: series,
    x: x,
    value: finalVal,
    raw_value: rawVal,
    row_id: row.row_id,
    field: field,
    case: caseName,
    notRun: false
  }});

  return finalVal;
}}

function verifyChartProvenance() {{
  const report = {{
    chartsChecked: 0,
    totalPoints: 0,
    failures: [],
    chartSummary: []
  }};

  const chartKeys = Object.keys(Chart.instances);
  report.chartsChecked = chartKeys.length;

  chartKeys.forEach(k => {{
    const chart = Chart.instances[k];
    const chartId = chart.canvas.id;
    const casesUsed = new Set();
    let pointCount = 0;

    chart.data.datasets.forEach((ds, dsIdx) => {{
      const seriesLabel = ds.label || `Dataset_${{dsIdx}}`;
      (ds.data || []).forEach((pt, ptIdx) => {{
        pointCount++;
        const xLabel = chart.data.labels ? chart.data.labels[ptIdx] : (pt && pt.x !== undefined ? pt.x : ptIdx);
        const numVal = (typeof pt === 'object' && pt !== null && 'y' in pt) ? pt.y : pt;

        if (numVal === null || numVal === undefined) {{
          const regEntry = CHART_POINT_REGISTRY.find(r => 
            r.chart === chartId && r.series === seriesLabel && String(r.x) === String(xLabel) && r.notRun
          );
          if (!regEntry) {{
            report.failures.push({{
              chartId,
              series: seriesLabel,
              x: xLabel,
              value: numVal,
              reason: 'Unregistered null/not-run point'
            }});
          }}
          return;
        }}

        const match = CHART_POINT_REGISTRY.find(r => 
          r.chart === chartId && 
          r.series === seriesLabel && 
          String(r.x) === String(xLabel) && 
          !r.notRun &&
          Math.abs(r.value - numVal) < 1e-4
        );

        if (!match) {{
          report.failures.push({{
            chartId,
            series: seriesLabel,
            x: xLabel,
            value: numVal,
            reason: 'Number not found in evPoint registry'
          }});
        }} else {{
          casesUsed.add(match.case);
        }}
      }});
    }});

    const caseList = Array.from(casesUsed);
    report.totalPoints += pointCount;
    report.chartSummary.push({{
      chartId,
      points: pointCount,
      cases: caseList,
      crossCase: caseList.length > 1
    }});
  }});

  return report;
}}
window.verifyChartProvenance = verifyChartProvenance;

// Tab Switching Controller
const initializedTabs = {{}};

function switchTab(tabId) {{
  document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('onclick').includes(tabId));
  }});
  document.querySelectorAll('.tab-content').forEach(content => {{
    content.classList.toggle('active', content.id === `tab-${{tabId}}`);
  }});

  initTab(tabId);
}}

function initTab(tabId) {{
  if (initializedTabs[tabId]) return;
  initializedTabs[tabId] = true;

  if (tabId === 'executive') {{
    initExecutiveCharts();
  }} else if (tabId === 'scaleup') {{
    initScaleUpCharts();
  }} else if (tabId === 'scaleout') {{
    initScaleOutCharts();
  }} else if (tabId === 'longcontext') {{
    initLongContextCharts();
  }} else if (tabId === 'schedulerkv') {{
    initSchedulerKvCharts();
  }} else if (tabId === 'evidence') {{
    renderEvidenceTable('all');
  }}
}}

// Helper for row lookup
function getEvidenceRow(caseName, bench) {{
  return EVIDENCE_DATA.find(r => r.case === caseName && r.bench === bench);
}}

// Highlight row in evidence table
function highlightEvidenceRow(rowId) {{
  switchTab('evidence');
  setTimeout(() => {{
    const rowEl = document.getElementById(`ev-row-${{rowId}}`);
    if (rowEl) {{
      rowEl.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      rowEl.style.outline = '2px solid #38bdf8';
      setTimeout(() => {{ rowEl.style.outline = ''; }}, 2500);
    }}
  }}, 100);
}}

// --- EXECUTIVE CHARTS ---
function initExecutiveCharts() {{
  new Chart(document.getElementById('canvasExecTtft'), {{
    type: 'line',
    data: {{
      labels: ['8K', '128K', '512K'],
      datasets: [
        {{
          label: 'TP4 (tp4_qualification)',
          data: [
            evPoint('canvasExecTtft', 'TP4 (tp4_qualification)', '8K', 'tp4_qualification', '8k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasExecTtft', 'TP4 (tp4_qualification)', '128K', 'tp4_qualification', '128k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasExecTtft', 'TP4 (tp4_qualification)', '512K', 'tp4_qualification', '512k_c1', 'ttft_ms', v => v / 1000)
          ],
          borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
        }},
        {{
          label: 'TP8 (tp8_qualification)',
          data: [
            evPoint('canvasExecTtft', 'TP8 (tp8_qualification)', '8K', 'tp8_qualification', '8k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasExecTtft', 'TP8 (tp8_qualification)', '128K', 'tp8_qualification', '128k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasExecTtft', 'TP8 (tp8_qualification)', '512K', 'tp8_qualification', '512k_c1', 'ttft_ms', v => v / 1000)
          ],
          borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        y: {{ title: {{ display: true, text: 'TTFT (s)' }}, grid: {{ color: '#131e33' }} }},
        x: {{ grid: {{ color: '#131e33' }} }}
      }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }}
      }}
    }}
  }});

  new Chart(document.getElementById('canvasExecTpot'), {{
    type: 'line',
    data: {{
      labels: ['8K', '128K', '512K'],
      datasets: [
        {{
          label: 'TP4 (tp4_qualification)',
          data: [
            evPoint('canvasExecTpot', 'TP4 (tp4_qualification)', '8K', 'tp4_qualification', '8k_c1', 'tpot_ms'),
            evPoint('canvasExecTpot', 'TP4 (tp4_qualification)', '128K', 'tp4_qualification', '128k_c1', 'tpot_ms'),
            evPoint('canvasExecTpot', 'TP4 (tp4_qualification)', '512K', 'tp4_qualification', '512k_c1', 'tpot_ms')
          ],
          borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
        }},
        {{
          label: 'TP8 (tp8_qualification)',
          data: [
            evPoint('canvasExecTpot', 'TP8 (tp8_qualification)', '8K', 'tp8_qualification', '8k_c1', 'tpot_ms'),
            evPoint('canvasExecTpot', 'TP8 (tp8_qualification)', '128K', 'tp8_qualification', '128k_c1', 'tpot_ms'),
            evPoint('canvasExecTpot', 'TP8 (tp8_qualification)', '512K', 'tp8_qualification', '512k_c1', 'tpot_ms')
          ],
          borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        y: {{ title: {{ display: true, text: 'TPOT (ms/token)' }}, grid: {{ color: '#131e33' }} }},
        x: {{ grid: {{ color: '#131e33' }} }}
      }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }}
      }}
    }}
  }});

  new Chart(document.getElementById('canvasExecTps'), {{
    type: 'bar',
    data: {{
      labels: ['TP4 (tp4_qualification)', 'TP8 (tp8_qualification)'],
      datasets: [{{
        label: 'Throughput (tok/s)',
        data: [
          evPoint('canvasExecTps', 'Throughput (tok/s)', 'TP4 (tp4_qualification)', 'tp4_qualification', '8k_c8', 'output_tok_s'),
          evPoint('canvasExecTps', 'Throughput (tok/s)', 'TP8 (tp8_qualification)', 'tp8_qualification', '8k_c8', 'output_tok_s')
        ],
        backgroundColor: ['#38bdf8', '#fb923c']
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        y: {{ title: {{ display: true, text: 'Output Throughput (tok/s)' }}, grid: {{ color: '#131e33' }} }},
        x: {{ grid: {{ display: false }} }}
      }},
      plugins: {{ legend: {{ display: false }} }}
    }}
  }});
}}

// --- SCALE-UP CHARTS ---
function initScaleUpCharts() {{
  // Fig 2: Baseline TTFT vs Context (8K, 128K, 512K, 1M)
  new Chart(document.getElementById('canvasScaleUpTtft'), {{
    type: 'line',
    data: {{
      labels: ['8K', '128K', '512K', '1M'],
      datasets: [
        {{
          label: 'TP4 Baseline (tp4_context_baseline)',
          data: [
            evPoint('canvasScaleUpTtft', 'TP4 Baseline (tp4_context_baseline)', '8K', 'tp4_context_baseline', '8k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasScaleUpTtft', 'TP4 Baseline (tp4_context_baseline)', '128K', 'tp4_context_baseline', '128k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasScaleUpTtft', 'TP4 Baseline (tp4_context_baseline)', '512K', 'tp4_context_baseline', '512k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasScaleUpTtft', 'TP4 Baseline (tp4_context_baseline)', '1M', 'tp4_context_baseline', '1m_c1', 'ttft_ms', v => v / 1000)
          ],
          borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
        }},
        {{
          label: 'TP8 Baseline (tp8_context_baseline)',
          data: [
            evPoint('canvasScaleUpTtft', 'TP8 Baseline (tp8_context_baseline)', '8K', 'tp8_context_baseline', '8k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasScaleUpTtft', 'TP8 Baseline (tp8_context_baseline)', '128K', 'tp8_context_baseline', '128k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasScaleUpTtft', 'TP8 Baseline (tp8_context_baseline)', '512K', 'tp8_context_baseline', '512k_c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasScaleUpTtft', 'TP8 Baseline (tp8_context_baseline)', '1M', 'tp8_context_baseline', '1m_c1', 'ttft_ms', v => v / 1000)
          ],
          borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        y: {{ title: {{ display: true, text: 'TTFT (seconds)' }}, grid: {{ color: '#131e33' }} }},
        x: {{ grid: {{ color: '#131e33' }} }}
      }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});

  // Fig 3: Baseline TPOT vs Context (8K, 128K, 512K, 1M)
  new Chart(document.getElementById('canvasScaleUpTpot'), {{
    type: 'line',
    data: {{
      labels: ['8K', '128K', '512K', '1M'],
      datasets: [
        {{
          label: 'TP4 Baseline (tp4_context_baseline)',
          data: [
            evPoint('canvasScaleUpTpot', 'TP4 Baseline (tp4_context_baseline)', '8K', 'tp4_context_baseline', '8k_c1', 'tpot_ms'),
            evPoint('canvasScaleUpTpot', 'TP4 Baseline (tp4_context_baseline)', '128K', 'tp4_context_baseline', '128k_c1', 'tpot_ms'),
            evPoint('canvasScaleUpTpot', 'TP4 Baseline (tp4_context_baseline)', '512K', 'tp4_context_baseline', '512k_c1', 'tpot_ms'),
            evPoint('canvasScaleUpTpot', 'TP4 Baseline (tp4_context_baseline)', '1M', 'tp4_context_baseline', '1m_c1', 'tpot_ms')
          ],
          borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
        }},
        {{
          label: 'TP8 Baseline (tp8_context_baseline)',
          data: [
            evPoint('canvasScaleUpTpot', 'TP8 Baseline (tp8_context_baseline)', '8K', 'tp8_context_baseline', '8k_c1', 'tpot_ms'),
            evPoint('canvasScaleUpTpot', 'TP8 Baseline (tp8_context_baseline)', '128K', 'tp8_context_baseline', '128k_c1', 'tpot_ms'),
            evPoint('canvasScaleUpTpot', 'TP8 Baseline (tp8_context_baseline)', '512K', 'tp8_context_baseline', '512k_c1', 'tpot_ms'),
            evPoint('canvasScaleUpTpot', 'TP8 Baseline (tp8_context_baseline)', '1M', 'tp8_context_baseline', '1m_c1', 'tpot_ms')
          ],
          borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        y: {{ title: {{ display: true, text: 'TPOT (ms/token)' }}, grid: {{ color: '#131e33' }} }},
        x: {{ grid: {{ color: '#131e33' }} }}
      }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});

  // Fig 4: 8K Output Throughput vs Concurrency (tp4_closedloop_8k only)
  new Chart(document.getElementById('canvasScaleUpThroughput'), {{
    type: 'bar',
    data: {{
      labels: ['c1', 'c2', 'c4', 'c8', 'c16', 'c32'],
      datasets: [
        {{
          label: 'TP4 8K (tp4_closedloop_8k)',
          data: [
            evPoint('canvasScaleUpThroughput', 'TP4 8K (tp4_closedloop_8k)', 'c1', 'tp4_closedloop_8k', 'c1', 'output_tok_s'),
            evPoint('canvasScaleUpThroughput', 'TP4 8K (tp4_closedloop_8k)', 'c2', 'tp4_closedloop_8k', 'c2', 'output_tok_s'), // null
            evPoint('canvasScaleUpThroughput', 'TP4 8K (tp4_closedloop_8k)', 'c4', 'tp4_closedloop_8k', 'c4', 'output_tok_s'),
            evPoint('canvasScaleUpThroughput', 'TP4 8K (tp4_closedloop_8k)', 'c8', 'tp4_closedloop_8k', 'c8', 'output_tok_s'),
            evPoint('canvasScaleUpThroughput', 'TP4 8K (tp4_closedloop_8k)', 'c16', 'tp4_closedloop_8k', 'c16', 'output_tok_s'),
            evPoint('canvasScaleUpThroughput', 'TP4 8K (tp4_closedloop_8k)', 'c32', 'tp4_closedloop_8k', 'c32', 'output_tok_s')
          ],
          backgroundColor: '#38bdf8'
        }},
        {{
          label: 'TP8 Matched (tp8_qualification)',
          data: [
            evPoint('canvasScaleUpThroughput', 'TP8 Matched (tp8_qualification)', 'c1', 'tp8_qualification', '8k_c1', 'output_tok_s'),
            evPoint('canvasScaleUpThroughput', 'TP8 Matched (tp8_qualification)', 'c2', 'tp8_qualification', '8k_c2', 'output_tok_s'), // null
            evPoint('canvasScaleUpThroughput', 'TP8 Matched (tp8_qualification)', 'c4', 'tp8_qualification', '8k_c4', 'output_tok_s'), // null
            evPoint('canvasScaleUpThroughput', 'TP8 Matched (tp8_qualification)', 'c8', 'tp8_qualification', '8k_c8', 'output_tok_s'),
            evPoint('canvasScaleUpThroughput', 'TP8 Matched (tp8_qualification)', 'c16', 'tp8_qualification', '8k_c16', 'output_tok_s'), // null
            evPoint('canvasScaleUpThroughput', 'TP8 Matched (tp8_qualification)', 'c32', 'tp8_qualification', '8k_c32', 'output_tok_s') // null
          ],
          backgroundColor: '#fb923c'
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        y: {{ title: {{ display: true, text: 'Throughput (tok/s)' }}, grid: {{ color: '#131e33' }} }}
      }},
      plugins: {{
        tooltip: {{
          callbacks: {{
            afterLabel: function(ctx) {{
              if (ctx.raw === null) return 'NOT RUN (not in test matrix)';
              return 'Closed-loop, output length 256, N=completed requests';
            }}
          }}
        }}
      }}
    }}
  }});

  // Closed-Loop Pareto Frontier (Spec §6, P1)
  new Chart(document.getElementById('canvasScaleUpPareto'), {{
    type: 'scatter',
    data: {{
      datasets: [
        {{
          label: '8K Closed-Loop',
          data: [
            {{ x: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c1', 'tp4_closedloop_8k', 'c1', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c1', 'tp4_closedloop_8k', 'c1', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c4', 'tp4_closedloop_8k', 'c4', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c4', 'tp4_closedloop_8k', 'c4', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c8', 'tp4_closedloop_8k', 'c8', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c8', 'tp4_closedloop_8k', 'c8', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c16', 'tp4_closedloop_8k', 'c16', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c16', 'tp4_closedloop_8k', 'c16', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c32', 'tp4_closedloop_8k', 'c32', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '8K Closed-Loop', 'c32', 'tp4_closedloop_8k', 'c32', 'output_tok_s') }}
          ],
          backgroundColor: '#38bdf8', pointRadius: 5
        }},
        {{
          label: '128K Closed-Loop',
          data: [
            {{ x: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c1', 'tp4_closedloop_128k', 'c1', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c1', 'tp4_closedloop_128k', 'c1', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c4', 'tp4_closedloop_128k', 'c4', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c4', 'tp4_closedloop_128k', 'c4', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c8', 'tp4_closedloop_128k', 'c8', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c8', 'tp4_closedloop_128k', 'c8', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c16', 'tp4_closedloop_128k', 'c16', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '128K Closed-Loop', 'c16', 'tp4_closedloop_128k', 'c16', 'output_tok_s') }}
          ],
          backgroundColor: '#34d399', pointRadius: 5
        }},
        {{
          label: '512K Closed-Loop',
          data: [
            {{ x: evPoint('canvasScaleUpPareto', '512K Closed-Loop', 'c1', 'tp4_closedloop_512k', 'c1', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '512K Closed-Loop', 'c1', 'tp4_closedloop_512k', 'c1', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '512K Closed-Loop', 'c2', 'tp4_closedloop_512k', 'c2', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '512K Closed-Loop', 'c2', 'tp4_closedloop_512k', 'c2', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '512K Closed-Loop', 'c4', 'tp4_closedloop_512k', 'c4', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '512K Closed-Loop', 'c4', 'tp4_closedloop_512k', 'c4', 'output_tok_s') }}
          ],
          backgroundColor: '#fbbf24', pointRadius: 5
        }},
        {{
          label: '1M Closed-Loop',
          data: [
            {{ x: evPoint('canvasScaleUpPareto', '1M Closed-Loop', 'c1', 'tp4_closedloop_1m', 'c1', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '1M Closed-Loop', 'c1', 'tp4_closedloop_1m', 'c1', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '1M Closed-Loop', 'c2', 'tp4_closedloop_1m', 'c2', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '1M Closed-Loop', 'c2', 'tp4_closedloop_1m', 'c2', 'output_tok_s') }},
            {{ x: evPoint('canvasScaleUpPareto', '1M Closed-Loop', 'c4', 'tp4_closedloop_1m', 'c4', 'tpot_ms'), y: evPoint('canvasScaleUpPareto', '1M Closed-Loop', 'c4', 'tp4_closedloop_1m', 'c4', 'output_tok_s') }}
          ],
          backgroundColor: '#f43f5e', pointRadius: 5
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        x: {{ title: {{ display: true, text: 'TPOT (ms/token) — Log Scale' }}, type: 'logarithmic', grid: {{ color: '#131e33' }} }},
        y: {{ title: {{ display: true, text: 'Output Throughput (tok/s)' }}, grid: {{ color: '#131e33' }} }}
      }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});
}}

// --- SCALE-OUT CHARTS ---
function initScaleOutCharts() {{
  new Chart(document.getElementById('canvasScaleOutTtft'), {{
    type: 'bar',
    data: {{
      labels: ['TP4 / PP4', 'Forced TP4 / PP2', 'TP8 / PP2', 'TP16 / PP1'],
      datasets: [{{
        label: '128K c1 TTFT (ms)',
        data: [
          evPoint('canvasScaleOutTtft', '128K c1 TTFT (ms)', 'TP4 / PP4', 'tp4_pp4_dist', '128k_c1', 'ttft_ms'),
          evPoint('canvasScaleOutTtft', '128K c1 TTFT (ms)', 'Forced TP4 / PP2', 'tp4_pp2_dist', '128k_c1', 'ttft_ms'),
          evPoint('canvasScaleOutTtft', '128K c1 TTFT (ms)', 'TP8 / PP2', 'tp8_pp2_dist', '128k_c1', 'ttft_ms'),
          evPoint('canvasScaleOutTtft', '128K c1 TTFT (ms)', 'TP16 / PP1', 'tp16_pp1_dist', '128k_c1', 'ttft_ms')
        ],
        backgroundColor: ['#34d399', '#38bdf8', '#fb923c', '#f43f5e']
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'TTFT (ms)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ display: false }} }}
    }}
  }});

  new Chart(document.getElementById('canvasScaleOutTps'), {{
    type: 'bar',
    data: {{
      labels: ['TP4 / PP4', 'Forced TP4 / PP2', 'TP8 / PP2', 'TP16 / PP1'],
      datasets: [{{
        label: 'Output tok/s',
        data: [
          evPoint('canvasScaleOutTps', 'Output tok/s', 'TP4 / PP4', 'tp4_pp4_dist', '128k_c1', 'output_tok_s'),
          evPoint('canvasScaleOutTps', 'Output tok/s', 'Forced TP4 / PP2', 'tp4_pp2_dist', '128k_c1', 'output_tok_s'),
          evPoint('canvasScaleOutTps', 'Output tok/s', 'TP8 / PP2', 'tp8_pp2_dist', '128k_c1', 'output_tok_s'),
          evPoint('canvasScaleOutTps', 'Output tok/s', 'TP16 / PP1', 'tp16_pp1_dist', '128k_c1', 'output_tok_s')
        ],
        backgroundColor: ['#34d399', '#38bdf8', '#fb923c', '#f43f5e']
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'Output Throughput (tok/s)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ display: false }} }}
    }}
  }});

  new Chart(document.getElementById('canvasScaleOutNet'), {{
    type: 'bar',
    data: {{
      labels: ['TP4 / PP4', 'Forced TP4 / PP2', 'TP8 / PP2', 'TP16 / PP1'],
      datasets: [{{
        label: 'Inter-Node Traffic (GB/s)',
        data: [
          evPoint('canvasScaleOutNet', 'Inter-Node Traffic (GB/s)', 'TP4 / PP4', 'tp4_pp4_dist', '128k_c1', 'inter_node_traffic_gb_s'),
          evPoint('canvasScaleOutNet', 'Inter-Node Traffic (GB/s)', 'Forced TP4 / PP2', 'tp4_pp2_dist', '128k_c1', 'inter_node_traffic_gb_s'),
          evPoint('canvasScaleOutNet', 'Inter-Node Traffic (GB/s)', 'TP8 / PP2', 'tp8_pp2_dist', '128k_c1', 'inter_node_traffic_gb_s'),
          evPoint('canvasScaleOutNet', 'Inter-Node Traffic (GB/s)', 'TP16 / PP1', 'tp16_pp1_dist', '128k_c1', 'inter_node_traffic_gb_s')
        ],
        backgroundColor: ['#34d399', '#38bdf8', '#fb923c', '#f43f5e']
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'Traffic (GB/s)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ display: false }} }}
    }}
  }});
}}

// --- LONG CONTEXT CHARTS ---
function initLongContextCharts() {{
  // Fig 8: 1M TP4 Closed-Loop Concurrency (c1, c2, c4)
  new Chart(document.getElementById('canvasLongCtxTtft'), {{
    type: 'bar',
    data: {{
      labels: ['c1', 'c2', 'c4'],
      datasets: [
        {{
          label: '1M TTFT (s)',
          data: [
            evPoint('canvasLongCtxTtft', '1M TTFT (s)', 'c1', 'tp4_closedloop_1m', 'c1', 'ttft_ms', v => v / 1000),
            evPoint('canvasLongCtxTtft', '1M TTFT (s)', 'c2', 'tp4_closedloop_1m', 'c2', 'ttft_ms', v => v / 1000),
            evPoint('canvasLongCtxTtft', '1M TTFT (s)', 'c4', 'tp4_closedloop_1m', 'c4', 'ttft_ms', v => v / 1000)
          ],
          backgroundColor: '#38bdf8'
        }},
        {{
          label: '1M TPOT (ms / 10)',
          data: [
            evPoint('canvasLongCtxTtft', '1M TPOT (ms / 10)', 'c1', 'tp4_closedloop_1m', 'c1', 'tpot_ms', v => v / 10),
            evPoint('canvasLongCtxTtft', '1M TPOT (ms / 10)', 'c2', 'tp4_closedloop_1m', 'c2', 'tpot_ms', v => v / 10),
            evPoint('canvasLongCtxTtft', '1M TPOT (ms / 10)', 'c4', 'tp4_closedloop_1m', 'c4', 'tpot_ms', v => v / 10)
          ],
          backgroundColor: '#fb923c'
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'TTFT (s) / Scaled TPOT' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});

  // Fig 7: 1M c1 Chunk Sweep (4K, 8K, 16K)
  new Chart(document.getElementById('canvasLongCtxChunk'), {{
    type: 'bar',
    data: {{
      labels: ['4K Chunk Budget', '8K Chunk Budget', '16K Chunk Budget'],
      datasets: [{{
        label: '1M c1 TTFT (s)',
        data: [
          evPoint('canvasLongCtxChunk', '1M c1 TTFT (s)', '4K Chunk Budget', 'tp4_chunk4k', '1m_c1', 'ttft_ms', v => v / 1000),
          evPoint('canvasLongCtxChunk', '1M c1 TTFT (s)', '8K Chunk Budget', 'tp4_chunk8k', '1m_c1', 'ttft_ms', v => v / 1000),
          evPoint('canvasLongCtxChunk', '1M c1 TTFT (s)', '16K Chunk Budget', 'tp4_chunk16k', '1m_c1', 'ttft_ms', v => v / 1000)
        ],
        backgroundColor: ['#f43f5e', '#fb923c', '#34d399']
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'TTFT (seconds)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ display: false }} }}
    }}
  }});

  // Prefix Caching: Aggregate Mean TTFT (128K & 512K)
  new Chart(document.getElementById('canvasLongCtxPrefix'), {{
    type: 'bar',
    data: {{
      labels: ['128K Prefix Aggregate Mean', '512K Prefix Aggregate Mean'],
      datasets: [{{
        label: 'Aggregate Mean TTFT (ms)',
        data: [
          evPoint('canvasLongCtxPrefix', 'Aggregate Mean TTFT (ms)', '128K Prefix Aggregate Mean', 'tp4_prefix128k', 'prefix128k', 'ttft_ms'),
          evPoint('canvasLongCtxPrefix', 'Aggregate Mean TTFT (ms)', '512K Prefix Aggregate Mean', 'tp4_prefix512k', 'prefix512k', 'ttft_ms')
        ],
        backgroundColor: ['#38bdf8', '#34d399']
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'TTFT (ms)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ display: false }} }}
    }}
  }});

  // Fig 5: 128K Capacity Knee
  new Chart(document.getElementById('canvasLongCtxKv'), {{
    type: 'line',
    data: {{
      labels: ['c1', 'c4', 'c8', 'c16'],
      datasets: [
        {{
          label: '128K Output tok/s',
          data: [
            evPoint('canvasLongCtxKv', '128K Output tok/s', 'c1', 'tp4_closedloop_128k', 'c1', 'output_tok_s'),
            evPoint('canvasLongCtxKv', '128K Output tok/s', 'c4', 'tp4_closedloop_128k', 'c4', 'output_tok_s'),
            evPoint('canvasLongCtxKv', '128K Output tok/s', 'c8', 'tp4_closedloop_128k', 'c8', 'output_tok_s'),
            evPoint('canvasLongCtxKv', '128K Output tok/s', 'c16', 'tp4_closedloop_128k', 'c16', 'output_tok_s')
          ],
          borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4, yAxisID: 'y'
        }},
        {{
          label: '128K TPOT (ms)',
          data: [
            evPoint('canvasLongCtxKv', '128K TPOT (ms)', 'c1', 'tp4_closedloop_128k', 'c1', 'tpot_ms'),
            evPoint('canvasLongCtxKv', '128K TPOT (ms)', 'c4', 'tp4_closedloop_128k', 'c4', 'tpot_ms'),
            evPoint('canvasLongCtxKv', '128K TPOT (ms)', 'c8', 'tp4_closedloop_128k', 'c8', 'tpot_ms'),
            evPoint('canvasLongCtxKv', '128K TPOT (ms)', 'c16', 'tp4_closedloop_128k', 'c16', 'tpot_ms')
          ],
          borderColor: '#f43f5e', backgroundColor: '#f43f5e', borderWidth: 2, pointRadius: 4, yAxisID: 'y1'
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{
        y: {{ type: 'linear', position: 'left', title: {{ display: true, text: 'Throughput (tok/s)' }}, grid: {{ color: '#131e33' }} }},
        y1: {{ type: 'linear', position: 'right', title: {{ display: true, text: 'TPOT (ms)' }}, grid: {{ drawOnChartArea: false }} }}
      }}
    }}
  }});
}}

// --- SCHEDULER & KV CHARTS ---
function initSchedulerKvCharts() {{
  // Fig 11: KV Cache Block Peak % vs Concurrency
  new Chart(document.getElementById('canvasSchedKvUtil'), {{
    type: 'bar',
    data: {{
      labels: ['c1', 'c4', 'c8', 'c16', 'c32'],
      datasets: [
        {{
          label: '8K KV Peak % (tp4_closedloop_8k)',
          data: [
            evPoint('canvasSchedKvUtil', '8K KV Peak % (tp4_closedloop_8k)', 'c1', 'tp4_closedloop_8k', 'c1', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '8K KV Peak % (tp4_closedloop_8k)', 'c4', 'tp4_closedloop_8k', 'c4', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '8K KV Peak % (tp4_closedloop_8k)', 'c8', 'tp4_closedloop_8k', 'c8', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '8K KV Peak % (tp4_closedloop_8k)', 'c16', 'tp4_closedloop_8k', 'c16', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '8K KV Peak % (tp4_closedloop_8k)', 'c32', 'tp4_closedloop_8k', 'c32', 'kv_peak_pct')
          ],
          backgroundColor: '#38bdf8'
        }},
        {{
          label: '128K KV Peak % (tp4_closedloop_128k)',
          data: [
            evPoint('canvasSchedKvUtil', '128K KV Peak % (tp4_closedloop_128k)', 'c1', 'tp4_closedloop_128k', 'c1', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '128K KV Peak % (tp4_closedloop_128k)', 'c4', 'tp4_closedloop_128k', 'c4', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '128K KV Peak % (tp4_closedloop_128k)', 'c8', 'tp4_closedloop_128k', 'c8', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '128K KV Peak % (tp4_closedloop_128k)', 'c16', 'tp4_closedloop_128k', 'c16', 'kv_peak_pct'),
            evPoint('canvasSchedKvUtil', '128K KV Peak % (tp4_closedloop_128k)', 'c32', 'tp4_closedloop_128k', 'c32', 'kv_peak_pct') // null
          ],
          backgroundColor: '#fb923c'
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'KV Block Utilization (%)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});

  // Queue Delay (ms)
  new Chart(document.getElementById('canvasSchedQueue'), {{
    type: 'line',
    data: {{
      labels: ['c1', 'c4', 'c8', 'c16', 'c32'],
      datasets: [
        {{
          label: '8K Queue Mean (ms)',
          data: [
            evPoint('canvasSchedQueue', '8K Queue Mean (ms)', 'c1', 'tp4_closedloop_8k', 'c1', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '8K Queue Mean (ms)', 'c4', 'tp4_closedloop_8k', 'c4', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '8K Queue Mean (ms)', 'c8', 'tp4_closedloop_8k', 'c8', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '8K Queue Mean (ms)', 'c16', 'tp4_closedloop_8k', 'c16', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '8K Queue Mean (ms)', 'c32', 'tp4_closedloop_8k', 'c32', 'queue_mean_s_from_hist', v => v * 1000)
          ],
          borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
        }},
        {{
          label: '128K Queue Mean (ms)',
          data: [
            evPoint('canvasSchedQueue', '128K Queue Mean (ms)', 'c1', 'tp4_closedloop_128k', 'c1', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '128K Queue Mean (ms)', 'c4', 'tp4_closedloop_128k', 'c4', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '128K Queue Mean (ms)', 'c8', 'tp4_closedloop_128k', 'c8', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '128K Queue Mean (ms)', 'c16', 'tp4_closedloop_128k', 'c16', 'queue_mean_s_from_hist', v => v * 1000),
            evPoint('canvasSchedQueue', '128K Queue Mean (ms)', 'c32', 'tp4_closedloop_128k', 'c32', 'queue_mean_s_from_hist', v => v * 1000) // null
          ],
          borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'Queue Wait (ms)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});

  // max_num_seqs Dedicated Sweep at 512K c4
  new Chart(document.getElementById('canvasSchedTtftPcts'), {{
    type: 'bar',
    data: {{
      labels: ['max_num_seqs = 4', 'max_num_seqs = 8', 'max_num_seqs = 16'],
      datasets: [
        {{
          label: 'TTFT (s)',
          data: [
            evPoint('canvasSchedTtftPcts', 'TTFT (s)', 'max_num_seqs = 4', 'tp4_512k_maxseq4', '512k_c4', 'ttft_ms', v => v / 1000),
            evPoint('canvasSchedTtftPcts', 'TTFT (s)', 'max_num_seqs = 8', 'tp4_512k_maxseq8', '512k_c4', 'ttft_ms', v => v / 1000),
            evPoint('canvasSchedTtftPcts', 'TTFT (s)', 'max_num_seqs = 16', 'tp4_512k_maxseq16', '512k_c4', 'ttft_ms', v => v / 1000)
          ],
          backgroundColor: '#38bdf8'
        }},
        {{
          label: 'TPOT (ms / 10)',
          data: [
            evPoint('canvasSchedTtftPcts', 'TPOT (ms / 10)', 'max_num_seqs = 4', 'tp4_512k_maxseq4', '512k_c4', 'tpot_ms', v => v / 10),
            evPoint('canvasSchedTtftPcts', 'TPOT (ms / 10)', 'max_num_seqs = 8', 'tp4_512k_maxseq8', '512k_c4', 'tpot_ms', v => v / 10),
            evPoint('canvasSchedTtftPcts', 'TPOT (ms / 10)', 'max_num_seqs = 16', 'tp4_512k_maxseq16', '512k_c4', 'tpot_ms', v => v / 10)
          ],
          backgroundColor: '#fb923c'
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'TTFT (s) / Scaled TPOT' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});

  // Fig 6: Long-Context TPOT Degradation under Concurrency
  new Chart(document.getElementById('canvasSchedTpotPcts'), {{
    type: 'line',
    data: {{
      labels: ['c1', 'c2', 'c4'],
      datasets: [
        {{
          label: '512K TPOT (ms)',
          data: [
            evPoint('canvasSchedTpotPcts', '512K TPOT (ms)', 'c1', 'tp4_closedloop_512k', 'c1', 'tpot_ms'),
            evPoint('canvasSchedTpotPcts', '512K TPOT (ms)', 'c2', 'tp4_closedloop_512k', 'c2', 'tpot_ms'),
            evPoint('canvasSchedTpotPcts', '512K TPOT (ms)', 'c4', 'tp4_closedloop_512k', 'c4', 'tpot_ms')
          ],
          borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
        }},
        {{
          label: '1M TPOT (ms)',
          data: [
            evPoint('canvasSchedTpotPcts', '1M TPOT (ms)', 'c1', 'tp4_closedloop_1m', 'c1', 'tpot_ms'),
            evPoint('canvasSchedTpotPcts', '1M TPOT (ms)', 'c2', 'tp4_closedloop_1m', 'c2', 'tpot_ms'),
            evPoint('canvasSchedTpotPcts', '1M TPOT (ms)', 'c4', 'tp4_closedloop_1m', 'c4', 'tpot_ms')
          ],
          borderColor: '#f43f5e', backgroundColor: '#f43f5e', borderWidth: 2, pointRadius: 4
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ title: {{ display: true, text: 'TPOT (ms/token)' }}, grid: {{ color: '#131e33' }} }} }},
      plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 8 }} }} }}
    }}
  }});
}}

// --- DYNAMIC EVIDENCE TABLE RENDERING (Part 2 Batch B, Spec §12) ---
function renderEvidenceTable(filter) {{
  const tbody = document.getElementById('evidenceTableBody');
  if (!tbody) return;

  tbody.innerHTML = '';
  let filtered = EVIDENCE_DATA;
  if (filter === '8k') {{
    filtered = EVIDENCE_DATA.filter(r => r.input_tokens_displayed === 8192);
  }} else if (filter === '128k') {{
    filtered = EVIDENCE_DATA.filter(r => r.input_tokens_displayed === 131072);
  }} else if (filter === '512k') {{
    filtered = EVIDENCE_DATA.filter(r => r.input_tokens_displayed === 524288);
  }} else if (filter === '1m') {{
    filtered = EVIDENCE_DATA.filter(r => r.input_tokens_displayed === 1000000);
  }}

  filtered.forEach((r, idx) => {{
    const tr = document.createElement('tr');
    tr.id = `ev-row-${{r.row_id}}`;
    tr.style.cursor = 'pointer';
    tr.title = 'Click to copy Row ID';
    tr.onclick = () => {{
      navigator.clipboard.writeText(r.row_id);
    }};

    tr.innerHTML = `
      <td>${{idx + 1}}</td>
      <td style="font-family:monospace; font-weight:700; color:#38bdf8;">${{r.row_id}}</td>
      <td>${{r.case}}</td>
      <td>${{r.bench}}</td>
      <td>${{r.tp}}</td>
      <td>${{r.pp}}</td>
      <td>${{r.input_tokens_displayed.toLocaleString()}}</td>
      <td>c${{r.concurrency}}</td>
      <td style="text-align:right;">${{r.ttft_ms.toFixed(1)}}</td>
      <td style="text-align:right;">${{r.tpot_ms.toFixed(2)}}</td>
      <td style="text-align:right;">${{r.output_tok_s.toFixed(1)}}</td>
      <td style="text-align:right;">${{r.kv_peak_pct.toFixed(1)}}%</td>
      <td style="text-align:right;">${{r.metric_samples || 'null'}}</td>
      <td style="text-align:right;">${{r.completed || 'null'}}</td>
      <td style="text-align:right;">${{r.preemptions_delta !== null ? r.preemptions_delta.toFixed(1) : 'null'}}</td>
      <td><span style="color:#34d399;">${{r.status}}</span></td>
      <td style="font-size:7px; color:#94a3b8;">${{r.provenance_status}}</td>
      <td style="font-size:7px; color:#cbd5e1;">${{r.source_file}}</td>
    `;
    tbody.appendChild(tr);
  }});
}}

function filterEvidence(filter) {{
  document.querySelectorAll('.context-filter-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('onclick').includes(filter));
  }});
  renderEvidenceTable(filter);
}}

// Initialize executive tab on load
window.addEventListener('DOMContentLoaded', () => {{
  initTab('executive');
  // Also initialize all tabs so charts exist for verifier
  ['scaleup', 'scaleout', 'longcontext', 'schedulerkv', 'evidence'].forEach(t => initTab(t));
}});
</script>
</body>
</html>
"""

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"MASTER_CHARACTERIZATION_DASHBOARD.html successfully generated ({len(html_content.splitlines())} lines).")
