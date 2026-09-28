"""
apply_boss_requested_fixes.py

Applies the two requested updates across the Performance Characterization dashboards:
1. Folds the 60-second Finding Map list in the solo tab version (KEY_DISCOVERIES_STANDALONE_DASHBOARD.html)
   using a native, accessible <details class="kd-map-card"> folded by default with dynamic toggle state,
   while making it foldable in the master dashboards.
2. Adds explicit topology labels, custom pill styling, and enhanced tooltips to the 1M Latency vs Resource
   Frontier chart (Chart 2 of Finding 6: Parallelism Frontier) on the canvas for all 6 points:
   - TP4 / PP1 (93.2s)
   - TP4 / PP2 (52.5s)
   - TP4 / PP4 (28.6s)
   - TP8 / PP1 (74.7s)
   - TP8 / PP2 (41.5s)
   - TP16 / PP1 (68.2s)
"""

import os
import shutil

print("Applying Boss Requested Updates (Fold 60-sec Map + 1M Frontier Chart Labels)...")

# --- 1. DEFINITION OF REPLACEMENT BLOCKS ---

# Chart 2 for Finding 6 (Parallelism Frontier) with Point Canvas Labels & Detailed Tooltips
NEW_P6_CHART2_CODE = '''        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'scatter',
                data: {
                    datasets: [
                        {
                            type: 'line',
                            label: 'Measured Non-Dominated Frontier (TP4 Family)',
                            data: [
                                { x: 372.99, y: 93.248, name: 'TP4 / PP1 (93.2s)', classification: 'Non-Dominated (Max Efficiency)', align: 'left', offsetX: 10, offsetY: 0 },
                                { x: 420.21, y: 52.526, name: 'TP4 / PP2 (52.5s)', classification: 'Non-Dominated (Balanced)', align: 'left', offsetX: 10, offsetY: -4 },
                                { x: 457.09, y: 28.568, name: 'TP4 / PP4 (28.6s)', classification: 'Non-Dominated (Min Latency)', align: 'left', offsetX: 10, offsetY: 4 }
                            ],
                            borderColor: '#4ade80',
                            backgroundColor: 'rgba(74, 222, 128, 0.1)',
                            borderWidth: 2,
                            pointBackgroundColor: '#4ade80',
                            pointBorderColor: '#ffffff',
                            pointRadius: 6,
                            pointHoverRadius: 8,
                            fill: false,
                            tension: 0.15
                        },
                        {
                            type: 'scatter',
                            label: 'Dominated Configurations (Measured)',
                            data: [
                                { x: 597.50, y: 74.688, name: 'TP8 / PP1 (74.7s)', classification: 'Dominated (sub-optimal)', align: 'left', offsetX: 10, offsetY: 0 },
                                { x: 664.24, y: 41.515, name: 'TP8 / PP2 (41.5s)', classification: 'Dominated by TP4/PP4', align: 'left', offsetX: 10, offsetY: 0 },
                                { x: 1091.15, y: 68.197, name: 'TP16 / PP1 (68.2s)', classification: 'Severely Dominated (+139% cost)', align: 'right', offsetX: -12, offsetY: -6 }
                            ],
                            borderColor: '#f87171',
                            backgroundColor: '#f87171',
                            pointBackgroundColor: '#f87171',
                            pointBorderColor: '#ffffff',
                            pointRadius: 7,
                            pointHoverRadius: 9,
                            pointStyle: 'crossRot'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: { top: 14, right: 32, bottom: 8, left: 8 }
                    },
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom',
                            suggestedMin: 320,
                            suggestedMax: 1180,
                            title: { display: true, text: 'Resource Occupancy Proxy (GPU-seconds / request)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        },
                        y: {
                            suggestedMin: 18,
                            suggestedMax: 105,
                            title: { display: true, text: '1M TTFT (seconds — Lower is Better)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#cbd5e1', font: { size: 10, weight: '600' } } },
                        tooltip: {
                            callbacks: {
                                title: function(items) {
                                    if (!items.length) return '';
                                    var p = items[0].raw;
                                    return p.name ? (p.name.split(' (')[0]) : items[0].dataset.label;
                                },
                                label: function(ctx) {
                                    var p = ctx.raw;
                                    var name = p.name ? (p.name.split(' (')[0] + ': ') : '';
                                    var frontier = p.classification ? (' — ' + p.classification) : '';
                                    return name + p.y.toFixed(2) + 's TTFT, ' + p.x.toFixed(1) + ' GPU-s' + frontier;
                                }
                            }
                        }
                    }
                },
                plugins: [{
                    id: 'frontierPointLabels',
                    afterDatasetsDraw: function(chart) {
                        var ctx = chart.ctx;
                        chart.data.datasets.forEach(function(dataset, dIdx) {
                            var meta = chart.getDatasetMeta(dIdx);
                            if (!meta.hidden) {
                                meta.data.forEach(function(element, idx) {
                                    var p = dataset.data[idx];
                                    if (p && p.name) {
                                        ctx.save();
                                        ctx.font = '600 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                                        var isFrontier = (dIdx === 0);
                                        var textColor = isFrontier ? '#86efac' : '#fca5a5';
                                        var bgColor = isFrontier ? 'rgba(6, 78, 59, 0.88)' : 'rgba(127, 29, 29, 0.88)';
                                        var borderColor = isFrontier ? 'rgba(74, 222, 128, 0.6)' : 'rgba(248, 113, 113, 0.6)';
                                        
                                        var textWidth = ctx.measureText(p.name).width;
                                        var padH = 6;
                                        var h = 18;
                                        var w = textWidth + (padH * 2);
                                        
                                        var align = p.align || 'left';
                                        var offX = p.offsetX || 10;
                                        var offY = p.offsetY || 0;
                                        
                                        var boxX = (align === 'right') ? (element.x + offX - w) : (element.x + offX);
                                        var boxY = element.y + offY - (h / 2);
                                        
                                        ctx.fillStyle = bgColor;
                                        ctx.strokeStyle = borderColor;
                                        ctx.lineWidth = 1;
                                        ctx.beginPath();
                                        if (ctx.roundRect) {
                                            ctx.roundRect(boxX, boxY, w, h, 4);
                                        } else {
                                            ctx.rect(boxX, boxY, w, h);
                                        }
                                        ctx.fill();
                                        ctx.stroke();
                                        
                                        ctx.fillStyle = textColor;
                                        ctx.textAlign = 'left';
                                        ctx.textBaseline = 'middle';
                                        ctx.fillText(p.name, boxX + padH, boxY + (h / 2));
                                        ctx.restore();
                                    }
                                });
                            }
                        });
                    }
                }]
            });
        }'''

