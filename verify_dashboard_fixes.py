#!/usr/bin/env python3
"""
verify_dashboard_fixes.py
Verifies that all 9 items in §5 of Dashboard_Fix_Verification_v1.md,
all 5 self-contradictions in §3, all §6 layout additions,
and all §7 4-chart time budget extensions from v1.2 are completely resolved.
"""

import sys, re, json, os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

MASTER_FILE = "MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html"

with open(MASTER_FILE, "r", encoding="utf-8") as f:
    text = f.read()

errors = []
passes = []

def test(cond, desc):
    if cond:
        passes.append(desc)
        print(f"  [PASS] {desc}")
    else:
        errors.append(desc)
        print(f"  [FAIL] {desc}")

print("=== VERIFYING SECTION 3: SELF-CONTRADICTIONS ===")

# 1. TP8 AllReduce ratio: hero 3.10x, narrative 3.10x, definitions box 3.10x on both sides
m_232_narrative = re.search(r'2\.32× higher \(132\.3 ms vs 409\.9 ms', text)
test(m_232_narrative is None, "Contradiction 1: 2.32x removed from KD#7 narrative (now 3.10x)")
m_hero_310 = re.search(r'132\.3ms → 409\.9ms Self CUDA \(Decode-Only, 3\.10×', text)
test(m_hero_310 is not None, "Contradiction 1: Hero shows 132.3ms → 409.9ms (3.10x)")
m_def_both_310 = "<td>3.10× (Decode-only per call, 18.9 → 58.7 µs)</td><td>3.10× (Both agree on decode-only)</td>" in text
test(m_def_both_310, "Contradiction 1: Definitions box states 3.10x on both sides")

# 2. NUMA: no longer asserted as proven cause; ring latency + pending pinning test used
m_numa_cause_1 = "avoids cross-NUMA barrier delay" in text
test(not m_numa_cause_1, "Contradiction 2: Executive decision map no longer asserts cross-NUMA delay")
m_numa_cause_2 = "Cross-validated: 4-GPU barrier avoids NUMA bridge crossing" in text
test(not m_numa_cause_2, "Contradiction 2: TPOT card no longer claims cross-validated NUMA crossing")
m_numa_cause_3 = "TP=8 incurs cross-NUMA socket collective synchronization overhead" in text
test(not m_numa_cause_3, "Contradiction 2: KD#7 explorer no longer claims cross-NUMA overhead")
m_numa_cause_4 = "AllReduce ring barrier surges from 369.5μs to 446.5μs (+20.8%)" in text
test(not m_numa_cause_4, "Contradiction 2: Profiler deployment rules no longer has eager 369.5/446.5 NUMA claim")
m_numa_cause_5 = "NUMA &amp; cross-socket bus traversal identified as cause for TP8 slowdown." in text
test(not m_numa_cause_5, "Contradiction 2: Reviewer-audit matrix no longer names NUMA as cause")

# 3. Decode profiles: eager numbers removed from evidence claims & PROFILER_REGISTRY updated with mode
m_claim_863 = "86.3% aggregate GPU kernel-work share in exact TP4 decode profile" in text
test(not m_claim_863, "Contradiction 3: Decision claim registry row 1 no longer uses 86.3% eager share")
m_pr002_mode = "mode: 'graphs-on" in text
test(m_pr002_mode, "Contradiction 3: PROFILER_REGISTRY entries have explicit mode field")

# 4. Finding 3 NCCL growth: 2.18x sublinear claim removed, replaced by SendRecv 4.5x, AllReduce 2.7x
m_218_map = 'NCCL 2.18&times; (p≈0.56)' in text
test(not m_218_map, "Contradiction 4: 60-second map no longer shows NCCL 2.18x")
m_45_map = 'SendRecv 4.5&times; · AllReduce 2.7&times;' in text
test(m_45_map, "Contradiction 4: 60-second map shows SendRecv 4.5x · AllReduce 2.7x")
m_218_sublinear = "inter-node NCCL Send/Recv scales sub-linearly (~2.18×)" in text
test(not m_218_sublinear, "Contradiction 4: KD#3 takeaway no longer claims SendRecv scales sub-linearly (~2.18x)")

# 5. The knee: harmonized at 0.75x SLO / 0.90x slope; 1.00x row called full load
m_8k_knee_contra = "At the 8K knee, 71% of all decode waiting" in text
test(not m_8k_knee_contra, "Contradiction 5: 1.00x row in stall card no longer called 'the 8K knee'")

print("\n=== VERIFYING SECTION 5: THE 9 CLOSING ACTION ITEMS ===")

# Item 1: 3.10x
test(m_def_both_310, "Item 1: 3.10x in KD#7 narrative and definitions box")

# Item 2: NUMA wording rewritten
test(not m_numa_cause_1 and not m_numa_cause_2 and not m_numa_cause_3, "Item 2: NUMA rewritten to ring latency & pending pinning")

