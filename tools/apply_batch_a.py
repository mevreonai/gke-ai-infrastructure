import json
import csv
import os
import re
import datetime

print("Running tools/apply_batch_a.py...")

# 1. Load authoritative typed data
with open('data/evidence.json', 'r', encoding='utf-8') as f:
    full_data = json.load(f)

meta = full_data['meta']
rows = full_data['rows']
missing = full_data['missing_configured_cases']

# Load HTML
dashboard_path = 'MASTER_CHARACTERIZATION_DASHBOARD.html'
with open(dashboard_path, 'r', encoding='utf-8') as f:
    html = f.read()

# ==============================================================================
# PHASE 2: EXECUTIVE TAB REMEDIATION (Spec §5)
# ==============================================================================

# Executive KPI 1: TP4 Decode Qualification
old_kpi1 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap">🏆</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Best Decode (Qualification)</div>
          <div class="kpi-main-val">TP4</div>
          <div class="kpi-sub-text">Lower TPOT in tested points</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>"""

new_kpi1 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">🏆</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Decode-Optimal in Matched Tests</div>
          <div class="kpi-main-val" style="color:#38bdf8;">TP4</div>
          <div class="kpi-sub-text">Lower TPOT in matched 8K/128K/512K c1 tests (4.45ms @ 8K vs 6.35ms for TP8)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>"""

# Executive KPI 2: TP8 Long-Prefill
old_kpi2 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap">🧊</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Potential Long-Prefill Challenger</div>
          <div class="kpi-main-val">TP8</div>
          <div class="kpi-sub-text">512K TTFT lead observed; needs full V6 confirmation</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>"""

new_kpi2 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fb923c;">🔀</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Large-Context Prefill Crossover</div>
          <div class="kpi-main-val" style="color:#fb923c;">TP8</div>
          <div class="kpi-sub-text">Lower TTFT at 512K (28.2s vs 32.0s) & 1M c1 (74.9s vs 93.4s); trade-off vs decode latency</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>"""

# Executive KPI 3: Qualification Status / V6 Matrix Coverage Summary
old_kpi3 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap">✅</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Qualification Status</div>
          <div class="kpi-main-val">8/8 Passed</div>
          <div class="kpi-sub-text">0 failed requests · 0 preemptions</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>"""

new_kpi3 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">📊</div>
        <div class="kpi-big-info">
          <div class="kpi-label">V6 Matrix Coverage</div>
          <div class="kpi-main-val" style="color:#34d399;">58/64 + 1 Extra</div>
          <div class="kpi-sub-text">8/8 qualification runs raw-validated (51 pending raw re-validation; 6 cases absent)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>"""

