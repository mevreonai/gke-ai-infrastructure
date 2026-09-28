# build_kd_assets.py
import json

with open("scratch/build_v5_subpages.py", "r", encoding="utf-8") as f:
    code = f.read()

ns = {}
exec(code, ns)
PAGES = ns["PAGES"]

with open("build_full_key_discoveries.py", "r", encoding="utf-8") as f:
    bcode = f.read()

import re
css_match = re.search(r'CSS_EXTRA = """(.*?)"""', bcode, re.DOTALL)
CSS_EXTRA = css_match.group(1) if css_match else ""

with open("scratch/apply_full_v5_key_discoveries.py", "r", encoding="utf-8") as f:
    fcode = f.read()

ns2 = {"PAGES": PAGES}
exec(fcode, ns2)
generate_keydiscoveries_tab_html = ns2["generate_keydiscoveries_tab_html"]

tab_html = generate_keydiscoveries_tab_html()

with open("scratch/test_js_generation.py", "r", encoding="utf-8") as f:
    jcode = f.read()

ns3 = {"PAGES": PAGES, "json": json}
exec(jcode, ns3)
js_base = ns3["js_code"]

# Now add initKeyDiscoveryCharts function to js_base
charts_js = """
window.initKeyDiscoveryCharts = function(pageId, prefix) {
    prefix = prefix || '';
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not available yet');
        return;
    }

    window.kdCharts = window.kdCharts || {};

    function cleanChart(canvasId) {
        if (window.kdCharts[canvasId]) {
            try { window.kdCharts[canvasId].destroy(); } catch(e){}
            delete window.kdCharts[canvasId];
        }
        var c = Chart.getChart(canvasId);
        if (c) {
            try { c.destroy(); } catch(e){}
        }
    }

    var defaultChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 350 },
        plugins: {
            legend: {
                labels: { color: '#cbd5e1', font: { size: 10, weight: '600' }, boxWidth: 12 }
            },
            tooltip: {
                backgroundColor: '#0f1c30',
                titleColor: '#ffffff',
                bodyColor: '#cbd5e1',
                borderColor: '#233857',
                borderWidth: 1,
                padding: 10
            }
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8', font: { size: 10 } },
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
            },
            y: {
                ticks: { color: '#94a3b8', font: { size: 10 } },
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
            }
        }
    };

    var cid1 = prefix + 'chart-p' + pageId + '-primary';
    var cid2 = prefix + 'chart-p' + pageId + '-secondary';

    if (pageId === 1) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.type = 'logarithmic';
            opt1.scales.y.title = { display: true, text: 'TTFT (seconds, log scale)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'line',
                data: {
                    labels: ['128K Context', '512K Context', '1M Extreme Context'],
                    datasets: [
                        { label: 'TP4 / PP2 (20G Cap)', data: [2.926, 18.860, 53.127], borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)', tension: 0.2, pointRadius: 4 },
                        { label: 'TP8 / PP2 (20G Cap)', data: [2.510, 15.650, 41.472], borderColor: '#a78bfa', backgroundColor: 'rgba(167, 139, 250, 0.1)', tension: 0.2, pointRadius: 4 },
                        { label: 'TP4 / PP4 (20G Cap)', data: [1.961, 11.134, 29.684], borderColor: '#4ade80', backgroundColor: 'rgba(74, 222, 128, 0.1)', tension: 0.2, pointRadius: 4 },
                        { label: 'TP16 / PP1 (20G Cap - Severe)', data: [31.050, 128.270, 256.889], borderColor: '#f87171', backgroundColor: 'rgba(248, 113, 113, 0.15)', borderWidth: 3, tension: 0.2, pointRadius: 5 }
                    ]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.title = { display: true, text: 'TTFT Delta vs Native (%)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['TP4 / PP2', 'TP8 / PP2', 'TP4 / PP4', 'TP16 / PP1 (Severe Exposure)'],
                    datasets: [{
                        label: '1M Degradation vs Native (20G Cap %)',
                        data: [1.14, -0.10, 3.91, 276.69],
                        backgroundColor: ['#38bdf8', '#a78bfa', '#4ade80', '#f87171'],
                        borderRadius: 4
                    }]
                },
                options: opt2
            });
        }
    } else if (pageId === 2) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.title = { display: true, text: 'Output Throughput Gain c1→c4 (%)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['8K Context', '128K Context', '512K Context', '1M Extreme Context'],
                    datasets: [{
                        label: 'Output TPS Gain (c1 → c4 %)',
                        data: [120.82, 10.27, 2.19, 1.52],
                        backgroundColor: ['#4ade80', '#38bdf8', '#facc15', '#f87171'],
                        borderRadius: 4
                    }]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.type = 'logarithmic';
            opt2.scales.y.title = { display: true, text: 'Queue Residence Time (seconds, log scale)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'line',
                data: {
                    labels: ['8K', '128K', '512K', '1M'],
                    datasets: [{
                        label: 'c4 Queue Wait (seconds)',
                        data: [0.027, 5.110, 53.660, 134.430],
                        borderColor: '#f87171',
                        backgroundColor: 'rgba(248, 113, 113, 0.15)',
                        fill: true,
                        tension: 0.25,
                        pointRadius: 5
                    }]
                },
                options: opt2
            });
        }
    } else if (pageId === 3) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.indexAxis = 'y';
            opt1.scales.x.title = { display: true, text: 'Work Growth Factor 128K → 512K (×)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['NCCL P2P', 'Intra-Node TP', 'MoE Experts', 'KDA Recurrent', 'GEMM Family', 'FlashAttention O(N²)'],
                    datasets: [{
                        label: 'Relative Growth (128K → 512K)',
                        data: [2.18, 3.50, 3.80, 3.95, 5.25, 15.70],
                        backgroundColor: ['#4ade80', '#60a5fa', '#a78bfa', '#fb923c', '#38bdf8', '#f87171'],
                        borderRadius: 4
                    }]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.title = { display: true, text: 'Share of GPU Kernel Work (%)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['FlashAttention', 'GEMM', 'MoE', 'Intra TP', 'Inter P2P', 'KDA'],
                    datasets: [
                        { label: '128K Share (%)', data: [22.8, 8.5, 13.2, 40.0, 8.3, 2.7], backgroundColor: 'rgba(56, 189, 248, 0.75)', borderRadius: 3 },
                        { label: '512K Share (%)', data: [44.8, 5.1, 6.2, 35.6, 5.2, 2.7], backgroundColor: 'rgba(248, 113, 113, 0.85)', borderRadius: 3 }
                    ]
                },
                options: opt2
            });
        }
    } else if (pageId === 4) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.type = 'logarithmic';
            opt1.scales.y.title = { display: true, text: 'TTFT (seconds, log scale)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['~128K Context', '~512K Context', '1M Extreme Context'],
                    datasets: [
                        { label: 'First / Cold TTFT (Uncached)', data: [4.8965, 32.5762, 94.2272], backgroundColor: 'rgba(248, 113, 113, 0.85)', borderRadius: 3 },
                        { label: 'Repeat-Hit Median (Cached)', data: [0.3307, 1.1679, 2.6140], backgroundColor: 'rgba(74, 222, 128, 0.85)', borderRadius: 3 }
                    ]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.title = { display: true, text: 'Prefill Speedup Factor (×)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'line',
                data: {
                    labels: ['~128K', '~512K', '1M'],
                    datasets: [{
                        label: 'Measured Speedup Multiplier',
                        data: [14.8, 27.9, 36.0],
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.2)',
                        fill: true,
                        tension: 0.2,
                        pointRadius: 5
                    }]
                },
                options: opt2
            });
        }
    } else if (pageId === 5) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.title = { display: true, text: 'Median Achieved Rate (req/s)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['8K Context', '128K Context'],
                    datasets: [{
                        label: 'Achieved Requests / Sec (Apparent 18.2× Gap)',
                        data: [3.3586, 0.1846],
                        backgroundColor: ['#38bdf8', '#f87171'],
                        borderRadius: 4
                    }]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.title = { display: true, text: 'Normalized Input Ingestion (kTok/s)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['8K Context', '128K Context'],
                    datasets: [{
                        label: 'Normalized Input Tokens / Sec (True ~1.14× Gap)',
                        data: [27.51, 24.19],
                        backgroundColor: ['#4ade80', '#38bdf8'],
                        borderRadius: 4
                    }]
                },
                options: opt2
            });
        }
    } else if (pageId === 6) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.type = 'logarithmic';
            opt1.scales.y.title = { display: true, text: 'TTFT (seconds, log scale)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['8K', '128K', '512K', '1M'],
                    datasets: [
                        { label: 'TP4 / PP1 TTFT (s)', data: [0.222, 4.532, 31.916, 93.248], backgroundColor: 'rgba(56, 189, 248, 0.75)', borderRadius: 3 },
                        { label: 'TP8 / PP1 TTFT (s)', data: [0.263, 4.810, 28.089, 74.688], backgroundColor: 'rgba(167, 139, 250, 0.75)', borderRadius: 3 }
                    ]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'scatter',
                data: {
                    datasets: [
                        {
                            type: 'line',
                            label: 'Non-Dominated Pareto Frontier (TP4 Family)',
                            data: [
                                { x: 373.0, y: 93.248 },
                                { x: 420.2, y: 52.526 },
                                { x: 457.1, y: 28.568 }
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
                            label: 'Dominated Configurations (Sub-Optimal)',
                            data: [
                                { x: 597.5, y: 74.688 },
                                { x: 1091.2, y: 68.197 }
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
                    plugins: {
                        legend: {
                            labels: { color: '#cbd5e1', font: { size: 10, weight: '600' } }
                        },
                        tooltip: {
                            backgroundColor: '#0f1c30',
                            titleColor: '#ffffff',
                            bodyColor: '#cbd5e1',
                            borderColor: '#233857',
                            borderWidth: 1,
                            padding: 10,
                            callbacks: {
                                label: function(ctx) {
                                    var p = ctx.raw;
                                    if (p.x === 373.0) return 'TP4/PP1 (4 GPUs): TTFT = 93.25s, 373.0 GPU-s [Max Cluster Efficiency]';
                                    if (p.x === 420.2) return 'TP4/PP2 (8 GPUs): TTFT = 52.53s, 420.2 GPU-s [Balanced Frontier Point]';
                                    if (p.x === 457.1) return 'TP4/PP4 (16 GPUs): TTFT = 28.57s, 457.1 GPU-s [Minimal Turn Latency]';
                                    if (p.x === 597.5) return 'TP8/PP1 (8 GPUs): TTFT = 74.69s, 597.5 GPU-s [Dominated by TP4/PP2: +42% GPU-s, +42% slower!]';
                                    if (p.x === 1091.2) return 'TP16/PP1 (16 GPUs): TTFT = 68.20s, 1091.2 GPU-s [Dominated by TP4/PP4: +139% GPU-s, +139% slower!]';
                                    return 'GPU-s: ' + p.x + ', TTFT: ' + p.y + 's';
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'linear',
                            min: 300,
                            max: 1200,
                            title: { display: true, text: 'Resource Occupancy: GPU-seconds / Request (Lower is Better)', color: '#facc15' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        },
                        y: {
                            type: 'linear',
                            min: 15,
                            max: 105,
                            title: { display: true, text: 'Turn Latency: TTFT in seconds (Lower is Better)', color: '#4ade80' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        }
                    }
                }
            });
        }
    } else if (pageId === 7) {
        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.title = { display: true, text: 'Time Per Output Token (ms)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['8K Context', '128K Context', '512K Context', '1M Extreme Context'],
                    datasets: [
                        { label: 'TP4 / PP1 TPOT (ms)', data: [4.475, 5.120, 7.340, 11.230], backgroundColor: 'rgba(56, 189, 248, 0.75)', borderRadius: 3 },
                        { label: 'TP8 / PP1 TPOT (ms - Slower)', data: [6.350, 7.117, 9.175, 13.240], backgroundColor: 'rgba(248, 113, 113, 0.75)', borderRadius: 3 }
                    ]
                },
                options: opt2
            });
        }
    } else if (pageId === 8) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.title = { display: true, text: 'Latency Reduction (%)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['128K Context', '512K Context', '1M Extreme Context'],
                    datasets: [{
                        label: 'Chunk 4K → 16K TTFT Reduction (%)',
                        data: [16.5, 24.4, 27.1],
                        backgroundColor: ['#38bdf8', '#60a5fa', '#4ade80'],
                        borderRadius: 4
                    }]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.min = 232.0;
            opt2.scales.y.max = 232.5;
            opt2.scales.y.title = { display: true, text: '1M c4 TTFT (s) — Zoomed to show 0.049% spread', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['max_num_seqs = 4', 'max_num_seqs = 8', 'max_num_seqs = 16'],
                    datasets: [{
                        label: 'Observed TTFT (seconds) — Completely Flat',
                        data: [232.342, 232.364, 232.250],
                        backgroundColor: 'rgba(148, 163, 184, 0.75)',
                        borderRadius: 4
                    }]
                },
                options: opt2
            });
        }
    } else if (pageId === 9) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.title = { display: true, text: 'Reported GPU SM Util (%)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['128K Context', '512K Context', '1M Context'],
                    datasets: [
                        { label: 'TP4 / PP4 Util (%)', data: [35.2, 55.3, 62.8], backgroundColor: 'rgba(74, 222, 128, 0.75)', borderRadius: 3 },
                        { label: 'TP16 / PP1 Util (%) - Erroneous High', data: [63.2, 67.8, 80.6], backgroundColor: 'rgba(248, 113, 113, 0.75)', borderRadius: 3 }
                    ]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.type = 'logarithmic';
            opt2.scales.y.title = { display: true, text: 'TTFT (seconds, log scale — Lower is Better)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['128K Context', '512K Context', '1M Context'],
                    datasets: [
                        { label: 'TP4 / PP4 TTFT (s) - Fast & Efficient', data: [1.710, 10.222, 28.568], backgroundColor: 'rgba(74, 222, 128, 0.75)', borderRadius: 3 },
                        { label: 'TP16 / PP1 TTFT (s) - Up to 3.75× Slower!', data: [6.420, 29.624, 68.197], backgroundColor: 'rgba(248, 113, 113, 0.75)', borderRadius: 3 }
                    ]
                },
                options: opt2
            });
        }
    } else if (pageId === 10) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.scales.y.title = { display: true, text: 'Reported KV Cache (%)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['TP4/PP1', 'TP4/PP2', 'TP4/PP4', 'TP8/PP1 (Rep)', 'TP8/PP2 (Rep)'],
                    datasets: [{
                        label: 'Reported KV Cache Pressure (%) — Dilutes with PP',
                        data: [12.29, 5.91, 2.75, 12.18, 5.88],
                        backgroundColor: ['#38bdf8', '#38bdf8', '#4ade80', '#a78bfa', '#a78bfa'],
                        borderRadius: 4
                    }]
                },
                options: opt1
            });
        }

        cleanChart(cid2);
        var el2 = document.getElementById(cid2);
        if (el2) {
            var opt2 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt2.scales.y.min = 80;
            opt2.scales.y.max = 100;
            opt2.scales.y.title = { display: true, text: 'Peak Physical Memory (GiB) — Usable = 95.59 GiB', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['TP4/PP1', 'TP4/PP2', 'TP4/PP4', 'TP8/PP1 (Rep)', 'TP8/PP2 (Rep)'],
                    datasets: [{
                        label: 'Peak Allocated Physical VRAM (GiB) — Flat ~88.8 GiB',
                        data: [88.39, 88.69, 88.83, 88.65, 88.70],
                        backgroundColor: 'rgba(250, 204, 21, 0.75)',
                        borderRadius: 4
                    }]
                },
                options: opt2
            });
        }
    }
};

// Route hash listener for Key Discoveries subpages
window.addEventListener('hashchange', function() {
    var hash = window.location.hash || '';
    if (hash.indexOf('#keyfinds/') === 0 || hash.indexOf('#keydiscoveries/') === 0) {
        var slug = hash.replace('#keyfinds/', '').replace('#keydiscoveries/', '');
        for (var i = 0; i < window.KD_PAGES_DATA.length; i++) {
            if (window.KD_PAGES_DATA[i].slug === slug) {
                if (typeof window.switchTab === 'function') {
                    window.switchTab('keydiscoveries');
                }
                window.openFindingSubPage(window.KD_PAGES_DATA[i].id, '');
                break;
            }
        }
    }
});
"""

full_js = js_base + "\n" + charts_js

print(f"Full tab HTML length: {len(tab_html)}")
print(f"Full CSS length: {len(CSS_EXTRA)}")
print(f"Full JS length: {len(full_js)}")

# Write to a bundle file
with open("scratch/kd_bundle.py", "w", encoding="utf-8") as f:
    f.write(f'CSS_EXTRA = """{CSS_EXTRA}"""\n\n')
    f.write(f'TAB_HTML = """{tab_html}"""\n\n')
    f.write(f'FULL_JS = """{full_js}"""\n\n')

print("Saved scratch/kd_bundle.py")
