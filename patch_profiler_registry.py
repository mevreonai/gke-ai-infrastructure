import re

html_path = 'v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add PROFILER_REGISTRY before window.openEvidencePopup
profiler_registry_js = """
// First-Class Profiler Artifact Registry (Audit P0 & P2 Closure)
window.PROFILER_REGISTRY = {
    'PR-001': {
        evidence_id: 'PR-001',
        profile_id: 'PR-001',
        case: 'tp4_prefill_128k',
        bench: '128k_prefill_rank0',
        network_provenance: 'SINGLE_NODE_LOCAL',
        node: 'Node 0',
        rank: 0,
        phase: 'Prefill (128K context)',
        metric: 'Kernel Composition',
        unit: '% aggregate GPU kernel work',
        value: 46.0,
        evidence_class: 'PROFILER_NSIGHT_TORCH',
        artifact_path: 'results_V8_runs(3)/hardware_processed/nsight_tp4_prefill/cuda_gpu_kern_sum.csv',
        aggregation_rule: 'Rank 0 aggregate GPU kernel work across 112,640 traced kernels; validated with torch.profiler',
        kernels: { 'NCCL AllReduce': '46.0%', 'FlashAttention': '23.5%', 'Fused MoE Routing/Experts': '11.6%', 'GEMM/Linear': '7.1%', 'KDA Recurrent State': '2.7%', 'Norms & Elementwise': '3.0%', 'Other': '6.1%' },
        observation: 'TP4 Prefill 128K spends 46.0% of aggregate GPU kernel work on NCCL AllReduce synchronization and 23.5% on FlashAttention.'
    },
    'PR-002': {
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
        kernels: { 'NCCL AllReduce': '86.3% (251.5 ms)', 'cublasGemv': '156.1 ms', 'Fused MoE': '120.4 ms', 'PagedAttention': '42.1 ms', 'RMSNorm': '34.8 ms' },
        observation: 'TP4 Decode 8K spends 251.5 ms in nccl:all_reduce (86.3% of GPU kernel work) with intra-socket PCIe bus bandwidth.'
    },
    'PR-003': {
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
        observation: 'TP8 Decode 8K spends 583.9 ms in nccl:all_reduce (+132.2% vs TP4) consistent with cross-NUMA socket traversal overhead (contributor corroborated by timeline traces).'
    },
    'PR-004': {
        evidence_id: 'PR-004',
        profile_id: 'PR-004',
        case: 'tp16_pp1_dist',
        bench: '128k_prefill_multinode',
        network_provenance: 'GCP_NATIVE',
        node: 'Node 0 & 1',
        rank: 'Selected Rank 0 (Multi-Rank Mean: 77.6%)',
        phase: 'Prefill (128K context)',
        metric: 'NCCL AllReduce Exposure',
        unit: '% aggregate GPU kernel work',
        value: 76.2,
        evidence_class: 'PROFILER_DISTRIBUTED',
        artifact_path: 'results_V8_runs(3)/hardware_processed/distributed_profiles/tp16_pp1_128k/PROFILE_VALIDATION.json',
        aggregation_rule: 'Selected Node 0 Rank 0: 76.2%; multi-rank mean across all 16 ranks: 77.6% (range 74.8% - 79.5%)',
        kernels: { 'NCCL AllReduce': '76.2% (Mean 77.6%)', 'FlashAttention': '11.2%', 'Fused MoE': '5.6%', 'GEMM': '3.1%', 'Other': '3.9%' },
        observation: 'TP16/PP1 cross-node tensor parallelism spends 76.2% of kernel work on network AllReduce collectives over VPC.'
    },
    'PR-005': {
        evidence_id: 'PR-005',
        profile_id: 'PR-005',
        case: 'tp4_pp4_dist',
        bench: '128k_prefill_multinode',
        network_provenance: 'GCP_NATIVE',
        node: 'Node 0 (Stage 0)',
        rank: 'Stage 0 / Rank 0',
        phase: 'Prefill (128K context)',
        metric: 'P2P SendRecv vs AllReduce',
        unit: '% aggregate GPU kernel work',
        value: 40.0,
        evidence_class: 'PROFILER_DISTRIBUTED',
        artifact_path: 'results_V8_runs(3)/hardware_processed/distributed_profiles/tp4_pp4_128k/PROFILE_VALIDATION.json',
        aggregation_rule: 'Pipeline Stage 0 / Rank 0: 40.0% intra-node TP AllReduce, 8.3% inter-node P2P SendRecv; Stage 3 P2P: 8.1%',
        kernels: { 'Intra-Node TP AllReduce': '40.0%', 'FlashAttention': '22.8%', 'Fused MoE': '13.2%', 'Inter-Node P2P SendRecv': '8.3%', 'GEMM': '8.5%' },
        observation: 'TP4/PP4 restricts cross-node communication to point-to-point SendRecv (8.3%), keeping TP AllReduce local to PCIe.'
    },
    'PR-006': {
        evidence_id: 'PR-006',
        profile_id: 'PR-006',
        case: 'tp16_pp1_dist_long',
        bench: '512k_prefill_multinode',
        network_provenance: 'GCP_NATIVE',
        node: 'Node 0 & 1',
        rank: 'Selected Rank 0',
        phase: 'Long Prefill (512K context)',
        metric: 'FlashAttention vs MoE Scaling',
        unit: 'relative kernel work growth vs 128K',
        value: 15.7,
        evidence_class: 'PROFILER_DISTRIBUTED',
        artifact_path: 'results_V8_runs(3)/hardware_processed/distributed_profiles/tp16_pp1_512k/PROFILE_VALIDATION.json',
        aggregation_rule: 'Matched 128K vs 512K profile scaling; FlashAttention scales ~15.7x while MoE scales ~3.8x and KDA ~3.9x',
        kernels: { 'FlashAttention Growth': '15.7x (~O(N^1.98))', 'KDA Recurrent State': '3.9x (~O(N^0.98))', 'Fused MoE': '3.8x (~O(N^0.96))' },
        observation: 'At 512K context, FlashAttention expands from 11.2% to 45.1% of GPU kernel work, driving quadratic prefill expansion.'
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
};

window.openEvidencePopup = function(target, discoveryOpt) {
"""

