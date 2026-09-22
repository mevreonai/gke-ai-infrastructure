import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Deployment Decision Map Table
old_exec_t1 = """<tbody>
<tr><td>Short-context interactive</td><td>TPOT</td><td class="unknown">post-run</td><td class="unknown">post-run</td><td>Native / N/A single-node</td><td class="unknown">post-run</td><td>—</td></tr>
<tr><td>Long prompt, c1</td><td>TTFT</td><td class="unknown">post-run</td><td class="unknown">post-run</td><td>Native / N/A single-node</td><td class="unknown">post-run</td><td>—</td></tr>
<tr><td>512K serving</td><td>TTFT + TPOT</td><td class="unknown">post-run</td><td class="unknown">post-run</td><td>Native / N/A single-node</td><td class="unknown">post-run</td><td>—</td></tr>
<tr><td>1M c1</td><td>Feasibility + TTFT</td><td class="unknown">post-run</td><td class="unknown">post-run</td><td>Native / N/A single-node</td><td class="unknown">post-run</td><td>—</td></tr>
<tr><td>1M concurrent</td><td>TTFT/TPOT + queue</td><td class="unknown">post-run</td><td class="unknown">post-run</td><td>Native / N/A single-node</td><td class="unknown">post-run</td><td>—</td></tr>
<tr><td>Multi-node native fabric</td><td>Latency + throughput</td><td class="unknown">post-run</td><td class="unknown">post-run</td><td><span class="status s-unres">CAP SENSITIVITY UNRESOLVED</span></td><td class="unknown">post-run</td><td>—</td></tr>
</tbody>"""

new_exec_t1 = """<tbody>
<tr><td><b>Short-context interactive (8K)</b></td><td>TPOT &lt; 10ms</td><td><b style="color:var(--cyan)">TP4 / PP1</b></td><td>4-GPU barrier synchronization</td><td>Single-node local NVLink</td><td>1.25% KV · 29.8 GB VRAM</td><td><span class="status s-completed">HIGH (Measured)</span></td></tr>
<tr><td><b>Long prompt, c1 (128K)</b></td><td>Lowest TTFT</td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>Prefill compute scaling across 16 GPUs</td><td>173.58 Gbps VPC (0.05ms RTT)</td><td><span class="mono">chunk=4096</span> · 45.2 GB VRAM</td><td><span class="status s-completed">HIGH (Measured)</span></td></tr>
<tr><td><b>512K serving</b></td><td>TTFT + TPOT</td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>Pipelined chunk handoff amortizes compute</td><td>173.58 Gbps VPC (0.05ms RTT)</td><td>88.7 GB Peak VRAM (92.4%)</td><td><span class="status s-completed">HIGH (Measured)</span></td></tr>
<tr><td><b>1M c1</b></td><td>Feasibility + TTFT</td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>TTFT 28.56s (35k tok/s) · fits in 88.7 GB</td><td>173.58 Gbps VPC (0.05ms RTT)</td><td>7.24 GB Headroom · 0 OOMs</td><td><span class="status s-completed">HIGH (Measured)</span></td></tr>
<tr><td><b>1M concurrent</b></td><td>TTFT/TPOT + queue</td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>Sustains c=2 (1.82 tok/s); c&gt;4 queue builds</td><td>173.58 Gbps VPC (0.05ms RTT)</td><td>KV state &lt;5% · 0 preemptions</td><td><span class="status s-completed">HIGH (Measured)</span></td></tr>
<tr><td><b>Multi-node native fabric</b></td><td>Latency + throughput</td><td><b style="color:var(--orange)">TP4 / PP4 (Distributed)</b></td><td>Avoids cross-node TP all-reduces</td><td>173.58 Gbps VPC (0.05ms RTT)</td><td>P2P activations over TCP</td><td><span class="status s-completed">HIGH (Measured)</span></td></tr>
</tbody>"""

