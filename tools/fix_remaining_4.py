import sys, re

dash_file = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"

with open(dash_file, "r", encoding="utf-8") as f:
    h = f.read()

# 1. Replace heatmap table tbody
hm_pos = h.find('id="scaleout-sensitivity-heatmap"')
if hm_pos != -1:
    tbody_start = h.find('<tbody>', hm_pos)
    tbody_end = h.find('</tbody>', tbody_start)
    
    new_tbody = """<tbody>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>128K</td><td>1.710s</td><td>1.761s</td><td><span class="badge b-green">+2.97%</span></td><td>1.961s</td><td><span class="badge b-green">+14.67%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>512K</td><td>10.222s</td><td>10.389s</td><td><span class="badge b-green">+1.64%</span></td><td>11.134s</td><td><span class="badge b-green">+8.93%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>1M</td><td>28.568s</td><td>28.866s</td><td><span class="badge b-green">+1.04%</span></td><td>29.684s</td><td><span class="badge b-green">+3.91%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>128K</td><td>2.788s</td><td>2.826s</td><td><span class="badge b-green">+1.36%</span></td><td>2.810s</td><td><span class="badge b-green">+0.81%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>512K</td><td>15.576s</td><td>15.548s</td><td><span class="badge b-green">-0.18%</span></td><td>15.546s</td><td><span class="badge b-green">-0.19%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>1M</td><td>41.515s</td><td>41.462s</td><td><span class="badge b-green">-0.13%</span></td><td>41.472s</td><td><span class="badge b-green">-0.10%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>128K</td><td>2.647s</td><td>2.665s</td><td><span class="badge b-green">+0.66%</span></td><td>2.859s</td><td><span class="badge b-green">+8.01%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>512K</td><td>17.945s</td><td>17.982s</td><td><span class="badge b-green">+0.20%</span></td><td>18.372s</td><td><span class="badge b-green">+2.37%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>1M</td><td>52.526s</td><td>52.597s</td><td><span class="badge b-green">+0.13%</span></td><td>53.127s</td><td><span class="badge b-green">+1.14%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>128K</td><td>6.420s</td><td>9.736s</td><td><span class="badge b-green">+51.64%</span></td><td>31.053s</td><td><span class="badge b-red">+383.66%</span></td><td><span class="status s-failed">HIGH CAP SENSITIVITY / EXPOSED</span></td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>512K</td><td>29.624s</td><td>43.095s</td><td><span class="badge b-green">+45.47%</span></td><td>128.275s</td><td><span class="badge b-red">+333.01%</span></td><td><span class="status s-failed">HIGH CAP SENSITIVITY / EXPOSED</span></td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>1M</td><td>68.197s</td><td>92.992s</td><td><span class="badge b-green">+36.36%</span></td><td>256.889s</td><td><span class="badge b-red">+276.69%</span></td><td><span class="status s-failed">HIGH CAP SENSITIVITY / EXPOSED</span></td></tr>"""
    
    h = h[:tbody_start] + new_tbody + h[tbody_end:]
    print("Replaced heatmap tbody successfully!")

# 2. Replace mathematically certain offload note
offload_old = "While offload was disabled during active serving benchmarks, the physical bounds are mathematically certain: reloading latent KV from host DRAM costs only ~0.3% of a full prefill (0.14s vs 93.3s)."
offload_new = "While initial offload serving runs failed to start (rc=1; verified in Stage 2), bandwidth calculations indicate reloading latent KV from host DRAM costs ~0.14s (tested empirically in Stage 2 with DDR5 swapping)."
if offload_old in h:
    h = h.replace(offload_old, offload_new)
    print("Replaced offload mathematically certain note!")
else:
    print("Could not find exact offload note, searching regex...")
    h = re.sub(
        r"While offload was disabled.*?the physical bounds are mathematically certain:.*?\(0\.14s vs 93\.3s\)\.",
        offload_new,
        h
    )

# 3. Replace KD#3 chart block
kd3_pos = h.find('if (pageId === 3)')
if kd3_pos != -1:
    kd4_pos = h.find('else if (pageId === 4)', kd3_pos)
    new_kd3_block = """if (pageId === 3) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.indexAxis = 'y';
            opt1.scales.x.title = { display: true, text: 'Work Growth Factor 128K → 512K (×, 16-Rank Aggregates)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['AllReduce Intra', 'MoE Experts', 'KDA Recurrent', 'SendRecv Inter P2P', 'GEMM Family', 'Full Attention (p≈1.99)'],
                    datasets: [{
                        label: 'Relative Growth (128K → 512K)',
                        data: [2.71, 3.80, 3.95, 4.48, 5.25, 15.70],
                        backgroundColor: ['#38bdf8', '#a78bfa', '#fb923c', '#4ade80', '#38bdf8', '#f87171'],
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
            opt2.scales.y.title = { display: true, text: '16-Rank Aggregate Share of GPU Work (%)', color: '#94a3b8' };
            window.kdCharts[cid2] = new Chart(el2, {
                type: 'bar',
                data: {
                    labels: ['Full Attention', 'Intra TP AllReduce', 'Inter-Node SendRecv', 'MoE Experts', 'GEMM', 'KDA'],
                    datasets: [
                        { label: '128K Aggregate Share (%)', data: [14.7, 43.1, 14.9, 8.3, 7.8, 1.9], backgroundColor: 'rgba(56, 189, 248, 0.75)', borderRadius: 3 },
                        { label: '512K Aggregate Share (%)', data: [43.8, 22.4, 12.8, 4.4, 4.8, 1.7], backgroundColor: 'rgba(248, 113, 113, 0.85)', borderRadius: 3 }
                    ]
                },
                options: opt2
            });
        }
    } """
    h = h[:kd3_pos] + new_kd3_block + h[kd4_pos:]
    print("Replaced KD#3 chart block successfully!")

with open(dash_file, "w", encoding="utf-8") as f:
    f.write(h)

print("Saved HTML!")
