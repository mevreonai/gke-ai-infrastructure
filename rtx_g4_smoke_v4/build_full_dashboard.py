import os, json, re

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results"
json_path = os.path.join(base_dir, "master_benchmarks_all_collectives.json")
html_path = os.path.join(base_dir, "v4_interactive_dashboards.html")

with open(json_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

# Read HTML lines up to line 297 (end of Tab 1: 9-Panel Infographic)
with open(html_path, "r", encoding="utf-8") as f:
    raw_lines = f.readlines()

header_and_tab1 = "".join(raw_lines[:297])

expected_header_tabs = """  <div class="tabs">
    <button class="tab-btn active" onclick="showTab(1)">Dashboard 1: 9-Panel Infographic</button>
    <button class="tab-btn" onclick="showTab(2)">Dashboard 2: AllReduce</button>
    <button class="tab-btn" onclick="showTab(3)">Dashboard 3: AllGather</button>
    <button class="tab-btn" onclick="showTab(4)">Dashboard 4: ReduceScatter</button>
    <button class="tab-btn" onclick="showTab(5)">Dashboard 5: AllToAll</button>
    <button class="tab-btn" onclick="showTab(6)">Dashboard 6: SendRecv (P2P)</button>
  </div>"""

header_and_tab1 = re.sub(r'<div class="tabs">[\s\S]*?<\/div>', expected_header_tabs, header_and_tab1, count=1)

# Function to build Tabs 2, 3, 4, 5
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

# Function to build Tab 6: SendRecv
def build_sendrecv_tab():
    return """
<!-- TAB 6: SendRecv Suite -->
<div id="tab6" class="tab-content">
  <!-- Controls Bar -->
  <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
    <div>
      <h2 style="font-size: 18px; color: #fff; font-weight: 700; margin-bottom: 3px;">2-Node Point-to-Point (Send/Recv) Characterization</h2>
      <p style="font-size: 13px; color: var(--text-muted);">Measured live: Rank 0 on Node 0 &rarr; Rank 1 on Node 1 across 5 network bandwidth tiers vs Intra-Node Local Baselines.</p>
    </div>
    <div style="display: flex; gap: 10px;">
      <a href="sendrecv_2node_vs_local_comparison.csv" download style="background:rgba(16,185,129,0.3); border:1px solid #10b981; color:#fff; font-size:12px; font-weight:700; padding:8px 14px; border-radius:6px; text-decoration:none;">SendRecv Comparison CSV &darr;</a>
      <a href="SENDRECV_EXECUTIVE_REPORT.md" download style="background:rgba(139,92,246,0.3); border:1px solid #8b5cf6; color:#fff; font-size:12px; font-weight:700; padding:8px 14px; border-radius:6px; text-decoration:none;">Executive Report (.md) &darr;</a>
    </div>
  </div>

  <!-- Charts Row -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
    <div class="card">
      <div class="card-header">
        <h3>Point-to-Point Latency: 2-Node P2P vs Local Intra/Cross-NUMA (ms)</h3>
        <span class="badge badge-hw">LOG SCALE (ms)</span>
      </div>
      <div style="height: 270px;">
        <canvas id="sendrecv_chartLatency"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h3>Point-to-Point Algorithmic Bandwidth (GB/s)</h3>
        <span class="badge badge-hw">GB/s</span>
      </div>
      <div style="height: 270px;">
        <canvas id="sendrecv_chartBandwidth"></canvas>
      </div>
    </div>
  </div>

  <!-- Table Card -->
  <div class="card" style="margin-bottom: 20px;">
    <div class="card-header">
      <h3>Empirical P2P Benchmark Data Points (Latency in Milliseconds - ms)</h3>
      <span class="badge badge-hw">100% REAL VM MEASURED</span>
    </div>
    <div id="sendrecv_tableContainer" style="overflow-x: auto;"></div>
  </div>

  <!-- Insights -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
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
      'NATIVE': '#10b981',
      '100': '#3b82f6',
      '50': '#f59e0b',
      '20': '#f97316',
      '10': '#ef4444'
    }};

    let currentTpKey = (sel === 'compare') ? 'tp16' : sel;
    let tpLabel = (sel === 'tp16') ? 'TP=16' : ((sel === 'tp8') ? 'TP=8' : ((sel === 'tp4') ? 'TP=4' : 'TP'));
    
    let dlHtml = `
      <a href="tp16_vs_tp8_local_${{coll}}_comparison.csv" download style="background:rgba(16,185,129,0.3); border:1px solid #10b981; color:#fff; font-size:12px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">TP-16 vs TP-8 Local CSV &darr;</a>
      <a href="tp8_multinode_vs_local_${{coll}}_comparison.csv" download style="background:rgba(59,130,246,0.3); border:1px solid #3b82f6; color:#fff; font-size:12px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">TP-8 Multi vs Local CSV &darr;</a>
      <a href="tp4_multinode_vs_local_${{coll}}_comparison.csv" download style="background:rgba(236,72,153,0.3); border:1px solid #ec4899; color:#fff; font-size:12px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">TP-4 Multi vs Local CSV &darr;</a>
      <a href="${{coll.toUpperCase()}}_EXECUTIVE_REPORT.md" download style="background:rgba(139,92,246,0.3); border:1px solid #8b5cf6; color:#fff; font-size:12px; font-weight:700; padding:6px 12px; border-radius:6px; text-decoration:none;">Executive Report (.md) &darr;</a>
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
            ticks: {{ callback: function(value) {{ return Number(value).toFixed(value < 1 ? 2 : 0) + ' ms'; }} }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }},
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
          x: {{ title: {{ display: true, text: 'Buffer Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{ title: {{ display: true, text: 'Algorithmic Bandwidth (GB/s)', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }} }}
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
    const colors = {{ 'NATIVE': '#10b981', '100': '#3b82f6', '50': '#f59e0b', '20': '#f97316', '10': '#ef4444' }};

    let chart1Datasets = [];
    chart1Datasets.push({{
      label: 'Local Intra-NUMA (Same Socket)',
      data: allSizes.map(s => data.local_intra[s] ? (data.local_intra[s].time_us / 1000) : 0),
      borderColor: '#34d399',
      borderDash: [5, 5],
      tension: 0.2
    }});
    chart1Datasets.push({{
      label: 'Local Cross-NUMA (Inter-Socket)',
      data: allSizes.map(s => data.local_cross[s] ? (data.local_cross[s].time_us / 1000) : 0),
      borderColor: '#a855f7',
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
          x: {{ title: {{ display: true, text: 'Payload Buffer Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: 'Latency (Milliseconds - Log Scale)', color: '#94a3b8' }},
            grid: {{ color: 'rgba(255,255,255,0.05)' }},
            ticks: {{ callback: function(value) {{ return Number(value).toFixed(value < 1 ? 2 : 0) + ' ms'; }} }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }},
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
          x: {{ title: {{ display: true, text: 'Buffer Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{ title: {{ display: true, text: 'Algorithmic Bandwidth (GB/s)', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }} }}
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

  function initTab1Charts() {{
    const elWithinNode = document.getElementById('chartWithinNode');
    if (elWithinNode) {{
      new Chart(elWithinNode, {{
        type: 'bar',
        data: {{
          labels: ['16K Latency (µs)', '128M AlgBW (GB/s)'],
          datasets: [
            {{ label: 'TP4 (Single-NUMA)', data: [17.93, 26.00], backgroundColor: '#10b981' }},
            {{ label: 'TP8 (Cross-Socket)', data: [37.52, 22.79], backgroundColor: '#3b82f6' }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#9ca3af', font: {{ size: 10 }} }} }} }}, scales: {{ y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, x: {{ ticks: {{ color: '#9ca3af' }} }} }} }}
      }});
    }}
    const elComputeRoof = document.getElementById('chartComputeRoof');
    if (elComputeRoof) {{
      new Chart(elComputeRoof, {{
        type: 'bar',
        data: {{
          labels: ['BF16 TFLOPS', 'FP8 TFLOPS'],
          datasets: [
            {{ label: 'Measured Per-GPU Peak', data: [91.4, 715.2], backgroundColor: '#06b6d4' }},
            {{ label: 'Theoretical Spec Ceiling', data: [91.1, 729.0], backgroundColor: 'rgba(255,255,255,0.2)' }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#9ca3af', font: {{ size: 10 }} }} }} }}, scales: {{ y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, x: {{ ticks: {{ color: '#9ca3af' }} }} }} }}
      }});
    }}
  }}

  window.addEventListener('DOMContentLoaded', () => {{
    initTab1Charts();
  }});
</script>
</body>
</html>
"""

full_html = header_and_tab1 + "\n" + tab2_html + "\n" + tab3_html + "\n" + tab4_html + "\n" + tab5_html + "\n" + tab6_html + "\n" + script_js

with open(html_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"Interactive dashboard successfully generated at: {html_path}")