OLD_P6_CHART2_CODE = '''        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'scatter',
                data: {
                    datasets: [
                        {
                            type: 'line',
                            label: 'Measured Non-Dominated Frontier (TP4 Family)',
                            data: [
                                { x: 372.99, y: 93.248 },
                                { x: 420.21, y: 52.526 },
                                { x: 457.09, y: 28.568 }
                            ],
                            borderColor: '#4ade80',
                            backgroundColor: 'rgba(74, 222, 128, 0.1)',
                            borderWidth: 2,
                            pointBackgroundColor: '#4ade80',
                            pointBorderColor: '#ffffff',
                            pointRadius: 6,
                            pointHoverRadius: 8,
                            fill: false,
                            tension: 0.15
                        },
                        {
                            type: 'scatter',
                            label: 'Dominated Configurations (Measured)',
                            data: [
                                { x: 597.50, y: 74.688 },
                                { x: 664.24, y: 41.515 },
                                { x: 1091.15, y: 68.197 }
                            ],
                            borderColor: '#f87171',
                            backgroundColor: '#f87171',
                            pointBackgroundColor: '#f87171',
                            pointBorderColor: '#ffffff',
                            pointRadius: 7,
                            pointHoverRadius: 9,
                            pointStyle: 'crossRot'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom',
                            title: { display: true, text: 'Resource Occupancy Proxy (GPU-seconds / request)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        },
                        y: {
                            title: { display: true, text: '1M TTFT (seconds — Lower is Better)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#cbd5e1', font: { size: 10, weight: '600' } } },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.dataset.label + ': ' + ctx.raw.x.toFixed(1) + ' GPU-s, ' + ctx.raw.y.toFixed(2) + 's TTFT';
                                }
                            }
                        }
                    }
                }
            });
        }'''

# Foldable styles for details.kd-map-card
MAP_CARD_CSS_ADDITION = '''
details.kd-map-card summary::-webkit-details-marker {
    display: none;
}
details.kd-map-card summary {
    list-style: none;
}
details.kd-map-card[open] summary {
    margin-bottom: 8px !important;
}
'''

MAP_CARD_JS_HANDLER = '''
  // Handle 60-sec Finding Map fold/unfold dynamic toggle indicator
  var kdDetails = document.getElementById('kd-map-details');
  if (kdDetails) {
    var foldText = kdDetails.querySelector('.kd-fold-state-text');
    kdDetails.addEventListener('toggle', function() {
      if (foldText) {
        foldText.textContent = kdDetails.open ? 'Fold 60-sec Map ▲' : 'Unfold 60-sec Map ▼';
      }
    });
  }
'''

