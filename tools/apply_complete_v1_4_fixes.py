import sys, re

dash_file = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"

with open(dash_file, "r", encoding="utf-8") as f:
    h = f.read()

print("Initial HTML length:", len(h))

# 1. Fix remaining 'Stages 1–3 wait 17–22%'
h = h.replace(
    "Stage 0 only; Stages 1–3 wait 17–22%",
    "Stage 0 only; Stage 3 waits 17.2–21.9%, Stages 0–2 wait 8.0–11.2%"
)
h = h.replace(
    "Stage 0 only; Stages 1-3 wait 17-22%",
    "Stage 0 only; Stage 3 waits 17.2–21.9%, Stages 0–2 wait 8.0–11.2%"
)
h = h.replace(
    "SendRecv P2P handoff is 8.3% of Stage 0 work (Stages 1–3 wait 17–22%)",
    "SendRecv P2P handoff is 8.3% of Stage 0 work (Stage 3 waits 17.2–21.9%, Stages 0–2 wait 8.0–11.2%)"
)
h = h.replace(
    "SendRecv P2P handoff is 8.3% of Stage 0 work (Stages 1-3 wait 17-22%)",
    "SendRecv P2P handoff is 8.3% of Stage 0 work (Stage 3 waits 17.2–21.9%, Stages 0–2 wait 8.0–11.2%)"
)

# 2. Fix duplicated mode badge in openEvidencePopup
h = h.replace(
    'if (datum.mode) badgesHtml += `<span class="badge b-amber" style="font-weight:600">Mode: ${datum.mode}</span>`;\n        if (datum.mode) badgesHtml += `<span class="badge b-amber" style="font-weight:600">Mode: ${datum.mode}</span>`;',
    'if (datum.mode) badgesHtml += `<span class="badge b-amber" style="font-weight:600">Mode: ${datum.mode}</span>`;'
)

# 3. Fix duplicate chips in profiler scenario chips
old_chips = """    <span class="chip prof-scenario-chip" data-scenario="tp4_pp4_dist" style="cursor:pointer">TP4/PP4 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp4_pp2_dist" style="cursor:pointer">TP4/PP2 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp8_pp2_dist" style="cursor:pointer">TP8/PP2 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp4_pp2_dist" style="cursor:pointer">TP4/PP2 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp8_pp2_dist" style="cursor:pointer">TP8/PP2 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp16_pp1_dist" style="cursor:pointer">TP16/PP1 Dist Prefill (128K Native)</span>"""

new_chips = """    <span class="chip prof-scenario-chip" data-scenario="tp4_pp4_dist" style="cursor:pointer">TP4/PP4 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp4_pp2_dist" style="cursor:pointer">TP4/PP2 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp8_pp2_dist" style="cursor:pointer">TP8/PP2 Dist Prefill (128K Native)</span>
    <span class="chip prof-scenario-chip" data-scenario="tp16_pp1_dist" style="cursor:pointer">TP16/PP1 Dist Prefill (128K Native)</span>"""

h = h.replace(old_chips, new_chips)

# 4. Fix composition chart onClick prMap to 7 valid datasets
h = h.replace(
    "const prMap = ['PR-001', 'PR-002', 'PR-003', 'PR-004', 'PR-005'];\n                return { profile_id: prMap[dsIdx] };",
    "const prMap = ['PR-001', 'PR-002', 'PR-003', 'PR-004', 'PR-005', 'PR-005', 'PR-005'];\n                return { profile_id: prMap[dsIdx] || 'PR-001' };"
)

# 5. Fix 1.95x / 1.95× occurrences
h = h.replace(
    '{"layer": "1. Raw NCCL Microbench", "metric": "16K AllReduce Latency", "tp4": "19.0 \\u03bcs", "tp8": "37.0 \\u03bcs", "delta": "+94.7% (1.95x)"}',
    '{"layer": "1. Raw NCCL Microbench", "metric": "16K AllReduce Latency", "tp4": "19.0 \\u03bcs", "tp8": "37.6 \\u03bcs", "delta": "+97.9% (1.98x)"}'
)
h = h.replace(
    '1.95× NCCL Barrier Latency → 3.10× PyTorch AR CUDA → +41.9% End-to-End TPOT',
    '1.98× NCCL Barrier Latency (19.0 vs 37.6 µs) → 3.10× PyTorch AR CUDA → +41.9% End-to-End TPOT'
)
h = h.replace(
    '<td>nccl_points.csv (16 KiB AllReduce)</td><td>19.0 μs</td><td>37.0 μs</td><td><b>1.95× barrier latency</b></td>',
    '<td>nccl_points.csv (16 KiB AllReduce)</td><td>19.0 μs</td><td>37.6 μs</td><td><b>1.98× barrier latency</b></td>'
)
h = h.replace(
    '16 KiB AllReduce latency is 1.95× higher (19 μs vs 37 μs)',
    '16 KiB AllReduce latency is 1.98× higher (19.0 μs vs 37.6 μs)'
)

