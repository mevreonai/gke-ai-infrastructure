#!/usr/bin/env python3
"""
apply_verification_fixes.py
Applies all 9 closure action items from Dashboard_Fix_Verification_v1.md
to fix MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html and sync to all dashboard copies.
"""

import sys, os, re, json, shutil

sys.stdout.reconfigure(encoding='utf-8')

MASTER_FILE = "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html"

with open(MASTER_FILE, "r", encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)
print(f"Loaded master dashboard: {orig_len} characters")

# =========================================================================
# 1. Replace 2.32x with 3.10x in KD#7 narrative, definitions box, and data
# =========================================================================
print("\n--- 1. Fixing 2.32x -> 3.10x in KD#7, definitions box, and data ---")

# In CANONICAL_DASHBOARD_DATA and EXECUTIVE_DISCOVERIES
content = content.replace(
    "increases by 2.32\\u00d7 (251.5ms \\u2192 583.9ms across 7040 traced AllReduce calls)",
    "increases by 3.10\\u00d7 (132.3ms \\u2192 409.9ms decode-only across 6,985 calls; 18.9 µs vs 58.7 µs/call)"
)
content = content.replace(
    '{"layer":"2. PyTorch Framework","metric":"Self CUDA allreduce Duration","tp4":"251.5 ms","tp8":"583.9 ms","delta":"+132.2% (2.32x, 7040 calls)"}',
    '{"layer":"2. PyTorch Framework","metric":"Self CUDA allreduce Duration (Decode)","tp4":"132.3 ms","tp8":"409.9 ms","delta":"+209.8% (3.10x, 6,985 calls; 18.9 vs 58.7 µs)"}'
)

# In Definitions Box
old_def_row = '<tr><td><b>TP8 Decode AllReduce Penalty</b></td><td>2.32× (7,040-call Self CUDA sum)</td><td>3.10× (Decode-only per call, 18.9 → 58.7 µs)</td><td>Dashboard sum includes the single 8K prefill step\'s 55 large AllReduces (119.2ms vs 174.0ms); decode-only per-call ratio is 3.10×.</td></tr>'
new_def_row = '<tr><td><b>TP8 Decode AllReduce Penalty</b></td><td>3.10× (Decode-only per call, 18.9 → 58.7 µs)</td><td>3.10× (Both agree on decode-only)</td><td>Dashboard and Brief aligned on 3.10× decode-only AllReduce growth across 6,985 calls (132.3 ms vs 409.9 ms); old 2.32× metric was contaminated by the single 8K prefill step\'s 55 large AllReduces.</td></tr>'
if old_def_row in content:
    content = content.replace(old_def_row, new_def_row)
    print("  ✓ Replaced definitions box TP8 decode row with 3.10x")
else:
    print("  ! Warning: old_def_row exact string not found, searching with regex...")
    content = re.sub(
        r'<tr><td><b>TP8 Decode AllReduce Penalty</b></td><td>2\.32×.*?</tr>',
        new_def_row,
        content,
        flags=re.DOTALL
    )

# In KD#7 explorer narrative
content = content.replace(
    "1.95× NCCL Barrier Latency → 2.32× PyTorch AR CUDA → +41.9% End-to-End TPOT",
    "1.95× NCCL Barrier Latency → 3.10× PyTorch AR CUDA → +41.9% End-to-End TPOT"
)
content = content.replace(
    '<span style="color:var(--dim)">7040 calls: 252ms → 584ms (2.32×)</span>',
    '<span style="color:var(--dim)">6985 decode calls: 132.3ms → 409.9ms (3.10×)</span>'
)
content = content.replace(
    "PyTorch Profiler AllReduce Self CUDA time is 2.32× higher (132.3 ms vs 409.9 ms decode-only across 6,985 calls (prefill step took 119.2ms vs 174.0ms in 55 calls))",
    "PyTorch Profiler AllReduce Self CUDA time is 3.10× higher (132.3 ms vs 409.9 ms decode-only across 6,985 calls; 18.9 µs vs 58.7 µs/call; prefill step took 119.2ms vs 174.0ms in 55 calls)"
)

# =========================================================================
# 2. Harmonize NUMA / Ring collective explanations & drop "cross-validated"
# =========================================================================
print("\n--- 2. Harmonizing NUMA / Ring collective explanations ---")

# Executive decision map:
content = content.replace(
    "4.475ms TPOT @ 8K c1 (vs 6.350ms on TP8); avoids cross-NUMA barrier delay",
    "4.475ms TPOT @ 8K c1 (vs 6.350ms on TP8); avoids 14-step ring AllReduce barrier delay (+17 µs ring; socket crossing ≤ 0.4 µs; thread pinning pending diagnostic)"
)

# TPOT card:
content = content.replace(
    "<div><b>Interpretation</b><span>Cross-validated: 4-GPU barrier avoids NUMA bridge crossing</span></div>",
    "<div><b>Interpretation</b><span>4-GPU barrier avoids 14-step ring AllReduce latency (+17 µs ring; socket crossing adds ≤ 0.4 µs; thread pinning pending diagnostic)</span></div>"
)

# KD#7 explorer:
content = content.replace(
    "Spanning all 8 GPUs incurs cross-NUMA socket collective synchronization overhead for token-by-token generation.",
    "Spanning all 8 GPUs incurs 14-step PCIe ring collective barrier overhead (+17 µs ring; socket crossing ≤ 0.4 µs; thread pinning pending diagnostic)."
)
content = content.replace(
    "prefer TP=4 as candidate deployment topology; TP=8 incurs cross-NUMA socket collective synchronization overhead.",
    "prefer TP=4 as candidate deployment topology; TP=8 incurs 14-step PCIe ring collective barrier overhead (+17 µs ring; socket crossing ≤ 0.4 µs; thread pinning pending diagnostic)."
)

# Reviewer-audit matrix:
content = content.replace(
    "NUMA &amp; cross-socket bus traversal identified as cause for TP8 slowdown.",
    "14-step ring latency identified as contributor (+17 µs ring; socket crossing adds ≤ 0.4 µs; thread pinning pending diagnostic)."
)

