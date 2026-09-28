#!/usr/bin/env python3
"""
apply_26sep_1am_closure_fixes.py
Implements all deterministic closure fixes identified in V8_V4_26SEP_1AM_FINAL_CLOSURE_REAUDIT.md:
- P0: Prefix evidence IDs in exactMap, chart_long_prefix, and Top #4 discovery (EV-053, EV-054, EV-075)
- P0: Top #1 profiler topology mismatch (PR-005, PR-007 for TP4/PP4 matched 128K/512K profiles)
- P1: Top 10 backing discovery objects alignment (confidence, decision, boundaries, headroom)
- P1: Scale-Up C2 Decision Output row wording
- P1: Long Context FP8 chart quantitative initialization removal (clean NOT_RUN guardrail)
- P1: Profiler PR-002 and PR-003 backing wording (across 22 layers, barrier, cross-NUMA traversal)
- P1: Evidence Decision Claim Registry row (PP avoids cross-node AllReduce)
- Sync all 4 dashboard HTML targets and canonical JSON files
"""

import os
import sys
import json
import re
import subprocess

sys.stdout.reconfigure(encoding='utf-8')
print("Starting 26 Sept 1am Closure Re-Audit Fixes...")

# ---------------------------------------------------------------------------
# 1. Update build_canonical_executive_data.py
# ---------------------------------------------------------------------------
builder_path = "build_canonical_executive_data.py"
with open(builder_path, "r", encoding="utf-8") as f:
    bcode = f.read()

# --- TOP 1: Fix profiler topology mismatch & confidence ---
# Top 1 drilldown: PR-005 (TP4/PP4 128k) and PR-007 (TP4/PP4 512k), removing TP16 profiles (PR-004, PR-006)
bcode = bcode.replace(
    '"causal_confidence": "HIGH",\n        "evidence_class": ["MEASURED", "DERIVED", "MODELED_INTERPOLATION"],',
    '"causal_confidence": "MED-HIGH",\n        "evidence_class": ["MEASURED", "DERIVED", "MODELED_INTERPOLATION"],'
)
bcode = bcode.replace(
    '"drilldown": ["EV-082", "EV-083", "EV-084", "PR-001", "PR-004", "PR-006"]',
    '"drilldown": ["EV-082", "EV-083", "EV-084", "PR-005", "PR-007"]'
)

# --- TOP 2: Backing decision_changed alignment ---
bcode = bcode.replace(
    '"decision_changed": "Do not provision distributed inference from NIC/iperf capability alone. Topology determines how much transport degradation becomes exposed to user-visible TTFT. Disallow cross-node TP16 over standard VPC; standardize on TP4/PP4 for multi-node serving."',
    '"decision_changed": "Do not provision distributed inference from NIC/iperf capability alone. Topology determines how much transport degradation becomes exposed to user-visible TTFT. For bandwidth-constrained networks, candidate topology favors TP4/PP4, but topology selection should be evaluated per workload SLO rather than applying a universal constraint."'
)

# --- TOP 3: Backing decision_changed alignment ---
bcode = bcode.replace(
    '"decision_changed": "Enforce admission control on queue/TTFT SLO thresholds, NOT on KV cache exhaustion. At 1M context, KV capacity remains ~84% free while latency SLOs are destroyed 26× over."',
    '"decision_changed": "Enforce admission control on queue/TTFT SLO thresholds, NOT on reported KV cache exhaustion. At 1M context, reported KV utilization remains ~15.5% while TTFT and TPOT degrade sharply; evaluate admission gating at candidate knees depending on target SLO."'
)

# --- TOP 4: Prefix evidence IDs (EV-053, EV-054, EV-075) & decision_changed ---
bcode = bcode.replace(
    '"drilldown": ["EV-073", "EV-074", "EV-075"]',
    '"drilldown": ["EV-053", "EV-054", "EV-075"]'
)
bcode = bcode.replace(
    '"decision_changed": "Deploy prefix caching for agents, long-document Q&A, and few-shot workloads. Size KV cache specifically to prevent prefix eviction on primary shared system prompts."',
    '"decision_changed": "Prefix reuse should be treated as a workload-routing/caching lever; as a candidate deployment experiment, evaluate routing multi-turn chat and RAG to cache-warm replicas with sticky sessions."'
)

