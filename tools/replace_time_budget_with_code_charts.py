import json, os, re

dash_path = r"v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html"

with open("time_budget_data.json", "r", encoding="utf-8") as f:
    tb_data = json.load(f)

d1 = tb_data["d1"]
d2 = tb_data["d2"]
d3 = tb_data["d3"]
d4 = tb_data["d4"]

with open(dash_path, "r", encoding="utf-8") as f:
    html = f.read()

# Extract the 4 base64 image strings
pattern = r'<img src="(data:image/png;base64,[^"]+)"'
imgs = re.findall(pattern, html)
print(f"Found {len(imgs)} base64 images")
assert len(imgs) == 4, f"Expected 4 images, got {len(imgs)}"

# Locate the block containing the 4 image containers
start_marker = '<!-- Chart View 1: First Token Single Request -->'
end_marker = '<div class="grid2" style="gap:8px;margin-top:4px">'

start_pos = html.find(start_marker)
end_pos = html.find(end_marker)

assert start_pos != -1, "start_marker not found"
assert end_pos != -1, "end_marker not found"
assert start_pos < end_pos, "markers in wrong order"

new_containers_html = f'''<!-- Chart View 1: First Token Single Request -->
  <div id="budget-first-single-container" class="budget-view-container" style="display:block">
    <div style="background:rgba(0,0,0,0.35);padding:14px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:6px">
        <div>
          <div style="font-weight:700;color:var(--cyan);font-size:12px">⚡ Interactive 100% Stacked Wall-Time Budget — First Token (TTFT)</div>
          <div style="font-size:10px;color:var(--muted)">24 Operating Points · Prefill Kernels vs Collectives vs Queue vs Waits (Hover for exact duration &amp; split source)</div>
        </div>
        <div style="display:flex;gap:6px">
          <span class="badge b-cyan"><span class="dot"></span>INTERACTIVE CANVAS</span>
          <span class="badge b-purple">CHART.JS LIVE RENDER</span>
        </div>
      </div>
      <div style="height:560px;position:relative">
        <canvas id="chart_budget_first_single"></canvas>
      </div>
    </div>
  </div>

  <!-- Chart View 2: Decode Token Single Request -->
  <div id="budget-decode-single-container" class="budget-view-container" style="display:none">
    <div style="background:rgba(0,0,0,0.35);padding:14px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:6px">
        <div>
          <div style="font-weight:700;color:var(--purple);font-size:12px">⚡ Interactive 100% Stacked Wall-Time Budget — Decode Token (TPOT)</div>
          <div style="font-size:10px;color:var(--muted)">24 Operating Points · Memory Floor (KV Read) vs Compute Kernels vs AllReduce vs Pipeline Hops vs In-Flight Waits</div>
        </div>
        <div style="display:flex;gap:6px">
          <span class="badge b-cyan"><span class="dot"></span>INTERACTIVE CANVAS</span>
          <span class="badge b-purple">CHART.JS LIVE RENDER</span>
        </div>
      </div>
      <div style="height:560px;position:relative">
        <canvas id="chart_budget_decode_single"></canvas>
      </div>
    </div>
  </div>

  <!-- Chart View 3: First Token Under Load -->
  <div id="budget-first-load-container" class="budget-view-container" style="display:none">
    <div style="background:rgba(0,0,0,0.35);padding:14px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:6px">
        <div>
          <div style="font-weight:700;color:var(--amber);font-size:12px">⚡ Interactive 100% Stacked Wall-Time Budget — First Token Under Load (Queue Saturation)</div>
          <div style="font-size:10px;color:var(--muted)">24 Operating Points · Queue Wait Growth across Concurrency (c1 → c32) and Poisson Arrival Rates (0.5× → 1.0×)</div>
        </div>
        <div style="display:flex;gap:6px">
          <span class="badge b-cyan"><span class="dot"></span>INTERACTIVE CANVAS</span>
          <span class="badge b-purple">CHART.JS LIVE RENDER</span>
        </div>
      </div>
      <div style="height:560px;position:relative">
        <canvas id="chart_budget_first_load"></canvas>
      </div>
    </div>
  </div>

  <!-- Chart View 4: Decode Token Under Load -->
  <div id="budget-decode-load-container" class="budget-view-container" style="display:none">
    <div style="background:rgba(0,0,0,0.35);padding:14px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:6px">
        <div>
          <div style="font-weight:700;color:var(--red);font-size:12px">⚡ Interactive 100% Stacked Wall-Time Budget — Decode Token Under Load (Head-of-Line Blocking)</div>
          <div style="font-size:10px;color:var(--muted)">24 Operating Points · Waiting Behind In-Flight Prefills Dominating Decode Turn-Around at Scale</div>
        </div>
        <div style="display:flex;gap:6px">
          <span class="badge b-cyan"><span class="dot"></span>INTERACTIVE CANVAS</span>
          <span class="badge b-purple">CHART.JS LIVE RENDER</span>
        </div>
      </div>
      <div style="height:560px;position:relative">
        <canvas id="chart_budget_decode_load"></canvas>
      </div>
    </div>
  </div>

  <!-- Collapsible Reference: Publication Static PNGs (Preserved for Audit Verification & Reference) -->
  <details style="margin:10px 0;padding:8px 12px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:6px;font-size:11px">
    <summary style="cursor:pointer;color:var(--muted);font-weight:600">🖼️ View Static Publication Reference PNGs (300 DPI Pre-rendered Artifacts)</summary>
    <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:6px">
        <div style="font-size:10px;color:var(--cyan);font-weight:700;margin-bottom:4px">1. wall_time_budget_first_token.png</div>
        <img src="{imgs[0]}" alt="First Token Wall Time Budget (Single Request)" style="max-width:100%;height:auto;border-radius:4px" />
      </div>
      <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:6px">
        <div style="font-size:10px;color:var(--purple);font-weight:700;margin-bottom:4px">2. wall_time_budget_decode_token.png</div>
        <img src="{imgs[1]}" alt="Decode Token Wall Time Budget (Single Request)" style="max-width:100%;height:auto;border-radius:4px" />
      </div>
      <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:6px">
        <div style="font-size:10px;color:var(--amber);font-weight:700;margin-bottom:4px">3. wall_time_budget_first_token_under_load.png</div>
        <img src="{imgs[2]}" alt="First Token Wall Time Budget (Under Load)" style="max-width:100%;height:auto;border-radius:4px" />
      </div>
      <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:6px">
        <div style="font-size:10px;color:var(--red);font-weight:700;margin-bottom:4px">4. wall_time_budget_decode_token_under_load.png</div>
        <img src="{imgs[3]}" alt="Decode Token Wall Time Budget (Under Load)" style="max-width:100%;height:auto;border-radius:4px" />
      </div>
    </div>
  </details>
  '''