# 6. Fix KD#7 Layer 2 from 2.32x to 3.10x
h = h.replace(
    '{"layer": "2. PyTorch Framework", "metric": "Self CUDA allreduce Duration", "tp4": "251.5 ms", "tp8": "583.9 ms", "delta": "+132.2% (2.32x, 7040 calls)"}',
    '{"layer": "2. PyTorch Framework (Graphs-On)", "metric": "Decode-Only AllReduce Duration", "tp4": "132.3 ms (18.9 \\u03bcs/call)", "tp8": "409.9 ms (58.7 \\u03bcs/call)", "delta": "+209.8% (3.10x, 6,985 calls; whole-capture was 251.5 vs 583.9 ms)"}'
)

# 7. Fix GEMV tooltip (44.6ms faster instead of 66.9ms)
h = h.replace(
    "TP8 decode GEMV is 66.9ms faster, but outweighed by the 14-step collective ring barrier delay",
    "TP8 decode GEMV is 44.6ms faster (171.2 → 126.5 ms), but outweighed by the 14-step collective ring barrier delay"
)

# 8. Fix operator accounting sentence order
h = h.replace(
    "TP8 decode-only AllReduce penalty (+277.6 ms) exceeds GEMV savings (+39.8 µs/call over 6,985 decode steps)",
    "TP8 decode-only AllReduce penalty (+277.6 ms; +39.8 µs/call over 6,985 decode calls) exceeds GEMV savings (−44.6 ms: 171.2 → 126.5 ms)"
)

# 9. Fix Executive prefill communications
h = h.replace(
    '<tr><td><b>8K</b></td><td>1</td><td>≈ 0.12 s</td><td>0.222 s</td><td><span class="badge b-amber">≈ 50 %</span></td><td>Intra-node PCIe ring bus bandwidth (26 GB/s, no NVLink) makes AllReduce 50% of 8K TTFT.',
    '<tr><td><b>8K</b></td><td>1</td><td>≈ 0.12 s</td><td>0.222 s</td><td><span class="badge b-amber">54 %</span></td><td>Intra-node PCIe ring bus bandwidth (26 GB/s, no NVLink) makes AllReduce 54% of 8K TTFT.'
)
h = h.replace(
    "intra-node TP prefill spends 14–50% of first token in AllReduce depending on prompt length",
    "intra-node TP prefill spends 16–57% of first token in AllReduce depending on prompt length"
)
h = h.replace(
    "§4.4 &amp; §4.8: 14–50% of TTFT in AllReduce for in-node TP by prompt length",
    "§4.4 &amp; §4.8: 16–57% of TTFT in AllReduce for in-node TP by prompt length"
)

# 10. Fix tile KV read labels
h = h.replace(
    "1M decode is 54% KV read · Load is 50–96% queue/stalls",
    "1M decode has 54% memory-speed floor (mostly KV read) · Load is 50–96% queue/stalls"
)

# 11. Fix Campaign scope unresolved decode line
h = h.replace(
    "decode profiles in graphs-on mode (captured in eager mode only; serving operates with CUDA Graphs ON)",
    "two-node decode profiles (single-node graphs-on decode profiles exist; multi-node decode profiles deferred)"
)

# 12. Fix PR-001 aggregation rule & subtitle
h = h.replace(
    "Rank 0 aggregate GPU kernel work across 112,640 traced kernels; validated with torch.profiler",
    "Rank 0 aggregate GPU kernel work across 84,456 kernel launches (5,060 AllReduce calls) from Nsight export"
)
h = h.replace(
    "cuda_gpu_kern_sum.csv across 112,640 traced kernels (not exclusive request wall-clock; Rank 0 primary reporting)",
    "cuda_gpu_kern_sum.csv (84,456 kernel launches in prefill, 112,640 AllReduces in decode; Rank 0 primary reporting)"
)
h = h.replace(
    "afterBody: () => ['Empirically extracted from Nsight Systems SQLite exports across 112,640 traced kernel calls.']",
    "afterBody: () => ['Empirically extracted from Nsight Systems SQLite exports.']"
)

