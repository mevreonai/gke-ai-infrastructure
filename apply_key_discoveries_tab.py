import sys
import os

files = [
    'v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/dashboards/v4_dashboard/index.html',
    'v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/release_specs/index.html'
]

CSS_CODE = """
/* === KEY DISCOVERIES TAB STYLING === */
#keydiscoveries {
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.kd-header-banner {
    background: #091322;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.kd-header-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}
.kd-title-group h1 {
    font-size: 24px;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 4px 0;
    letter-spacing: -0.3px;
}
.kd-title-group p {
    font-size: 11.5px;
    color: #94a3b8;
    margin: 0;
    max-width: 900px;
    line-height: 1.4;
}
.kd-mode-switch {
    display: flex;
    gap: 4px;
    background: #060d18;
    padding: 3px;
    border: 1px solid #1a2a44;
    border-radius: 6px;
}
.kd-mode-btn {
    padding: 4px 14px;
    font-size: 10px;
    font-weight: 700;
    border-radius: 4px;
    border: 1px solid transparent;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.15s ease;
}
.kd-mode-btn.active {
    background: #1d4ed8;
    color: #ffffff;
    border-color: #3b82f6;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
}
.kd-mode-btn:not(.active) {
    background: transparent;
    color: #64748b;
}
.kd-mode-btn:not(.active):hover {
    color: #cbd5e1;
    background: rgba(255, 255, 255, 0.04);
}
.kd-trust-strip {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    padding-top: 10px;
    border-top: 1px solid #152238;
    font-size: 10.5px;
}
.kd-model-pill {
    background: #0f1c30;
    border: 1px solid #233857;
    border-radius: 20px;
    padding: 3px 12px;
    color: #cbd5e1;
    font-weight: 600;
}
.kd-stat-item {
    display: flex;
    align-items: baseline;
    gap: 5px;
}
.kd-stat-num {
    font-size: 15px;
    font-weight: 800;
    color: #38bdf8;
}
.kd-stat-label {
    font-size: 10px;
    color: #94a3b8;
}
.kd-badge-validated {
    background: rgba(34, 197, 94, 0.12);
    border: 1px solid rgba(34, 197, 94, 0.4);
    color: #4ade80;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 9.5px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 4px;
}
.kd-badge-warning {
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #f87171;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 9.5px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 4px;
}
.kd-transport-info {
    margin-left: auto;
    color: #94a3b8;
    font-size: 10px;
}

/* 60-Second Finding Map */
.kd-map-card {
    background: #091322;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
}
.kd-map-title {
    font-size: 12px;
    font-weight: 800;
    color: #38bdf8;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.kd-map-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 10.5px;
}
.kd-map-table th {
    text-align: left;
    padding: 5px 8px;
    color: #64748b;
    font-weight: 700;
    border-bottom: 1px solid #1a2a44;
    text-transform: uppercase;
    font-size: 9px;
    letter-spacing: 0.5px;
}
.kd-map-table td {
    padding: 5px 8px;
    border-bottom: 1px solid #111e33;
    color: #cbd5e1;
    line-height: 1.3;
}
.kd-map-table tr:hover td {
    background: rgba(56, 189, 248, 0.05);
    color: #ffffff;
    cursor: pointer;
}
.kd-map-table td.num {
    font-weight: 800;
    color: #38bdf8;
    width: 24px;
}
.kd-map-table td.finding {
    font-weight: 700;
    color: #f1f5f9;
    width: 150px;
}
.kd-map-table td.surprise {
    color: #94a3b8;
}
.kd-map-table td.decision {
    color: #facc15;
    font-weight: 500;
}

/* Grid Layouts */
.kd-section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #94a3b8;
    margin: 16px 0 10px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #1a2a44;
}
.kd-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 16px;
}
.kd-grid-4 {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 16px;
}
@media (max-width: 1400px) {
    .kd-grid-4 {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
@media (max-width: 1024px) {
    .kd-grid-3 {
        grid-template-columns: 1fr;
    }
    .kd-grid-4 {
        grid-template-columns: 1fr;
    }
}

/* Card Styling */
.kd-card {
    background: #091322;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease;
    position: relative;
}
.kd-card:hover {
    border-color: #2563eb;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}
.kd-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
}
.kd-card-num-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 800;
    color: #ffffff;
}
.kd-card-num {
    background: #1e3a8a;
    color: #93c5fd;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 800;
}
.kd-open-eng-btn {
    background: transparent;
    border: 1px solid #233857;
    color: #38bdf8;
    font-size: 9px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
}
.kd-open-eng-btn:hover {
    background: rgba(56, 189, 248, 0.15);
    border-color: #38bdf8;
    color: #ffffff;
}
.kd-card-sub {
    font-size: 10.5px;
    color: #94a3b8;
    line-height: 1.35;
    margin-bottom: 10px;
    min-height: 28px;
}

/* Hero Numbers */
.kd-hero-metric {
    font-size: 20px;
    font-weight: 900;
    color: #facc15;
    letter-spacing: -0.3px;
    margin-bottom: 2px;
}
.kd-hero-caption {
    font-size: 9.5px;
    color: #64748b;
    margin-bottom: 10px;
}

/* Heatmap & Tables */
.kd-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5px;
    margin-bottom: 10px;
}
.kd-table th {
    text-align: left;
    padding: 3px 5px;
    color: #64748b;
    border-bottom: 1px solid #1a2a44;
    font-weight: 700;
}
.kd-table td {
    padding: 3px 5px;
    border-bottom: 1px solid #101c30;
    color: #cbd5e1;
}
.kd-heatmap-cell {
    font-weight: 700;
    text-align: right;
    padding: 3px 6px;
    border-radius: 2px;
}
.kd-hm-blue-1 { background: #0c213d; color: #93c5fd; }
.kd-hm-blue-2 { background: #11325d; color: #bfdbfe; }
.kd-hm-blue-3 { background: #19437d; color: #dbeafe; }
.kd-hm-green { background: #0d2822; color: #86efac; }
.kd-hm-red-1 { background: #451119; color: #fca5a5; }
.kd-hm-red-2 { background: #5c1421; color: #fecaca; }
.kd-hm-red-3 { background: #731728; color: #ffffff; font-weight: 800; }

/* Sub-panels & Decision Box */
.kd-info-box {
    background: #060e1a;
    border: 1px solid #16243b;
    border-radius: 4px;
    padding: 6px 8px;
    margin-bottom: 8px;
    font-size: 9.5px;
}
.kd-decision-box {
    background: rgba(250, 204, 21, 0.05);
    border-left: 2px solid #eab308;
    border-radius: 0 4px 4px 0;
    padding: 6px 8px;
    margin: 8px 0;
    font-size: 9.5px;
    color: #fef08a;
    line-height: 1.35;
}
.kd-decision-box b {
    color: #fde047;
}

/* Footer & Badges */
.kd-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 8px;
    border-top: 1px solid #142238;
    margin-top: auto;
}
.kd-pill-group {
    display: flex;
    gap: 4px;
    align-items: center;
}
.kd-pill {
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.kd-pill-high { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
.kd-pill-med { background: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
.kd-pill-low { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.kd-inspect-btn {
    background: transparent;
    border: none;
    color: #38bdf8;
    font-size: 9px;
    font-weight: 700;
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    gap: 2px;
}
.kd-inspect-btn:hover {
    color: #7dd3fc;
    text-decoration: underline;
}

/* Engineer Mode Elements */
.kd-eng-detail {
    display: none;
    background: #040912;
    border: 1px dashed #1e3a8a;
    border-radius: 4px;
    padding: 8px;
    margin: 8px 0;
    font-size: 9px;
    color: #94a3b8;
}
body.kd-mode-engineer .kd-eng-detail {
    display: block;
}
body.kd-mode-forensics .kd-eng-detail {
    display: block;
}

/* Deep Modal View */
#kd-deep-modal-backdrop {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(2, 6, 15, 0.85);
    backdrop-filter: blur(4px);
    z-index: 9998;
}
#kd-deep-modal {
    display: none;
    position: fixed;
    top: 5vh;
    left: 10vw;
    width: 80vw;
    height: 90vh;
    background: #07111e;
    border: 1px solid #1e3a8a;
    border-radius: 8px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
    z-index: 9999;
    flex-direction: column;
    overflow: hidden;
}
.kd-modal-header {
    background: #091527;
    padding: 14px 20px;
    border-bottom: 1px solid #1e3a8a;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.kd-modal-tabs {
    display: flex;
    gap: 8px;
    padding: 8px 20px;
    background: #060e1a;
    border-bottom: 1px solid #14243b;
}
.kd-modal-tab-btn {
    background: transparent;
    border: 1px solid transparent;
    color: #94a3b8;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 10.5px;
    font-weight: 700;
    cursor: pointer;
}
.kd-modal-tab-btn.active {
    background: #1e3a8a;
    color: #ffffff;
    border-color: #3b82f6;
}
.kd-modal-body {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
}
"""