# --- TOP 5: Confidence (MED-HIGH / LOW-MED) and 16x prompt length ratio ---
bcode = bcode.replace(
    '"top_id": 5,\n        "hero_order": None,\n        "title": "Prompt-Token Admission Fingerprint",\n        "sub_title": "System Absorbs Prompt Tokens at a Finite Rate Regardless of Request Sizing",\n        "one_line_finding": "At open-loop saturation, the engine admits ~24K–27K prompt tokens/s across both 8K and 128K context regimes, dictating admission control rules.",\n        "large_number": "~24.2K vs ~27.4K Prompt Tok/s",\n        "large_number_caption": "Open-Loop Saturation Ingestion Ceiling",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "HIGH",',
    '"top_id": 5,\n        "hero_order": None,\n        "title": "Prompt-Token Admission Fingerprint",\n        "sub_title": "System Absorbs Prompt Tokens at a Finite Rate Regardless of Request Sizing",\n        "one_line_finding": "At open-loop saturation, the engine admits ~24K–27K prompt tokens/s across both 8K and 128K context regimes, dictating admission control rules.",\n        "large_number": "~24.2K vs ~27.4K Prompt Tok/s",\n        "large_number_caption": "Open-Loop Saturation Ingestion Ceiling",\n        "evidence_confidence": "MED-HIGH",\n        "causal_confidence": "LOW-MED",'
)
bcode = bcode.replace(
    'Admitting ten 128K requests generates 160× the prefill token stress of ten 8K requests.',
    'Admitting ten 128K requests generates 16× the prefill token stress of ten 8K requests (16× prompt length ratio; candidate deployment takeaway: capacity planning should normalize demand into prompt tokens/s).'
)

# --- TOP 6: Causal confidence & decision alignment ---
bcode = bcode.replace(
    '"top_id": 6,\n        "hero_order": None,\n        "title": "Parallelism Directional Elasticity",\n        "sub_title": "Context Length Inverts TP/PP Scaling Leverage and GPU-Second Occupancy",\n        "one_line_finding": "Doubling TP at 8K increases latency (η = -0.245, negative elasticity). Doubling PP at 1M slashes TTFT near-linearly (η = +0.879), establishing the optimal GPU-second frontier.",\n        "large_number": "η = -0.245 (8K TP) vs η = +0.879 (1M PP)",\n        "large_number_caption": "Scaling Elasticity Coefficient Crossover",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "HIGH",',
    '"top_id": 6,\n        "hero_order": None,\n        "title": "Parallelism Directional Elasticity",\n        "sub_title": "Context Length Inverts TP/PP Scaling Leverage and GPU-Second Occupancy",\n        "one_line_finding": "Doubling TP at 8K increases latency (η = -0.245, negative elasticity). Doubling PP at 1M slashes TTFT near-linearly (η = +0.879), establishing the optimal GPU-second frontier.",\n        "large_number": "η = -0.245 (8K TP) vs η = +0.879 (1M PP)",\n        "large_number_caption": "Scaling Elasticity Coefficient Crossover",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "MED-HIGH",'
)
bcode = bcode.replace(
    '"decision_changed": "Deploy TP4 for short-context instances to maximize single-node efficiency. Scale out via Pipeline Parallelism (PP4) rather than wide Tensor Parallelism (TP16) for extreme 1M contexts."',
    '"decision_changed": "Allocate additional GPUs along the parallelism dimension that has positive measured elasticity for the workload/SLO, and expose the GPU-second trade-off instead of declaring a universal topology winner."'
)

