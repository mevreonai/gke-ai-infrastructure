import os, json, hashlib

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results"
json_path = os.path.join(base_dir, "fresh_benchmark_suite", "master_benchmarks.json")
html_path = os.path.join(base_dir, "v4_interactive_dashboards.html")

with open(json_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

# Read existing HTML to extract header and Tab 1
with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

header_and_tab1 = "".join(lines[:297])

# Ensure header has all 6 tabs
old_header_tabs = """  <div class="tabs">
    <button class="tab-btn active" onclick="showTab(1)">Dashboard 1: 9-Panel Decomposition</button>
    <button class="tab-btn" onclick="showTab(2)">Dashboard 2: 3-Pair AllReduce Deep Dive</button>
    <button class="tab-btn" onclick="showTab(3)">Dashboard 3: AllReduce Bandwidth Sweep (10G-175G)</button>
    <button class="tab-btn" onclick="showTab(4)">Dashboard 4: Pipeline Calculator & Fabric</button>
  </div>"""

current_4_tabs = """  <div class="tabs">
    <button class="tab-btn active" onclick="showTab(1)">Dashboard 1: 9-Panel Infographic</button>
    <button class="tab-btn" onclick="showTab(2)">Dashboard 2: AllReduce Suite</button>
    <button class="tab-btn" onclick="showTab(3)">Dashboard 3: AllGather Suite</button>
    <button class="tab-btn" onclick="showTab(4)">Dashboard 4: ReduceScatter Suite</button>
  </div>"""

new_6_tabs = """  <div class="tabs">
    <button class="tab-btn active" onclick="showTab(1)" id="btnTab1">1. Infographic</button>
    <button class="tab-btn" onclick="showTab(2)" id="btnTab2">2. AllReduce</button>
    <button class="tab-btn" onclick="showTab(3)" id="btnTab3">3. AllGather</button>
    <button class="tab-btn" onclick="showTab(4)" id="btnTab4">4. ReduceScatter</button>
    <button class="tab-btn" onclick="showTab(5)" id="btnTab5">5. Local vs Multi-Node</button>
    <button class="tab-btn" onclick="showTab(6)" id="btnTab6">6. Files & Artifacts Hub</button>
  </div>"""

if current_4_tabs in header_and_tab1:
    header_and_tab1 = header_and_tab1.replace(current_4_tabs, new_6_tabs)
elif old_header_tabs in header_and_tab1:
    header_and_tab1 = header_and_tab1.replace(old_header_tabs, new_6_tabs)

# Inject extra styles for Tab 5, Tab 6, file cards, and modal viewer
extra_styles = """
  /* Extra Styles for File Explorer & Tab 5/6 */
  .hub-header { background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95)); border: 1px solid var(--border); border-radius: 12px; padding: 22px; margin-bottom: 24px; }
  .hub-title { font-size: 20px; font-weight: 800; color: #fff; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; }
  .hub-subtitle { font-size: 13px; color: var(--text-muted); line-height: 1.5; }
  
  .filter-bar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 16px; }
  .filter-pill { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text-muted); padding: 7px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .filter-pill.active { background: var(--accent-blue); color: #fff; border-color: var(--accent-blue); box-shadow: 0 0 10px rgba(59,130,246,0.4); }
  .search-box { flex: 1; min-width: 260px; background: #131b2e; border: 1px solid var(--border); border-radius: 8px; padding: 8px 14px; color: #fff; font-size: 13px; }
  .search-box:focus { outline: none; border-color: var(--accent-cyan); }

  .file-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 18px; margin-bottom: 30px; }
  .file-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s, border-color 0.2s; }
  .file-card:hover { transform: translateY(-3px); border-color: rgba(59,130,246,0.6); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
  .file-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
  .file-badge-group { display: flex; gap: 6px; align-items: center; }
  .file-ext { font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; }
  .ext-csv { background: rgba(16,185,129,0.15); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.4); }
  .ext-md { background: rgba(139,92,246,0.15); color: var(--accent-purple); border: 1px solid rgba(139,92,246,0.4); }
  .ext-tgz { background: rgba(245,158,11,0.15); color: var(--accent-amber); border: 1px solid rgba(245,158,11,0.4); }
  .ext-json { background: rgba(6,182,212,0.15); color: var(--accent-cyan); border: 1px solid rgba(6,182,212,0.4); }
  
  .file-title { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 4px; line-height: 1.3; }
  .file-name { font-family: monospace; font-size: 11px; color: var(--accent-cyan); word-break: break-all; margin-bottom: 8px; }
  .file-desc { font-size: 12px; color: var(--text-muted); line-height: 1.5; margin-bottom: 16px; flex-grow: 1; }
  .file-actions { display: flex; gap: 10px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; }
  .btn-download { background: var(--accent-blue); color: #fff; border: none; border-radius: 6px; padding: 7px 14px; font-size: 12px; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; transition: background 0.2s; }
  .btn-download:hover { background: #2563eb; }
  .btn-preview { background: rgba(255,255,255,0.06); border: 1px solid var(--border); color: #e2e8f0; border-radius: 6px; padding: 7px 14px; font-size: 12px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s; }
  .btn-preview:hover { background: rgba(255,255,255,0.12); border-color: #fff; color: #fff; }

  /* Modal Viewer */
  .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 9999; justify-content: center; align-items: center; padding: 24px; }
  .modal-overlay.active { display: flex; }
  .modal-content { background: #0f172a; border: 1px solid var(--border); border-radius: 14px; width: 95%; max-width: 1200px; height: 90vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
  .modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--border); background: #131d36; }
  .modal-title-group { display: flex; align-items: center; gap: 12px; }
  .modal-title { font-size: 17px; font-weight: 700; color: #fff; }
  .modal-body { flex: 1; overflow-y: auto; padding: 24px; font-size: 13px; line-height: 1.6; }
  .modal-close { background: none; border: none; color: var(--text-muted); font-size: 24px; cursor: pointer; transition: color 0.2s; }
  .modal-close:hover { color: #fff; }

  /* KPI Stat Box */
  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
  .kpi-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; }
  .kpi-title { font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 6px; }
  .kpi-val { font-size: 22px; font-weight: 800; color: #fff; margin-bottom: 2px; }
  .kpi-sub { font-size: 11px; color: var(--text-muted); display: flex; justify-content: space-between; }
"""

header_and_tab1 = header_and_tab1.replace("</style>", extra_styles + "\n</style>")

# Read all deliverables to embed
files_to_embed = [
    {
        "id": "tp16_vs_tp8_local_allreduce",
        "filename": "tp16_vs_tp8_local_allreduce_comparison.csv",
        "title": "TP-16 Multi-Node vs. TP-8 Local (AllReduce)",
        "type": "csv",
        "category": "comparisons",
        "collective": "AllReduce",
        "size": "1.9 KB",
        "desc": "Side-by-side comparison of 16-GPU multi-node AllReduce across 5 network bandwidth caps (175G Native down to 10G) against the 8-GPU node-local PCIe Gen5 baseline from 16 KiB to 256 MiB."
    },
    {
        "id": "TP16_VS_TP8_LOCAL_ALLREDUCE_REPORT",
        "filename": "TP16_VS_TP8_LOCAL_ALLREDUCE_REPORT.md",
        "title": "AllReduce Characterization Executive Report",
        "type": "md",
        "category": "reports",
        "collective": "AllReduce",
        "size": "4.0 KB",
        "desc": "Complete executive markdown briefing on AllReduce latency milestones, mathematical alpha/beta analysis, and network penalty multipliers for distributed training."
    },
    {
        "id": "tp16_vs_tp8_local_allgather",
        "filename": "tp16_vs_tp8_local_allgather_comparison.csv",
        "title": "TP-16 Multi-Node vs. TP-8 Local (AllGather)",
        "type": "csv",
        "category": "comparisons",
        "collective": "AllGather",
        "size": "1.9 KB",
        "desc": "Direct characterization of distributed AllGather communication times, comparing TP=16 multi-node across 10G-175G against single-node 8-GPU PCIe across 16 payload sizes."
    },
    {
        "id": "TP16_VS_TP8_LOCAL_ALLGATHER_REPORT",
        "filename": "TP16_VS_TP8_LOCAL_ALLGATHER_REPORT.md",
        "title": "AllGather Characterization Executive Report",
        "type": "md",
        "category": "reports",
        "collective": "AllGather",
        "size": "4.0 KB",
        "desc": "Executive briefing detailing AllGather scaling from 16 KiB token decode to 256 MiB prefill, ring communication models, and network saturation ceilings."
    },
    {
        "id": "tp16_vs_tp8_local_reducescatter",
        "filename": "tp16_vs_tp8_local_reducescatter_comparison.csv",
        "title": "TP-16 Multi-Node vs. TP-8 Local (ReduceScatter)",
        "type": "csv",
        "category": "comparisons",
        "collective": "ReduceScatter",
        "size": "1.9 KB",
        "desc": "Empirical benchmarks for ReduceScatter across 10G-175G multi-node vs. 8-GPU local PCIe Gen5 baseline with exact speedup/slowdown ratios."
    },
    {
        "id": "TP16_VS_TP8_LOCAL_REDUCESCATTER_REPORT",
        "filename": "TP16_VS_TP8_LOCAL_REDUCESCATTER_REPORT.md",
        "title": "ReduceScatter Characterization Executive Report",
        "type": "md",
        "category": "reports",
        "collective": "ReduceScatter",
        "size": "4.0 KB",
        "desc": "Technical markdown report on ReduceScatter latency, ring pipeline decomposition, and duality verification with AllGather."
    },
    {
        "id": "tp16_vs_tp8_local_all_collectives",
        "filename": "tp16_vs_tp8_local_all_collectives_comparison.csv",
        "title": "TP-16 vs. TP-8 Local All Collectives Master CSV",
        "type": "csv",
        "category": "master",
        "collective": "All Collectives",
        "size": "5.7 KB",
        "desc": "Unified comparative dataset combining AllReduce, AllGather, and ReduceScatter for TP-16 vs. TP-8 Local across all payload buffer sizes."
    },
    {
        "id": "TP16_VS_TP8_LOCAL_MASTER_REPORT",
        "filename": "TP16_VS_TP8_LOCAL_MASTER_REPORT.md",
        "title": "Master Distributed Collective Comparison Report",
        "type": "md",
        "category": "reports",
        "collective": "All Collectives",
        "size": "2.1 KB",
        "desc": "Executive master summary comparing all three collectives, presenting the 256 MiB comparison table, and mathematical validation."
    },
    {
        "id": "tp8_multinode_vs_local_allreduce",
        "filename": "tp8_multinode_vs_local_allreduce_comparison.csv",
        "title": "TP-8 Multi-Node (4+4) vs. TP-8 Local (AllReduce)",
        "type": "csv",
        "category": "comparisons",
        "collective": "AllReduce",
        "size": "2.5 KB",
        "desc": "Isolates network impact for 8 GPUs: compares 4+4 ranks split across 2 nodes over VPC against 8 ranks colocated on a single node."
    },
    {
        "id": "tp8_multinode_vs_local_allgather",
        "filename": "tp8_multinode_vs_local_allgather_comparison.csv",
        "title": "TP-8 Multi-Node (4+4) vs. TP-8 Local (AllGather)",
        "type": "csv",
        "category": "comparisons",
        "collective": "AllGather",
        "size": "2.5 KB",
        "desc": "Evaluates AllGather communication overhead of splitting TP=8 across 2 nodes at various network rates vs. single-node local."
    },
    {
        "id": "tp8_multinode_vs_local_reducescatter",
        "filename": "tp8_multinode_vs_local_reducescatter_comparison.csv",
        "title": "TP-8 Multi-Node (4+4) vs. TP-8 Local (ReduceScatter)",
        "type": "csv",
        "category": "comparisons",
        "collective": "ReduceScatter",
        "size": "2.6 KB",
        "desc": "Empirical comparison of ReduceScatter on TP=8 multi-node vs. TP=8 single-node PCIe Gen5."
    },
    {
        "id": "tp4_multinode_vs_local_allreduce",
        "filename": "tp4_multinode_vs_local_allreduce_comparison.csv",
        "title": "TP-4 Multi-Node (2+2) vs. TP-4 Local (AllReduce)",
        "type": "csv",
        "category": "comparisons",
        "collective": "AllReduce",
        "size": "2.6 KB",
        "desc": "Evaluates 4 GPUs: compares 2 ranks per node across 2 nodes against 4 ranks colocated on a single socket (NUMA0 zero-UPI)."
    },
    {
        "id": "tp4_multinode_vs_local_allgather",
        "filename": "tp4_multinode_vs_local_allgather_comparison.csv",
        "title": "TP-4 Multi-Node (2+2) vs. TP-4 Local (AllGather)",
        "type": "csv",
        "category": "comparisons",
        "collective": "AllGather",
        "size": "2.6 KB",
        "desc": "AllGather performance when distributing 4 GPUs across 2 nodes vs. socket-local NUMA0."
    },
    {
        "id": "tp4_multinode_vs_local_reducescatter",
        "filename": "tp4_multinode_vs_local_reducescatter_comparison.csv",
        "title": "TP-4 Multi-Node (2+2) vs. TP-4 Local (ReduceScatter)",
        "type": "csv",
        "category": "comparisons",
        "collective": "ReduceScatter",
        "size": "2.6 KB",
        "desc": "ReduceScatter scaling for TP=4 multi-node vs. socket-local NUMA0."
    },
    {
        "id": "tp8_and_tp4_local_vs_multinode_comparison_master",
        "filename": "tp8_and_tp4_local_vs_multinode_comparison_master.csv",
        "title": "TP-8 & TP-4 Local vs. Multi-Node Master CSV",
        "type": "csv",
        "category": "master",
        "collective": "Multi-Topology",
        "size": "13.7 KB",
        "desc": "Master dataset with all 90 benchmark rows comparing TP-8 and TP-4 local baselines against multi-node 10G-175G across AllReduce, AllGather, and ReduceScatter."
    },
    {
        "id": "TP8_AND_TP4_LOCAL_VS_MULTINODE_REPORT",
        "filename": "TP8_AND_TP4_LOCAL_VS_MULTINODE_REPORT.md",
        "title": "TP-8 & TP-4 Local vs. Multi-Node Comprehensive Report",
        "type": "md",
        "category": "reports",
        "collective": "Multi-Topology",
        "size": "16.4 KB",
        "desc": "Detailed 160-line architectural breakdown comparing node-local dual-socket and socket-local NUMA0 baselines against multi-node sweeps."
    },
    {
        "id": "allreduce_fresh",
        "filename": "allreduce_fresh.tgz",
        "title": "Raw AllReduce VM Execution Logs & Telemetry",
        "type": "tgz",
        "category": "raw",
        "collective": "AllReduce",
        "size": "126.1 KB",
        "sha256": "ffdeae298be489ba92b729ba93660c4633e084b13bddd48377d0722b444ef348",
        "desc": "Compressed tarball containing raw nccl-tests stdout logs, tc qdisc rate validation telemetry, and mpirun traces directly from kimi-node-0 and kimi-node-1."
    },
    {
        "id": "allgather_reducescatter_fresh",
        "filename": "allgather_reducescatter_fresh.tgz",
        "title": "Raw AllGather & ReduceScatter VM Execution Logs",
        "type": "tgz",
        "category": "raw",
        "collective": "AllGather & ReduceScatter",
        "size": "251.4 KB",
        "sha256": "499a0021b167ace2e9e82c557260f8f313b2aee8cd1505a4335e0c2b567badf3",
        "desc": "Compressed tarball containing all raw stdout logs and network verification telemetry for AllGather and ReduceScatter multi-node runs."
    },
    {
        "id": "master_benchmarks_json",
        "filename": "fresh_benchmark_suite/master_benchmarks.json",
        "title": "Master Hardware Benchmarks JSON Database",
        "type": "json",
        "category": "master",
        "collective": "All Collectives",
        "size": "18.5 KB",
        "desc": "Structured JSON database containing all raw latency and bandwidth data points for AllReduce, AllGather, and ReduceScatter across all TP configurations and network rates."
    }
]

# Read content of text files
embedded_contents = {}
for item in files_to_embed:
    if item["type"] in ["csv", "md", "json"]:
        p = os.path.join(base_dir, item["filename"])
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as fp:
                embedded_contents[item["id"]] = fp.read()

# Build collective tabs (Tab 2, 3, 4)
def build_collective_tab(tab_num, coll_key, coll_title, coll_desc):
    return f"""
<!-- TAB {tab_num}: {coll_title} Suite -->
<div id="tab{tab_num}" class="tab-content">
  <!-- Controls Bar -->
  <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
    <div>
      <h2 style="font-size: 18px; color: #fff; font-weight: 700; margin-bottom: 3px;">{coll_title} Distributed Characterization</h2>
      <p style="font-size: 13px; color: var(--text-muted);">{coll_desc}</p>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
      <label style="font-size: 13px; font-weight: 600; color: var(--accent-cyan);">Select TP Configuration:</label>
      <select id="{coll_key}_tpSelect" onchange="renderCollectiveView('{coll_key}')" style="background: #131b2e; border: 1px solid var(--accent-blue); color: #fff; padding: 8px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer;">
        <option value="tp16" selected>Page 1: TP=16 Multi-Node Network Sweep (10G - 175G)</option>
        <option value="tp8">Page 2: TP=8 Multi-Node Network Sweep (10G - 175G + Node-Local)</option>
        <option value="tp4">Page 3: TP=4 Multi-Node Network Sweep (10G - 175G + Socket-Local)</option>
        <option value="compare">Page 4: All TPs & Baseline Comparison (TP16 vs TP8 vs TP4)</option>
      </select>
    </div>
  </div>

  <!-- Dynamic Download Bar -->
  <div id="{coll_key}_downloadBar" style="margin-bottom: 18px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;"></div>

  <!-- Charts Row -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
    <div class="card">
      <div class="card-header">
        <h3 id="{coll_key}_chart1_title">Latency vs Payload Size (8 KiB - 256 MiB)</h3>
        <span class="badge badge-hw">LOG SCALE (ms)</span>
      </div>
      <div style="height: 270px;">
        <canvas id="{coll_key}_chartLatency"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h3 id="{coll_key}_chart2_title">Throughput / Algorithmic Bandwidth</h3>
        <span class="badge badge-hw">GB/s</span>
      </div>
      <div style="height: 270px;">
        <canvas id="{coll_key}_chartBandwidth"></canvas>
      </div>
    </div>
  </div>

  <!-- Dynamic Data Table Card -->
  <div class="card" style="margin-bottom: 20px;">
    <div class="card-header">
      <h3 id="{coll_key}_table_title">Empirical Benchmark Data Points (Latency in Milliseconds - ms)</h3>
      <span class="badge badge-hw" id="{coll_key}_table_badge">FRESH RUN &bull; LIVE HARDWARE</span>
    </div>
    <div id="{coll_key}_tableContainer" style="overflow-x: auto;"></div>
  </div>

  <!-- Analysis Callout -->
  <div id="{coll_key}_insightsContainer" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;"></div>
</div>
"""

tab2_html = build_collective_tab(2, "allreduce", "AllReduce", "Measured live on 16x RTX PRO 6000 Blackwell GPUs across 8 KiB to 256 MiB.")
tab3_html = build_collective_tab(3, "allgather", "AllGather", "Measured live on 16x RTX PRO 6000 Blackwell GPUs across 8 KiB to 256 MiB.")
tab4_html = build_collective_tab(4, "reducescatter", "ReduceScatter", "Measured live on 16x RTX PRO 6000 Blackwell GPUs across 8 KiB to 256 MiB.")

# Build Tab 5: Multi-Node vs. Local Deep Dive
tab5_html = """
<!-- TAB 5: Multi-Node vs Local Deep Dive -->
<div id="tab5" class="tab-content">
  <!-- Controls Bar -->
  <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
    <div>
      <h2 style="font-size: 18px; color: #fff; font-weight: 700; margin-bottom: 3px;">Multi-Node vs. Local Topology Comparison Suite</h2>
      <p style="font-size: 13px; color: var(--text-muted);">Direct empirical characterization of scale-out network penalty across all rates (175G Native down to 10G) against local PCIe Gen5 / NUMA baselines.</p>
    </div>
    <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
      <div>
        <label style="font-size: 12px; font-weight: 600; color: var(--accent-cyan); display:block; margin-bottom:4px;">Comparison Topology:</label>
        <select id="tab5_topoSelect" onchange="renderTab5View()" style="background: #131b2e; border: 1px solid var(--accent-blue); color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer;">
          <option value="tp16_vs_tp8" selected>TP-16 Multi-Node (16 GPUs) vs. TP-8 Node-Local (PCIe Gen5)</option>
          <option value="tp8_multi_vs_local">TP-8 Multi-Node (4+4 GPUs) vs. TP-8 Node-Local (PCIe Gen5)</option>
          <option value="tp4_multi_vs_local">TP-4 Multi-Node (2+2 GPUs) vs. TP-4 Socket-Local (NUMA0 Zero-UPI)</option>
        </select>
      </div>
      <div>
        <label style="font-size: 12px; font-weight: 600; color: var(--accent-cyan); display:block; margin-bottom:4px;">Collective:</label>
        <select id="tab5_collSelect" onchange="renderTab5View()" style="background: #131b2e; border: 1px solid var(--accent-blue); color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer;">
          <option value="allreduce" selected>AllReduce</option>
          <option value="allgather">AllGather</option>
          <option value="reducescatter">ReduceScatter</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Dynamic Download Bar for Tab 5 -->
  <div id="tab5_downloadBar" style="margin-bottom: 18px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;"></div>

  <!-- Key Milestone KPI Cards -->
  <div class="kpi-row" id="tab5_kpis"></div>

  <!-- Charts Row -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
    <div class="card">
      <div class="card-header">
        <h3 id="tab5_chart1_title">Latency: Local vs. Multi-Node (ms)</h3>
        <span class="badge badge-hw">LOG SCALE</span>
      </div>
      <div style="height: 280px;">
        <canvas id="tab5_chartLatency"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h3 id="tab5_chart2_title">Algorithmic Bandwidth Comparison (GB/s)</h3>
        <span class="badge badge-hw">BANDWIDTH</span>
      </div>
      <div style="height: 280px;">
        <canvas id="tab5_chartBandwidth"></canvas>
      </div>
    </div>
  </div>

  <!-- Detailed Table -->
  <div class="card" style="margin-bottom: 20px;">
    <div class="card-header">
      <h3 id="tab5_table_title">Empirical Comparison Table (Milliseconds - ms)</h3>
      <span class="badge badge-hw">100% REAL HARDWARE MEASURED</span>
    </div>
    <div id="tab5_tableContainer" style="overflow-x: auto;"></div>
  </div>

  <!-- Architecture Takeaways -->
  <div id="tab5_insights" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;"></div>
</div>
"""

# Build Tab 6: Files & Deliverables Hub / Artifacts Explorer
tab6_html = f"""
<!-- TAB 6: Files & Deliverables Hub -->
<div id="tab6" class="tab-content">
  <div class="hub-header">
    <div class="hub-title">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--accent-cyan);"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
      Distributed Benchmarks Deliverables & Artifacts Explorer
    </div>
    <p class="hub-subtitle">
      All 18 live hardware-verified files generated from <code>kimi-node-0</code> and <code>kimi-node-1</code> on GCP. Every dataset and report is standalone, exportable, and inspectable in-browser with zero external dependencies.
    </p>
    
    <div class="filter-bar">
      <button class="filter-pill active" onclick="filterArtifacts('all')">All Deliverables ({len(files_to_embed)})</button>
      <button class="filter-pill" onclick="filterArtifacts('reports')">Executive Reports (.md)</button>
      <button class="filter-pill" onclick="filterArtifacts('comparisons')">Comparison Datasets (.csv)</button>
      <button class="filter-pill" onclick="filterArtifacts('master')">Master Aggregations</button>
      <button class="filter-pill" onclick="filterArtifacts('raw')">Raw VM Archives (.tgz)</button>
      <input type="text" id="fileSearchInput" class="search-box" placeholder="Filter deliverables by title, collective, filename..." oninput="searchArtifacts(this.value)">
    </div>
  </div>

  <!-- Artifacts Grid -->
  <div class="file-grid" id="artifactsGrid"></div>
</div>

<!-- Modal Viewer -->
<div id="fileModal" class="modal-overlay" onclick="closeModalOnBackdrop(event)">
  <div class="modal-content" onclick="event.stopPropagation()">
    <div class="modal-header">
      <div class="modal-title-group">
        <span id="modalExtBadge" class="file-ext"></span>
        <div>
          <h3 id="modalTitle" class="modal-title"></h3>
          <div id="modalSubtitle" class="file-name" style="margin-bottom:0;"></div>
        </div>
      </div>
      <div style="display:flex; gap:10px; align-items:center;">
        <button id="modalCopyBtn" class="btn-preview" onclick="copyModalContent()">Copy Content</button>
        <a id="modalDlBtn" class="btn-download" href="#" download>Download File &darr;</a>
        <button class="modal-close" onclick="closeFileModal()">&times;</button>
      </div>
    </div>
    <div id="modalBody" class="modal-body"></div>
  </div>
</div>
"""

# Javascript logic for rendering charts, tables, tab 5, tab 6, and file modal
script_js = f"""
<script>
  const benchData = {json.dumps(bench_data)};
  const filesList = {json.dumps(files_to_embed)};
  const embeddedFiles = {json.dumps(embedded_contents)};

  function showTab(n) {{
    document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', i === n - 1));
    document.querySelectorAll('.tab-content').forEach((c, i) => c.classList.toggle('active', i === n - 1));
    if (n === 2) renderCollectiveView('allreduce');
    if (n === 3) renderCollectiveView('allgather');
    if (n === 4) renderCollectiveView('reducescatter');
    if (n === 5) renderTab5View();
    if (n === 6) renderArtifactsHub();
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

  // Render Tabs 2, 3, 4
  function renderCollectiveView(coll) {{
    const sel = document.getElementById(coll + '_tpSelect').value;
    const data = benchData[coll];

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
      'NATIVE': '#10b981',
      '100': '#3b82f6',
      '50': '#f59e0b',
      '20': '#f97316',
      '10': '#ef4444'
    }};

    // 1. Render Enhanced Download Bar
    let dlHtml = `
      <a href="tp16_vs_tp8_local_${{coll}}_comparison.csv" download class="btn-download" style="background:#10b981; font-size:12px; padding:6px 12px;">TP-16 vs TP-8 Local CSV &darr;</a>
      <a href="TP16_VS_TP8_LOCAL_${{coll.toUpperCase()}}_REPORT.md" download class="btn-download" style="background:#8b5cf6; font-size:12px; padding:6px 12px;">Executive Report (.md) &darr;</a>
      <button onclick="openFileViewer('tp16_vs_tp8_local_${{coll}}')" class="btn-preview" style="font-size:12px; padding:6px 12px;">Preview CSV &equiv;</button>
      <button onclick="openFileViewer('TP16_VS_TP8_LOCAL_${{coll.toUpperCase()}}_REPORT')" class="btn-preview" style="font-size:12px; padding:6px 12px;">Read Report &equiv;</button>
      <button onclick="showTab(5); document.getElementById('tab5_collSelect').value='${{coll}}'; renderTab5View();" class="btn-preview" style="background:rgba(59,130,246,0.15); border-color:#3b82f6; color:#93c5fd; font-size:12px; padding:6px 12px;">Deep Dive Tab 5 &rarr;</button>
    `;
    dlBar.innerHTML = dlHtml;

    // 2. Prepare Data Points
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
          borderColor: '#a855f7',
          borderDash: [5, 5],
          tension: 0.2
        }});
      }} else if (sel === 'tp4' && data.tp4_local) {{
        chart1Datasets.push({{
          label: 'Socket-Local NUMA0 (Zero-UPI)',
          data: allSizes.map(s => data.tp4_local[s] ? (data.tp4_local[s].time_us / 1000) : 0),
          borderColor: '#ec4899',
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
          <div class="card-header"><h3>${{tpLabel(sel)}} Small Decode Alpha Floor</h3><span class="badge badge-hw">16 KiB - 512 KiB</span></div>
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">For small decode packets, multi-node ${{tpLabel(sel)}} latency remains bounded by TCP socket signaling (<b>~0.10 ms to 0.27 ms</b>). Bandwidth capping does not penalize token decode times because the socket framing latency dominates.</p>
        </div>
        <div class="card">
          <div class="card-header"><h3>${{tpLabel(sel)}} Prefill Bandwidth Scalability</h3><span class="badge badge-hw">64 MiB - 256 MiB</span></div>
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">For large prefill tensors (256 MiB), link bandwidth is strictly determinative. Capping from 175G Native down to 10G causes up to an <b>8x to 9x latency penalty</b> on multi-node rings.</p>
        </div>
      `;
    }} else if (sel === 'compare') {{
      document.getElementById(coll + '_chart1_title').innerText = coll.toUpperCase() + ' Latency Comparison: Multi-Node vs Local Baselines (ms)';
      document.getElementById(coll + '_chart2_title').innerText = coll.toUpperCase() + ' Algorithmic Bandwidth Comparison';

      chart1Datasets.push({{ label: 'TP=4 Socket-Local (NUMA0)', data: allSizes.map(s => data.tp4_local[s] ? (data.tp4_local[s].time_us / 1000) : 0), borderColor: '#10b981', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=8 Node-Local (PCIe)', data: allSizes.map(s => data.tp8_local[s] ? (data.tp8_local[s].time_us / 1000) : 0), borderColor: '#3b82f6', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=4 Multi-Node (175G)', data: allSizes.map(s => data.tp4.NATIVE[s] ? (data.tp4.NATIVE[s].time_us / 1000) : 0), borderColor: '#f59e0b', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=8 Multi-Node (175G)', data: allSizes.map(s => data.tp8.NATIVE[s] ? (data.tp8.NATIVE[s].time_us / 1000) : 0), borderColor: '#8b5cf6', tension: 0.2 }});
      chart1Datasets.push({{ label: 'TP=16 Multi-Node (175G)', data: allSizes.map(s => data.tp16.NATIVE[s] ? data.tp16.NATIVE[s].time_us / 1000 : 0), borderColor: '#06b6d4', tension: 0.2 }});

      chart2Datasets.push({{ label: 'TP=4 Local', data: allSizes.map(s => data.tp4_local[s] ? data.tp4_local[s].algbw_gb_s : 0), backgroundColor: '#10b981' }});
      chart2Datasets.push({{ label: 'TP=8 Local', data: allSizes.map(s => data.tp8_local[s] ? data.tp8_local[s].algbw_gb_s : 0), backgroundColor: '#3b82f6' }});
      chart2Datasets.push({{ label: 'TP=16 Multi-Node (175G)', data: allSizes.map(s => data.tp16.NATIVE[s] ? data.tp16.NATIVE[s].algbw_gb_s : 0), backgroundColor: '#06b6d4' }});

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

    // Charts
    const ctx1 = document.getElementById(coll + '_chartLatency').getContext('2d');
    chartInstances[coll + '_lat'] = new Chart(ctx1, {{
      type: 'line',
      data: {{ labels: labels, datasets: chart1Datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Payload Buffer Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: 'Latency (Milliseconds - Log Scale)', color: '#94a3b8' }},
            grid: {{ color: 'rgba(255,255,255,0.05)' }},
            ticks: {{ callback: v => Number(v).toFixed(v < 1 ? 2 : 0) + ' ms' }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }},
          tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + (ctx.parsed.y < 1 ? ctx.parsed.y.toFixed(3) : ctx.parsed.y.toFixed(2)) + ' ms' }} }}
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
          x: {{ title: {{ display: true, text: 'Buffer Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{ title: {{ display: true, text: 'Algorithmic Bandwidth (GB/s)', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }} }}
      }}
    }});
  }}

  function tpLabel(sel) {{
    return (sel === 'tp16') ? 'TP=16' : ((sel === 'tp8') ? 'TP=8' : ((sel === 'tp4') ? 'TP=4' : 'TP'));
  }}

  // Render Tab 5: Multi-Node vs. Local Deep Dive
  function renderTab5View() {{
    const topo = document.getElementById('tab5_topoSelect').value;
    const coll = document.getElementById('tab5_collSelect').value;
    const data = benchData[coll];

    let localKey = 'tp8_local';
    let localLabel = 'TP=8 Local (Node-Local Dual-Socket PCIe)';
    let multiKey = 'tp16';
    let multiLabel = 'TP=16 Multi-Node (16 GPUs Across 2 Nodes)';
    let csvFileName = 'tp16_vs_tp8_local_' + coll + '_comparison.csv';
    let reportFileName = 'TP16_VS_TP8_LOCAL_' + coll.toUpperCase() + '_REPORT.md';
    let fileKey = 'tp16_vs_tp8_local_' + coll;
    let reportKey = 'TP16_VS_TP8_LOCAL_' + coll.toUpperCase() + '_REPORT';

    if (topo === 'tp8_multi_vs_local') {{
      localKey = 'tp8_local';
      localLabel = 'TP=8 Local (Node-Local Dual-Socket PCIe)';
      multiKey = 'tp8';
      multiLabel = 'TP=8 Multi-Node (4+4 GPUs Across 2 Nodes)';
      csvFileName = 'tp8_multinode_vs_local_' + coll + '_comparison.csv';
      reportFileName = 'TP8_AND_TP4_LOCAL_VS_MULTINODE_REPORT.md';
      fileKey = 'tp8_multinode_vs_local_' + coll;
      reportKey = 'TP8_AND_TP4_LOCAL_VS_MULTINODE_REPORT';
    }} else if (topo === 'tp4_multi_vs_local') {{
      localKey = 'tp4_local';
      localLabel = 'TP=4 Local (Socket-Local NUMA0 Zero-UPI)';
      multiKey = 'tp4';
      multiLabel = 'TP=4 Multi-Node (2+2 GPUs Across 2 Nodes)';
      csvFileName = 'tp4_multinode_vs_local_' + coll + '_comparison.csv';
      reportFileName = 'TP8_AND_TP4_LOCAL_VS_MULTINODE_REPORT.md';
      fileKey = 'tp4_multinode_vs_local_' + coll;
      reportKey = 'TP8_AND_TP4_LOCAL_VS_MULTINODE_REPORT';
    }}

    // 1. Download Quick Bar
    document.getElementById('tab5_downloadBar').innerHTML = `
      <a href="${{csvFileName}}" download class="btn-download" style="background:#10b981; font-size:12px;">Download ${{csvFileName}} &darr;</a>
      <a href="${{reportFileName}}" download class="btn-download" style="background:#8b5cf6; font-size:12px;">Download Report (${{reportFileName}}) &darr;</a>
      <button onclick="openFileViewer('${{fileKey}}')" class="btn-preview" style="font-size:12px;">Preview CSV Table &equiv;</button>
      <button onclick="openFileViewer('${{reportKey}}')" class="btn-preview" style="font-size:12px;">Read Full Report &equiv;</button>
      <a href="tp8_and_tp4_local_vs_multinode_comparison_master.csv" download class="btn-preview" style="border-color:var(--accent-cyan); color:var(--accent-cyan); font-size:12px;">Master 90-Row CSV &darr;</a>
    `;

    // 2. Data mappings
    const localData = data[localKey];
    const multiData = data[multiKey];
    const allSizes = Object.keys(multiData.NATIVE).map(Number).sort((a,b)=>a-b);
    const labels = allSizes.map(formatSize);

    // 3. KPIs for 16K, 1M, 128M, 256M
    function getKpi(sizeBytes, name) {{
      const locT = localData[sizeBytes] ? (localData[sizeBytes].time_us / 1000) : 0;
      const natT = multiData.NATIVE[sizeBytes] ? (multiData.NATIVE[sizeBytes].time_us / 1000) : 0;
      const cap10T = multiData['10'][sizeBytes] ? (multiData['10'][sizeBytes].time_us / 1000) : 0;
      const slow175 = locT > 0 ? (natT / locT).toFixed(1) + 'x' : '-';
      const slow10 = locT > 0 ? (cap10T / locT).toFixed(1) + 'x' : '-';
      return `
        <div class="kpi-card">
          <div class="kpi-title">${{name}} (${{formatSize(sizeBytes)}})</div>
          <div class="kpi-val">${{formatMs(natT)}} <span style="font-size:13px; color:var(--accent-green); font-weight:600;">(vs ${{formatMs(locT)}} loc)</span></div>
          <div class="kpi-sub">
            <span>175G Slowdown: <b>${{slow175}}</b></span>
            <span>10G Cap: <b style="color:var(--accent-red);">${{slow10}}</b></span>
          </div>
        </div>
      `;
    }}

    document.getElementById('tab5_kpis').innerHTML = 
      getKpi(16384, 'Batch-1 Decode Token') +
      getKpi(1048576, 'Activation Tensor') +
      getKpi(134217728, '8K Prefill Chunk') +
      getKpi(268435456, 'Large Prefill');

    // 4. Charts
    if (chartInstances['tab5_lat']) chartInstances['tab5_lat'].destroy();
    if (chartInstances['tab5_bw']) chartInstances['tab5_bw'].destroy();

    document.getElementById('tab5_chart1_title').innerText = `${{coll.toUpperCase()}} Latency: ${{localLabel}} vs ${{multiLabel}} (ms)`;
    document.getElementById('tab5_chart2_title').innerText = `${{coll.toUpperCase()}} Algorithmic Bandwidth Comparison (GB/s)`;

    let chart1Datasets = [
      {{
        label: 'Local Baseline (' + (localKey === 'tp8_local' ? 'Node-Local PCIe' : 'Socket NUMA0') + ')',
        data: allSizes.map(s => localData[s] ? (localData[s].time_us / 1000) : 0),
        borderColor: '#a855f7',
        borderWidth: 3,
        borderDash: [6, 4],
        tension: 0.2
      }},
      {{
        label: 'Multi-Node 175G Native',
        data: allSizes.map(s => multiData.NATIVE[s] ? (multiData.NATIVE[s].time_us / 1000) : 0),
        borderColor: '#10b981',
        tension: 0.2
      }},
      {{
        label: 'Multi-Node 100G Capped',
        data: allSizes.map(s => multiData['100'][s] ? (multiData['100'][s].time_us / 1000) : 0),
        borderColor: '#3b82f6',
        tension: 0.2
      }},
      {{
        label: 'Multi-Node 50G Capped',
        data: allSizes.map(s => multiData['50'][s] ? (multiData['50'][s].time_us / 1000) : 0),
        borderColor: '#f59e0b',
        tension: 0.2
      }},
      {{
        label: 'Multi-Node 20G Capped',
        data: allSizes.map(s => multiData['20'][s] ? (multiData['20'][s].time_us / 1000) : 0),
        borderColor: '#f97316',
        tension: 0.2
      }},
      {{
        label: 'Multi-Node 10G Capped',
        data: allSizes.map(s => multiData['10'][s] ? (multiData['10'][s].time_us / 1000) : 0),
        borderColor: '#ef4444',
        tension: 0.2
      }}
    ];

    const ctx1 = document.getElementById('tab5_chartLatency').getContext('2d');
    chartInstances['tab5_lat'] = new Chart(ctx1, {{
      type: 'line',
      data: {{ labels: labels, datasets: chart1Datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Payload Buffer Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: 'Latency (Milliseconds - Log Scale)', color: '#94a3b8' }},
            grid: {{ color: 'rgba(255,255,255,0.05)' }},
            ticks: {{ callback: v => Number(v).toFixed(v < 1 ? 2 : 0) + ' ms' }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }},
          tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + (ctx.parsed.y < 1 ? ctx.parsed.y.toFixed(3) : ctx.parsed.y.toFixed(2)) + ' ms' }} }}
        }}
      }}
    }});

    const highSizes = [16777216, 33554432, 67108864, 134217728, 268435456];
    const ctx2 = document.getElementById('tab5_chartBandwidth').getContext('2d');
    chartInstances['tab5_bw'] = new Chart(ctx2, {{
      type: 'bar',
      data: {{
        labels: ['16M', '32M', '64M', '128M', '256M'],
        datasets: [
          {{ label: 'Local Baseline', data: highSizes.map(s => localData[s] ? localData[s].algbw_gb_s : 0), backgroundColor: '#a855f7' }},
          {{ label: 'Multi 175G Native', data: highSizes.map(s => multiData.NATIVE[s] ? multiData.NATIVE[s].algbw_gb_s : 0), backgroundColor: '#10b981' }},
          {{ label: 'Multi 100G', data: highSizes.map(s => multiData['100'][s] ? multiData['100'][s].algbw_gb_s : 0), backgroundColor: '#3b82f6' }},
          {{ label: 'Multi 50G', data: highSizes.map(s => multiData['50'][s] ? multiData['50'][s].algbw_gb_s : 0), backgroundColor: '#f59e0b' }},
          {{ label: 'Multi 20G', data: highSizes.map(s => multiData['20'][s] ? multiData['20'][s].algbw_gb_s : 0), backgroundColor: '#f97316' }},
          {{ label: 'Multi 10G', data: highSizes.map(s => multiData['10'][s] ? multiData['10'][s].algbw_gb_s : 0), backgroundColor: '#ef4444' }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Payload Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{ title: {{ display: true, text: 'Algorithmic Bandwidth (GB/s)', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }} }}
      }}
    }});

    // 5. Comparison Table
    document.getElementById('tab5_table_title').innerText = `${{coll.toUpperCase()}} Empirical Benchmarks: ${{localLabel}} vs ${{multiLabel}}`;
    
    let tableHtml = `<table>
      <thead>
        <tr>
          <th>Payload</th><th>Milestone</th>
          <th>Local Latency (ms)</th><th>Local AlgBW (GB/s)</th>
          <th>Multi 175G (ms)</th><th>Multi 100G (ms)</th><th>Multi 50G (ms)</th><th>Multi 20G (ms)</th><th>Multi 10G (ms)</th>
          <th>175G vs Local</th><th>10G vs Local</th>
        </tr>
      </thead>
      <tbody>` +
      allSizes.map(s => {{
        const tLoc = localData[s] ? (localData[s].time_us / 1000) : 0;
        const bwLoc = localData[s] ? localData[s].algbw_gb_s.toFixed(2) : '-';
        const tNat = multiData.NATIVE[s] ? (multiData.NATIVE[s].time_us / 1000) : 0;
        const t100 = multiData['100'][s] ? (multiData['100'][s].time_us / 1000) : 0;
        const t50 = multiData['50'][s] ? (multiData['50'][s].time_us / 1000) : 0;
        const t20 = multiData['20'][s] ? (multiData['20'][s].time_us / 1000) : 0;
        const t10 = multiData['10'][s] ? (multiData['10'][s].time_us / 1000) : 0;
        const slowNat = tLoc > 0 ? (tNat / tLoc).toFixed(2) + 'x' : '-';
        const slow10 = tLoc > 0 ? (t10 / tLoc).toFixed(2) + 'x' : '-';
        return `<tr>
          <td><b>${{formatSize(s)}}</b></td>
          <td>${{getHumanLabel(s)}}</td>
          <td class="highlight-green">${{formatMs(tLoc)}}</td>
          <td>${{bwLoc}}</td>
          <td>${{formatMs(tNat)}}</td>
          <td>${{formatMs(t100)}}</td>
          <td>${{formatMs(t50)}}</td>
          <td>${{formatMs(t20)}}</td>
          <td>${{formatMs(t10)}}</td>
          <td class="highlight-green"><b>${{slowNat}}</b></td>
          <td class="${{parseFloat(slow10) > 10 ? 'highlight-red' : 'highlight-amber'}}"><b>${{slow10}}</b></td>
        </tr>`;
      }}).join('') + `</tbody></table>`;

    document.getElementById('tab5_tableContainer').innerHTML = tableHtml;

    // 6. Insights
    document.getElementById('tab5_insights').innerHTML = `
      <div class="card">
        <div class="card-header"><h3>Network Crossing Penalty: Small vs Large Payloads</h3><span class="badge badge-hw">KEY FINDING</span></div>
        <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">
          Crossing the multi-node boundary imposes a <b>~6x to 10x latency floor</b> for small decode packets (16 KiB token decode takes <b>~0.016 - 0.028 ms</b> locally vs <b>~0.20 - 0.27 ms</b> over multi-node TCP).
          However, for massive 256 MiB prefill payloads on unthrottled 175G fabric, the multi-node overhead remains constrained to <b>~2.5x - 2.9x</b>.
        </p>
      </div>
      <div class="card">
        <div class="card-header"><h3>Bandwidth Throttling Sensitivity</h3><span class="badge badge-hw">BANDWIDTH BOUND</span></div>
        <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">
          Restricting VPC network egress from 175G down to 10G has virtually zero impact on token decode times (&lt;5% difference), but causes an astronomical <b>21x to 23x slowdown</b> on prefill chunks (jumping from ~18 ms local to over <b>421 ms</b> on 10G multi-node AllReduce).
        </p>
      </div>
    `;
  }}

  // Render Tab 6: Files & Deliverables Hub
  let currentFilter = 'all';
  let searchQuery = '';

  function renderArtifactsHub() {{
    const grid = document.getElementById('artifactsGrid');
    const filtered = filesList.filter(f => {{
      const matchCat = (currentFilter === 'all') || (f.category === currentFilter);
      const q = searchQuery.toLowerCase();
      const matchSearch = !q || f.title.toLowerCase().includes(q) || f.filename.toLowerCase().includes(q) || f.collective.toLowerCase().includes(q) || f.desc.toLowerCase().includes(q);
      return matchCat && matchSearch;
    }});

    grid.innerHTML = filtered.map(f => {{
      const extClass = 'ext-' + f.type;
      return `
        <div class="file-card">
          <div class="file-top">
            <div class="file-badge-group">
              <span class="file-ext ${{extClass}}">${{f.type.toUpperCase()}}</span>
              <span class="badge badge-hw">${{f.collective}}</span>
            </div>
            <span style="font-size:11px; color:var(--text-muted); font-weight:600;">${{f.size}}</span>
          </div>
          <div class="file-title">${{f.title}}</div>
          <div class="file-name">${{f.filename}}</div>
          <div class="file-desc">${{f.desc}}</div>
          <div class="file-actions">
            <a href="${{f.filename}}" download class="btn-download">Download &darr;</a>
            <button onclick="openFileViewer('${{f.id}}')" class="btn-preview">Preview &equiv;</button>
          </div>
        </div>
      `;
    }}).join('');
  }}

  function filterArtifacts(cat) {{
    currentFilter = cat;
    document.querySelectorAll('.filter-pill').forEach(b => {{
      b.classList.toggle('active', b.innerText.toLowerCase().includes(cat) || (cat === 'all' && b.innerText.includes('All')));
    }});
    renderArtifactsHub();
  }}

  function searchArtifacts(val) {{
    searchQuery = val;
    renderArtifactsHub();
  }}

  // File Viewer Modal Logic
  let activeModalContent = '';

  function openFileViewer(fileId) {{
    const fileMeta = filesList.find(f => f.id === fileId);
    if (!fileMeta) return;

    const modal = document.getElementById('fileModal');
    const title = document.getElementById('modalTitle');
    const subtitle = document.getElementById('modalSubtitle');
    const extBadge = document.getElementById('modalExtBadge');
    const body = document.getElementById('modalBody');
    const dlBtn = document.getElementById('modalDlBtn');

    title.innerText = fileMeta.title;
    subtitle.innerText = fileMeta.filename + ' (' + fileMeta.size + ')';
    extBadge.className = 'file-ext ext-' + fileMeta.type;
    extBadge.innerText = fileMeta.type.toUpperCase();
    dlBtn.href = fileMeta.filename;

    const content = embeddedFiles[fileId];
    activeModalContent = content || '';

    if (fileMeta.type === 'csv' && content) {{
      body.innerHTML = renderCsvTable(content);
    }} else if (fileMeta.type === 'md' && content) {{
      body.innerHTML = renderMarkdown(content);
    }} else if (fileMeta.type === 'tgz') {{
      body.innerHTML = renderTgzDetails(fileMeta);
    }} else if (fileMeta.type === 'json' && content) {{
      body.innerHTML = `<pre style="background:rgba(0,0,0,0.4); padding:16px; border-radius:8px; overflow:auto; color:#93c5fd; font-family:monospace; font-size:12px;">${{escapeHtml(JSON.stringify(JSON.parse(content), null, 2))}}</pre>`;
    }} else {{
      body.innerHTML = `<p style="color:var(--text-muted);">Content preview not available. Please use download button.</p>`;
    }}

    modal.classList.add('active');
  }}

  function closeFileModal() {{
    document.getElementById('fileModal').classList.remove('active');
  }}

  function closeModalOnBackdrop(e) {{
    if (e.target.id === 'fileModal') closeFileModal();
  }}

  function copyModalContent() {{
    if (!activeModalContent) return;
    navigator.clipboard.writeText(activeModalContent).then(() => {{
      const btn = document.getElementById('modalCopyBtn');
      btn.innerText = 'Copied!';
      btn.style.borderColor = 'var(--accent-green)';
      btn.style.color = 'var(--accent-green)';
      setTimeout(() => {{
        btn.innerText = 'Copy Content';
        btn.style.borderColor = 'var(--border)';
        btn.style.color = '#e2e8f0';
      }}, 2000);
    }});
  }}

  function escapeHtml(str) {{
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }}

  function renderCsvTable(csvText) {{
    const lines = csvText.trim().split('\\n');
    if (lines.length === 0) return '<p>Empty CSV</p>';
    
    const headers = lines[0].split(',').map(h => h.trim());
    const rows = lines.slice(1).map(l => l.split(',').map(c => c.trim()));

    let th = headers.map(h => `<th style="padding:10px 12px; border:1px solid var(--border); background:rgba(30,41,59,0.9); color:var(--accent-cyan); font-weight:700; position:sticky; top:0;">${{h}}</th>`).join('');
    let tb = rows.map((r, ri) => {{
      let td = r.map((c, ci) => {{
        let isSlowdown = headers[ci] && headers[ci].includes('vs');
        let clr = isSlowdown && parseFloat(c) > 5 ? 'var(--accent-red)' : (ci === 0 ? '#fff' : 'var(--text-muted)');
        return `<td style="padding:8px 12px; border:1px solid var(--border); background:${{ri % 2 === 0 ? 'rgba(15,23,42,0.5)' : 'rgba(30,41,59,0.3)'}}; color:${{clr}};">${{c}}</td>`;
      }}).join('');
      return `<tr>${{td}}</tr>`;
    }}).join('');

    return `
      <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
        <span class="badge badge-hw">${{rows.length}} Rows &bull; ${{headers.length}} Columns</span>
        <span style="font-size:12px; color:var(--text-muted);">Empirical Hardware Dataset</span>
      </div>
      <div style="overflow:auto; max-height:72vh; border:1px solid var(--border); border-radius:8px;">
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
          <thead><tr>${{th}}</tr></thead>
          <tbody>${{tb}}</tbody>
        </table>
      </div>
    `;
  }}

  function renderMarkdown(md) {{
    let html = escapeHtml(md);

    // Markdown tables
    const lines = html.split('\\n');
    let inTable = false;
    let tableLines = [];
    let newLines = [];

    for (let i = 0; i < lines.length; i++) {{
      const line = lines[i].trim();
      if (line.startsWith('|') && line.endsWith('|')) {{
        inTable = true;
        tableLines.push(line);
      }} else {{
        if (inTable) {{
          newLines.push(formatMdTable(tableLines));
          inTable = false;
          tableLines = [];
        }}
        newLines.push(lines[i]);
      }}
    }}
    if (inTable) newLines.push(formatMdTable(tableLines));
    html = newLines.join('\\n');

    // Headers
    html = html.replace(/^#### (.*$)/gim, '<h4 style="color:var(--accent-cyan); font-size:14px; margin:16px 0 6px;">$1</h4>');
    html = html.replace(/^### (.*$)/gim, '<h3 style="color:#fff; font-size:16px; margin:20px 0 8px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:4px;">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 style="color:var(--accent-cyan); font-size:18px; margin:24px 0 10px; border-bottom:1px solid var(--border); padding-bottom:6px;">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 style="color:#fff; font-size:22px; margin:26px 0 14px; border-bottom:2px solid var(--accent-blue); padding-bottom:8px;">$1</h1>');

    // Bold & italic
    html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<b style="color:#fff;">$1</b>');
    html = html.replace(/\\*(.*?)\\*/g, '<i style="color:var(--text-muted);">$1</i>');

    // Math callouts
    html = html.replace(/\\$\\$(.*?)\\$\\$/g, '<div style="background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.3); border-radius:6px; padding:10px 14px; margin:12px 0; font-family:monospace; color:#93c5fd;">$1</div>');

    // Rules & bullets
    html = html.replace(/^---$/gim, '<hr style="border:none; border-top:1px solid var(--border); margin:20px 0;">');
    html = html.replace(/^\\- (.*$)/gim, '<li style="margin-left:20px; margin-bottom:4px; color:var(--text-muted);">$1</li>');

    return `<div style="max-width:1000px; margin:0 auto;">${{html}}</div>`;
  }}

  function formatMdTable(lines) {{
    if (lines.length < 2) return lines.join('<br>');
    const headers = lines[0].split('|').filter((c, i, a) => i > 0 && i < a.length - 1).map(c => c.trim());
    let rows = [];
    for (let i = 2; i < lines.length; i++) {{
      const cells = lines[i].split('|').filter((c, idx, a) => idx > 0 && idx < a.length - 1).map(c => c.trim());
      rows.push(cells);
    }}
    let th = headers.map(h => `<th style="padding:10px; border:1px solid var(--border); background:rgba(30,41,59,0.9); color:var(--accent-cyan); font-weight:700;">${{h}}</th>`).join('');
    let tb = rows.map((r, ri) => {{
      let td = r.map((c, ci) => {{
        let clr = c.includes('x') && parseFloat(c) > 5 ? 'var(--accent-red)' : (ci === 0 ? '#fff' : 'var(--text-muted)');
        return `<td style="padding:8px 10px; border:1px solid var(--border); background:${{ri % 2 === 0 ? 'rgba(15,23,42,0.4)' : 'rgba(30,41,59,0.2)'}}; color:${{clr}};">${{c}}</td>`;
      }}).join('');
      return `<tr>${{td}}</tr>`;
    }}).join('');
    return `<div style="overflow-x:auto; margin:16px 0; border:1px solid var(--border); border-radius:8px;"><table style="width:100%; border-collapse:collapse; font-size:12px;"><thead><tr>${{th}}</tr></thead><tbody>${{tb}}</tbody></table></div>`;
  }}

  function renderTgzDetails(meta) {{
    return `
      <div style="background:rgba(15,23,42,0.6); border:1px solid var(--border); border-radius:10px; padding:20px; max-width:800px; margin:0 auto;">
        <h3 style="color:#fff; margin-bottom:12px;">Raw Live Telemetry Archive</h3>
        <p style="color:var(--text-muted); margin-bottom:16px;">This archive contains all raw execution logs, stdout/stderr streams, and network verification outputs recorded directly during the live runs on <code>kimi-node-0</code> and <code>kimi-node-1</code>.</p>
        
        <table style="width:100%; font-size:12px; margin-bottom:20px;">
          <tr><td style="color:var(--text-muted); width:140px;">Filename:</td><td><b>${{meta.filename}}</b></td></tr>
          <tr><td style="color:var(--text-muted);">Compressed Size:</td><td>${{meta.size}}</td></tr>
          <tr><td style="color:var(--text-muted);">Verification SHA256:</td><td style="font-family:monospace; color:var(--accent-cyan); font-size:11px;">${{meta.sha256}}</td></tr>
          <tr><td style="color:var(--text-muted);">Status:</td><td><span class="badge badge-hw">100% REAL VM HARDWARE LOGS</span></td></tr>
        </table>

        <div style="background:#0b0f19; border:1px solid var(--border); border-radius:6px; padding:12px; margin-bottom:16px;">
          <div style="font-size:11px; color:var(--text-muted); margin-bottom:4px;">Extract Command (Linux/macOS/WSL):</div>
          <code style="color:var(--accent-green); font-size:12px;">tar -xzvf ${{meta.filename}}</code>
        </div>

        <a href="${{meta.filename}}" download class="btn-download" style="display:inline-flex; width:auto;">Download Raw Archive (${{meta.size}}) &darr;</a>
      </div>
    `;
  }}

  window.addEventListener('DOMContentLoaded', () => {{
    renderCollectiveView('allreduce');
  }});
</script>
"""

full_html = header_and_tab1 + "\n" + tab2_html + "\n" + tab3_html + "\n" + tab4_html + "\n" + tab5_html + "\n" + tab6_html + "\n" + script_js + "\n</body>\n</html>"

with open(html_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"Successfully generated full interactive dashboard HTML! Size: {len(full_html):,} bytes")