TAB_HTML = """
<!-- KEY DISCOVERIES TAB (NEW ENTITY - SINGLE-PAGE SIGNAL IMPLEMENTATION V4) -->
<section class="tabpage" id="keydiscoveries">
  <div class="kd-header-banner">
    <div class="kd-header-top">
      <div class="kd-title-group">
        <h1>Key Deployment Findings</h1>
        <p>Ten evidence-backed findings from the V8 characterization campaign. Start with the measured signal, expand any finding for engineering detail or exact raw provenance.</p>
      </div>
      <div class="kd-mode-switch">
        <button class="kd-mode-btn active" id="kd-btn-signal" onclick="setKeyDiscoveriesMode('signal')">Signal</button>
        <button class="kd-mode-btn" id="kd-btn-engineer" onclick="setKeyDiscoveriesMode('engineer')">Engineer</button>
        <button class="kd-mode-btn" id="kd-btn-forensics" onclick="setKeyDiscoveriesMode('forensics')">Forensics</button>
      </div>
    </div>
    <div class="kd-trust-strip">
      <div class="kd-model-pill">Kimi-Linear 48B surrogate &middot; BF16 &middot; 16&times; RTX PRO 6000 Blackwell</div>
      <div class="kd-stat-item">
        <span class="kd-stat-num">119/126</span>
        <span class="kd-stat-label">application rows complete</span>
      </div>
      <div class="kd-stat-item">
        <span class="kd-stat-num">14/22</span>
        <span class="kd-stat-label">distributed profiles complete</span>
      </div>
      <div class="kd-badge-validated">
        <span>&#10004;</span> E2E RUN MATRIX VALIDATED
      </div>
      <div class="kd-badge-warning">
        <span>&#9888;</span> STRICT SUITE SIGN-OFF INCOMPLETE
      </div>
      <div class="kd-transport-info">
        Measured transport: <b>Native 173.58 Gb/s</b> &middot; <b>100G 56.84 Gb/s</b> &middot; <b>20G 16.48 Gb/s</b>
      </div>
    </div>
  </div>

  <!-- 60-Second Finding Map -->
  <div class="kd-map-card">
    <div class="kd-map-title">
      <span>&#128506;</span> 60-second Finding Map (Click to Focus Finding)
    </div>
    <table class="kd-map-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Finding</th>
          <th>Measured surprise</th>
          <th>Decision</th>
        </tr>
      </thead>
      <tbody>
        <tr onclick="focusKeyDiscovery(1)">
          <td class="num">1</td>
          <td class="finding">Fabric Exposure</td>
          <td class="surprise">1M/20G: TP16/PP1 +276.7% TTFT vs TP4/PP4 +3.9%</td>
          <td class="decision">Topology controls exposed fabric risk</td>
        </tr>
        <tr onclick="focusKeyDiscovery(2)">
          <td class="num">2</td>
          <td class="finding">Concurrency</td>
          <td class="surprise">1M TP4 c1&rarr;c4: +1.52% output TPS, 2.48&times; TTFT, 26.15&times; TPOT</td>
          <td class="decision">Admission from queue/latency SLO, not memory fit</td>
        </tr>
        <tr onclick="focusKeyDiscovery(3)">
          <td class="num">3</td>
          <td class="finding">Long Context</td>
          <td class="surprise">128K&rarr;512K: Attention ~15.7&times;, NCCL ~2.18&times;, KDA ~3.9&times;, MoE ~3.8&times;</td>
          <td class="decision">Optimization target shifts with context</td>
        </tr>
        <tr onclick="focusKeyDiscovery(4)">
          <td class="num">4</td>
          <td class="finding">Prefix Reuse</td>
          <td class="surprise">1M: first/cold 94.2272 s &rarr; repeat-hit median 2.6140 s (~36.0&times;)</td>
          <td class="decision">Repeated-prefix traffic is a different latency regime</td>
        </tr>
        <tr onclick="focusKeyDiscovery(5)">
          <td class="num">5</td>
          <td class="finding">Prompt Tokens</td>
          <td class="surprise">High-load normalized input rate: 8K ~27.5K tok/s vs 128K ~24.2K tok/s</td>
          <td class="decision">Compare prefill-heavy demand in tokens/s, not only req/s</td>
        </tr>
        <tr onclick="focusKeyDiscovery(6)">
          <td class="num">6</td>
          <td class="finding">Parallelism Frontier</td>
          <td class="surprise">1M GPU-s/request frontier: TP4/PP1 373.0 &rarr; TP4/PP2 420.2 &rarr; TP4/PP4 457.1</td>
          <td class="decision">Show latency/resource frontier, not one winner</td>
        </tr>
        <tr onclick="focusKeyDiscovery(7)">
          <td class="num">7</td>
          <td class="finding">TP Decode</td>
          <td class="surprise">Same 7040 AllReduce calls; TP8 rank-local Self CUDA 583.866 ms vs TP4 251.529 ms; 8K TPOT 6.3500 ms vs 4.4748 ms</td>
          <td class="decision">Wider TP can hurt interactive decode</td>
        </tr>
        <tr onclick="focusKeyDiscovery(8)">
          <td class="num">8</td>
          <td class="finding">Runtime Knobs</td>
          <td class="surprise">max_num_seqs 4/8/16: 232.342 / 232.364 / 232.250 s; chunk 4K&rarr;8K&rarr;16K: 122.049 &rarr; 93.277 &rarr; 88.951 s</td>
          <td class="decision">Tune only knobs with measured derivative</td>
        </tr>
        <tr onclick="focusKeyDiscovery(9)">
          <td class="num">9</td>
          <td class="finding">Busy GPU</td>
          <td class="surprise">1M: TP4/PP4 62.8% util @ 28.568 s vs TP16/PP1 80.6% util @ 68.197 s</td>
          <td class="decision">GPU busy != efficient serving</td>
        </tr>
        <tr onclick="focusKeyDiscovery(10)">
          <td class="num">10</td>
          <td class="finding">KV vs VRAM</td>
          <td class="surprise">1M TP4/PP4: 2.75% peak KV vs 88.83 GiB peak GPU memory</td>
          <td class="decision">KV pressure and VRAM headroom are different metrics</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- SECTION 1: ARCHITECTURE & FABRIC (GRID 3) -->
  <div class="kd-section-header">
    <span>&#127979;</span> Architecture &amp; Fabric Exposure
  </div>
  <div class="kd-grid-3">
    <!-- CARD 1: FABRIC EXPOSURE FINGERPRINT -->
    <div class="kd-card" id="kd-card-1">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">1</span>
            <span>Fabric Exposure Fingerprint</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(1)">Open Engineer View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          The same measured fabric constraint produces radically different TTFT damage depending on topology.
        </div>
        <div class="kd-hero-metric">+276.7% vs +3.9% TTFT</div>
        <div class="kd-hero-caption">1M c1 TTFT degradation under 20G condition</div>

        <div style="font-size:9px;font-weight:700;color:#94a3b8;margin-bottom:4px">20G TTFT Degradation vs Native (&Delta;%)</div>
        <table class="kd-table">
          <thead>
            <tr><th>Topology</th><th style="text-align:right">128K</th><th style="text-align:right">512K</th><th style="text-align:right">1M</th></tr>
          </thead>
          <tbody>
            <tr><td>TP4/PP2</td><td class="kd-heatmap-cell kd-hm-blue-1">+8.0%</td><td class="kd-heatmap-cell kd-hm-blue-1">+2.4%</td><td class="kd-heatmap-cell kd-hm-blue-1">+1.1%</td></tr>
            <tr><td>TP8/PP2</td><td class="kd-heatmap-cell kd-hm-blue-1">+0.8%</td><td class="kd-heatmap-cell kd-hm-green">-0.2%</td><td class="kd-heatmap-cell kd-hm-green">-0.1%</td></tr>
            <tr><td>TP4/PP4</td><td class="kd-heatmap-cell kd-hm-blue-2">+14.7%</td><td class="kd-heatmap-cell kd-hm-blue-1">+8.9%</td><td class="kd-heatmap-cell kd-hm-blue-1">+3.9%</td></tr>
            <tr><td>TP16/PP1</td><td class="kd-heatmap-cell kd-hm-red-3">+383.7%</td><td class="kd-heatmap-cell kd-hm-red-2">+333.0%</td><td class="kd-heatmap-cell kd-hm-red-1">+276.7%</td></tr>
          </tbody>
        </table>

        <div style="font-size:9px;font-weight:700;color:#94a3b8;margin:8px 0 4px">Transport Layer Measurements</div>
        <table class="kd-table">
          <thead>
            <tr><th>Condition</th><th>Native</th><th>100G</th><th>20G</th></tr>
          </thead>
          <tbody>
            <tr><td>Measured iperf (Gb/s)</td><td>173.58</td><td>56.84</td><td>16.48</td></tr>
            <tr><td>Measured 256M SendRecv</td><td>~7.11 GB/s</td><td>~5.54 GB/s</td><td>~2.04 GB/s</td></tr>
            <tr><td>Application response</td><td>Baseline</td><td>Intermed.</td><td>TTFT Tax</td></tr>
          </tbody>
        </table>

        <div class="kd-eng-detail">
          <b>Engineer Context Rail:</b> 8K: &mdash; | 128K: &#9679; | 512K: &#9679; | 1M: &#9679;<br>
          <b>Latency Tax:</b> 128K +24.63s | 512K +98.65s | 1M +188.69s on TP16/PP1
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Choose scale-out topology from measured application exposure to transport degradation, not from NIC/iperf alone.
        </div>
      </div>

      <div class="kd-card-footer">
        <div class="kd-pill-group">
          <span class="kd-pill kd-pill-high">Evidence HIGH</span>
          <span class="kd-pill kd-pill-med">Cause MED-HIGH</span>
        </div>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('tp16_pp1_dist_1m_c1_capped_20g')">Inspect Evidence &rarr;</button>
      </div>
    </div>

    <!-- CARD 2: CONCURRENCY VALUE DESTRUCTION -->
    <div class="kd-card" id="kd-card-2">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">2</span>
            <span>Concurrency Value Destruction</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(2)">Open Engineer View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          At 1M, concurrency spends latency but buys almost no output throughput.
        </div>
        <div class="kd-hero-metric">+1.52% Output TPS &middot; 2.48&times; TTFT</div>
        <div class="kd-hero-caption" style="color:#fde047">26.15&times; TPOT &middot; 134.43 s Queue</div>

        <table class="kd-table">
          <thead>
            <tr><th>Metric (1M TP4/PP1)</th><th>c1</th><th>c2</th><th>c4</th></tr>
          </thead>
          <tbody>
            <tr><td>Output TPS</td><td>0.34147</td><td>0.34486 (+0.99%)</td><td>0.34666 (+1.52%)</td></tr>
            <tr><td>TTFT</td><td>93.395 s</td><td>139.374 s (1.49&times;)</td><td>231.268 s (2.48&times;)</td></tr>
            <tr><td>TPOT</td><td>10.228 ms</td><td>181.974 ms (17.79&times;)</td><td>267.411 ms (26.15&times;)</td></tr>
            <tr><td>Queue time</td><td>~0 s</td><td>44.340 s</td><td>134.428 s</td></tr>
            <tr><td>Peak KV usage</td><td>12.29%</td><td>15.52%</td><td>15.51%</td></tr>
            <tr><td>Preemptions</td><td>0</td><td>0</td><td>0</td></tr>
          </tbody>
        </table>

        <div class="kd-info-box">
          <div style="font-size:8.5px;color:#94a3b8;margin-bottom:3px;font-weight:700">Queue-accounting closure (measured vs predicted)</div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;text-align:center;font-size:9px">
            <div style="background:#0b192e;padding:3px;border-radius:2px"><span style="color:#64748b">TP4 c2</span><br><b style="color:#4ade80">96.4%</b></div>
            <div style="background:#0b192e;padding:3px;border-radius:2px"><span style="color:#64748b">TP4 c4</span><br><b style="color:#4ade80">97.5%</b></div>
            <div style="background:#0b192e;padding:3px;border-radius:2px"><span style="color:#64748b">TP8 c2</span><br><b style="color:#4ade80">95.7%</b></div>
            <div style="background:#0b192e;padding:3px;border-radius:2px"><span style="color:#64748b">TP8 c4</span><br><b style="color:#4ade80">97.2%</b></div>
          </div>
        </div>

        <div class="kd-eng-detail">
          <b>8K Benchmark Contrast:</b> 8K c1&rarr;c4 yields <b>+120.82% TPS</b> (0.027s queue), while 1M yields only <b>+1.52% TPS</b> with 134.43s queue.
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Define admission from TTFT/TPOT/queue SLOs; &ldquo;fits in KV&rdquo; is not the production-capacity criterion.
        </div>
      </div>

      <div class="kd-card-footer">
        <div class="kd-pill-group">
          <span class="kd-pill kd-pill-high">Evidence HIGH</span>
          <span class="kd-pill kd-pill-med">Cause MED-HIGH</span>
        </div>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('tp4_1m_c4')">Inspect Evidence &rarr;</button>
      </div>
    </div>

    <!-- CARD 3: LONG-CONTEXT RESOURCE-PRESSURE SHIFT -->
    <div class="kd-card" id="kd-card-3">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">3</span>
            <span>Long-Context Resource-Pressure Shift</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(3)">Open Engineer View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          As context grows, full-attention work accelerates much faster than KDA, MoE, or NCCL in matched profiles.
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <span style="font-size:9px;font-weight:700;color:#94a3b8">GPU Work Growth (128K &rarr; 512K)</span>
          <span style="font-size:8px;color:#64748b">TP4/PP4 Profile Pair</span>
        </div>

        <!-- Visual Growth Bars -->
        <div style="display:flex;flex-direction:column;gap:5px;margin-bottom:8px">
          <div>
            <div style="display:flex;justify-content:space-between;font-size:8.5px;margin-bottom:2px">
              <span style="color:#f87171">&#9679; Full attention (O(N&sup2;))</span>
              <b style="color:#f87171">15.7&times; (exp 1.99)</b>
            </div>
            <div style="background:#132238;height:6px;border-radius:3px;overflow:hidden">
              <div style="background:#ef4444;width:100%;height:100%"></div>
            </div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:8.5px;margin-bottom:2px">
              <span style="color:#38bdf8">&#9679; GEMM family</span>
              <b style="color:#38bdf8">5.25&times; (exp 1.20)</b>
            </div>
            <div style="background:#132238;height:6px;border-radius:3px;overflow:hidden">
              <div style="background:#38bdf8;width:33.4%;height:100%"></div>
            </div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:8.5px;margin-bottom:2px">
              <span style="color:#4ade80">&#9679; KDA Recurrent State</span>
              <b style="color:#4ade80">3.9&times; (exp 0.99)</b>
            </div>
            <div style="background:#132238;height:6px;border-radius:3px;overflow:hidden">
              <div style="background:#22c55e;width:24.8%;height:100%"></div>
            </div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:8.5px;margin-bottom:2px">
              <span style="color:#c084fc">&#9679; Fused MoE Routing</span>
              <b style="color:#c084fc">3.8&times; (exp 0.96)</b>
            </div>
            <div style="background:#132238;height:6px;border-radius:3px;overflow:hidden">
              <div style="background:#a855f7;width:24.2%;height:100%"></div>
            </div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:8.5px;margin-bottom:2px">
              <span style="color:#facc15">&#9679; NCCL SendRecv</span>
              <b style="color:#facc15">2.18&times; (exp 0.56)</b>
            </div>
            <div style="background:#132238;height:6px;border-radius:3px;overflow:hidden">
              <div style="background:#eab308;width:13.9%;height:100%"></div>
            </div>
          </div>
        </div>

        <div style="padding:4px 8px;background:rgba(56,189,248,0.06);border-left:2px solid #38bdf8;font-size:8.5px;color:#93c5fd;margin-bottom:6px">
          &#8505; Aggregate GPU work != exclusive request wall-clock critical path
        </div>

        <div class="kd-eng-detail">
          <b>Artifact Registry Lineage:</b> PR-005 (128K prefill, 22.8% FlashAttn) &rarr; PR-007 (512K prefill, 44.8% FlashAttn)
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Do not tune long-context serving from a single 128K profile; re-evaluate the optimization target as context increases.
        </div>
      </div>

      <div class="kd-card-footer">
        <div class="kd-pill-group">
          <span class="kd-pill kd-pill-high">Evidence HIGH</span>
          <span class="kd-pill kd-pill-med">Cause MEDIUM</span>
        </div>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('PR-007')">Inspect Evidence &rarr;</button>
      </div>
    </div>
  </div>

  <!-- SECTION 2: OPTIMIZATION & REUSE (GRID 4) -->
  <div class="kd-section-header">
    <span>&#9881;</span> Optimization, Knobs &amp; Reuse Regimes
  </div>
  <div class="kd-grid-4">
    <!-- CARD 4: PREFIX REUSE -->
    <div class="kd-card" id="kd-card-4">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">4</span>
            <span>Prefix Reuse Curve</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(4)">View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          Repeated-prefix traffic changes latency scaling from quadratic to near constant.
        </div>

        <table class="kd-table">
          <thead>
            <tr><th>Context</th><th>Cold TTFT</th><th>Repeat-hit</th><th>Speedup</th></tr>
          </thead>
          <tbody>
            <tr><td>128K</td><td>4.8965 s</td><td>0.3307 s</td><td style="color:#4ade80;font-weight:700">~14.8&times;</td></tr>
            <tr><td>512K</td><td>32.5762 s</td><td>1.1679 s</td><td style="color:#4ade80;font-weight:700">~27.9&times;</td></tr>
            <tr><td>1M</td><td>94.2272 s</td><td>2.6140 s</td><td style="color:#4ade80;font-weight:800">~36.0&times;</td></tr>
          </tbody>
        </table>

        <div class="kd-eng-detail">
          Prefix counters: 128K: 87.33% hit ratio | 512K: 49.98% | 1M: 49.97%
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Treat repeated-prefix traffic as a distinct workload class.
        </div>
      </div>
      <div class="kd-card-footer">
        <span class="kd-pill kd-pill-high">Evidence HIGH</span>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('EV-075')">Inspect &rarr;</button>
      </div>
    </div>

    <!-- CARD 5: PARALLELISM FRONTIER -->
    <div class="kd-card" id="kd-card-5">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">5</span>
            <span>Parallelism Frontier</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(5)">View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          Expose latency/resource trade-off along positive elasticity frontier.
        </div>

        <div style="background:#050c17;padding:6px;border-radius:4px;margin-bottom:8px">
          <div style="font-size:8.5px;color:#94a3b8;margin-bottom:4px;font-weight:700">1M Native Latency/GPU-s Frontier</div>
          <div style="display:flex;justify-content:space-between;font-size:8.5px;color:#cbd5e1;padding:2px 0;border-bottom:1px solid #132238">
            <span>TP4/PP1 (4 GPUs)</span><b>93.2s &middot; 373 GPU-s</b>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:8.5px;color:#38bdf8;padding:2px 0;border-bottom:1px solid #132238">
            <span>TP4/PP2 (8 GPUs)</span><b>52.5s &middot; 420 GPU-s</b>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:8.5px;color:#4ade80;padding:2px 0">
            <span>TP4/PP4 (16 GPUs)</span><b>28.6s &middot; 457 GPU-s</b>
          </div>
        </div>

        <div class="kd-eng-detail">
          TP4 vs TP8: 8K TP4 is +18.5% faster; 1M TP8 is +19.9% faster. Elasticity flips with context!
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Expose latency/resource trade-off instead of naming a universal winner.
        </div>
      </div>
      <div class="kd-card-footer">
        <span class="kd-pill kd-pill-high">Evidence HIGH</span>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('tp4_pp4_dist_1m_c1_native')">Inspect &rarr;</button>
      </div>
    </div>

    <!-- CARD 6: PROMPT-TOKEN ADMISSION -->
    <div class="kd-card" id="kd-card-6">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">6</span>
            <span>Prompt-Token Fingerprint</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(6)">View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          Achieved input token rate normalizes prefill load across prompt lengths.
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px">
          <div style="background:#060e1a;padding:5px;border-radius:3px;text-align:center">
            <span style="font-size:7.5px;color:#64748b">REQUESTS / S</span><br>
            <b style="font-size:11px;color:#f87171">8K: 3.36</b><br>
            <b style="font-size:10px;color:#cbd5e1">128K: 0.185</b><br>
            <span style="font-size:7.5px;color:#f87171">~18.2&times; gap</span>
          </div>
          <div style="background:#060e1a;padding:5px;border-radius:3px;text-align:center">
            <span style="font-size:7.5px;color:#64748b">INPUT TOKENS / S</span><br>
            <b style="font-size:11px;color:#4ade80">8K: ~27.5K</b><br>
            <b style="font-size:10px;color:#cbd5e1">128K: ~24.2K</b><br>
            <span style="font-size:7.5px;color:#4ade80">~1.14&times; gap</span>
          </div>
        </div>

        <div class="kd-eng-detail">
          Median achieved throughput evaluated across 1.00&times;, 1.10&times;, and 1.25&times; offered open-loop load.
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Normalize prefill-heavy demand into prompt tokens/s before comparing capacity.
        </div>
      </div>
      <div class="kd-card-footer">
        <span class="kd-pill kd-pill-med">Evidence MED-HIGH</span>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('EV-051')">Inspect &rarr;</button>
      </div>
    </div>

    <!-- CARD 7: RUNTIME KNOBS -->
    <div class="kd-card" id="kd-card-7">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">7</span>
            <span>Runtime-Knob Derivative</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(7)">View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          Chunk size has steep leverage; max_num_seqs is non-binding in measured state.
        </div>

        <div style="font-size:8px;color:#94a3b8;margin-bottom:2px;font-weight:700">Chunk size at 1M c1: High leverage</div>
        <div style="display:flex;justify-content:space-between;font-size:8.5px;color:#cbd5e1;background:#050c17;padding:3px 5px;border-radius:2px;margin-bottom:4px">
          <span>4K: 122.0s</span><span>8K: 93.3s</span><b style="color:#4ade80">16K: 88.9s (-27.1%)</b>
        </div>

        <div style="font-size:8px;color:#94a3b8;margin-bottom:2px;font-weight:700">max_num_seqs at 1M c4: Non-binding</div>
        <div style="display:flex;justify-content:space-between;font-size:8.5px;color:#94a3b8;background:#050c17;padding:3px 5px;border-radius:2px;margin-bottom:8px">
          <span>4: 232.3s</span><span>8: 232.4s</span><span>16: 232.2s (spread 0.05%)</span>
        </div>

        <div class="kd-eng-detail">
          Telemetry proves peak_running=2, peak_waiting=3. Configured ceiling is never reached.
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Tune only knobs with a material matched A/B derivative in the measured state.
        </div>
      </div>
      <div class="kd-card-footer">
        <span class="kd-pill kd-pill-high">Evidence HIGH</span>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('EV-035')">Inspect &rarr;</button>
      </div>
    </div>
  </div>

  <!-- SECTION 3: EVIDENCE CHAIN & OPERATIONAL TRAPS (GRID 3) -->
  <div class="kd-section-header">
    <span>&#128269;</span> Evidence Chain &amp; Operational Traps
  </div>
  <div class="kd-grid-3">
    <!-- CARD 8: TP DECODE EVIDENCE CHAIN -->
    <div class="kd-card" id="kd-card-8">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">8</span>
            <span>TP Decode Evidence Chain</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(8)">Open Engineer View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          Cross-NUMA AllReduce latency overhead accumulates across decode turns on TP8.
        </div>

        <!-- 4 Block Flow -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:10px;text-align:center">
          <div style="background:#060e1a;border:1px solid #1a2a44;padding:4px;border-radius:3px">
            <span style="font-size:7px;color:#38bdf8;font-weight:700">1. NCCL</span><br>
            <span style="font-size:8px;color:#cbd5e1">TP8 latency<br><b style="color:#f87171">~1.9&ndash;2.2&times;</b></span>
          </div>
          <div style="background:#060e1a;border:1px solid #1a2a44;padding:4px;border-radius:3px">
            <span style="font-size:7px;color:#38bdf8;font-weight:700">2. PROFILER</span><br>
            <span style="font-size:8px;color:#cbd5e1">Self CUDA<br><b style="color:#f87171">251 &rarr; 584ms</b></span>
          </div>
          <div style="background:#060e1a;border:1px solid #1a2a44;padding:4px;border-radius:3px">
            <span style="font-size:7px;color:#38bdf8;font-weight:700">3. NSIGHT</span><br>
            <span style="font-size:8px;color:#cbd5e1">AllReduce is<br>dominant cat.</span>
          </div>
          <div style="background:#060e1a;border:1px solid #1a2a44;padding:4px;border-radius:3px">
            <span style="font-size:7px;color:#38bdf8;font-weight:700">4. E2E TPOT</span><br>
            <span style="font-size:8px;color:#cbd5e1">8K TPOT<br><b style="color:#f87171">+41.9%</b></span>
          </div>
        </div>

        <div class="kd-eng-detail">
          Exact invocation count matches: 7,040 AllReduce calls on both TP4 and TP8. Cross-socket bridge adds 332.4ms.
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Wider TP can hurt interactive decode.
        </div>
      </div>
      <div class="kd-card-footer">
        <div class="kd-pill-group">
          <span class="kd-pill kd-pill-high">Evidence HIGH</span>
          <span class="kd-pill kd-pill-med">Cause MED-HIGH</span>
        </div>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('PR-003')">Inspect Evidence &rarr;</button>
      </div>
    </div>

    <!-- CARD 9: BUSY GPU != EFFICIENT SERVING -->
    <div class="kd-card" id="kd-card-9">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">9</span>
            <span>Busy GPU != Efficient Serving</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(9)">Open Engineer View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          High GPU utilization often reflects communication waiting rather than useful throughput.
        </div>

        <table class="kd-table">
          <thead>
            <tr><th>Context</th><th>TP4/PP4 Util</th><th>TP4/PP4 TTFT</th><th>TP16/PP1 Util</th><th>TP16/PP1 TTFT</th></tr>
          </thead>
          <tbody>
            <tr><td>128K</td><td>35.2%</td><td style="color:#4ade80">1.710 s</td><td>63.2%</td><td>6.420 s</td></tr>
            <tr><td>512K</td><td>55.3%</td><td style="color:#4ade80">10.222 s</td><td>67.8%</td><td>29.624 s</td></tr>
            <tr><td>1M</td><td>62.8%</td><td style="color:#4ade80">28.568 s</td><td>80.6%</td><td style="color:#f87171">68.197 s</td></tr>
          </tbody>
        </table>

        <div style="font-size:9.5px;color:#fde047;background:#060e1a;padding:4px 6px;border-radius:3px;margin-bottom:8px">
          1M: TP16/PP1 is <b>2.39&times; slower</b> despite reporting <b>80.6%</b> GPU utilization.
        </div>

        <div class="kd-eng-detail">
          GPU utilization captures active SM cycles from synchronization loops; it does not measure token progress.
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Never use GPU utilization alone to choose topology.
        </div>
      </div>
      <div class="kd-card-footer">
        <div class="kd-pill-group">
          <span class="kd-pill kd-pill-high">Evidence HIGH</span>
          <span class="kd-pill kd-pill-med">Cause MEDIUM</span>
        </div>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('tp16_pp1_dist_1m_c1_native')">Inspect Evidence &rarr;</button>
      </div>
    </div>

    <!-- CARD 10: KV HEADROOM != VRAM HEADROOM -->
    <div class="kd-card" id="kd-card-10">
      <div>
        <div class="kd-card-header">
          <div class="kd-card-num-title">
            <span class="kd-card-num">10</span>
            <span>KV Headroom != VRAM Headroom</span>
          </div>
          <button class="kd-open-eng-btn" onclick="openKeyDiscoveryDetail(10)">Open Engineer View &rarr;</button>
        </div>
        <div class="kd-card-sub">
          Pipeline parallelism dilutes reported KV% while physical device VRAM remains high and flat.
        </div>

        <table class="kd-table">
          <thead>
            <tr><th>Configuration (1M)</th><th>Peak KV usage (%)</th><th>Peak GPU memory (GiB)</th></tr>
          </thead>
          <tbody>
            <tr><td>TP4 / PP1</td><td>12.29%</td><td>88.39 GiB</td></tr>
            <tr><td>TP4 / PP2</td><td>5.91%</td><td>88.69 GiB</td></tr>
            <tr><td>TP4 / PP4</td><td style="color:#38bdf8;font-weight:700">2.75%</td><td style="color:#fde047;font-weight:700">88.83 GiB</td></tr>
            <tr><td>TP16 / PP1</td><td>12.13%</td><td>86.71 GiB</td></tr>
          </tbody>
        </table>

        <div style="font-size:8.5px;color:#64748b;margin-bottom:6px">
          Raw device capacity reported in preflight: 97,887 MiB &approx; 95.59 GiB per GPU
        </div>

        <div class="kd-eng-detail">
          TP8 Replication confirms pattern: TP8/PP1 12.18% KV &rarr; TP8/PP2 5.88% KV while memory remains 88.7 GiB.
        </div>

        <div class="kd-decision-box">
          <b>Decision changed:</b> Use KV% for cache pressure and memory telemetry for true VRAM headroom; never substitute one for the other.
        </div>
      </div>
      <div class="kd-card-footer">
        <div class="kd-pill-group">
          <span class="kd-pill kd-pill-high">Evidence HIGH</span>
          <span class="kd-pill kd-pill-med">Cause MED-HIGH</span>
        </div>
        <button class="kd-inspect-btn" onclick="window.openEvidencePopup('EV-084')">Inspect Evidence &rarr;</button>
      </div>
    </div>
  </div>

  <!-- FOOTER TRUST & CONFORMANCE STRIP -->
  <div style="background:#091322;border:1px solid #1a2a44;border-radius:6px;padding:10px 14px;margin-top:10px;font-size:9.5px;color:#94a3b8;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
    <div>
      &#8505; All values shown above are taken from canonical V8 run data, HTML evidence, or the V3 review spec. Derived values are explicitly labeled in the UI.
    </div>
    <div style="display:flex;gap:8px;align-items:center">
      <span>Evidence: <b style="color:#4ade80">&#9679; HIGH</b> <b style="color:#facc15">&#9679; MEDIUM</b> <b style="color:#f87171">&#9679; LOW</b></span>
      <span>&middot;</span>
      <span>Cause confidence: <b style="color:#4ade80">&#9679; HIGH</b> <b style="color:#facc15">&#9679; MEDIUM</b> <b style="color:#f87171">&#9679; LOW</b></span>
    </div>
  </div>
</section>

<!-- SUB-PAGE DEEP DETAIL MODAL (INTERACTIVE DISCOVERY EXPLORER) -->
<div id="kd-deep-modal-backdrop" onclick="closeKeyDiscoveryDetail()"></div>
<div id="kd-deep-modal">
  <div class="kd-modal-header">
    <div>
      <div style="font-size:10px;font-weight:700;color:#38bdf8;text-transform:uppercase" id="kd-modal-eyebrow">FINDING DETAIL &middot; ENGINEER DEPTH</div>
      <div style="font-size:16px;font-weight:800;color:#fff" id="kd-modal-title">Finding Detail</div>
    </div>
    <button onclick="closeKeyDiscoveryDetail()" style="background:#132238;border:1px solid #233854;color:#cbd5e1;font-size:16px;width:28px;height:28px;border-radius:4px;cursor:pointer">&times;</button>
  </div>
  <div class="kd-modal-tabs">
    <button class="kd-modal-tab-btn active" id="kd-mtab-btn-findings" onclick="switchKdModalTab('findings')">Findings &amp; Telemetry</button>
    <button class="kd-modal-tab-btn" id="kd-mtab-btn-derivation" onclick="switchKdModalTab('derivation')">Derivations &amp; Formulas</button>
    <button class="kd-modal-tab-btn" id="kd-mtab-btn-profiler" onclick="switchKdModalTab('profiler')">Profiler &amp; Kernel Shares</button>
    <button class="kd-modal-tab-btn" id="kd-mtab-btn-artifacts" onclick="switchKdModalTab('artifacts')">Raw Artifact Provenance</button>
  </div>
  <div class="kd-modal-body" id="kd-modal-body">
    <!-- Populated dynamically via JS -->
  </div>
</div>
"""