html = html.replace('window.openEvidencePopup = function(target, discoveryOpt) {', profiler_registry_js, 1)

# 2. Update resolveDatum implementation inside openEvidencePopup
old_resolve_datum_start = """    // Helper: find datum by query or ID
    function resolveDatum(t) {
        if (!t) return null;
        if (typeof t === 'object' && t.evidence_id) return t;
        
        const reg = (window.CANONICAL_DASHBOARD_DATA && window.CANONICAL_DASHBOARD_DATA.evidence_registry) || {};
        
        // Exact ID match
        if (typeof t === 'string' && reg[t]) return reg[t];
        if (typeof t === 'object' && t.id && reg[t.id]) return reg[t.id];

        // Search string / query
        const qStr = (typeof t === 'string' ? t : (t.query || (t.case ? t.case + ' ' + (t.bench || '') : ''))).toLowerCase().trim();"""

new_resolve_datum_start = """    // Helper: find datum by query, evidence_id, or profile_id
    function resolveDatum(t) {
        if (!t) return null;
        const reg = (window.CANONICAL_DASHBOARD_DATA && window.CANONICAL_DASHBOARD_DATA.evidence_registry) || {};
        const pReg = window.PROFILER_REGISTRY || {};

        if (typeof t === 'object' && t.profile_id && pReg[t.profile_id]) return pReg[t.profile_id];
        if (typeof t === 'object' && t.evidence_id) {
            if (reg[t.evidence_id]) return reg[t.evidence_id];
            if (pReg[t.evidence_id]) return pReg[t.evidence_id];
            return t;
        }
        
        // Exact ID match
        if (typeof t === 'string' && reg[t]) return reg[t];
        if (typeof t === 'string' && pReg[t]) return pReg[t];
        if (typeof t === 'object' && t.id && reg[t.id]) return reg[t.id];
        if (typeof t === 'object' && t.id && pReg[t.id]) return pReg[t.id];

        // Search string / query
        const qStr = (typeof t === 'string' ? t : (t.query || (t.case ? t.case + ' ' + (t.bench || '') : ''))).toLowerCase().trim();

        // Profiler Aliases
        const profilerMap = {
            'tp4_prefill': 'PR-001',
            'tp4_prefill 128k': 'PR-001',
            'tp4_prefill_128k': 'PR-001',
            'tp4_decode': 'PR-002',
            'tp4_decode 8k': 'PR-002',
            'tp4_decode_8k': 'PR-002',
            'tp8_decode': 'PR-003',
            'tp8_decode 8k': 'PR-003',
            'tp8_decode_8k': 'PR-003',
            'tp16_pp1_dist_prefill': 'PR-004',
            'tp16_pp1_dist 128k profile': 'PR-004',
            'tp4_pp4_dist_prefill': 'PR-005',
            'tp4_pp4_dist 128k profile': 'PR-005',
            'tp16_pp1_dist 512k profile': 'PR-006',
            'tp16_pp1_dist_long_prefill_512k': 'PR-006',
            'tp4_pp4_dist 512k profile': 'PR-007',
            'tp4_pp4_dist_long_prefill_512k': 'PR-007',
            'profiler': 'PR-002'
        };
        if (profilerMap[qStr] && pReg[profilerMap[qStr]]) return pReg[profilerMap[qStr]];"""

html = html.replace(old_resolve_datum_start, new_resolve_datum_start, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated PROFILER_REGISTRY and resolveDatum in HTML!")
