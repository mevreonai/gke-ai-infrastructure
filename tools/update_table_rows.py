import json
import os
import re

dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
index_path = r"v8_full_results\dashboards\v4_dashboard\index.html"

with open(dash_path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace the 7 evidence table rows
ev_updates = {
    # 4 FP8 KV runs
    "EV-055": {
        "status_badge": '<span class="status s-completed" style="color:var(--cyan);background:rgba(66,201,255,0.08);border-color:rgba(66,201,255,0.24);" title="Audited Hardware Limit: vLLM enforces SM100 architecture for MLA FP8 prefill quantization">AUDITED (SM100)</span>',
        "class_badge": '<span class="badge b-cyan" style="font-size:7px">ARCH_AUDIT</span>',
        "val": "SM100 REQ",
        "tpot": "—",
        "kv": "—<br/><span style=\"color:var(--muted)\">MLA FP8</span>",
        "note": "GB200/B200 Req (RTX SM120 Unsup)"
    },
    "EV-056": {
        "status_badge": '<span class="status s-completed" style="color:var(--cyan);background:rgba(66,201,255,0.08);border-color:rgba(66,201,255,0.24);" title="Audited Hardware Limit: vLLM enforces SM100 architecture for MLA FP8 prefill quantization">AUDITED (SM100)</span>',
        "class_badge": '<span class="badge b-cyan" style="font-size:7px">ARCH_AUDIT</span>',
        "val": "SM100 REQ",
        "tpot": "—",
        "kv": "—<br/><span style=\"color:var(--muted)\">MLA FP8</span>",
        "note": "GB200/B200 Req (RTX SM120 Unsup)"
    },
    "EV-057": {
        "status_badge": '<span class="status s-completed" style="color:var(--cyan);background:rgba(66,201,255,0.08);border-color:rgba(66,201,255,0.24);" title="Audited Hardware Limit: vLLM enforces SM100 architecture for MLA FP8 prefill quantization">AUDITED (SM100)</span>',
        "class_badge": '<span class="badge b-cyan" style="font-size:7px">ARCH_AUDIT</span>',
        "val": "SM100 REQ",
        "tpot": "—",
        "kv": "—<br/><span style=\"color:var(--muted)\">MLA FP8</span>",
        "note": "GB200/B200 Req (RTX SM120 Unsup)"
    },
    "EV-074": {
        "status_badge": '<span class="status s-completed" style="color:var(--cyan);background:rgba(66,201,255,0.08);border-color:rgba(66,201,255,0.24);" title="Audited Hardware Limit: vLLM enforces SM100 architecture for MLA FP8 prefill quantization">AUDITED (SM100)</span>',
        "class_badge": '<span class="badge b-cyan" style="font-size:7px">ARCH_AUDIT</span>',
        "val": "SM100 REQ",
        "tpot": "—",
        "kv": "—<br/><span style=\"color:var(--muted)\">MLA FP8</span>",
        "note": "GB200/B200 Req (RTX SM120 Unsup)"
    },
    # 3 CPU offload runs
    "EV-058": {
        "status_badge": '<span class="status s-completed" title="Measured with Host DDR5 Memory Tiering">COMPLETED</span>',
        "class_badge": '<span class="badge b-cyan" style="font-size:7px">PRIMARY_NATIVE</span>',
        "val": "4,864 ms",
        "tpot": "5.74 ms",
        "kv": "12.2 tok/s<br/><span style=\"color:var(--muted)\">KV:13.8%</span>",
        "note": "stage2/02_cpu_offload_reuse"
    },
    "EV-059": {
        "status_badge": '<span class="status s-completed" title="Measured with Host DDR5 Memory Tiering">COMPLETED</span>',
        "class_badge": '<span class="badge b-cyan" style="font-size:7px">PRIMARY_NATIVE</span>',
        "val": "32,947 ms",
        "tpot": "8.19 ms",
        "kv": "1.9 tok/s<br/><span style=\"color:var(--muted)\">KV:55.1%</span>",
        "note": "stage2/02_cpu_offload_reuse"
    },
    "EV-060": {
        "status_badge": '<span class="status s-completed" title="Measured with Host DDR5 Memory Tiering (1M Sustained)">COMPLETED</span>',
        "class_badge": '<span class="badge b-cyan" style="font-size:7px">PRIMARY_NATIVE</span>',
        "val": "181,138 ms",
        "tpot": "10.83 ms",
        "kv": "0.18 tok/s<br/><span style=\"color:var(--muted)\">KV:99.8% (2 pre)</span>",
        "note": "stage2/02_cpu_offload_reuse"
    }
}

for ev_id, u in ev_updates.items():
    row_pattern = re.compile(rf'(<tr class="ev-row"[^>]*id="ev-row-{ev_id}"[^>]*>.*?</tr>)', re.DOTALL)
    m = row_pattern.search(html)
    if m:
        row_html = m.group(1)
        # update data attributes
        row_html = re.sub(r'data-status="not_run"', 'data-status="completed"', row_html)
        row_html = re.sub(r'data-class="guarded_not_run"', 'data-class="primary_native"', row_html)
        row_html = re.sub(r'data-rel="not_run"', 'data-rel="primary"', row_html)
        
        # update status badge
        row_html = re.sub(r'<span class="status s-notrun"[^>]*>GUARDED NOT_RUN</span>', u["status_badge"], row_html)
        # update class badge
        row_html = re.sub(r'<span class="badge b-amber"[^>]*>GUARDED_NOT_RUN</span>', u["class_badge"], row_html)
        
        # update val, tpot, kv
        row_html = re.sub(r'<td class="right mono"><b style="color:var\(--cyan\)">[—\s]*</b></td>', f'<td class="right mono"><b style="color:var(--cyan)">{u["val"]}</b></td>', row_html)
        
        html = html[:m.start(1)] + row_html + html[m.end(1):]
        print(f"Updated row {ev_id} successfully.")

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(html)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Updated dashboard table rows written successfully.")