JS_CONTROLLER = """
// === KEY DISCOVERIES CONTROLLER (SIGNAL / ENGINEER / FORENSICS) ===
function setKeyDiscoveriesMode(mode) {
    document.querySelectorAll('.kd-mode-btn').forEach(b => b.classList.remove('active'));
    document.body.classList.remove('kd-mode-engineer', 'kd-mode-forensics');
    
    const btn = document.getElementById('kd-btn-' + mode);
    if (btn) btn.classList.add('active');
    
    if (mode === 'engineer') {
        document.body.classList.add('kd-mode-engineer');
    } else if (mode === 'forensics') {
        document.body.classList.add('kd-mode-forensics');
    }
}

function focusKeyDiscovery(id) {
    const card = document.getElementById('kd-card-' + id);
    if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.style.borderColor = '#38bdf8';
        card.style.boxShadow = '0 0 25px rgba(56, 189, 248, 0.4)';
        setTimeout(() => {
            card.style.borderColor = '';
            card.style.boxShadow = '';
        }, 1500);
    }
}

// Deep Detail Modal Handler
const KD_DETAILS_STORE = {
    1: {
        title: "Fabric Exposure Fingerprint",
        eyebrow: "FINDING #1 &middot; TOPOLOGY-DEPENDENT NETWORK SENSITIVITY",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Cross-node tensor parallelism (TP16/PP1) suffers catastrophic TTFT degradation (+276.7% at 1M, +383.7% at 128K) when network bandwidth drops to 20G, because its AllReduce collective is directly serialized across the VPC bridge. Conversely, pipeline parallelism (TP4/PP4) exhibits only a +3.9% TTFT increase, because cross-node traffic is restricted to point-to-point Send/Recv transfers overlapping with computation.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Configuration</th><th>128K Context (&Delta;%)</th><th>512K Context (&Delta;%)</th><th>1M Context (&Delta;%)</th><th>Evidence Status</th></tr></thead>
                <tbody>
                    <tr><td>TP4 / PP2</td><td>+8.01% (+0.21s)</td><td>+2.37% (+0.43s)</td><td>+1.14% (+0.60s)</td><td>MEASURED (EV-085)</td></tr>
                    <tr><td>TP8 / PP2</td><td>+0.81% (+0.02s)</td><td>-0.19% (-0.03s)</td><td>-0.10% (-0.03s)</td><td>MEASURED (EV-086)</td></tr>
                    <tr><td>TP4 / PP4</td><td>+14.67% (+0.25s)</td><td>+8.93% (+0.91s)</td><td>+3.91% (+1.12s)</td><td>MEASURED (EV-087)</td></tr>
                    <tr><td>TP16 / PP1</td><td style="color:#f87171;font-weight:700">+383.66% (+24.63s)</td><td style="color:#f87171;font-weight:700">+333.01% (+98.65s)</td><td style="color:#f87171;font-weight:700">+276.69% (+188.69s)</td><td>MEASURED (EV-016)</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Communication Exposure Derivation:</b><br>
                For TP16/PP1, the volume of data exchanged over the network per token is given by:<br>
                <code>V_AllReduce = 2 &times; (TP - 1) / TP &times; B &times; H &times; L &times; sizeof(dtype)</code><br>
                Across 27 layers with H=2304 and BF16, each prefill token transfers ~237.6 KB over the VPC. At 1M context, this equals ~237.6 GB of network AllReduce traffic serialized on the critical path.<br><br>
                Under configured-20G (iperf 16.48 Gb/s), transfer time alone requires:<br>
                <code>T_comm = (237.6 GB &times; 8) / 16.48 Gb/s &approx; 115.3 s</code><br>
                This closely matches the measured +188.69s degradation when combined with collective synchronization overhead.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Profiler Evidence (PR-004 vs PR-005):</b><br>
                - <b>PR-004 (TP16/PP1 128K):</b> NCCL AllReduce accounts for <b>76.2%</b> of total aggregate GPU kernel work (all-rank mean: 77.6%).<br>
                - <b>PR-005 (TP4/PP4 128K):</b> Inter-node P2P SendRecv accounts for only <b>8.3%</b> of total GPU kernel work; intra-node TP AllReduce (local PCIe) is 40.0%.<br>
                <b>Conclusion:</b> PP4 shields the scale-out fabric by substituting heavy AllReduce collectives with lightweight P2P boundaries.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleout_matrix/vllm_scaleout_network_matrix/tp16_pp1_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp16_pp1_dist_1m_c1_capped_20g.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_capped_20g.json<br>
                hardware_processed/iperf/iperf_summary.json<br>
                hardware_processed/distributed_profiles/tp16_pp1_128k/PROFILE_VALIDATION.json
            </div>
        `
    },
    2: {
        title: "Concurrency Value Destruction",
        eyebrow: "FINDING #2 &middot; WORKLOAD ADMISSION & QUEUE COLLAPSE",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> While 8K context benefits strongly from concurrency (+120.8% throughput from c1&rarr;c4), long-context concurrency completely collapses in efficiency. At 1M context, increasing concurrency from c1 to c4 increases output throughput by only <b>+1.52%</b> while inflating TTFT by <b>2.48&times;</b>, TPOT by <b>26.15&times;</b>, and queue time from 0s to <b>134.43s</b>.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>TPS Gain (c1&rarr;c4)</th><th>TTFT Inflation</th><th>TPOT Inflation</th><th>c4 Queue Time</th></tr></thead>
                <tbody>
                    <tr><td>8K Context</td><td style="color:#4ade80;font-weight:700">+120.82%</td><td>2.74&times;</td><td>1.63&times;</td><td>0.027 s</td></tr>
                    <tr><td>128K Context</td><td>+10.27%</td><td>2.28&times;</td><td>12.96&times;</td><td>5.11 s</td></tr>
                    <tr><td>512K Context</td><td>+2.19%</td><td>2.74&times;</td><td>57.36&times;</td><td>53.66 s</td></tr>
                    <tr><td>1M Context</td><td style="color:#f87171;font-weight:700">+1.52%</td><td>2.48&times;</td><td>26.15&times;</td><td style="color:#f87171;font-weight:700">134.43 s</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Queue-Accounting Mathematical Closure:</b><br>
                Queue time accounts for almost 100% of the additional TTFT observed under concurrency:<br>
                <code>Closure = Queue_Time / (TTFT_cn - TTFT_c1)</code><br>
                - At c2: Queue = 44.340s, &Delta;TTFT = 45.979s &rarr; <b>96.4% closure</b><br>
                - At c4: Queue = 134.428s, &Delta;TTFT = 137.873s &rarr; <b>97.5% closure</b><br>
                <b>Replication:</b> Independent validation on TP8/PP1 confirmed 95.7% (c2) and 97.2% (c4) queue closure. Preemptions remained zero across all runs.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Mechanism:</b> Pre-fill chunk serialization causes subsequent incoming requests to wait behind active GPU chunks, stalling the engine scheduler while KV cache memory remains underutilized (peak KV was only 15.51% at c4). Memory fit does not guarantee operational throughput.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleup_matrix/vllm_scaleup_concurrency_matrix/tp4_1m_c1.json<br>
                scaleup_matrix/vllm_scaleup_concurrency_matrix/tp4_1m_c2.json<br>
                scaleup_matrix/vllm_scaleup_concurrency_matrix/tp4_1m_c4.json<br>
                scaleup_matrix/vllm_scaleup_concurrency_matrix/tp8_1m_c1.json<br>
                scaleup_matrix/vllm_scaleup_concurrency_matrix/tp8_1m_c4.json
            </div>
        `
    },
    3: {
        title: "Long-Context Resource-Pressure Shift",
        eyebrow: "FINDING #3 &middot; MATCHED DISTRIBUTED PROFILER SCALING",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Profile scaling between matched 128K and 512K prefill profiles demonstrates that the primary optimization bottleneck shifts with context length. While GEMM, MoE, and KDA scale linearly with sequence length (exponents ~0.96&ndash;1.20), FlashAttention accelerates quadratically (~15.7&times; growth, exponent 1.99), expanding from 22.8% to 44.8% of aggregate GPU kernel work.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Kernel Category</th><th>128K Share (PR-005)</th><th>512K Share (PR-007)</th><th>Relative Growth</th><th>Fitted Exponent</th></tr></thead>
                <tbody>
                    <tr><td>FlashAttention (O(N&sup2;))</td><td>22.8%</td><td>44.8%</td><td style="color:#f87171;font-weight:700">~15.7&times;</td><td>~1.99</td></tr>
                    <tr><td>GEMM Family</td><td>8.5%</td><td>5.1%</td><td>~5.25&times;</td><td>~1.20</td></tr>
                    <tr><td>KDA Recurrent State</td><td>2.7%</td><td>2.7%</td><td>~3.9&times;</td><td>~0.99</td></tr>
                    <tr><td>Fused MoE Experts</td><td>13.2%</td><td>6.2%</td><td>~3.8&times;</td><td>~0.96</td></tr>
                    <tr><td>Intra-Node TP AllReduce</td><td>40.0%</td><td>35.6%</td><td>~3.5&times;</td><td>~0.90</td></tr>
                    <tr><td>Inter-Node P2P SendRecv</td><td>8.3%</td><td>5.2%</td><td>~2.18&times;</td><td>~0.56</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Scaling Exponent Derivation:</b><br>
                Sequence length increased by 4.0&times; (131,328 &rarr; 524,544 tokens).<br>
                <code>Growth = Factor^Exponent &rArr; Exponent = ln(Growth) / ln(4.0)</code><br>
                - FlashAttention: <code>ln(15.7) / ln(4) = 2.75 / 1.386 &approx; 1.99</code> (Quadratic shift)<br>
                - MoE: <code>ln(3.8) / ln(4) = 1.335 / 1.386 &approx; 0.96</code> (Linear sequence dependence)
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Profiler Artifact Registry:</b><br>
                - <b>PR-005:</b> TP4/PP4 128K Prefill (Stage 0, Rank 0), Duration: 1710.2 ms, Artifact: <code>distributed_profiles/tp4_pp4_128k/PROFILE_VALIDATION.json</code><br>
                - <b>PR-007:</b> TP4/PP4 512K Prefill (Stage 0, Rank 0), Duration: 14782.3 ms, Artifact: <code>long_prefill_512k/PROFILE_VALIDATION.json</code>
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/PROFILE_VALIDATION.json<br>
                results_V8_runs(3)/hardware_processed/distributed_profiles/tp4_pp4_128k/PROFILE_VALIDATION.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_128k_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_512k_c1_native.json
            </div>
        `
    },
    4: {
        title: "Prefix Reuse Changes the Curve",
        eyebrow: "FINDING #4 &middot; WORKLOAD REGIME SHIFT",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Repeated-prefix traffic changes latency scaling from quadratic (O(N&sup2;)) to near-constant (O(1)). At 1M context, repeat-hit requests complete prefill in <b>2.614s</b> compared to <b>94.227s</b> for first/cold requests (&approx;<b>36.0&times; speedup</b>).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>Cold TTFT</th><th>Repeat-Hit Median</th><th>Speedup</th><th>Runtime Prefix Counters</th></tr></thead>
                <tbody>
                    <tr><td>128K Context</td><td>4.8965 s</td><td>0.3307 s</td><td style="color:#4ade80;font-weight:700">~14.8&times;</td><td>87.33% hit ratio</td></tr>
                    <tr><td>512K Context</td><td>32.5762 s</td><td>1.1679 s</td><td style="color:#4ade80;font-weight:700">~27.9&times;</td><td>49.98% hit ratio</td></tr>
                    <tr><td>1M Context</td><td>94.2272 s</td><td>2.6140 s</td><td style="color:#4ade80;font-weight:800">~36.0&times;</td><td>49.97% hit ratio</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Derivation:</b> Prefix caching bypasses attention computation for previously ingested prompt blocks. The repeat prefill latency reflects only the un-cached suffix (here fixed to ~500 tokens) plus KV pointer block table lookup overhead.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Execution Behavior:</b> KV blocks remain in GPU high-bandwidth memory (HBM). Radix tree traversal takes &lt;1ms; prefill computation scales only with the novel token delta.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleup_prefix_matrix/tp4_prefix128k.json (EV-053)<br>
                scaleup_prefix_matrix/tp4_prefix512k.json (EV-054)<br>
                scaleup_prefix_matrix/tp4_prefix1m.json (EV-075)
            </div>
        `
    },
    5: {
        title: "Parallelism Directional Elasticity + Frontier",
        eyebrow: "FINDING #5 &middot; PARETO SCALING FRONTIER",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Parallelism elasticity flips sign with context length. While TP8 is slower than TP4 at short contexts (8K: +18.5% TTFT penalty) due to cross-socket AllReduce overhead, it becomes faster at long contexts (1M: -19.9% TTFT improvement) as compute scaling overtakes communication.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>TP4/PP1 TTFT</th><th>TP8/PP1 TTFT</th><th>TP8 Latency Effect</th><th>Resource Elasticity</th></tr></thead>
                <tbody>
                    <tr><td>8K Context</td><td>0.222 s</td><td>0.263 s</td><td style="color:#f87171">+18.5% (Slower)</td><td>Negative Elasticity</td></tr>
                    <tr><td>128K Context</td><td>4.532 s</td><td>4.810 s</td><td style="color:#f87171">+6.1% (Slower)</td><td>Near-Zero Elasticity</td></tr>
                    <tr><td>512K Context</td><td>31.916 s</td><td>28.089 s</td><td style="color:#4ade80">-12.0% (Faster)</td><td>Positive Elasticity</td></tr>
                    <tr><td>1M Context</td><td>93.248 s</td><td>74.688 s</td><td style="color:#4ade80">-19.9% (Faster)</td><td>High Positive Elasticity</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Pipeline Frontier at 1M (Holding TP=4, Scaling PP):</b><br>
                - TP4/PP1 (4 GPUs): TTFT = 93.248s &rarr; <b>373.0 GPU-s/req</b><br>
                - TP4/PP2 (8 GPUs): TTFT = 52.526s &rarr; <b>420.2 GPU-s/req</b> (+12.7% resource footprint)<br>
                - TP4/PP4 (16 GPUs): TTFT = 28.568s &rarr; <b>457.1 GPU-s/req</b> (+22.5% resource footprint)<br>
                PP provides smooth latency reduction (3.26&times; speedup) with modest +22.5% resource overhead.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Trade-off:</b> TP scales within node; PP scales across nodes. Choosing topology depends on whether the workload optimizes for minimal turn latency (PP4) or maximal cluster occupancy efficiency (PP1).
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp1_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp2_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_native.json
            </div>
        `
    },
    6: {
        title: "Prompt-Token Admission Fingerprint",
        eyebrow: "FINDING #6 &middot; OPEN-LOOP PREFILL CAPACITY",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Request throughput varies dramatically by prompt length (~18.2&times; gap between 8K and 128K), but when normalized by input tokens, achieved throughput collapses to nearly the same processing rate (~27.5K vs ~24.2K input tok/s, a mere ~1.14&times; gap).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>Offered Load Sweep</th><th>Median Achieved Req/s</th><th>Input Token Rate</th><th>Ratio vs 8K</th></tr></thead>
                <tbody>
                    <tr><td>8K Context</td><td>1.00&times;, 1.10&times;, 1.25&times;</td><td style="color:#f87171;font-weight:700">3.3586 req/s</td><td style="color:#4ade80;font-weight:700">27.51K tok/s</td><td>1.00&times;</td></tr>
                    <tr><td>128K Context</td><td>1.00&times;, 1.10&times;, 1.25&times;</td><td style="color:#f87171;font-weight:700">0.1846 req/s</td><td style="color:#4ade80;font-weight:700">24.19K tok/s</td><td>1.14&times;</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Normalization Formula:</b><br>
                <code>Input_Token_Rate = Achieved_Request_Rate &times; Prompt_Tokens</code><br>
                - 8K: <code>3.3586 &times; 8,192 &approx; 27,513 tokens/s</code><br>
                - 128K: <code>0.1846 &times; 131,072 &approx; 24,192 tokens/s</code><br>
                The ~18.2&times; request rate gap is primarily sequence length volume; admission control must track prompt token budgets.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Evaluated under open-loop Poisson arrival traffic. High-load stress demonstrates that engine prefill pipelines saturate on cumulative token volume.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                openloop_matrix/tp4_8k_load_sweep.json<br>
                openloop_matrix/tp4_128k_load_sweep.json
            </div>
        `
    },
    7: {
        title: "Runtime-Knob Derivative Fingerprint",
        eyebrow: "FINDING #7 &middot; CHUNK SIZE VS MAX_NUM_SEQS",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Tuning max_num_seqs between 4, 8, and 16 produces less than 0.05% change in TTFT (&lt;110ms on a 232s turn) because concurrency is constrained by memory and prompt chunking. In contrast, chunk size tuning (4K&rarr;16K) delivers a steep <b>27.1% TTFT reduction</b> (122.0s &rarr; 88.9s).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Runtime Knob</th><th>Evaluated Values</th><th>Observed TTFT Delta</th><th>Leverage / Derivative</th></tr></thead>
                <tbody>
                    <tr><td>Chunk Size (1M c1)</td><td>4K &rarr; 8K &rarr; 16K</td><td>122.049s &rarr; 93.277s &rarr; 88.951s</td><td style="color:#4ade80;font-weight:700">High (-27.1% latency)</td></tr>
                    <tr><td>max_num_seqs (1M c4)</td><td>4 &rarr; 8 &rarr; 16</td><td>232.342s &rarr; 232.364s &rarr; 232.250s</td><td style="color:#94a3b8">Non-binding (0.049% spread)</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Telemetry Confirmation:</b> Server engine telemetry confirms <code>peak_running=2</code> and <code>peak_waiting=3</code> during the 1M c4 benchmark. The ceiling of 16 was never activated; chunk size, by contrast, directly scales GEMM arithmetic intensity on the HBM bus.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Larger chunk size amortizes kernel launch overhead and improves cuBLAS GEMM tensor core utilization during prefill chunk execution.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleup_matrix/vllm_scaleup_chunk_matrix/tp4_1m_chunk4k.json<br>
                scaleup_matrix/vllm_scaleup_chunk_matrix/tp4_1m_chunk8k.json<br>
                scaleup_matrix/vllm_scaleup_chunk_matrix/tp4_1m_chunk16k.json<br>
                scaleup_matrix/vllm_scaleup_scheduler_matrix/tp4_1m_seqs4.json<br>
                scaleup_matrix/vllm_scaleup_scheduler_matrix/tp4_1m_seqs16.json
            </div>
        `
    },
    8: {
        title: "TP Decode Evidence Chain",
        eyebrow: "FINDING #8 &middot; COLLECTIVE CROSS-SOCKET OVERHEAD",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Wider tensor parallelism hurts single-stream decode turns on dual-socket architectures. At 8K decode, TP8 incurs a <b>+41.9% TPOT penalty</b> (6.350ms vs 4.475ms on TP4). The cause is directly traced across four measurement layers to cross-NUMA PCIe bridge AllReduce latency.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Layer</th><th>Tool / Instrument</th><th>TP4 / PP1</th><th>TP8 / PP1</th><th>Observation</th></tr></thead>
                <tbody>
                    <tr><td>1. Microbench</td><td>NCCL test</td><td>~19 &mu;s</td><td>~37 &mu;s</td><td>~1.9&ndash;2.2&times; latency over PCIe bridge</td></tr>
                    <tr><td>2. Profiler</td><td>PyTorch Profiler</td><td>251.529 ms</td><td>583.866 ms</td><td>+332.3ms in nccl:all_reduce (7040 calls)</td></tr>
                    <tr><td>3. Nsight</td><td>CUDA GPU Kernels</td><td>Intra-socket bus</td><td>Cross-socket bridge</td><td>AllReduce is dominant decode category</td></tr>
                    <tr><td>4. E2E Metric</td><td>vLLM Serving</td><td>4.475 ms TPOT</td><td>6.350 ms TPOT</td><td>+41.9% interactive turn latency penalty</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Invocation Analysis:</b> Both TP4 and TP8 execute precisely 7,040 AllReduce calls per 8K decode run. Average latency per collective increases from 35.7&mu;s to 82.9&mu;s on TP8 due to PCIe socket traversal.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                - <b>PR-002:</b> TP4 Decode 8K, Self CUDA Time = 251.5 ms (86.3% of kernel work)<br>
                - <b>PR-003:</b> TP8 Decode 8K, Self CUDA Time = 583.9 ms (89.1% of kernel work)<br>
                Artifacts: <code>results_V8_runs(3)/hardware_processed/nsight_tp4_decode/</code> and <code>nsight_tp8_decode/</code>
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                hardware_processed/nsight_tp4_decode/cuda_gpu_kern_sum.csv (PR-002)<br>
                hardware_processed/nsight_tp8_decode/cuda_gpu_kern_sum.csv (PR-003)<br>
                scaleup_matrix/tp4_8k_decode.json (EV-009)<br>
                scaleup_matrix/tp8_8k_decode.json (EV-013)
            </div>
        `
    },
    9: {
        title: "Busy GPU != Efficient Serving",
        eyebrow: "FINDING #9 &middot; OBSERVABILITY & SM CYCLE DIVERGENCE",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> GPU SM utilization is fundamentally misleading as a sizing metric. At 1M context, cross-node TP16/PP1 reports <b>80.6%</b> GPU utilization while executing prefill in 68.197s. TP4/PP4 reports only <b>62.8%</b> GPU utilization yet finishes prefill in <b>28.568s</b> (&approx;<b>2.39&times; faster</b>).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>TP4/PP4 SM Util</th><th>TP4/PP4 TTFT</th><th>TP16/PP1 SM Util</th><th>TP16/PP1 TTFT</th><th>Efficiency Winner</th></tr></thead>
                <tbody>
                    <tr><td>128K Context</td><td>35.2%</td><td>1.710 s</td><td>63.2%</td><td>6.420 s</td><td style="color:#4ade80;font-weight:700">TP4/PP4 (3.75&times; faster)</td></tr>
                    <tr><td>512K Context</td><td>55.3%</td><td>10.222 s</td><td>67.8%</td><td>29.624 s</td><td style="color:#4ade80;font-weight:700">TP4/PP4 (2.90&times; faster)</td></tr>
                    <tr><td>1M Context</td><td>62.8%</td><td>28.568 s</td><td>80.6%</td><td>68.197 s</td><td style="color:#4ade80;font-weight:700">TP4/PP4 (2.39&times; faster)</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Mechanism:</b> GPU utilization telemetry measures whether SM warps are scheduled. In distributed TP16, warps spend extensive cycles polling and waiting in NCCL AllReduce synchronization barriers, keeping the SMs registered as 'busy' without advancing token computation.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Nsight profiling proves that &gt;76% of TP16 execution time is collective network communication. Sizing workloads by GPU % alone would erroneously favor the slower configuration.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp16_pp1_dist_1m_c1_native.json
            </div>
        `
    },
    10: {
        title: "KV Headroom != VRAM Headroom",
        eyebrow: "FINDING #10 &middot; MEMORY DILUTION TELEMETRY",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Pipeline parallelism dilutes the engine's reported KV cache utilization percentage, giving the false illusion of vast memory headroom. At 1M context, reported peak KV drops from 12.29% (PP1) to 5.91% (PP2) to <b>2.75% (PP4)</b>, yet peak physical GPU VRAM allocation remains flat and saturated at <b>~88.83 GiB</b> out of ~95.59 GiB usable capacity.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Topology (1M Context)</th><th>Reported Peak KV %</th><th>Global Model KV Check</th><th>Peak Physical VRAM</th><th>Apparent vs Real Headroom</th></tr></thead>
                <tbody>
                    <tr><td>TP4 / PP1</td><td>12.29%</td><td>12.29%</td><td>88.39 GiB</td><td>Matches single-device reality</td></tr>
                    <tr><td>TP4 / PP2</td><td>5.91%</td><td>~11.82% (2 &times; 5.91%)</td><td>88.69 GiB</td><td>KV diluted across 2 stages</td></tr>
                    <tr><td>TP4 / PP4</td><td style="color:#38bdf8;font-weight:700">2.75%</td><td>~11.00% (4 &times; 2.75%)</td><td style="color:#fde047;font-weight:700">88.83 GiB</td><td>Appears 97.2% free, but VRAM is 88.8G!</td></tr>
                    <tr><td>TP16 / PP1</td><td>12.13%</td><td>12.13%</td><td>86.71 GiB</td><td>Slightly lower static buffer</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Mathematical Proof:</b> Pipeline stages shard layers across GPUs (PP4 divides 27 layers &approx; 6.75 layers/stage). Each stage holds only 1/4th of the active KV blocks. However, model weights, CUDA runtime, and activation buffers maintain total per-GPU footprint at ~88.4&ndash;88.8 GiB.<br>
                Raw device capacity reported in preflight: <code>97,887 MiB &approx; 95.59 GiB</code> per GPU.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Independent replication on TP8 confirms the pattern: TP8/PP1 12.18% KV &rarr; TP8/PP2 5.88% KV while memory remains 88.7 GiB.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_native.json (EV-084)<br>
                final_validation/STATIC_VALIDATION.json<br>
                hardware_processed/memory_telemetry.json
            </div>
        `
    }
};

function openKeyDiscoveryDetail(id) {
    const data = KD_DETAILS_STORE[id];
    if (!data) {
        window.openEvidencePopup('EV-084');
        return;
    }
    document.getElementById('kd-modal-eyebrow').innerHTML = data.eyebrow;
    document.getElementById('kd-modal-title').innerHTML = data.title;
    window.currentKdDetail = data;
    switchKdModalTab('findings');
    document.getElementById('kd-deep-modal-backdrop').style.display = 'block';
    document.getElementById('kd-deep-modal').style.display = 'flex';
}

function closeKeyDiscoveryDetail() {
    document.getElementById('kd-deep-modal-backdrop').style.display = 'none';
    document.getElementById('kd-deep-modal').style.display = 'none';
}

function switchKdModalTab(tab) {
    document.querySelectorAll('.kd-modal-tab-btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById('kd-mtab-btn-' + tab);
    if (btn) btn.classList.add('active');
    
    if (window.currentKdDetail) {
        document.getElementById('kd-modal-body').innerHTML = window.currentKdDetail[tab] || '<p>Detailed documentation in evidence drawer.</p>';
    }
}
"""