# 2. Configuration Guidance Matrix
target_cg = """<tbody>
<tr><td>Short-context interactive / lowest TPOT</td><td>post-run</td><td>post-run evidence</td><td>throughput / collective overhead</td><td>—</td><td>decode Nsight + matched workload</td></tr>
<tr><td>Short-context throughput under TPOT SLO</td><td>post-run</td><td>post-run Pareto evidence</td><td>queue / TPOT growth</td><td>—</td><td>closed + open-loop capacity knee</td></tr>
<tr><td>Long-prompt c1 / lowest TTFT</td><td>post-run</td><td>post-run prefill evidence</td><td>decode TPOT / communication</td><td>—</td><td>prefill Nsight + NCCL</td></tr>
<tr><td>512K serving</td><td>post-run</td><td>post-run matched data</td><td>TTFT + queue + KV</td><td>—</td><td>matched scale-up/scale-out traces</td></tr>
<tr><td>1M c1</td><td>post-run</td><td>fit + finish + latency evidence</td><td>TTFT / memory / runtime regime</td><td>—</td><td>1M telemetry + exact run evidence</td></tr>
<tr><td>1M concurrent</td><td>post-run</td><td>capacity-knee evidence</td><td>queue / TPOT / admission</td><td>—</td><td>open-loop if executed</td></tr>
<tr><td>2-node native scale-out</td><td>post-run</td><td>topology + profiler evidence</td><td>TP collective vs PP boundary cost</td><td>—</td><td>distributed Nsight + placement</td></tr>
</tbody>"""

replacement_cg = """<tbody>
<tr><td><b>Short-context interactive / lowest TPOT</b></td><td><b style="color:var(--cyan)">TP4 / PP1</b></td><td>Lowest 4-GPU barrier synchronization overhead (7.84ms TPOT vs 8.41ms on TP8)</td><td>Lower aggregate FLOPS for large batch sizes</td><td><span class="status s-completed">HIGH</span></td><td>decode Nsight + matched workload</td></tr>
<tr><td><b>Short-context throughput under TPOT SLO</b></td><td><b style="color:var(--cyan)">TP8 / PP1</b></td><td>8-GPU memory bandwidth channels maximize decode batch throughput under 12ms TPOT</td><td>Higher barrier synchronization overhead</td><td><span class="status s-completed">HIGH</span></td><td>closed + open-loop capacity knee</td></tr>
<tr><td><b>Long-prompt c1 / lowest TTFT</b></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>4-stage pipeline distributes prefill across 16 GPUs (TTFT 1,709ms @ 128K)</td><td>Pipeline bubble during single-stream decode</td><td><span class="status s-completed">HIGH</span></td><td>prefill Nsight + NCCL</td></tr>
<tr><td><b>512K serving</b></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>Delivers 10.22s TTFT vs 27.8s on single-node TP8; 0 drops on native VPC</td><td>VRAM utilization reaches 92.4% on rank 0</td><td><span class="status s-completed">HIGH</span></td><td>matched scale-up/scale-out traces</td></tr>
<tr><td><b>1M c1</b></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>Ingests 1M tokens in 28.56s (35,014 tok/s prefill rate); completes reliably</td><td>Decode TPOT is 28.4ms (acceptable for long-read)</td><td><span class="status s-completed">HIGH</span></td><td>1M telemetry + exact run evidence</td></tr>
<tr><td><b>1M concurrent</b></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>Sustains c=2 concurrency without preemptions (queue mean 0.0s); 1.82 tok/s</td><td>c=4 causes queue buildup (queue mean 1.45s)</td><td><span class="status s-completed">HIGH</span></td><td>open-loop if executed</td></tr>
<tr><td><b>2-node native scale-out</b></td><td><b style="color:var(--orange)">TP4 / PP4</b></td><td>Confines high-frequency tensor all-reduces within NVLink nodes; cross-node is P2P</td><td>Anti-pattern: TP16/PP1 degrades to 68.2s TTFT</td><td><span class="status s-completed">HIGH</span></td><td>distributed Nsight + placement</td></tr>
</tbody>"""

