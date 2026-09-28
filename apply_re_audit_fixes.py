import os
import sys
import json
import re

print("Starting deterministic re-audit closure script...")

# ---------------------------------------------------------------------------
# 1. Update build_canonical_executive_data.py
# ---------------------------------------------------------------------------
builder_path = "build_canonical_executive_data.py"
with open(builder_path, "r", encoding="utf-8") as f:
    builder_code = f.read()

# Top 1 updates
builder_code = builder_code.replace(
    '"drilldown": ["EV-082", "EV-083", "EV-084", "tp16_pp1_dist_prefill_128k", "tp16_pp1_dist_long_prefill_512k"]',
    '"drilldown": ["EV-082", "EV-083", "EV-084", "PR-001", "PR-004", "PR-006"]'
)
builder_code = builder_code.replace(
    '"decision_changed": "Engineers optimizing 8K–128K should focus on MoE dispatch and recurrence kernel launch overhead. For 512K–1M deployments, all optimization efforts must pivot to FlashAttention chunk budgeting, sequence parallelism, and KV cache layout."',
    '"decision_changed": "Candidate optimization focus to validate: For 8K–128K, evaluate MoE dispatch and recurrence kernel launch overhead; for ≥512K, prioritize FlashAttention chunk budgeting, sequence parallelism, and KV cache layout."'
)

# Top 2 updates
builder_code = builder_code.replace(
    '≈ 116 bytes/token (H=2304, b=2 bytes BF16)',
    '≈ 116 (dimensionless hidden-width-equivalent exposure coefficient, E_H, with H=2304, b=2 bytes BF16)'
)

# Top 4 updates
builder_code = builder_code.replace(
    '"decision_changed": "Deploy prefix caching for agents, long-document Q&A, and few-shot workloads. Size KV cache specifically to prevent prefix eviction during peak load."',
    '"decision_changed": "Prefix reuse should be treated as a workload-routing/caching lever; as a candidate deployment experiment, evaluate routing multi-turn chat and RAG to cache-warm replicas with sticky sessions."'
)

# Top 5 updates
builder_code = builder_code.replace(
    '"drilldown": ["EV-112", "EV-113", "EV-114", "EV-115", "EV-116", "EV-117", "EV-118", "EV-119", "EV-120", "EV-121", "EV-122", "EV-123", "EV-124", "EV-125"]',
    '"drilldown": ["EV-116", "EV-117", "EV-118", "EV-123", "EV-124", "EV-125"]'
)
builder_code = builder_code.replace(
    '"decision_changed": "Rate limiters and ingress gateways must enforce prompt-token concurrency budgets, not simple request counts. Admitting 8K vs 128K queries under identical RPS triggers severe prefill starvation."',
    '"decision_changed": "Candidate deployment takeaway: Capacity planning for prefill-heavy traffic should normalize demand into prompt tokens/s rather than compare workloads only in requests/s."'
)

# Top 6 updates
builder_code = builder_code.replace(
    '"drilldown": ["EV-001", "EV-005", "EV-076", "EV-078", "EV-082", "EV-084", "EV-079", "EV-081", "EV-085", "EV-087"]',
    '"drilldown": ["EV-009", "EV-010", "EV-011", "EV-012", "EV-013", "EV-014", "EV-015", "EV-016", "EV-076", "EV-077", "EV-078", "EV-079", "EV-080", "EV-081", "EV-082", "EV-083", "EV-084", "EV-085", "EV-086", "EV-087"]'
)
builder_code = builder_code.replace(
    '"decision_changed": "Deploy TP4 for short-context instances to maximize single-node efficiency. Scale out via Pipeline Parallelism (PP4) rather than cross-node TP16 for distributed long-context serving."',
    '"decision_changed": "Allocate additional GPUs along the parallelism dimension that has positive measured elasticity for the workload/SLO, and expose the GPU-second trade-off instead of declaring a universal topology winner."'
)

# Top 7 updates
builder_code = builder_code.replace(
    '"drilldown": ["EV-009", "EV-013", "tp4_decode_8k", "tp8_decode_8k"]',
    '"drilldown": ["EV-009", "EV-013", "PR-002", "PR-003"]'
)
builder_code = builder_code.replace(
    '"decision_changed": "Cap Tensor Parallelism at TP4 for decode-heavy or conversational workloads. Avoid TP8 unless model parameters exceed 4-GPU VRAM capacity."',
    '"decision_changed": "For interactive short-context decode, prefer TP=4 as candidate deployment topology; TP=8 incurs cross-NUMA socket collective synchronization overhead."'
)

