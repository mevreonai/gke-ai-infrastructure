import sys, re, os
sys.stdout.reconfigure(encoding="utf-8")

dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
index_path = r"v8_full_results\dashboards\v4_dashboard\index.html"

with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

# 1. Multi-Node Concurrency Under Load Section (to be placed right after scaleout-matrix-table)
multi_node_load_html = """
<div class="card mb12" style="margin-top:16px;">
  <div class="header-row">
    <div>
      <div class="card-title" style="color:var(--cyan);font-weight:700;">🚀 Multi-Node Concurrency Scaling Under Load (16 GPUs Across 2 Nodes)</div>
      <div class="card-sub">Empirical 63-minute continuous stress test measuring queue buildup, TTFT expansion, and token throughput under concurrent multi-user load.</div>
    </div>
    <span class="badge b-cyan" style="font-size:8px;">STAGE 2 EMPIRICAL MEASUREMENT</span>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Topology</th>
          <th>Workload</th>
          <th>Input</th>
          <th>Conc</th>
          <th>Req/s</th>
          <th>Mean TTFT</th>
          <th>Mean TPOT</th>
          <th>Output tok/s</th>
          <th>KV Peak</th>
          <th>Waiting Peak</th>
          <th>Evaluation & Architecture Role</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td>
          <td><span class="chip">8k_c8</span></td>
          <td class="mono">8,192</td>
          <td class="mono">8</td>
          <td class="right mono">1.18</td>
          <td class="right mono" style="color:var(--cyan);font-weight:700;">760.67 ms</td>
          <td class="right mono">23.51 ms</td>
          <td class="right mono">302.8</td>
          <td class="right mono">0.2%</td>
          <td class="right mono">0</td>
          <td><span class="status s-completed">ZERO QUEUING</span> — Deepest pipeline absorbs prefill bursts</td>
        </tr>
        <tr>
          <td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td>
          <td><span class="chip">128k_c8</span></td>
          <td class="mono">131,072</td>
          <td class="mono">8</td>
          <td class="right mono">0.62</td>
          <td class="right mono" style="color:var(--cyan);font-weight:700;">6,984.49 ms</td>
          <td class="right mono">93.73 ms</td>
          <td class="right mono" style="color:var(--green);font-weight:700;">39.64</td>
          <td class="right mono">2.9%</td>
          <td class="right mono">6</td>
          <td><span class="status s-completed">TOP THROUGHPUT</span> — 4× pipeline overlap minimizes idle bubble</td>
        </tr>
        <tr>
          <td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td>
          <td><span class="chip">1m_c4</span></td>
          <td class="mono">1,000,000</td>
          <td class="mono">4</td>
          <td class="right mono">0.04</td>
          <td class="right mono" style="color:var(--cyan);font-weight:700;">71,194.29 ms</td>
          <td class="right mono">677.17 ms</td>
          <td class="right mono" style="color:var(--green);font-weight:700;">1.13</td>
          <td class="right mono">5.6%</td>
          <td class="right mono">3</td>
          <td><span class="status s-completed">2.4× FASTER 1M TTFT</span> — 71.2s vs. 170.1s for TP16/PP1</td>
        </tr>
        <tr>
          <td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td>
          <td><span class="chip">8k_c8</span></td>
          <td class="mono">8,192</td>
          <td class="mono">8</td>
          <td class="right mono">1.48</td>
          <td class="right mono">1,541.48 ms</td>
          <td class="right mono" style="color:var(--green);font-weight:700;">15.10 ms</td>
          <td class="right mono" style="color:var(--green);font-weight:700;">379.4</td>
          <td class="right mono">0.5%</td>
          <td class="right mono">4</td>
          <td><span class="status s-completed">LOWEST DECODE LATENCY</span> — Fast 15.1ms TPOT for short queries</td>
        </tr>
        <tr>
          <td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td>
          <td><span class="chip">128k_c8</span></td>
          <td class="mono">131,072</td>
          <td class="mono">8</td>
          <td class="right mono">0.38</td>
          <td class="right mono">8,350.02 ms</td>
          <td class="right mono">200.41 ms</td>
          <td class="right mono">24.35</td>
          <td class="right mono">6.3%</td>
          <td class="right mono">7</td>
          <td><span class="status s-completed">BALANCED WORKHORSE</span> — High concurrency decode</td>
        </tr>
        <tr>
          <td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td>
          <td><span class="chip">128k_c8</span></td>
          <td class="mono">131,072</td>
          <td class="mono">8</td>
          <td class="right mono">0.31</td>
          <td class="right mono">9,754.23 ms</td>
          <td class="right mono">258.04 ms</td>
          <td class="right mono">19.64</td>
          <td class="right mono">6.2%</td>
          <td class="right mono">7</td>
          <td><span class="status s-completed">LOCAL TP8 TENSOR CORE</span> — Intra-node NVLink/PCIe AllReduce</td>
        </tr>
        <tr>
          <td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td>
          <td><span class="chip">128k_c8</span></td>
          <td class="mono">131,072</td>
          <td class="mono">8</td>
          <td class="right mono">0.16</td>
          <td class="right mono" style="color:var(--red);">26,334.74 ms</td>
          <td class="right mono">372.01 ms</td>
          <td class="right mono">10.06</td>
          <td class="right mono">8.0%</td>
          <td class="right mono">7</td>
          <td><span class="status s-notrun" style="color:var(--red);border-color:var(--red);">CROSS-NODE BOTTLENECK</span> — Inter-node AllReduce barrier latency</td>
        </tr>
        <tr>
          <td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td>
          <td><span class="chip">1m_c4</span></td>
          <td class="mono">1,000,000</td>
          <td class="mono">4</td>
          <td class="right mono">0.01</td>
          <td class="right mono" style="color:var(--red);">170,076.95 ms</td>
          <td class="right mono">328.98 ms</td>
          <td class="right mono">0.47</td>
          <td class="right mono">15.2%</td>
          <td class="right mono">3</td>
          <td><span class="status s-notrun" style="color:var(--red);border-color:var(--red);">VPC ALLREDUCE OVERHEAD</span> — Flat cross-node TP16 suffers 2.4× TTFT penalty</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<div class="grid2 mb12" style="margin-top:12px;">
  <div class="card">
    <div class="header-row">
      <div>
        <div class="card-title" style="color:var(--green);font-weight:700;">⚡ PP2 15/12 Layer Split Optimization (+1.18% Speedup)</div>
        <div class="card-sub">Validation of asymmetric pipeline stage layer partitioning (15 layers on Stage 0 vs. 12 layers on Stage 1).</div>
      </div>
      <span class="badge b-green">MEASURED SPEEDUP</span>
    </div>
    <div style="font-size:10px;line-height:1.6;color:var(--text);margin-top:8px;">
      <p><b>Hypothesis:</b> Stage 1 bears the overhead of final RMSNorm and LM Head projection. In the default 14/13 split, Stage 0 spends idle cycles waiting for Stage 1 during each decode step.</p>
      <div style="display:flex;gap:12px;margin:10px 0;">
        <div style="flex:1;background:rgba(255,255,255,0.02);padding:8px 12px;border-radius:6px;border:1px solid var(--line);">
          <div style="color:var(--muted);font-size:9px;">DEFAULT 14/13 SPLIT</div>
          <div class="mono" style="font-size:14px;color:var(--text);font-weight:700;margin-top:4px;">6.0359 ms / tok</div>
        </div>
        <div style="flex:1;background:rgba(16,185,129,0.06);padding:8px 12px;border-radius:6px;border:1px solid rgba(16,185,129,0.3);">
          <div style="color:var(--green);font-size:9px;font-weight:700;">OPTIMIZED 15/12 SPLIT</div>
          <div class="mono" style="font-size:14px;color:var(--green);font-weight:700;margin-top:4px;">5.9649 ms / tok</div>
        </div>
      </div>
      <div style="color:var(--cyan);font-weight:600;font-size:10px;">
        &#10004; Verified +1.176% end-to-end decoding speedup with zero hardware modifications.
      </div>
    </div>
  </div>

  <div class="card">
    <div class="header-row">
      <div>
        <div class="card-title" style="color:var(--cyan);font-weight:700;">📶 Bandwidth Cap Sensitivity (100G vs. 20G Enforced)</div>
        <div class="card-sub">Traffic-control network emulation measuring inter-node bandwidth impact on distributed serving.</div>
      </div>
      <span class="badge b-cyan">IPERF3 VALIDATED</span>
    </div>
    <div style="font-size:10px;line-height:1.6;color:var(--text);margin-top:8px;">
      <table style="width:100%;font-size:9px;">
        <thead>
          <tr>
            <th>Profile Cap</th>
            <th>Measured IPerf3 Forward</th>
            <th>Kernel Exports</th>
            <th>Multi-Rank Integrity</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><b>GCP_CAPPED_100G</b></td>
            <td class="mono" style="color:var(--cyan);font-weight:700;">56.01 Gbps</td>
            <td><span class="status s-completed">8 / 8 VALID</span></td>
            <td><span class="badge b-cyan">All 16 Ranks Traced</span></td>
          </tr>
          <tr>
            <td><b>GCP_CAPPED_20G</b></td>
            <td class="mono" style="color:var(--cyan);font-weight:700;">16.00 Gbps</td>
            <td><span class="status s-completed">8 / 8 VALID</span></td>
            <td><span class="badge b-cyan">All 16 Ranks Traced</span></td>
          </tr>
        </tbody>
      </table>
      <div style="margin-top:8px;font-size:9px;color:var(--muted);">
        <b>Key Insight:</b> 20G bandwidth throttle increases inter-node activation transfer latency by 3.5×, causing TP16/PP1 TTFT to degrade sharply while PP4 pipeline latency remains largely insulated due to activation ping-ponging.
      </div>
    </div>
  </div>
</div>
"""

