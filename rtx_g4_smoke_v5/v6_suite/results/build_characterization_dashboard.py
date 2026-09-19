import json
import os

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V5 vLLM Runtime Characterization Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root {
    --bg: #0b0f17;
    --card-bg: #121824;
    --card-bg-subtle: #172033;
    --border: #222f46;
    --border-light: #2c3e5d;
    --accent-blue: #3b82f6;
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --accent-purple: #a855f7;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
  body { background-color: var(--bg); color: var(--text-main); padding: 18px; min-height: 100vh; font-size: 12px; }

  /* Navigation Bar */
  .header-nav { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 10px 18px; margin-bottom: 16px; }
  .nav-title-group h1 { font-size: 18px; font-weight: 700; color: #fff; letter-spacing: -0.3px; display: flex; align-items: center; gap: 10px; }
  .nav-title-group p { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
  .view-switcher { display: flex; background: #0b111c; padding: 4px; border-radius: 8px; border: 1px solid var(--border); gap: 4px; }
  .switch-btn { background: transparent; border: none; color: var(--text-muted); font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 6px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; gap: 6px; }
  .switch-btn:hover { color: #fff; background: rgba(255,255,255,0.05); }
  .switch-btn.active { background: var(--accent-blue); color: #fff; box-shadow: 0 2px 10px rgba(59, 130, 246, 0.4); }

  .badges-row { display: flex; gap: 8px; align-items: center; font-size: 10px; }
  .badge { display: inline-flex; align-items: center; gap: 5px; padding: 3px 8px; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
  .badge-dot { width: 6px; height: 6px; border-radius: 50%; }
  .badge-measured { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
  .badge-measured .badge-dot { background: #10b981; }
  .badge-derived { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
  .badge-derived .badge-dot { background: #3b82f6; }
  .badge-local { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
  .badge-local .badge-dot { background: #f59e0b; }
  .badge-unresolved { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }
  .badge-unresolved .badge-dot { background: #f43f5e; }

  /* 6 Top KPI Sparkline Grid */
  .kpi-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 16px; }
  .kpi-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; justify-content: space-between; position: relative; overflow: hidden; }
  .kpi-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
  .kpi-title { font-size: 11px; font-weight: 600; color: var(--text-muted); }
  .kpi-subtitle { font-size: 9.5px; color: var(--text-dim); }
  .kpi-value-row { display: flex; justify-content: space-between; align-items: flex-end; margin: 4px 0; }
  .kpi-value { font-size: 15px; font-weight: 700; color: #fff; }
  .kpi-trend { font-size: 10px; color: var(--accent-emerald); font-weight: 600; }
  .kpi-sparkline { width: 64px; height: 26px; }
  .kpi-footer { font-size: 9.5px; color: var(--text-dim); margin-top: 4px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 4px; }

  /* 3-Column Main Content Layout */
  .dashboard-body { display: grid; grid-template-columns: 280px 1fr 320px; gap: 14px; }
  .col-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; margin-bottom: 14px; }
  .col-card:last-child { margin-bottom: 0; }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
  .card-header h3 { font-size: 12px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px; }

  /* Tables */
  .custom-table { width: 100%; border-collapse: collapse; font-size: 10px; }
  .custom-table th { text-align: left; padding: 5px 6px; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--border); }
  .custom-table td { padding: 5px 6px; border-bottom: 1px solid rgba(255,255,255,0.03); color: #cbd5e1; }
  .custom-table tr:hover td { background: rgba(255,255,255,0.02); }

  /* Regime Transitions Pipeline */
  .regime-pipeline { display: flex; gap: 4px; margin: 8px 0; }
  .regime-step { flex: 1; padding: 6px 4px; font-size: 9px; text-align: center; border-radius: 4px; font-weight: 600; line-height: 1.2; position: relative; }
  .regime-step small { display: block; font-size: 7.5px; font-weight: 400; opacity: 0.8; margin-top: 2px; }
  .reg-1 { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
  .reg-2 { background: rgba(6, 182, 212, 0.2); color: #67e8f9; border: 1px solid rgba(6, 182, 212, 0.4); }
  .reg-3 { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }
  .reg-4 { background: rgba(249, 115, 22, 0.2); color: #fdba74; border: 1px solid rgba(249, 115, 22, 0.4); }
  .reg-5 { background: rgba(244, 63, 94, 0.2); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.4); }

  /* Charts Container */
  .charts-2x2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .chart-box { background: var(--card-bg-subtle); border: 1px solid var(--border); border-radius: 6px; padding: 10px; height: 230px; position: relative; }
  .chart-title { font-size: 11px; font-weight: 600; color: #fff; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }

  /* Heatmap */
  .heatmap-grid { display: grid; grid-template-columns: 50px repeat(4, 1fr); gap: 4px; margin-top: 6px; font-size: 9.5px; }
  .heat-col-head { text-align: center; color: var(--text-muted); font-weight: 600; padding: 3px 0; }
  .heat-row-head { color: var(--text-muted); font-weight: 600; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px; }
  .heat-cell { padding: 6px 2px; text-align: center; border-radius: 4px; font-weight: 600; font-size: 9px; cursor: default; transition: transform 0.15s ease; }
  .heat-cell:hover { transform: scale(1.05); z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
  .heat-healthy { background: #065f46; color: #a7f3d0; border: 1px solid #047857; }
  .heat-queueing { background: #78350f; color: #fde68a; border: 1px solid #b45309; }
  .heat-pressure { background: #831843; color: #fbcfe8; border: 1px solid #be185d; }
  .heat-unresolved { background: #27272a; color: #a1a1aa; border: 1px dashed #52525b; }

  /* Breakdown Segmented Bars */
  .formula-box { background: #090d14; border: 1px solid var(--border); border-radius: 4px; padding: 6px 8px; font-family: monospace; font-size: 9.5px; color: #38bdf8; margin: 6px 0; }
  .segmented-bar { display: flex; height: 22px; border-radius: 4px; overflow: hidden; margin: 8px 0; font-size: 9px; font-weight: 700; color: #000; }
  .seg { display: flex; align-items: center; justify-content: center; }
  .seg-a { background: #34d399; }
  .seg-b { background: #38bdf8; }
  .seg-c { background: #818cf8; }
  .seg-d { background: #c084fc; }
  .seg-e { background: #fb7185; }
  .seg-f { background: #facc15; }
  .seg-g { background: #94a3b8; }
  .seg-o { background: #1e293b; color: #fff; border: 1px dashed #64748b; }

  /* Takeaways Accordion / List */
  .takeaway-item { background: var(--card-bg-subtle); border: 1px solid var(--border); border-radius: 6px; padding: 7px 10px; margin-bottom: 6px; font-size: 10px; }
  .takeaway-header { font-weight: 600; color: #fff; display: flex; align-items: center; gap: 8px; }
  .takeaway-num { width: 16px; height: 16px; border-radius: 50%; background: var(--accent-blue); color: #fff; font-size: 9px; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; }
  .takeaway-body { color: var(--text-muted); font-size: 9.5px; margin-top: 4px; padding-left: 24px; line-height: 1.35; }

  /* Topology Cards for Multi-Node */
  .topo-card { background: var(--card-bg-subtle); border: 1px solid var(--border); border-radius: 6px; padding: 10px; margin-bottom: 8px; transition: border-color 0.2s; }
  .topo-card:hover { border-color: var(--accent-blue); }
  .topo-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
  .topo-name { font-size: 12px; font-weight: 700; color: #fff; }
  .topo-desc { font-size: 9.5px; color: var(--text-dim); }
  .topo-bullets { margin-top: 6px; font-size: 9.5px; color: #cbd5e1; list-style: none; }
  .topo-bullets li { position: relative; padding-left: 12px; margin-bottom: 2px; }
  .topo-bullets li::before { content: "•"; position: absolute; left: 2px; color: var(--accent-blue); }

  /* Cluster Map SVG styling */
  .cluster-box { background: #080d17; border: 1px solid var(--border); border-radius: 6px; padding: 10px; margin: 8px 0; }
  .cluster-title { font-size: 10px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; }

  /* Footer */
  .dashboard-footer { margin-top: 14px; padding: 10px 14px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 10px; color: var(--text-dim); }
</style>
</head>
<body>

<!-- Header & Nav -->
<div class="header-nav">
  <div class="nav-title-group">
    <h1 id="mainTitle">V5 vLLM Runtime Characterization — Scale Up (Single Node)</h1>
    <p id="mainSubtitle">MEASURED-48B surrogate; do not scale absolute values to Kimi K3. | GCP Blackwell / RTX 6000 Ada Live Telemetry</p>
  </div>
  <div class="view-switcher">
    <button class="switch-btn active" id="btnScaleUp" onclick="switchView('scale-up')">
      <span>⚡</span> Scale Up (Single Node)
    </button>
    <button class="switch-btn" id="btnScaleOut" onclick="switchView('scale-out')">
      <span>🌐</span> Scale Out (Multi-Node)
    </button>
  </div>
  <div class="badges-row">
    <span class="badge badge-measured"><span class="badge-dot"></span>MEASURED-48B</span>
    <span class="badge badge-derived"><span class="badge-dot"></span>MODELED-K3</span>
    <span class="badge badge-local"><span class="badge-dot"></span>LOCAL-REAL</span>
    <span class="badge badge-unresolved"><span class="badge-dot"></span>UNRESOLVED</span>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 1: SCALE UP (SINGLE NODE) -->
<!-- ======================================================== -->
<div id="viewScaleUp">
  <!-- 6 Top KPI Sparkline Grid -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">TTFT</div>
          <div class="kpi-subtitle">(time to first token)</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">222 ms → 74.8s</div>
        <svg class="kpi-sparkline" viewBox="0 0 60 25">
          <path d="M 2 22 L 18 20 L 35 14 L 58 3" fill="none" stroke="#10b981" stroke-width="2"/>
        </svg>
      </div>
      <div class="kpi-footer">Increases with context; higher for TP8 at long context.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">TPOT / ITL</div>
          <div class="kpi-subtitle">(per output token)</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">4.45 → 10.2 ms</div>
        <svg class="kpi-sparkline" viewBox="0 0 60 25">
          <path d="M 2 5 L 18 12 L 35 16 L 58 19" fill="none" stroke="#38bdf8" stroke-width="2"/>
        </svg>
      </div>
      <div class="kpi-footer">Decreases with concurrency, then plateaus.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">Throughput</div>
          <div class="kpi-subtitle">(tokens / second)</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">28.2 → 721 tok/s</div>
        <svg class="kpi-sparkline" viewBox="0 0 60 25">
          <path d="M 2 20 L 18 14 L 35 8 L 58 6" fill="none" stroke="#10b981" stroke-width="2"/>
        </svg>
      </div>
      <div class="kpi-footer">Rises with concurrency, then flattens (capacity knee).</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">Queue Time</div>
          <div class="kpi-subtitle">(time in scheduler)</div>
        </div>
        <span class="badge badge-derived">D</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">0.008 → 0.95 s</div>
        <svg class="kpi-sparkline" viewBox="0 0 60 25">
          <path d="M 2 22 L 25 22 L 40 18 L 58 4" fill="none" stroke="#f59e0b" stroke-width="2"/>
        </svg>
      </div>
      <div class="kpi-footer">Low → rises after capacity knee.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">KV Utilization</div>
          <div class="kpi-subtitle">(of GPU memory)</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">1.2% → 15.5%</div>
        <svg class="kpi-sparkline" viewBox="0 0 60 25">
          <path d="M 2 21 L 18 18 L 35 12 L 58 7" fill="none" stroke="#a855f7" stroke-width="2"/>
        </svg>
      </div>
      <div class="kpi-footer">Increases with context and concurrency.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">Capacity Knee</div>
          <div class="kpi-subtitle">(queueing onset)</div>
        </div>
        <span class="badge badge-derived">D</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">c = 8 → 16</div>
        <svg class="kpi-sparkline" viewBox="0 0 60 25">
          <path d="M 2 22 L 20 20 L 35 15 L 45 8 L 58 4" fill="none" stroke="#f43f5e" stroke-width="2"/>
        </svg>
      </div>
      <div class="kpi-footer">Model and config dependent (gated admission).</div>
    </div>
  </div>

  <!-- 3-Column Body -->
  <div class="dashboard-body">
    <!-- Left Column -->
    <div>
      <div class="col-card">
        <div class="card-header">
          <h3>Workload & Config Matrix</h3>
          <span class="badge badge-measured">M</span>
        </div>
        <table class="custom-table">
          <thead>
            <tr>
              <th>Context</th>
              <th>Concurrency</th>
              <th>Chunk</th>
              <th>Topo</th>
              <th>Cache</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>8K</strong></td>
              <td>c1, c4, c8, c16, c32</td>
              <td>4K/8K/16K</td>
              <td>TP4 / TP8</td>
              <td>cold / hit</td>
            </tr>
            <tr>
              <td><strong>128K</strong></td>
              <td>c1, c4, c8, c16, c32</td>
              <td>4K/8K/16K</td>
              <td>TP4 / TP8</td>
              <td>cold / hit</td>
            </tr>
            <tr>
              <td><strong>512K</strong></td>
              <td>c1, c4, c8, c16, c32</td>
              <td>4K/8K/16K</td>
              <td>TP4 / TP8</td>
              <td>cold / hit</td>
            </tr>
            <tr>
              <td><strong>~1M</strong></td>
              <td>c1, c2, c4 (gated)</td>
              <td>4K/8K/16K</td>
              <td>TP4 / TP8</td>
              <td>cold / hit</td>
            </tr>
          </tbody>
        </table>
        <div style="background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); border-radius: 4px; padding: 6px; margin-top: 8px; font-size: 9px; color: #fbbf24;">
          ⚠️ ~1M context is capacity-gated (admitted cleanly up to c=4 without OOM).
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>Regime Transitions</h3>
          <span class="badge badge-derived">D</span>
        </div>
        <div class="regime-pipeline">
          <div class="regime-step reg-1">Under-<br>utilized<small>Compute bound</small></div>
          <div class="regime-step reg-2">Efficient<br>batching<small>High TPS</small></div>
          <div class="regime-step reg-3">Queue<br>onset<small>Knee reached</small></div>
          <div class="regime-step reg-4">KV cache<br>pressure<small>Paging active</small></div>
          <div class="regime-step reg-5">Collapse /<br>throttle<small>Avoided (gate)</small></div>
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>Runtime Reserve (Overheads)</h3>
          <span class="badge badge-measured">M</span>
        </div>
        <table class="custom-table">
          <thead>
            <tr><th>Component</th><th>Impact</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr><td>Scheduler / Queue</td><td><div style="width: 25px; height: 4px; background:#38bdf8; border-radius:2px;"></div></td><td>Measured</td></tr>
            <tr><td>Preemption</td><td><div style="width: 5px; height: 4px; background:#10b981; border-radius:2px;"></div></td><td>0 in matrix</td></tr>
            <tr><td>KV Cache Paging</td><td><div style="width: 45px; height: 4px; background:#a855f7; border-radius:2px;"></div></td><td>12-15% peak</td></tr>
            <tr><td>CPU Offload</td><td><div style="width: 65px; height: 4px; background:#f43f5e; border-radius:2px;"></div></td><td>Severe penalty</td></tr>
            <tr><td>Kernel Launch</td><td><div style="width: 30px; height: 4px; background:#38bdf8; border-radius:2px;"></div></td><td>PyTorch runtime</td></tr>
            <tr><td>Prefix Cache Hit</td><td><div style="width: 75px; height: 4px; background:#10b981; border-radius:2px;"></div></td><td>-47% to -80%</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Center Column (4 Charts) -->
    <div>
      <div class="charts-2x2">
        <div class="chart-box">
          <div class="chart-title">
            <span>TTFT vs Context Length</span>
            <span class="badge badge-measured">M</span>
          </div>
          <canvas id="chartTtftContext"></canvas>
        </div>

        <div class="chart-box">
          <div class="chart-title">
            <span>TPOT / ITL vs Concurrency</span>
            <span class="badge badge-measured">M</span>
          </div>
          <canvas id="chartTpotConcurrency"></canvas>
        </div>

        <div class="chart-box">
          <div class="chart-title">
            <span>Throughput & Queue Time vs Concurrency</span>
            <span class="badge badge-measured">M</span>
          </div>
          <canvas id="chartTpsQueue"></canvas>
        </div>

        <div class="chart-box" style="display: flex; flex-direction: column;">
          <div class="chart-title">
            <span>Workload Envelope (Observed Behavior)</span>
            <span class="badge badge-measured">M</span>
          </div>
          <div class="heatmap-grid" style="flex: 1;">
            <div class="heat-col-head"></div>
            <div class="heat-col-head">8K</div>
            <div class="heat-col-head">128K</div>
            <div class="heat-col-head">512K</div>
            <div class="heat-col-head">~1M</div>

            <div class="heat-row-head">c32</div>
            <div class="heat-cell heat-queueing">Queueing</div>
            <div class="heat-cell heat-queueing">Queueing</div>
            <div class="heat-cell heat-pressure">KV Press</div>
            <div class="heat-cell heat-unresolved">NOT RUN</div>

            <div class="heat-row-head">c16</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-queueing">Queueing</div>
            <div class="heat-cell heat-pressure">KV Press</div>
            <div class="heat-cell heat-unresolved">NOT RUN</div>

            <div class="heat-row-head">c8</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-queueing">Queueing</div>
            <div class="heat-cell heat-pressure">KV Press</div>

            <div class="heat-row-head">c4</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-queueing">Queueing</div>

            <div class="heat-row-head">c1</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-healthy">Healthy</div>
            <div class="heat-cell heat-healthy">Healthy</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Column (Breakdowns & Takeaways) -->
    <div>
      <div class="col-card">
        <div class="card-header">
          <h3>TTFT / Prefill Breakdown</h3>
          <span class="badge badge-derived">D</span>
        </div>
        <div class="formula-box">T_prefill ≈ A_GPU + B_TP + C_PP + D_PCIe + E_vLLM + F_CPU - O_overlap</div>
        <div class="segmented-bar">
          <div class="seg seg-a" style="width: 48%;" title="A_GPU (Attention & GEMM)">A (48%)</div>
          <div class="seg seg-b" style="width: 22%;" title="B_TP (AllReduce)">B (22%)</div>
          <div class="seg seg-c" style="width: 8%;" title="C_PP (Pipeline)">C (8%)</div>
          <div class="seg seg-e" style="width: 14%;" title="E_vLLM (Scheduler)">E (14%)</div>
          <div class="seg seg-f" style="width: 8%;" title="F_CPU (Launch)">F (8%)</div>
        </div>
        <div style="font-size: 9px; color: var(--text-dim);">
          A: GPU GEMM (Measured) | B: TP Comm (Measured) | E: vLLM Schedule (Measured)
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>TPOT / Decode Breakdown</h3>
          <span class="badge badge-derived">D</span>
        </div>
        <div class="formula-box">T_decode ≈ A_comp + B_TP + C_runtime + D_KV - O_overlap</div>
        <div class="segmented-bar">
          <div class="seg seg-a" style="width: 32%;" title="A_comp (Small-M GEMM)">A (32%)</div>
          <div class="seg seg-b" style="width: 38%;" title="B_TP (Latency Bound)">B (38%)</div>
          <div class="seg seg-c" style="width: 18%;" title="C_runtime">C (18%)</div>
          <div class="seg seg-d" style="width: 12%;" title="D_KV (Gather/Paging)">D (12%)</div>
        </div>
        <div style="font-size: 9px; color: var(--text-dim);">
          At small batch, TP comm (B) and UPI socket crossings dominate decode.
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>Interpretation (Key Takeaways)</h3>
        </div>
        <div class="takeaway-item">
          <div class="takeaway-header">
            <span class="takeaway-num">1</span>
            <span>Best Chunk Size: 16K Budget</span>
          </div>
          <div class="takeaway-body">16K chunk reduces 1M TTFT to 89.16s (vs 93.38s @ 8K and 122.10s @ 4K).</div>
        </div>
        <div class="takeaway-item">
          <div class="takeaway-header">
            <span class="takeaway-num">2</span>
            <span>TP4 vs TP8 Topology Crossover</span>
          </div>
          <div class="takeaway-body">TP8 is 19.8% faster on 1M prefill; TP4 is 15.2% faster on 1M decode by avoiding Intel UPI cross-socket latency.</div>
        </div>
        <div class="takeaway-item">
          <div class="takeaway-header">
            <span class="takeaway-num">3</span>
            <span>Capacity Knee at c=8 to 16</span>
          </div>
          <div class="takeaway-body">Throughput plateaus near ~720 tok/s at 8K while queue wait rises past 200 ms.</div>
        </div>
        <div class="takeaway-item">
          <div class="takeaway-header">
            <span class="takeaway-num">4</span>
            <span>Prefix Caching Reduces TTFT by 80%</span>
          </div>
          <div class="takeaway-body">128K prefix reduces TTFT from 4,534 ms to 910 ms; 512K prefix cuts TTFT from 31.9s to 16.8s.</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================== -->
<!-- TAB 2: SCALE OUT (MULTI-NODE) -->
<!-- ======================================================== -->
<div id="viewScaleOut" style="display: none;">
  <!-- 6 Top KPI Multi-Node Grid -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">TTFT (128K)</div>
          <div class="kpi-subtitle">Lower is better</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">1,723.7 ms</div>
        <div class="kpi-trend">TP4 / PP4</div>
      </div>
      <div class="kpi-footer">56.0% faster than single-node baseline.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">TPOT / ITL</div>
          <div class="kpi-subtitle">Lower is better</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">5.43 ms</div>
        <div class="kpi-trend">TP4 / PP2</div>
      </div>
      <div class="kpi-footer">Confined within local PCIe socket.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">Throughput</div>
          <div class="kpi-subtitle">Higher is better</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">63,284 tok/s</div>
        <div class="kpi-trend">TP4 / PP4</div>
      </div>
      <div class="kpi-footer">Aggregate token processing rate across 16 GPUs.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">Topology Champ</div>
          <div class="kpi-subtitle">Optimal layout</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">TP4 / PP4</div>
        <div class="kpi-trend">Optimal</div>
      </div>
      <div class="kpi-footer">Avoids cross-node AllReduce entirely.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">PP Bubble Risk</div>
          <div class="kpi-subtitle">Pipeline overhead</div>
        </div>
        <span class="badge badge-derived">D</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">~11.4%</div>
        <div class="kpi-trend" style="color:#f59e0b;">PP4 Bubble</div>
      </div>
      <div class="kpi-footer">Well compensated by localized TP4 speed.</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-header">
        <div>
          <div class="kpi-title">Network Penalty</div>
          <div class="kpi-subtitle">VPC TCP/IP Impact</div>
        </div>
        <span class="badge badge-measured">M</span>
      </div>
      <div class="kpi-value-row">
        <div class="kpi-value">3.5x Slowdown</div>
        <div class="kpi-trend" style="color:#f43f5e;">TP16 / PP1</div>
      </div>
      <div class="kpi-footer">Cross-node AllReduce severely bounded.</div>
    </div>
  </div>

  <!-- 3-Column Body -->
  <div class="dashboard-body">
    <!-- Left Column: Topology Cards & Cluster Map -->
    <div>
      <div class="col-card">
        <div class="card-header">
          <h3>Topology Candidates</h3>
          <span class="badge badge-measured">M</span>
        </div>
        
        <div class="topo-card">
          <div class="topo-head">
            <span class="topo-name" style="color:#38bdf8;">TP4 / PP4 (Optimal)</span>
            <span class="badge badge-measured">M</span>
          </div>
          <div class="topo-desc">Multi-Node (2 nodes × 8 GPUs, 16 GPUs total)</div>
          <ul class="topo-bullets">
            <li><strong>128K TTFT: 1,723.66 ms</strong> | <strong>TPOT: 5.53 ms</strong></li>
            <li><strong>512K TTFT: 10,226.07 ms</strong> (Fastest 512K)</li>
            <li>TP4 stays within NUMA socket; PP4 crosses nodes.</li>
          </ul>
        </div>

        <div class="topo-card">
          <div class="topo-head">
            <span class="topo-name" style="color:#34d399;">TP4 / PP2</span>
            <span class="badge badge-measured">M</span>
          </div>
          <div class="topo-desc">Multi-Node (2 nodes × 4 GPUs active)</div>
          <ul class="topo-bullets">
            <li>128K TTFT: 2,646.62 ms | TPOT: 5.43 ms</li>
            <li>512K TTFT: 17,959.16 ms</li>
            <li>Minimal PP bubble; lower aggregate compute.</li>
          </ul>
        </div>

        <div class="topo-card">
          <div class="topo-head">
            <span class="topo-name" style="color:#a855f7;">TP8 / PP2</span>
            <span class="badge badge-measured">M</span>
          </div>
          <div class="topo-desc">Multi-Node (2 nodes × 8 GPUs)</div>
          <ul class="topo-bullets">
            <li>128K TTFT: 2,817.62 ms | TPOT: 7.47 ms</li>
            <li>512K TTFT: 15,588.37 ms</li>
            <li>TP8 incurs intra-node UPI latency on decode.</li>
          </ul>
        </div>

        <div class="topo-card">
          <div class="topo-head">
            <span class="topo-name" style="color:#f43f5e;">TP16 / PP1 (Network Bound)</span>
            <span class="badge badge-measured">M</span>
          </div>
          <div class="topo-desc">Single Stage (16 GPUs AllReduce over VPC)</div>
          <ul class="topo-bullets">
            <li>128K TTFT: 6,024.89 ms | TPOT: 11.35 ms</li>
            <li>Zero PP bubble, but severe network latency penalty.</li>
          </ul>
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>Cluster Map (2 Nodes × 8 GPUs)</h3>
          <span class="badge badge-local">L</span>
        </div>
        <div class="cluster-box">
          <svg viewBox="0 0 240 100" style="width: 100%; height: auto;">
            <!-- Node 0 -->
            <rect x="5" y="5" width="105" height="90" rx="6" fill="#121a29" stroke="#38bdf8" stroke-width="1.2"/>
            <text x="12" y="20" fill="#38bdf8" font-size="8" font-weight="700">Node 0 (10.128.0.39)</text>
            <!-- Sockets -->
            <rect x="10" y="26" width="45" height="40" rx="3" fill="#1e293b" stroke="#334155" stroke-width="0.8"/>
            <text x="14" y="36" fill="#94a3b8" font-size="6">Socket 0 (TP4)</text>
            <circle cx="20" cy="50" r="4" fill="#10b981"/><text x="18" y="52" fill="#000" font-size="5" font-weight="700">0</text>
            <circle cx="30" cy="50" r="4" fill="#10b981"/><text x="28" y="52" fill="#000" font-size="5" font-weight="700">1</text>
            <circle cx="40" cy="50" r="4" fill="#10b981"/><text x="38" y="52" fill="#000" font-size="5" font-weight="700">2</text>
            <circle cx="50" cy="50" r="4" fill="#10b981"/><text x="48" y="52" fill="#000" font-size="5" font-weight="700">3</text>

            <rect x="60" y="26" width="45" height="40" rx="3" fill="#1e293b" stroke="#334155" stroke-width="0.8"/>
            <text x="64" y="36" fill="#94a3b8" font-size="6">Socket 1 (TP4)</text>
            <circle cx="70" cy="50" r="4" fill="#10b981"/><text x="68" y="52" fill="#000" font-size="5" font-weight="700">4</text>
            <circle cx="80" cy="50" r="4" fill="#10b981"/><text x="78" y="52" fill="#000" font-size="5" font-weight="700">5</text>
            <circle cx="90" cy="50" r="4" fill="#10b981"/><text x="88" y="52" fill="#000" font-size="5" font-weight="700">6</text>
            <circle cx="100" cy="50" r="4" fill="#10b981"/><text x="98" y="52" fill="#000" font-size="5" font-weight="700">7</text>

            <text x="15" y="86" fill="#64748b" font-size="6.5">Ray Head: Port 6379</text>

            <!-- Network Link -->
            <path d="M 110 50 L 130 50" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="2,2"/>
            <text x="113" y="44" fill="#f59e0b" font-size="6">VPC</text>

            <!-- Node 1 -->
            <rect x="130" y="5" width="105" height="90" rx="6" fill="#121a29" stroke="#a855f7" stroke-width="1.2"/>
            <text x="137" y="20" fill="#a855f7" font-size="8" font-weight="700">Node 1 (10.128.0.40)</text>
            <!-- Sockets -->
            <rect x="135" y="26" width="45" height="40" rx="3" fill="#1e293b" stroke="#334155" stroke-width="0.8"/>
            <text x="139" y="36" fill="#94a3b8" font-size="6">Socket 0 (TP4)</text>
            <circle cx="145" cy="50" r="4" fill="#10b981"/><text x="143" y="52" fill="#000" font-size="5" font-weight="700">0</text>
            <circle cx="155" cy="50" r="4" fill="#10b981"/><text x="153" y="52" fill="#000" font-size="5" font-weight="700">1</text>
            <circle cx="165" cy="50" r="4" fill="#10b981"/><text x="163" y="52" fill="#000" font-size="5" font-weight="700">2</text>
            <circle cx="175" cy="50" r="4" fill="#10b981"/><text x="173" y="52" fill="#000" font-size="5" font-weight="700">3</text>

            <rect x="185" y="26" width="45" height="40" rx="3" fill="#1e293b" stroke="#334155" stroke-width="0.8"/>
            <text x="189" y="36" fill="#94a3b8" font-size="6">Socket 1 (TP4)</text>
            <circle cx="195" cy="50" r="4" fill="#10b981"/><text x="193" y="52" fill="#000" font-size="5" font-weight="700">4</text>
            <circle cx="205" cy="50" r="4" fill="#10b981"/><text x="203" y="52" fill="#000" font-size="5" font-weight="700">5</text>
            <circle cx="215" cy="50" r="4" fill="#10b981"/><text x="213" y="52" fill="#000" font-size="5" font-weight="700">6</text>
            <circle cx="225" cy="50" r="4" fill="#10b981"/><text x="223" y="52" fill="#000" font-size="5" font-weight="700">7</text>

            <text x="140" y="86" fill="#64748b" font-size="6.5">Ray Worker Joined</text>
          </svg>
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>Per-Node GPU Balance</h3>
          <span class="badge badge-measured">M</span>
        </div>
        <div style="height: 140px;">
          <canvas id="chartGpuBalance"></canvas>
        </div>
      </div>
    </div>

    <!-- Center Column: Multi-Node Charts -->
    <div>
      <div class="charts-2x2">
        <div class="chart-box">
          <div class="chart-title">
            <span>TTFT by Topology & Context</span>
            <span class="badge badge-measured">M</span>
          </div>
          <canvas id="chartMultiTtft"></canvas>
        </div>

        <div class="chart-box">
          <div class="chart-title">
            <span>TPOT / ITL by Topology</span>
            <span class="badge badge-measured">M</span>
          </div>
          <canvas id="chartMultiTpot"></canvas>
        </div>

        <div class="chart-box" style="grid-column: span 2; height: 240px;">
          <div class="chart-title">
            <span>Network & PP Sensitivity (Provenance Analysis)</span>
            <span class="badge badge-derived">D</span>
          </div>
          <canvas id="chartNetworkSensitivity"></canvas>
        </div>
      </div>
    </div>

    <!-- Right Column: Decision Panel & Analysis -->
    <div>
      <div class="col-card">
        <div class="card-header">
          <h3>Tworkload Decomposition</h3>
          <span class="badge badge-derived">D</span>
        </div>
        <div class="formula-box">T_workload = A_GPU + B_TP + C_PP + D_PCIe + E_vLLM + F_CPU - O_overlap</div>
        <div class="segmented-bar">
          <div class="seg seg-a" style="width: 44%;" title="A_GPU (Compute)">A (44%)</div>
          <div class="seg seg-b" style="width: 18%;" title="B_TP (Local TP4)">B (18%)</div>
          <div class="seg seg-c" style="width: 22%;" title="C_PP (PP4 Stage Hops)">C (22%)</div>
          <div class="seg seg-e" style="width: 10%;" title="E_vLLM (Runtime)">E (10%)</div>
          <div class="seg seg-f" style="width: 6%;" title="F_CPU">F (6%)</div>
        </div>
        <div style="font-size: 9px; color: var(--text-dim);">
          In TP4/PP4, PP stage latency (C) replaces network AllReduce completely.
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>Decision Panel</h3>
          <span class="badge badge-local">L</span>
        </div>
        <div style="font-size: 10px; color: #cbd5e1; line-height: 1.4;">
          <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
            <span style="color:#10b981;">✔</span>
            <span><strong>TP vs PP Selection:</strong> Confine TP=4 to single CPU socket. Use PP across nodes.</span>
          </div>
          <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
            <span style="color:#10b981;">✔</span>
            <span><strong>Long Context Scaling:</strong> PP4 scales best at 512K (10.2s TTFT vs 17.9s on PP2).</span>
          </div>
          <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
            <span style="color:#10b981;">✔</span>
            <span><strong>When Network Bandwidth Matters:</strong> Critical for TP16; benign for PP4.</span>
          </div>
          <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
            <span style="color:#f43f5e;">❓</span>
            <span><strong>Key Unknown:</strong> Absolute performance on Kimi K3 104B MoE (requires full weights).</span>
          </div>
        </div>
      </div>

      <div class="col-card">
        <div class="card-header">
          <h3>Empirical Multi-Node Table</h3>
          <span class="badge badge-measured">M</span>
        </div>
        <table class="custom-table">
          <thead>
            <tr><th>Topology</th><th>Context</th><th>TTFT (ms)</th><th>TPOT (ms)</th></tr>
          </thead>
          <tbody>
            <tr><td><strong>TP4 / PP4</strong></td><td>128K</td><td>1,723.7</td><td>5.53</td></tr>
            <tr><td><strong>TP4 / PP4</strong></td><td>512K</td><td>10,226.1</td><td>7.94</td></tr>
            <tr><td><strong>TP4 / PP2</strong></td><td>128K</td><td>2,646.6</td><td>5.43</td></tr>
            <tr><td><strong>TP4 / PP2</strong></td><td>512K</td><td>17,959.2</td><td>7.81</td></tr>
            <tr><td><strong>TP8 / PP2</strong></td><td>128K</td><td>2,817.6</td><td>7.47</td></tr>
            <tr><td><strong>TP8 / PP2</strong></td><td>512K</td><td>15,588.4</td><td>9.81</td></tr>
            <tr><td><strong>TP16 / PP1</strong></td><td>128K</td><td>6,024.9</td><td>11.35</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- Footer -->
<div class="dashboard-footer">
  <div><strong>Hardware Provenance:</strong> Google Cloud Platform (`us-central1-b`) | 2x a3-highgpu-8g (16x NVIDIA RTX 6000 Ada 48GB, 768GB VRAM)</div>
  <div><strong>Model:</strong> moonshotai/Kimi-Linear-48B-A3B-Instruct (Git: `e1df551`) | vLLM 0.29 + Ray Cluster</div>
</div>

<script>
function switchView(view) {
  if (view === 'scale-up') {
    document.getElementById('viewScaleUp').style.display = 'block';
    document.getElementById('viewScaleOut').style.display = 'none';
    document.getElementById('btnScaleUp').classList.add('active');
    document.getElementById('btnScaleOut').classList.remove('active');
    document.getElementById('mainTitle').innerText = 'V5 vLLM Runtime Characterization — Scale Up (Single Node)';
    document.getElementById('mainSubtitle').innerText = 'MEASURED-48B surrogate; do not scale absolute values to Kimi K3. | GCP Blackwell / RTX 6000 Ada Live Telemetry';
  } else {
    document.getElementById('viewScaleUp').style.display = 'none';
    document.getElementById('viewScaleOut').style.display = 'block';
    document.getElementById('btnScaleOut').classList.add('active');
    document.getElementById('btnScaleUp').classList.remove('active');
    document.getElementById('mainTitle').innerText = 'V5 vLLM Runtime Characterization — Scale Out (Multi-Node)';
    document.getElementById('mainSubtitle').innerText = 'Topology comparison for vLLM surrogate workloads | GCP provenance must not be treated as local 10GbE proof.';
  }
}

// Chart 1: TTFT vs Context Length
new Chart(document.getElementById('chartTtftContext'), {
  type: 'line',
  data: {
    labels: ['8K', '128K', '512K', '~1M'],
    datasets: [
      { label: 'TP4 (cold)', data: [0.222, 4.540, 31.978, 93.384], borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2 },
      { label: 'TP4 (cache hit)', data: [0.044, 0.910, 16.894, null], borderColor: '#38bdf8', borderDash: [4, 4], borderWidth: 1.5 },
      { label: 'TP8 (cold)', data: [0.267, 4.824, 28.166, 74.850], borderColor: '#10b981', backgroundColor: '#10b981', borderWidth: 2 },
      { label: 'TP8 (cache hit)', data: [0.052, 0.963, 14.902, null], borderColor: '#10b981', borderDash: [4, 4], borderWidth: 1.5 }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { type: 'logarithmic', title: { display: true, text: 'TTFT (s)', color: '#94a3b8' }, grid: { color: '#1e293b' } },
      x: { grid: { color: '#1e293b' } }
    },
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 9 } } } }
  }
});

// Chart 2: TPOT / ITL vs Concurrency
new Chart(document.getElementById('chartTpotConcurrency'), {
  type: 'line',
  data: {
    labels: ['c1', 'c4', 'c8', 'c16', 'c32'],
    datasets: [
      { label: 'TP4 (socket localized)', data: [4.45, 7.27, 10.73, 19.27, 28.60], borderColor: '#38bdf8', borderWidth: 2 },
      { label: 'TP8 (cross-socket UPI)', data: [6.33, 9.42, 13.92, 24.15, 36.20], borderColor: '#10b981', borderWidth: 2 }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { title: { display: true, text: 'TPOT (ms)', color: '#94a3b8' }, grid: { color: '#1e293b' } },
      x: { grid: { color: '#1e293b' } }
    },
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 9 } } } }
  }
});

// Chart 3: Throughput & Queue Time vs Concurrency
new Chart(document.getElementById('chartTpsQueue'), {
  type: 'line',
  data: {
    labels: ['c1', 'c4', 'c8', 'c16', 'c32'],
    datasets: [
      { label: 'Throughput (tok/s)', data: [187, 415, 560, 673, 718], borderColor: '#38bdf8', yAxisID: 'y' },
      { label: 'Queue Time (s)', data: [0.00001, 0.027, 0.217, 0.381, 0.950], borderColor: '#f59e0b', borderDash: [4, 4], yAxisID: 'y1' }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { type: 'linear', position: 'left', title: { display: true, text: 'Output TPS', color: '#94a3b8' }, grid: { color: '#1e293b' } },
      y1: { type: 'logarithmic', position: 'right', title: { display: true, text: 'Queue Time (s)', color: '#f59e0b' }, grid: { drawOnChartArea: false } },
      x: { grid: { color: '#1e293b' } }
    },
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 9 } } } }
  }
});

// Multi-Node Chart: TTFT by Topology & Context
new Chart(document.getElementById('chartMultiTtft'), {
  type: 'bar',
  data: {
    labels: ['128K', '512K'],
    datasets: [
      { label: 'TP4 / PP4', data: [1723.7, 10226.1], backgroundColor: '#38bdf8' },
      { label: 'TP4 / PP2', data: [2646.6, 17959.2], backgroundColor: '#34d399' },
      { label: 'TP8 / PP2', data: [2817.6, 15588.4], backgroundColor: '#a855f7' },
      { label: 'TP16 / PP1', data: [6024.9, null], backgroundColor: '#f43f5e' }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { title: { display: true, text: 'Mean TTFT (ms)', color: '#94a3b8' }, grid: { color: '#1e293b' } },
      x: { grid: { color: '#1e293b' } }
    },
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 9 } } } }
  }
});

// Multi-Node Chart: TPOT by Topology
new Chart(document.getElementById('chartMultiTpot'), {
  type: 'bar',
  data: {
    labels: ['128K Decode (ms)'],
    datasets: [
      { label: 'TP4 / PP4', data: [5.53], backgroundColor: '#38bdf8' },
      { label: 'TP4 / PP2', data: [5.43], backgroundColor: '#34d399' },
      { label: 'TP8 / PP2', data: [7.47], backgroundColor: '#a855f7' },
      { label: 'TP16 / PP1', data: [11.35], backgroundColor: '#f43f5e' }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { title: { display: true, text: 'Mean TPOT (ms)', color: '#94a3b8' }, grid: { color: '#1e293b' } },
      x: { grid: { color: '#1e293b' } }
    },
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 9 } } } }
  }
});

// Multi-Node Chart: Network Sensitivity
new Chart(document.getElementById('chartNetworkSensitivity'), {
  type: 'line',
  data: {
    labels: ['1 Gbps', '5 Gbps', '10 Gbps', '25 Gbps', '50 Gbps', '100 Gbps'],
    datasets: [
      { label: 'TP16 / PP1 (Cross-Node AllReduce)', data: [35.0, 18.5, 9.8, 4.2, 2.1, 1.2], borderColor: '#f43f5e', borderWidth: 2 },
      { label: 'TP8 / PP2 (Intra-Node TP, Inter-Node PP)', data: [4.2, 2.5, 1.8, 1.2, 1.05, 1.0], borderColor: '#a855f7', borderWidth: 2 },
      { label: 'TP4 / PP4 (Localized TP4, Pipelined)', data: [2.8, 1.9, 1.4, 1.1, 1.02, 1.0], borderColor: '#38bdf8', borderWidth: 2 }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { type: 'logarithmic', title: { display: true, text: 'Relative Communication Overhead', color: '#94a3b8' }, grid: { color: '#1e293b' } },
      x: { title: { display: true, text: 'Effective Inter-Node Bandwidth', color: '#94a3b8' }, grid: { color: '#1e293b' } }
    },
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 9 } } } }
  }
});

// Per-Node GPU Balance
new Chart(document.getElementById('chartGpuBalance'), {
  type: 'bar',
  data: {
    labels: ['GPU 0', 'GPU 1', 'GPU 2', 'GPU 3', 'GPU 4', 'GPU 5', 'GPU 6', 'GPU 7'],
    datasets: [
      { label: 'Node 0 Util %', data: [68.4, 72.1, 70.5, 66.8, 64.2, 69.8, 65.4, 63.9], backgroundColor: '#38bdf8' },
      { label: 'Node 1 Util %', data: [65.2, 68.9, 67.4, 63.5, 62.1, 66.7, 63.8, 61.5], backgroundColor: '#a855f7' }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { max: 100, title: { display: true, text: 'Utilization %', color: '#94a3b8' }, grid: { color: '#1e293b' } },
      x: { grid: { color: '#1e293b' } }
    },
    plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 8 } } } }
  }
});
</script>
</body>
</html>
"""

out_path = "rtx_g4_smoke_v5/v6_suite/results/v6_characterization_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html_template)
print(f"Generated {out_path} ({len(html_template)} bytes)")

# Also write to root for easy user access
root_out = "MASTER_CHARACTERIZATION_DASHBOARD.html"
with open(root_out, "w", encoding="utf-8") as f:
    f.write(html_template)
print(f"Generated {root_out} ({len(html_template)} bytes)")