# Scale-Up tab NUMA wording:
content = content.replace(
    "Single-NUMA ring avoids cross-socket NUMA bridge AllReduce overhead (cross-validated contributor; timeline corroboration pending)",
    "Single-NUMA 4-GPU ring avoids 14-step ring AllReduce latency (+17 µs ring; socket crossing adds ≤ 0.4 µs; thread pinning pending diagnostic)"
)
content = content.replace(
    "Single-NUMA 4-GPU ring avoids dual-NUMA bridge traversal (cross-validated contributor to lower TP4 decode latency; timeline corroboration pending)",
    "Single-NUMA 4-GPU ring avoids 14-step ring AllReduce latency (contributor to lower TP4 decode latency; +17 µs ring; socket crossing adds ≤ 0.4 µs; thread pinning pending diagnostic)"
)

# Tooltip / chart texts:
content = content.replace(
    "Wider-TP AllReduce cost is a cross-validated contributor (+332.4ms crossing NUMA socket PCIe bridges).",
    "Wider-TP AllReduce cost is a measured contributor (14-step ring adds +17 µs/call; socket crossing adds ≤ 0.4 µs; CPU thread pinning pending diagnostic)."
)
content = content.replace(
    "TP8 decode GEMV is 66.9ms faster, but outweighed by the collective barrier delay crossing NUMA socket PCIe bridges.",
    "TP8 decode GEMV is 66.9ms faster, but outweighed by the 14-step collective ring barrier delay (+17 µs ring; socket crossing adds ≤ 0.4 µs; CPU thread pinning pending diagnostic)."
)
content = content.replace(
    "[Rank 0; Cross-NUMA Socket Traversal Overhead]",
    "[Rank 0; 14-Step Ring Collective Barrier Overhead]"
)

# =========================================================================
# 3. Profiler deployment rules row 1, Decision Claim Registry row 1, PROFILER_REGISTRY
# =========================================================================
print("\n--- 3. Updating Profiler deployment rules, claim registry, and PROFILER_REGISTRY ---")

# Profiler deployment rules row 1
old_dep_row_1 = """        <tr>
          <td><b style="color:var(--cyan)">TP4 Decode beats TP8 (-29.5% TPOT @ 8K c1)</b></td>
          <td>Canonical matched 8K context baseline: TP4 4.475ms vs TP8 6.350ms (TP4 ~29.5% lower TPOT). TP8 spans 2 NUMA sockets across host PCIe bridges; AllReduce ring barrier surges from 369.5μs to 446.5μs (+20.8%) which cancels out GEMV acceleration.</td>
          <td><b>Single-Node Interactive Serving:</b> For interactive decode serving: Co-locating TP4 workers within a single NUMA socket is a candidate optimization to evaluate; avoid spanning TP across sockets for short-context decode.</td>
          <td><span class="mono">tp4_decode/nsys_stats.txt</span> vs <span class="mono">tp8_decode/nsys_stats.txt</span></td>
        </tr>"""

new_dep_row_1 = """        <tr>
          <td><b style="color:var(--cyan)">TP4 Decode beats TP8 (-29.5% TPOT @ 8K c1)</b></td>
          <td>Canonical matched 8K context baseline: TP4 4.475ms vs TP8 6.350ms (TP4 ~29.5% lower TPOT). Under graphs-on serving, TP8 14-step ring AllReduce barrier latency increases to 58.7 µs vs 18.9 µs on TP4 (3.23 ms vs 1.04 ms collective budget; +17 µs from longer ring, socket crossing adds ≤ 0.4 µs), canceling out GEMV speedup.</td>
          <td><b>Single-Node Interactive Serving:</b> For interactive decode serving: Co-locating TP4 workers within a single socket/ring avoids 14-step ring AllReduce latency; CPU thread pinning (numactl/taskset) across dual sockets is pending diagnostic.</td>
          <td><span class="mono">profiles_torch_single_node/ (graphs-on torch profiles)</span></td>
        </tr>"""

if old_dep_row_1 in content:
    content = content.replace(old_dep_row_1, new_dep_row_1)
    print("  ✓ Replaced Profiler deployment rules row 1")
else:
    print("  ! Warning: old_dep_row_1 exact string not found, using regex...")
    content = re.sub(
        r'<tr>\s*<td><b style="color:var\(--cyan\)">TP4 Decode beats TP8 \(-29\.5% TPOT @ 8K c1\)</b></td>.*?</tr>',
        new_dep_row_1,
        content,
        flags=re.DOTALL
    )

# Decision Claim Registry row 1
old_claim_row_1 = '<tr><td>Interactive scale-up candidate</td><td>TP4/PP1: 4.475ms TPOT @ 8K c1</td><td>Sub-10ms decode; 86.3% aggregate GPU kernel-work share in exact TP4 decode profile</td><td>TP4/PP1 for interactive 8K workloads</td><td><span class="status s-completed">DIRECT_MEASURED</span></td><td>tp4_8192_c1 + nsys_stats.txt</td><td><span class="status s-completed">RESOLVED</span></td></tr>'
new_claim_row_1 = '<tr><td>Interactive scale-up candidate</td><td>TP4/PP1: 4.475ms TPOT @ 8K c1</td><td>Sub-10ms decode; graphs-on budget confirms 23% AR collective share (1.04 of 4.47 ms; weights stream at 46% mem BW; eager nsys capture 86.3% noted as reference)</td><td>TP4/PP1 for interactive 8K workloads</td><td><span class="status s-completed">DIRECT_MEASURED</span></td><td>tp4_8192_c1 + torch_graphs_profile</td><td><span class="status s-completed">RESOLVED</span></td></tr>'
if old_claim_row_1 in content:
    content = content.replace(old_claim_row_1, new_claim_row_1)
    print("  ✓ Replaced Decision Claim Registry row 1")
else:
    print("  ! Warning: old_claim_row_1 exact string not found, using regex...")
    content = re.sub(
        r'<tr><td>Interactive scale-up candidate</td>.*?</tr>',
        new_claim_row_1,
        content
    )

# Update PROFILER_REGISTRY with mode fields and verified numbers
old_pr_002 = """    'PR-002': {
        evidence_id: 'PR-002',
        profile_id: 'PR-002',
        case: 'tp4_decode_8k',
        bench: '8k_decode_rank0',
        network_provenance: 'SINGLE_NODE_LOCAL',
        node: 'Node 0',
        rank: 0,
        phase: 'Decode (8K context)',
        metric: 'nccl:all_reduce Self CUDA Time',
        unit: 'ms',
        value: 251.5,
        evidence_class: 'PROFILER_NSIGHT_TORCH',
        artifact_path: 'results_V8_runs(3)/hardware_processed/nsight_tp4_decode/cuda_gpu_kern_sum.csv',
        aggregation_rule: 'Rank 0 aggregate Self CUDA time; 7040 AllReduce invocations average 35.7 μs per collective across 7040 traced AllReduce calls',
        kernels: { 'NCCL AllReduce': '86.3% (251.5 ms)', 'cublasGemv': '171.2 ms', 'Fused MoE': '120.4 ms', 'PagedAttention': '42.1 ms', 'RMSNorm': '34.8 ms' },
        observation: 'TP4 Decode 8K spends 251.5 ms in nccl:all_reduce (86.3% of GPU kernel work) with intra-socket PCIe bus bandwidth.'
    },"""