# --- TOP 7: Causal confidence & 7040 traced AllReduce calls ---
bcode = bcode.replace(
    '"top_id": 7,\n        "hero_order": None,\n        "title": "TP Decode Evidence Chain",\n        "sub_title": "4-Layer Root-Cause Corroboration of Tensor-Parallel Decode Degradation",\n        "one_line_finding": "At 8K decode, TP8 increases token latency by +41.9% over TP4 (4.48ms → 6.35ms). Corroborated across 4 instrumentation layers from raw NCCL up to E2E TPOT.",\n        "large_number": "+41.9% Token Latency on TP8 (4.48ms → 6.35ms)",\n        "large_number_caption": "8K Decode TPOT Degradation from AllReduce Bus Contention",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "HIGH",',
    '"top_id": 7,\n        "hero_order": None,\n        "title": "TP Decode Evidence Chain",\n        "sub_title": "4-Layer Root-Cause Corroboration of Tensor-Parallel Decode Degradation",\n        "one_line_finding": "At 8K decode, TP8 increases token latency by +41.9% over TP4 (4.48ms → 6.35ms). Corroborated across 4 instrumentation layers from raw NCCL up to E2E TPOT.",\n        "large_number": "+41.9% Token Latency on TP8 (4.48ms → 6.35ms)",\n        "large_number_caption": "8K Decode TPOT Degradation from AllReduce Bus Contention",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "MED-HIGH",'
)
bcode = bcode.replace(
    '2) PyTorch self-CUDA allreduce time increases by 2.32× (251.5ms → 583.9ms across 7040 calls);',
    '2) PyTorch self-CUDA allreduce time increases by 2.32× (251.5ms → 583.9ms across 7040 traced AllReduce calls);'
)

# --- TOP 8: Causal confidence, scoped decision, boundary ---
bcode = bcode.replace(
    '"top_id": 8,\n        "hero_order": None,\n        "title": "Runtime-Knob Derivative Fingerprint",\n        "sub_title": "Inert Knobs (max_num_seqs) vs High-Leverage Knobs (chunk size) Characterization",\n        "one_line_finding": "Some runtime knobs are completely non-binding (<0.05% change for max_num_seqs) while others have huge leverage: increasing chunk size from 4K to 16K cuts 1M TTFT by 27.1%.",\n        "large_number": "<0.05% (max_seqs) vs -27.1% (chunk size) TTFT",\n        "large_number_caption": "Runtime Knob Sensitivity Spread @ 1M",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "HIGH",',
    '"top_id": 8,\n        "hero_order": None,\n        "title": "Runtime-Knob Derivative Fingerprint",\n        "sub_title": "Inert Knobs (max_num_seqs) vs High-Leverage Knobs (chunk size) Characterization",\n        "one_line_finding": "Some runtime knobs are completely non-binding (<0.05% change for max_num_seqs) while others have huge leverage: increasing chunk size from 4K to 16K cuts 1M TTFT by 27.1%.",\n        "large_number": "<0.05% (max_seqs) vs -27.1% (chunk size) TTFT",\n        "large_number_caption": "Runtime Knob Sensitivity Spread @ 1M",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "MED-HIGH",'
)
bcode = bcode.replace(
    '"boundary": "16K chunk size requires sufficient activation VRAM. In constrained memory configs, 16K chunks increase risk of Out-Of-Memory during high concurrent prefill.",',
    '"boundary": "16K chunk size was evaluated for single-stream prefill (c=1); multi-tenant concurrent prefill dynamics require further instrumentation.",'
)
bcode = bcode.replace(
    '"decision_changed": "Do not spend engineering time tuning max_num_seqs when operating below concurrency saturation. Focus tuning effort entirely on max_num_batched_tokens and chunk size allocation."',
    '"decision_changed": "Candidate operational focus: evaluate tuning chunked prefill / token budget (which reduced measured TTFT by ~27.1%) while max_num_seqs spread was <0.05% across tested points; tune chunk budget according to workload SLO."'
)

