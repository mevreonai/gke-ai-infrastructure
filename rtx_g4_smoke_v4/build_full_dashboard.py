import os, json

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results"
json_path = os.path.join(base_dir, "fresh_benchmark_suite", "master_benchmarks.json")
html_path = os.path.join(base_dir, "v4_interactive_dashboards.html")

with open(json_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

# Read existing HTML up to line 297 (end of Tab 1)
with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

header_and_tab1 = "".join(lines[:297])

# Ensure Panel 3 mentions fresh ms numbers
header_and_tab1 = header_and_tab1.replace("16K = 425 µs, 256M = 5.04 ms.", "16 KiB = 0.14 ms, 256 MiB = 60.5 ms.")

# Replace header navigation buttons if not already updated
old_header_tabs = """  <div class="tabs">
    <button class="tab-btn active" onclick="showTab(1)">Dashboard 1: 9-Panel Decomposition</button>
    <button class="tab-btn" onclick="showTab(2)">Dashboard 2: 3-Pair AllReduce Deep Dive</button>
    <button class="tab-btn" onclick="showTab(3)">Dashboard 3: AllReduce Bandwidth Sweep (10G-175G)</button>
    <button class="tab-btn" onclick="showTab(4)">Dashboard 4: Pipeline Calculator & Fabric</button>
  </div>"""

new_header_tabs = """  <div class="tabs">
    <button class="tab-btn active" onclick="showTab(1)">Dashboard 1: 9-Panel Infographic</button>
    <button class="tab-btn" onclick="showTab(2)">Dashboard 2: AllReduce Suite</button>
    <button class="tab-btn" onclick="showTab(3)">Dashboard 3: AllGather Suite</button>
    <button class="tab-btn" onclick="showTab(4)">Dashboard 4: ReduceScatter Suite</button>
  </div>"""

header_and_tab1 = header_and_tab1.replace(old_header_tabs, new_header_tabs)

# Function to build Tabs 2, 3, and 4
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
  <div id="{coll_key}_downloadBar" style="margin-bottom: 18px; display: flex; gap: 10px; flex-wrap: wrap;"></div>

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

# Javascript logic for rendering charts, tables, and dropdowns (in milliseconds)
script_js = f"""
<script>
  const benchData = {json.dumps(bench_data)};

  function showTab(n) {{
    document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', i === n - 1));
    document.querySelectorAll('.tab-content').forEach((c, i) => c.classList.toggle('active', i === n - 1));
    if (n === 2) renderCollectiveView('allreduce');
    if (n === 3) renderCollectiveView('allgather');
    if (n === 4) renderCollectiveView('reducescatter');
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

    // 1. Render Dynamic Download Links based on selected TP
    let currentTpKey = (sel === 'compare') ? 'tp16' : sel;
    let tpLabel = (sel === 'tp16') ? 'TP=16' : ((sel === 'tp8') ? 'TP=8' : ((sel === 'tp4') ? 'TP=4' : 'TP'));
    
    let dlHtml = `
      <a href="fresh_benchmark_suite/${{coll}}/${{coll}}_${{currentTpKey}}_sweep.csv" style="background:rgba(59,130,246,0.2); border:1px solid #3b82f6; color:#93c5fd; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">${{tpLabel}} Full Sweep CSV &darr;</a>
      <a href="fresh_benchmark_suite/${{coll}}/${{coll}}_${{currentTpKey}}_175g_native.csv" style="background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#34d399; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">175G Native CSV &darr;</a>
      <a href="fresh_benchmark_suite/${{coll}}/${{coll}}_${{currentTpKey}}_100g.csv" style="background:rgba(255,255,255,0.06); border:1px solid var(--border); color:#fff; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">100G CSV &darr;</a>
      <a href="fresh_benchmark_suite/${{coll}}/${{coll}}_${{currentTpKey}}_50g.csv" style="background:rgba(255,255,255,0.06); border:1px solid var(--border); color:#fff; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">50G CSV &darr;</a>
      <a href="fresh_benchmark_suite/${{coll}}/${{coll}}_${{currentTpKey}}_20g.csv" style="background:rgba(255,255,255,0.06); border:1px solid var(--border); color:#fff; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">20G CSV &darr;</a>
      <a href="fresh_benchmark_suite/${{coll}}/${{coll}}_${{currentTpKey}}_10g.csv" style="background:rgba(239,68,68,0.2); border:1px solid #ef4444; color:#fca5a5; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">10G CSV &darr;</a>
    `;
    if (sel === 'tp8' || sel === 'compare') {{
      dlHtml += `<a href="fresh_benchmark_suite/${{coll}}/${{coll}}_tp8_node_local.csv" style="background:rgba(139,92,246,0.2); border:1px solid #8b5cf6; color:#c4b5fd; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">TP=8 Local PCIe CSV &darr;</a>`;
    }}
    if (sel === 'tp4' || sel === 'compare') {{
      dlHtml += `<a href="fresh_benchmark_suite/${{coll}}/${{coll}}_tp4_socket_local.csv" style="background:rgba(236,72,153,0.2); border:1px solid #ec4899; color:#fbcfe8; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; text-decoration:none;">TP=4 Socket-Local NUMA CSV &darr;</a>`;
    }}
    dlBar.innerHTML = dlHtml;

    // 2. Prepare Data Points
    const allSizes = Object.keys(data.tp16.NATIVE).map(Number).sort((a,b)=>a-b);
    const labels = allSizes.map(formatSize);

    // Chart Destroy helper
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

      // Add local baseline line for comparison if TP=8 or TP=4
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

      // Bandwidth Chart (for high payload sizes)
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
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">For small decode payloads (8K - 512K), multi-node ${{tpLabel}} latency remains bounded at <b>~0.11 ms to 0.18 ms</b>. Linux TCP socket synchronization sets the floor, meaning network bandwidth caps (10G vs 175G) have minimal latency impact until payload exceeds ~1 MiB.</p>
        </div>
        <div class="card">
          <div class="card-header"><h3>${{tpLabel}} Prefill Scalability (&beta;-bound)</h3><span class="badge badge-hw">64M - 256M</span></div>
          <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">At 256 MiB, the physical network link is the dominant bottleneck. Throttling from 175G Native (~50 ms) down to 10G Capped (~390 ms) causes a <b>~7.5x - 8x slowdown</b>, demonstrating why high-bandwidth interconnects are vital for multi-node LLM serving.</p>
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

    // Render Table
    tableContainer.innerHTML = tableHtml;

    // Render Latency Chart (Log scale in ms)
    const ctx1 = document.getElementById(coll + '_chartLatency').getContext('2d');
    chartInstances[coll + '_lat'] = new Chart(ctx1, {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: chart1Datasets
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'Payload Buffer Size', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: 'Latency (Milliseconds - Log Scale)', color: '#94a3b8' }},
            grid: {{ color: 'rgba(255,255,255,0.05)' }},
            ticks: {{
              callback: function(value) {{
                return Number(value).toFixed(value < 1 ? 2 : 0) + ' ms';
              }}
            }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#e2e8f0', boxWidth: 12 }} }},
          tooltip: {{
            callbacks: {{
              label: function(ctx) {{
                const v = ctx.parsed.y;
                return ctx.dataset.label + ': ' + (v < 1 ? v.toFixed(3) : v.toFixed(2)) + ' ms';
              }}
            }}
          }}
        }}
      }}
    }});

    // Render Bandwidth Chart
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

  // Initialize Tab 2 on page load
  window.addEventListener('DOMContentLoaded', () => {{
    renderCollectiveView('allreduce');
  }});
</script>
"""

full_html = header_and_tab1 + "\n" + tab2_html + "\n" + tab3_html + "\n" + tab4_html + "\n" + script_js + "\n</body>\n</html>"

with open(html_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print("Successfully updated dashboard to milliseconds across all charts, tables, tooltips, and badges!")