# 13. Fix PR-004 range and PR-006 & PR-007
h = h.replace(
    "range 74.8% - 79.5%",
    "range 76.3% - 79.5%"
)
h = h.replace(
    "All-Rank Range 75.1–78.9%, Mean 77.6%",
    "All-Rank Range 76.3–79.5%, Mean 77.6%"
)
h = h.replace(
    "Matched 128K vs 512K profile scaling; FlashAttention scales ~15.7x while MoE scales ~3.8x and KDA ~3.9x",
    "1 of 12 rank exports usable; no composition claimed (TP4/PP4 128K vs 512K matched scaling shown for context)"
)
h = h.replace(
    "kernels: { 'Stage 0 FlashAttention': '22.0%', 'Stages 1-3 FlashAttention': '44.8%', 'Intra-Node TP AllReduce': '35.6%', 'Fused MoE Routing/Experts': '6.2%', 'Inter-Node P2P SendRecv': '5.2%' }",
    "kernels: { 'Stage 0 FlashAttention': '22.4%', 'Stages 1-3 FlashAttention': '44.8%', 'Stage 0 SendRecv': '25.8%', 'Stage 0 AllReduce': '21.3%', 'Fused MoE': '6.2%' }"
)

# 14. Fix Repeatability examples
h = h.replace(
    "Deltas of ±0.10% (e.g. 100G cap at 128K) are within pure replicate noise; +1.14% (TP4/PP2 at 20G, 1M) is at the statistical boundary; +3.91% (TP4/PP4 at 20G, 128K) is an empirically verified network slowdown.",
    "Deltas of ±0.10% (e.g. TP8/PP2 at 1M: −0.10%, or TP4/PP2 at 1M under 100G: +0.13%) are within pure replicate noise; +1.14% (TP4/PP2 at 20G, 1M) is at the statistical boundary; +3.91% (TP4/PP4 at 20G, 1M) and +14.67% (TP4/PP4 at 20G, 128K) are empirically verified network slowdowns."
)

# 15. Fix D2H 56.6 GB/s and offload text
h = h.replace(
    "D2H 56.6 GB/s",
    "D2H 56.5 GB/s"
)
h = h.replace(
    "While offload was disabled in active serving benchmarks, the physical bounds are mathematically certain: reloading latent KV from host DRAM costs only ~0.3% of a full prefill (0.14s vs 93.3s).",
    "While initial offload serving runs failed to start (rc=1; verified in Stage 2), bandwidth calculations indicate reloading latent KV from host DRAM costs ~0.14s (tested empirically in Stage 2 with DDR5 swapping)."
)

# 16. Fix Finding 1 & 2 overstatements
h = h.replace(
    "Per-request trace proves it: wave arrivals land at <b>0.23, 0.65, 0.87, 0.88s</b>. A 256-token headroom expansion (budget 8,448 or 8,000 prompt tokens) saves <b>211 ms</b> at c4.",
    "Per-request trace shows first tokens land at <b>0.23, 0.65, 0.87, 0.88s</b>. Expanding batch token headroom to <b>8,448</b> (or 8,000 prompt tokens) is predicted to save <b>~211 ms</b> at c4 (plan A1 test)."
)
h = h.replace(
    "Concurrency forces uniform routing to touch <b>163 of 256 experts</b> at c32 and <b>222 at full load</b> (vs 8 at c1), driving weights read from 0.9 ms to 10.5 and 14.9 ms at memory speed. By c16, decode is memory-bound again on expert weights, causing sub-linear throughput scaling.",
    "A batch of 32 is expected to touch <b>~163 of 256 experts</b> under uniform routing (upper estimate; <b>222 at full load</b> vs 8 at c1), driving weights read from 0.9 ms to 10.5 and 14.9 ms at memory speed while kernels above the floor stay at 2.5–4.8 ms. By c16, decode is memory-bound again on expert weights."
)
h = h.replace(
    "Expanding batch token headroom to <b>8,448</b> (or prompting with 8,000 tokens) eliminates this <b>211 ms</b> penalty.",
    "Expanding batch token headroom to <b>8,448</b> (or prompting with 8,000 tokens) is predicted to save <b>~211 ms</b> (plan A1 test)."
)
h = h.replace(
    "Under load, MoE decode step expands from <b>4.5 ms</b> (c1, 8 active experts) to <b>15.8 ms</b> (c32, 163 of 256 experts) and <b>22.9 ms</b> at full load (222 experts). Routed weights read at memory speed grow from 0.9 ms to 10.5 and 14.9 ms.",
    "Under load, MoE decode step expands from <b>4.5 ms</b> (c1, 8 active experts) to <b>15.8 ms</b> (c32, ~163 of 256 experts expected under uniform routing) and <b>22.9 ms</b> at full load (~222 experts). Routed weights read at memory speed grow from 0.9 ms to 10.5 and 14.9 ms, while kernels above the floor stay at 2.5–4.8 ms."
)