# --- TOP 9: Causal confidence, softened spin-wait observation, decision ---
bcode = bcode.replace(
    '"top_id": 9,\n        "hero_order": None,\n        "title": "Busy GPU != Efficient Serving",\n        "sub_title": "High GPU Utilization Masks Severe Cross-Node Barrier Synchronization Spinning",\n        "one_line_finding": "High GPU utilization is not proof of efficient compute: TP16 shows ~80.6% utilization but takes 68.2s TTFT at 1M, while TP4/PP4 shows ~62.8% utilization and delivers 28.6s TTFT (2.39× faster).",\n        "large_number": "80.6% Util (68.2s) vs 62.8% Util (28.6s)",\n        "large_number_caption": "TP16/PP1 vs TP4/PP4 Utilization vs Latency Paradox @ 1M",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "HIGH",',
    '"top_id": 9,\n        "hero_order": None,\n        "title": "Busy GPU != Efficient Serving",\n        "sub_title": "High GPU Utilization Masks Severe Cross-Node Barrier Synchronization Spinning",\n        "one_line_finding": "High GPU utilization is not proof of efficient compute: TP16 shows ~80.6% utilization but takes 68.2s TTFT at 1M, while TP4/PP4 shows ~62.8% utilization and delivers 28.6s TTFT (2.39× faster).",\n        "large_number": "80.6% Util (68.2s) vs 62.8% Util (28.6s)",\n        "large_number_caption": "TP16/PP1 vs TP4/PP4 Utilization vs Latency Paradox @ 1M",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "MEDIUM",'
)
bcode = bcode.replace(
    'Nsight profiling reveals that for TP16, over 40% of the active GPU cycles are spent in active CUDA spin-wait loops inside NCCL AllReduce barriers awaiting cross-node network packets.',
    'Profiler traces show TP16 incurs significant collective wait and barrier communication overhead across nodes during distributed execution.'
)
bcode = bcode.replace(
    '"decision_changed": "Never use nvidia-smi GPU utilization as an operational health metric or auto-scaling trigger for distributed LLM inference. Rely exclusively on E2E TTFT, TPOT, and queue residency."',
    '"decision_changed": "Hardware GPU utilization alone does not indicate productive token generation efficiency; cross-validate throughput and TTFT alongside device telemetry. In collective-heavy topologies, high device utilization can correlate with communication wait cycles."'
)

# --- TOP 10: Remove unsupported 7.86 GiB margin / 8.19% headroom; retain measured KV% and 88.83 GiB ---
bcode = bcode.replace(
    '"fit_quality": "Reported KV% = 2.75% (PP divides KV), actual physical VRAM = 88.83 GiB (7.86 GiB margin)",',
    '"fit_quality": "Reported peak KV% = 2.75% (PP divides KV per stage), peak physical GPU memory allocation = ~88.83 GiB",'
)
bcode = bcode.replace(
    '"one_line_finding": "On TP4/PP4 at 1M, reported peak KV cache usage is only ~2.75% (PP divides KV per stage), yet physical VRAM allocation is ~88.83 GiB out of 96.0 GiB (~7.86 GiB actual headroom).",',
    '"one_line_finding": "On TP4/PP4 at 1M, reported peak KV cache usage is only ~2.75% (PP divides KV per stage), yet physical GPU memory allocation peaks at ~88.83 GiB.",'
)
bcode = bcode.replace(
    '"large_number_caption": "Reported KV Headroom vs Physical VRAM Reality @ 1M",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "HIGH",',
    '"large_number_caption": "Reported KV Headroom vs Physical VRAM Telemetry @ 1M",\n        "evidence_confidence": "HIGH",\n        "causal_confidence": "MED-HIGH",'
)
bcode = bcode.replace(
    'leaving only ~7.86 GiB of true headroom.',
    'leaving limited margin before memory exhaustion.'
)
bcode = bcode.replace(
    '"boundary": "Exact activation and runtime memory split cannot be fully separated without CUDA allocator instrumentation.",',
    '"boundary": "Exact activation, runtime, and buffer memory breakdown cannot be fully separated without CUDA allocator instrumentation; true headroom depends on driver and allocator reservations.",'
)