# Top 9 updates
builder_code = builder_code.replace(
    '"formula_derivation": "Effective compute efficiency: Eff = Work_useful / (Utilization * Time). TP4/PP4 achieves 2.39x higher useful token progression per unit of time despite lower reported utilization."',
    '"formula_derivation": "Heuristic efficiency proxy: Eff_heuristic = Work_useful / (Utilization * Time). TP4/PP4 achieves 2.39x higher useful token progression per unit of time despite lower reported utilization; this is an operational heuristic proxy, not a direct micro-architectural FLOP count."'
)

# Top 10 updates
builder_code = builder_code.replace(
    '"True Total Model KV Footprint (PP \u00d7 KV%)"',
    '"Global KV Consistency Check (PP \u00d7 KV%)"'
)
builder_code = builder_code.replace(
    '"formula_derivation": "True VRAM Headroom = VRAM_total - VRAM_peak_physical. 96.00 - 88.83 = 7.17 GiB. Normalized KV usage: KV_global = PP * KV_reported."',
    '"formula_derivation": "VRAM telemetry shows flat ~88.4–88.8 GiB physical allocation across pipeline stages, while reported KV cache usage is divided across stages (2.75% on PP4 vs 12.29% on PP1). Global KV consistency check: PP * reported KV% ≈ 11.0% (assuming symmetric stage distribution; exact allocator sharding unmeasured)."'
)

with open(builder_path, "w", encoding="utf-8") as f:
    f.write(builder_code)

print("Updated build_canonical_executive_data.py")

# ---------------------------------------------------------------------------
# 2. Run build_canonical_executive_data.py to regenerate JSONs
# ---------------------------------------------------------------------------
import subprocess
res = subprocess.run([sys.executable, "build_canonical_executive_data.py"], capture_output=True, text=True)
if res.returncode != 0:
    print("Error executing build_canonical_executive_data.py:", res.stderr)
    sys.exit(1)
else:
    print("Regenerated canonical JSONs via build_canonical_executive_data.py")

# Read updated EXECUTIVE_DISCOVERIES
with open("v8_full_results/dashboards/v4_dashboard/EXECUTIVE_DISCOVERIES.json", "r", encoding="utf-8") as f:
    updated_discoveries = json.load(f)

# Also update the V2 file copies if needed
with open("v8_full_results/dashboards/v4_dashboard/EXECUTIVE_DISCOVERIES_V2.json", "w", encoding="utf-8") as f:
    json.dump(updated_discoveries, f, indent=2)

with open("v8_full_results/results/real_data/final_validation/EXECUTIVE_DISCOVERIES_V2.json", "w", encoding="utf-8") as f:
    json.dump(updated_discoveries, f, indent=2)

print("Updated EXECUTIVE_DISCOVERIES_V2.json across dashboard and validation directories.")

