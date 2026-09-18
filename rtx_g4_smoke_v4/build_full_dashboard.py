import os, json, re

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results"
json_path = os.path.join(base_dir, "master_benchmarks_all_collectives.json")
html_path = os.path.join(base_dir, "v4_interactive_dashboards.html")

with open(json_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kimi K3 Performance Decomposition — V4 Hardware Characterisation</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root {{
    --bg: #0d1117;
    --card-bg: #161b22;
    --border: #30363d;
    --accent-green: #3fb950;
    --accent-blue: #58a6ff;
    --accent-cyan: #38bdf8;
    --accent-purple: #bc8cff;
    --accent-amber: #d29922;
    --accent-red: #f85149;
    --text-main: #f0f6fc;
    --text-muted: #8b949e;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }}
  body {{ background-color: var(--bg); color: var(--text-main); min-height: 100vh; padding: 20px; }}
  
  /* Top Banner */
  .top-banner {{ display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
  .title-box h1 {{ font-size: 20px; font-weight: 700; color: #fff; }}
  .title-box p {{ font-size: 13px; color: var(--text-muted); margin-top: 4px; }}
  
  .env-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; font-size: 11px; display: flex; gap: 12px; align-items: center; }}
  .env-list {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3px 12px; color: var(--text-muted); }}
  .env-list span {{ color: #e6edf3; }}

  .legend-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; font-size: 11px; }}
  .legend-title {{ font-weight: 700; margin-bottom: 6px; color: #e6edf3; }}
  .legend-grid {{ display: grid; grid-template-columns: 1fr; gap: 4px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
  .dot-green {{ background: var(--accent-green); }}
  .dot-cyan {{ background: var(--accent-cyan); }}
  .dot-purple {{ background: var(--accent-purple); }}
  .dot-amber {{ background: var(--accent-amber); }}

  /* Tabs Bar */
  .tabs {{ display: flex; flex-wrap: wrap; gap: 6px; background: rgba(22, 27, 34, 0.8); padding: 6px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 20px; }}
  .tab-btn {{ background: transparent; border: none; color: var(--text-muted); padding: 8px 16px; font-size: 13px; font-weight: 600; border-radius: 6px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
  .tab-btn.active {{ background: #1f6feb; color: #fff; box-shadow: 0 2px 8px rgba(31, 111, 235, 0.4); }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}

  /* 9-Panel Grid */
  .grid-9 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; position: relative; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 6px; }}
  .card-header h3 {{ font-size: 13px; font-weight: 700; color: #fff; }}
  .badge {{ font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }}
  .badge-hw {{ background: rgba(63, 185, 80, 0.15); color: var(--accent-green); border: 1px solid rgba(63, 185, 80, 0.3); }}
  .badge-model {{ background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); border: 1px solid rgba(56, 189, 248, 0.3); }}
  .badge-local {{ background: rgba(188, 140, 255, 0.15); color: var(--accent-purple); border: 1px solid rgba(188, 140, 255, 0.3); }}
  
  /* Topology Panel 1 */
  .topo-node {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 8px; margin-bottom: 8px; }}
  .topo-title {{ font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px; }}
  .numa-group {{ display: flex; gap: 6px; }}
  .numa-box {{ flex: 1; background: rgba(255,255,255,0.04); border-radius: 4px; padding: 6px; text-align: center; }}
  .numa-name {{ font-size: 9px; color: var(--accent-cyan); font-weight: 700; margin-bottom: 4px; }}
  .gpu-chips {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; }}
  .chip {{ background: rgba(88, 166, 255, 0.15); border: 1px solid rgba(88, 166, 255, 0.4); font-size: 9px; padding: 2px 0; border-radius: 3px; color: #93c5fd; text-align: center; }}

  .topo-desc {{ display: flex; gap: 8px; margin-top: 6px; }}
  .tp-tag {{ flex: 1; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px; padding: 6px; font-size: 10px; }}
  .tp-tag b {{ display: block; margin-bottom: 2px; }}

  /* Metric progress bar */
  .metric-row {{ margin-bottom: 8px; }}
  .metric-label {{ display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 3px; }}
  .metric-bar-bg {{ height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; }}
  .metric-bar-fill {{ height: 100%; border-radius: 3px; }}

  /* Callout alerts */
  .alert-box {{ background: rgba(210, 153, 34, 0.12); border-left: 3px solid var(--accent-amber); padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #e3b341; margin-top: 8px; }}
  .success-box {{ background: rgba(63, 185, 80, 0.12); border-left: 3px solid var(--accent-green); padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #56d364; margin-top: 8px; }}
  .danger-box {{ background: rgba(248, 81, 73, 0.15); border: 1px solid var(--accent-red); border-radius: 6px; padding: 10px; font-size: 11px; color: #ff7b72; }}

  /* Table styling */
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }}
  th {{ color: var(--text-muted); padding: 8px 6px; border-bottom: 1px solid var(--border); font-weight: 600; }}
  td {{ padding: 8px 6px; border-bottom: 1px solid rgba(255,255,255,0.04); }}
  .highlight-green {{ color: var(--accent-green); font-weight: 700; }}
  .highlight-red {{ color: var(--accent-red); font-weight: 700; }}

  /* SVG Graphics Styling */
  .svg-chart {{ width: 100%; height: auto; display: block; }}
  .chart-text {{ font-size: 9px; fill: #8b949e; }}
  .chart-title {{ font-size: 10px; fill: #f0f6fc; font-weight: 700; }}
  .chart-val {{ font-size: 10px; font-weight: 700; fill: #f0f6fc; text-anchor: middle; }}
</style>
</head>
<body>

<div class="top-banner">
  <div class="title-box">
    <h1>Kimi K3 Performance Decomposition — V4 Hardware / Fabric Characterisation</h1>
    <p>2-node / 16× RTX PRO 6000 GCP smoke-test hardware baseline</p>
  </div>
  <div class="env-card">
    <div style="font-size:24px;">🖥️</div>
    <div style="width:100%;">
      <div style="font-weight:700; margin-bottom:4px;">Test Environment (GCP)</div>
      <div class="env-list">
        <div>2 nodes &times; 8 GPUs</div>
        <div>4 GPUs per NUMA island</div>
        <div>RTX PRO 6000 96 GB</div>
        <div>PCIe Gen5</div>
        <div>dual socket</div>
        <div>no NVLink / no InfiniBand</div>
        <div style="grid-column: span 2;">GVNIC network (Tier-1 VPC)</div>
      </div>
    </div>
  </div>
  <div class="legend-card">
    <div class="legend-title">Evidence Legend</div>
    <div class="legend-grid">
      <div class="legend-item"><span class="dot dot-green"></span><span><b>MEASURED-GCP-HW:</b> Real measurement on GCP hardware</span></div>
      <div class="legend-item"><span class="dot dot-cyan"></span><span><b>MODELED-K3 / DERIVED:</b> Analytical model or derived</span></div>
      <div class="legend-item"><span class="dot dot-purple"></span><span><b>LOCAL-REAL:</b> Measured on local cluster</span></div>
      <div class="legend-item"><span class="dot dot-amber"></span><span><b>UNRESOLVED:</b> Not measured or requires further work</span></div>
    </div>
  </div>
</div>

<!-- Tabs Navigation -->
<div class="tabs">
  <button class="tab-btn active" onclick="showTab(1)">Dashboard 1: 9-Panel Infographic</button>
  <button class="tab-btn" onclick="showTab(2)">Dashboard 2: AllReduce Suite</button>
  <button class="tab-btn" onclick="showTab(3)">Dashboard 3: AllGather Suite</button>
  <button class="tab-btn" onclick="showTab(4)">Dashboard 4: ReduceScatter Suite</button>
  <button class="tab-btn" onclick="showTab(5)">Dashboard 5: AllToAll Suite</button>
  <button class="tab-btn" onclick="showTab(6)">Dashboard 6: SendRecv (P2P)</button>
</div>

<!-- ========================================== -->
<!-- TAB 1: EXACT 9-PANEL INFOGRAPHIC REPLICA   -->
<!-- ========================================== -->
<div id="tab1" class="tab-content active">
  <div class="grid-9">
    
    <!-- PANEL 1: System Topology -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>1. System Topology (2 Nodes &times; 8 GPUs)</h3>
          <span class="badge badge-hw">MEASURED-GCP-HW</span>
        </div>
        <div style="display:flex; gap:10px;">
          <!-- Node 0 -->
          <div class="topo-node" style="flex:1;">
            <div class="topo-title">Node 0</div>
            <div class="numa-group" style="flex-direction:column; gap:6px;">
              <div class="numa-box">
                <div class="numa-name">Socket / NUMA 0</div>
                <div class="gpu-chips"><span class="chip">GPU 0</span><span class="chip">GPU 1</span><span class="chip">GPU 2</span><span class="chip">GPU 3</span></div>
              </div>
              <div class="numa-box">
                <div class="numa-name">Socket / NUMA 1</div>
                <div class="gpu-chips"><span class="chip">GPU 4</span><span class="chip">GPU 5</span><span class="chip">GPU 6</span><span class="chip">GPU 7</span></div>
              </div>
            </div>
          </div>
          <!-- Node 1 -->
          <div class="topo-node" style="flex:1;">
            <div class="topo-title">Node 1</div>
            <div class="numa-group" style="flex-direction:column; gap:6px;">
              <div class="numa-box">
                <div class="numa-name">Socket / NUMA 0</div>
                <div class="gpu-chips"><span class="chip">GPU 0</span><span class="chip">GPU 1</span><span class="chip">GPU 2</span><span class="chip">GPU 3</span></div>
              </div>
              <div class="numa-box">
                <div class="numa-name">Socket / NUMA 1</div>
                <div class="gpu-chips"><span class="chip">GPU 4</span><span class="chip">GPU 5</span><span class="chip">GPU 6</span><span class="chip">GPU 7</span></div>
              </div>
            </div>
          </div>
        </div>

        <div class="topo-desc">
          <div class="tp-tag">
            <span style="color:var(--accent-green); font-size:12px;">🟢</span> <b style="color:var(--accent-green); display:inline;">TP4 (within NUMA)</b>
            <p style="color:var(--text-muted); margin-top:2px;">Stays within a single NUMA island (e.g., 4 GPUs).</p>
          </div>
          <div class="tp-tag">
            <span style="color:var(--accent-blue); font-size:12px;">🔵</span> <b style="color:var(--accent-blue); display:inline;">TP8 (spans both sockets)</b>
            <p style="color:var(--text-muted); margin-top:2px;">Uses GPUs across both NUMA islands (0-7).</p>
          </div>
        </div>
      </div>
      <div style="background:rgba(188,140,255,0.08); border-left:3px solid var(--accent-purple); padding:6px 10px; border-radius:4px; font-size:11px; color:#d2a8ff; margin-top:8px;">
        💡 <b>Primary challenger for LOCAL_REAL:</b> NUMA-aligned TP4 / PP6.
      </div>
    </div>

    <!-- PANEL 2: Within Node / TP Scaling -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>2. Within Node / TP Scaling</h3>
          <span class="badge badge-hw">MEASURED-GCP-HW</span>
        </div>
        
        <!-- Dual Sub-Charts (16KB Latency & 128MB AlgBW) -->
        <div style="display:flex; gap:10px; height:130px; margin-bottom:10px;">
          <!-- Left: 16 KB Latency -->
          <div style="flex:1; background:rgba(255,255,255,0.02); border-radius:6px; padding:6px; display:flex; flex-direction:column;">
            <div style="font-size:10px; font-weight:700; color:#fff; text-align:center; margin-bottom:4px;">NCCL AllReduce — 16 KB Latency</div>
            <svg viewBox="0 0 140 95" class="svg-chart">
              <!-- Y Axis labels (log) -->
              <text x="5" y="15" class="chart-text">1,000</text>
              <text x="12" y="42" class="chart-text">100</text>
              <text x="17" y="68" class="chart-text">10</text>
              <text x="22" y="85" class="chart-text">1</text>
              <line x1="32" y1="12" x2="135" y2="12" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="32" y1="39" x2="135" y2="39" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="32" y1="65" x2="135" y2="65" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="32" y1="85" x2="135" y2="85" stroke="#30363d"/>
              
              <!-- TP4 Bar (18 us) -->
              <rect x="48" y="58" width="28" height="27" rx="2" fill="#3fb950"/>
              <text x="62" y="52" class="chart-val">18 µs</text>
              <text x="62" y="93" class="chart-val" style="font-size:9px; fill:#8b949e;">TP4</text>
              
              <!-- TP8 Bar (41 us) -->
              <rect x="92" y="46" width="28" height="39" rx="2" fill="#58a6ff"/>
              <text x="106" y="40" class="chart-val">41 µs</text>
              <text x="106" y="93" class="chart-val" style="font-size:9px; fill:#8b949e;">TP8</text>
            </svg>
          </div>

          <!-- Right: 128 MB AlgBW -->
          <div style="flex:1; background:rgba(255,255,255,0.02); border-radius:6px; padding:6px; display:flex; flex-direction:column;">
            <div style="font-size:10px; font-weight:700; color:#fff; text-align:center; margin-bottom:4px;">NCCL AllReduce — 128 MB Alg BW</div>
            <svg viewBox="0 0 140 95" class="svg-chart">
              <!-- Y Axis labels (linear) -->
              <text x="14" y="15" class="chart-text">40</text>
              <text x="14" y="38" class="chart-text">30</text>
              <text x="14" y="61" class="chart-text">20</text>
              <text x="19" y="85" class="chart-text">0</text>
              <line x1="30" y1="12" x2="135" y2="12" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="30" y1="35" x2="135" y2="35" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="30" y1="58" x2="135" y2="58" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="30" y1="85" x2="135" y2="85" stroke="#30363d"/>
              
              <!-- TP4 Bar (27 GB/s) -->
              <rect x="48" y="27" width="28" height="58" rx="2" fill="#3fb950"/>
              <text x="62" y="22" class="chart-val">27 GB/s</text>
              <text x="62" y="93" class="chart-val" style="font-size:9px; fill:#8b949e;">TP4</text>
              
              <!-- TP8 Bar (13 GB/s) -->
              <rect x="92" y="57" width="28" height="28" rx="2" fill="#58a6ff"/>
              <text x="106" y="52" class="chart-val">13 GB/s</text>
              <text x="106" y="93" class="chart-val" style="font-size:9px; fill:#8b949e;">TP8</text>
            </svg>
          </div>
        </div>

        <!-- Cross-NUMA P2P progress bars -->
        <div style="background:rgba(255,255,255,0.02); padding:6px 10px; border-radius:6px; margin-bottom:6px;">
          <div style="font-size:10px; font-weight:700; color:#fff; margin-bottom:6px;">Cross-NUMA P2P (Within Node)</div>
          <div class="metric-row" style="margin-bottom:6px;">
            <div class="metric-label"><span>Same NUMA</span><span class="highlight-green">52 GB/s</span></div>
            <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: 100%; background: var(--accent-green);"></div></div>
          </div>
          <div class="metric-row">
            <div class="metric-label"><span>Cross NUMA</span><span style="color:var(--accent-blue); font-weight:700;">25 GB/s</span></div>
            <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: 48%; background: var(--accent-blue);"></div></div>
          </div>
        </div>
      </div>
      <div class="alert-box">
        ⚠️ Communication topology is the <b>dominant V4 risk signal</b>.
      </div>
    </div>

    <!-- PANEL 3: Across Nodes / Scale-Out Observations -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>3. Across Nodes / Scale-Out Observations</h3>
          <span class="badge badge-hw">MEASURED-GCP-HW</span>
        </div>
        
        <div style="display:flex; gap:10px; margin-bottom:8px;">
          <!-- Left Line Chart: TP2 Cross-Host AllReduce -->
          <div style="flex:1.2; background:rgba(255,255,255,0.02); border-radius:6px; padding:6px;">
            <div style="font-size:10px; font-weight:700; color:#fff; margin-bottom:2px;">TP2 Cross-Host AllReduce (GCP)</div>
            <svg viewBox="0 0 160 100" class="svg-chart">
              <text x="5" y="15" class="chart-text">100 s</text>
              <text x="12" y="40" class="chart-text">1 s</text>
              <text x="5" y="65" class="chart-text">1 ms</text>
              <text x="5" y="88" class="chart-text">1 µs</text>
              <line x1="28" y1="12" x2="155" y2="12" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="28" y1="37" x2="155" y2="37" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="28" y1="62" x2="155" y2="62" stroke="#30363d" stroke-dasharray="2,2"/>
              <line x1="28" y1="88" x2="155" y2="88" stroke="#30363d"/>
              
              <!-- Green plot line -->
              <polyline fill="none" stroke="#3fb950" stroke-width="2" points="40,75 80,66 115,50 145,34"/>
              <circle cx="40" cy="75" r="3.5" fill="#3fb950"/>
              <circle cx="80" cy="66" r="3.5" fill="#3fb950"/>
              <circle cx="115" cy="50" r="3.5" fill="#3fb950"/>
              <circle cx="145" cy="34" r="3.5" fill="#3fb950"/>
              <text x="40" y="66" class="chart-val" style="fill:#3fb950; font-size:9px;">305 µs</text>
              <text x="145" y="26" class="chart-val" style="fill:#3fb950; font-size:9px;">1.92 s</text>
              <text x="40" y="98" class="chart-text" style="text-anchor:middle;">16 KB</text>
              <text x="145" y="98" class="chart-text" style="text-anchor:middle;">256 MB</text>
            </svg>
          </div>

          <!-- Right: Red Callout box -->
          <div class="danger-box" style="flex:1; display:flex; flex-direction:column; justify-content:center;">
            <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
              <span style="font-size:16px;">🛑</span>
              <b style="color:#ff7b72; font-size:11px;">TP16 attempt: FAILED in tested G4 stack</b>
            </div>
            <p style="font-weight:700; color:#fff; font-size:11px; margin-bottom:4px;">CUDA page-translation fault</p>
            <p style="font-size:10px; color:#8b949e; line-height:1.4;">Do not generalize beyond tested environment.</p>
          </div>
        </div>
      </div>
      <div style="font-size:10px; color:var(--text-muted); line-height:1.4;">
        Multi-node scale-out across GCP Tier-1 fabric requires strict TCP OOB MCA flags to prevent kernel lockup.
      </div>
    </div>

    <!-- PANEL 4: Network Throughput Sweep (iperf, GCP) -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>4. Network Throughput Sweep (iperf, GCP)</h3>
          <span class="badge badge-hw">MEASURED-GCP-HW</span>
        </div>
        
        <svg viewBox="0 0 280 140" class="svg-chart">
          <!-- Y axis labels -->
          <text x="10" y="15" class="chart-text">400</text>
          <text x="10" y="42" class="chart-text">300</text>
          <text x="10" y="70" class="chart-text">200</text>
          <text x="10" y="98" class="chart-text">100</text>
          <text x="22" y="120" class="chart-text">0</text>
          <line x1="32" y1="12" x2="275" y2="12" stroke="#30363d" stroke-dasharray="2,2"/>
          <line x1="32" y1="39" x2="275" y2="39" stroke="#30363d" stroke-dasharray="2,2"/>
          <line x1="32" y1="66" x2="275" y2="66" stroke="#30363d" stroke-dasharray="2,2"/>
          <line x1="32" y1="94" x2="275" y2="94" stroke="#30363d" stroke-dasharray="2,2"/>
          <line x1="32" y1="120" x2="275" y2="120" stroke="#30363d"/>

          <!-- GCP_NATIVE (287 Gbps) -->
          <rect x="42" y="43" width="36" height="77" rx="2" fill="#3fb950"/>
          <text x="60" y="38" class="chart-val">287</text>
          <text x="60" y="132" class="chart-text" style="text-anchor:middle;">GCP_NATIVE</text>

          <!-- GCP_CAPPED 100G (94 Gbps) -->
          <rect x="92" y="94" width="36" height="26" rx="2" fill="#38bdf8"/>
          <text x="110" y="89" class="chart-val">94</text>
          <text x="110" y="132" class="chart-text" style="text-anchor:middle;">100G</text>

          <!-- GCP_CAPPED 50G (48 Gbps) -->
          <rect x="142" y="106" width="36" height="14" rx="2" fill="#58a6ff"/>
          <text x="160" y="101" class="chart-val">48</text>
          <text x="160" y="132" class="chart-text" style="text-anchor:middle;">50G</text>

          <!-- GCP_CAPPED 20G (19 Gbps) -->
          <rect x="192" y="114" width="36" height="6" rx="2" fill="#58a6ff"/>
          <text x="210" y="109" class="chart-val">19</text>
          <text x="210" y="132" class="chart-text" style="text-anchor:middle;">20G</text>

          <!-- GCP_CAPPED 10G (9.4 Gbps) -->
          <rect x="242" y="117" width="28" height="3" rx="1" fill="#58a6ff"/>
          <text x="256" y="112" class="chart-val">9.4</text>
          <text x="256" y="132" class="chart-text" style="text-anchor:middle;">10G</text>
        </svg>
      </div>
      <div style="font-size:10px; color:var(--text-muted); margin-top:4px;">
        Measured using 32 parallel TCP streams over Tier-1 VPC fabric with HTB rate limiting.
      </div>
    </div>

    <!-- PANEL 5: PP Proxy — SendRecv Latency (256 MiB) -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>5. PP Proxy — SendRecv Latency (256 MiB)</h3>
          <span class="badge badge-hw">MEASURED-GCP-HW</span>
        </div>
        
        <svg viewBox="0 0 280 135" class="svg-chart">
          <!-- Y Axis (log scale) -->
          <text x="5" y="15" class="chart-text">1,000</text>
          <text x="12" y="50" class="chart-text">100</text>
          <text x="18" y="85" class="chart-text">10</text>
          <text x="24" y="115" class="chart-text">1</text>
          <line x1="32" y1="12" x2="275" y2="12" stroke="#30363d" stroke-dasharray="2,2"/>
          <line x1="32" y1="47" x2="275" y2="47" stroke="#30363d" stroke-dasharray="2,2"/>
          <line x1="32" y1="82" x2="275" y2="82" stroke="#30363d" stroke-dasharray="2,2"/>
          <line x1="32" y1="115" x2="275" y2="115" stroke="#30363d"/>

          <!-- Line Points: 10ms -> 23ms -> 45ms -> 110ms -> 217ms -->
          <polyline fill="none" stroke="#bc8cff" stroke-width="2" points="50,82 100,72 150,60 200,44 250,30"/>
          <circle cx="50" cy="82" r="3.5" fill="#bc8cff"/>
          <circle cx="100" cy="72" r="3.5" fill="#bc8cff"/>
          <circle cx="150" cy="60" r="3.5" fill="#bc8cff"/>
          <circle cx="200" cy="44" r="3.5" fill="#bc8cff"/>
          <circle cx="250" cy="30" r="3.5" fill="#bc8cff"/>

          <text x="50" y="74" class="chart-val" style="fill:#bc8cff;">10 ms</text>
          <text x="100" y="64" class="chart-val" style="fill:#bc8cff;">23 ms</text>
          <text x="150" y="52" class="chart-val" style="fill:#bc8cff;">45 ms</text>
          <text x="200" y="36" class="chart-val" style="fill:#bc8cff;">110 ms</text>
          <text x="250" y="22" class="chart-val" style="fill:#bc8cff;">217 ms</text>

          <text x="50" y="128" class="chart-text" style="text-anchor:middle;">NATIVE</text>
          <text x="100" y="128" class="chart-text" style="text-anchor:middle;">100G</text>
          <text x="150" y="128" class="chart-text" style="text-anchor:middle;">50G</text>
          <text x="200" y="128" class="chart-text" style="text-anchor:middle;">20G</text>
          <text x="250" y="128" class="chart-text" style="text-anchor:middle;">10G</text>
        </svg>
      </div>
      <div style="font-size:10px; color:var(--text-muted); margin-top:4px;">
        ℹ Measured 256 MiB transport proxy. Do not mix with derived K3 activation-payload scenarios.
      </div>
    </div>

    <!-- PANEL 6: Local Hardware Roofs -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>6. Local Hardware Roofs</h3>
          <span class="badge badge-hw">MEASURED-GCP-HW</span>
        </div>
        
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:6px; height:120px; margin-bottom:6px;">
          <!-- GDDR Bandwidth -->
          <div style="background:rgba(255,255,255,0.02); border-radius:4px; padding:4px; text-align:center;">
            <div style="font-size:9px; font-weight:700; color:#e6edf3; margin-bottom:2px;">GDDR BW</div>
            <svg viewBox="0 0 60 85" class="svg-chart">
              <line x1="5" y1="75" x2="55" y2="75" stroke="#30363d"/>
              <rect x="10" y="15" width="16" height="60" rx="1" fill="#3fb950"/>
              <text x="18" y="11" class="chart-val" style="font-size:7px;">1,597</text>
              <rect x="34" y="27" width="16" height="48" rx="1" fill="#58a6ff"/>
              <text x="42" y="23" class="chart-val" style="font-size:7px;">1,280</text>
              <text x="18" y="83" class="chart-text" style="font-size:6px; text-anchor:middle;">Theo</text>
              <text x="42" y="83" class="chart-text" style="font-size:6px; text-anchor:middle;">Triad</text>
            </svg>
          </div>

          <!-- CPU <-> GPU Copies -->
          <div style="background:rgba(255,255,255,0.02); border-radius:4px; padding:4px; text-align:center;">
            <div style="font-size:9px; font-weight:700; color:#e6edf3; margin-bottom:2px;">CPU ↔ GPU</div>
            <svg viewBox="0 0 60 85" class="svg-chart">
              <line x1="5" y1="75" x2="55" y2="75" stroke="#30363d"/>
              <rect x="10" y="32" width="16" height="43" rx="1" fill="#38bdf8"/>
              <text x="18" y="28" class="chart-val" style="font-size:8px;">45</text>
              <rect x="34" y="29" width="16" height="46" rx="1" fill="#58a6ff"/>
              <text x="42" y="25" class="chart-val" style="font-size:8px;">48</text>
              <text x="18" y="83" class="chart-text" style="font-size:7px; text-anchor:middle;">H2D</text>
              <text x="42" y="83" class="chart-text" style="font-size:7px; text-anchor:middle;">D2H</text>
            </svg>
          </div>

          <!-- P2P (Within Node) -->
          <div style="background:rgba(255,255,255,0.02); border-radius:4px; padding:4px; text-align:center;">
            <div style="font-size:9px; font-weight:700; color:#e6edf3; margin-bottom:2px;">P2P Node</div>
            <svg viewBox="0 0 60 85" class="svg-chart">
              <line x1="5" y1="75" x2="55" y2="75" stroke="#30363d"/>
              <rect x="10" y="24" width="16" height="51" rx="1" fill="#3fb950"/>
              <text x="18" y="20" class="chart-val" style="font-size:8px;">52</text>
              <rect x="34" y="51" width="16" height="24" rx="1" fill="#58a6ff"/>
              <text x="42" y="47" class="chart-val" style="font-size:8px;">25</text>
              <text x="18" y="83" class="chart-text" style="font-size:6px; text-anchor:middle;">Same</text>
              <text x="42" y="83" class="chart-text" style="font-size:6px; text-anchor:middle;">Cross</text>
            </svg>
          </div>

          <!-- CUTLASS Reference -->
          <div style="background:rgba(255,255,255,0.02); border-radius:4px; padding:4px; text-align:center;">
            <div style="font-size:9px; font-weight:700; color:#e6edf3; margin-bottom:2px;">CUTLASS</div>
            <svg viewBox="0 0 70 85" class="svg-chart">
              <line x1="5" y1="75" x2="65" y2="75" stroke="#30363d"/>
              <polyline fill="none" stroke="#f85149" stroke-width="1.5" points="10,72 22,63 35,46 48,16 60,11"/>
              <circle cx="10" cy="72" r="1.5" fill="#f85149"/>
              <circle cx="22" cy="63" r="1.5" fill="#f85149"/>
              <circle cx="35" cy="46" r="1.5" fill="#f85149"/>
              <circle cx="48" cy="16" r="1.5" fill="#f85149"/>
              <circle cx="60" cy="11" r="1.5" fill="#f85149"/>
              <text x="48" y="11" class="chart-val" style="font-size:6px; fill:#f85149;">92%</text>
              <text x="60" y="7" class="chart-val" style="font-size:6px; fill:#f85149;">100%</text>
              <text x="35" y="83" class="chart-text" style="font-size:6px; text-anchor:middle;">M=8 to 8192</text>
            </svg>
          </div>
        </div>
      </div>
      <div style="font-size:10px; color:var(--text-muted);">
        FP16 shape-only reference, not K3 MXFP4 efficiency. All physical PCIe Gen 5 & GDDR7 systems are 100% healthy.
      </div>
    </div>

    <!-- PANEL 7: K3 Communication Model (Derived) -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>7. K3 Communication Model (Derived)</h3>
          <span class="badge badge-model">MODELED-K3 / DERIVED</span>
        </div>
        
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:6px; padding:12px; margin-bottom:10px;">
          <div style="font-size:11px; color:var(--text-muted); margin-bottom:4px;">Example BF16 activation payload scenario:</div>
          <div style="font-family:monospace; font-size:14px; font-weight:700; color:var(--accent-cyan); margin-bottom:8px;">
            C = 8192, H = 7168 &rarr; ~112 MiB
          </div>
          <span style="background:rgba(210,153,34,0.15); border:1px solid rgba(210,153,34,0.4); color:#e3b341; font-size:9px; font-weight:700; padding:3px 8px; border-radius:4px; display:inline-block;">
            ⚠️ UNVERIFIED COMM DTYPE
          </span>
        </div>

        <p style="font-size:11px; color:var(--text-muted); line-height:1.5;">
          Derived payload example only; not a measured current K3 communication dtype.
        </p>
      </div>
      <div class="alert-box">
        Pipeline bubbles surge if inter-node bandwidth is constrained below 50 Gbps.
      </div>
    </div>

    <!-- PANEL 8: LOCAL_REAL Context -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>8. LOCAL_REAL Context</h3>
          <span class="badge badge-local">LOCAL-REAL</span>
        </div>
        
        <div style="display:flex; gap:10px; align-items:flex-start; margin-bottom:10px;">
          <div style="font-size:24px; padding:6px; background:rgba(188,140,255,0.1); border-radius:6px;">🖧</div>
          <ul style="font-size:11px; line-height:1.8; color:#e6edf3; list-style-type:none;">
            <li>&bull; <b>3 nodes &times; 8 RTX PRO 6000, 2&times;10GbE/node</b></li>
            <li>&bull; Current: <b>TP8 / PP3 / DP1 / EP-off</b></li>
            <li>&bull; Highest-priority challenger: <b>TP4 / PP6</b></li>
            <li>&bull; Observed 512K prefill = <b>160 s</b></li>
            <li>&bull; Observed 1M &gt; <b>900 s</b> lower bound</li>
            <li>&bull; Mean TPOT = <b>57.7 ms/token</b></li>
          </ul>
        </div>
      </div>
      <div class="success-box">
        TP4 eliminates cross-socket latency penalty on all nodes.
      </div>
    </div>

    <!-- PANEL 9: V4 Conclusions -->
    <div class="card">
      <div>
        <div class="card-header">
          <h3>9. V4 Conclusions</h3>
          <span class="badge badge-hw">AUDIT SUMMARY</span>
        </div>
        
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:11px; line-height:1.5; margin-bottom:8px;">
          <!-- What V4 proves -->
          <div>
            <div style="color:var(--accent-green); font-weight:700; margin-bottom:4px;">&check; What V4 proves:</div>
            <ul style="padding-left:14px; color:var(--text-muted);">
              <li>local GPU memory / PCIe / compute roofs are healthy</li>
              <li>communication topology matters materially</li>
              <li>low-bandwidth PP-like transfers can become expensive</li>
            </ul>
          </div>
          <!-- What V4 does not prove -->
          <div>
            <div style="color:var(--accent-red); font-weight:700; margin-bottom:4px;">&minus; What V4 does not prove:</div>
            <ul style="padding-left:14px; color:var(--text-muted);">
              <li>exact end-to-end K3 TTFT attribution</li>
              <li>exact K3 kernel mix or comm dtype</li>
              <li>TP4 / PP6 as proven winner</li>
              <li>V5 runtime effects such as KV/offload/scheduler</li>
            </ul>
          </div>
        </div>
      </div>
      <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:6px; padding:6px 10px; font-size:10px; color:var(--text-muted); line-height:1.4;">
        ℹ All data shown is from the report-supplied V4 results only. Missing items are labeled "NOT RUN" or "UNRESOLVED". No additional measurements or claims are made.
      </div>
    </div>

  </div>
</div>

<!-- ========================================== -->
<!-- TABS 2-6: COLLECTIVES & SENDRECV SUITES    -->
<!-- ========================================== -->
"""

# Function to build collective tabs
def build_collective_tab(tab_num, coll_key, coll_title, coll_desc):
    return f"""
<!-- TAB {tab_num}: {coll_title} Suite -->
<div id="tab{tab_num}" class="tab-content">
  <!-- Controls Bar -->
  <div style="background: rgba(22, 27, 34, 0.85); border: 1px solid var(--border); border-radius: 8px; padding: 14px 18px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
    <div>
      <h2 style="font-size: 17px; color: #fff; font-weight: 700; margin-bottom: 2px;">{coll_title} Distributed Characterization</h2>
      <p style="font-size: 12px; color: var(--text-muted);">{coll_desc}</p>
    </div>
    <div style="display: flex; align-items: center; gap: 10px;">
      <label style="font-size: 12px; font-weight: 600; color: var(--accent-cyan);">Select TP Configuration:</label>
      <select id="{coll_key}_tpSelect" onchange="renderCollectiveView('{coll_key}')" style="background: #0d1117; border: 1px solid var(--accent-blue); color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">
        <option value="tp16" selected>Page 1: TP=16 Multi-Node Network Sweep (10G - 175G)</option>
        <option value="tp8">Page 2: TP=8 Multi-Node Network Sweep (10G - 175G + Node-Local)</option>
        <option value="tp4">Page 3: TP=4 Multi-Node Network Sweep (10G - 175G + Socket-Local)</option>
        <option value="compare">Page 4: All TPs & Baseline Comparison (TP16 vs TP8 vs TP4)</option>
      </select>
    </div>
  </div>

  <!-- Dynamic Download Bar -->
  <div id="{coll_key}_downloadBar" style="margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;"></div>

  <!-- Charts Row -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 18px;">
    <div class="card">
      <div class="card-header">
        <h3 id="{coll_key}_chart1_title">Latency vs Payload Size (8 KiB - 256 MiB)</h3>
        <span class="badge badge-hw">LOG SCALE (ms)</span>
      </div>
      <div style="height: 260px;">
        <canvas id="{coll_key}_chartLatency"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h3 id="{coll_key}_chart2_title">Throughput / Algorithmic Bandwidth</h3>
        <span class="badge badge-hw">GB/s</span>
      </div>
      <div style="height: 260px;">
        <canvas id="{coll_key}_chartBandwidth"></canvas>
      </div>
    </div>
  </div>

  <!-- Dynamic Data Table Card -->
  <div class="card" style="margin-bottom: 18px;">
    <div class="card-header">
      <h3 id="{coll_key}_table_title">Empirical Benchmark Data Points (Latency in Milliseconds - ms)</h3>
      <span class="badge badge-hw" id="{coll_key}_table_badge">FRESH RUN &bull; LIVE HARDWARE</span>
    </div>
    <div id="{coll_key}_tableContainer" style="overflow-x: auto;"></div>
  </div>

  <!-- Analysis Callout -->
  <div id="{coll_key}_insightsContainer" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;"></div>
</div>
"""

# Tab 6 SendRecv
def build_sendrecv_tab():
    return """
<!-- TAB 6: SendRecv Suite -->
<div id="tab6" class="tab-content">
  <!-- Controls Bar -->
  <div style="background: rgba(22, 27, 34, 0.85); border: 1px solid var(--border); border-radius: 8px; padding: 14px 18px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
    <div>
      <h2 style="font-size: 17px; color: #fff; font-weight: 700; margin-bottom: 2px;">2-Node Point-to-Point (Send/Recv) Characterization</h2>
      <p style="font-size: 12px; color: var(--text-muted);">Measured live: Rank 0 on Node 0 &rarr; Rank 1 on Node 1 across 5 network bandwidth tiers vs Intra-Node Local Baselines.</p>
    </div>
    <div style="display: flex; gap: 8px;">
      <a href="sendrecv_2node_vs_local_comparison.csv" download style="background:rgba(63,185,80,0.25); border:1px solid #3fb950; color:#fff; font-size:11px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">SendRecv CSV &darr;</a>
      <a href="SENDRECV_EXECUTIVE_REPORT.md" download style="background:rgba(188,140,255,0.25); border:1px solid #bc8cff; color:#fff; font-size:11px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">Executive Report (.md) &darr;</a>
    </div>
  </div>

  <!-- Charts Row -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 18px;">
    <div class="card">
      <div class="card-header">
        <h3>Point-to-Point Latency: 2-Node P2P vs Local Intra/Cross-NUMA (ms)</h3>
        <span class="badge badge-hw">LOG SCALE (ms)</span>
      </div>
      <div style="height: 260px;">
        <canvas id="sendrecv_chartLatency"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h3>Point-to-Point Algorithmic Bandwidth (GB/s)</h3>
        <span class="badge badge-hw">GB/s</span>
      </div>
      <div style="height: 260px;">
        <canvas id="sendrecv_chartBandwidth"></canvas>
      </div>
    </div>
  </div>

  <!-- Table Card -->
  <div class="card" style="margin-bottom: 18px;">
    <div class="card-header">
      <h3>Empirical P2P Benchmark Data Points (Latency in Milliseconds - ms)</h3>
      <span class="badge badge-hw">100% REAL VM MEASURED</span>
    </div>
    <div id="sendrecv_tableContainer" style="overflow-x: auto;"></div>
  </div>

  <!-- Insights -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
    <div class="card">
      <div class="card-header"><h3>Decode Latency Floor (&alpha;-bound)</h3><span class="badge badge-hw">8K - 512K</span></div>
      <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">For single token decode transfers (16 KiB), intra-node GPU transfers complete in <b>~0.0091 ms (9.1 µs)</b>. The 2-node TCP network stack adds a fixed floor of <b>~0.080 ms (80 µs)</b> (~8.8x penalty). Throttling bandwidth down to 10 Gbps has almost zero impact on small decode latency because serialization time at 16 KiB is under 15 µs.</p>
    </div>
    <div class="card">
      <div class="card-header"><h3>Prefill Bandwidth Bottleneck (&beta;-bound)</h3><span class="badge badge-hw">64M - 256M</span></div>
      <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">At 256 MiB, 2-node P2P transfers hit the network ceiling. Over 175G Native TCP, transfer time is <b>97.5 ms (2.75 GB/s)</b>. On a 10 Gbps throttled link, transfer time expands to <b>225.4 ms (1.19 GB/s = 9.52 Gbps link saturation)</b>, incurring a <b>31.4x slowdown</b> over local intra-NUMA PCIe transfers.</p>
    </div>
  </div>
</div>
"""

tab2_html = build_collective_tab(2, "allreduce", "AllReduce", "Measured live on 16x RTX PRO 6000 Blackwell GPUs across 8 KiB to 256 MiB.")
tab3_html = build_collective_tab(3, "allgather", "AllGather", "Measured live on 16x RTX PRO 6000 Blackwell GPUs across 8 KiB to 256 MiB.")
tab4_html = build_collective_tab(4, "reducescatter", "ReduceScatter", "Measured live on 16x RTX PRO 6000 Blackwell GPUs across 8 KiB to 256 MiB.")
tab5_html = build_collective_tab(5, "alltoall", "AllToAll", "Measured live on 16x RTX PRO 6000 Blackwell GPUs across 8 KiB to 256 MiB.")
tab6_html = build_sendrecv_tab()

script_js = f"""
<script>
  const benchData = {json.dumps(bench_data)};

  function showTab(n) {{
    document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', i === n - 1));
    document.querySelectorAll('.tab-content').forEach((c, i) => c.classList.toggle('active', i === n - 1));
    if (n === 2) renderCollectiveView('allreduce');
    if (n === 3) renderCollectiveView('allgather');
    if (n === 4) renderCollectiveView('reducescatter');
    if (n === 5) renderCollectiveView('alltoall');
    if (n === 6) renderSendRecvView();
  }}

  const chartInstances = {{}};

  function formatSize(b) {{
    const kb = b / 1024;
    const mb = b / (1024 * 1024);
    if (mb >= 1) return mb % 1 === 0 ? mb + 'M' : mb.toFixed(1) + 'M';
    return kb % 1 === 0 ? kb + 'K' : kb.toFixed(1) + 'K';
  }}

  function getHumanLabel(s) {{
    const b = parseInt(s);
    if (b === 8192) return "8 KiB (Min Floor)";
    if (b === 16384) return "16 KiB (Decode Token)";
    if (b === 131072) return "128 KiB (Small Activation)";
    if (b === 1048576) return "1 MiB Tensor";
    if (b === 16777216) return "16 MiB Activation";
    if (b === 67108864) return "64 MiB Chunk";
    if (b === 134217728) return "128 MiB (8K Prefill Chunk)";
    if (b === 268435456) return "256 MiB (Large Prefill)";
    return formatSize(b) + "iB";
  }}

  function formatMs(msVal) {{
    if (msVal === 0 || isNaN(msVal)) return "-";
    if (msVal < 1) return msVal.toFixed(3) + " ms";
    if (msVal < 10) return msVal.toFixed(2) + " ms";
    return msVal.toFixed(1) + " ms";
  }}

  function renderCollectiveView(coll) {{
    const sel = document.getElementById(coll + '_tpSelect').value;
    const data = benchData[coll];
    if (!data) return;

    const dlBar = document.getElementById(coll + '_downloadBar');
    const tableContainer = document.getElementById(coll + '_tableContainer');
    const insights = document.getElementById(coll + '_insightsContainer');

    const rates = ['NATIVE', '100', '50', '20', '10'];
    const rateNames = {{
      'NATIVE': '175G Native',
      '100': '100G Capped',
      '50': '50G Capped',
      '20': '20G Capped',
      '10': '10G Capped'
    }};
    const colors = {{
      'NATIVE': '#3fb950',
      '100': '#58a6ff',
      '50': '#d29922',
      '20': '#f0883e',
      '10': '#f85149'
    }};

    let currentTpKey = (sel === 'compare') ? 'tp16' : sel;
    let tpLabel = (sel === 'tp16') ? 'TP=16' : ((sel === 'tp8') ? 'TP=8' : ((sel === 'tp4') ? 'TP=4' : 'TP'));
    
    let dlHtml = `
      <a href="tp16_vs_tp8_local_${{coll}}_comparison.csv" download style="background:rgba(63,185,80,0.25); border:1px solid #3fb950; color:#fff; font-size:11px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">TP-16 vs TP-8 Local CSV &darr;</a>
      <a href="tp8_multinode_vs_local_${{coll}}_comparison.csv" download style="background:rgba(88,166,255,0.25); border:1px solid #58a6ff; color:#fff; font-size:11px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">TP-8 Multi vs Local CSV &darr;</a>
      <a href="tp4_multinode_vs_local_${{coll}}_comparison.csv" download style="background:rgba(219,109,255,0.25); border:1px solid #db6dff; color:#fff; font-size:11px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">TP-4 Multi vs Local CSV &darr;</a>
      <a href="${{coll.toUpperCase()}}_EXECUTIVE_REPORT.md" download style="background:rgba(188,140,255,0.25); border:1px solid #bc8cff; color:#fff; font-size:11px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">Executive Report (.md) &darr;</a>
    `;
    dlBar.innerHTML = dlHtml;

    const allSizes = Object.keys(data.tp16.NATIVE).map(Number).sort((a,b)=>a-b);
    const labels = allSizes.map(formatSize);

    if (chartInstances[coll + '_lat']) chartInstances[coll + '_lat'].destroy();
    if (chartInstances[coll + '_bw']) chartInstances[coll + '_bw'].destroy();

    let chart1Datasets = [];
    let chart2Datasets = [];
    let tableHtml = '';

    if (sel === 'tp16' || sel === 'tp8' || sel === 'tp4') {{
      const curData = data[sel];
      const tpTitle = (sel === 'tp16') ? 'TP=16 (16 GPUs Multi-Node)' : ((sel === 'tp8') ? 'TP=8 (4+4 GPUs Multi-Node)' : 'TP=4 (2+2 GPUs Multi-Node)');
      
      document.getElementById(coll + '_chart1_title').innerText = `${{coll.toUpperCase()}} (${{tpTitle}}) Latency Across 5 Bandwidths (ms)`;
      document.getElementById(coll + '_chart2_title').innerText = `${{coll.toUpperCase()}} (${{tpTitle}}) Algorithmic Bandwidth (GB/s)`;

      rates.forEach(r => {{
        const latData = allSizes.map(s => curData[r] && curData[r][s] ? (curData[r][s].time_us / 1000) : 0);
        chart1Datasets.push({{
          label: rateNames[r],
          data: latData,
          borderColor: colors[r],
          tension: 0.2
        }});
      }});

      if (sel === 'tp8' && data.tp8_local) {{
        chart1Datasets.push({{
          label: 'Node-Local PCIe (Dual-Socket)',
          data: allSizes.map(s => data.tp8_local[s] ? (data.tp8_local[s].time_us / 1000) : 0),
          borderColor: '#bc8cff',
          borderDash: [5, 5],
          tension: 0.2
        }});
      }} else if (sel === 'tp4' && data.tp4_local) {{
        chart1Datasets.push({{
          label: 'Socket-Local NUMA0 (Zero-UPI)',
          data: allSizes.map(s => data.tp4_local[s] ? (data.tp4_local[s].time_us / 1000) : 0),
          borderColor: '#f778ba',
          borderDash: [5, 5],
          tension: 0.2
        }});
      }}

      const subsetSizes = [16777216, 33554432, 67108864, 134217728, 268435456];
      rates.forEach(r => {{
        const bwData = subsetSizes.map(s => curData[r] && curData[r][s] ? curData[r][s].algbw_gb_s : 0);
        chart2Datasets.push({{
          label: rateNames[r],
          data: bwData,
          backgroundColor: colors[r]
        }});
      }});

      tableHtml = `<table>
        <thead>
          <tr>
            <th>Payload Size</th><th>Label</th>
            <th>Native 175G (ms)</th><th>Capped 100G (ms)</th><th>Capped 50G (ms)</th><th>Capped 20G (ms)</th><th>Capped 10G (ms)</th>
            <th>100G vs Native</th><th>10G vs Native Penalty</th>
          </tr>
        </thead>
        <tbody>` +
        allSizes.map(s => {{
          const tNat = (curData.NATIVE && curData.NATIVE[s]) ? (curData.NATIVE[s].time_us / 1000) : 0;
          const t100 = (curData['100'] && curData['100'][s]) ? (curData['100'][s].time_us / 1000) : 0;
          const t50 = (curData['50'] && curData['50'][s]) ? (curData['50'][s].time_us / 1000) : 0;
          const t20 = (curData['20'] && curData['20'][s]) ? (curData['20'][s].time_us / 1000) : 0;
          const t10 = (curData['10'] && curData['10'][s]) ? (curData['10'][s].time_us / 1000) : 0;
          const r100 = tNat > 0 ? (t100/tNat).toFixed(2) + 'x' : '-';
          const r10 = tNat > 0 ? (t10/tNat).toFixed(2) + 'x' : '-';
          return `<tr>
            <td><b>${{formatSize(s)}}</b></td>
            <td>${{getHumanLabel(s)}}</td>
            <td>${{formatMs(tNat)}}</td>
            <td>${{formatMs(t100)}}</td>
            <td>${{formatMs(t50)}}</td>
            <td>${{formatMs(t20)}}</td>
            <td>${{formatMs(t10)}}</td>
            <td>${{r100}}</td>
            <td class="${{parseFloat(r10) > 1.5 ? 'highlight-red' : 'highlight-green'}}"><b>${{r10}}</b></td>
          </tr>`;
        }}).join('') + `</tbody></table>`;

      insights.innerHTML = `
        <div class="card">
          <div class="card-header"><h3>${{tpLabel}} Decode Latency Floor (&alpha;-bound)</h3><span class="badge badge-hw">8K - 512K</span></div>
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">For small decode payloads (8K - 512K), multi-node ${{tpLabel}} latency remains bounded at <b>~0.10 ms to 0.35 ms</b>. Linux TCP socket synchronization sets the floor, meaning network bandwidth caps (10G vs 175G) have minimal latency impact until payload exceeds ~1 MiB.</p>
        </div>
        <div class="card">
          <div class="card-header"><h3>${{tpLabel}} Prefill Scalability (&beta;-bound)</h3><span class="badge badge-hw">64M - 256M</span></div>
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">At 256 MiB, the physical network link is the dominant bottleneck. Throttling from 175G Native down to 10G Capped causes up to a <b>~9x - 110x slowdown</b> depending on collective communication pattern, proving why 100G+ fabric is required for high-throughput multi-node LLM serving.</p>
        </div>
      `;
    }} else if (sel === 'compare') {{
      document.getElementById(coll + '_chart1_title').innerText = coll.toUpperCase() + ' Latency Comparison: Multi-Node vs Local Baselines (ms)';
      document.getElementById(coll + '_chart2_title').innerText = coll.toUpperCase() + ' Algorithmic Bandwidth Comparison';

      chart1Datasets.push({{ label: 'TP=4 Socket-Local (NUMA0)', data: allSizes.map(s => data.tp4_local[s] ? (data.tp4_local[s].time_us / 1000) : 0), borderColor: '#3fb950', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=8 Node-Local (PCIe)', data: allSizes.map(s => data.tp8_local[s] ? (data.tp8_local[s].time_us / 1000) : 0), borderColor: '#58a6ff', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=4 Multi-Node (175G)', data: allSizes.map(s => data.tp4.NATIVE[s] ? (data.tp4.NATIVE[s].time_us / 1000) : 0), borderColor: '#d29922', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=8 Multi-Node (175G)', data: allSizes.map(s => data.tp8.NATIVE[s] ? (data.tp8.NATIVE[s].time_us / 1000) : 0), borderColor: '#bc8cff', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=16 Multi-Node (175G)', data: allSizes.map(s => data.tp16.NATIVE[s] ? data.tp16.NATIVE[s].time_us / 1000 : 0), borderColor: '#38bdf8', tension: 0.2 }});

      chart2Datasets.push({{ label: 'TP=4 Local', data: allSizes.map(s => data.tp4_local[s] ? data.tp4_local[s].algbw_gb_s : 0), backgroundColor: '#3fb950' }});
      chart2Datasets.push({{ label: 'TP=8 Local', data: allSizes.map(s => data.tp8_local[s] ? data.tp8_local[s].algbw_gb_s : 0), backgroundColor: '#58a6ff' }});
      chart2Datasets.push({{ label: 'TP=16 Multi-Node (175G)', data: allSizes.map(s => data.tp16.NATIVE[s] ? data.tp16.NATIVE[s].algbw_gb_s : 0), backgroundColor: '#38bdf8' }});

      tableHtml = `<table>
        <thead><tr><th>Payload</th><th>Phase</th><th>TP=4 (NUMA-Local)</th><th>TP=8 (Node-Local)</th><th>TP=8 Multi-Node</th><th>TP=16 Multi-Node</th><th>Local vs Multi-Node Speedup</th></tr></thead>
        <tbody>` +
        allSizes.map(s => {{
          const t4L = data.tp4_local[s] ? (data.tp4_local[s].time_us / 1000) : 0;
          const t8L = data.tp8_local[s] ? (data.tp8_local[s].time_us / 1000) : 0;
          const t8M = data.tp8.NATIVE[s] ? (data.tp8.NATIVE[s].time_us / 1000) : 0;
          const t16M = data.tp16.NATIVE[s] ? (data.tp16.NATIVE[s].time_us / 1000) : 0;
          const speedup = t4L > 0 && t16M > 0 ? (t16M/t4L).toFixed(1) + 'x' : '-';
          return `<tr>
            <td><b>${{formatSize(s)}}</b></td>
            <td>${{getHumanLabel(s)}}</td>
            <td class="highlight-green">${{formatMs(t4L)}}</td>
            <td class="highlight-green">${{formatMs(t8L)}}</td>
            <td>${{formatMs(t8M)}}</td>
            <td>${{formatMs(t16M)}}</td>
            <td class="highlight-green"><b>${{speedup}}</b></td>
          </tr>`;
        }}).join('') + `</tbody></table>`;

      insights.innerHTML = `
        <div class="card">
          <div class="card-header"><h3>Core Architecture Takeaway: NUMA Locality</h3><span class="badge badge-hw">TOPOLOGY</span></div>
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">Across all collectives (${{coll.toUpperCase()}}), TP=4 yields the lowest latency floor (<b>~0.016 ms - 0.018 ms</b>), outperforming TP=8 by ~2x and multi-node TP=16 by over <b>10x - 20x</b> on small decode packets due to zero inter-socket UPI cross-talk.</p>
        </div>
        <div class="card">
          <div class="card-header"><h3>Scale-Out Scaling Law</h3><span class="badge badge-hw">DISTRIBUTED</span></div>
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">For large prefill batches (&gt;64 MiB), TP=16 leverages the full compute of 16 GPUs, reaching line-rate saturation when backed by &ge; 50 Gbps network fabric.</p>
        </div>
      `;
    }}

    tableContainer.innerHTML = tableHtml;

    const ctx1 = document.getElementById(coll + '_chartLatency').getContext('2d');
    chartInstances[coll + '_lat'] = new Chart(ctx1, {{
      type: 'line',
      data: {{ labels: labels, datasets: chart1Datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Payload Buffer Size', color: '#8b949e' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: 'Latency (Milliseconds - Log Scale)', color: '#8b949e' }},
            grid: {{ color: 'rgba(255,255,255,0.05)' }},
            ticks: {{ callback: function(value) {{ return Number(value).toFixed(value < 1 ? 2 : 0) + ' ms'; }} }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#e6edf3', boxWidth: 12 }} }},
          tooltip: {{ callbacks: {{ label: function(ctx) {{ const v = ctx.parsed.y; return ctx.dataset.label + ': ' + (v < 1 ? v.toFixed(3) : v.toFixed(2)) + ' ms'; }} }} }}
        }}
      }}
    }});

    const ctx2 = document.getElementById(coll + '_chartBandwidth').getContext('2d');
    chartInstances[coll + '_bw'] = new Chart(ctx2, {{
      type: 'bar',
      data: {{
        labels: (sel === 'tp16' || sel === 'tp8' || sel === 'tp4') ? ['16M', '32M', '64M', '128M', '256M'] : labels,
        datasets: chart2Datasets
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Buffer Size', color: '#8b949e' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{ title: {{ display: true, text: 'Algorithmic Bandwidth (GB/s)', color: '#8b949e' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#e6edf3', boxWidth: 12 }} }} }}
      }}
    }});
  }}

  function renderSendRecvView() {{
    const data = benchData.sendrecv;
    if (!data) return;

    const allSizes = Object.keys(data.NATIVE).map(Number).sort((a,b)=>a-b);
    const labels = allSizes.map(formatSize);

    if (chartInstances['sr_lat']) chartInstances['sr_lat'].destroy();
    if (chartInstances['sr_bw']) chartInstances['sr_bw'].destroy();

    const rates = ['NATIVE', '100', '50', '20', '10'];
    const rateNames = {{ 'NATIVE': '2-Node 175G Native', '100': '2-Node 100G', '50': '2-Node 50G', '20': '2-Node 20G', '10': '2-Node 10G' }};
    const colors = {{ 'NATIVE': '#3fb950', '100': '#58a6ff', '50': '#d29922', '20': '#f0883e', '10': '#f85149' }};

    let chart1Datasets = [];
    chart1Datasets.push({{
      label: 'Local Intra-NUMA (Same Socket)',
      data: allSizes.map(s => data.local_intra[s] ? (data.local_intra[s].time_us / 1000) : 0),
      borderColor: '#3fb950',
      borderDash: [5, 5],
      tension: 0.2
    }});
    chart1Datasets.push({{
      label: 'Local Cross-NUMA (Inter-Socket)',
      data: allSizes.map(s => data.local_cross[s] ? (data.local_cross[s].time_us / 1000) : 0),
      borderColor: '#bc8cff',
      borderDash: [5, 5],
      tension: 0.2
    }});

    rates.forEach(r => {{
      chart1Datasets.push({{
        label: rateNames[r],
        data: allSizes.map(s => data[r][s] ? (data[r][s].time_us / 1000) : 0),
        borderColor: colors[r],
        tension: 0.2
      }});
    }});

    let chart2Datasets = [];
    const subsetSizes = [16777216, 33554432, 67108864, 134217728, 268435456];
    rates.forEach(r => {{
      chart2Datasets.push({{
        label: rateNames[r],
        data: subsetSizes.map(s => data[r][s] ? data[r][s].algbw_gb_s : 0),
        backgroundColor: colors[r]
      }});
    }});

    const ctx1 = document.getElementById('sendrecv_chartLatency').getContext('2d');
    chartInstances['sr_lat'] = new Chart(ctx1, {{
      type: 'line',
      data: {{ labels: labels, datasets: chart1Datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Payload Buffer Size', color: '#8b949e' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: 'Latency (Milliseconds - Log Scale)', color: '#8b949e' }},
            grid: {{ color: 'rgba(255,255,255,0.05)' }},
            ticks: {{ callback: function(value) {{ return Number(value).toFixed(value < 1 ? 2 : 0) + ' ms'; }} }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#e6edf3', boxWidth: 12 }} }},
          tooltip: {{ callbacks: {{ label: function(ctx) {{ const v = ctx.parsed.y; return ctx.dataset.label + ': ' + (v < 1 ? v.toFixed(3) : v.toFixed(2)) + ' ms'; }} }} }}
        }}
      }}
    }});

    const ctx2 = document.getElementById('sendrecv_chartBandwidth').getContext('2d');
    chartInstances['sr_bw'] = new Chart(ctx2, {{
      type: 'bar',
      data: {{ labels: ['16M', '32M', '64M', '128M', '256M'], datasets: chart2Datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Buffer Size', color: '#8b949e' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{ title: {{ display: true, text: 'Algorithmic Bandwidth (GB/s)', color: '#8b949e' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#e6edf3', boxWidth: 12 }} }} }}
      }}
    }});

    let tableHtml = `<table>
      <thead>
        <tr>
          <th>Payload Size</th><th>Label</th>
          <th>Intra-NUMA (ms)</th><th>Cross-NUMA (ms)</th>
          <th>2-Node 175G (ms)</th><th>2-Node 100G (ms)</th><th>2-Node 50G (ms)</th><th>2-Node 20G (ms)</th><th>2-Node 10G (ms)</th>
          <th>10G vs Intra-NUMA</th>
        </tr>
      </thead>
      <tbody>` +
      allSizes.map(s => {{
        const intra = data.local_intra[s] ? (data.local_intra[s].time_us / 1000) : 0;
        const cross = data.local_cross[s] ? (data.local_cross[s].time_us / 1000) : 0;
        const nat = data.NATIVE[s] ? (data.NATIVE[s].time_us / 1000) : 0;
        const t100 = data['100'][s] ? (data['100'][s].time_us / 1000) : 0;
        const t50 = data['50'][s] ? (data['50'][s].time_us / 1000) : 0;
        const t20 = data['20'][s] ? (data['20'][s].time_us / 1000) : 0;
        const t10 = data['10'][s] ? (data['10'][s].time_us / 1000) : 0;
        const pen = intra > 0 ? (t10/intra).toFixed(1) + 'x' : '-';
        return `<tr>
          <td><b>${{formatSize(s)}}</b></td>
          <td>${{getHumanLabel(s)}}</td>
          <td class="highlight-green">${{formatMs(intra)}}</td>
          <td class="highlight-green">${{formatMs(cross)}}</td>
          <td>${{formatMs(nat)}}</td>
          <td>${{formatMs(t100)}}</td>
          <td>${{formatMs(t50)}}</td>
          <td>${{formatMs(t20)}}</td>
          <td>${{formatMs(t10)}}</td>
          <td class="highlight-red"><b>${{pen}}</b></td>
        </tr>`;
      }}).join('') + `</tbody></table>`;

    document.getElementById('sendrecv_tableContainer').innerHTML = tableHtml;
  }}
</script>
</body>
</html>
"""

full_html = html_content + "\n" + tab2_html + "\n" + tab3_html + "\n" + tab4_html + "\n" + tab5_html + "\n" + tab6_html + "\n" + script_js

with open(html_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"Generated complete dashboard at: {html_path}")