# 17. Fix 14/22 header chip
h = h.replace(
    '<div class="k-value" style="color:var(--amber)">14 / 22 CAPTURED</div><div class="k-note">7 with usable exports (all prefill); decode deferred · 8 missing</div>',
    '<div class="k-value" style="color:var(--amber)">14 / 22 CAPTURED</div><div class="k-note">8 with usable exports (all prefill); decode deferred · 8 missing</div>'
)

# 18. Fix Scheduler scale-out ledger queue column
old_sched_rows = """<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>0.365%</b></td><td>0.012ms</td><td>~88.83 GiB</td><td><span class="status s-completed">Peak KV 0.37% · 0 Preempt</span></td><td>Pipeline stage memory partitioning</td><td><b style="color:var(--green)">Lowest Measured TTFT (1.71s)</b></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>1.444%</b></td><td>0.020ms</td><td>~88.83 GiB</td><td><span class="status s-completed">Peak KV 1.44% · 0 Preempt</span></td><td>Clean activation handoff across stages</td><td><b style="color:var(--green)">Lowest Measured TTFT (10.22s)</b></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>1M</td><td>c=1</td><td><b style="color:var(--green)">2.748%</b></td><td>0.020ms</td><td>~88.83 GiB</td><td><span class="status s-completed">Peak KV 2.75% · 0 Preempt</span></td><td>Observed per-stage peak KV allocation (~2.75%), consistent with 4-stage pipeline distribution</td><td><b style="color:var(--green)">Cleanest Distributed 1M (28.57s)</b></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>0.785%</b></td><td>0.012ms</td><td>~88.69 GiB</td><td><span class="status s-completed">Peak KV 0.79% · 0 Preempt</span></td><td>Balanced 2-stage pipeline layout</td><td><b style="color:var(--cyan)">Lowest Measured TPOT (5.51ms)</b></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>3.105%</b></td><td>0.020ms</td><td>~88.69 GiB</td><td><span class="status s-completed">Peak KV 3.10% · 0 Preempt</span></td><td>Balanced 2-stage pipeline layout</td><td><b style="color:var(--cyan)">Lowest Measured TPOT (7.86ms)</b></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>1M</td><td>c=1</td><td><b>5.911%</b></td><td>0.020ms</td><td>~88.69 GiB</td><td><span class="status s-completed">Peak KV 5.91% · 0 Preempt</span></td><td>Balanced 2-stage pipeline layout</td><td><b style="color:var(--cyan)">Lowest Measured TPOT (10.54ms)</b></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>0.776%</b></td><td>0.012ms</td><td>~87.51 GiB</td><td><span class="status s-completed">Peak KV 0.78% · 0 Preempt</span></td><td>Single intra-node stage AllReduce</td><td>Viable</td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>3.087%</b></td><td>0.020ms</td><td>~87.51 GiB</td><td><span class="status s-completed">Peak KV 3.09% · 0 Preempt</span></td><td>Single intra-node stage AllReduce</td><td>Viable</td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>1M</td><td>c=1</td><td><b>5.882%</b></td><td>0.020ms</td><td>~87.51 GiB</td><td><span class="status s-completed">Peak KV 5.88% · 0 Preempt</span></td><td>Single intra-node stage AllReduce</td><td>Viable</td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>1.595%</b></td><td>0.012ms</td><td>~86.71 GiB</td><td><span class="status s-completed">Peak KV 1.60% · 0 Preempt</span></td><td>Cross-node TCP AllReduce collective</td><td>Completed (6.42s TTFT)</td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>6.362%</b></td><td>0.020ms</td><td>~86.71 GiB</td><td><span class="status s-completed">Peak KV 6.36% · 0 Preempt</span></td><td>Cross-node TCP AllReduce collective</td><td>Completed (29.62s TTFT)</td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>1M</td><td>c=1</td><td><b>12.129%</b></td><td>0.020ms</td><td>~86.71 GiB</td><td><span class="status s-completed">Peak KV 12.13% · 0 Preempt</span></td><td>Cross-node TCP AllReduce collective</td><td>Highest TTFT (68.20s)</td></tr>"""

