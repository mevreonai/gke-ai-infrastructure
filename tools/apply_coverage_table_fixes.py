dash_file = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"

with open(dash_file, "r", encoding="utf-8") as f:
    h = f.read()

# 1. Update low-export rows in coverage matrix
h = h.replace(
    '<tr><td><span class="mono">tp4_pp2_decode_8k</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export incomplete (2/8 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>',
    '<tr><td><span class="mono">tp4_pp2_decode_8k</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">4 / 4</span></td><td><span class="status s-completed">4 / 4</span></td><td><span class="status s-unres">INCOMPLETE (2/8 usable)</span></td><td>Eager-mode capture; per-worker nsys export incomplete (2/8 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>'
)

h = h.replace(
    '<tr><td><span class="mono">tp4_pp2_decode_8k_c8</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=8 Batched)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export failed (0/4 usable ranks). Stable queue in serving (0 preemptions).</td></tr>',
    '<tr><td><span class="mono">tp4_pp2_decode_8k_c8</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=8 Batched)</td><td><span class="status s-completed">4 / 4</span></td><td><span class="status s-completed">4 / 4</span></td><td><span class="status s-unres">INCOMPLETE (0/4 usable)</span></td><td>Eager-mode capture; per-worker nsys export failed (0/4 usable ranks). Stable queue in serving (0 preemptions).</td></tr>'
)

h = h.replace(
    '<tr><td><span class="mono">tp16_pp1_decode_8k</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export failed (0/9 usable ranks). Decode AllReduce estimated at 210-290 µs/call.</td></tr>',
    '<tr><td><span class="mono">tp16_pp1_decode_8k</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-unres">INCOMPLETE (0/9 usable)</span></td><td>Eager-mode capture; per-worker nsys export failed (0/9 usable ranks). Decode AllReduce estimated at 210-290 µs/call.</td></tr>'
)

h = h.replace(
    '<tr><td><span class="mono">tp16_pp1_prefill_512k</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>GCP_NATIVE</td><td>512K Heavy Prefill</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export incomplete (1/12 usable ranks). TTFT climbs to 29.62s (Native) and explodes to 128.28s under 20G cap (+333%).</td></tr>',
    '<tr><td><span class="mono">tp16_pp1_prefill_512k</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>GCP_NATIVE</td><td>512K Heavy Prefill</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-unres">INCOMPLETE (1/12 usable)</span></td><td>Eager-mode capture; per-worker nsys export incomplete (1/12 usable ranks). TTFT climbs to 29.62s (Native) and explodes to 128.28s under 20G cap (+333%).</td></tr>'
)

h = h.replace(
    '<tr><td><span class="mono">tp4_pp2_prefill_128k</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span>',
    '<tr><td><span class="mono">tp4_pp2_prefill_128k</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">4 / 4</span></td><td><span class="status s-completed">4 / 4</span>'
)

# 2. Update capped rows in coverage matrix
old_capped_block = """        <!-- Configured-100G Complete (3) -->
        <tr style="background:rgba(66,201,255,0.04)"><td><span class="mono">tp4_pp2_dist_capped100g</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>CAPPED_100G</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Complete 16-rank dual-node capture under configured 100G bandwidth cap</td></tr>
        <tr style="background:rgba(66,201,255,0.04)"><td><span class="mono">tp4_pp4_dist_capped100g</span></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>CAPPED_100G</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Complete 16-rank dual-node capture under configured 100G bandwidth cap</td></tr>
        <tr style="background:rgba(66,201,255,0.04)"><td><span class="mono">tp8_pp2_dist_capped100g</span></td><td><b style="color:var(--amber)">TP8 / PP2</b></td><td>CAPPED_100G</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Complete 16-rank dual-node capture under configured 100G bandwidth cap</td></tr>

        <!-- Remaining Expected Capped Points (5) -->
        <tr style="opacity:0.65"><td><span class="mono">tp16_pp1_dist_capped100g</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>CAPPED_100G</td><td>128K Prefill</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Deferred in favor of empirical E2E benchmark runs and iperf3 validation</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp4_pp4_decode_capped100g</span></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>CAPPED_100G</td><td>8K Decode</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Deferred in favor of empirical E2E benchmark runs and iperf3 validation</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp8_pp2_decode_capped100g</span></td><td><b style="color:var(--amber)">TP8 / PP2</b></td><td>CAPPED_100G</td><td>8K Decode</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Deferred in favor of empirical E2E benchmark runs and iperf3 validation</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp4_pp2_decode_capped100g</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>CAPPED_100G</td><td>8K Decode</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Deferred in favor of empirical E2E benchmark runs and iperf3 validation</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp16_pp1_decode_capped100g</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>CAPPED_100G</td><td>8K Decode</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Deferred in favor of empirical E2E benchmark runs and iperf3 validation</td></tr>"""