# Executive KPI 4: Runtime Reserve
old_kpi4 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap">∑</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Runtime Reserve</div>
          <div style="font-size:11px; font-weight:700; color:#cbd5e1; font-family:monospace; margin-top:2px;">
            Tworkload = AGPU + BTP + CPP + DPCIe/offload + EvLLM + FCPU/launch + Gother - Ooverlap
          </div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-k3"><span class="dot"></span>CONCEPT</span></div>
    </div>"""

new_kpi4 = """    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">∑</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Runtime Reserve Equation (Algebraic Ledger)</div>
          <div style="font-size:10px; font-weight:700; color:#cbd5e1; font-family:monospace; margin-top:2px;">
            T_workload = A_GPU + B_TP + C_PP + D_PCIe + E_vLLM + F_CPU + G_other - O_overlap
          </div>
          <div class="kpi-sub-text">Unresolved ledger: no synthetic percentages; PP=N/A on PP1 single-node</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-derived"><span class="dot"></span>DERIVED</span></div>
    </div>"""

html = html.replace(old_kpi1, new_kpi1)
html = html.replace(old_kpi2, new_kpi2)
html = html.replace(old_kpi3, new_kpi3)
html = html.replace(old_kpi4, new_kpi4)

# Executive Takeaways annotations replacement
old_exec_charts = """      <div class="charts-3row">
        <!-- Chart 1: TTFT vs Context -->
        <div class="chart-unit">
          <div class="chart-unit-head">
            <span class="chart-unit-title">TTFT vs Context (Qualification) <span style="color:var(--text-dim);">ℹ</span></span>
            <span class="pill-badge badge-m" style="padding:1px 4px; font-size:7.5px;"><span class="dot"></span>MEASURED-48B</span>
          </div>
          <div class="chart-canvas-box"><canvas id="canvasExecTtft"></canvas></div>
          <div class="takeaways-box">
            <strong>Key Takeaways</strong>
            <ul>
              <li>Observation: TP4 leads at 8K and 128K; TP8 leads at 512K in qualification.</li>
              <li>Interpretation: Decode-favoring TP4 vs possible large-prefill TP8 crossover.</li>
              <li>Action: Validate with full V6 and 1M runs.</li>
            </ul>
          </div>
        </div>

        <!-- Chart 2: TPOT vs Context -->
        <div class="chart-unit">
          <div class="chart-unit-head">
            <span class="chart-unit-title">TPOT vs Context (Qualification) <span style="color:var(--text-dim);">ℹ</span></span>
            <span class="pill-badge badge-m" style="padding:1px 4px; font-size:7.5px;"><span class="dot"></span>MEASURED-48B</span>
          </div>
          <div class="chart-canvas-box"><canvas id="canvasExecTpot"></canvas></div>
          <div class="takeaways-box">
            <strong>Key Takeaways</strong>
            <ul>
              <li>Observation: TP4 has lower TPOT across tested contexts.</li>
              <li>Interpretation: TP communication / NUMA overhead likely hurts TP8 decode.</li>
              <li>Action: Use TP4 as current decode-sensitive baseline.</li>
            </ul>
          </div>
        </div>

        <!-- Chart 3: 8K c8 Output Throughput -->
        <div class="chart-unit">
          <div class="chart-unit-head">
            <span class="chart-unit-title">8K c8 Output Throughput <span style="color:var(--text-dim);">ℹ</span></span>
            <span class="pill-badge badge-m" style="padding:1px 4px; font-size:7.5px;"><span class="dot"></span>MEASURED-48B</span>
          </div>
          <div class="chart-canvas-box"><canvas id="canvasExecTps"></canvas></div>
          <div class="takeaways-box">
            <strong>Key Takeaways</strong>
            <ul>
              <li>Observation: TP4 delivers higher 8K c8 output throughput.</li>
              <li>Interpretation: Better decode efficiency outweighs extra TP8 parallelism at this workload.</li>
              <li>Action: Prefer TP4 for low-latency, high-interactivity serving.</li>
            </ul>
          </div>
        </div>
      </div>"""

new_exec_charts = """      <div class="charts-3row">
        <!-- Chart 1: TTFT vs Context -->
        <div class="chart-unit">
          <div class="chart-unit-head">
            <span class="chart-unit-title">TTFT vs Context (Qualification) <span style="color:var(--text-dim);">ℹ</span></span>
            <span class="pill-badge badge-m" style="padding:1px 4px; font-size:7.5px;"><span class="dot"></span>MEASURED-48B</span>
          </div>
          <div class="chart-canvas-box"><canvas id="canvasExecTtft"></canvas></div>
          <div class="takeaways-box">
            <strong>Audit Annotation</strong>
            <ul>
              <li><strong>Observation:</strong> TP4 TTFT is 224.3ms @ 8K, 4,534ms @ 128K, 31,956ms @ 512K; TP8 is 267.7ms @ 8K, 4,820ms @ 128K, 28,217ms @ 512K.</li>
              <li><strong>Interpretation [High]:</strong> TP4 leads up to 128K due to lower TP overhead; TP8 leads at 512K (+11.7% speedup) due to compute parallelism.</li>
              <li><strong>Decision:</strong> Workload-scoped: prefer TP4 for &le;128K context; evaluate TP8 for &ge;512K context.</li>
              <li><strong>Next evidence:</strong> 1M baseline verification; chunked prefill timeline.</li>
              <li><strong>Evidence:</strong> MEASURED-48B (raw-validated) · tp4_qualification, tp8_qualification · N=12 requests (86 samples).</li>
            </ul>
          </div>
        </div>

        <!-- Chart 2: TPOT vs Context -->
        <div class="chart-unit">
          <div class="chart-unit-head">
            <span class="chart-unit-title">TPOT vs Context (Qualification) <span style="color:var(--text-dim);">ℹ</span></span>
            <span class="pill-badge badge-m" style="padding:1px 4px; font-size:7.5px;"><span class="dot"></span>MEASURED-48B</span>
          </div>
          <div class="chart-canvas-box"><canvas id="canvasExecTpot"></canvas></div>
          <div class="takeaways-box">
            <strong>Audit Annotation</strong>
            <ul>
              <li><strong>Observation:</strong> TP4 TPOT is 4.45ms @ 8K, 5.08ms @ 128K, 7.58ms @ 512K; TP8 is 6.35ms @ 8K, 7.03ms @ 128K, 9.47ms @ 512K.</li>
              <li><strong>Interpretation [High]:</strong> TP4 exhibits 25–30% lower decode token latency across all tested contexts due to lower all-reduce overhead.</li>
              <li><strong>Decision:</strong> For interactive decode-latency-sensitive serving, select TP4.</li>
              <li><strong>Next evidence:</strong> Concurrency decode sweeps (c1–c32).</li>
              <li><strong>Evidence:</strong> MEASURED-48B (raw-validated) · tp4_qualification, tp8_qualification · N=12 requests.</li>
            </ul>
          </div>
        </div>

        <!-- Chart 3: 8K c8 Output Throughput -->
        <div class="chart-unit">
          <div class="chart-unit-head">
            <span class="chart-unit-title">8K c8 Output Throughput <span style="color:var(--text-dim);">ℹ</span></span>
            <span class="pill-badge badge-m" style="padding:1px 4px; font-size:7.5px;"><span class="dot"></span>MEASURED-48B</span>
          </div>
          <div class="chart-canvas-box"><canvas id="canvasExecTps"></canvas></div>
          <div class="takeaways-box">
            <strong>Audit Annotation</strong>
            <ul>
              <li><strong>Observation:</strong> At 8K c8, TP4 delivers 555.0 tok/s vs TP8 445.8 tok/s (+24.5% higher throughput for TP4).</li>
              <li><strong>Interpretation [High]:</strong> Superior decode efficiency per token on TP4 dominates at moderate concurrency.</li>
              <li><strong>Decision:</strong> Select TP4 for 8K batched interactive serving.</li>
              <li><strong>Next evidence:</strong> Memory bandwidth profiling during batched decode.</li>
              <li><strong>Evidence:</strong> MEASURED-48B (raw-validated) · tp4_qualification::8k_c8, tp8_qualification::8k_c8 · N=12 requests.</li>
            </ul>
          </div>
        </div>
      </div>"""

html = html.replace(old_exec_charts, new_exec_charts)

# Executive Serving Envelope Heatmap: measured-only cells (8K, 128K, 512K, 1M)
old_envelope = """    <!-- Serving Envelope -->
    <div class="envelope-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <span style="font-size:10px; font-weight:700; color:#fff;">Serving Envelope (Full V6 populates)</span>
        <span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span>
      </div>
      <table class="heatmap-table">
        <thead>
          <tr><th>Context</th><th>c1</th><th>c4</th><th>c8</th><th>c16</th><th>c32</th></tr>
        </thead>
        <tbody>
          <tr><td><strong>8K</strong></td><td class="hm-green">188 tok/s</td><td class="hm-green">412 tok/s</td><td class="hm-green">559 tok/s</td><td class="hm-teal">840 tok/s</td><td class="hm-teal">1,120 tok/s</td></tr>
          <tr><td><strong>32K</strong></td><td class="hm-green">114 tok/s</td><td class="hm-green">280 tok/s</td><td class="hm-teal">420 tok/s</td><td class="hm-teal">610 tok/s</td><td class="hm-yellow">780 tok/s</td></tr>
          <tr><td><strong>64K</strong></td><td class="hm-green">68 tok/s</td><td class="hm-teal">195 tok/s</td><td class="hm-teal">310 tok/s</td><td class="hm-yellow">460 tok/s</td><td class="hm-orange">590 tok/s</td></tr>
          <tr><td><strong>128K</strong></td><td class="hm-teal">24.7 tok/s</td><td class="hm-teal">88 tok/s</td><td class="hm-yellow">142 tok/s</td><td class="hm-orange">210 tok/s</td><td class="hm-red">280 tok/s</td></tr>
          <tr><td><strong>256K</strong></td><td class="hm-yellow">8.4 tok/s</td><td class="hm-yellow">28 tok/s</td><td class="hm-orange">54 tok/s</td><td class="hm-red">82 tok/s</td><td class="hm-gray">Gated</td></tr>
          <tr><td><strong>512K</strong></td><td class="hm-yellow">2.2 tok/s</td><td class="hm-orange">7.8 tok/s</td><td class="hm-red">14 tok/s</td><td class="hm-gray">Gated</td><td class="hm-gray">Gated</td></tr>
          <tr><td><strong>1M</strong></td><td class="hm-orange">0.4 tok/s</td><td class="hm-red">1.5 tok/s</td><td class="hm-gray">Gated</td><td class="hm-gray">Gated</td><td class="hm-gray">Gated</td></tr>
        </tbody>
      </table>
    </div>"""

new_envelope = """    <!-- Serving Envelope (Measured-Only, Spec §5) -->
    <div class="envelope-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <div>
          <span style="font-size:10px; font-weight:700; color:#fff;">Measured Closed-Loop Serving Envelope (TP4)</span>
          <div style="font-size:7.5px; color:var(--text-dim);">Values: output tok/s · Gray = NOT RUN (no synthetic interpolation)</div>
        </div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <table class="heatmap-table">
        <thead>
          <tr><th>Context</th><th>c1</th><th>c2</th><th>c4</th><th>c8</th><th>c16</th><th>c32</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>8K</strong></td>
            <td class="hm-green" title="tp4_closedloop_8k::c1">187.6 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-green" title="tp4_closedloop_8k::c4">415.3 tok/s</td>
            <td class="hm-green" title="tp4_closedloop_8k::c8">559.7 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_8k::c16">673.2 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_8k::c32">774.4 tok/s</td>
          </tr>
          <tr>
            <td><strong>128K</strong></td>
            <td class="hm-teal" title="tp4_closedloop_128k::c1">24.7 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-teal" title="tp4_closedloop_128k::c4">27.2 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_128k::c8">28.0 tok/s</td>
            <td class="hm-teal" title="tp4_closedloop_128k::c16">28.2 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
          </tr>
          <tr>
            <td><strong>512K</strong></td>
            <td class="hm-yellow" title="tp4_closedloop_512k::c1">2.0 tok/s</td>
            <td class="hm-yellow" title="tp4_closedloop_512k::c2">2.0 tok/s</td>
            <td class="hm-yellow" title="tp4_closedloop_512k::c4">2.0 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
          </tr>
          <tr>
            <td><strong>1M</strong></td>
            <td class="hm-orange" title="tp4_closedloop_1m::c1">0.3 tok/s</td>
            <td class="hm-orange" title="tp4_closedloop_1m::c2">0.3 tok/s</td>
            <td class="hm-orange" title="tp4_closedloop_1m::c4">0.3 tok/s</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
            <td class="hm-gray" title="Not tested">NOT RUN</td>
          </tr>
        </tbody>
      </table>
      <div style="font-size:7.5px; color:#94a3b8; margin-top:4px;">
        Note: 32K, 64K, 256K contexts were not in the V6 test matrix. Closed-loop concurrency is not open-loop user capacity.
      </div>
    </div>"""

html = html.replace(old_envelope, new_envelope)

# Executive Runtime Reserve Bar: algebraic component ledger
old_reserve = """    <!-- Runtime Reserve & vLLM Breakdown -->
    <div class="reserve-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <span style="font-size:10px; font-weight:700; color:#fff;">Runtime Reserve & vLLM Breakdown</span>
        <span class="pill-badge badge-local"><span class="dot"></span>LOCAL-REAL</span>
      </div>

      <div class="segmented-bar-wrap">
        <div class="segmented-bar-label">
          <span>TTFT / Prefill Breakdown</span>
          <span>GPU (48%) | TP Comm (22%) | PP Bubble (8%) | vLLM (14%) | CPU (8%)</span>
        </div>
        <div class="segmented-bar">
          <div class="seg-gpu" title="Attention Compute">GPU 48%</div>
          <div class="seg-tp" title="TP All-Reduce">TP 22%</div>
          <div class="seg-pp" title="Pipeline Transfer">PP 8%</div>
          <div class="seg-vllm" title="vLLM Runtime">vLLM 14%</div>
          <div class="seg-cpu" title="CPU Launch">CPU 8%</div>
        </div>
      </div>

      <div class="reserve-mini-grid">
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Memory Headroom</div>
          <div class="reserve-mini-val" style="color:#34d399;">18.4 GB</div>
          <div class="reserve-mini-sub">38.3% free per GPU</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Peak KV Block</div>
          <div class="reserve-mini-val" style="color:#38bdf8;">15.5%</div>
          <div class="reserve-mini-sub">Under 1M c4 load</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Preemptions</div>
          <div class="reserve-mini-val" style="color:#34d399;">0 Count</div>
          <div class="reserve-mini-sub">100% clean admission</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">1M Context Bound</div>
          <div class="reserve-mini-val" style="color:#c084fc;">Passed</div>
          <div class="reserve-mini-sub">74.85s TTFT (TP8)</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Chunk Schedule</div>
          <div class="reserve-mini-val" style="color:#fbbf24;">8K / 16K</div>
          <div class="reserve-mini-sub">Optimal chunk budget</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Transport</div>
          <div class="reserve-mini-val" style="color:#38bdf8;">VPC Sockets</div>
          <div class="reserve-mini-sub">PyNCCL TCP backend</div>
        </div>
      </div>
    </div>"""

new_reserve = """    <!-- Runtime Reserve & vLLM Breakdown (Algebraic Ledger, Spec §5, §11) -->
    <div class="reserve-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <span style="font-size:10px; font-weight:700; color:#fff;">Runtime Reserve Component Ledger (T_workload)</span>
        <span class="pill-badge badge-derived"><span class="dot"></span>DERIVED</span>
      </div>

      <div style="background:#080f1d; border:1px solid #1e293b; border-radius:4px; padding:6px 8px; margin:4px 0 8px 0; font-family:monospace; font-size:9px; color:#cbd5e1;">
        <div>T_workload = A_GPU + B_TP + C_PP + D_PCIe + E_vLLM + F_CPU + G_other − O_overlap</div>
        <div style="font-size:7.5px; color:#94a3b8; margin-top:2px;">
          * Status: Unresolved ledger. Synthetic percentages removed. PP=N/A on PP1 single-node profiles.
        </div>
      </div>

      <div class="reserve-mini-grid">
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Preemptions</div>
          <div class="reserve-mini-val" style="color:#34d399;">0.0 Delta</div>
          <div class="reserve-mini-sub">vllm_runs.csv (pending raw)</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Peak KV Block</div>
          <div class="reserve-mini-val" style="color:#38bdf8;">15.5%</div>
          <div class="reserve-mini-sub">tp4_closedloop_1m::c4</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Memory Headroom</div>
          <div class="reserve-mini-val" style="color:#34d399;">66.4 GB</div>
          <div class="reserve-mini-sub">30.8% of 96GB allocated</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">1M Feasibility</div>
          <div class="reserve-mini-val" style="color:#c084fc;">c1/c2/c4 Run</div>
          <div class="reserve-mini-sub">TP4 c1: 93.38s · TP8 c1: 74.85s</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Chunk Finding</div>
          <div class="reserve-mini-val" style="color:#fbbf24;">16K Lowest</div>
          <div class="reserve-mini-sub">89.16s TTFT @ 1M c1</div>
        </div>
        <div class="reserve-mini-card">
          <div style="font-size:8px; color:var(--text-muted);">Queue Overhead</div>
          <div class="reserve-mini-val" style="color:#94a3b8;">NOT CAPTURED</div>
          <div class="reserve-mini-sub">Hist mean: 7.2µs - 48ms</div>
        </div>
      </div>
    </div>"""

html = html.replace(old_reserve, new_reserve)

# ==============================================================================
# PHASE 3: SCALE-UP TAB REMEDIATION (Spec §6–7)
# ==============================================================================

# Scale-Up KPI Row
old_scaleup_kpis = """  <!-- Top KPI Row -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">⚡</div>
        <div class="kpi-big-info">
          <div class="kpi-label">TP4 Decode Advantage</div>
          <div class="kpi-main-val" style="color:#38bdf8;">30.6% Faster</div>
          <div class="kpi-sub-text">4.48ms vs 6.41ms TPOT @ 8K context</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fb923c;">🔀</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Prefill Crossover Point</div>
          <div class="kpi-main-val" style="color:#fb923c;">~350K Tokens</div>
          <div class="kpi-sub-text">TP8 overtakes TP4 at 512K (28.2s vs 31.9s)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🚀</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Peak 8K c8 Output TPS</div>
          <div class="kpi-main-val" style="color:#34d399;">555.0 tok/s</div>
          <div class="kpi-sub-text">TP4 delivers 24.5% higher throughput than TP8 (445.8)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">💾</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Per-GPU Memory Footprint</div>
          <div class="kpi-main-val" style="color:#c084fc;">29.6 GB</div>
          <div class="kpi-sub-text">30.8% of 96GB GDDR7 allocated (66.4GB free)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>"""

new_scaleup_kpis = """  <!-- Top KPI Row (Spec §6-7) -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">⚡</div>
        <div class="kpi-big-info">
          <div class="kpi-label">TP4 Decode Advantage (8K c1)</div>
          <div class="kpi-main-val" style="color:#38bdf8;">29.9% Lower TPOT</div>
          <div class="kpi-sub-text">4.45ms vs 6.35ms (tp4_qualification vs tp8_qualification)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fb923c;">🔀</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Prefill Crossover Bracket</div>
          <div class="kpi-main-val" style="color:#fb923c;">128K – 512K</div>
          <div class="kpi-sub-text">TP4 leads at 128K (4.54s vs 4.82s); TP8 leads at 512K (28.17s vs 31.98s)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🚀</div>
        <div class="kpi-big-info">
          <div class="kpi-label">8K Closed-Loop Throughput</div>
          <div class="kpi-main-val" style="color:#34d399;">774.4 tok/s @ c32</div>
          <div class="kpi-sub-text">c1: 187.6 · c4: 415.3 · c8: 559.7 · c16: 673.2 tok/s (tp4_closedloop_8k)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#f43f5e;">📉</div>
        <div class="kpi-big-info">
          <div class="kpi-label">128K Capacity Knee</div>
          <div class="kpi-main-val" style="color:#f43f5e;">c4 Knee (~28 tok/s)</div>
          <div class="kpi-sub-text">Throughput flattens c4→c16 (+3.7%) while TPOT rises 47x (5.1ms → 242.9ms)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>"""

html = html.replace(old_scaleup_kpis, new_scaleup_kpis)

# Scale-Up 4 Charts Grid & Annotations
old_scaleup_charts = """  <!-- 4 Interactive Charts Grid -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📈</span> TTFT vs Context Length (8K to 1M)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Scaling Analysis:</strong> TP4 leads up to 256K context due to minimal TP all-reduce overhead. At 512K (28.2s vs 31.9s) and 1M (74.8s vs 93.4s), TP8 compute parallelism wins by 19.9%.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> Decode TPOT vs Concurrency (c1 to c32)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpTpot"></canvas></div>
      <div class="takeaways-box">
        <strong>Decode Latency Sensitivity:</strong> Across all concurrency levels, TP4 consistently beats TP8 by 2.0 to 3.5ms per token because PCIe/NUMA cross-socket latency penalizes 8-way all-reduce.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🚀</span> Total Output Throughput (tok/s) vs Concurrency</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpThroughput"></canvas></div>
      <div class="takeaways-box">
        <strong>Throughput Saturation:</strong> Concurrency scales near-linearly from c1 (188 tok/s) to c8 (555 tok/s), peaking at ~1,120 tok/s at c32 before memory bandwidth saturates.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📊</span> Inter-GPU All-Reduce Overhead Breakdown</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpComm"></canvas></div>
      <div class="takeaways-box">
        <strong>NUMA Ring Bottleneck:</strong> In an 8-GPU PCIe topology without NVLink bridges, TP8 suffers a 2.4x latency penalty in tensor all-reduce compared to single-socket TP4.
      </div>
    </div>
  </div>"""

new_scaleup_charts = """  <!-- 4 Interactive Charts Grid (Spec §6-7) -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
    <!-- Chart 1: Baseline TTFT vs Context (Fig 2) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📈</span> Baseline TTFT vs Context (8K, 128K, 512K, 1M c1)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> TP4 TTFT: 8K=0.222s, 128K=4.541s, 512K=31.979s, 1M=93.385s. TP8: 8K=0.268s, 128K=4.824s, 512K=28.167s, 1M=74.850s.</li>
          <li><strong>Interpretation [High]:</strong> TP4 leads at 8K and 128K. Crossover occurs between 128K and 512K; TP8 compute parallelism reduces 1M TTFT by 18.5s.</li>
          <li><strong>Decision:</strong> Scope by workload SLA: TP4 for &le;128K; TP8 for &ge;512K long-context prefill.</li>
          <li><strong>Next evidence:</strong> Per-chunk iteration timeline across 128K–512K bracket.</li>
          <li><strong>Evidence:</strong> MEASURED-48B (current UI values pending raw re-validation) · tp4_context_baseline, tp8_context_baseline · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: TPOT vs Concurrency (Matched Only) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> 8K Decode TPOT vs Concurrency (Matched Points Only)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpTpot"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> TP4 8K TPOT: c1=4.47ms, c4=7.27ms, c8=10.73ms, c16=19.27ms, c32=34.96ms. TP8 matched points: c1=6.35ms, c8=13.92ms (c2/c4/c16/c32 NOT RUN).</li>
          <li><strong>Interpretation [High]:</strong> TP4 maintains lower TPOT at matched points (+29.9% faster @ c1, +22.9% faster @ c8); PCIe all-reduce overhead penalizes TP8.</li>
          <li><strong>Decision:</strong> Prefer TP4 for low-latency interactive serving. Do not interpolate unmeasured TP8 concurrencies.</li>
          <li><strong>Next evidence:</strong> Execute TP8 closed-loop c4 and c16 sweeps.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_8k, tp8_qualification · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: Output Throughput vs Concurrency (Fig 4) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🚀</span> 8K Closed-Loop Output Throughput (tp4_closedloop_8k)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpThroughput"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> TP4 throughput: c1=187.6, c4=415.3, c8=559.7, c16=673.2, c32=774.4 tok/s. (c2 = NOT RUN). TP8 matched: c1=135.7, c8=445.8 tok/s.</li>
          <li><strong>Interpretation [High]:</strong> Scaling flattens beyond c8; c16 $\to$ c32 yields only +15% throughput while TPOT rises 81% (19.3ms $\to$ 35.0ms).</li>
          <li><strong>Decision:</strong> Optimal operating concurrency for 8K serving is c8–c16. c32 is past the latency-efficiency knee.</li>
          <li><strong>Next evidence:</strong> Memory bandwidth saturation profile at c32.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_8k, tp8_qualification · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 4: 128K Capacity Knee (Fig 5) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📉</span> 128K Capacity Knee & Latency-Throughput Tradeoff (Fig 5)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasScaleUpComm"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> At 128K, closed-loop c1 $\to$ c16 raises output throughput from 24.7 to 28.2 tok/s (+14%) while TPOT rises from 5.11 to 242.85 ms (~47x).</li>
          <li><strong>Interpretation [Medium]:</strong> Throughput saturates at c4 (27.2 tok/s) while queue contention degrades decode latency. This is a classic capacity knee.</li>
          <li><strong>Decision:</strong> For 128K with a decode latency SLO, operating concurrency must be kept below c4. Never describe c16 as "supported users".</li>
          <li><strong>Next evidence:</strong> Scheduler running/waiting queue traces and preemption metrics under open-loop RPS.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_128k::{c1,c4,c8,c16} · N=12 requests.</li>
        </ul>
      </div>
    </div>
  </div>"""

html = html.replace(old_scaleup_charts, new_scaleup_charts)

# ==============================================================================
# PHASE 4: LONG CONTEXT TAB REMEDIATION (Spec §8)
# ==============================================================================

old_long_kpis = """  <!-- Top KPI Row -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🎯</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Context Feasibility</div>
          <div class="kpi-main-val" style="color:#34d399;">100% Passed</div>
          <div class="kpi-sub-text">74.85s TTFT on TP8 · 0 OOM · 0 Preemptions</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">📦</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Chunked Prefill Budget</div>
          <div class="kpi-main-val" style="color:#38bdf8;">8,192 Tokens</div>
          <div class="kpi-sub-text">Sweet spot balancing prefill throughput & decode SLA</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fbbf24;">⚡</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Prefix Cache Speedup</div>
          <div class="kpi-main-val" style="color:#fbbf24;">6.5x Faster</div>
          <div class="kpi-sub-text">TTFT drops from 93.4s to 14.4s at 90% prefix hit</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">🧠</div>
        <div class="kpi-big-info">
          <div class="kpi-label">KV Memory Scaling</div>
          <div class="kpi-main-val" style="color:#c084fc;">1.23 GB / 100K</div>
          <div class="kpi-sub-text">Total KV pool consumes only 12.3 GB for 1M tokens</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>"""

new_long_kpis = """  <!-- Top KPI Row (Spec §8) -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🎯</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Context Feasibility Scope</div>
          <div class="kpi-main-val" style="color:#34d399;">Baseline + Closed-Loop</div>
          <div class="kpi-sub-text">TP4 & TP8 c1 baseline + TP4 c1/c2/c4 completed; offload & multi-node unverified</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">📦</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Chunk-Size Sweep (c1)</div>
          <div class="kpi-main-val" style="color:#38bdf8;">16K Lowest TTFT</div>
          <div class="kpi-sub-text">16K: 89.16s vs 8K: 93.38s and 4K: 122.10s (caveat: concurrent decode SLA not evaluated)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fbbf24;">📈</div>
        <div class="kpi-big-info">
          <div class="kpi-label">1M Closed-Loop Concurrency</div>
          <div class="kpi-main-val" style="color:#fbbf24;">c1 $\to$ c4 Collapse</div>
          <div class="kpi-sub-text">TTFT: 93.5s $\to$ 231.5s; TPOT: 10.2ms $\to$ 267.7ms; throughput flat at 0.3 tok/s</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">🧠</div>
        <div class="kpi-big-info">
          <div class="kpi-label">KV Block Utilization Peak</div>
          <div class="kpi-main-val" style="color:#c084fc;">12.3% – 15.5%</div>
          <div class="kpi-sub-text">12.3% @ c1; 15.5% @ c2 and c4 (stated in %, not converted to GB)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>"""

html = html.replace(old_long_kpis, new_long_kpis)

# Long Context Charts Grid
old_long_charts = """  <!-- 4 Interactive Charts Grid -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📈</span> TTFT vs Context Length Progression (8K to 1M)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Context Scaling Dynamics:</strong> Attention compute scales super-linearly past 256K tokens. TP8's compute advantage grows from 512K onwards, reducing 1M prefill time by 18.5 seconds.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📦</span> Chunked Prefill Schedules vs Total Prefill Time</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxChunk"></canvas></div>
      <div class="takeaways-box">
        <strong>Chunk Size Tradeoff:</strong> 4K chunking suffers 30.7% overhead due to kernel relaunch frequency. 8K and 16K chunks maximize SM occupancy without starving existing decode streams.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⚡</span> Prefix Caching Hit Rate vs Effective TTFT</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxPrefix"></canvas></div>
      <div class="takeaways-box">
        <strong>Prefix Cache Multiplier:</strong> Reusing prefill blocks yields dramatic reductions in TTFT (e.g. 50% hit cuts 1M prefill to 48.2s; 90% hit cuts prefill to 14.4s).
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>💾</span> KV Cache Memory Footprint (GB) vs Context Length</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxKv"></canvas></div>
      <div class="takeaways-box">
        <strong>Linear Memory Growth:</strong> PagedAttention blocks scale strictly linearly with token count. 1M tokens require 12.3 GB of KV cache, leaving ample headroom on 48GB Ada GPUs.
      </div>
    </div>
  </div>"""

new_long_charts = """  <!-- 4 Interactive Charts Grid (Spec §8) -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
    <!-- Chart 1: TTFT Scaling to 1M (Measured Points Only) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📈</span> Baseline TTFT Progression to 1M (Measured Points Only)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxTtft"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 1M c1 TTFT: TP4 = 93.38s; TP8 = 74.85s (18.53s lower on TP8). No 32K, 64K, 256K runs exist.</li>
          <li><strong>Interpretation [High]:</strong> At 1M context, linear attention prefill is compute-heavy, enabling TP8 tensor parallelism to overcome bus latency penalties.</li>
          <li><strong>Decision:</strong> Deploy TP8 for 1M batch prefill where TTFT is the primary bottleneck.</li>
          <li><strong>Next evidence:</strong> Multi-node 1M distribution profile (NOT CONFIGURED in current suite).</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_context_baseline, tp8_context_baseline · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: 1M Chunk-Size Sweep (Fig 7) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📦</span> 1M TP4 c1 Chunk-Size Sweep (Fig 7)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxChunk"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 1M c1 TTFT: 4K chunk budget = 122.10s; 8K chunk budget = 93.38s; 16K chunk budget = 89.16s.</li>
          <li><strong>Interpretation [High]:</strong> 16K provides the lowest isolated 1M c1 TTFT (-27.0% vs 4K, -4.5% vs 8K) by reducing scheduling/dispatch boundaries.</li>
          <li><strong>Decision:</strong> Scope finding: 16K is fastest for single-stream prefill; concurrent decode SLO impacts are unmeasured.</li>
          <li><strong>Next evidence:</strong> Chunk prefill sweep under concurrent decode traffic.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_chunk4k, tp4_chunk8k, tp4_chunk16k · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: 1M Closed-Loop Concurrency (Fig 8) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📉</span> 1M TP4 Closed-Loop Concurrency (Fig 8 Headline)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxPrefix"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Under c1 $\to$ c4, TTFT rises 93.46s $\to$ 150.65s $\to$ 231.50s; TPOT rises 10.20ms $\to$ 239.25ms $\to$ 267.69ms; output throughput is flat at 0.3 tok/s; KV peak is 12.3% $\to$ 15.5%.</li>
          <li><strong>Interpretation [High]:</strong> Serving capacity at 1M collapses under closed-loop concurrency due to memory bus contention and prefill queuing.</li>
          <li><strong>Decision:</strong> 1M serving requires strict queue admission control ($c \le 1$ per GPU group). c4 is not production-viable.</li>
          <li><strong>Next evidence:</strong> Prefix-caching 1M execution to test warm KV mitigation.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_1m::{c1,c2,c4} · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 4: KV Cache Utilization % vs Context -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>💾</span> KV Cache Peak Utilization (%) vs Context Length</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasLongCtxKv"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> KV peak utilization: 8K c1 = 0.1%, 128K c1 = 1.6%, 512K c1 = 6.5%, 1M c1 = 12.3%, 1M c4 = 15.5%. Stated strictly in %, not GB.</li>
          <li><strong>Interpretation [High]:</strong> Linear attention KV cache scales linearly with sequence length; block allocation overhead remains well within pool limits.</li>
          <li><strong>Decision:</strong> KV cache memory capacity is not the limiting factor on 96GB GPUs for single streams up to 1M tokens.</li>
          <li><strong>Next evidence:</strong> Extended concurrency sweeps with native KV offload (NOT RUN in current suite).</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_context_baseline, tp4_closedloop_1m · N=12 requests.</li>
        </ul>
      </div>
    </div>
  </div>"""

html = html.replace(old_long_charts, new_long_charts)

# ==============================================================================
# PHASE 6: SCHEDULER & KV TAB REMEDIATION (Spec §10)
# ==============================================================================

old_sched_kpis = """  <!-- Top KPI Row -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🛡️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Zero Preemptions</div>
          <div class="kpi-main-val" style="color:#34d399;">0 Events</div>
          <div class="kpi-sub-text">100% stable execution across all 59 benchmark runs</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">📊</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Max Concurrency @ 128K</div>
          <div class="kpi-main-val" style="color:#38bdf8;">c = 16 Stable</div>
          <div class="kpi-sub-text">Peak KV block utilization safely bounded at 78.4%</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fbbf24;">⏱️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Scheduler Iteration Overhead</div>
          <div class="kpi-main-val" style="color:#fbbf24;">&lt; 0.04 ms</div>
          <div class="kpi-sub-text">Mean queue dispatch latency is negligible</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">🧩</div>
        <div class="kpi-big-info">
          <div class="kpi-label">KV Cache Fragmentation</div>
          <div class="kpi-main-val" style="color:#c084fc;">&lt; 1.8%</div>
          <div class="kpi-sub-text">PagedAttention block size (16 tokens) near-zero waste</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>"""

new_sched_kpis = """  <!-- Top KPI Row (Spec §10) -->
  <div class="kpi-row-4">
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#34d399;">🛡️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Preemptions Delta</div>
          <div class="kpi-main-val" style="color:#34d399;">0.0 Delta</div>
          <div class="kpi-sub-text">source: vllm_runs.csv, pending raw re-validation</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#38bdf8;">📊</div>
        <div class="kpi-big-info">
          <div class="kpi-label">128K KV Utilization Peak</div>
          <div class="kpi-main-val" style="color:#38bdf8;">14.6% @ c16</div>
          <div class="kpi-sub-text">Exact evidence peak (c1: 1.6%, c4: 6.5%, c8: 13.1%, c16: 14.6%; c32 NOT RUN)</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#fbbf24;">⏱️</div>
        <div class="kpi-big-info">
          <div class="kpi-label">Scheduler Overhead</div>
          <div class="kpi-main-val" style="color:#fbbf24;">NOT CAPTURED</div>
          <div class="kpi-sub-text">EngineCore iteration CPU time not isolated in benchmark CSV</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-unres"><span class="dot"></span>UNRESOLVED</span></div>
    </div>
    <div class="kpi-big-card">
      <div class="kpi-big-left">
        <div class="kpi-icon-wrap" style="color:#c084fc;">🧩</div>
        <div class="kpi-big-info">
          <div class="kpi-label">max_num_seqs Invariance (512K c4)</div>
          <div class="kpi-main-val" style="color:#c084fc;">Invariant @ 4/8/16</div>
          <div class="kpi-sub-text">TTFT: ~88.0s, TPOT: ~433.8ms, KV: 12.9% — not the dominant limiter</div>
        </div>
      </div>
      <div class="kpi-card-badge"><span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span></div>
    </div>
  </div>"""

html = html.replace(old_sched_kpis, new_sched_kpis)

# Scheduler Charts Grid: Replace synthetic percentiles with Fig 11, max_num_seqs, and Long-context TPOT
old_sched_charts = """  <!-- 4 Interactive Charts Grid -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📊</span> KV Cache Block Utilization % vs Concurrency</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedKvUtil"></canvas></div>
      <div class="takeaways-box">
        <strong>Capacity Planning:</strong> At 8K context, even c32 consumes only 26% KV blocks. At 128K context, capacity gating engages at c16 (78.4%), preventing OOM aborts.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏳</span> Request Queue Wait Time (s) vs Concurrency</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedQueue"></canvas></div>
      <div class="takeaways-box">
        <strong>Queue Stability:</strong> Queue delay remains sub-millisecond up to c8. At c16 and c32, queue delay increases smoothly without thrashing or preempting active sequences.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🎯</span> TTFT Latency Percentiles (P50, P95, P99)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedTtftPcts"></canvas></div>
      <div class="takeaways-box">
        <strong>Tail Latency Tightness:</strong> P99 TTFT stays within 1.05x of P50 at low concurrency and under 1.25x at c8, showing excellent deterministic scheduling behavior.
      </div>
    </div>

    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> TPOT Decode Percentiles (P50, P95, P99)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedTpotPcts"></canvas></div>
      <div class="takeaways-box">
        <strong>Decode Inter-Token Variance:</strong> P99 TPOT is within 0.8ms of P50, ensuring smooth streaming token delivery for interactive end-user experiences.
      </div>
    </div>
  </div>"""

new_sched_charts = """  <!-- 4 Interactive Charts Grid (Spec §10) -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
    <!-- Chart 1: KV Utilization (Fig 11) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>📊</span> KV Cache Block Peak % vs Concurrency (Fig 11)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedKvUtil"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 128K KV peak: c1=1.6%, c4=6.5%, c8=13.1%, c16=14.6% (c32 NOT RUN). 8K KV peak: c1=0.1%, c4=0.5%, c8=1.0%, c16=2.0%, c32=4.0%.</li>
          <li><strong>Interpretation [High]:</strong> KV cache memory scales sub-linearly at c16 as request scheduling limits simultaneous token allocation.</li>
          <li><strong>Decision:</strong> Corrected from UI synthetic 29.44% scaling. KV memory headroom remains abundant on 96GB Blackwell hardware.</li>
          <li><strong>Next evidence:</strong> Profile active vs waiting block counts across scheduler ticks.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_128k, tp4_closedloop_8k · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 2: Queue Wait Time -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏳</span> Histogram-Derived Mean Queue Delay (ms)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedQueue"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> 8K queue mean: c1=0.007ms, c4=0.012ms, c8=0.021ms, c16=0.045ms, c32=0.140ms. 128K: c1=0.012ms, c4=0.045ms, c16=2.80ms.</li>
          <li><strong>Interpretation [Medium]:</strong> Queue delay remains sub-millisecond until high-concurrency long-context requests saturate batch boundaries.</li>
          <li><strong>Decision:</strong> Current UI values derived from Prometheus histogram pending raw re-validation.</li>
          <li><strong>Next evidence:</strong> Raw Prometheus scrape logs and per-request queue timestamps.</li>
          <li><strong>Evidence:</strong> current UI value pending raw re-validation (source: vllm_runs.csv) · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 3: max_num_seqs Dedicated Sweep (Spec §10) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>🧩</span> max_num_seqs Sweep @ 512K c4 (Spec §10)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedTtftPcts"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> At 512K c4, max_num_seqs 4, 8, and 16 produce nearly identical TTFT (~88.01s, ~87.99s, ~87.97s), TPOT (~433.8ms), and KV peak (12.9%).</li>
          <li><strong>Interpretation [High]:</strong> Scheduler max_num_seqs was not the dominant limiter for this workload; memory bus prefill duration dominates.</li>
          <li><strong>Decision:</strong> Tuning max_num_seqs between 4 and 16 provides no throughput benefit for high-context low-concurrency regimes.</li>
          <li><strong>Next evidence:</strong> Sweep max_num_seqs under short-context high-concurrency (8K c32).</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_512k_maxseq4, tp4_512k_maxseq8, tp4_512k_maxseq16 · N=12 requests.</li>
        </ul>
      </div>
    </div>

    <!-- Chart 4: Long-Context TPOT Degradation (Fig 6) -->
    <div class="pane-card">
      <div class="pane-header">
        <div class="pane-header-title"><span>⏱️</span> Long-Context TPOT Degradation under Concurrency (Fig 6)</div>
        <span class="pill-badge badge-m"><span class="dot"></span>MEASURED-48B</span>
      </div>
      <div style="height:220px; position:relative;"><canvas id="canvasSchedTpotPcts"></canvas></div>
      <div class="takeaways-box">
        <strong>Audit Annotation</strong>
        <ul>
          <li><strong>Observation:</strong> Under c1 $\to$ c4: 512K TPOT rises 7.56ms $\to$ 367.40ms $\to$ 433.95ms; 1M TPOT rises 10.20ms $\to$ 239.25ms $\to$ 267.69ms. Output throughput is flat (2.0 and 0.3 tok/s).</li>
          <li><strong>Interpretation [High]:</strong> Concurrency severely degrades token generation latency in long context due to chunked prefill interruptions.</li>
          <li><strong>Decision:</strong> Restrict long-context concurrency in production to preserve interactive token generation SLAs.</li>
          <li><strong>Next evidence:</strong> Chunked prefill prioritization vs decode preemption scheduling.</li>
          <li><strong>Evidence:</strong> MEASURED-48B · tp4_closedloop_512k, tp4_closedloop_1m · N=12 requests.</li>
        </ul>
      </div>
    </div>
  </div>"""

html = html.replace(old_sched_charts, new_sched_charts)

# ==============================================================================
# SCRIPT CONTROLLERS: REBIND ALL CHARTS TO window.EVIDENCE_DATA
# ==============================================================================

old_script_charts = """// --- TAB 1: EXECUTIVE CHARTS ---
new Chart(document.getElementById('canvasExecTtft'), {
  type: 'line',
  data: {
    labels: ['8K', '128K', '512K'],
    datasets: [
      { label: 'TP4', data: [0.271, 4.53, 31.95], borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4 },
      { label: 'TP8', data: [0.271, 4.85, 28.39], borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4 }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 0, max: 40, title: { display: true, text: 'TTFT (s)', color: '#94a3b8', font: { size: 8 } }, grid: { color: '#131e33' } },
      x: { grid: { color: '#131e33' }, title: { display: true, text: 'Context Length', color: '#94a3b8', font: { size: 8 } } }
    },
    plugins: { legend: { position: 'top', labels: { boxWidth: 8, padding: 6, font: { size: 8 } } } }
  }
});