new_sched_rows = """<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>0.365%</b></td><td>0.012ms</td><td>~88.83 GiB</td><td><span class="status s-completed">Peak KV 0.37% · 0 Preempt</span></td><td>Pipeline stage memory partitioning</td><td><b style="color:var(--green)">Lowest Measured TTFT (1.71s)</b></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>1.444%</b></td><td>0.016ms</td><td>~88.83 GiB</td><td><span class="status s-completed">Peak KV 1.44% · 0 Preempt</span></td><td>Clean activation handoff across stages</td><td><b style="color:var(--green)">Lowest Measured TTFT (10.22s)</b></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>1M</td><td>c=1</td><td><b style="color:var(--green)">2.748%</b></td><td>0.020ms</td><td>~88.83 GiB</td><td><span class="status s-completed">Peak KV 2.75% · 0 Preempt</span></td><td>Observed per-stage peak KV allocation (~2.75%), consistent with 4-stage pipeline distribution</td><td><b style="color:var(--green)">Cleanest Distributed 1M (28.57s)</b></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>0.785%</b></td><td>0.012ms</td><td>~88.69 GiB</td><td><span class="status s-completed">Peak KV 0.79% · 0 Preempt</span></td><td>Balanced 2-stage pipeline layout</td><td><b style="color:var(--cyan)">Lowest Measured TPOT (5.51ms)</b></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>3.105%</b></td><td>0.023ms</td><td>~88.69 GiB</td><td><span class="status s-completed">Peak KV 3.10% · 0 Preempt</span></td><td>Balanced 2-stage pipeline layout</td><td><b style="color:var(--cyan)">Lowest Measured TPOT (7.86ms)</b></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>1M</td><td>c=1</td><td><b>5.911%</b></td><td>0.021ms</td><td>~88.69 GiB</td><td><span class="status s-completed">Peak KV 5.91% · 0 Preempt</span></td><td>Balanced 2-stage pipeline layout</td><td><b style="color:var(--cyan)">Lowest Measured TPOT (10.54ms)</b></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>0.776%</b></td><td>0.012ms</td><td>~87.51 GiB</td><td><span class="status s-completed">Peak KV 0.78% · 0 Preempt</span></td><td>Single intra-node stage AllReduce</td><td>Viable</td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>3.087%</b></td><td>0.020ms</td><td>~87.51 GiB</td><td><span class="status s-completed">Peak KV 3.09% · 0 Preempt</span></td><td>Single intra-node stage AllReduce</td><td>Viable</td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>1M</td><td>c=1</td><td><b>5.882%</b></td><td>0.038ms</td><td>~87.51 GiB</td><td><span class="status s-completed">Peak KV 5.88% · 0 Preempt</span></td><td>Single intra-node stage AllReduce</td><td>Viable</td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>128K</td><td>c=1</td><td><b>1.595%</b></td><td>0.019ms</td><td>~86.71 GiB</td><td><span class="status s-completed">Peak KV 1.60% · 0 Preempt</span></td><td>Cross-node TCP AllReduce collective</td><td>Completed (6.42s TTFT)</td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>512K</td><td>c=1</td><td><b>6.362%</b></td><td>0.021ms</td><td>~86.71 GiB</td><td><span class="status s-completed">Peak KV 6.36% · 0 Preempt</span></td><td>Cross-node TCP AllReduce collective</td><td>Completed (29.62s TTFT)</td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>1M</td><td>c=1</td><td><b>12.129%</b></td><td>0.021ms</td><td>~86.71 GiB</td><td><span class="status s-completed">Peak KV 12.13% · 0 Preempt</span></td><td>Cross-node TCP AllReduce collective</td><td>Highest TTFT (68.20s)</td></tr>"""