html = html[:start_pos] + new_containers_html + html[end_pos:]

# Update toggleBudgetView script
old_toggle_script = '''function toggleBudgetView(view) {
    if (view === 'first') view = 'first_single';
    if (view === 'decode') view = 'decode_single';
    const containers = {
        'first_single': document.getElementById('budget-first-single-container'),
        'decode_single': document.getElementById('budget-decode-single-container'),
        'first_load': document.getElementById('budget-first-load-container'),
        'decode_load': document.getElementById('budget-decode-load-container')
    };
    const buttons = {
        'first_single': document.getElementById('btn-budget-first-single'),
        'decode_single': document.getElementById('btn-budget-decode-single'),
        'first_load': document.getElementById('btn-budget-first-load'),
        'decode_load': document.getElementById('btn-budget-decode-load')
    };
    for (let key in containers) {
        if (containers[key]) {
            containers[key].style.display = (key === view) ? 'block' : 'none';
        }
        if (buttons[key]) {
            if (key === view) {
                buttons[key].classList.add('active');
            } else {
                buttons[key].classList.remove('active');
            }
        }
    }
}'''

new_toggle_script = '''function toggleBudgetView(view) {
    if (view === 'first') view = 'first_single';
    if (view === 'decode') view = 'decode_single';
    const containers = {
        'first_single': document.getElementById('budget-first-single-container'),
        'decode_single': document.getElementById('budget-decode-single-container'),
        'first_load': document.getElementById('budget-first-load-container'),
        'decode_load': document.getElementById('budget-decode-load-container')
    };
    const buttons = {
        'first_single': document.getElementById('btn-budget-first-single'),
        'decode_single': document.getElementById('btn-budget-decode-single'),
        'first_load': document.getElementById('btn-budget-first-load'),
        'decode_load': document.getElementById('btn-budget-decode-load')
    };
    for (let key in containers) {
        if (containers[key]) {
            containers[key].style.display = (key === view) ? 'block' : 'none';
        }
        if (buttons[key]) {
            if (key === view) {
                buttons[key].classList.add('active');
            } else {
                buttons[key].classList.remove('active');
            }
        }
    }
    setTimeout(() => { window.dispatchEvent(new Event('resize')); }, 60);
}'''

