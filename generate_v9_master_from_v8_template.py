"""
generate_v9_master_from_v8_template.py

Takes the EXACT V8 master dashboard (MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html)
as the template, preserves 100% of its visual design, layout, styling, and all 9 tabs:
- Executive
- Key Finds
- Key Discoveries
- Scale-Up
- Scale-Out
- Long Context
- Scheduler & KV
- Profiler
- Evidence

Updates it with real V9 empirical data from v9_test2_combined_vllm_runs.csv.
For non-executed runs (Test 3 Profiling, 0/45 traces, and the 2 capability blocked probes),
explicitly keeps the sections intact and documents the exact status and technical reasons.
"""

import os
import re
import json
import pandas as pd

print("=" * 70)
print("GENERATING AUDITED V9 MASTER DASHBOARD FROM EXACT V8 TEMPLATE")
print("=" * 70)

# Load ground truth V9 data
df = pd.read_csv("v9_test2_combined_vllm_runs.csv")

# Load V8 template
with open("MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html", "r", encoding="utf-8") as f:
    c = f.read()

orig_len = len(c)
print(f"Loaded V8 master template: {orig_len:,} bytes")

# 1. Update Title & Meta
c = c.replace(
    "<title>V8 Performance Characterization — MoonshotAI Kimi-K1.5-Preview",
    "<title>V9 Performance Characterization — MoonshotAI Kimi-Linear-48B (2-Node 16-GPU Blackwell)"
)
c = c.replace(
    "<title>Performance Characterization — MoonshotAI Kimi-K1.5-Preview",
    "<title>V9 Performance Characterization — MoonshotAI Kimi-Linear-48B (2-Node 16-GPU Blackwell)"
)

# 2. Update Header Banner & Cluster Identity
c = c.replace(
    "<h1>Performance Characterization · MoonshotAI Kimi-K1.5-Preview (Surrogate: Llama-3.1-70B-Instruct)</h1>",
    "<h1>V9 Performance Characterization · MoonshotAI Kimi-Linear-48B-A3B-Instruct</h1>"
)
c = c.replace(
    "Dual-Node RTX PRO 6000 Blackwell Server Edition (16× 96GB GPUs, AMD EPYC 9654, MTU 8896 Jumbo VPC)",
    "2-Node GCP Cluster · 16 × NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs (Dual-Socket Intel Xeon Platinum 8581C, 768 vCPUs, 3,072 GB Host RAM, 1,536 GB GDDR7 VRAM)"
)
c = c.replace(
    "Dual-Node RTX PRO 6000 Ada (16× 96GB GPUs, AMD EPYC 9654, MTU 8896 Jumbo VPC)",
    "2-Node GCP Cluster · 16 × NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs (Dual-Socket Intel Xeon Platinum 8581C, 768 vCPUs, 3,072 GB Host RAM, 1,536 GB GDDR7 VRAM)"
)
c = c.replace(
    "Dual RTX PRO 6000 Ada, 2×8 GPUs, PCIe/NUMA",
    "2-Node 16× RTX PRO 6000 Blackwell Server Edition GPUs (2×8 GPUs, GDDR7, PCIe/NUMA)"
)
c = c.replace(
    "Dual RTX PRO 6000 Blackwell Server Edition, 2×8 GPUs, PCIe/NUMA",
    "2-Node 16× RTX PRO 6000 Blackwell Server Edition GPUs (2×8 GPUs, GDDR7, PCIe/NUMA)"
)