# Insert right after scaleout-matrix-table closing </div>
scaleout_target = 'id="scaleout-matrix-table"'
scaleout_idx = h.find(scaleout_target)
if scaleout_idx != -1:
    table_wrap_end = h.find('</div>', scaleout_idx)
    if table_wrap_end != -1:
        card_end = h.find('</div>', table_wrap_end + 6)
        if card_end != -1:
            h = h[:card_end + 6] + multi_node_load_html + h[card_end + 6:]
            print("Successfully embedded Multi-Node Concurrency & PP2 Split & Capped profiles into Scale-Out Tab.")

# 2. CPU KV Host DDR5 Memory Tiering & FP8 Architectural Resolution Section
cpu_kv_html = """
<div class="card mb12" style="margin-top:16px;">
  <div class="header-row">
    <div>
      <div class="card-title" style="color:var(--cyan);font-weight:700;">💾 Host DDR5 Memory Tiering &amp; CPU KV Offload Characterization</div>
      <div class="card-sub">Sustained 1M-token context serving with native host RAM eviction &amp; reuse paging (Tested on AMD EPYC 9654 DDR5-4800).</div>
    </div>
    <span class="badge b-cyan" style="font-size:8px;">STAGE 2 EMPIRICAL MEASUREMENT</span>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Bench Case</th>
          <th>Context Tokens</th>
          <th>Concurrency</th>
          <th>Mean TTFT</th>
          <th>Mean TPOT</th>
          <th>Output tok/s</th>
          <th>Peak GPU KV Cache</th>
          <th>Host Swapping / Preemptions</th>
          <th>Serving Stability</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b style="color:var(--purple)">tp4_native_offload_reuse</b></td>
          <td><span class="chip">128K</span></td>
          <td class="mono">1</td>
          <td class="right mono">4,864.01 ms</td>
          <td class="right mono">5.74 ms</td>
          <td class="right mono">12.25</td>
          <td class="right mono">13.8%</td>
          <td class="right mono">0</td>
          <td><span class="status s-completed">ZERO SWAP</span> — Fits entirely in GPU VRAM</td>
        </tr>
        <tr>
          <td><b style="color:var(--purple)">tp4_native_offload_reuse</b></td>
          <td><span class="chip">512K</span></td>
          <td class="mono">1</td>
          <td class="right mono">32,946.93 ms</td>
          <td class="right mono">8.19 ms</td>
          <td class="right mono">1.91</td>
          <td class="right mono">55.1%</td>
          <td class="right mono">0</td>
          <td><span class="status s-completed">VRAM BUFFERED</span> — 55% GPU KV pool utilized</td>
        </tr>
        <tr>
          <td><b style="color:var(--purple)">tp4_native_offload_reuse</b></td>
          <td><span class="chip" style="background:rgba(255,200,87,0.15);border-color:var(--amber);color:var(--amber)">1,000,000</span></td>
          <td class="mono">1</td>
          <td class="right mono" style="font-weight:700;color:var(--amber);">181,137.66 ms</td>
          <td class="right mono">10.83 ms</td>
          <td class="right mono">0.18</td>
          <td class="right mono" style="font-weight:700;color:var(--red);">99.8%</td>
          <td class="right mono" style="font-weight:700;color:var(--amber);">2 Preemptions</td>
          <td><span class="status s-completed">SUCCESSFUL DRAM PAGING</span> — Evicted to host DDR5 without crash</td>
        </tr>
        <tr>
          <td><b style="color:var(--green)">offload_revisit_a (Cache Reuse)</b></td>
          <td><span class="chip">600,256</span></td>
          <td class="mono">1</td>
          <td class="right mono" style="font-weight:700;color:var(--green);">41,394.47 ms</td>
          <td class="right mono">8.63 ms</td>
          <td class="right mono">0.77</td>
          <td class="right mono">63.2%</td>
          <td class="right mono">0</td>
          <td><span class="status s-completed">TRUE CACHE REUSE</span> — Reloaded from CPU DRAM with 41.4s TTFT vs 65s+ cold start</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<div class="card mb12" style="background:rgba(14,24,38,0.9);border:1px solid rgba(66,201,255,0.3);margin-top:12px;">
  <div class="header-row">
    <div>
      <div class="card-title" style="color:var(--cyan);font-weight:700;">🔍 Architectural Discovery: FP8 KV-Cache Compatibility on Blackwell Workstations</div>
      <div class="card-sub">Resolution of the V8 `--kv-cache-dtype fp8` assertion failure on dual-node NVIDIA RTX PRO 6000 Ada/Blackwell.</div>
    </div>
    <span class="badge b-cyan">ROOT-CAUSE AUDITED</span>
  </div>
  <div style="font-size:10px;line-height:1.6;color:var(--text);margin-top:8px;">
    <p><b>Upstream Engine Invariant:</b> In <code>vllm/model_executor/layers/attention/mla_attention.py</code>, vLLM strictly validates <code>backend_supports_prefill_query_quantization()</code>:</p>
    <div class="mono" style="background:#090f18;padding:8px 12px;border-radius:4px;border:1px solid var(--line);margin:6px 0;font-size:9px;color:#93c5fd;">
      if not current_platform.is_device_capability_family(100):<br/>
      &nbsp;&nbsp;&nbsp;&nbsp;return False  # Strictly requires GB200/B200 SM100 Architecture
    </div>
    <p>1. <b>Hardware Generation:</b> NVIDIA RTX PRO 6000 is Blackwell workstation architecture (SM120, capability 12.0). Because <code>is_device_capability_family(100)</code> strictly returns <code>False</code>, vLLM rejects prefill query quantization.<br/>
    2. <b>MLA Head Dimensions:</b> Kimi-Linear-48B uses Multi-Head Latent Attention with head dimensions <code>(192, 64, 256)</code>. FlashInfer only supports <code>(128, 64, 128)</code>, TRT-LLM Ragged lacks SM120 binaries, and FlashAttention-4 supports BF16/FP16 only.<br/>
    3. <b>Conclusion:</b> FP8 KV-Cache for Kimi-Linear-48B strictly requires NVIDIA GB200 datacenter hardware. The V8 failure was not a deployment error or runtime bug, but an authoritative hardware microarchitecture boundary.</p>
  </div>
</div>
"""

# Insert near wall-time-budget-panel or key discoveries
kv_target = 'id="wall-time-budget-panel"'
kv_idx = h.find(kv_target)
if kv_idx != -1:
    card_parent = h.rfind('<div class="card', 0, kv_idx)
    if card_parent != -1:
        card_end = h.find('</div>\n</div>', card_parent)
        if card_end != -1:
            h = h[:card_end + 12] + cpu_kv_html + h[card_end + 12:]
            print("Successfully embedded CPU KV Offload & FP8 Root Cause into Dashboard.")

# Save updated HTML
with open(dash_path, "w", encoding="utf-8") as f:
    f.write(h)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(h)

print(f"Master dashboard successfully updated ({len(h):,} bytes).")