new Chart(document.getElementById('canvasExecTpot'), {
  type: 'line',
  data: {
    labels: ['8K', '128K', '512K'],
    datasets: [
      { label: 'TP4', data: [4.48, 5.10, 7.60], borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4 },
      { label: 'TP8', data: [6.41, 7.02, 9.53], borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4 }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 0, max: 12, title: { display: true, text: 'TPOT (ms)', color: '#94a3b8', font: { size: 8 } }, grid: { color: '#131e33' } },
      x: { grid: { color: '#131e33' }, title: { display: true, text: 'Context Length', color: '#94a3b8', font: { size: 8 } } }
    },
    plugins: { legend: { position: 'top', labels: { boxWidth: 8, padding: 6, font: { size: 8 } } } }
  }
});

new Chart(document.getElementById('canvasExecTps'), {
  type: 'bar',
  data: {
    labels: ['TP4', 'TP8'],
    datasets: [{
      data: [559, 443],
      backgroundColor: ['#38bdf8', '#fb923c'],
      borderRadius: 4
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 0, max: 800, title: { display: true, text: 'Throughput (tok/s)', color: '#94a3b8', font: { size: 8 } }, grid: { color: '#131e33' } },
      x: { grid: { display: false } }
    },
    plugins: { legend: { display: false } }
  }
});"""

new_script_charts = """// --- TAB 1: EXECUTIVE CHARTS (Bound Strictly to window.EVIDENCE_DATA) ---
const q_tp4_8k = getEvidenceRow('tp4_qualification', '8k_c1');
const q_tp4_128k = getEvidenceRow('tp4_qualification', '128k_c1');
const q_tp4_512k = getEvidenceRow('tp4_qualification', '512k_c1');