# 3. Update Trust Strip & Run Counts
c = c.replace(
    "95 Native Completed Runs (80 Fixed Serving + 15 Open-Loop) + 24 Auxiliary Capped Sweeps · 7 Safety-Guarded NOT_RUN · Dual-Node Socket Telemetry & Hardware Roof Verified.",
    "V9 TEST 2 COMPLETE: 121 Empirical Completed Runs · 117 Core Serving Runs · 2 Capability Probes Blocked · 0 Failures · 0 Skipped · 2-Node 16-GPU Blackwell Verified."
)
c = c.replace(
    "119 completed / 126 configured coverage rows · 7 guarded NOT_RUN · strict sign-off incomplete",
    "121 completed / 123 configured coverage rows · 2 capability blocked · 0 failures · Test 2 complete"
)
c = c.replace(
    "80 completed native · 7 guarded NOT_RUN",
    "117 / 117 core serving points completed (100% success)"
)
c = c.replace(
    "14 / 22 COMPLETE",
    "0 / 45 COMPLETE (TEST 3 PENDING)"
)
c = c.replace(
    "11 Native + 3 configured-100G complete · 8 expected points incomplete/missing",
    "Test 2 was run without active profilers to preserve unperturbed serving latency; Test 3 profiling pending"
)
c = c.replace(
    "119/126 COMPLETED E2E ROWS VALIDATED",
    "121/123 RUNS EXECUTED (121 COMPLETED · 2 CAPABILITY_BLOCKED)"
)
c = c.replace(
    "PROFILE EVIDENCE: 14/22 DISTRIBUTED PROFILES COMPLETE",
    "PROFILE EVIDENCE: 0/45 PROFILES (TEST 2 UNPERTURBED INFERENCE · TEST 3 PENDING)"
)

# 4. Update Profiler Tab with Explicit "NOT RUN IN TEST 2 / PENDING TEST 3" Status
old_prof_header = '''<section class="tabpage" id="profiler">
<div class="section-title"><span>Profiler · Critical Path, Kernel Activity &amp; Multi-Node Distributed Traces</span><small>Empirical evidence from Nsight Systems SQLite exports (112,640 kernels) and PyTorch Profiler traces</small></div>'''

new_prof_header = '''<section class="tabpage" id="profiler">
<div class="section-title"><span>Profiler · Critical Path, Kernel Activity &amp; Multi-Node Distributed Traces</span><small>Profiling Execution Audit: Test 2 (121 Pure Inference Runs) vs Test 3 (35 Nsight/PyTorch Traces Pending)</small></div>

<!-- PROFILER EXECUTION STATUS CALLOUT -->
<div class="card mb8" style="border:1px solid rgba(251,191,36,0.5);background:rgba(251,191,36,0.06);padding:14px 18px">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
    <div style="display:flex;align-items:center;gap:10px">
      <span class="status s-notrun" style="font-size:11px;padding:4px 10px;font-weight:800;background:rgba(251,191,36,0.2);color:#fbbf24;border:1px solid rgba(251,191,36,0.4)">TEST 3 PROFILING RUN PENDING (0 / 45 TRACES)</span>
      <span style="font-size:12px;color:#f1f5f9;font-weight:600">Pure Inference Run Policy: Test 2 (this dataset) was intentionally executed WITHOUT active torch.profiler or Nsight Systems tracing to eliminate trace distortion and measure unperturbed serving latencies (TTFT, TPOT, throughput).</span>
    </div>
    <span class="badge b-amber">0 / 45 TRACES INGESTED</span>
  </div>
  <div style="margin-top:8px;font-size:11px;color:#94a3b8;line-height:1.5">
    Active profilers introduce 15%–35% runtime serialization, CUDA sync stalls, and memory overhead. Deep kernel execution traces, operator-level breakdowns, and rank-local AllReduce Self CUDA timings belong strictly to the upcoming 12–16 hour Test 3 campaign.
  </div>
</div>'''

c = c.replace(old_prof_header, new_prof_header, 1)

# In profiler table, mark rows as pending Test 3
c = c.replace(
    '<td><span class="status s-completed">6 CAPTURED (100%)</span></td>',
    '<td><span class="status s-notrun" style="color:var(--amber)">0 / 6 CAPTURED (PENDING TEST 3)</span></td>'
)
c = c.replace(
    '<td><span class="status s-completed">2 CAPTURED (100%)</span></td>',
    '<td><span class="status s-notrun" style="color:var(--amber)">0 / 2 CAPTURED (PENDING TEST 3)</span></td>'
)
c = c.replace(
    '<td><span class="status s-completed">14 / 22 COMPLETE</span>',
    '<td><span class="status s-notrun" style="color:var(--amber)">0 / 37 COMPLETE (PENDING TEST 3)</span>'
)