for target in files:
    print(f"Applying Key Discoveries tab to {target}...")
    with open(target, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Add CSS before </head> or </style>
    if "/* === KEY DISCOVERIES TAB STYLING === */" not in html:
        style_idx = html.find("</style>")
        if style_idx != -1:
            html = html[:style_idx] + "\n" + CSS_CODE + "\n" + html[style_idx:]
            print(f"  Injected CSS into {target}")

    # 2. Add Tab Button into <div class="tabs">
    tab_btn = '<button class="tab" data-tab="keydiscoveries">\u2728 Key Discoveries</button>'
    if 'data-tab="keydiscoveries"' not in html:
        kf_btn = '<button class="tab" data-tab="keyfinds">'
        idx_kf = html.find(kf_btn)
        if idx_kf != -1:
            idx_btn_end = html.find('</button>', idx_kf) + len('</button>')
            html = html[:idx_btn_end] + "\n" + tab_btn + html[idx_btn_end:]
            print(f"  Injected tab button into {target}")

    # 3. Add Tab Page Section before <section class="tabpage" id="scaleup">
    if 'id="keydiscoveries"' not in html:
        scaleup_sec = '<section class="tabpage" id="scaleup">'
        idx_scaleup = html.find(scaleup_sec)
        if idx_scaleup != -1:
            html = html[:idx_scaleup] + TAB_HTML + "\n\n" + html[idx_scaleup:]
            print(f"  Injected tabpage section into {target}")

    # 4. Add JS Controller before </body>
    if 'const KD_DETAILS_STORE' not in html:
        body_end = html.find('</body>')
        if body_end != -1:
            html = html[:body_end] + "\n<script>\n" + JS_CONTROLLER + "\n</script>\n" + html[body_end:]
            print(f"  Injected JS Controller into {target}")

    with open(target, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved {target} successfully.\n")

print("All 4 targets updated with Key Discoveries Tab!")