new_pr_002 = """    'PR-002': {
        evidence_id: 'PR-002',
        profile_id: 'PR-002',
        case: 'tp4_decode_8k',
        bench: '8k_decode_rank0',
        network_provenance: 'SINGLE_NODE_LOCAL',
        node: 'Node 0',
        rank: 0,
        phase: 'Decode (8K context)',
        mode: 'graphs-on (serving decode; eager capture 251.5 ms shown for reference)',
        metric: 'nccl:all_reduce Self CUDA Time (Graphs-ON)',
        unit: 'ms',
        value: 1.04,
        evidence_class: 'PROFILER_NSIGHT_TORCH',
        artifact_path: 'results_real_data/profiles_torch_single_node/tp4_8k_decode/torch_profile.json',
        aggregation_rule: 'Graphs-on serving profile: 18.9 µs/call across 55 decode AllReduce calls (1.04 ms of 4.47 ms TPOT budget, 23% collective share). Eager Nsight baseline: 251.5 ms across 7,040 calls.',
        kernels: { 'NCCL AllReduce (Graphs-ON)': '23% (1.04 ms)', 'Weight Streaming (46% BW)': '0.79 TB/s', 'GEMV/MoE Compute': '51% (1.94 ms)', 'Eager Nsight AR (Ref)': '251.5 ms' },
        observation: 'Under graphs-on serving, TP4 8K decode spends 1.04 ms in AllReduce (23% of 4.47 ms TPOT, 18.9 µs/call), with weights streaming at 46% memory bandwidth (0.79 TB/s).'
    },"""

old_pr_003 = """    'PR-003': {
        evidence_id: 'PR-003',
        profile_id: 'PR-003',
        case: 'tp8_decode_8k',
        bench: '8k_decode_rank0',
        network_provenance: 'SINGLE_NODE_LOCAL',
        node: 'Node 0',
        rank: 0,
        phase: 'Decode (8K context)',
        metric: 'nccl:all_reduce Self CUDA Time',
        unit: 'ms',
        value: 583.9,
        evidence_class: 'PROFILER_NSIGHT_TORCH',
        artifact_path: 'results_V8_runs(3)/hardware_processed/nsight_tp8_decode/cuda_gpu_kern_sum.csv',
        aggregation_rule: 'Rank 0 aggregate Self CUDA time; 7040 AllReduce invocations across NUMA socket PCIe bridges (+332.4 ms higher collective time on TP8 vs TP4)',
        kernels: { 'NCCL AllReduce': '89.1% (583.9 ms)', 'cublasGemv': '89.2 ms', 'Fused MoE': '118.2 ms', 'PagedAttention': '38.6 ms', 'RMSNorm': '29.5 ms' },
        observation: 'TP8 Decode 8K spends 583.9 ms in nccl:all_reduce (+132.2% vs TP4), consistent with cross-NUMA socket traversal overhead (contributor corroborated by timeline traces).'
    },"""

new_pr_003 = """    'PR-003': {
        evidence_id: 'PR-003',
        profile_id: 'PR-003',
        case: 'tp8_decode_8k',
        bench: '8k_decode_rank0',
        network_provenance: 'SINGLE_NODE_LOCAL',
        node: 'Node 0',
        rank: 0,
        phase: 'Decode (8K context)',
        mode: 'graphs-on (serving decode; eager capture 583.9 ms shown for reference)',
        metric: 'nccl:all_reduce Self CUDA Time (Graphs-ON)',
        unit: 'ms',
        value: 3.23,
        evidence_class: 'PROFILER_NSIGHT_TORCH',
        artifact_path: 'results_real_data/profiles_torch_single_node/tp8_8k_decode/torch_profile.json',
        aggregation_rule: 'Graphs-on serving profile: 58.7 µs/call across 55 decode AllReduce calls (3.23 ms of 6.35 ms TPOT budget, 51% collective share). Eager Nsight baseline: 583.9 ms across 7,040 calls. 14-step ring adds +17 µs; socket crossing adds ≤ 0.4 µs; thread pinning pending.',
        kernels: { 'NCCL AllReduce (Graphs-ON)': '51% (3.23 ms)', 'Weight Streaming': '46% BW', 'GEMV/MoE Compute': '49%', 'Eager Nsight AR (Ref)': '583.9 ms' },
        observation: 'Under graphs-on serving, TP8 8K decode collective budget surges to 3.23 ms (51% of 6.35 ms TPOT, 58.7 µs/call). 14-step ring adds +17 µs/call vs TP4, canceling GEMV speedup.'
    },"""

if old_pr_002 in content:
    content = content.replace(old_pr_002, new_pr_002)
    print("  ✓ Updated PROFILER_REGISTRY PR-002")
else:
    print("  ! Warning: PR-002 exact block not matched")

if old_pr_003 in content:
    content = content.replace(old_pr_003, new_pr_003)
    print("  ✓ Updated PROFILER_REGISTRY PR-003")
else:
    print("  ! Warning: PR-003 exact block not matched")

# Update PR-001 mode
content = content.replace(
    "phase: 'Prefill (128K context)',\n        metric: 'Kernel Composition',",
    "phase: 'Prefill (128K context)',\n        mode: 'eager (--enforce-eager; prefill)',\n        metric: 'Kernel Composition',"
)

# Update PR-004 rank and aggregation_rule
content = content.replace(
    "rank: 'Selected Rank 0 (Multi-Rank Mean: 77.6%)',\n        phase: 'Prefill (128K context)',",
    "rank: 'Selected Rank 0 (12 usable of 16 ranks; mean: 77.6%)',\n        phase: 'Prefill (128K context)',\n        mode: 'eager (prefill)',"
)
content = content.replace(
    "aggregation_rule: 'Selected Node 0 Rank 0: 76.2%; multi-rank mean across all 16 ranks: 77.6% (range 74.8% - 79.5%)',",
    "aggregation_rule: 'Selected Node 0 Rank 0: 76.2%; multi-rank mean across 12 usable ranks: 77.6% (range 74.8% - 79.5%; 4 rank traces unexportable)',"
)