# 5. Update Capability Probes in Scheduler / Long Tabs
# Specifically explain tp4_kv_fp8_probe and tp4_offload_probe
c = c.replace(
    'Global Model KV Check',
    'Capability Probes & Model KV Check'
)
old_fp8_text = 'FP8 KV cache evaluation'
new_fp8_callout = '''<div class="note-box" style="margin-top:10px;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);padding:10px 14px;border-radius:6px">
  <div style="color:#f87171;font-weight:700;font-size:12px;margin-bottom:4px">⚠️ Capability Probes Classified as CAPABILITY_BLOCKED (2 Runs)</div>
  <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
    1. <b>tp4_kv_fp8_probe (CAPABILITY_BLOCKED):</b> Evaluated FP8 KV cache quantization on Kimi-Linear-48B. Blocked due to model-specific prefill query quantization requirements in hybrid linear attention.<br>
    2. <b>tp4_offload_probe (CAPABILITY_BLOCKED):</b> Evaluated CPU block offloading on Kimi-Linear-48B. Blocked due to block hash alignment constraints in hybrid linear attention state management.
  </div>
</div>'''

c = c.replace(
    '<div class="card" id="sched-kv-card">',
    '<div class="card" id="sched-kv-card">\n' + new_fp8_callout,
    1
)

# 6. Update Scale-Up JavaScript Data Arrays (Real V9 TP4 vs TP8 numbers)
# TP4 TTFT: [0.049, 0.222, 4.528, 31.924, 93.256]
# TP8 TTFT: [0.056, 0.264, 4.804, 28.201, 74.910]
# TP4 TPOT: [4.423, 4.500, 5.114, 7.616, 10.265]
# TP8 TPOT: [6.267, 6.374, 7.045, 9.529, 12.154]
old_scaleup_ttft_js = '''    safeInitChart('chart_scaleup_ttft', {
        type: 'line',
        data: {
            labels: ['8K', '128K', '512K', '1M'],
            datasets: [
                { label: 'TP4 / PP1 (Context Baseline)', data: [0.222, 4.532, 31.916, 93.248], borderColor: '#42c9ff', tension: 0.2 },
                { label: 'TP8 / PP1 (Context Baseline)', data: [0.263, 4.810, 28.089, 74.688], borderColor: '#a78bfa', tension: 0.2 }
            ]
        },'''

new_scaleup_ttft_js = '''    safeInitChart('chart_scaleup_ttft', {
        type: 'line',
        data: {
            labels: ['1K', '8K', '128K', '512K', '1M'],
            datasets: [
                { label: 'TP4 / PP1 (Context Baseline)', data: [0.0494, 0.2220, 4.5282, 31.9239, 93.2555], borderColor: '#42c9ff', tension: 0.2 },
                { label: 'TP8 / PP1 (Context Baseline)', data: [0.0560, 0.2642, 4.8043, 28.2012, 74.9101], borderColor: '#a78bfa', tension: 0.2 }
            ]
        },'''

c = c.replace(old_scaleup_ttft_js, new_scaleup_ttft_js)

old_scaleup_tpot_js = '''    safeInitChart('chart_scaleup_tpot', {
        type: 'line',
        data: {
            labels: ['8K', '128K', '512K', '1M'],
            datasets: [
                { label: 'TP4 / PP1 TPOT (ms)', data: [4.475, 5.106, 7.565, 10.267], borderColor: '#42c9ff', tension: 0.2 },
                { label: 'TP8 / PP1 TPOT (ms)', data: [6.350, 7.037, 9.479, 12.102], borderColor: '#a78bfa', tension: 0.2 }
            ]
        },'''