assert old_toggle_script in html, "old_toggle_script not found"
html = html.replace(old_toggle_script, new_toggle_script)

# Add chart initialization logic for the 4 wall-time budget charts
budget_js_code = f'''
    // ==========================================
    // WALL-TIME BUDGET CHARTS (REAL CODE CHARTS)
    // ==========================================
    const budgetRawData1 = {json.dumps(d1)};
    const budgetRawData2 = {json.dumps(d2)};
    const budgetRawData3 = {json.dumps(d3)};
    const budgetRawData4 = {json.dumps(d4)};

    function initBudgetCharts() {{
        // Chart 1: First Token Single Request (TTFT)
        safeInitChart('chart_budget_first_single', {{
            type: 'bar',
            data: {{
                labels: budgetRawData1.map(r => r.operating_point),
                datasets: [
                    {{ label: 'Prefill Kernels / Compute', data: budgetRawData1.map(r => r.prefill_kernels_pct), backgroundColor: 'rgba(66, 201, 255, 0.85)' }},
                    {{ label: 'Prefill Collectives (AllReduce)', data: budgetRawData1.map(r => r.prefill_collectives_pct), backgroundColor: 'rgba(255, 159, 67, 0.85)' }},
                    {{ label: 'Pipeline Communication / Waits', data: budgetRawData1.map(r => r.pipeline_waits_pct), backgroundColor: 'rgba(165, 94, 234, 0.85)' }},
                    {{ label: 'Queue Wait Delay', data: budgetRawData1.map(r => r.queue_wait_pct), backgroundColor: 'rgba(255, 82, 82, 0.85)' }},
                    {{ label: 'Shared Step / Co-located', data: budgetRawData1.map(r => r.shared_step_pct), backgroundColor: 'rgba(75, 123, 236, 0.85)' }},
                    {{ label: 'Engine Overhead', data: budgetRawData1.map(r => r.overhead_pct), backgroundColor: 'rgba(116, 125, 140, 0.85)' }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        max: 100,
                        title: {{ display: true, text: '% of Total First Token Wall Time', color: '#94a3b8' }},
                        ticks: {{ color: '#94a3b8', callback: v => v + '%' }},
                        grid: {{ color: 'rgba(255,255,255,0.06)' }}
                    }},
                    y: {{
                        stacked: true,
                        ticks: {{ color: '#e2e8f0', font: {{ size: 10, family: 'monospace' }} }},
                        grid: {{ color: 'rgba(255,255,255,0.04)' }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'top', labels: {{ color: '#cbd5e1', font: {{ size: 10.5 }}, boxWidth: 12, padding: 8 }} }},
                    tooltip: {{
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#38bdf8',
                        bodyColor: '#f1f5f9',
                        borderColor: 'rgba(56, 189, 248, 0.3)',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {{
                            title: function(items) {{
                                const idx = items[0].dataIndex;
                                const pt = budgetRawData1[idx];
                                return pt.operating_point + ' [' + pt.split_source + '] · TTFT: ' + pt.first_token_ttft_s + 's';
                            }},
                            label: function(ctx) {{
                                const idx = ctx.dataIndex;
                                const pt = budgetRawData1[idx];
                                const pct = ctx.raw;
                                const dur = (pt.first_token_ttft_s * pct / 100).toFixed(3);
                                return ' ' + ctx.dataset.label + ': ' + pct + '% (' + dur + 's)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Chart 2: Decode Token Single Request (TPOT)
        safeInitChart('chart_budget_decode_single', {{
            type: 'bar',
            data: {{
                labels: budgetRawData2.map(r => r.operating_point),
                datasets: [
                    {{ label: 'Memory Floor (KV Read)', data: budgetRawData2.map(r => r.memory_floor_pct), backgroundColor: 'rgba(46, 213, 115, 0.85)' }},
                    {{ label: 'Compute Kernels Above Floor', data: budgetRawData2.map(r => r.kernels_above_floor_pct), backgroundColor: 'rgba(66, 201, 255, 0.85)' }},
                    {{ label: 'TP Collectives (AllReduce)', data: budgetRawData2.map(r => r.collectives_ar_pct), backgroundColor: 'rgba(255, 159, 67, 0.85)' }},
                    {{ label: 'Pipeline Communication / Hops', data: budgetRawData2.map(r => r.pipeline_hops_pct), backgroundColor: 'rgba(165, 94, 234, 0.85)' }},
                    {{ label: 'Waiting Behind Prefills', data: budgetRawData2.map(r => r.waiting_behind_prefills_pct), backgroundColor: 'rgba(252, 92, 101, 0.85)' }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        max: 100,
                        title: {{ display: true, text: '% of Total Decode Step Time', color: '#94a3b8' }},
                        ticks: {{ color: '#94a3b8', callback: v => v + '%' }},
                        grid: {{ color: 'rgba(255,255,255,0.06)' }}
                    }},
                    y: {{
                        stacked: true,
                        ticks: {{ color: '#e2e8f0', font: {{ size: 10, family: 'monospace' }} }},
                        grid: {{ color: 'rgba(255,255,255,0.04)' }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'top', labels: {{ color: '#cbd5e1', font: {{ size: 10.5 }}, boxWidth: 12, padding: 8 }} }},
                    tooltip: {{
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#38bdf8',
                        bodyColor: '#f1f5f9',
                        borderColor: 'rgba(56, 189, 248, 0.3)',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {{
                            title: function(items) {{
                                const idx = items[0].dataIndex;
                                const pt = budgetRawData2[idx];
                                return pt.operating_point + ' [' + pt.split_source + '] · TPOT: ' + pt.decode_tpot_ms + ' ms';
                            }},
                            label: function(ctx) {{
                                const idx = ctx.dataIndex;
                                const pt = budgetRawData2[idx];
                                const pct = ctx.raw;
                                const dur = (pt.decode_tpot_ms * pct / 100).toFixed(2);
                                return ' ' + ctx.dataset.label + ': ' + pct + '% (' + dur + ' ms)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Chart 3: First Token Under Load
        safeInitChart('chart_budget_first_load', {{
            type: 'bar',
            data: {{
                labels: budgetRawData3.map(r => r.operating_point),
                datasets: [
                    {{ label: 'Queue Wait Delay', data: budgetRawData3.map(r => r.queue_wait_pct), backgroundColor: 'rgba(255, 82, 82, 0.85)' }},
                    {{ label: 'Prefill Collectives', data: budgetRawData3.map(r => r.prefill_collectives_pct), backgroundColor: 'rgba(255, 159, 67, 0.85)' }},
                    {{ label: 'Pipeline Waits', data: budgetRawData3.map(r => r.pipeline_waits_pct), backgroundColor: 'rgba(165, 94, 234, 0.85)' }},
                    {{ label: 'Prefill Kernels', data: budgetRawData3.map(r => r.prefill_kernels_pct), backgroundColor: 'rgba(66, 201, 255, 0.85)' }},
                    {{ label: 'Shared Chunk Steps', data: budgetRawData3.map(r => r.shared_steps_pct), backgroundColor: 'rgba(75, 123, 236, 0.85)' }},
                    {{ label: 'Outside Engine Overhead', data: budgetRawData3.map(r => r.outside_engine_pct), backgroundColor: 'rgba(116, 125, 140, 0.85)' }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        max: 100,
                        title: {{ display: true, text: '% of Loaded First Token Wall Time', color: '#94a3b8' }},
                        ticks: {{ color: '#94a3b8', callback: v => v + '%' }},
                        grid: {{ color: 'rgba(255,255,255,0.06)' }}
                    }},
                    y: {{
                        stacked: true,
                        ticks: {{ color: '#e2e8f0', font: {{ size: 10, family: 'monospace' }} }},
                        grid: {{ color: 'rgba(255,255,255,0.04)' }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'top', labels: {{ color: '#cbd5e1', font: {{ size: 10.5 }}, boxWidth: 12, padding: 8 }} }},
                    tooltip: {{
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#38bdf8',
                        bodyColor: '#f1f5f9',
                        borderColor: 'rgba(56, 189, 248, 0.3)',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {{
                            title: function(items) {{
                                const idx = items[0].dataIndex;
                                const pt = budgetRawData3[idx];
                                return pt.operating_point + ' [' + pt.split_source + '] · TTFT: ' + pt.first_token_ttft_s + 's';
                            }},
                            label: function(ctx) {{
                                const idx = ctx.dataIndex;
                                const pt = budgetRawData3[idx];
                                const pct = ctx.raw;
                                const dur = (pt.first_token_ttft_s * pct / 100).toFixed(3);
                                return ' ' + ctx.dataset.label + ': ' + pct + '% (' + dur + 's)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Chart 4: Decode Token Under Load
        safeInitChart('chart_budget_decode_load', {{
            type: 'bar',
            data: {{
                labels: budgetRawData4.map(r => r.operating_point),
                datasets: [
                    {{ label: 'Waiting Behind In-Flight Prefills', data: budgetRawData4.map(r => r.waiting_behind_prefills_pct), backgroundColor: 'rgba(252, 92, 101, 0.85)' }},
                    {{ label: 'Memory Floor (KV Read)', data: budgetRawData4.map(r => r.memory_floor_pct), backgroundColor: 'rgba(46, 213, 115, 0.85)' }},
                    {{ label: 'Compute Kernels Above Floor', data: budgetRawData4.map(r => r.kernels_above_floor_pct), backgroundColor: 'rgba(66, 201, 255, 0.85)' }},
                    {{ label: 'Collectives AllReduce', data: budgetRawData4.map(r => r.collectives_ar_pct), backgroundColor: 'rgba(255, 159, 67, 0.85)' }},
                    {{ label: 'Pipeline Communication / Hops', data: budgetRawData4.map(r => r.pipeline_hops_pct), backgroundColor: 'rgba(165, 94, 234, 0.85)' }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        max: 100,
                        title: {{ display: true, text: '% of Loaded Decode Turn-Around Time', color: '#94a3b8' }},
                        ticks: {{ color: '#94a3b8', callback: v => v + '%' }},
                        grid: {{ color: 'rgba(255,255,255,0.06)' }}
                    }},
                    y: {{
                        stacked: true,
                        ticks: {{ color: '#e2e8f0', font: {{ size: 10, family: 'monospace' }} }},
                        grid: {{ color: 'rgba(255,255,255,0.04)' }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'top', labels: {{ color: '#cbd5e1', font: {{ size: 10.5 }}, boxWidth: 12, padding: 8 }} }},
                    tooltip: {{
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#38bdf8',
                        bodyColor: '#f1f5f9',
                        borderColor: 'rgba(56, 189, 248, 0.3)',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {{
                            title: function(items) {{
                                const idx = items[0].dataIndex;
                                const pt = budgetRawData4[idx];
                                return pt.operating_point + ' [' + pt.split_source + '] · TPOT: ' + pt.decode_tpot_ms + ' ms (Own: ' + pt.own_step_ms + ' ms, Stalled: ' + pt.stalled_tokens_pct + '%)';
                            }},
                            label: function(ctx) {{
                                const idx = ctx.dataIndex;
                                const pt = budgetRawData4[idx];
                                const pct = ctx.raw;
                                const dur = (pt.decode_tpot_ms * pct / 100).toFixed(2);
                                return ' ' + ctx.dataset.label + ': ' + pct + '% (' + dur + ' ms)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    }}
'''

# Find where to insert initBudgetCharts call - right where safeInitChart charts are initialized
marker_init = "// Chart 8c: Queue Saturation Cliff: TP4 vs TP8"
pos_init = html.find(marker_init)
assert pos_init != -1, "marker_init not found"

# Insert budget_js_code and initBudgetCharts() call
# Find safe place after Chart 8c
target_str = "safeInitChart('chart_scaleup_queue_cliff',"
pos_scaleup = html.find(target_str)
# Find the closing of this safeInitChart block
pos_block_end = html.find("});", pos_scaleup) + 3

insert_code = f"\n{budget_js_code}\n    initBudgetCharts();\n"
html = html[:pos_block_end] + insert_code + html[pos_block_end:]

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Updated MASTER_CHARACTERIZATION_DASHBOARD.html with real code charts!")

# Also copy to release_specs
release_path = r"v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html"
with open(release_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Updated release_specs copy as well!")