# Update PR-005 per-stage handoff
content = content.replace(
    "phase: 'Prefill (128K context)',\n        metric: 'P2P SendRecv vs AllReduce',",
    "phase: 'Prefill (128K context)',\n        mode: 'eager (prefill)',\n        metric: 'P2P SendRecv vs AllReduce',"
)
content = content.replace(
    "aggregation_rule: 'Pipeline Stage 0 / Rank 0: 40.0% intra-node TP AllReduce, 8.3% inter-node P2P SendRecv; Stage 3 P2P: 8.1%',",
    "aggregation_rule: 'Pipeline Stage 0 / Rank 0: 40.0% intra-node TP AllReduce, 8.3% inter-node P2P SendRecv handoff (Stage 0 only; Stages 1–3 wait 17–22%)',",
)
content = content.replace(
    "kernels: { 'Intra-Node TP AllReduce': '40.0%', 'FlashAttention': '22.8%', 'Fused MoE': '13.2%', 'Inter-Node P2P SendRecv': '8.3%', 'GEMM': '8.5%' },",
    "kernels: { 'Intra-Node TP AllReduce': '40.0%', 'FlashAttention': '22.8%', 'Fused MoE': '13.2%', 'Inter-Node P2P SendRecv (Stage 0)': '8.3%', 'P2P Wait (Stages 1-3)': '17-22%', 'GEMM': '8.5%' },"
)
content = content.replace(
    "observation: 'TP4/PP4 restricts cross-node communication to point-to-point SendRecv (8.3%), keeping TP AllReduce local to PCIe.'",
    "observation: 'TP4/PP4 restricts cross-node communication to point-to-point SendRecv (8.3% of Stage 0 work; downstream stages 1–3 wait 17–22%), keeping TP AllReduce local to intra-node PCIe.'"
)

# Update PR-006 mode
content = content.replace(
    "phase: 'Long Prefill (512K context)',\n        metric: 'FlashAttention vs MoE Scaling',",
    "phase: 'Long Prefill (512K context)',\n        mode: 'eager (prefill)',\n        metric: 'FlashAttention vs MoE Scaling',"
)

# Update PR-007 Stage 0 vs Stages 1-3 FlashAttention
content = content.replace(
    "phase: 'Prefill (512K context)',\n        metric: 'Kernel Composition (512K)',",
    "phase: 'Prefill (512K context)',\n        mode: 'eager (prefill)',\n        metric: 'Kernel Composition (512K)',"
)
content = content.replace(
    "rank: 'Stage 0 / Rank 0',\n        phase: 'Prefill (512K context)',",
    "rank: 'Stage 0 / Rank 0 (Stages 1–3 FlashAttention: 44.8%; Stage 0: 22%)',\n        phase: 'Prefill (512K context)',"
)
content = content.replace(
    "aggregation_rule: 'Pipeline Stage 0 / Rank 0: 44.8% FlashAttention, 35.6% intra-node TP AllReduce, 6.2% Fused MoE, 5.2% P2P SendRecv',",
    "aggregation_rule: 'Pipeline Stage 0 / Rank 0: 22% FlashAttention, 35.6% intra-node TP AllReduce, 6.2% Fused MoE, 5.2% P2P SendRecv (Stages 1–3 full-attention layers carry 44.8% FlashAttention)',"
)
content = content.replace(
    "kernels: { 'FlashAttention': '44.8%', 'Intra-Node TP AllReduce': '35.6%', 'Fused MoE Routing/Experts': '6.2%', 'Inter-Node P2P SendRecv': '5.2%', 'GEMM/Linear': '5.1%', 'KDA Recurrent State': '2.7%' },",
    "kernels: { 'Stage 0 FlashAttention': '22.0%', 'Stages 1-3 FlashAttention': '44.8%', 'Intra-Node TP AllReduce': '35.6%', 'Fused MoE Routing/Experts': '6.2%', 'Inter-Node P2P SendRecv': '5.2%' },"
)

# Also update modal drawer to display `datum.mode` when present
content = content.replace(
    "badgesHtml += `<span class=\"badge b-purple\">${datum.phase || ''}</span>`;",
    "badgesHtml += `<span class=\"badge b-purple\">${datum.phase || ''}</span>`;\n        if (datum.mode) badgesHtml += `<span class=\"badge b-amber\" style=\"font-weight:600\">Mode: ${datum.mode}</span>`;"
)

# =========================================================================
# 4. KD#3: Replace 2.18x sentence and map row with reproducible numbers
# =========================================================================
print("\n--- 4. KD#3: Fixing 2.18x NCCL scaling claim & 60s map row ---")

# SVG 60-second map
content = content.replace(
    '<text x="216" y="102" fill="#facc15" font-size="8.5">NCCL 2.18&times; (p≈0.56)</text>',
    '<text x="216" y="102" fill="#facc15" font-size="8.5">SendRecv 4.5&times; · AllReduce 2.7&times;</text>'
)

# Table row at pos 432451
content = content.replace(
    '<tr><td><b>NCCL</b></td><td>~1.63 s</td><td>~3.56 s</td><td>~2.18×</td><td>~0.56</td></tr>',
    '<tr><td><b>NCCL (SendRecv / AR)</b></td><td>SendRecv + AR</td><td>nsys eager</td><td><b>SendRecv 4.5× · AR 2.7×</b></td><td>excluding start-up broadcast</td></tr>'
)

# CANONICAL_DASHBOARD_DATA / EXECUTIVE_DISCOVERIES
content = content.replace(
    '{"component":"NCCL Collectives","t_128k":"~1.63 s","t_512k":"~3.56 s","growth":"~2.18x","exponent":"p \\u2248 0.56"}',
    '{"component":"NCCL Collectives (SendRecv 4.5× / AR 2.7×)","t_128k":"128K nsys","t_512k":"512K nsys","growth":"4.5x / 2.7x","exponent":"nsys eager (excl broadcast)"}'
)

# =========================================================================
# 5. Port tab fixes into KD Explorer Pages (KD 1, 2, 3, 4, 5, 6, 8, 9, 10)
# =========================================================================
print("\n--- 5. Updating KD_PAGES_DATA in master HTML ---")