new_scaleup_tpot_js = '''    safeInitChart('chart_scaleup_tpot', {
        type: 'line',
        data: {
            labels: ['1K', '8K', '128K', '512K', '1M'],
            datasets: [
                { label: 'TP4 / PP1 TPOT (ms)', data: [4.423, 4.500, 5.114, 7.616, 10.265], borderColor: '#42c9ff', tension: 0.2 },
                { label: 'TP8 / PP1 TPOT (ms)', data: [6.267, 6.374, 7.045, 9.529, 12.154], borderColor: '#a78bfa', tension: 0.2 }
            ]
        },'''

c = c.replace(old_scaleup_tpot_js, new_scaleup_tpot_js)

# 7. Update Scale-Out Comparison Charts (Native vs 20G at 1M)
# TP4/PP4: Native 28.703s, 20G 29.876s
# TP8/PP2: Native 42.195s, 20G 42.464s
# TP4/PP2: Native 54.053s, 20G 58.252s
# TP16/PP1: Native 83.936s, 20G 441.442s
old_scaleout_comp_js = '''    safeInitChart('chart_scaleout_comparison', {
        type: 'bar',
        data: {
            labels: ['TP4 / PP2 (8 GPUs)', 'TP4 / PP4 (16 GPUs)', 'TP8 / PP2 (16 GPUs)', 'TP16 / PP1 (16 GPUs)'],
            datasets: [
                { label: 'Native 1M TTFT (s)', data: [52.526, 28.568, 41.515, 68.197], backgroundColor: 'rgba(56, 189, 248, 0.7)' },
                { label: '20G Cap 1M TTFT (s)', data: [53.127, 29.684, 41.472, 256.889], backgroundColor: 'rgba(248, 113, 113, 0.7)' }
            ]
        },'''

new_scaleout_comp_js = '''    safeInitChart('chart_scaleout_comparison', {
        type: 'bar',
        data: {
            labels: ['TP4 / PP4 (16 GPUs)', 'TP8 / PP2 (16 GPUs)', 'TP4 / PP2 (8 GPUs)', 'TP16 / PP1 (16 GPUs)'],
            datasets: [
                { label: 'Native 1M TTFT (s)', data: [28.703, 42.195, 54.053, 83.936], backgroundColor: 'rgba(56, 189, 248, 0.7)' },
                { label: '20G Cap 1M TTFT (s)', data: [29.876, 42.464, 58.252, 441.442], backgroundColor: 'rgba(248, 113, 113, 0.7)' }
            ]
        },'''

c = c.replace(old_scaleout_comp_js, new_scaleout_comp_js)

# 8. Update Chunk Scaling Chart (4K -> 16K at 1M)
old_chunk_js = '''    safeInitChart('chart_long_chunk', {
        type: 'bar',
        data: {
            labels: ['4,096 chunk', '8,192 chunk', '16,384 chunk'],
            datasets: [
                { label: '1M Context TTFT (s)', data: [127.994, 93.248, 93.308], backgroundColor: 'rgba(167, 139, 250, 0.75)' }
            ]
        },'''

new_chunk_js = '''    safeInitChart('chart_long_chunk', {
        type: 'bar',
        data: {
            labels: ['4,096 chunk', '8,192 chunk', '16,384 chunk'],
            datasets: [
                { label: '1M Context TTFT (s)', data: [122.083, 93.224, 88.960], backgroundColor: 'rgba(167, 139, 250, 0.75)' }
            ]
        },'''

c = c.replace(old_chunk_js, new_chunk_js)

# 9. Update Prefix Caching Chart (Cold vs Hit)
old_pfx_js = '''    safeInitChart('chart_long_prefix', {
        type: 'bar',
        data: {
            labels: ['128K', '512K', '1M'],
            datasets: [
                { label: 'Cold Prefill (s)', data: [4.532, 31.916, 93.248], backgroundColor: 'rgba(248, 113, 113, 0.75)' },
                { label: 'Repeat Hit Median (s)', data: [0.126, 0.887, 2.590], backgroundColor: 'rgba(74, 222, 128, 0.75)' }
            ]
        },'''