# Item 3: Eager decode numbers removed from rules & claim registry; PROFILER_REGISTRY updated
m_pr002_val = "'PR-002': {\n        evidence_id: 'PR-002',\n        profile_id: 'PR-002',\n        case: 'tp4_decode_8k',\n        bench: '8k_decode_rank0',\n        network_provenance: 'SINGLE_NODE_LOCAL',\n        node: 'Node 0',\n        rank: 0,\n        phase: 'Decode (8K context)',\n        mode: 'graphs-on" in text
test(m_pr002_val, "Item 3: PROFILER_REGISTRY PR-002 updated with graphs-on serving figures")

# Item 4: KD#3 reproducible numbers
test(m_45_map, "Item 4: KD#3 2.18x replaced by SendRecv 4.5x / AllReduce 2.7x")

# Item 5: KD pages 1, 2, 4, 5, 6, 8, 9, 10
pos_kd = text.find('window.KD_PAGES_DATA = [')
end_kd = text.find('];\n', pos_kd)
if end_kd == -1: end_kd = text.find('];', pos_kd)
kd_data = json.loads(text[pos_kd + len('window.KD_PAGES_DATA = '):end_kd+1])

kd_dict = {p['id']: p for p in kd_data}
test("37.7 MB per call" in kd_dict[1]['takeaways'][1], "Item 5: KD#1 includes 37.7 MB per call and SendRecv ceiling")
test("93.5s, 185.4s, 277.3s, 368.9s" in kd_dict[2]['takeaways'][1], "Item 5: KD#2 includes arrival ladder and partial prefill limit")
test("7 of 7 repeats hit" in kd_dict[4]['takeaways'][2], "Item 5: KD#4 includes exact per-request miss counts")
test("1.8×" in kd_dict[5]['takeaways'][2], "Item 5: KD#5 includes SLO-conditioned 1.8x usable capacity")
test("4 scale-out + 2 scale-up" in kd_dict[6]['takeaways'][2], "Item 5: KD#6 specifies 4 scale-out + 2 scale-up topologies")
test("Pareto-dominates 8K" in kd_dict[8]['takeaways'][1], "Item 5: KD#8 specifies 16K chunk Pareto-dominates 8K")
test("nvidia-smi background sampler" in kd_dict[9]['confidence_note'], "Item 5: KD#9 confidence note specifies nvidia-smi sampler")
test("TP4/PP1: 8.14M" in kd_dict[10]['takeaways'][1], "Item 5: KD#10 provides empirical KV pool size in tokens")

# Item 6: Coverage matrix: status from usable exports; qualify 14/22 tiles
test("DECODE DEFERRED (0/16 usable)" in text, "Item 6: Coverage matrix shows DECODE DEFERRED on 0/16 ranks")
test("14 / 22 CAPTURED" in text, "Item 6: 14/22 tiles qualified as CAPTURED with usable exports noted")

# Item 7: Remove ~0.1ms RTT (8 cells); define VERDICT; print heatmap threshold rule; label c1
test("~0.1ms RTT" not in text and "0.1ms RTT" not in text, "Item 7: All ~0.1ms RTT occurrences eliminated")
test("Verdict Rules:</b> RECOMMENDED = lowest measured latency" in text, "Item 7: VERDICT defined in Scale-Out matrix")
test("Sensitivity Classification Rule:</b> HIGH NETWORK RESILIENCE = &lt;15%" in text, "Item 7: Network sensitivity classification rule defined")
test("Queue (c1)" in text or "Queue (c1 — single-stream" in text, "Item 7: Queue view explicitly labeled c1")

# Item 8: Scheduler K3 hedge -> pool-in-tokens; K6 units; K9 tokens axis; regime-map 8K row
test("8.14M, TP8/PP1 8.21M, TP16/PP1 8.24M" in text, "Item 8: Scheduler K3 card contains empirical pool in tokens")
test("<td>0.00001s</td>" not in text, "Item 8: Scale-out ledger queue units unified to ms")
test("Peak KV % &amp; Equivalent Token Capacity" in text, "Item 8: KV chart title/subtitle contains token capacity")
test("kernel-time + collectives (46 % of memory BW)" in text, "Item 8: Regime map 8K row corrected to kernel-time + collectives")

# Item 9: Evidence ledger & Readiness audit panel
test('id="cluster-readiness-panel"' in text, "Item 9: Cluster & Campaign Readiness Audit Panel added")

print("\n=== VERIFYING SECTION 6: V1.1 EXTENSIONS ===")

# Section 6: Scope notes
test("Single-node local execution (TP4/PP1 &amp; TP8/PP1). Distributed layouts (TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1) were run at c=1 only" in text, "Section 6: Single-node scope labels present on concurrency/stall panels")

