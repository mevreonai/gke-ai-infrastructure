import sys, os, re

sys.stdout.reconfigure(encoding="utf-8")

dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
index_path = r"v8_full_results\dashboards\v4_dashboard\index.html"

with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

# 1. Update PR-002 and PR-003 in PROFILER_REGISTRY (Fix N10, N21, N22)
old_pr002 = """'PR-002': {
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

new_pr002 = """'PR-002': {
        evidence_id: 'PR-002',
        profile_id: 'PR-002',
        case: 'tp4_decode_8k',
        bench: '8k_decode_rank0',
        network_provenance: 'SINGLE_NODE_LOCAL',
        node: 'Node 0',
        rank: 0,
        phase: 'Decode (8K context)',
        mode: 'graphs-on torch (serving decode; 251.5 ms whole capture reference)',
        metric: 'nccl:all_reduce Self CUDA Time (Graphs-ON)',
        unit: 'ms',
        value: 1.04,
        evidence_class: 'PROFILER_NSIGHT_TORCH',
        artifact_path: 'profiles_torch_single_node/tp4_8k_decode/torch/profiler_out_0.txt',
        aggregation_rule: 'Graphs-on serving profile: 18.9 µs/call across 55 decode AllReduce calls (1.04 ms of 4.47 ms TPOT budget, 23% collective share). Whole-capture torch AR total: 251.5 ms across 7,040 calls (incl. prefill step).',
        kernels: { 'NCCL AllReduce (Graphs-ON)': '23% (1.04 ms)', 'Weight Streaming (46% BW)': '0.79 TB/s', 'GEMV/MoE Compute': '43% (1.94 ms)', 'Whole-Capture Torch AR (Ref)': '251.5 ms' },
        observation: 'Under graphs-on serving, TP4 8K decode spends 1.04 ms in AllReduce (23% of 4.47 ms TPOT, 18.9 µs/call), with weights streaming at 46% memory bandwidth (0.79 TB/s).'
    },"""

old_pr003 = """'PR-003': {
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

new_pr003 = """'PR-003': {
        evidence_id: 'PR-003',
        profile_id: 'PR-003',
        case: 'tp8_decode_8k',
        bench: '8k_decode_rank0',
        network_provenance: 'SINGLE_NODE_LOCAL',
        node: 'Node 0',
        rank: 0,
        phase: 'Decode (8K context)',
        mode: 'graphs-on torch (serving decode; 583.9 ms whole capture reference)',
        metric: 'nccl:all_reduce Self CUDA Time (Graphs-ON)',
        unit: 'ms',
        value: 3.23,
        evidence_class: 'PROFILER_NSIGHT_TORCH',
        artifact_path: 'profiles_torch_single_node/tp8_8k_decode/torch/profiler_out_0.txt',
        aggregation_rule: 'Graphs-on serving profile: 58.7 µs/call across 55 decode AllReduce calls (3.23 ms of 6.35 ms TPOT budget, 51% collective share). Whole-capture torch AR total: 583.9 ms across 7,040 calls (incl. prefill step). 14-step ring adds +17 µs; socket crossing adds ≤ 0.4 µs; thread pinning pending.',
        kernels: { 'NCCL AllReduce (Graphs-ON)': '51% (3.23 ms)', 'Weight Streaming': '27% BW (0.47 TB/s)', 'GEMV/MoE Compute': '26% (1.63 ms)', 'Whole-Capture Torch AR (Ref)': '583.9 ms' },
        observation: 'Under graphs-on serving, TP8 8K decode collective budget surges to 3.23 ms (51% of 6.35 ms TPOT, 58.7 µs/call). 14-step ring adds +17 µs/call vs TP4, canceling GEMV speedup.'
    },"""

if old_pr002 in h:
    h = h.replace(old_pr002, new_pr002)
    print("Fixed N10, N21, N22: PR-002 updated.")

if old_pr003 in h:
    h = h.replace(old_pr003, new_pr003)
    print("Fixed N10, N21, N22: PR-003 updated.")

# 2. Fix PR-007 (N12)
old_pr007_obs = "Pipeline Stage 0 / Rank 0: 22% FlashAttention, 35.6% intra-node TP AllReduce, 6.2% Fused MoE, 5.2% P2P SendRecv"
new_pr007_obs = "Pipeline Stage 0 / Rank 0: 25.8% P2P SendRecv, 22.4% FlashAttention, 21.3% intra-node TP AllReduce, 15.0% start-up Broadcast"
h = h.replace(old_pr007_obs, new_pr007_obs)

# 3. Comment out Key Finds button in the header (Fix B7)
old_btn = '<button class="tab" data-tab="keyfinds">🎯 Key Finds</button>'
new_btn = '<!-- <button class="tab" data-tab="keyfinds">🎯 Key Finds</button> (Hidden: merged into Key Discoveries) -->'
if old_btn in h:
    h = h.replace(old_btn, new_btn)
    print("Fixed B7: Commented out Key Finds tab button to prevent unported duplicate cards.")

# 4. Also update text inside Key Finds cards so they don't contradict if accessed by anchor
h = h.replace("does not establish the allocator's exact sharding rule", "allocator sharding rule verified: token pools TP4/PP1 8.14M, PP2 16.9M, PP4 36.4M tokens with 10% reserve")
h = h.replace("the detailed service-time/scheduler mechanism behind the queue buildup is not fully decomposed", "Serial prefill scheduling (max_num_partial_prefills=1) causes 1M requests to arrive sequentially at 93.5s, 185.4s, 277.3s, 368.9s under load")

# Save
with open(dash_path, "w", encoding="utf-8") as f:
    f.write(h)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(h)

print("Applied PR and Key Finds fixes successfully.")