const q_tp8_8k = getEvidenceRow('tp8_qualification', '8k_c1');
const q_tp8_128k = getEvidenceRow('tp8_qualification', '128k_c1');
const q_tp8_512k = getEvidenceRow('tp8_qualification', '512k_c1');

const q_tp4_c8 = getEvidenceRow('tp4_qualification', '8k_c8');
const q_tp8_c8 = getEvidenceRow('tp8_qualification', '8k_c8');

new Chart(document.getElementById('canvasExecTtft'), {
  type: 'line',
  data: {
    labels: ['8K', '128K', '512K'],
    datasets: [
      {
        label: 'TP4',
        data: [q_tp4_8k.ttft_ms / 1000, q_tp4_128k.ttft_ms / 1000, q_tp4_512k.ttft_ms / 1000],
        borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
      },
      {
        label: 'TP8',
        data: [q_tp8_8k.ttft_ms / 1000, q_tp8_128k.ttft_ms / 1000, q_tp8_512k.ttft_ms / 1000],
        borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 0, max: 40, title: { display: true, text: 'TTFT (s)', color: '#94a3b8', font: { size: 8 } }, grid: { color: '#131e33' } },
      x: { grid: { color: '#131e33' }, title: { display: true, text: 'Context Length', color: '#94a3b8', font: { size: 8 } } }
    },
    plugins: {
      legend: { position: 'top', labels: { boxWidth: 8, padding: 6, font: { size: 8 } } },
      tooltip: {
        callbacks: {
          afterLabel: function(ctx) {
            return `Evidence: qualification (raw-validated), N=12 requests`;
          }
        }
      }
    }
  }
});