h = h.replace(old_sched_rows, new_sched_rows)

# 19. Fix Exact Heatmap HTML Rows
old_heatmap_rows = """<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>128K</td><td>1.710s</td><td>1.761s</td><td><span class="badge b-green">+2.97%</span></td><td>1.961s</td><td><span class="badge b-green">+14.67%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>512K</td><td>10.222s</td><td>10.389s</td><td><span class="badge b-green">+1.64%</span></td><td>11.134s</td><td><span class="badge b-green">+8.93%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>1M</td><td>28.568s</td><td>28.866s</td><td><span class="badge b-green">+1.04%</span></td><td>29.684s</td><td><span class="badge b-green">+3.91%</span></td><td><span class="status s-completed">LOWEST DELTA ON 20G CAP</span></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>128K</td><td>2.791s</td><td>2.829s</td><td><span class="badge b-green">+1.37%</span></td><td>2.813s</td><td><span class="badge b-green">+0.81%</span></td><td><span class="status s-completed">LOW APPLICATION TTFT SENSITIVITY IN THIS MEASURED CAP SWEEP</span></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>512K</td><td>15.578s</td><td>15.551s</td><td><span class="badge b-green">-0.18%</span></td><td>15.548s</td><td><span class="badge b-green">-0.19%</span></td><td><span class="status s-completed">INSENSITIVE TO EGRESS CAP</span></td></tr>
<tr><td><b style="color:var(--amber)">TP8 / PP2 (Dist)</b></td><td>1M</td><td>41.512s</td><td>41.459s</td><td><span class="badge b-green">-0.13%</span></td><td>41.469s</td><td><span class="badge b-green">-0.10%</span></td><td><span class="status s-completed">INSENSITIVE TO EGRESS CAP</span></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>128K</td><td>2.646s</td><td>2.664s</td><td><span class="badge b-green">+0.66%</span></td><td>2.858s</td><td><span class="badge b-green">+8.01%</span></td><td><span class="status s-completed">MODERATE NETWORK SENSITIVITY</span></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>512K</td><td>17.947s</td><td>17.984s</td><td><span class="badge b-green">+0.20%</span></td><td>18.373s</td><td><span class="badge b-green">+2.37%</span></td><td><span class="status s-completed">MODERATE NETWORK SENSITIVITY</span></td></tr>
<tr><td><b style="color:var(--cyan)">TP4 / PP2 (Dist)</b></td><td>1M</td><td>52.529s</td><td>52.600s</td><td><span class="badge b-green">+0.13%</span></td><td>53.130s</td><td><span class="badge b-green">+1.14%</span></td><td><span class="status s-completed">MODERATE NETWORK SENSITIVITY</span></td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>128K</td><td>6.420s</td><td>9.735s</td><td><span class="badge b-green">+51.64%</span></td><td>31.051s</td><td><span class="badge b-red">+383.66%</span></td><td><span class="status s-failed">HIGH NETWORK SENSITIVITY (COMPLETED)</span></td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>512K</td><td>29.624s</td><td>43.095s</td><td><span class="badge b-green">+45.47%</span></td><td>128.275s</td><td><span class="badge b-red">+333.01%</span></td><td><span class="status s-failed">HIGH NETWORK SENSITIVITY (COMPLETED)</span></td></tr>
<tr><td><b style="color:var(--red)">TP16 / PP1 (Dist)</b></td><td>1M</td><td>68.197s</td><td>92.992s</td><td><span class="badge b-green">+36.36%</span></td><td>256.892s</td><td><span class="badge b-red">+276.69%</span></td><td><span class="status s-failed">HIGH NETWORK SENSITIVITY (COMPLETED)</span></td></tr>"""

new_heatmap_rows = """<tr><td><b style="color:var(--purple)">TP4 / PP4 (Dist)</b></td><td>128K</td><td>1.710s</td><td>1.761s</td><td><span class="badge b-green">+2.97%</span></td><td>1.961s</td><td><span class="badge b-green">+14.67%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span></td></tr>
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

h = h.replace(old_heatmap_rows, new_heatmap_rows)

with open(dash_file, "w", encoding="utf-8") as f:
    f.write(h)

print("Saved updated HTML. New length:", len(h))
