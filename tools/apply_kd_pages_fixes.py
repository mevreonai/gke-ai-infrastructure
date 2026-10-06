import sys, re, json

dash_file = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"

with open(dash_file, "r", encoding="utf-8") as f:
    h = f.read()

# 1. Update KD_PAGES_DATA
pos = h.find('KD_PAGES_DATA = [')
end_pos = h.find(';\n', pos)
data_str = h[pos + len('KD_PAGES_DATA = '):end_pos]
data = json.loads(data_str)

for p in data:
    pid = p.get('id')
    # Page 1: Fabric exposure
    if pid == 1:
        # Disentangle the mechanism takeaway
        new_takeaways = []
        for t in p.get('takeaways', []):
            if "SendRecv ceiling drops 7.11 → 2.04 GB/s with 16 KiB latency rising to 227–290 µs across 37.7 MB per call" in t:
                new_takeaways.append(
                    "TP16/PP1 is severely exposed to transport degradation because AllReduce collectives (37.7 MB per prefill call) are serialized over the cross-node fabric on every layer (+188.69s tax @ 1M; 16 KiB cross-node AllReduce latency is 227–290 µs on native fabric, and inter-node SendRecv ceiling drops 7.11 → 2.04 GB/s under 20G cap)."
                )
            else:
                new_takeaways.append(t)
        p['takeaways'] = new_takeaways

    # Page 3: Resource pressure shift
    elif pid == 3:
        p['hero_points'] = [
            {'val': '15.7×', 'label': 'Full Attention Work', 'color': '#f87171', 'sub': 'empirical p≈1.99 (super-linear)'},
            {'val': '4.5×', 'label': 'SendRecv P2P Work', 'color': '#4ade80', 'sub': '4.31 → 19.29 s (16-rank sum, nsys eager)'},
            {'val': '2.7×', 'label': 'AllReduce Intra Work', 'color': '#38bdf8', 'sub': '12.44 → 33.75 s (16-rank sum, nsys eager)'}
        ]
        p['confidence']['notes'] = 'Direct Nsight multi-node prefill kernel breakdown on TP4/PP4 (16-rank aggregate, nsys eager mode, start-up broadcast excluded; single-node PyTorch profiles do not cover multi-node prefill).'
        p['quick_comp'] = {
            'title': 'Subsystem Growth Factors (128K → 512K 16-Rank Aggregates)',
            'headers': ['Subsystem / Kernel Group', '128K Work Share', '512K Work Share', 'Growth Factor', 'Empirical Scaling / Work Times', 'Evidence'],
            'rows': [
                ['Full Attention (FlashAttention)', '14.7%', "<span style='color:#f87171;font-weight:700'>43.8%</span>", "<span style='color:#f87171;font-weight:700'>~15.70×</span>", 'p ≈ 1.99 (1.47 → 23.08 s)', '16-rank aggregate (nsys eager)'],
                ['AllReduce (Intra-Node TP)', '43.1%', '22.4%', '~2.71×', '12.44 → 33.75 s (2.7× growth)', '16-rank aggregate (nsys eager)'],
                ['SendRecv (Inter-Node P2P)', '14.9%', '12.8%', "<span style='color:#4ade80;font-weight:700'>~4.48×</span>", '4.31 → 19.29 s (4.5× growth)', '16-rank aggregate (nsys eager)'],
                ['MoE Expert Fused Kernels', '8.3%', '4.4%', '~3.80×', 'p ≈ 0.96 (near-linear)', '16-rank aggregate (nsys eager)'],
                ['GEMM Family (Projections)', '7.8%', '4.8%', '~5.25×', 'p ≈ 1.20', '16-rank aggregate (nsys eager)'],
                ['KDA Recurrent Kernels', '1.9%', '1.7%', '~3.95×', 'p ≈ 0.99 (near-linear)', '16-rank aggregate (nsys eager)']
            ]
        }

    # Page 5: Prompt token admission
    elif pid == 5:
        new_takeaways = []
        for t in p.get('takeaways', []):
            if "usable capacity is 1.8× (SLO-conditioned knee)" in t:
                new_takeaways.append(
                    "The 8K-vs-128K gap in usable throughput is 1.8×: 24,977 vs 13,967 tok/s (prompt + output) at the highest load that keeps p95 TPOT ≤ 100 ms with ≥ 90% of the offered rate served (8K at 0.75×, 128K at 0.50×; prompt tokens alone give 24,220 vs 13,940 tok/s = 1.7×)."
                )
            else:
                new_takeaways.append(t)
        p['takeaways'] = new_takeaways

    # Page 7: TP decode
    elif pid == 7:
        # Delete duplicate pointer takeaway
        seen_pointer = False
        new_takeaways = []
        for t in p.get('takeaways', []):
            if "Cross-Node & Pipeline Decode Pointer" in t:
                if not seen_pointer:
                    new_takeaways.append(t)
                    seen_pointer = True
            else:
                new_takeaways.append(t)
        p['takeaways'] = new_takeaways

    # Page 8: Runtime knobs
    elif pid == 8:
        new_takeaways = []
        for t in p.get('takeaways', []):
            if "16K chunk size Pareto-dominates 8K and 4K under concurrency" in t:
                new_takeaways.append(
                    "16K is the better default for ≥128K prompts: lowest c1 TTFT at 128K–1M (-27.1% at 1M) and lowest c4 mean TPOT (141.3 → 119.3 → 105.1 ms); not dominant on every axis (at 128K c4, TTFT is 10.88s vs 8K's 10.66s)."
                )
            else:
                new_takeaways.append(t)
        p['takeaways'] = new_takeaways

    # Page 9: Busy GPU
    elif pid == 9:
        p['chart_primary_title'] = "Reported GPU Utilization (%) [nvidia-smi sampler]"