new Chart(document.getElementById('canvasExecTpot'), {
  type: 'line',
  data: {
    labels: ['8K', '128K', '512K'],
    datasets: [
      {
        label: 'TP4',
        data: [q_tp4_8k.tpot_ms, q_tp4_128k.tpot_ms, q_tp4_512k.tpot_ms],
        borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
      },
      {
        label: 'TP8',
        data: [q_tp8_8k.tpot_ms, q_tp8_128k.tpot_ms, q_tp8_512k.tpot_ms],
        borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 0, max: 12, title: { display: true, text: 'TPOT (ms)', color: '#94a3b8', font: { size: 8 } }, grid: { color: '#131e33' } },
      x: { grid: { color: '#131e33' }, title: { display: true, text: 'Context Length', color: '#94a3b8', font: { size: 8 } } }
    },
    plugins: {
      legend: { position: 'top', labels: { boxWidth: 8, padding: 6, font: { size: 8 } } },
      tooltip: {
        callbacks: {
          afterLabel: function(ctx) {
            return `Evidence: qualification (raw-validated), N=12 requests`;
          }
        }
      }
    }
  }
});

new Chart(document.getElementById('canvasExecTps'), {
  type: 'bar',
  data: {
    labels: ['TP4', 'TP8'],
    datasets: [{
      data: [q_tp4_c8.output_tok_s, q_tp8_c8.output_tok_s],
      backgroundColor: ['#38bdf8', '#fb923c'],
      borderRadius: 4
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 0, max: 800, title: { display: true, text: 'Output Throughput (tok/s)', color: '#94a3b8', font: { size: 8 } }, grid: { color: '#131e33' } },
      x: { grid: { display: false } }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          afterLabel: function(ctx) {
            return `Evidence: 8k_c8 qualification, N=12 requests (86 samples)`;
          }
        }
      }
    }
  }
});"""

html = html.replace(old_script_charts, new_script_charts)

# Tab controllers: rebind scaleup, longcontext, schedulerkv
old_tab_controllers = """  if (tabId === 'scaleup') {
    new Chart(document.getElementById('canvasScaleUpTtft'), {
      type: 'line',
      data: {
        labels: ['8K', '32K', '64K', '128K', '256K', '512K', '1M'],
        datasets: [
          { label: 'TP4 Single-Node', data: [0.22, 0.98, 2.14, 4.53, 11.2, 31.95, 93.38], borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4, tension: 0.2 },
          { label: 'TP8 Single-Node', data: [0.27, 1.15, 2.45, 4.82, 10.8, 28.22, 74.85], borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4, tension: 0.2 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: {{ title: { display: true, text: 'TTFT (seconds)' }, grid: { color: '#131e33' } }, x: { grid: { color: '#131e33' } } },
        plugins: { legend: { position: 'top', labels: { boxWidth: 8 } } }
      }
    });

    new Chart(document.getElementById('canvasScaleUpTpot'), {
      type: 'line',
      data: {
        labels: ['c1', 'c2', 'c4', 'c8', 'c16', 'c32'],
        datasets: [
          { label: 'TP4 TPOT (8K)', data: [4.45, 5.82, 7.94, 10.70, 16.4, 25.8], borderColor: '#38bdf8', borderWidth: 2, pointRadius: 4 },
          { label: 'TP8 TPOT (8K)', data: [6.35, 7.90, 10.45, 13.92, 19.8, 29.5], borderColor: '#fb923c', borderWidth: 2, pointRadius: 4 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'TPOT (ms/token)' }, grid: { color: '#131e33' } }, x: { grid: { color: '#131e33' } } }
      }
    });

    new Chart(document.getElementById('canvasScaleUpThroughput'), {
      type: 'bar',
      data: {
        labels: ['c1', 'c2', 'c4', 'c8', 'c16', 'c32'],
        datasets: [
          { label: 'TP4 Output tok/s', data: [188.4, 312.0, 485.0, 555.0, 840.0, 1120.0], backgroundColor: '#38bdf8' },
          { label: 'TP8 Output tok/s', data: [135.7, 248.0, 395.0, 445.8, 710.0, 960.0], backgroundColor: '#fb923c' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'Throughput (tok/s)' }, grid: { color: '#131e33' } } }
      }
    });

    new Chart(document.getElementById('canvasScaleUpComm'), {
      type: 'bar',
      data: {
        labels: ['4 MB', '16 MB', '64 MB', '128 MB'],
        datasets: [
          { label: 'TP4 All-Reduce Latency', data: [0.12, 0.42, 1.58, 3.12], backgroundColor: '#38bdf8' },
          { label: 'TP8 All-Reduce Latency', data: [0.28, 0.98, 3.75, 7.42], backgroundColor: '#fb923c' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'Latency (ms)' }, grid: { color: '#131e33' } } }
      }
    });
  }"""

new_scaleup_tab_controller = """  if (tabId === 'scaleup') {
    // Fig 2: Baseline TTFT vs Context (8K, 128K, 512K, 1M)
    const b_tp4_8k = getEvidenceRow('tp4_context_baseline', '8k_c1');
    const b_tp4_128k = getEvidenceRow('tp4_context_baseline', '128k_c1');
    const b_tp4_512k = getEvidenceRow('tp4_context_baseline', '512k_c1');
    const b_tp4_1m = getEvidenceRow('tp4_context_baseline', '1m_c1');

    const b_tp8_8k = getEvidenceRow('tp8_context_baseline', '8k_c1');
    const b_tp8_128k = getEvidenceRow('tp8_context_baseline', '128k_c1');
    const b_tp8_512k = getEvidenceRow('tp8_context_baseline', '512k_c1');
    const b_tp8_1m = getEvidenceRow('tp8_context_baseline', '1m_c1');

    new Chart(document.getElementById('canvasScaleUpTtft'), {
      type: 'line',
      data: {
        labels: ['8K', '128K', '512K', '1M'],
        datasets: [
          {
            label: 'TP4 Baseline (tp4_context_baseline)',
            data: [b_tp4_8k.ttft_ms / 1000, b_tp4_128k.ttft_ms / 1000, b_tp4_512k.ttft_ms / 1000, b_tp4_1m.ttft_ms / 1000],
            borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
          },
          {
            label: 'TP8 Baseline (tp8_context_baseline)',
            data: [b_tp8_8k.ttft_ms / 1000, b_tp8_128k.ttft_ms / 1000, b_tp8_512k.ttft_ms / 1000, b_tp8_1m.ttft_ms / 1000],
            borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'TTFT (seconds)' }, grid: { color: '#131e33' } },
          x: { grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } },
          tooltip: {
            callbacks: {
              afterLabel: function(ctx) {
                return `Evidence: context_baseline, c1, N=12 requests`;
              }
            }
          }
        }
      }
    });

    // Fig 3/TPOT vs Concurrency: tp4_closedloop_8k (c1, c4, c8, c16, c32) + matched TP8 (c1, c8)
    const cl8_c1 = getEvidenceRow('tp4_closedloop_8k', 'c1');
    const cl8_c4 = getEvidenceRow('tp4_closedloop_8k', 'c4');
    const cl8_c8 = getEvidenceRow('tp4_closedloop_8k', 'c8');
    const cl8_c16 = getEvidenceRow('tp4_closedloop_8k', 'c16');
    const cl8_c32 = getEvidenceRow('tp4_closedloop_8k', 'c32');

    new Chart(document.getElementById('canvasScaleUpTpot'), {
      type: 'line',
      data: {
        labels: ['c1', 'c2', 'c4', 'c8', 'c16', 'c32'],
        datasets: [
          {
            label: 'TP4 8K (tp4_closedloop_8k)',
            data: [cl8_c1.tpot_ms, null, cl8_c4.tpot_ms, cl8_c8.tpot_ms, cl8_c16.tpot_ms, cl8_c32.tpot_ms],
            borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4, spanGaps: true
          },
          {
            label: 'TP8 Matched (qualification)',
            data: [q_tp8_8k.tpot_ms, null, null, q_tp8_c8.tpot_ms, null, null],
            borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 5, showLine: false
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'TPOT (ms/token)' }, grid: { color: '#131e33' } },
          x: { grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                if (ctx.raw === null) return `${ctx.dataset.label}: NOT RUN`;
                return `${ctx.dataset.label}: ${ctx.raw} ms`;
              }
            }
          }
        }
      }
    });

    // Fig 4: Throughput vs Concurrency (tp4_closedloop_8k bound strictly)
    new Chart(document.getElementById('canvasScaleUpThroughput'), {
      type: 'bar',
      data: {
        labels: ['c1', 'c2', 'c4', 'c8', 'c16', 'c32'],
        datasets: [
          {
            label: 'TP4 Output tok/s (tp4_closedloop_8k)',
            data: [cl8_c1.output_tok_s, null, cl8_c4.output_tok_s, cl8_c8.output_tok_s, cl8_c16.output_tok_s, cl8_c32.output_tok_s],
            backgroundColor: '#38bdf8'
          },
          {
            label: 'TP8 Output tok/s (matched qualification)',
            data: [q_tp8_8k.output_tok_s, null, null, q_tp8_c8.output_tok_s, null, null],
            backgroundColor: '#fb923c'
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'Throughput (tok/s)' }, grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                if (ctx.raw === null) return `${ctx.dataset.label}: NOT RUN`;
                return `${ctx.dataset.label}: ${ctx.raw} tok/s (closed-loop, output=256, N=12 requests)`;
              }
            }
          }
        }
      }
    });

    // Fig 5: 128K Capacity Knee (tp4_closedloop_128k c1, c4, c8, c16)
    const cl128_c1 = getEvidenceRow('tp4_closedloop_128k', 'c1');
    const cl128_c4 = getEvidenceRow('tp4_closedloop_128k', 'c4');
    const cl128_c8 = getEvidenceRow('tp4_closedloop_128k', 'c8');
    const cl128_c16 = getEvidenceRow('tp4_closedloop_128k', 'c16');

    new Chart(document.getElementById('canvasScaleUpComm'), {
      type: 'line',
      data: {
        labels: ['c1', 'c4', 'c8', 'c16'],
        datasets: [
          {
            label: 'Output tok/s (Throughput)',
            data: [cl128_c1.output_tok_s, cl128_c4.output_tok_s, cl128_c8.output_tok_s, cl128_c16.output_tok_s],
            borderColor: '#38bdf8', backgroundColor: '#38bdf8', yAxisID: 'y', borderWidth: 2, pointRadius: 4
          },
          {
            label: 'TPOT ms (Decode Latency)',
            data: [cl128_c1.tpot_ms, cl128_c4.tpot_ms, cl128_c8.tpot_ms, cl128_c16.tpot_ms],
            borderColor: '#f43f5e', backgroundColor: '#f43f5e', yAxisID: 'y1', borderWidth: 2, pointRadius: 4, borderDash: [4, 4]
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { type: 'linear', position: 'left', title: { display: true, text: 'Output tok/s' }, grid: { color: '#131e33' } },
          y1: { type: 'linear', position: 'right', title: { display: true, text: 'TPOT (ms)' }, grid: { display: false } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } }
        }
      }
    });
  }"""

html = html.replace(old_tab_controllers, new_scaleup_tab_controller)

# Long Context controller:
old_long_controller = """  else if (tabId === 'longcontext') {
    new Chart(document.getElementById('canvasLongCtxTtft'), {
      type: 'line',
      data: {
        labels: ['8K', '32K', '64K', '128K', '256K', '512K', '1M'],
        datasets: [
          { label: 'TP4 Scaling', data: [0.22, 0.98, 2.14, 4.53, 11.20, 31.95, 93.38], borderColor: '#38bdf8', borderWidth: 2, pointRadius: 4 },
          { label: 'TP8 Scaling', data: [0.27, 1.15, 2.45, 4.82, 10.80, 28.22, 74.85], borderColor: '#fb923c', borderWidth: 2, pointRadius: 4 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'TTFT (seconds)' } } }
      }
    });

    new Chart(document.getElementById('canvasLongCtxChunk'), {
      type: 'bar',
      data: {
        labels: ['4K Chunk Budget', '8K Chunk Budget', '16K Chunk Budget'],
        datasets: [{
          label: '1M Prefill Time (s)',
          data: [122.10, 93.38, 89.16],
          backgroundColor: ['#f43f5e', '#38bdf8', '#34d399']
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'Prefill Duration (seconds)' } } }
      }
    });

    new Chart(document.getElementById('canvasLongCtxPrefix'), {
      type: 'line',
      data: {
        labels: ['0% Hit', '25% Hit', '50% Hit', '75% Hit', '90% Hit'],
        datasets: [{
          label: '1M Context Effective TTFT (s)',
          data: [93.38, 71.20, 48.20, 26.50, 14.38],
          borderColor: '#34d399', backgroundColor: '#34d399', borderWidth: 2, pointRadius: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'Effective TTFT (s)' } } }
      }
    });

    new Chart(document.getElementById('canvasLongCtxKv'), {
      type: 'line',
      data: {
        labels: ['8K', '64K', '128K', '256K', '512K', '1M'],
        datasets: [{
          label: 'KV Cache Pool VRAM (GB)',
          data: [0.12, 0.98, 1.84, 3.68, 7.36, 12.30],
          borderColor: '#c084fc', backgroundColor: '#c084fc', borderWidth: 2, pointRadius: 4
        }]
      }},
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'VRAM Usage (GB)' } } }
      }
    });
  }"""

new_long_controller = """  else if (tabId === 'longcontext') {
    // Chart 1: Measured baseline TTFT progression (8K, 128K, 512K, 1M)
    const b_tp4_8k = getEvidenceRow('tp4_context_baseline', '8k_c1');
    const b_tp4_128k = getEvidenceRow('tp4_context_baseline', '128k_c1');
    const b_tp4_512k = getEvidenceRow('tp4_context_baseline', '512k_c1');
    const b_tp4_1m = getEvidenceRow('tp4_context_baseline', '1m_c1');

    const b_tp8_8k = getEvidenceRow('tp8_context_baseline', '8k_c1');
    const b_tp8_128k = getEvidenceRow('tp8_context_baseline', '128k_c1');
    const b_tp8_512k = getEvidenceRow('tp8_context_baseline', '512k_c1');
    const b_tp8_1m = getEvidenceRow('tp8_context_baseline', '1m_c1');

    new Chart(document.getElementById('canvasLongCtxTtft'), {
      type: 'line',
      data: {
        labels: ['8K', '128K', '512K', '1M'],
        datasets: [
          {
            label: 'TP4 Baseline TTFT (s)',
            data: [b_tp4_8k.ttft_ms / 1000, b_tp4_128k.ttft_ms / 1000, b_tp4_512k.ttft_ms / 1000, b_tp4_1m.ttft_ms / 1000],
            borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
          },
          {
            label: 'TP8 Baseline TTFT (s)',
            data: [b_tp8_8k.ttft_ms / 1000, b_tp8_128k.ttft_ms / 1000, b_tp8_512k.ttft_ms / 1000, b_tp8_1m.ttft_ms / 1000],
            borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'TTFT (seconds)' }, grid: { color: '#131e33' } },
          x: { grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } }
        }
      }
    });

    // Fig 7: 1M TP4 c1 Chunk Sweep (tp4_chunk4k, 8k, 16k :: 1m_c1)
    const ch4k = getEvidenceRow('tp4_chunk4k', '1m_c1');
    const ch8k = getEvidenceRow('tp4_chunk8k', '1m_c1');
    const ch16k = getEvidenceRow('tp4_chunk16k', '1m_c1');

    new Chart(document.getElementById('canvasLongCtxChunk'), {
      type: 'bar',
      data: {
        labels: ['4K Chunk Budget', '8K Chunk Budget', '16K Chunk Budget'],
        datasets: [{
          label: '1M c1 Prefill TTFT (s)',
          data: [ch4k.ttft_ms / 1000, ch8k.ttft_ms / 1000, ch16k.ttft_ms / 1000],
          backgroundColor: ['#f43f5e', '#38bdf8', '#34d399'],
          borderRadius: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'TTFT (seconds)' }, grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: function(ctx) {
                return `Evidence: tp4_chunk{4k,8k,16k}::1m_c1, N=12 requests`;
              }
            }
          }
        }
      }
    });

    // Fig 8: 1M Closed-Loop Concurrency (tp4_closedloop_1m c1, c2, c4)
    const cl1m_c1 = getEvidenceRow('tp4_closedloop_1m', 'c1');
    const cl1m_c2 = getEvidenceRow('tp4_closedloop_1m', 'c2');
    const cl1m_c4 = getEvidenceRow('tp4_closedloop_1m', 'c4');

    new Chart(document.getElementById('canvasLongCtxPrefix'), {
      type: 'line',
      data: {
        labels: ['c1', 'c2', 'c4'],
        datasets: [
          {
            label: 'TTFT (seconds)',
            data: [cl1m_c1.ttft_ms / 1000, cl1m_c2.ttft_ms / 1000, cl1m_c4.ttft_ms / 1000],
            borderColor: '#38bdf8', backgroundColor: '#38bdf8', yAxisID: 'y', borderWidth: 2, pointRadius: 4
          },
          {
            label: 'TPOT (ms)',
            data: [cl1m_c1.tpot_ms, cl1m_c2.tpot_ms, cl1m_c4.tpot_ms],
            borderColor: '#f43f5e', backgroundColor: '#f43f5e', yAxisID: 'y1', borderWidth: 2, pointRadius: 4, borderDash: [4, 4]
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { type: 'linear', position: 'left', title: { display: true, text: 'TTFT (s)' }, grid: { color: '#131e33' } },
          y1: { type: 'linear', position: 'right', title: { display: true, text: 'TPOT (ms)' }, grid: { display: false } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } }
        }
      }
    });

    // Chart 4: KV Cache Utilization % vs Context Length (Strictly in %)
    new Chart(document.getElementById('canvasLongCtxKv'), {
      type: 'line',
      data: {
        labels: ['8K', '128K', '512K', '1M'],
        datasets: [{
          label: 'KV Block Utilization Peak (%)',
          data: [b_tp4_8k.kv_peak_pct, b_tp4_128k.kv_peak_pct, b_tp4_512k.kv_peak_pct, b_tp4_1m.kv_peak_pct],
          borderColor: '#c084fc', backgroundColor: '#c084fc', borderWidth: 2, pointRadius: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'KV Cache Utilization (%)' }, grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } }
        }
      }
    });
  }"""

html = html.replace(old_long_controller, new_long_controller)

# Scheduler controller:
old_sched_controller = """  else if (tabId === 'schedulerkv') {
    new Chart(document.getElementById('canvasSchedKvUtil'), {
      type: 'bar',
      data: {
        labels: ['c1', 'c4', 'c8', 'c16', 'c32'],
        datasets: [
          { label: '8K Context KV %', data: [0.12, 0.49, 0.98, 1.96, 4.12], backgroundColor: '#38bdf8' },
          { label: '128K Context KV %', data: [1.84, 7.36, 14.72, 29.44, 58.88], backgroundColor: '#fb923c' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'KV Block Utilization (%)' } } }
      }
    });

    new Chart(document.getElementById('canvasSchedQueue'), {
      type: 'line',
      data: {
        labels: ['c1', 'c2', 'c4', 'c8', 'c16', 'c32'],
        datasets: [{
          label: 'Queue Wait Time (ms)',
          data: [0.007, 0.012, 0.021, 0.045, 0.85, 2.80],
          borderColor: '#fbbf24', backgroundColor: '#fbbf24', borderWidth: 2, pointRadius: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'Queue Delay (ms)' } } }
      }
    });

    new Chart(document.getElementById('canvasSchedTtftPcts'), {
      type: 'bar',
      data: {
        labels: ['8K c1', '8K c8', '128K c1'],
        datasets: [
          { label: 'P50 TTFT (ms)', data: [224.7, 956.5, 4534.1], backgroundColor: '#38bdf8' },
          { label: 'P95 TTFT (ms)', data: [225.9, 962.0, 4548.0], backgroundColor: '#fb923c' },
          { label: 'P99 TTFT (ms)', data: [226.2, 968.4, 4556.2], backgroundColor: '#f43f5e' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'Latency (ms)' } } }
      }
    });

    new Chart(document.getElementById('canvasSchedTpotPcts'), {
      type: 'bar',
      data: {
        labels: ['8K c1', '8K c8', '128K c1'],
        datasets: [
          { label: 'P50 TPOT (ms)', data: [4.45, 10.70, 5.08], backgroundColor: '#38bdf8' },
          { label: 'P95 TPOT (ms)', data: [4.45, 10.78, 5.12], backgroundColor: '#fb923c' },
          { label: 'P99 TPOT (ms)', data: [4.45, 10.82, 5.15], backgroundColor: '#f43f5e' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: 'TPOT (ms)' } } }
      }
    });
  }"""

new_sched_controller = """  else if (tabId === 'schedulerkv') {
    // Fig 11: KV Utilization Peak % (Exact Evidence Rows)
    const cl8_c1 = getEvidenceRow('tp4_closedloop_8k', 'c1');
    const cl8_c4 = getEvidenceRow('tp4_closedloop_8k', 'c4');
    const cl8_c8 = getEvidenceRow('tp4_closedloop_8k', 'c8');
    const cl8_c16 = getEvidenceRow('tp4_closedloop_8k', 'c16');
    const cl8_c32 = getEvidenceRow('tp4_closedloop_8k', 'c32');

    const cl128_c1 = getEvidenceRow('tp4_closedloop_128k', 'c1');
    const cl128_c4 = getEvidenceRow('tp4_closedloop_128k', 'c4');
    const cl128_c8 = getEvidenceRow('tp4_closedloop_128k', 'c8');
    const cl128_c16 = getEvidenceRow('tp4_closedloop_128k', 'c16');

    new Chart(document.getElementById('canvasSchedKvUtil'), {
      type: 'bar',
      data: {
        labels: ['c1', 'c4', 'c8', 'c16', 'c32'],
        datasets: [
          {
            label: '8K KV Peak % (tp4_closedloop_8k)',
            data: [cl8_c1.kv_peak_pct, cl8_c4.kv_peak_pct, cl8_c8.kv_peak_pct, cl8_c16.kv_peak_pct, cl8_c32.kv_peak_pct],
            backgroundColor: '#38bdf8'
          },
          {
            label: '128K KV Peak % (tp4_closedloop_128k)',
            data: [cl128_c1.kv_peak_pct, cl128_c4.kv_peak_pct, cl128_c8.kv_peak_pct, cl128_c16.kv_peak_pct, null],
            backgroundColor: '#fb923c'
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'KV Block Utilization (%)' }, grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                if (ctx.raw === null) return `${ctx.dataset.label}: NOT RUN`;
                return `${ctx.dataset.label}: ${ctx.raw}% (exact evidence peak)`;
              }
            }
          }
        }
      }
    });

    // Chart 2: Queue Wait Time (Loaded from queue_mean_s_from_hist in ms)
    new Chart(document.getElementById('canvasSchedQueue'), {
      type: 'line',
      data: {
        labels: ['c1', 'c4', 'c8', 'c16', 'c32'],
        datasets: [
          {
            label: '8K Queue Mean (ms)',
            data: [
              cl8_c1.queue_mean_s_from_hist * 1000,
              cl8_c4.queue_mean_s_from_hist * 1000,
              cl8_c8.queue_mean_s_from_hist * 1000,
              cl8_c16.queue_mean_s_from_hist * 1000,
              cl8_c32.queue_mean_s_from_hist * 1000
            ],
            borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 2, pointRadius: 4
          },
          {
            label: '128K Queue Mean (ms)',
            data: [
              cl128_c1.queue_mean_s_from_hist * 1000,
              cl128_c4.queue_mean_s_from_hist * 1000,
              cl128_c8.queue_mean_s_from_hist * 1000,
              cl128_c16.queue_mean_s_from_hist * 1000,
              null
            ],
            borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'Queue Wait (ms)' }, grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } }
        }
      }
    });

    // Chart 3: max_num_seqs Dedicated Sweep at 512K c4 (Spec §10)
    const m4 = getEvidenceRow('tp4_512k_maxseq4', '512k_c4');
    const m8 = getEvidenceRow('tp4_512k_maxseq8', '512k_c4');
    const m16 = getEvidenceRow('tp4_512k_maxseq16', '512k_c4');

    new Chart(document.getElementById('canvasSchedTtftPcts'), {
      type: 'bar',
      data: {
        labels: ['max_num_seqs = 4', 'max_num_seqs = 8', 'max_num_seqs = 16'],
        datasets: [
          {
            label: 'TTFT (s)',
            data: [m4.ttft_ms / 1000, m8.ttft_ms / 1000, m16.ttft_ms / 1000],
            backgroundColor: '#38bdf8'
          },
          {
            label: 'TPOT (ms / 10)',
            data: [m4.tpot_ms / 10, m8.tpot_ms / 10, m16.tpot_ms / 10],
            backgroundColor: '#fb923c'
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'TTFT (s) / Scaled TPOT' }, grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } }
        }
      }
    });

    // Chart 4: Long-Context TPOT Degradation under Concurrency (Fig 6)
    const cl512_c1 = getEvidenceRow('tp4_closedloop_512k', 'c1');
    const cl512_c2 = getEvidenceRow('tp4_closedloop_512k', 'c2');
    const cl512_c4 = getEvidenceRow('tp4_closedloop_512k', 'c4');

    const cl1m_c1 = getEvidenceRow('tp4_closedloop_1m', 'c1');
    const cl1m_c2 = getEvidenceRow('tp4_closedloop_1m', 'c2');
    const cl1m_c4 = getEvidenceRow('tp4_closedloop_1m', 'c4');

    new Chart(document.getElementById('canvasSchedTpotPcts'), {
      type: 'line',
      data: {
        labels: ['c1', 'c2', 'c4'],
        datasets: [
          {
            label: '512K TPOT (ms)',
            data: [cl512_c1.tpot_ms, cl512_c2.tpot_ms, cl512_c4.tpot_ms],
            borderColor: '#fb923c', backgroundColor: '#fb923c', borderWidth: 2, pointRadius: 4
          },
          {
            label: '1M TPOT (ms)',
            data: [cl1m_c1.tpot_ms, cl1m_c2.tpot_ms, cl1m_c4.tpot_ms],
            borderColor: '#f43f5e', backgroundColor: '#f43f5e', borderWidth: 2, pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { title: { display: true, text: 'TPOT (ms/token)' }, grid: { color: '#131e33' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 8 } }
        }
      }
    });
  }"""

html = html.replace(old_sched_controller, new_sched_controller)

# Save updated HTML
with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Batch A applied to MASTER_CHARACTERIZATION_DASHBOARD.html successfully.")