pos_kd = content.find('window.KD_PAGES_DATA = [')
end_kd = content.find('];\n', pos_kd)
if end_kd == -1:
    end_kd = content.find('];', pos_kd)

kd_json_str = content[pos_kd + len('window.KD_PAGES_DATA = '):end_kd+1]
kd_data = json.loads(kd_json_str)

for p in kd_data:
    pid = p.get('id')
    if pid == 1:
        p['takeaways'] = [
            "Fabric sensitivity varies dramatically by topology: scale-out design cannot be treated as a single uniform class.",
            "TP16/PP1 is severely exposed to transport degradation because AllReduce collectives are serialized over the cross-node fabric on every layer (+188.69s tax @ 1M; SendRecv ceiling drops 7.11 → 2.04 GB/s with 16 KiB latency rising to 227–290 µs across 37.7 MB per call).",
            "TP4/PP4 is far less sensitive in the same 1M cap condition (+3.91% TTFT) because cross-node boundaries use point-to-point Send/Recv pipelining.",
            "Small negative TP8/PP2 delta (-0.10% @ 1M) sits well within the repeatability noise floor (0.03–0.5% at c1 across eight replicate pairs; within 1.9–3.9% under load).",
            "NCCL_NET Transport Boundary: PP point-to-point boundaries operate without penalty down to 20G cap; cross-node TP should not be deployed across VPC without NVLink."
        ]
        p['confidence_note'] = "HIGH for topology divergence. Cross-node AllReduce sends 37.7 MB per call across VPC; SendRecv ceiling drops from 7.11 GB/s (native) to 2.04 GB/s (20G cap) with 16 KiB latency rising to 227–290 µs (see Scale-Out α-β panel)."
    elif pid == 2:
        p['takeaways'] = [
            "At 8K, c1→c4 produces +120.82% throughput with only 0.027s queue delay (healthy concurrent batching).",
            "Under concurrency, prefills are serialized sequentially one full prefill apart due to vLLM admission limit (default max_num_partial_prefills=1): at 1M c4, first tokens arrive sequentially at 93.5s, 185.4s, 277.3s, 368.9s (peak_running = 2, peak_waiting = 3); at 512K c4, arrivals are 32.0s, 63.9s, 95.6s, 127.2s.",
            "Queue residence accounts for 134.43s (97.5% of added TTFT), verified across both TP4 and TP8 replications; stall budget card confirms 25% → 57% → 71% stall share under load.",
            "Peak KV at 1M c4 remains only 15.51% with 0 preemptions: 'fits in memory' does not equal production capacity."
        ]
        p['confidence_note'] = "HIGH for queue dominance and sequential prefill serialization. Verified by arrival ladder timestamps and vLLM admission state limits (max_num_partial_prefills=1)."
    elif pid == 3:
        p['takeaways'] = [
            "Subsystem resource pressure changes sharply with context: full-attention grouped GPU work grows ~15.7× from 128K to 512K (empirical p≈1.99 over measured range).",
            "KDA and MoE scale linearly (~3.95× and ~3.80× for 4× context growth). Reproducible NCCL scaling (nsys only, eager mode, start-up broadcast excluded): inter-node SendRecv grows 4.5× (including pipeline boundary waits) and intra-node AllReduce grows 2.7× (neither is sub-linear).",
            "Do not state 'Full Attention (O(N²))' as a proven campaign complexity law; report empirical p≈1.99 over the measured range.",
            "Aggregate GPU work ≠ exclusive request wall-clock critical path; pipeline stages introduce concurrency overlap."
        ]
        p['confidence_note'] = "HIGH for attention expansion. NCCL scaling verified from usable nsys prefill exports (excluding start-up broadcast; eager mode only)."
        # Update hero metrics on KD#3
        for stat in p.get('hero_stats', []):
            if '2.18' in str(stat.get('val', '')):
                stat['val'] = '4.5× / 2.7×'
                stat['label'] = 'SendRecv / AllReduce'
                stat['sub'] = 'SendRecv 4.5× · AllReduce 2.7× (nsys eager)'
        # Update table rows if present
        if 'table_card' in p and 'rows' in p['table_card']:
            for r in p['table_card']['rows']:
                if 'NCCL Transport' in str(r[0]):
                    r[0] = 'NCCL Transport (SendRecv 4.5× · AR 2.7×)'
                    r[3] = "<span style='color:#4ade80;font-weight:700'>4.5× / 2.7×</span>"
                    r[4] = "SendRecv 4.5× · AR 2.7× (nsys eager; start-up broadcast excluded)"
    elif pid == 4:
        p['takeaways'] = [
            "Cold TTFT scales super-linearly (empirical fit p=1.4427, R²=0.9979) while repeat-hit median scales near-linearly (p=1.0013, R²=0.9935).",
            "Do not describe this as 'quadratic to constant'; the empirical fit proves near-linear scaling (p≈1.00) with context length.",
            "Exact request hit counts: 128K: 7 of 7 repeats hit (87.33%); 512K: 2 of 3 hit (49.98% — 4th request missed due to token boundary shift at 524,545 vs 524,544 tokens); 1M: 2 of 3 hit (49.97% — 2nd request missed with identical 1,000,000 tokens).",
            "Treat repeated-prefix traffic as a distinct workload class; evaluate routing or dedicated-pool strategies against actual reuse, residency and eviction behavior."
        ]
        p['confidence_note'] = "HIGH for empirical fit and exact per-request hit/miss boundaries."
    elif pid == 5:
        p['takeaways'] = [
            "At 8K, the server achieves 3.359 req/s; at 128K, it achieves 0.185 req/s (an apparent 18.20× collapse in raw request capacity).",
            "When normalized to accepted prompt tokens, the server processes 27.51k tok/s at 8K vs 24.19k tok/s at 128K (only a 1.14× difference in prompt token processing).",
            "Under SLO gating (p95 TPOT ≤ 100 ms, ≥ 90% requests served), usable capacity is 1.8× (SLO-conditioned knee).",
            "Do not use requests/sec to size mixed-prompt clusters; use prompt-token arrival rate for admission control.",
            "Client concurrency was capped at --max-concurrency 64 / 32, which acts as a closed loop above the knee; 8K TTFT shows non-monotonicity above the knee (979 → 784 → 826 ms)."
        ]
        p['confidence_note'] = "HIGH for token-throughput preservation; client concurrency capped at 64/32 beyond the capacity knee."
    elif pid == 6:
        p['takeaways'] = [
            "At 8K/128K, the added TP synchronization cost is consistent with offsetting the compute benefit of wider TP (+18.5% and +6.1% TTFT penalty).",
            "At 512K/1M, measured E2E TTFT shows the compute-side benefit of wider TP outweighing the additional TP overhead in these runs (-12.0% and -19.9% TTFT).",
            "At 1M across 4 scale-out + 2 scale-up topologies, the TP4 pipeline family (TP4/PP1 → TP4/PP2 → TP4/PP4) forms the optimal Pareto frontier.",
            "TP8/PP2 achieves 41.52s TTFT but consumes 664.24 GPU-s (GPU-seconds = TTFT × total GPUs allocated; dominated by TP4/PP4 at 28.57s and 457.09 GPU-s).",
            "Energy per 1K tokens (§4.6): TP4/PP4 consumes 143.1 J/1K tokens (310 W) vs TP16 134.8 J/1K tokens (150 W) and TP4/PP2 179.7 J/1K tokens (268 W)."
        ]
        p['confidence_note'] = "HIGH across the 4 scale-out + 2 scale-up topologies evaluated at 1M (TP4/PP1, TP8/PP1 single-node; TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1 multi-node)."
    elif pid == 7:
        p['confidence_note'] = "HIGH for decode communication overhead. 14-step ring AllReduce adds +17 µs/call; socket crossing adds ≤ 0.4 µs (nvbandwidth); CPU thread pinning (numactl/taskset) across dual sockets is pending diagnostic."
    elif pid == 8:
        p['takeaways'] = [
            "Increasing chunked prefill from 4K to 16K delivers growing leverage with context: -16.5% @ 128K, -24.4% @ 512K, and -27.1% @ 1M in two-step progression (-23.6% from 4K→8K, -4.6% from 8K→16K).",
            "16K chunk size Pareto-dominates 8K and 4K under concurrency (TTFT drops −27.1% and TPOT improves 141.3 → 119.3 → 105.1 ms).",
            "Tuning max_num_seqs across 4, 8, and 16 produces a flat 0.049% spread (232.342s vs 232.364s vs 232.250s) because peak running sequences reached 2 (configured ceiling was non-binding).",
            "The binding constraint under concurrency is serial prefill chunk queueing, not memory capacity."
        ]
        p['confidence_note'] = "HIGH for chunk size leverage and max_num_seqs non-binding ceiling."
    elif pid == 9:
        p['takeaways'] = [
            "TP16/PP1 reports significantly higher GPU utilization across all context lengths (63.2% vs 35.2% @ 128K; 80.6% vs 62.8% @ 1M).",
            "Yet TP16/PP1 delivers 2.39× to 3.75× worse user-visible latency across the same exact hardware.",
            "GPU utilization measures device activity, which can include communication kernels; it is not a direct measure of useful-token efficiency.",
            "Power consumption (§4.6) reveals true work: TP16 at 80.6% utilization draws only 225 W (stalled waiting on VPC), whereas TP4/PP4 at 62.8% draws 310 W (continuous computation).",
            "The captured TP16 profile was captured under --enforce-eager mode; large aggregate AllReduce kernel work reflects eager prefill communication, not serving critical path."
        ]
        p['confidence_note'] = "HIGH. Telemetry sourced from nvidia-smi background sampler (1 Hz sampling across node 0 and node 1 GPUs; not Prometheus GPU SM utilization)."
    elif pid == 10:
        p['takeaways'] = [
            "Reported KV percentage falls sharply with pipeline parallelism: TP4/PP1 12.29% → TP4/PP2 5.91% → TP4/PP4 2.75%.",
            "Empirical KV pool size in tokens (requested_input_tokens / peak_kv_usage): TP4/PP1: 8.14M, TP8/PP1: 8.21M, TP16/PP1: 8.24M, TP4/PP2: 16.9M, TP8/PP2: 17.0M, TP4/PP4: 36.4M tokens.",
            "MLA latent KV cache (8,064 B/token) is replicated across all TP ranks; TP width adds no token capacity, while PP depth directly multiplies KV pool (headroom = ~10% vLLM reserve).",
            "Physical device memory remains high across all topologies: 88.83 GiB peak telemetry on a raw-reported ~95.59 GiB device (6.76 to 8.88 GiB headroom; do not label memory as saturated or exhausted)."
        ]
        p['confidence_note'] = "HIGH for empirical KV pool size and token headroom; vLLM reserves ~10% headroom by default (gpu_memory_utilization = 0.90)."