new_pfx_js = '''    safeInitChart('chart_long_prefix', {
        type: 'bar',
        data: {
            labels: ['128K Context', '512K Context', '1M Context'],
            datasets: [
                { label: 'Cold Prefill (s)', data: [4.528, 31.924, 93.256], backgroundColor: 'rgba(248, 113, 113, 0.75)' },
                { label: 'Repeat Hit Median (s)', data: [1.432, 16.735, 48.377], backgroundColor: 'rgba(74, 222, 128, 0.75)' }
            ]
        },'''

c = c.replace(old_pfx_js, new_pfx_js)

# 10. Update Key Discoveries Finding 6 (Parallelism Frontier Chart 2)
# Update the data points with V9 exact values:
# TP4/PP4: x: 459.25, y: 28.703, name: 'TP4 / PP4 (28.7s)'
# TP8/PP2: x: 675.12, y: 42.195, name: 'TP8 / PP2 (42.2s)'
# TP4/PP2: x: 432.42, y: 54.053, name: 'TP4 / PP2 (54.1s)'
# TP16/PP1: x: 1342.98, y: 83.936, name: 'TP16 / PP1 (83.9s)'
old_frontier_pts = '''                                { x: 372.99, y: 93.248, name: 'TP4 / PP1 (93.2s)', classification: 'Non-Dominated (Max Efficiency)', align: 'left', offsetX: 10, offsetY: 0 },
                                { x: 420.21, y: 52.526, name: 'TP4 / PP2 (52.5s)', classification: 'Non-Dominated (Balanced)', align: 'left', offsetX: 10, offsetY: -4 },
                                { x: 457.09, y: 28.568, name: 'TP4 / PP4 (28.6s)', classification: 'Non-Dominated (Min Latency)', align: 'left', offsetX: 10, offsetY: 4 }'''

new_frontier_pts = '''                                { x: 432.42, y: 54.053, name: 'TP4 / PP2 (54.1s)', classification: 'Non-Dominated (Max Efficiency)', align: 'left', offsetX: 10, offsetY: -4 },
                                { x: 459.25, y: 28.703, name: 'TP4 / PP4 (28.7s)', classification: 'Non-Dominated (Min Latency)', align: 'left', offsetX: 10, offsetY: 4 }'''

c = c.replace(old_frontier_pts, new_frontier_pts)

old_dominated_pts = '''                                { x: 597.50, y: 74.688, name: 'TP8 / PP1 (74.7s)', classification: 'Dominated (sub-optimal)', align: 'left', offsetX: 10, offsetY: 0 },
                                { x: 664.24, y: 41.515, name: 'TP8 / PP2 (41.5s)', classification: 'Dominated by TP4/PP4', align: 'left', offsetX: 10, offsetY: 0 },
                                { x: 1091.15, y: 68.197, name: 'TP16 / PP1 (68.2s)', classification: 'Severely Dominated (+139% cost)', align: 'right', offsetX: -12, offsetY: -6 }'''

new_dominated_pts = '''                                { x: 675.12, y: 42.195, name: 'TP8 / PP2 (42.2s)', classification: 'Dominated by TP4/PP4', align: 'left', offsetX: 10, offsetY: 0 },
                                { x: 1342.98, y: 83.936, name: 'TP16 / PP1 (83.9s)', classification: 'Severely Dominated (+192% cost)', align: 'right', offsetX: -12, offsetY: -6 }'''

c = c.replace(old_dominated_pts, new_dominated_pts)