def transform_map_card_in_html(content, is_folded_by_default=False):
    """
    Transforms <div class="kd-map-card"> into a foldable <details class="kd-map-card">.
    If is_folded_by_default is True, omits 'open' attribute.
    If False, includes 'open' attribute.
    """
    # 1. Add CSS rules if not already present
    if 'details.kd-map-card summary' not in content:
        style_pos = content.find('.kd-map-card {')
        if style_pos != -1:
            end_brace = content.find('}', style_pos) + 1
            content = content[:end_brace] + MAP_CARD_CSS_ADDITION + content[end_brace:]
    
    # 2. Transform the HTML card
    open_attr = "" if is_folded_by_default else " open"
    fold_text = "Unfold 60-sec Map ▼" if is_folded_by_default else "Fold 60-sec Map ▲"
    
    old_start = '<div class="kd-map-card">\\n      <div class="kd-map-title">\\n        <span>&#128506;</span> 60-second Finding Map\\n      </div>\\n      <table class="kd-map-table">'
    new_start = f'''<details class="kd-map-card" id="kd-map-details"{open_attr}>
      <summary class="kd-map-title" style="cursor:pointer; display:flex; align-items:center; justify-content:space-between; list-style:none; user-select:none; margin-bottom:0; padding:2px 0;">
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:14px">&#128506;</span>
          <span style="font-size:13px; font-weight:800; color:#38bdf8; letter-spacing:0.3px;">60-second Finding Map</span>
          <span class="badge b-blue" style="font-size:10px; padding:2px 8px; border-radius:4px;">10 Findings Executive Overview</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="kd-map-fold-badge" style="font-size:11px; font-weight:600; color:#38bdf8; background:rgba(56, 189, 248, 0.12); border:1px solid rgba(56, 189, 248, 0.3); padding:4px 12px; border-radius:4px; display:inline-flex; align-items:center; gap:6px;">
            <span class="kd-fold-state-text">{fold_text}</span>
          </span>
        </div>
      </summary>
      <div style="margin-top:12px; overflow-x:auto;">
        <table class="kd-map-table">'''
    
    # Handle both raw newlines and escaped
    target_start = None
    if '<div class="kd-map-card">\n      <div class="kd-map-title">\n        <span>&#128506;</span> 60-second Finding Map\n      </div>\n      <table class="kd-map-table">' in content:
        target_start = '<div class="kd-map-card">\n      <div class="kd-map-title">\n        <span>&#128506;</span> 60-second Finding Map\n      </div>\n      <table class="kd-map-table">'
    elif '<div class="kd-map-card">\n      <div class="kd-map-title">\n        <span>🗺</span> 60-second Finding Map\n      </div>\n      <table class="kd-map-table">' in content:
        target_start = '<div class="kd-map-card">\n      <div class="kd-map-title">\n        <span>🗺</span> 60-second Finding Map\n      </div>\n      <table class="kd-map-table">'
    
    if target_start:
        content = content.replace(target_start, new_start, 1)
        # Find closing </table>\n    </div>
        tbl_end = content.find('</table>', content.find('id="kd-map-details"'))
        div_end = content.find('</div>', tbl_end)
        if div_end != -1:
            new_close = '</table>\n      </div>\n    </details>'
            content = content[:tbl_end] + new_close + content[div_end + 6:]
            print("  Successfully transformed kd-map-card into <details> container.")
    
    # 3. Add JS toggle listener
    if 'kdDetails.addEventListener(\'toggle\'' not in content:
        script_end = content.rfind('</script>')
        if script_end != -1:
            content = content[:script_end] + MAP_CARD_JS_HANDLER + content[script_end:]
            print("  Added dynamic fold/unfold JS listener.")
            
    return content

def update_file(filepath, is_standalone=False):
    print(f"\nProcessing: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig_len = len(content)
    
    # A. Update Chart 2 for Finding 6 (Add labels)
    if OLD_P6_CHART2_CODE in content:
        content = content.replace(OLD_P6_CHART2_CODE, NEW_P6_CHART2_CODE)
        print("  Updated Finding 6 Chart 2 (added point canvas labels, pill badges, and enhanced tooltips).")
    else:
        print("  Finding 6 Chart 2 old target not found (may already be updated).")
    
    # B. Transform Finding Map
    # For solo/standalone, fold it by default (is_folded_by_default=True)
    # For master dashboards, make it foldable but open by default (is_folded_by_default=False)
    content = transform_map_card_in_html(content, is_folded_by_default=is_standalone)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Saved {filepath} ({orig_len:,} -> {len(content):,} bytes)")

# Update master files
master_files = [
    "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html",
    "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_WITH_KEYFINDS.html",
    "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html"
]

for mf in master_files:
    if os.path.exists(mf):
        update_file(mf, is_standalone=False)

# Update standalone file (folded by default!)
standalone_file = "KEY_DISCOVERIES_STANDALONE_DASHBOARD.html"
if os.path.exists(standalone_file):
    update_file(standalone_file, is_standalone=True)

# Synchronize copies to release_specs and dashboards/v4_dashboard
mirrors = [
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html", "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html"),
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_WITH_KEYFINDS.html", "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html"),
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html", "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD_NO_KEYFINDS.html"),
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html", "v8_full_results/dashboards/v4_dashboard/index.html"),
    ("KEY_DISCOVERIES_STANDALONE_DASHBOARD.html", "v8_full_results/dashboards/v4_dashboard/KEY_DISCOVERIES_STANDALONE_DASHBOARD.html"),
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html", "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html"),
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_WITH_KEYFINDS.html", "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html"),
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html", "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD_NO_KEYFINDS.html"),
    ("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html", "v8_full_results/release_specs/index.html"),
    ("KEY_DISCOVERIES_STANDALONE_DASHBOARD.html", "v8_full_results/release_specs/KEY_DISCOVERIES_STANDALONE_DASHBOARD.html"),
]

for src, dst in mirrors:
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"Synchronized mirror: {src} -> {dst}")

print("\nAll files successfully updated and synchronized!")