new_kd_json_str = json.dumps(kd_data, indent=2, ensure_ascii=False)
content = content[:pos_kd + len('window.KD_PAGES_DATA = ')] + new_kd_json_str + content[end_kd+1:]
print("  ✓ Updated window.KD_PAGES_DATA with all per-tab findings and correct numbers")

# =========================================================================
# 6. Coverage Matrix: set status from usable exports & qualify 14/22 tiles
# =========================================================================
print("\n--- 6. Profiler Coverage Matrix & 14/22 Tile Qualifiers ---")

# Replace Executive Tile
content = content.replace(
    '<div class="k-label">Distributed Profile Coverage</div><div class="k-value" style="color:var(--amber)">14 / 22 COMPLETE</div><div class="k-note">11 Native + 3 configured-100G complete · 8 expected points incomplete/missing</div>',
    '<div class="k-label">Distributed Profile Coverage</div><div class="k-value" style="color:var(--amber)">14 / 22 CAPTURED</div><div class="k-note">7 with usable exports (all prefill); decode deferred · 8 missing</div>'
)

# Replace Key Finds / Profiler Coverage Header Badges
content = content.replace(
    '<span class="status s-completed">14 / 22 COMPLETE</span><div class="small" style="font-size:7.5px;color:var(--muted)">11 Native + 3 configured-100G complete; 8 expected points incomplete/missing</div>',
    '<span class="status s-completed">14 / 22 CAPTURED</span><div class="small" style="font-size:7.5px;color:var(--muted)">7 usable exports (all prefill); decode deferred · 8 missing</div>'
)
content = content.replace(
    '<span class="badge b-cyan"><span class="dot"></span>14 / 22 COMPLETE</span>',
    '<span class="badge b-cyan"><span class="dot"></span>14 / 22 CAPTURED (7 Usable Exports — All Prefill; Decode Deferred)</span>'
)

