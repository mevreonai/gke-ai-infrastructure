import sys, re

sys.stdout.reconfigure(encoding="utf-8")
dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"

with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

checks = [
    # B1: Software Stack
    ("B1: vLLM 0.29.0 present", "0.29.0" in h),
    ("B1: CUDA 13.0 present", "CUDA <code>13.0</code>" in h or "CUDA 13.0" in h),
    ("B1: PyTorch 2.13.0 present", "2.13.0" in h),
    ("B1: Driver 580.173.02 present", "580.173.02" in h),
    ("B1: NCCL 2.29.7 present", "2.29.7" in h),
    ("B1: No invented AWS-OFI plugin", "AWS-OFI" not in h),
    ("B1: NCCL_NET=Socket present", "NCCL_NET=Socket" in h),
    
    # B2: Defect 2
    ("B2: Off-cluster path defect present", "FINAL_VALIDATION Off-Cluster Path Defect" in h),
    
    # B3: NOT_RUN & NOT_CAPTURED
    ("B3: No 'safety-gated configurations not executed'", "safety-gated configurations not executed" not in h),
    ("B3: Attempted / rc=1 reason stated", "server exited rc=1" in h or "rc=1" in h),
    
    # B4: Ledger container & alignment
    ("B4: <div class=\"card mb8\" id=\"perf-evidence-table-container\"> restored", '<div class="card mb8" id="perf-evidence-table-container">' in h),
    ("B4: No stray 'id=\"perf-evidence-table-container\">' text", '\n\nid="perf-evidence-table-container">' not in h),
    ("B4: No orphan Cold Load header", "<th>Cold Load</th>" not in h),
    
    # B5: Base64 embedded time-budget PNGs
    ("B5: Base64 embedded time-budget PNGs", "data:image/png;base64," in h),
    
    # B6: KD renderer
    ("B6: confidence_note rendered", "p.confidence_note" in h),
    ("B6: scope_note rendered", "p.scope_note" in h),
    ("B6: KD#6 4 scale-out + 2 scale-up in note", "4 scale-out + 2 scale-up topologies" in h),
    ("B6: KD#9 nvidia-smi sampler in note", "nvidia-smi background sampler" in h),
    
    # B7: Key Finds tab
    ("B7: Key Finds tab button commented out", '<!-- <button class="tab" data-tab="keyfinds">' in h),
    
    # P1: Evidence mapping
    ("P1: EV-111 mapped for finding 1", "1: 'EV-111'" in h),
    ("P1: EV-067 mapped for finding 2", "2: 'EV-067'" in h),
    ("P1: PR-007 mapped for finding 3", "3: 'PR-007'" in h),
    ("P1: EV-075 mapped for finding 4", "4: 'EV-075'" in h),
    ("P1: EV-116 mapped for finding 5", "5: 'EV-116'" in h),
    ("P1: EV-081 mapped for finding 6", "6: 'EV-081'" in h),
    ("P1: PR-003 mapped for finding 7", "7: 'PR-003'" in h),
    ("P1: EV-027 mapped for finding 8", "8: 'EV-027'" in h),
    ("P1: EV-084 mapped for finding 9", "9: 'EV-084'" in h),
    ("P1: EV-084 mapped for finding 10", "10: 'EV-084'" in h),
    
    # N5: Stage waits
    ("N5: Stage 3 wait 17.2-21.9%", "Stage 3 waits 17.2–21.9%" in h or "Stage 3 P2P wait 17.2–21.9%" in h),
    ("N5: No 'Stages 1–3 wait 17–22%'", "Stages 1–3 wait 17–22%" not in h and "Stages 1-3 wait 17-22%" not in h),
    
    # N6: Energy numbers
    ("N6: KD#6 1M energy TP16 247.2 J", "247.2 J/1K tokens" in h),
    ("N6: KD#6 1M energy TP4/PP4 143.1 J", "143.1 J/1K tokens" in h),
    
    # N8: PP2 3 vs 4 layers
    ("N8: PP2 3 vs 4 full-attention layers", "3 vs 4 full-attention layer distribution" in h),
    ("N8: No '6 vs 8 full-attention'", "6 vs 8 full-attention" not in h),
    
    # N9: Heatmap exact values and rule labels
    ("N9: TP8/PP2 128K 100G delta +1.36%", "+1.36%" in h),
    ("N9: TP4/PP2 rows classified as HIGH NETWORK RESILIENCE", 'TP4 / PP2 (Dist)</b></td><td>128K</td><td>2.647s</td><td>2.665s</td><td><span class="badge b-green">+0.66%</span></td><td>2.859s</td><td><span class="badge b-green">+8.01%</span></td><td><span class="status s-completed">HIGH NETWORK RESILIENCE</span>' in h),
    
    # N10, N21, N22: PR-002 & PR-003
    ("N10: PR-002 43% compute", "43% (1.94 ms)" in h),
    ("N10: PR-003 26% compute", "26% (1.63 ms)" in h),
    ("N10: PR-003 weight streaming 27% BW", "27% BW" in h),
    ("N22: PR-002 artifact path profiler_out_0.txt", "profiles_torch_single_node/tp4_8k_decode/torch/profiler_out_0.txt" in h),
    
    # N11: Duplicate mode badge
    ("N11: No duplicate mode badge line", 'Mode: ${datum.mode}</span>`;\n        if (datum.mode)' not in h),
    
    # N13: KD#7 duplicate pointer
    ("N13: No duplicate pointer in KD#7", h.count("Cross-Node & Pipeline Decode Pointer: Beyond single-node TP4 vs TP8") <= 1),
    
    # N14: Scenario chips duplicate
    ("N14: No duplicate scenario chips", h.count('data-scenario="tp4_pp2_dist"') == 1),
    
    # N15: prMap 7 items
    ("N15: prMap covers all 7 datasets", "const prMap = ['PR-001', 'PR-002', 'PR-003', 'PR-004', 'PR-005', 'PR-005', 'PR-005']" in h),
    
    # N16: Overstated findings resolved
    ("N16: No 'eliminates this 211 ms penalty'", "eliminates this 211 ms penalty" not in h),
    ("N16: No 'forces uniform routing to touch 163 of 256 experts'", "forces uniform routing to touch 163 of 256 experts" not in h),
    
    # N17: Scheduler queue values
    ("N17: Scheduler queue TP4/PP4 512K 0.016ms", "1.444%</b></td><td>0.016ms</td>" in h),
    ("N17: Scheduler queue TP4/PP2 512K 0.023ms", "3.105%</b></td><td>0.023ms</td>" in h),
    ("N17: Scheduler queue TP8/PP2 1M 0.038ms", "5.882%</b></td><td>0.038ms</td>" in h),
    ("N17: Scheduler queue TP16 128K 0.019ms", "1.595%</b></td><td>0.019ms</td>" in h),
    
    # P7: Operator card & tooltip
    ("P7: GEMV tooltip 44.6ms faster", "TP8 decode GEMV is 44.6ms faster" in h),
    ("P7: Operator card part order", "exceeds GEMV savings (−44.6 ms: 171.2 → 126.5 ms)" in h),
    
    # P8: Offload D2H and text
    ("P8: D2H 56.5 GB/s", "D2H 56.5 GB/s" in h),
    ("P8: No 'mathematically certain'", "mathematically certain" not in h),
    
    # P10: 1.98x nccl-tests
    ("P10: 1.98x barrier latency", "1.98x" in h or "1.98×" in h),
    
    # P11: Scope unresolved decode
    ("P11: Campaign scope two-node decode", "two-node decode profiles (single-node graphs-on decode profiles exist; multi-node decode profiles deferred)" in h),
    
    # P12: Prefill communications share
    ("P12: 8K TTFT AllReduce 54%", "makes AllReduce 54% of 8K TTFT" in h),
    ("P12: Single-node TP range 16-57%", "intra-node TP prefill spends 16–57%" in h),
    
    # P13: KV memory floor label
    ("P13: 54% memory-speed floor label", "1M decode has 54% memory-speed floor (mostly KV read)" in h),
    
    # P16: 84,456 kernel launches
    ("P16: PR-001 84,456 launches", "84,456 kernel launches" in h),
    
    # C1: 8 usable exports
    ("C1: 8 with usable exports", "8 with usable exports (all prefill); decode deferred · 8 missing" in h),
    
    # C3: Chunk Pareto note
    ("C3: Chunk Pareto clarified", "16K is the better default for ≥128K prompts" in h),
    
    # KD#3 16-rank aggregates
    ("KD#3: SendRecv 4.5x in hero", "4.5×" in h and "SendRecv P2P Work" in h),
    ("KD#3: AllReduce 2.7x in hero", "2.7×" in h and "AllReduce Intra Work" in h),
    ("KD#3: 16-rank aggregate chart title", "16-Rank Aggregate Share of GPU Work (%)" in h),
    
    # Coverage matrix row updates
    ("Coverage: TP4/PP2 decode incomplete status", "INCOMPLETE (2/8 usable)" in h),
    ("Coverage: TP4/PP2 batched incomplete status", "INCOMPLETE (0/4 usable)" in h),
    ("Coverage: TP16 decode incomplete status", "INCOMPLETE (0/9 usable)" in h),
    ("Coverage: TP16 512K incomplete status", "INCOMPLETE (1/12 usable)" in h),
    ("Coverage: Capped 20G planned prefill rows present", "tp4_pp4_dist_capped20g" in h and "tp8_pp2_dist_capped20g" in h),
    ("Coverage: No fake capped 8K decode rows", "tp4_pp4_decode_capped100g" not in h),
]

all_passed = True
print(f"=== COMPREHENSIVE V1.4 AUDIT VERIFICATION ({len(checks)} CHECKS) ===")
fail_count = 0
for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
        fail_count += 1
    print(f"[{status}] {name}")

print(f"\nFinal Result: {'ALL ' + str(len(checks)) + ' VERIFICATIONS PASSED (100%)!' if all_passed else str(fail_count) + ' CHECKS FAILED'}")
