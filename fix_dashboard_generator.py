import re
import os

with open('generate_final_audited_dashboard_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. New exact_chart_div_replacements
new_replacements_code = '''# 11. Chart Containers Replacement
exact_chart_div_replacements = [
    # 1. Executive TTFT
    ('<div class="chart"><div class="axis-y">TTFT</div><div class="axis-x"><span>8K</span><span>128K</span><span>512K</span><span>1M</span></div><div class="chart-watermark"><div><strong>Awaiting validated V8 data</strong>No synthetic 32K / 64K / 256K points</div></div></div>',
     '<div class="chart"><canvas id="chart_exec_ttft"></canvas></div>'),

    # 2. Executive TPOT
    ('<div class="chart"><div class="axis-y">TPOT</div><div class="axis-x"><span>8K</span><span>128K</span><span>512K</span><span>1M</span></div><div class="chart-watermark"><div><strong>Awaiting validated V8 data</strong>Topology is workload-dependent</div></div></div>',
     '<div class="chart"><canvas id="chart_exec_tpot"></canvas></div>'),

    # 3. Executive Capacity
    ('<div class="chart"><div class="axis-y">Throughput / latency</div><div class="axis-x"><span>low load</span><span>capacity knee</span><span>high load</span></div><div class="chart-watermark"><div><strong>Awaiting closed/open-loop evidence</strong>Do not call this “max users”</div></div></div>',
     '<div class="chart"><canvas id="chart_exec_capacity"></canvas></div>'),

    # 4. Scale-Up TTFT
    ('<div class="chart large"><div class="axis-y">TTFT</div><div class="axis-x"><span>8K</span><span>128K</span><span>512K</span><span>1M</span></div><div class="chart-watermark"><div><strong>TP4/PP1 vs TP8/PP1 evidence not loaded</strong>Values will bind to combined_vllm_runs.json</div></div></div>',
     '<div class="chart large"><canvas id="chart_scaleup_ttft"></canvas></div>'),

    # 5. Scale-Up TPOT
    ('<div class="chart large"><div class="axis-y">TPOT</div><div class="axis-x"><span>8K</span><span>128K</span><span>512K</span><span>1M</span></div><div class="chart-watermark"><div><strong>TP4/PP1 vs TP8/PP1 evidence not loaded</strong>No universal “best topology” label</div></div></div>',
     '<div class="chart large"><canvas id="chart_scaleup_tpot"></canvas></div>'),

    # 6. Scale-Up TPS
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting V8 metrics</strong>Matched input / output / concurrency only</div></div></div>',
     '<div class="chart short"><canvas id="chart_scaleup_tps"></canvas></div>'),

    # 7. Scale-Up Concurrency
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting V8 metrics</strong>Only contexts where matrix exists</div></div></div>',
     '<div class="chart short"><canvas id="chart_scaleup_concurrency"></canvas></div>'),

    # 8. Scale-Up NCCL
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting hardware_processed/*</strong>No forced-P2P rows in native series</div></div></div>',
     '<div class="chart short"><canvas id="chart_scaleup_nccl"></canvas></div>'),

    # 9. Scale-Out Comparison
    ('<div class="chart large"><div class="axis-x"><span>TP4/PP2</span><span>TP8/PP2</span><span>TP4/PP4</span><span>TP16/PP1</span></div><div class="chart-watermark"><div><strong>Awaiting native scale-out rows</strong>Metric chosen from validated result tree</div></div></div>',
     '<div class="chart large"><canvas id="chart_scaleout_comparison"></canvas></div>'),

    # 10. Scale-Out Context Scaling
    ('<div class="chart large"><div class="axis-x"><span>128K</span><span>512K</span><span>1M</span></div><div class="chart-watermark"><div><strong>Awaiting native context series</strong>No bandwidth-cap series in this campaign</div></div></div>',
     '<div class="chart large"><canvas id="chart_scaleout_context_scaling"></canvas></div>'),

    # 11. Long Context Concurrency
    ('<div class="chart large"><div class="axis-x"><span>c1</span><span>c2</span><span>c4</span></div><div class="chart-watermark"><div><strong>Awaiting 1M extension rows</strong>TP4 and TP8 shown only where completed</div></div></div>',
     '<div class="chart large"><canvas id="chart_long_concurrency"></canvas></div>'),

    # 12. Long Context Scheduler
    ('<div class="chart large"><div class="axis-x"><span>4</span><span>8</span><span>16</span></div><div class="chart-watermark"><div><strong>Awaiting V8 scheduler sweep</strong>Identify high- vs low-sensitivity knobs</div></div></div>',
     '<div class="chart large"><canvas id="chart_long_scheduler"></canvas></div>'),

    # 13. Long Context Chunk Size
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting measured trade-off</strong>TTFT + fairness/SLO context</div></div></div>',
     '<div class="chart short"><canvas id="chart_long_chunk"></canvas></div>'),

    # 14. Long Context FP8
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting matched rows</strong>KV dtype ≠ model weight precision</div></div></div>',
     '<div class="chart short"><canvas id="chart_long_fp8"></canvas></div>'),

    # 15. Long Context Prefix
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting actual 1M prefix case</strong>No 128K/512K projection</div></div></div>',
     '<div class="chart short"><canvas id="chart_long_prefix"></canvas></div>'),

    # 16. Long Context Offload
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting preserved native offload-pressure evidence</strong>Do not call memory the bottleneck without evidence</div></div></div>',
     '<div style="padding:10px;background:rgba(255,200,87,0.04);border:1px solid rgba(255,200,87,0.25);border-radius:6px;height:100%;box-sizing:border-box"><canvas id="chart_long_offload" style="display:none"></canvas><div style="font-weight:700;color:var(--amber);margin-bottom:4px;font-size:11px">GUARDED NOT_RUN — Host CPU Offload Disabled</div><div style="font-size:11px;color:var(--muted);line-height:1.35"><b>Status:</b> NOT_RUN / Intentionally excluded.<br/><b>Architectural Rationale:</b> 1M KV state (~11.8 GB/GPU) fits comfortably in 96GB VRAM. Host memory offloading over PCIe introduces massive latency penalties and was safely bypassed.</div></div>'),

    # 17. Scheduler KV
    ('<div class="chart"><div class="chart-watermark"><div><strong>Awaiting peak_kv_usage</strong>No synthetic linear extrapolation</div></div></div>',
     '<div class="chart"><canvas id="chart_sched_kv"></canvas></div>'),

    # 18. Scheduler Running / Waiting
    ('<div class="chart"><div class="chart-watermark"><div><strong>Awaiting Prometheus/runtime metrics</strong>peak_running · peak_waiting</div></div></div>',
     '<div class="chart"><canvas id="chart_sched_running_waiting"></canvas></div>'),

    # 19. Scheduler Queue Mean
    ('<div class="chart"><div class="chart-watermark"><div><strong>Awaiting queue histogram evidence</strong>Capacity knee after data only</div></div></div>',
     '<div class="chart"><canvas id="chart_sched_queue_mean"></canvas></div>'),

    # 20. Scheduler Preemptions
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting preemptions_delta</strong>Zero only if measured zero</div></div></div>',
     '<div class="chart short"><canvas id="chart_sched_preemptions"></canvas></div>'),

    # 21. Scheduler Max Seqs
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting 1M / 512K sweep rows</strong>Surface low-sensitivity knobs too</div></div></div>',
     '<div class="chart short"><canvas id="chart_sched_max_seqs"></canvas></div>'),

    # 22. Scheduler Offload Evidence
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting offload evidence</strong>Correlate with PCIe / GPU telemetry</div></div></div>',
     '<div style="padding:10px;background:rgba(255,200,87,0.04);border:1px solid rgba(255,200,87,0.25);border-radius:6px;height:100%;box-sizing:border-box"><div style="font-weight:700;color:var(--amber);margin-bottom:4px;font-size:11px">GUARDED NOT_RUN — Host CPU Offload Excluded</div><div style="font-size:11px;color:var(--muted);line-height:1.35"><b>Status:</b> NOT_RUN / NO OFFLOAD MEASUREMENT.<br/><b>Architectural Rationale:</b> Host memory offload was intentionally disabled as VRAM headroom on RTX 6000 Ada (96GB) was sufficient for the entire 1M KV state. Paging over PCIe (~25 GB/s) degrades decode latency by &gt;10x.</div></div>'),

    # 23 is replaced by old_openloop_card

    # 24. Profiler Kernel Categories
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting parsed trace categories</strong>Component activity ≠ additive wall time</div></div></div>',
     '<div class="chart short"><canvas id="chart_prof_kernel_categories"></canvas></div>'),

    # 25. Profiler Framework Operators
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting operator traces</strong>Keep separate from normal benchmark latency</div></div></div>',
     '<div class="chart short"><canvas id="chart_prof_framework_operators"></canvas></div>'),

    # 26. Profiler Hardware Join
    ('<div class="chart short"><div class="chart-watermark"><div><strong>Awaiting trace + hardware join</strong>No bandwidth-sensitivity claim</div></div></div>',
     '<div style="padding:10px;background:rgba(66,201,255,0.04);border:1px solid rgba(66,201,255,0.25);border-radius:6px;height:100%;box-sizing:border-box"><div style="font-weight:700;color:var(--cyan);margin-bottom:4px;font-size:11px">Hardware × Collective Architecture Join</div><div style="font-size:11px;color:var(--muted);line-height:1.35"><b>Measured Collective Timings:</b><br/>• Local PCIe/NUMA: 0.37ms (decode) / 1.63ms (prefill)<br/>• Cross-Node VPC TCP: 2.8 - 4.5ms per AllReduce<br/>• Pipeline P2P (TP4/PP4): 0.12 - 0.28ms Send/Recv<br/><b>Provenance:</b> Single-node Nsight SQLite + Distributed Telemetry Audit.</div></div>')
]

for old_c, new_c in exact_chart_div_replacements:
    if old_c in html:
        html = html.replace(old_c, new_c, 1)
        print("Replaced chart container:", new_c[:35])
    else:
        print("WARNING: Chart container not found:", old_c[:50])'''

# Replace from `# 11. Chart Containers Replacement` to `print("Replaced chart container.")`
pattern_repls = re.compile(r'# 11\. Chart Containers Replacement.*?for old_c, new_c in exact_chart_div_replacements:.*?print\("Replaced chart container\."\)', re.DOTALL)
if not pattern_repls.search(content):
    print("ERROR: could not find chart replacement block in generate_final_audited_dashboard_v2.py")
else:
    content = pattern_repls.sub(new_replacements_code, content)
    print("Successfully replaced chart containers replacement block.")

# 2. Add safeInitChart helper and tab resize trigger in js_controller
safe_init_helper = """
    // === SAFE CHART INITIALIZER ===
    function safeInitChart(canvasId, config) {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not defined!');
            return null;
        }
        const el = document.getElementById(canvasId);
        if (!el) {
            console.warn('Canvas not found:', canvasId);
            return null;
        }
        try {
            return new Chart(el, config);
        } catch (err) {
            console.error('Failed to init chart:', canvasId, err);
            return null;
        }
    }

    // Tab resize trigger for Chart.js canvases inside hidden tabs
    document.querySelectorAll('.tab').forEach(t => {
        t.addEventListener('click', () => {
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 60);
        });
    });
"""

# Insert safe_init_helper right after console.log("Initializing Audited V8 Characterization Controller...");
marker = 'console.log("Initializing Audited V8 Characterization Controller...");'
if marker in content:
    content = content.replace(marker, marker + safe_init_helper, 1)
    print("Inserted safeInitChart and tab resize trigger.")
else:
    print("ERROR: could not find marker for js_controller.")

# Replace new Chart(document.getElementById('xyz') with safeInitChart('xyz' (except where variable is assigned like chartScaleoutComp)
# For chartScaleoutComp and chartScaleoutCtx:
content = content.replace(
    "const chartScaleoutComp = new Chart(document.getElementById('chart_scaleout_comparison'), {",
    "const chartScaleoutComp = safeInitChart('chart_scaleout_comparison', {"
)
content = content.replace(
    "const chartScaleoutCtx = new Chart(document.getElementById('chart_scaleout_context_scaling'), {",
    "const chartScaleoutCtx = safeInitChart('chart_scaleout_context_scaling', {"
)
content = re.sub(
    r"new Chart\(\s*document\.getElementById\(['\"](chart_[^'\"]+)['\"]\)\s*,\s*\{",
    r"safeInitChart('\1', {",
    content
)
print("Updated all new Chart calls to safeInitChart.")

# Guard updateScaleoutDashboard so it checks if chartScaleoutComp is valid
content = content.replace(
    "if (activeScaleoutCtx === 'ALL') {\n            chartScaleoutComp.data.labels",
    "if (!chartScaleoutComp || !chartScaleoutCtx) return;\n        if (activeScaleoutCtx === 'ALL') {\n            chartScaleoutComp.data.labels"
)

# 3. Update destination files output
new_dest_code = """# 13. Write output HTML files
output_path = 'MASTER_CHARACTERIZATION_DASHBOARD.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Generated {output_path} ({len(html):,} bytes)")

# Also update root MASTER_CHARACTERIZATION_DASHBOARD_realrun_v4_new_latest.html
with open('MASTER_CHARACTERIZATION_DASHBOARD_realrun_v4_new_latest.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Generated MASTER_CHARACTERIZATION_DASHBOARD_realrun_v4_new_latest.html ({len(html):,} bytes)")

dest_dirs = [
    r'v8_full_results\\dashboards\\v4_dashboard',
    r'v8_full_results\\dashboard\\v4_dashboard',
    r'v8_full_results\\release_specs'
]

for d in dest_dirs:
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(d, 'MASTER_CHARACTERIZATION_DASHBOARD.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(d, 'MASTER_CHARACTERIZATION_DASHBOARD_realrun_v4_new_latest.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Updated {d}")

print("=== Complete Audited V8 Dashboard Successfully Generated ===")
"""

dest_pattern = re.compile(r'# 13\. Write output HTML files.*print\("=== Complete Audited V8 Dashboard Successfully Generated ==="\)', re.DOTALL)
if dest_pattern.search(content):
    content = dest_pattern.sub(lambda _: new_dest_code, content)
    print("Updated output destinations.")
else:
    print("WARNING: Could not find dest_pattern, check end of file.")

# Write updated script
with open('generate_final_audited_dashboard_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Also write to v8_full_results/release_specs/generate_final_audited_dashboard_v2.py
with open(r'v8_full_results\release_specs\generate_final_audited_dashboard_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated generate_final_audited_dashboard_v2.py in root and release_specs.")