with open(builder_path, "w", encoding="utf-8") as f:
    f.write(bcode)

print("Updated build_canonical_executive_data.py with all Section 11 alignments.")

# ---------------------------------------------------------------------------
# 2. Run build_canonical_executive_data.py to regenerate canonical JSONs
# ---------------------------------------------------------------------------
res = subprocess.run([sys.executable, builder_path], capture_output=True, text=True)
if res.returncode != 0:
    print("Error executing build_canonical_executive_data.py:", res.stderr)
    sys.exit(1)
print("Regenerated DASHBOARD_CANONICAL_DATA.json and EXECUTIVE_DISCOVERIES.json")

with open("v8_full_results/dashboards/v4_dashboard/EXECUTIVE_DISCOVERIES.json", "r", encoding="utf-8") as f:
    updated_discoveries = json.load(f)

# Update V2 files
with open("v8_full_results/dashboards/v4_dashboard/EXECUTIVE_DISCOVERIES_V2.json", "w", encoding="utf-8") as f:
    json.dump(updated_discoveries, f, indent=2)

with open("v8_full_results/results/real_data/final_validation/EXECUTIVE_DISCOVERIES_V2.json", "w", encoding="utf-8") as f:
    json.dump(updated_discoveries, f, indent=2)

print("Updated EXECUTIVE_DISCOVERIES_V2.json copies.")

# ---------------------------------------------------------------------------
# 3. Update patch_profiler_registry.py with PR-007 and wording fixes
# ---------------------------------------------------------------------------
patcher_path = "patch_profiler_registry.py"
with open(patcher_path, "r", encoding="utf-8") as f:
    pcode = f.read()

# PR-002: remove "across 22 layers"
pcode = pcode.replace(
    "across 22 layers, average 35.7 μs per collective",
    "average 35.7 μs per collective across 7040 traced AllReduce calls"
)
# PR-003: remove "barrier overhead" and "due to cross-NUMA"
pcode = pcode.replace(
    "(+332.4 ms barrier overhead vs TP4)",
    "(+332.4 ms higher collective time on TP8 vs TP4)"
)
pcode = pcode.replace(
    "due to cross-NUMA socket PCIe bridge traversal.",
    "consistent with cross-NUMA socket traversal overhead (contributor corroborated by timeline traces)."
)

# Add PR-007 to patch_profiler_registry.py if not present
if "'PR-007'" not in pcode:
    pr007_def = """    'PR-007': {
        evidence_id: 'PR-007',
        profile_id: 'PR-007',
        case: 'tp4_pp4_dist',
        bench: '512k_prefill_multinode',
        network_provenance: 'GCP_NATIVE',
        node: 'Node 0 (Stage 0)',
        rank: 'Stage 0 / Rank 0',
        phase: 'Prefill (512K context)',
        metric: 'Kernel Composition (512K)',
        unit: '% aggregate GPU kernel work',
        value: 44.8,
        evidence_class: 'PROFILER_DISTRIBUTED',
        artifact_path: 'profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/PROFILE_VALIDATION.json',
        aggregation_rule: 'Pipeline Stage 0 / Rank 0: 44.8% FlashAttention, 35.6% intra-node TP AllReduce, 6.2% Fused MoE, 5.2% P2P SendRecv',
        kernels: { 'FlashAttention': '44.8%', 'Intra-Node TP AllReduce': '35.6%', 'Fused MoE Routing/Experts': '6.2%', 'Inter-Node P2P SendRecv': '5.2%', 'GEMM/Linear': '5.1%', 'KDA Recurrent State': '2.7%' },
        observation: 'TP4/PP4 512K prefill profile shows FlashAttention work expanding to 44.8% of aggregate GPU kernel work, validating the quadratic attention shift.'
    }
};"""
    pcode = pcode.replace("    }\n};", "    },\n" + pr007_def)
    pcode = pcode.replace(
        "'tp16_pp1_dist_long_prefill_512k': 'PR-006',",
        "'tp16_pp1_dist_long_prefill_512k': 'PR-006',\n            'tp4_pp4_dist 512k profile': 'PR-007',\n            'tp4_pp4_dist_long_prefill_512k': 'PR-007',"
    )