# ---------------------------------------------------------------------------
# 3. Update the 4 HTML files with visible text audit fixes and embedded JSON
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

    # A. Update embedded window.EXECUTIVE_DISCOVERIES
    m = html.find("window.EXECUTIVE_DISCOVERIES = [")
    if m != -1:
        # find the end of this statement: ";\n" or ";\r\n"
        end = html.find("];", m)
        if end != -1:
            html = html[:m] + "window.EXECUTIVE_DISCOVERIES = " + updated_discoveries_json_str + html[end+1:]
            print(f"Re-injected window.EXECUTIVE_DISCOVERIES in {target}")

    # B. Key Finds - Top 1 (L1580)
    html = html.replace(
        "<b>DECISION CHANGED:</b> <span style=\"color:var(--green);font-weight:700\">Do not tune long-context performance from a single 128K profile. Prioritize FlashAttention & chunk budget for ≥512K; prioritize MoE routing and GEMMs for ≤128K.</span>",
        "<b>DECISION CHANGED:</b> <span style=\"color:var(--green);font-weight:700\">Do not tune long-context performance from a single 128K profile. Candidate optimization focus to validate: prioritize FlashAttention & chunk budget for ≥512K; prioritize MoE routing and GEMMs for ≤128K.</span>"
    )

    # C. Key Finds - Top 4 (L1643)
    html = html.replace(
        "<b>DECISION CHANGED:</b> <span style=\"color:var(--green);font-weight:700\">Prefix reuse should be treated as a workload-routing/caching lever: route multi-turn chat and RAG to cache-warm replicas with sticky sessions.</span>",
        "<b>DECISION CHANGED:</b> <span style=\"color:var(--green);font-weight:700\">Prefix reuse should be treated as a workload-routing/caching lever; as a candidate deployment experiment, evaluate routing multi-turn chat and RAG to cache-warm replicas with sticky sessions.</span>"
    )

    # D. Key Finds - Top 5 (L1679, L1684, L1689, L1691)
    html = html.replace(
        "Diverges by <b>18.2×</b> due to prompt length discrepancy.",
        "<b>18.2× lower accepted RPS</b> while prompt length is 16× larger."
    )
    html = html.replace(
        "Narrow <b>~14% spread</b> confirms prompt-token saturation.",
        "Narrow <b>~14% spread</b> yields a tighter measured band under token normalization."
    )
    html = html.replace(
        "(a narrow ~14% spread despite an 18.2× prompt length discrepancy).",
        "(a narrow ~14% spread with 18.2× lower accepted RPS while prompt length is 16× larger)."
    )
    html = html.replace(
        "<b>WHY (Mechanism):</b> GPU prefill engine saturation is fundamentally governed by aggregate input token compute, not discrete request counts.",
        "<b>WHY (Mechanism):</b> GPU prefill engine saturation exhibits high correlation with aggregate input token compute across measured prompt scales."
    )

    # E. Key Finds - Top 6 (L1758)
    html = html.replace(
        "<b>WHY (Mechanism):</b> Short prompts are memory-bandwidth and barrier latency bound, so wider TP adds barrier overhead without compute gain. Long prompts are compute-heavy, allowing pipelining to split prompt work with high efficiency.",
        "<b>WHY (Mechanism):</b> Measured TP return changes sign with context; exact compute-vs-communication balance remains an active investigation requiring timeline corroboration."
    )

    # F. Key Finds - Top 7 (L1828, L1829)
    html = html.replace(
        "<b>WHY (Mechanism):</b> Small-message decode AllReduce collectives are latency-bound. Spanning all 8 GPUs requires traversing the inter-NUMA PCIe bridge, increased cross-GPU communication and synchronization overhead on 8-GPU domain (cross-socket NUMA bridge crossing) for token-by-token generation.",
        "<b>WHY (Mechanism):</b> Small-message decode AllReduce collectives are latency-bound. Spanning all 8 GPUs incurs cross-NUMA socket collective synchronization overhead for token-by-token generation."
    )
    html = html.replace(
        "<b>DECISION CHANGED:</b> <span style=\"color:var(--green);font-weight:700\">Do not assume wider TP improves interactive decode. For short decode-heavy work, collective synchronization can erase the extra compute parallelism. Enforce TP=4 for interactive decode; avoid TP=8 due to PCIe/NUMA bus synchronization overhead.</span>",
        "<b>DECISION CHANGED:</b> <span style=\"color:var(--green);font-weight:700\">Do not assume wider TP improves interactive decode. For interactive short-context decode, prefer TP=4 as candidate deployment topology; TP=8 incurs cross-NUMA socket collective synchronization overhead.</span>"
    )

    # G. Scale-Up Tab - C6 Implication (L2066)
    html = html.replace(
        "<div><b>Implication</b><span>TP8 compute scaling overcomes communication overhead at long context</span></div>",
        "<div><b>Implication</b><span>TP8 lowers measured TTFT at 512K/1M; compute scaling vs collective overhead balance requires timeline/NCU confirmation</span></div>"
    )

    # H. Long Context Tab - E6 FP8 Status Card (L2332)
    old_fp8_card = """<div class="card"><div class="card-title">1M KV-Cache Dtype Sensitivity — FP8 vs Baseline</div><div class="card-sub">Compare only against otherwise matched baseline</div><div class="scope-note" style="margin:6px 0"><strong>Config: exact TP/PP must bind from the matched evidence rows; only KV-cache dtype is the intended comparison.</strong></div><div class="chart short"><canvas id="chart_long_fp8"></canvas></div></div>"""
    new_fp8_card = """<div class="card"><div class="card-title">1M KV-Cache Dtype Sensitivity — FP8 vs Baseline</div><div class="card-sub">Compare only against otherwise matched baseline</div><div class="scope-note" style="margin:6px 0"><strong>Config: exact TP/PP must bind from the matched evidence rows; only KV-cache dtype is the intended comparison.</strong></div><div style="padding:10px;background:rgba(255,200,87,0.04);border:1px solid rgba(255,200,87,0.25);border-radius:6px;height:calc(100% - 95px);box-sizing:border-box"><div style="font-weight:700;color:var(--amber);margin-bottom:4px;font-size:11px">GUARDED NOT_RUN — FP8 KV Cache Not Executed</div><div style="font-size:11px;color:var(--muted);line-height:1.35"><b>Status:</b> GUARDED NOT_RUN / Intentionally excluded.<br/><b>Architectural Rationale:</b> FP8 KV-cache runtime acceptance was not validated in this campaign; no quantitative comparison exists. All verified runs operated in BF16 baseline (~88.8 GiB GPU memory footprint).</div></div><canvas id="chart_long_fp8" style="display:none"></canvas></div>"""
    html = html.replace(old_fp8_card, new_fp8_card)

    # I. Scheduler Tab - F6, F7, F9 (L2421, L2427, L2445, L2448)
    html = html.replace(
        "divides the active KV allocation across 4 sequential stages",
        "is consistent with distributing active KV allocation across 4 sequential stages (exact allocator sharding is not directly measured)"
    )
    html = html.replace(
        "8K Short Context Sweep (tp4_openloop_8192) — Derived Capacity Knee @ ~0.90x Offered (~3.811 RPS Offered, ~3.302 req/s Achieved)",
        "8K Short Context Sweep (tp4_openloop_8192) — Candidate Capacity Knee @ ~0.90x Offered (heuristic: slope inflection of TPOT / queue degradation; ~3.811 RPS Offered, ~3.302 req/s Achieved)"
    )
    html = html.replace(
        "<tr><th>Knee location</th><td><b>8K:</b> ~0.90x offered load (~3.811 RPS offered, ~3.302 req/s achieved); queue 0.182s, TPOT 60.86ms · <b>128K:</b> ~0.75x offered load (~0.171 RPS); queue 1.94s, TPOT 50.57ms</td></tr>",
        "<tr><th>Candidate Knee location (Heuristic: slope inflection of TPOT / queue degradation)</th><td><b>8K:</b> ~0.90x offered load (~3.811 RPS offered, ~3.302 req/s achieved; queue 0.182s, TPOT 60.86ms) · <b>128K:</b> ~0.75x offered load (~0.171 RPS; queue 1.94s, TPOT 50.57ms)</td></tr>"
    )
    html = html.replace(
        "<tr><th>Decision</th><td>Workload-scoped admission limits: for 1M interactive/SLO workloads, admit at c=1 (cleanest measured single-node point); for 8K interactive decode, operate at c≤8 to keep TPOT ~10.8ms; for 128K open-loop, throttle admission beyond 0.75× (~0.171 RPS) before queuing cliff.</td></tr>",
        "<tr><th>Decision</th><td>Workload-scoped candidate admission limits: for 1M interactive/SLO workloads, admit at c=1 (cleanest measured single-node point); for 8K interactive decode, evaluate c≤8 to keep TPOT ~10.8ms depending on target SLO; for 128K open-loop, evaluate throttling admission beyond candidate knee 0.75× (~0.171 RPS) prior to the 1.00× queuing cliff.</td></tr>"
    )

    # J. Profiler Tab - G2, G4, G10 (L2586, L2703, L2992, L2999, L3004, L3010, L3016, L6250, L6251, L6252)
    html = html.replace(
        "<div><b>Prescription</b><span style=\"color:var(--cyan)\">Pin TP4 within a single NUMA socket for lowest interactive decode latency</span></div>",
        "<div><b>Prescription</b><span style=\"color:var(--cyan)\">Co-locating TP4 within a single NUMA socket is a candidate optimization to evaluate for interactive decode workloads</span></div>"
    )
    html = html.replace(
        "<td>Dominant aggregate GPU kernel-work share in decode profile (112,640 ring barriers); TP8 incurs +20.8% NUMA delay</td>",
        "<td>Dominant aggregate GPU kernel-work share in decode profile (112,640 traced ring AllReduce calls); TP8 incurs +20.8% cross-NUMA socket traversal overhead</td>"
    )
    html = html.replace(
        "<div class=\"card-title\">🧭 Empirical Profiler Root Cause → Production Deployment Rules</div>",
        "<div class=\"card-title\">🧭 Empirical Profiler Observations → Workload-Scoped Architectural Takeaways</div>"
    )
    html = html.replace(
        "<thead><tr><th>Empirical Finding</th><th>Physical / Hardware Root Cause</th><th>Production Deployment Rule</th><th>Supporting Artifact</th></tr></thead>",
        "<thead><tr><th>Empirical Observation</th><th>Cross-Validated Mechanism / Contributor</th><th>Workload-Scoped Candidate Takeaway</th><th>Supporting Artifact</th></tr></thead>"
    )
    html = html.replace(
        "<td><b>Single-Node Interactive Serving:</b> Bind TP4 workers strictly to a single NUMA socket (ranks 0..3 on Socket 0). Do NOT span TP across sockets for short-context decode.</td>",
        "<td><b>Single-Node Interactive Serving:</b> For interactive decode serving: Co-locating TP4 workers within a single NUMA socket is a candidate optimization to evaluate; avoid spanning TP across sockets for short-context decode.</td>"
    )
    html = html.replace(
        "<td><b>Single-Node Batch / Document Ingestion:</b> Use TP8 for long-context prefill workloads (512K+) where prompt processing latency dominates.</td>",
        "<td><b>Single-Node Batch / Document Ingestion:</b> For long-context prefill workloads (512K+), evaluate TP8 where prompt processing latency dominates.</td>"
    )
    html = html.replace(
        "<td><b>Multi-Node Cloud Deployment:</b> Prefer Pipeline Parallelism (TP4/PP4 or TP8/PP2) over cross-node Tensor Parallelism (TP16) for tested workloads and TCP/IP VPC conditions.</td>",
        "<td><b>Multi-Node Cloud Deployment:</b> For multi-node cloud deployments on TCP/IP VPC, candidate topology favors Pipeline Parallelism (TP4/PP4 or TP8/PP2) over cross-node Tensor Parallelism (TP16) for tested workloads.</td>"
    )

    # Chart 24 dataset labels (L6250, L6251, L6252)
    html = html.replace(
        "{ label: 'TP8 Decode 8K [Rank 0; NUMA Delay] (%)', data: [89.1, 1.4, 2.8, 3.2, 0.4, 1.1, 2.0], backgroundColor: 'rgba(255,200,87,0.8)' },",
        "{ label: 'TP8 Decode 8K [Rank 0; Cross-NUMA Socket Traversal Overhead] (%)', data: [89.1, 1.4, 2.8, 3.2, 0.4, 1.1, 2.0], backgroundColor: 'rgba(255,200,87,0.8)' },"
    )
    html = html.replace(
        "{ label: 'TP16/PP1 Dist Prefill [Selected Rank: Node 0 Rank 0; All-Rank Mean 77.6%] (%)', data: [76.2, 11.2, 5.6, 3.1, 1.2, 1.2, 1.5], backgroundColor: 'rgba(255,60,90,0.9)' },",
        "{ label: 'TP16/PP1 Dist Prefill [Selected Rank: Node 0 Rank 0 (76.2%); All-Rank Range 75.1–78.9%, Mean 77.6%] (%)', data: [76.2, 11.2, 5.6, 3.1, 1.2, 1.2, 1.5], backgroundColor: 'rgba(255,60,90,0.9)' },"
    )
    html = html.replace(
        "{ label: 'TP4/PP4 Dist Prefill [Selected Stage: Stage 0 / Rank 0; Stage 0 P2P 8.3%] (%)', data: [40.0, 22.8, 13.2, 8.5, 2.6, 4.6, 8.3], backgroundColor: 'rgba(179,136,255,0.85)' }",
        "{ label: 'TP4/PP4 Dist Prefill [Selected Stage: Stage 0 Rank 0 (40.0% AllReduce, 8.3% P2P); Pipeline Range Across Stages 38.2–42.1%] (%)', data: [40.0, 22.8, 13.2, 8.5, 2.6, 4.6, 8.3], backgroundColor: 'rgba(179,136,255,0.85)' }"
    )

    # Unit consistency: replace any '88.7 GB' with '88.7 GiB'
    html = html.replace('88.7 GB', '88.7 GiB')

    with open(target, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Successfully wrote updates to {target}")

print("All deterministic re-audit fixes applied across all 4 HTML files and canonical JSONs!")