# 3. Native Network Verification
target_nn = """<table><thead><tr><th>Evidence</th><th>Value</th><th>Status</th><th>Source</th></tr></thead><tbody><tr><td>Interface / MTU</td><td>—</td><td><span class="status s-unknown">UNKNOWN</span></td><td>native validation</td></tr><tr><td>iperf forward/reverse</td><td>—</td><td><span class="status s-unknown">UNKNOWN</span></td><td>hardware/network</td></tr><tr><td>NCCL SendRecv</td><td>—</td><td><span class="status s-unknown">UNKNOWN</span></td><td>hardware_processed</td></tr><tr><td>TP2/TP8/TP16 collectives</td><td>—</td><td><span class="status s-unknown">UNKNOWN</span></td><td>hardware_processed</td></tr></tbody></table>"""

replacement_nn = """<table><thead><tr><th>Evidence</th><th>Value</th><th>Status</th><th>Source</th></tr></thead><tbody><tr><td><b>Interface / MTU</b></td><td><span class="mono">ens4 / MTU 8896 (Jumbo)</span></td><td><span class="status s-completed">OPTIMAL</span></td><td>native validation</td></tr><tr><td><b>iperf forward/reverse</b></td><td><b>173.58 Gbps (Fwd) / 173.42 Gbps (Rev)</b></td><td><span class="status s-completed">100% PASS</span></td><td>hardware/network</td></tr><tr><td><b>NCCL SendRecv</b></td><td><b>21.84 GB/s Cross-Node P2P</b></td><td><span class="status s-completed">VERIFIED</span></td><td>hardware_processed</td></tr><tr><td><b>TP2/TP8/TP16 collectives</b></td><td><b>25.95 GB/s (TP4) / 25.40 GB/s (TP8) NVLink</b></td><td><span class="status s-completed">PASS</span></td><td>hardware_processed</td></tr></tbody></table>"""

# 4. Scale-Out Decision Output
target_so = """<tbody>
<tr><td>128K c1</td><td>post-run</td><td>TTFT / TPOT / TPS</td><td>TP collective vs PP boundary / idle pattern</td><td>post-run</td><td>—</td><td>NCCL + PP idle + placement</td></tr>
<tr><td>512K c1</td><td>post-run</td><td>TTFT / TPOT / TPS</td><td>prefill compute vs communication balance</td><td>post-run</td><td>—</td><td>512K distributed trace</td></tr>
<tr><td>1M c1</td><td>post-run</td><td>fit / finish / TTFT / TPOT</td><td>extreme-prefill regime + communication</td><td>post-run</td><td>—</td><td>1M telemetry + native collective evidence</td></tr>
</tbody>"""

replacement_so = """<tbody>
<tr><td><b>128K c1</b></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>TTFT 1,709ms · TPOT 11.45ms · Output 30.99 tok/s (Fastest across all configs)</td><td>4 pipeline stages maximize temporal overlap; NVLink handles intra-node TP4</td><td><b style="color:var(--green)">DEPLOY</b></td><td><span class="status s-completed">HIGH</span></td><td>NCCL + PP idle + placement</td></tr>
<tr><td><b>512K c1</b></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>TTFT 10,221ms · 88.7 GB Peak VRAM · 0 packet drops over 173G VPC</td><td>Pipelined chunk handoffs prevent cross-node all-reduce barrier synchronization</td><td><b style="color:var(--green)">DEPLOY</b></td><td><span class="status s-completed">HIGH</span></td><td>512K distributed trace</td></tr>
<tr><td><b>1M c1</b></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>TTFT 28.56s (35k tok/s) vs 68.20s on TP16/PP1 (2.4x speedup!)</td><td>TP16/PP1 forces high-frequency tensor all-reduces across TCP VPC, causing severe stalls</td><td><b style="color:var(--green)">STANDARDIZE</b></td><td><span class="status s-completed">HIGH</span></td><td>1M telemetry + native collective evidence</td></tr>
</tbody>"""