new_capped_block = """        <!-- Configured-100G Complete (3) -->
        <tr style="background:rgba(66,201,255,0.04)"><td><span class="mono">tp4_pp2_dist_capped100g</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>CAPPED_100G</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">4 / 4</span></td><td><span class="status s-completed">4 / 4</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Complete 8-rank dual-node capture (4+4 ranks; 8/8 usable) under configured 100G cap</td></tr>
        <tr style="background:rgba(66,201,255,0.04)"><td><span class="mono">tp4_pp4_dist_capped100g</span></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>CAPPED_100G</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Complete 16-rank dual-node capture (16/16 usable) under configured 100G cap</td></tr>
        <tr style="background:rgba(66,201,255,0.04)"><td><span class="mono">tp8_pp2_dist_capped100g</span></td><td><b style="color:var(--amber)">TP8 / PP2</b></td><td>CAPPED_100G</td><td>128K Prefill (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">7 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>16-rank dual-node capture (15/16 usable ranks) under configured 100G cap</td></tr>

        <!-- Remaining Expected Capped Points (5 Planned 128K Prefill Sweeps) -->
        <tr style="opacity:0.65"><td><span class="mono">tp16_pp1_dist_capped100g</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>CAPPED_100G</td><td>128K Prefill</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Planned 128K prefill sweep; not captured (cause not logged in archive)</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp4_pp4_dist_capped20g</span></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>CAPPED_20G</td><td>128K Prefill</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Planned 128K prefill sweep; not captured (no capped decode was ever planned)</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp8_pp2_dist_capped20g</span></td><td><b style="color:var(--amber)">TP8 / PP2</b></td><td>CAPPED_20G</td><td>128K Prefill</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Planned 128K prefill sweep; not captured (no capped decode was ever planned)</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp4_pp2_dist_capped20g</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>CAPPED_20G</td><td>128K Prefill</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Planned 128K prefill sweep; not captured (no capped decode was ever planned)</td></tr>
        <tr style="opacity:0.65"><td><span class="mono">tp16_pp1_dist_capped20g</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>CAPPED_20G</td><td>128K Prefill</td><td><span class="status s-na">—</span></td><td><span class="status s-na">—</span></td><td><span class="status s-na">NOT_CAPTURED</span></td><td>Planned 128K prefill sweep; not captured (no capped decode was ever planned)</td></tr>"""

h = h.replace(old_capped_block, new_capped_block)

# 3. Update provenance table row
h = h.replace(
    "3 Prefill sweeps captured at 100G; decode points deferred in favor of empirical E2E benchmarks",
    "3 Prefill sweeps captured at 100G (TP4/PP2, TP8/PP2, TP4/PP4); TP16 @ 100G and all 4 layouts @ 20G not captured (no capped decode was planned)"
)

with open(dash_file, "w", encoding="utf-8") as f:
    f.write(h)

print("Saved coverage table updates successfully! New length:", len(h))