# Coverage matrix table rows for 0-2 rank rows
content = content.replace(
    '<tr><td><span class="mono">tp4_pp4_decode_8k</span></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export incomplete (2/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>',
    '<tr><td><span class="mono">tp4_pp4_decode_8k</span></td><td><b style="color:var(--purple)">TP4 / PP4</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-deferred">DECODE DEFERRED (2/16 usable)</span></td><td>Eager-mode capture; per-worker nsys export incomplete (2/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>'
)
content = content.replace(
    '<tr><td><span class="mono">tp8_pp2_decode_8k</span></td><td><b style="color:var(--amber)">TP8 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export failed (0/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>',
    '<tr><td><span class="mono">tp8_pp2_decode_8k</span></td><td><b style="color:var(--amber)">TP8 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-deferred">DECODE DEFERRED (0/16 usable)</span></td><td>Eager-mode capture; per-worker nsys export failed (0/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>'
)
content = content.replace(
    '<tr><td><span class="mono">tp4_pp2_decode_8k</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export failed (0/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>',
    '<tr><td><span class="mono">tp4_pp2_decode_8k</span></td><td><b style="color:var(--cyan)">TP4 / PP2</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-deferred">DECODE DEFERRED (0/16 usable)</span></td><td>Eager-mode capture; per-worker nsys export failed (0/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>'
)
content = content.replace(
    '<tr><td><span class="mono">tp16_pp1_decode_8k</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">COMPLETE</span></td><td>Eager-mode capture; per-worker nsys export failed (0/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>',
    '<tr><td><span class="mono">tp16_pp1_decode_8k</span></td><td><b style="color:var(--red)">TP16 / PP1</b></td><td>GCP_NATIVE</td><td>8K Decode (c=1)</td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-completed">8 / 8</span></td><td><span class="status s-deferred">DECODE DEFERRED (0/16 usable)</span></td><td>Eager-mode capture; per-worker nsys export failed (0/16 usable ranks). Decode analysis referenced from graphs-on torch profiles.</td></tr>'
)

# Update tp4_pp4_prefill_128k finding text in coverage matrix
content = content.replace(
    'SendRecv P2P activation handoff is 8.3% of stage work, decoupling pipeline stages from cross-node tensor-parallel collective synchronization',
    'SendRecv P2P handoff is 8.3% of Stage 0 work (Stages 1–3 wait 17–22%), decoupling intra-node TP AllReduce from cross-node synchronization'
)

# =========================================================================
# 7. Remove ~0.1ms RTT (8 cells) & Polish Scale-Out Tab
# =========================================================================
print("\n--- 7. Removing ~0.1ms RTT, defining Verdict & Resilience Thresholds ---")

# Replace all ~0.1ms RTT and 0.1ms RTT in text
content = content.replace("173.58 Gbps VPC (~0.1ms RTT)", "173.58 Gbps VPC (MTU 1460, ens3)")
content = content.replace("173.6 Gbps (~0.1ms RTT)", "173.6 Gbps (MTU 1460)")
content = content.replace("~0.1ms RTT, ", "")
content = content.replace(", ~0.1ms RTT", "")

# In Scale-Out Decision Matrix table header: define Verdict & label c1
content = content.replace(
    '<div class="card-sub" id="scaleout-matrix-sub">Interactive status, latency &amp; throughput dynamically updated by Network, Context &amp; Metric selection</div>',
    '<div class="card-sub" id="scaleout-matrix-sub">Interactive status, latency &amp; throughput dynamically updated. <b>Verdict Rules:</b> RECOMMENDED = lowest measured latency / highest TPS; VIABLE = benchmark completed successfully under c=1 single-stream test without OOM; HIGH CAP SENSITIVITY = &gt;50% TTFT penalty under network cap. All metrics measured under c=1 (single-stream / zero queue).</div>'
)

content = content.replace(
    '<thead><tr><th>Topology</th><th>Context</th><th>TTFT</th><th>TPOT</th><th>Output TPS</th><th>Req TPS</th><th>KV %</th><th>Queue</th><th>Verdict</th></tr></thead>',
    '<thead><tr><th>Topology</th><th>Context</th><th>TTFT</th><th>TPOT</th><th>Output TPS (c1)</th><th>Req TPS (c1)</th><th>KV %</th><th>Queue (c1)</th><th>Verdict</th></tr></thead>'
)

# In Scale-Out Network Sensitivity table: print the threshold rule
content = content.replace(
    '<div class="card-sub">Measured impact of network bandwidth caps across 4 distributed topologies &amp; context lengths</div>',
    '<div class="card-sub">Measured impact of network bandwidth caps across 4 distributed topologies &amp; context lengths. <b>Sensitivity Classification Rule:</b> HIGH NETWORK RESILIENCE = &lt;15% TTFT delta on 20G cap vs native; MODERATE = 15–50% delta; HIGH CAP SENSITIVITY / EXPOSED = &gt;50% delta (e.g. TP16 +276.7% @ 1M).</div>'
)

# =========================================================================
# 8. Scheduler K3 hedge, K6 units, K9 tokens axis, regime map 8K row, Knee
# =========================================================================
print("\n--- 8. Scheduler & Executive Tab Refinements ---")

# Scheduler K3 Card hedge:
content = content.replace(
    'is consistent with distributing active KV allocation across 4 sequential stages (exact allocator sharding is not directly measured), reducing 1M context peak KV cache usage to just <b>2.748%</b>',
    'is verified by empirical token pool scaling: TP4/PP1 8.14M, TP8/PP1 8.21M, TP16/PP1 8.24M, TP4/PP2 16.9M, TP8/PP2 17.0M, TP4/PP4 36.4M tokens (MLA latent KV cache 8,064 B/token replicated across TP ranks; headroom = 10% vLLM reserve), reducing 1M context peak KV cache usage to just <b>2.748%</b>'
)
content = content.replace(
    'cause": "LOW-MEDIUM for exact allocator/sharding interpretation"',
    'cause": "HIGH for empirical KV pool size and token headroom"'
)

# Scale-out table queue units: 0.00001s / 0.00002s -> 0.012ms / 0.020ms
content = content.replace('<td>0.00001s</td>', '<td>0.012ms</td>')
content = content.replace('<td>0.00002s</td>', '<td>0.020ms</td>')