new_data_str = json.dumps(data, indent=2, ensure_ascii=False)
h = h[:pos + len('KD_PAGES_DATA = ')] + new_data_str + h[end_pos:]

# 2. Update KD#3 chart datasets in initKeyDiscoveryCharts
old_kd3_chart = """    if (pageId === 3) {
        cleanChart(cid1);
        var el1 = document.getElementById(cid1);
        if (el1) {
            var opt1 = JSON.parse(JSON.stringify(defaultChartOptions));
            opt1.indexAxis = 'y';
            opt1.scales.x.title = { display: true, text: 'Work Growth Factor 128K → 512K (×)', color: '#94a3b8' };
            window.kdCharts[cid1] = new Chart(el1, {
                type: 'bar',
                data: {
                    labels: ['NCCL P2P', 'MoE Experts', 'KDA Recurrent', 'GEMM Family', 'Full Attention (empirical p≈1.99)'],
                    datasets: [{
                        label: 'Relative Growth (128K → 512K)',
                        data: [2.18, 3.80, 3.95, 5.25, 15.70],
                        backgroundColor: ['#4ade80', '#a78bfa', '#fb923c', '#38bdf8', '#f87171'],
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
                    labels: ['Full Attention', 'GEMM', 'MoE', 'Intra TP', 'Inter P2P', 'KDA'],
                    datasets: [
                        { label: '128K Share (%)', data: [22.8, 8.5, 13.2, 40.0, 8.3, 2.7], backgroundColor: 'rgba(56, 189, 248, 0.75)', borderRadius: 3 },
                        { label: '512K Share (%)', data: [44.8, 5.1, 6.2, 35.6, 5.2, 2.7], backgroundColor: 'rgba(248, 113, 113, 0.85)', borderRadius: 3 }
                    ]
                },
                options: opt2
            });
        }
    }"""

new_kd3_chart = """    if (pageId === 3) {
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
    }"""

h = h.replace(old_kd3_chart, new_kd3_chart)

with open(dash_file, "w", encoding="utf-8") as f:
    f.write(h)

print("Saved KD pages updates successfully! New length:", len(h))