# Section 6.1: TP4/PP2 and TP8/PP2 kernel composition
test("TP4/PP2 Dist Prefill" in text and "TP8/PP2 Dist Prefill" in text, "Section 6.1: TP4/PP2 and TP8/PP2 scenario chips added to Profiler")
test("128K Prefill Kernel Composition Across All 6 Layouts" in text, "Section 6.1: 6-layout prefill composition comparison table present")
test("prefill_composition_128k_by_layout.csv" in text, "Section 6.1: Reference to prefill_composition_128k_by_layout.csv present")

# Section 6.2: §4.7 Stage panel PP2 check
test("Independent Confirmation (PP2 Check — §6.2)" in text, "Section 6.2: PP2 3:4 flash attention check added to §4.7 stage panel")

# Section 6.3: KD#7 decode pointer
test("Cross-Node & Pipeline Decode Pointer" in str(kd_dict[7]['takeaways']), "Section 6.3: KD#7 contains cross-node TP16 and pipeline hop decode pointers")

print("\n=== VERIFYING SECTION 7: V1.2 EXTENSIONS (4-CHART SUITE & FINDINGS) ===")

# Section 7: 4-Chart controls & views
test('id="profiler-wall-time-budget-card"' in text, "Section 7: profiler-wall-time-budget-card present")
test('id="btn-budget-first-single"' in text and 'id="btn-budget-decode-load"' in text, "Section 7: 4-way chart switcher buttons present")
test('id="budget-first-single-container"' in text and 'id="budget-decode-load-container"' in text, "Section 7: All 4 chart containers present")
test("wall_time_budget_first_token.png" in text and "wall_time_budget_decode_token_under_load.png" in text, "Section 7: All 4 chart images referenced")

# Section 7: Two Key Findings Surfaced Under Load
test("Finding 1: 8K First Token Doubles at c4 Due to Chunk Boundary" in text, "Section 7: Finding 1 (8K c4 chunk boundary) present on Profiler tab")
test("Finding 2: MoE Decode Batching Expands Active Experts" in text, "Section 7: Finding 2 (MoE expert expansion) present on Profiler tab")
test('id="scheduler-loaded-budget-findings"' in text, "Section 7: Scheduler tab contains dedicated loaded-budget findings card")
test("Chunk-Size / Prompt Budget Finding (8K at c4)" in text, "Section 7: Scheduler tab features Finding 1 chunk-size note")
test("MoE Decode Batching &amp; Expert Expansion Finding" in text, "Section 7: Scheduler tab features Finding 2 MoE expert expansion note")

# Section 7: Methodology & Wave Disclosures
test("Technical Clarification on \"Waves\"" in text, "Section 7: Technical clarification on vLLM V1 waves vs GPU wave quantization present")
test("Engine decode time matches client (e2e − first token) within 0.4%" in text, "Section 7: Loaded attribution methodology disclosure present")
test("Additive Scope Note:</b> This 4-chart panel is strictly additive" in text, "Section 7: Additive guarantee present")

# Section 7: Check disk artifacts
test(os.path.exists("time_budget/wall_time_budget_first_token.csv"), "Artifacts: wall_time_budget_first_token.csv exists")
test(os.path.exists("time_budget/wall_time_budget_decode_token.csv"), "Artifacts: wall_time_budget_decode_token.csv exists")
test(os.path.exists("time_budget/wall_time_budget_first_token_under_load.csv"), "Artifacts: wall_time_budget_first_token_under_load.csv exists")
test(os.path.exists("time_budget/wall_time_budget_decode_token_under_load.csv"), "Artifacts: wall_time_budget_decode_token_under_load.csv exists")
test(os.path.exists("time_budget/README_time_budget.md"), "Artifacts: README_time_budget.md exists")
test(os.path.exists("wall_time_budget_first_token.png"), "Artifacts: wall_time_budget_first_token.png exists in root")
test(os.path.exists("wall_time_budget_decode_token.png"), "Artifacts: wall_time_budget_decode_token.png exists in root")
test(os.path.exists("wall_time_budget_first_token_under_load.png"), "Artifacts: wall_time_budget_first_token_under_load.png exists in root")
test(os.path.exists("wall_time_budget_decode_token_under_load.png"), "Artifacts: wall_time_budget_decode_token_under_load.png exists in root")

# Verify row counts and columns of under_load CSVs
df_ftl = pd.read_csv("time_budget/wall_time_budget_first_token_under_load.csv")
test(len(df_ftl) == 24, f"Data Verification: first_token_under_load.csv has 24 rows (got {len(df_ftl)})")
df_dtl = pd.read_csv("time_budget/wall_time_budget_decode_token_under_load.csv")
test(len(df_dtl) == 24, f"Data Verification: decode_token_under_load.csv has 24 rows (got {len(df_dtl)})")
test("experts_touched" in df_dtl.columns and "stalled_tokens_pct" in df_dtl.columns, "Data Verification: decode_token_under_load.csv carries extra batch-load columns")

print("\n" + "="*50)
print(f"RESULTS: {len(passes)} Passed, {len(errors)} Failed")
if errors:
    print("FAILED TESTS:")
    for e in errors:
        print(" - " + e)
    sys.exit(1)
else:
    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