# Executive regime map 8K row:
content = content.replace(
    '<td><span class="status s-completed">Memory BW / Sync</span></td>',
    '<td><span class="status s-completed">kernel-time + collectives (46 % of memory BW)</span></td>'
)

# The knee contradiction (§3.5):
content = content.replace(
    'At the 8K knee, 71% of all decode waiting is another request\'s prefill chunk!',
    'At full load (1.00×), 71% of all decode waiting is another request\'s prefill chunk! (Knee occurs at 0.75× SLO / 0.90× slope)'
)

# Scheduler K9 KV Chart secondary axis / subtitle note:
content = content.replace(
    '<div class="card-sub">Series = exact TP/PP · context · concurrency · KV dtype; show GB only from verified byte fields</div><div class="chart"><canvas id="chart_sched_kv"></canvas></div>',
    '<div class="card-sub">Peak KV % &amp; Equivalent Token Capacity (8,064 B/tok MLA latent KV: TP4/PP1 8.14M, PP2 16.9M, PP4 36.4M tokens · 10% vLLM reserve) · Series = exact TP/PP · context · concurrency</div><div class="chart"><canvas id="chart_sched_kv"></canvas></div>'
)

# =========================================================================
# 9. Evidence Tab & Readiness Audit Panel (§4.16 / §2.8)
# =========================================================================
print("\n--- 9. Adding Cluster & Campaign Readiness Audit Panel & Ledger Polish ---")

readiness_panel_html = """
<div class="card mb8" id="cluster-readiness-panel">
  <div class="header-row">
    <div>
      <div class="card-title">🛡️ Cluster, Stack &amp; Campaign Readiness Audit (§4.16 / §2.8)</div>
      <div class="card-sub">Full hardware, software, profiler export provenance, known validator defects &amp; NOT_CAPTURED reconciliation</div>
    </div>
    <span class="badge b-green"><span class="dot"></span>AUDIT VERIFIED</span>
  </div>
  <div class="grid3 mb8">
    <div class="mini-panel" style="background:rgba(66,201,255,0.04);border:1px solid rgba(66,201,255,0.2);padding:10px;border-radius:6px;">
      <div style="font-weight:700;color:var(--cyan);font-size:11px;margin-bottom:4px">Software Stack Provenance</div>
      <div style="font-size:9.5px;line-height:1.5;color:var(--text)">
        <b>vLLM Version:</b> <code>0.6.2</code><br/>
        <b>PyTorch:</b> <code>2.4.0+cu124</code><br/>
        <b>CUDA Toolkit:</b> <code>12.4</code> (Driver 550.54.15)<br/>
        <b>NCCL:</b> <code>2.20.5</code> (AWS-OFI-NCCL / GCP VPC tuned)<br/>
        <b>Ray Core:</b> <code>2.37.0</code> (All 12 worker audits clean)
      </div>
    </div>
    <div class="mini-panel" style="background:rgba(255,200,87,0.04);border:1px solid rgba(255,200,87,0.2);padding:10px;border-radius:6px;">
      <div style="font-weight:700;color:var(--amber);font-size:11px;margin-bottom:4px">Validator Defect Disclosures</div>
      <div style="font-size:9.5px;line-height:1.5;color:var(--text)">
        <b>1. Ray NCCL Policy Validator Bug:</b> Tile previously showed INCOMPLETE due to a count validator defect; raw check confirms <code>ray_worker_audits ok: true</code> on 12/12 workers (CLEAN).<br/>
        <b>2. FINAL_VALIDATION Duplicate Keys:</b> Manifest validator emitted duplicate metric keys across multi-node runs; reconciled against raw JSON logs.
      </div>
    </div>
    <div class="mini-panel" style="background:rgba(179,136,255,0.04);border:1px solid rgba(179,136,255,0.2);padding:10px;border-radius:6px;">
      <div style="font-weight:700;color:var(--purple);font-size:11px;margin-bottom:4px">NOT_CAPTURED Reconciliation</div>
      <div style="font-size:9.5px;line-height:1.5;color:var(--text)">
        <b>E2E Ledger:</b> 7 runs marked GUARDED_NOT_RUN (safety-gated configurations not executed).<br/>
        <b>Profiler Matrix:</b> 5 distributed points NOT_CAPTURED (workload horizons where per-worker nsys daemon was skipped); 3 native incomplete; 14 captured (7 with usable rank exports, all prefill; decode deferred).
      </div>
    </div>
  </div>
</div>
"""

if 'id="cluster-readiness-panel"' not in content:
    pos_ledger = content.find('id="perf-evidence-table-container"')
    if pos_ledger != -1:
        content = content[:pos_ledger] + readiness_panel_html + "\n" + content[pos_ledger:]
        print("  ✓ Added Cluster & Campaign Readiness Audit Panel before evidence ledger")

# Update evidence table headers to add Warmups, Load Time, and Usable Exports
content = content.replace(
    '<th>Runtime Knobs</th>\n<th>Network Fabric</th>\n<th>Sample Reliability</th>',
    '<th>Runtime Knobs</th>\n<th>Warmup / Prompts</th>\n<th>Network Fabric</th>\n<th>Cold Load</th>\n<th>Sample Reliability</th>'
)

# Update EV rows to include Warmup and Cold Load info in ledger
content = re.sub(
    r'(<td class="mono" style="font-size:7px;color:var\(--dim\)">b=8192<br/>s=32<br/>BF16·pfx:OFF</td>)\s*(<td><span class="badge b-cyan" style="font-size:7px">Local PCIe</span>)',
    r'\1\n<td class="mono" style="font-size:7px;color:var(--text)">w=1 · 32 req</td>\n\2',
    content
)

# Write updated file
with open(MASTER_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nSuccessfully wrote updated master dashboard to {MASTER_FILE} ({len(content)} characters, delta: {len(content) - orig_len})")

# Write out MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html
TARGET_OCT4 = "MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html"
shutil.copy2(MASTER_FILE, TARGET_OCT4)
print(f"Created/updated {TARGET_OCT4}")

# Sync to all other 7 identical copies in workspace
SYNC_TARGETS = [
    "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_WITH_KEYFINDS.html",
    "MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html",
    "v8_full_results/dashboards/v4_dashboard/index.html",
    "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html",
    "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html",
    "v8_full_results/release_specs/index.html",
    "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html",
    "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html",
]

for tgt in SYNC_TARGETS:
    if os.path.exists(tgt):
        shutil.copy2(MASTER_FILE, tgt)
        print(f"Synced to {tgt}")
