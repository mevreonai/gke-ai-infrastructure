import json
import re
from pathlib import Path

def update_dashboard():
    dash_path = Path("v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html")
    index_path = Path("v9_full_result/index.html")
    
    html = dash_path.read_text(encoding="utf-8")
    
    # 1. Update scaleoutMetricsData
    # Real empirical numbers from v9_full_result/final_validation/combined_vllm_runs.csv:
    # tp4_pp2:
    #   128K c1: ttft 8.306s, tpot 64.71ms, out_tps 7.75, req_tps 0.120, kv 0.748%
    #   512K c1: ttft 49.144s, tpot 62.69ms, out_tps 1.21, req_tps 0.020, kv 1.712%
    #   1M c1:   ttft 127.131s, tpot 56.27ms, out_tps 0.25, req_tps 0.008, kv 2.877%
    # tp8_pp2:
    #   128K c1: ttft 9.331s, tpot 86.75ms, out_tps 6.29, req_tps 0.107, kv 0.545%
    #   512K c1: ttft 52.780s, tpot 84.69ms, out_tps 1.10, req_tps 0.019, kv 1.248%
    #   1M c1:   ttft 133.636s, tpot 78.07ms, out_tps 0.24, req_tps 0.007, kv 2.097%
    # tp4_pp4: null (SERVER_START_FAILED)
    # tp16_pp1: null (CAPABILITY_BLOCKED)
    # Capped 100G & 20G for scaleout: null (NOT_RUN)
    
    real_scaleout_js = """    const scaleoutMetricsData = {
      "GCP_NATIVE": {
        "tp4_pp4": {
          "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null },
          "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null },
          "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }
        },
        "tp8_pp2": {
          "128K": { ttft: 9.33, tpot: 86.75, req_tps: 0.107, out_tps: 6.29, queue: 0.000, kv: 0.545, preemptions: 0 },
          "512K": { ttft: 52.78, tpot: 84.69, req_tps: 0.019, out_tps: 1.10, queue: 0.000, kv: 1.248, preemptions: 0 },
          "1M": { ttft: 133.64, tpot: 78.07, req_tps: 0.007, out_tps: 0.24, queue: 0.000, kv: 2.097, preemptions: 0 }
        },
        "tp4_pp2": {
          "128K": { ttft: 8.31, tpot: 64.71, req_tps: 0.120, out_tps: 7.75, queue: 0.000, kv: 0.748, preemptions: 0 },
          "512K": { ttft: 49.14, tpot: 62.69, req_tps: 0.020, out_tps: 1.21, queue: 0.000, kv: 1.712, preemptions: 0 },
          "1M": { ttft: 127.13, tpot: 56.27, req_tps: 0.008, out_tps: 0.25, queue: 0.000, kv: 2.877, preemptions: 0 }
        },
        "tp16_pp1": {
          "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null },
          "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null },
          "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }
        }
      },
      "GCP_CAPPED_100G": {
        "tp4_pp4": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } },
        "tp8_pp2": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } },
        "tp4_pp2": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } },
        "tp16_pp1": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } }
      },
      "GCP_CAPPED_20G": {
        "tp4_pp4": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } },
        "tp8_pp2": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } },
        "tp4_pp2": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } },
        "tp16_pp1": { "128K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "512K": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null }, "1M": { ttft: null, tpot: null, req_tps: null, out_tps: null, queue: null, kv: null, preemptions: null } }
      }
    };"""

    # Replace the existing scaleoutMetricsData block
    html = re.sub(
        r'const scaleoutMetricsData\s*=\s*\{.*?\n\s*\}\s*;\s*\n\s*const metricMeta',
        real_scaleout_js + '\n\n    const metricMeta',
        html,
        count=1,
        flags=re.DOTALL
    )

    # 2. Update chart_scaleout_comparison to include TP4/PP2 and TP8/PP2 empirical data
    # and update chart_scaleout_context_scaling to include TP4/PP2 line
    chart_scaleout_comp_js = """    const chartScaleoutComp = safeInitChart('chart_scaleout_comparison', {
        type: 'bar',
        data: {
            labels: ['1K', '8K', '128K', '512K', '1M'],
            datasets: [
                {
                    label: 'TP4/PP2 Scale-Out TTFT (s) [REAL]',
                    data: [0.136, 0.658, 8.306, 49.144, 127.131],
                    backgroundColor: '#38bdf8',
                    borderRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: 'TP8/PP2 Scale-Out TTFT (s) [REAL]',
                    data: [0.147, 0.735, 9.331, 52.780, 133.636],
                    backgroundColor: '#a78bfa',
                    borderRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: 'TP8/PP1 Single-Node TTFT (s) [REAL]',
                    data: [0.147, 0.933, 16.039, 81.417, 189.681],
                    backgroundColor: '#64748b',
                    borderRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: 'TP4/PP2 Dual-Node TPOT (ms)',
                    data: [65.06, 65.09, 64.71, 62.69, 56.27],
                    type: 'line',
                    borderColor: '#38bdf8',
                    borderWidth: 2,
                    pointRadius: 4,
                    yAxisID: 'y1'
                },
                {
                    label: 'TP8/PP2 Dual-Node TPOT (ms)',
                    data: [87.14, 87.14, 86.75, 84.69, 78.07],
                    type: 'line',
                    borderColor: '#ffc107',
                    borderWidth: 2,
                    pointRadius: 4,
                    yAxisID: 'y1'
                },
                {
                    label: 'TP8/PP1 Single-Node TPOT (ms)',
                    data: [37.05, 37.04, 36.83, 34.83, 28.60],
                    type: 'line',
                    borderColor: '#34d399',
                    borderWidth: 2,
                    pointRadius: 4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { type: 'linear', position: 'left', title: { display: true, text: 'TTFT (seconds)', color: '#94a3b8' }, grid: { color: '#1e293b' } },
                y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'TPOT (ms)', color: '#94a3b8' } },
                x: { title: { display: true, text: 'Context Length', color: '#94a3b8' }, grid: { color: '#1e293b' } }
            }
        }
    });"""

    html = re.sub(
        r'const chartScaleoutComp\s*=\s*safeInitChart\(\'chart_scaleout_comparison\'.*?\n\s*\}\);\n',
        chart_scaleout_comp_js + '\n',
        html,
        count=1,
        flags=re.DOTALL
    )

    chart_scaleout_ctx_js = """    const chartScaleoutCtx = safeInitChart('chart_scaleout_context_scaling', {
        type: 'line',
        data: {
            labels: ['1024', '8192', '131072', '524288', '1000000'],
            datasets: [
                {
                    label: 'TP4/PP1 Single-Node TTFT Scaling (s)',
                    data: [0.049, 0.222, 4.528, 32.012, 93.430],
                    borderColor: '#34d399',
                    backgroundColor: 'rgba(52, 211, 153, 0.1)',
                    fill: false,
                    tension: 0.2,
                    pointRadius: 5
                },
                {
                    label: 'TP4/PP2 Dual-Node Context TTFT Scaling (s)',
                    data: [0.136, 0.658, 8.306, 49.144, 127.131],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    fill: false,
                    tension: 0.2,
                    pointRadius: 5
                },
                {
                    label: 'TP8/PP2 Dual-Node Context TTFT Scaling (s)',
                    data: [0.147, 0.735, 9.331, 52.780, 133.636],
                    borderColor: '#a78bfa',
                    backgroundColor: 'rgba(167, 139, 250, 0.15)',
                    fill: true,
                    tension: 0.2,
                    pointRadius: 5
                },
                {
                    label: 'TP8/PP1 Single-Node TTFT Scaling (s)',
                    data: [0.147, 0.933, 16.039, 81.417, 189.681],
                    borderColor: '#94a3b8',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.2,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { title: { display: true, text: 'TTFT (seconds)', color: '#94a3b8' }, grid: { color: '#1e293b' } },
                x: { title: { display: true, text: 'Context Tokens', color: '#94a3b8' }, grid: { color: '#1e293b' } }
            }
        }
    });"""

    html = re.sub(
        r'const chartScaleoutCtx\s*=\s*safeInitChart\(\'chart_scaleout_context_scaling\'.*?\n\s*\}\);\n',
        chart_scaleout_ctx_js + '\n',
        html,
        count=1,
        flags=re.DOTALL
    )

    # 3. Update the scaleout banner to include tp4_pp2_dist success
    scaleout_banner_new = """    <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid #f59e0b; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px; font-weight: 800; color: #fbbf24; font-size: 14px;">
            <span>ℹ️</span> SCALE-OUT TOPOLOGY EMPIRICAL STATUS AUDIT (ZERO MOCK PROTOCOL)
        </div>
        <div style="color: #cbd5e1; font-size: 11.5px; margin-top: 6px; line-height: 1.5;">
            • <strong>tp4_pp2_dist</strong>: <span style="color:#4ade80; font-weight:700;">100% COMPLETED</span> across all 7 benchmarks (1K: 0.136s, 8K: 0.658s, 128K: 8.31s, 512K: 49.14s, 1M: 127.13s). Lowest distributed TTFT at 1M.<br>
            • <strong>tp8_pp2_dist</strong>: <span style="color:#4ade80; font-weight:700;">100% COMPLETED</span> across all 7 benchmarks (1K: 0.147s, 8K: 0.735s, 128K: 9.33s, 512K: 52.78s, 1M: 133.64s). Outperforms single-node TP8 (189.68s) by 1.42× at 1M context.<br>
            • <strong>tp4_pp4_dist</strong>: <span style="color:#f87171; font-weight:700;">SERVER_START_FAILED / CAPABILITY_BLOCKED</span> &mdash; DeepSeek V4.1 Flash layers 20&ndash;42 share compressed KV caches with layer 20. Pipelining across 4 stages places layer 20 on Stage 2 while Stage 3 owns layers 24+, throwing <code>NotImplementedError: PP splits inside a v4.1 kv-sharing group are not supported</code>.<br>
            • <strong>tp16_pp1_dist</strong>: <span style="color:#fbbf24; font-weight:700;">CAPABILITY_BLOCKED</span> &mdash; DeepSeek V4.1 Flash has 24 Engram hash heads across layers. Dividing 24 heads across 16 ranks requires non-uniform sharding, which vLLM rejects.
        </div>
    </div>"""

    html = re.sub(
        r'<div style="background: rgba\(245, 158, 11, 0\.12\);.*?</div\s*>\s*</div\s*>',
        scaleout_banner_new,
        html,
        count=1,
        flags=re.DOTALL
    )

    # 4. Replace any remaining vestigial 28.57s / TP4/PP4 references in text with the real empirical numbers
    # Specifically:
    # "TP4/PP4 TTFT moves from 28.57s to 29.68s" -> "TP4/PP2 delivers 127.13s @ 1M (Native) and TP8/PP2 delivers 133.64s"
    html = html.replace(
        "TP4/PP4 lowest TTFT @ 1M (28.57s)",
        "TP4/PP2 lowest distributed TTFT @ 1M (127.13s)"
    )
    html = html.replace(
        "TP4/PP4 TTFT moves from 28.57s to 29.68s (+3.91% degradation)",
        "TP4/PP2 delivers 127.13s and TP8/PP2 delivers 133.64s @ 1M (TP4/PP4 failed due to KV-sharing PP split)"
    )
    html = html.replace(
        "TP4/PP4 Native TTFT scales from 1.71s (128K) to 10.22s (512K) to 28.57s (1M)",
        "TP4/PP2 Native TTFT scales from 8.31s (128K) to 49.14s (512K) to 127.13s (1M)"
    )
    html = html.replace(
        "scaling pipeline stages from PP2 to PP4 on TP4 reduces TTFT from 52.53s to 28.57s",
        "scaling to TP4/PP2 achieves 127.13s @ 1M (TP4/PP4 is blocked by KV-sharing boundary)"
    )
    html = html.replace(
        "TP4/PP4 runs at only ~62.8% GPU utilization, yet completes in 28.57s",
        "TP4/PP2 completes in 127.13s while TP8/PP2 completes in 133.64s (TP4/PP4 failed on KV split)"
    )
    html = html.replace(
        "Lowest measured TTFT across all 4 tested topologies on GCP_NATIVE (28.57s @ 1M)",
        "Verified distributed TTFT: TP4/PP2 (127.13s @ 1M) and TP8/PP2 (133.64s @ 1M)"
    )
    html = html.replace(
        "TTFT 28.57s (TP4/PP4)",
        "TTFT 127.13s (TP4/PP2)"
    )
    html = html.replace(
        "TTFT drops from 52.53s to 28.57s",
        "TTFT achieves 127.13s on TP4/PP2 vs 133.64s on TP8/PP2"
    )
    html = html.replace(
        "1M TTFT: 28.57s (62.8% Util)",
        "1M TTFT: 127.13s (TP4/PP2)"
    )
    html = html.replace(
        "128K TTFT: 1.71s (35.2% Util)",
        "128K TTFT: 8.31s (TP4/PP2)"
    )
    html = html.replace(
        "28.57s → 29.68s (+1.12s)",
        "127.13s (TP4/PP2) / 133.64s (TP8/PP2)"
    )
    html = html.replace(
        "Cleanest Distributed 1M (28.57s)",
        "Verified Distributed 1M: TP4/PP2 (127.13s)"
    )
    html = html.replace(
        "TTFT 28.57s — ~35,005 input tok/s derived ingestion rate",
        "TTFT 127.13s — ~7,866 input tok/s derived ingestion rate"
    )
    html = html.replace(
        "TTFT 28.57s — ~35.0k input tok/s derived ingestion rate",
        "TTFT 127.13s — ~7.87k input tok/s derived ingestion rate"
    )
    html = html.replace(
        "28.57s",
        "127.13s"
    )
    html = html.replace(
        "68.20s",
        "BLOCKED (Divisibility)"
    )
    html = html.replace(
        "52.53s",
        "127.13s"
    )
    html = html.replace(
        "17.95s",
        "49.14s"
    )

    # Write back both files
    dash_path.write_text(html, encoding="utf-8")
    index_path.write_text(html, encoding="utf-8")
    print(f"Updated {dash_path} and {index_path} successfully ({len(html)} bytes).")

if __name__ == "__main__":
    update_dashboard()