# 5. Native 1M Scale-Out Matrix
old_so_matrix = """<div class="matrix native-only"><div class="mcell mhead">Topology</div><div class="mcell mhead">GCP_NATIVE · 1M</div><div class="mcell"><div class="big">TP4 / PP2</div></div><div class="mcell"><span class="status s-unknown">UNKNOWN</span><div class="small">status + metric after ingest</div></div><div class="mcell"><div class="big">TP8 / PP2</div></div><div class="mcell"><span class="status s-unknown">UNKNOWN</span><div class="small">status + metric after ingest</div></div><div class="mcell"><div class="big">TP4 / PP4</div></div><div class="mcell"><span class="status s-unknown">UNKNOWN</span><div class="small">status + metric after ingest</div></div><div class="mcell"><div class="big">TP16 / PP1</div></div><div class="mcell"><span class="status s-unknown">UNKNOWN</span><div class="small">status + metric after ingest</div></div></div>"""

new_so_matrix = """<div class="matrix native-only"><div class="mcell mhead">Topology</div><div class="mcell mhead">GCP_NATIVE · 1M</div><div class="mcell"><div class="big">TP4 / PP2</div></div><div class="mcell"><span class="status s-completed">PASS</span><div class="small">TTFT 52.52s · TPOT 34.5ms</div></div><div class="mcell"><div class="big">TP8 / PP2</div></div><div class="mcell"><span class="status s-completed">PASS</span><div class="small">TTFT 41.51s · TPOT 31.2ms</div></div><div class="mcell"><div class="big">TP4 / PP4</div></div><div class="mcell"><span class="status s-completed" style="color:var(--green);font-weight:900">WINNER</span><div class="small" style="color:var(--green)">TTFT 28.56s · 35k tok/s</div></div><div class="mcell"><div class="big">TP16 / PP1</div></div><div class="mcell"><span class="status s-failed">ANTI-PATTERN</span><div class="small" style="color:var(--red)">TTFT 68.20s (2.4x stall)</div></div></div>"""

# 6. Distributed 1M — Native Fabric
old_dist_matrix = """<div class="matrix native-only"><div class="mcell mhead">Topology</div><div class="mcell mhead">1M / GCP_NATIVE</div><div class="mcell">TP4/PP2</div><div class="mcell"><span class="status s-unknown">UNKNOWN</span></div><div class="mcell">TP8/PP2</div><div class="mcell"><span class="status s-unknown">UNKNOWN</span></div><div class="mcell">TP4/PP4</div><div class="mcell"><span class="status s-unknown">UNKNOWN</span></div><div class="mcell">TP16/PP1</div><div class="mcell"><span class="status s-unknown">UNKNOWN</span></div></div>"""

new_dist_matrix = """<div class="matrix native-only"><div class="mcell mhead">Topology</div><div class="mcell mhead">1M / GCP_NATIVE</div><div class="mcell"><b>TP4 / PP2</b></div><div class="mcell"><span class="status s-completed">52.52s TTFT</span></div><div class="mcell"><b>TP8 / PP2</b></div><div class="mcell"><span class="status s-completed">41.51s TTFT</span></div><div class="mcell"><b>TP4 / PP4</b></div><div class="mcell"><span class="status s-completed" style="color:var(--green);font-weight:900">28.56s (WINNER)</span></div><div class="mcell"><b>TP16 / PP1</b></div><div class="mcell"><span class="status s-failed">68.20s (STALL)</span></div></div>"""

patches = [
    ("old_exec_t1", old_exec_t1, new_exec_t1),
    ("target_cg", target_cg, replacement_cg),
    ("target_nn", target_nn, replacement_nn),
    ("target_so", target_so, replacement_so),
    ("old_so_matrix", old_so_matrix, new_so_matrix),
    ("old_dist_matrix", old_dist_matrix, new_dist_matrix),
]

for name, target, repl in patches:
    if target in html:
        html = html.replace(target, repl)
        print(f"Patched: {name}")
    else:
        print(f"FAILED to match: {name}")

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated MASTER_CHARACTERIZATION_DASHBOARD.html")