with open(patcher_path, "w", encoding="utf-8") as f:
    f.write(pcode)

print("Updated patch_profiler_registry.py with PR-007 and qualified phrasing.")

# ---------------------------------------------------------------------------
# 4. Update the 4 Dashboard HTML files
# ---------------------------------------------------------------------------
html_targets = [
    "v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html",
    "v8_full_results/dashboards/v4_dashboard/index.html",
    "v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html",
    "v8_full_results/release_specs/index.html"
]

updated_discoveries_json_str = json.dumps(updated_discoveries, separators=(',', ':'))

for target in html_targets:
    with open(target, "r", encoding="utf-8") as f:
        html = f.read()

    # A. In-place exactMap prefix fixes (EV-053 and EV-054)
    html = html.replace(
        "'tp4_prefix128k': 'EV-073',",
        "'tp4_prefix128k': 'EV-053',"
    )
    html = html.replace(
        "'tp4_prefix512k': 'EV-074',",
        "'tp4_prefix512k': 'EV-054',"
    )

    # B. chart_long_prefix click handler fixes (EV-053, EV-054, EV-075)
    html = html.replace(
        "const ids = ['EV-073', 'EV-074', 'EV-075'];",
        "const ids = ['EV-053', 'EV-054', 'EV-075'];"
    )

    # C. Scale-Up C2 Decision Output row (NUMA qualification)
    html = html.replace(
        "<td>Single-NUMA ring avoids dual-NUMA bridge AllReduce penalty</td><td>Deploy TP4 / PP1 for lowest interactive turn latency</td>",
        "<td>Single-NUMA ring avoids cross-socket NUMA bridge AllReduce overhead (cross-validated contributor; timeline corroboration pending)</td><td>Candidate deployment recommendation: prefer TP4 / PP1 for lowest interactive turn latency</td>"
    )

    # D. Evidence Decision Claim Registry row (PP AllReduce softening)
    html = html.replace(
        "<td>Pipeline parallelism avoids cross-node AllReduce collective stalls in tested conditions</td>",
        "<td>Pipeline communication structure exhibits lower measured network sensitivity than cross-node AllReduce in tested VPC conditions</td>"
    )

    # E. Profiler Registry PR-002 and PR-003 phrasing updates
    html = html.replace(
        "across 22 layers, average 35.7 μs per collective",
        "average 35.7 μs per collective across 7040 traced AllReduce calls"
    )
    html = html.replace(
        "(+332.4 ms barrier overhead vs TP4)",
        "(+332.4 ms higher collective time on TP8 vs TP4)"
    )
    html = html.replace(
        "TP8 Decode 8K spends 583.9 ms in nccl:all_reduce (+132.2% vs TP4) due to cross-NUMA socket PCIe bridge traversal.",
        "TP8 Decode 8K spends 583.9 ms in nccl:all_reduce (+132.2% vs TP4), consistent with cross-NUMA socket traversal overhead (contributor corroborated by timeline traces)."
    )

    # F. Add PR-007 to PROFILER_REGISTRY in HTML if not present
    if "'PR-007': {" not in html:
        pr006_end = "observation: 'At 512K context, FlashAttention expands from 11.2% to 45.1% of GPU kernel work, driving quadratic prefill expansion.'\n    }\n};"
        pr007_block = """observation: 'At 512K context, FlashAttention expands from 11.2% to 45.1% of GPU kernel work, driving quadratic prefill expansion.'
    },
    'PR-007': {
        evidence_id: 'PR-007',
        profile_id: 'PR-007',
        case: 'tp4_pp4_dist',
        bench: '512k_prefill_multinode',
        network_provenance: 'GCP_NATIVE',
        node: 'Node 0 (Stage 0)',
        rank: 'Stage 0 / Rank 0',
        phase: 'Prefill (512K context)',
        metric: 'Kernel Composition (512K)',
        unit: '% aggregate GPU kernel work',
        value: 44.8,
        evidence_class: 'PROFILER_DISTRIBUTED',
        artifact_path: 'profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/PROFILE_VALIDATION.json',
        aggregation_rule: 'Pipeline Stage 0 / Rank 0: 44.8% FlashAttention, 35.6% intra-node TP AllReduce, 6.2% Fused MoE, 5.2% P2P SendRecv',
        kernels: { 'FlashAttention': '44.8%', 'Intra-Node TP AllReduce': '35.6%', 'Fused MoE Routing/Experts': '6.2%', 'Inter-Node P2P SendRecv': '5.2%', 'GEMM/Linear': '5.1%', 'KDA Recurrent State': '2.7%' },
        observation: 'TP4/PP4 512K prefill profile shows FlashAttention work expanding to 44.8% of aggregate GPU kernel work, validating the quadratic attention shift.'
    }
};"""
        if pr006_end in html:
            html = html.replace(pr006_end, pr007_block)
            print(f"Added PR-007 to PROFILER_REGISTRY in {target}")
        else:
            print(f"WARNING: pr006_end not matched in {target}")

        # Also add alias to profilerMap
        html = html.replace(
            "'tp16_pp1_dist_long_prefill_512k': 'PR-006',",
            "'tp16_pp1_dist_long_prefill_512k': 'PR-006',\n            'tp4_pp4_dist 512k profile': 'PR-007',\n            'tp4_pp4_dist_long_prefill_512k': 'PR-007',"
        )

    # G. Long Context FP8 chart quantitative bar initialization removal
    # Replace quantitative chart_long_fp8 initialization with guarded non-comparative status
    old_fp8_js = """    // Chart 14: FP8 KV Cache Status
    safeInitChart('chart_long_fp8', {
        type: 'bar',
        data: {
            labels: ['BF16 KV (Measured: 88.7 GiB)', 'FP8 KV: NOT_RUN (Guarded)'],
            datasets: [
                { label: 'Peak VRAM (GB)', data: [88.7, null], backgroundColor: ['rgba(57,217,138,0.7)', 'rgba(255,200,87,0.3)'] }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { max: 100, title: { display: true, text: 'VRAM Usage (GB)' } } } }
    });"""

    new_fp8_js = """    // Chart 14: FP8 KV Cache Status — GUARDED NOT_RUN / Intentionally excluded
    // Guardrail: No quantitative comparison initialized; runtime acceptance was unvalidated (all verified runs used BF16)."""

    html = html.replace(old_fp8_js, new_fp8_js)

    # H. Re-inject window.EXECUTIVE_DISCOVERIES
    m = html.find("window.EXECUTIVE_DISCOVERIES = [")
    if m != -1:
        end = html.find("];", m)
        if end != -1:
            html = html[:m] + "window.EXECUTIVE_DISCOVERIES = " + updated_discoveries_json_str + html[end+1:]
            print(f"Re-injected window.EXECUTIVE_DISCOVERIES in {target}")

    # I. Also update embedded CANONICAL_DASHBOARD_DATA
    with open("v8_full_results/dashboards/v4_dashboard/DASHBOARD_CANONICAL_DATA.json", "r", encoding="utf-8") as f:
        can_data = json.load(f)
    can_json_str = json.dumps(can_data, separators=(',', ':'))

    cm = html.find("window.CANONICAL_DASHBOARD_DATA = {")
    if cm != -1:
        cend = html.find("};\n", cm)
        if cend != -1:
            html = html[:cm] + "window.CANONICAL_DASHBOARD_DATA = " + can_json_str + html[cend+1:]
            print(f"Re-injected window.CANONICAL_DASHBOARD_DATA in {target}")

    with open(target, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Successfully wrote updates to {target}")

print("\nAll closure fixes applied successfully across all targets!")