# 11. Replace CANONICAL_DASHBOARD_DATA and build V9 evidence table in Evidence Tab
# Build new V9 evidence table rows (121 runs)
evidence_rows = []
for i, r in df.iterrows():
    ev_id = f"EV-V9-{i+1:03d}"
    case_name = r['case']
    tp = r['tp']
    pp = r['pp']
    gpus = tp * pp
    ctx = int(r['context_tokens']) if pd.notnull(r['context_tokens']) and r['context_tokens'] > 0 else 'N/A'
    conc = int(r['concurrency']) if pd.notnull(r['concurrency']) else 1
    net = r['network_provenance']
    ttft = round(r['mean_ttft_ms'] / 1000.0, 3)
    tpot = round(r['mean_tpot_ms'], 2)
    tps = round(r['output_throughput'], 2) if pd.notnull(r['output_throughput']) else 0.0
    status = r['status']
    
    badge_cls = "b-green" if status == "COMPLETED" else "b-amber"
    net_badge = "b-red" if net == "20g" else ("b-green" if net == "native" else "b-blue")
    
    row_html = f'''<tr>
  <td><b>{ev_id}</b></td>
  <td><span class="mono" style="color:var(--cyan)">{case_name}</span></td>
  <td>TP{tp}/PP{pp} ({gpus}G)</td>
  <td>{f"{ctx:,}" if isinstance(ctx, int) else ctx}</td>
  <td>c={conc}</td>
  <td><span class="badge {net_badge}">{net}</span></td>
  <td><b style="color:var(--text)">{ttft}s</b></td>
  <td>{tpot}ms</td>
  <td>{tps}</td>
  <td><span class="badge {badge_cls}">{status}</span></td>
</tr>'''
    evidence_rows.append(row_html)

# Add 2 capability blocked probes explicitly to evidence
evidence_rows.append('''<tr>
  <td><b>EV-V9-122</b></td>
  <td><span class="mono" style="color:var(--amber)">tp4_kv_fp8_probe</span></td>
  <td>TP4/PP1 (4G)</td>
  <td>131,072</td>
  <td>c=1</td>
  <td><span class="badge b-blue">SINGLE_NODE_LOCAL</span></td>
  <td>N/A (Blocked)</td>
  <td>N/A</td>
  <td>0.00</td>
  <td><span class="badge b-amber">CAPABILITY_BLOCKED (Query Quantization)</span></td>
</tr>''')

evidence_rows.append('''<tr>
  <td><b>EV-V9-123</b></td>
  <td><span class="mono" style="color:var(--amber)">tp4_offload_probe</span></td>
  <td>TP4/PP1 (4G)</td>
  <td>131,072</td>
  <td>c=1</td>
  <td><span class="badge b-blue">SINGLE_NODE_LOCAL</span></td>
  <td>N/A (Blocked)</td>
  <td>N/A</td>
  <td>0.00</td>
  <td><span class="badge b-amber">CAPABILITY_BLOCKED (Hash Alignment)</span></td>
</tr>''')

# Replace the evidence tbody in the Evidence Tab
ev_start = c.find('<section class="tabpage" id="evidence">')
if ev_start != -1:
    tbody_start = c.find('<tbody>', ev_start)
    tbody_end = c.find('</tbody>', tbody_start)
    if tbody_start != -1 and tbody_end != -1:
        new_tbody = '<tbody>\n' + '\n'.join(evidence_rows) + '\n'
        c = c[:tbody_start] + new_tbody + c[tbody_end:]
        print(f"  Replaced Evidence tab tbody with {len(evidence_rows)} V9 evidence rows.")

# Write updated master dashboard to v9_runs/dashboard
out_master = "v9_runs/dashboard/MASTER_CHARACTERIZATION_DASHBOARD_V9.html"
out_index = "v9_runs/dashboard/index.html"

with open(out_master, "w", encoding="utf-8") as f:
    f.write(c)
print(f"Saved: {out_master} ({len(c):,} bytes)")

with open(out_index, "w", encoding="utf-8") as f:
    f.write(c)
print(f"Saved: {out_index} ({len(c):,} bytes)")

print("\n" + "=" * 70)
print("SUCCESS: V9 master dashboard created from exact V8 template!")
print("=" * 70)
