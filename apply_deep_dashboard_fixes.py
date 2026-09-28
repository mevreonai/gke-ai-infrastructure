import re
import os
import json

def update_dashboard_file(filepath):
    print(f"Applying deep audit fixes to {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Ensure PROFILER_REGISTRY is present
    profiler_registry_def = """// First-Class Profiler Artifact Registry (Audit P0 & P2 Closure)
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
        aggregation_rule: 'Rank 0 aggregate Self CUDA time; 7040 AllReduce invocations across 22 layers, average 35.7 μs per collective',
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
        aggregation_rule: 'Rank 0 aggregate Self CUDA time; 7040 AllReduce invocations across NUMA socket PCIe bridges (+332.4 ms barrier overhead vs TP4)',
        kernels: { 'NCCL AllReduce': '89.1% (583.9 ms)', 'cublasGemv': '89.2 ms', 'Fused MoE': '118.2 ms', 'PagedAttention': '38.6 ms', 'RMSNorm': '29.5 ms' },
        observation: 'TP8 Decode 8K spends 583.9 ms in nccl:all_reduce (+132.2% vs TP4) due to cross-NUMA socket PCIe bridge traversal.'
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
    }
};

window.openEvidencePopup = function(target, discoveryOpt) {"""

    if 'window.PROFILER_REGISTRY =' not in content:
        content = content.replace('window.openEvidencePopup = function(target, discoveryOpt) {', profiler_registry_def, 1)

    # 2. Update resolveDatum inside openEvidencePopup
    resolve_datum_full = """    // Helper: find datum by query, evidence_id, or profile_id
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
            'profiler': 'PR-002'
        };
        if (profilerMap[qStr] && pReg[profilerMap[qStr]]) return pReg[profilerMap[qStr]];

        // Exact Query Aliases (100% deterministic, zero ambiguity for distributed and profiler charts)
        const exactMap = {
            // TP4 Context Baselines
            'tp4_context_baseline 8k': 'EV-009',
            'tp4_context_baseline 8k_c1': 'EV-009',
            'tp4_context_baseline 128k': 'EV-010',
            'tp4_context_baseline 128k_c1': 'EV-010',
            'tp4_context_baseline 512k': 'EV-011',
            'tp4_context_baseline 512k_c1': 'EV-011',
            'tp4_context_baseline 1m': 'EV-012',
            'tp4_context_baseline 1m_c1': 'EV-012',

            // TP8 Context Baselines
            'tp8_context_baseline 8k': 'EV-013',
            'tp8_context_baseline 8k_c1': 'EV-013',
            'tp8_context_baseline 128k': 'EV-014',
            'tp8_context_baseline 128k_c1': 'EV-014',
            'tp8_context_baseline 512k': 'EV-015',
            'tp8_context_baseline 512k_c1': 'EV-015',
            'tp8_context_baseline 1m': 'EV-016',
            'tp8_context_baseline 1m_c1': 'EV-016',

            // Distributed Native Topologies (Primary)
            'tp4_pp4_dist 128k': 'EV-082',
            'tp4_pp4_dist 128k_c1': 'EV-082',
            'tp4_pp4_dist 512k': 'EV-083',
            'tp4_pp4_dist 512k_c1': 'EV-083',
            'tp4_pp4_dist 1m': 'EV-084',
            'tp4_pp4_dist 1m_c1': 'EV-084',

            'tp16_pp1_dist 128k': 'EV-085',
            'tp16_pp1_dist 128k_c1': 'EV-085',
            'tp16_pp1_dist 512k': 'EV-086',
            'tp16_pp1_dist 512k_c1': 'EV-086',
            'tp16_pp1_dist 1m': 'EV-087',
            'tp16_pp1_dist 1m_c1': 'EV-087',

            'tp4_pp2_dist 128k': 'EV-076',
            'tp4_pp2_dist 128k_c1': 'EV-076',
            'tp4_pp2_dist 512k': 'EV-077',
            'tp4_pp2_dist 512k_c1': 'EV-077',
            'tp4_pp2_dist 1m': 'EV-078',
            'tp4_pp2_dist 1m_c1': 'EV-078',

            'tp8_pp2_dist 128k': 'EV-079',
            'tp8_pp2_dist 128k_c1': 'EV-079',
            'tp8_pp2_dist 512k': 'EV-080',
            'tp8_pp2_dist 512k_c1': 'EV-080',
            'tp8_pp2_dist 1m': 'EV-081',
            'tp8_pp2_dist 1m_c1': 'EV-081',

            // 1M Concurrency Extensions
            'tp4_1m_concurrency_extension 1m_c1': 'EV-065',
            'tp4_1m_concurrency_extension 1m_c2': 'EV-066',
            'tp4_1m_concurrency_extension 1m_c4': 'EV-067',
            'tp8_1m_concurrency_extension 1m_c1': 'EV-068',
            'tp8_1m_concurrency_extension 1m_c2': 'EV-069',
            'tp8_1m_concurrency_extension 1m_c4': 'EV-070',

            // Capped 100G Distributed Topologies
            'tp4_pp4_dist 128k gcp_capped_100g': 'EV-094',
            'tp4_pp4_dist 512k gcp_capped_100g': 'EV-095',
            'tp4_pp4_dist 1m gcp_capped_100g': 'EV-096',
            'tp16_pp1_dist 128k gcp_capped_100g': 'EV-097',
            'tp16_pp1_dist 512k gcp_capped_100g': 'EV-098',
            'tp16_pp1_dist 1m gcp_capped_100g': 'EV-099',
            'tp4_pp2_dist 128k gcp_capped_100g': 'EV-088',
            'tp4_pp2_dist 512k gcp_capped_100g': 'EV-089',
            'tp4_pp2_dist 1m gcp_capped_100g': 'EV-090',
            'tp8_pp2_dist 128k gcp_capped_100g': 'EV-091',
            'tp8_pp2_dist 512k gcp_capped_100g': 'EV-092',
            'tp8_pp2_dist 1m gcp_capped_100g': 'EV-093',

            // Capped 20G Distributed Topologies
            'tp4_pp4_dist 128k gcp_capped_20g': 'EV-106',
            'tp4_pp4_dist 512k gcp_capped_20g': 'EV-107',
            'tp4_pp4_dist 1m gcp_capped_20g': 'EV-108',
            'tp16_pp1_dist 128k gcp_capped_20g': 'EV-109',
            'tp16_pp1_dist 512k gcp_capped_20g': 'EV-110',
            'tp16_pp1_dist 1m gcp_capped_20g': 'EV-111',
            'tp4_pp2_dist 128k gcp_capped_20g': 'EV-100',
            'tp4_pp2_dist 512k gcp_capped_20g': 'EV-101',
            'tp4_pp2_dist 1m gcp_capped_20g': 'EV-102',
            'tp8_pp2_dist 128k gcp_capped_20g': 'EV-103',
            'tp8_pp2_dist 512k gcp_capped_20g': 'EV-104',
            'tp8_pp2_dist 1m gcp_capped_20g': 'EV-105',

            // Scheduler MaxSeq & Chunk
            'tp4_1m_maxseq4': 'EV-071',
            'tp4_1m_maxseq8': 'EV-072',
            'tp4_1m_maxseq16': 'EV-073',
            'tp4_chunk4k 1m_c1': 'EV-027',
            'tp4_chunk8k 1m_c1': 'EV-031',
            'tp4_chunk16k 1m_c1': 'EV-035',

            // Prefix Re-use
            'tp4_prefix128k': 'EV-073',
            'tp4_prefix512k': 'EV-074',
            'tp4_prefix1m': 'EV-075',

            // Open-loop sweeps
            'tp4_openloop_8192 0.25x': 'EV-112',
            'tp4_openloop_8192 0.50x': 'EV-113',
            'tp4_openloop_8192 0.75x': 'EV-114',
            'tp4_openloop_8192 0.90x': 'EV-115',
            'tp4_openloop_8192 1.00x': 'EV-116',
            'tp4_openloop_8192 1.10x': 'EV-117',
            'tp4_openloop_8192 1.25x': 'EV-118',
            'tp4_openloop_131072 0.25x': 'EV-119',
            'tp4_openloop_131072 0.50x': 'EV-120',
            'tp4_openloop_131072 0.75x': 'EV-121',
            'tp4_openloop_131072 0.90x': 'EV-122',
            'tp4_openloop_131072 1.00x': 'EV-123',
            'tp4_openloop_131072 1.10x': 'EV-124',
            'tp4_openloop_131072 1.25x': 'EV-125'
        };

        if (exactMap[qStr]) {
            const mappedId = exactMap[qStr];
            if (reg[mappedId]) return reg[mappedId];
            if (pReg[mappedId]) return pReg[mappedId];
        }

        const tokens = qStr.split(/\s+/).filter(Boolean);
        // Default distributed queries to GCP_NATIVE if no network specified
        if (tokens.some(tok => tok.includes('dist')) && !tokens.some(tok => ['native', '100g', '20g', '50g', '10g'].includes(tok))) {
            tokens.push('gcp_native');
        }

        for (let [evId, rec] of Object.entries(reg)) {
            const hay = `${evId} ${rec.case} ${rec.bench} ${rec.network_provenance}`.toLowerCase();
            if (tokens.every(tok => hay.includes(tok))) {
                return rec;
            }
        }
        return null;
    }"""

    # Replace resolveDatum block cleanly
    resolve_datum_pattern = r'    // Helper: find datum by query.*?return null;\s+\}'
    content = re.sub(resolve_datum_pattern, lambda m: resolve_datum_full, content, flags=re.DOTALL)

    # 3. Update Drawer Renderer to format Profiler records rich & clean
    old_drawer_title_block = """    // 1. Title & Header
    const titleEl = document.getElementById('popup-title');
    const badgesEl = document.getElementById('popup-badges');
    titleEl.innerText = discovery ? (discovery.title + (discovery.sub_title ? ' — ' + discovery.sub_title : '')) : ((datum ? datum.case + ' / ' + datum.bench : 'Evidence Record'));

    let badgesHtml = '';
    if (datum && datum.evidence_id) {
        badgesHtml += `<span class="badge b-cyan" style="font-weight:700">${datum.evidence_id}</span>`;
    }
    if (discovery && discovery.evidence_confidence) {
        badgesHtml += `<span class="badge b-green">Evidence: ${discovery.evidence_confidence}</span>`;
    }
    if (discovery && discovery.causal_confidence) {
        badgesHtml += `<span class="badge b-purple">Causal: ${discovery.causal_confidence}</span>`;
    }
    if (datum && datum.evidence_class) {
        badgesHtml += `<span class="badge b-amber">${datum.evidence_class}</span>`;
    }
    if (datum && datum.network_provenance) {
        badgesHtml += `<span class="badge b-cyan">${datum.network_provenance}</span>`;
    }
    badgesEl.innerHTML = badgesHtml;"""

    new_drawer_title_block = """    // 1. Title & Header
    const titleEl = document.getElementById('popup-title');
    const badgesEl = document.getElementById('popup-badges');
    titleEl.innerText = discovery ? (discovery.title + (discovery.sub_title ? ' — ' + discovery.sub_title : '')) : (datum ? (datum.profile_id ? `${datum.profile_id} — ${datum.case} (${datum.phase})` : `${datum.case} / ${datum.bench}`) : 'Evidence Record');

    let badgesHtml = '';
    if (datum && datum.profile_id) {
        badgesHtml += `<span class="badge b-purple" style="font-weight:700">${datum.profile_id}</span>`;
        badgesHtml += `<span class="badge b-cyan">${datum.evidence_class || 'PROFILER'}</span>`;
        badgesHtml += `<span class="badge b-green">${datum.node || 'Node 0'}</span>`;
        badgesHtml += `<span class="badge b-amber">Rank: ${datum.rank !== undefined ? datum.rank : '0'}</span>`;
        badgesHtml += `<span class="badge b-purple">${datum.phase || ''}</span>`;
    } else {
        if (datum && datum.evidence_id) {
            badgesHtml += `<span class="badge b-cyan" style="font-weight:700">${datum.evidence_id}</span>`;
        }
        if (discovery && discovery.evidence_confidence) {
            badgesHtml += `<span class="badge b-green">Evidence: ${discovery.evidence_confidence}</span>`;
        }
        if (discovery && discovery.causal_confidence) {
            badgesHtml += `<span class="badge b-purple">Causal: ${discovery.causal_confidence}</span>`;
        }
        if (datum && datum.evidence_class) {
            badgesHtml += `<span class="badge b-amber">${datum.evidence_class}</span>`;
        }
        if (datum && datum.network_provenance) {
            badgesHtml += `<span class="badge b-cyan">${datum.network_provenance}</span>`;
        }
    }
    badgesEl.innerHTML = badgesHtml;"""

    content = content.replace(old_drawer_title_block, new_drawer_title_block)

    # 4. Update Tab 1 Observation and Measured Values for Profiler
    old_mv_block = """    const mvEl = document.getElementById('popup-measured-values');
    if (discovery && discovery.exact_measured_values) {"""

    new_mv_block = """    const mvEl = document.getElementById('popup-measured-values');
    if (datum && datum.kernels) {
        let kHtml = '<table style="width:100%;font-size:9.5px"><thead><tr><th>Kernel / Collective Component</th><th>Attribution / Work Share</th></tr></thead><tbody>';
        for (let [kName, kVal] of Object.entries(datum.kernels)) {
            kHtml += `<tr><td><b>${kName}</b></td><td style="color:var(--cyan);font-weight:700">${kVal}</td></tr>`;
        }
        kHtml += '</tbody></table>';
        mvEl.innerHTML = kHtml;
    } else if (discovery && discovery.exact_measured_values) {"""

    content = content.replace(old_mv_block, new_mv_block)

    # 5. Update Tab 2 Telemetry for Profiler
    old_telemetry_block = """    // 3. Tab 2: Measured Telemetry
    const kpiEl = document.getElementById('popup-telemetry-kpis');
    if (datum) {"""

    new_telemetry_block = """    // 3. Tab 2: Measured Telemetry
    const kpiEl = document.getElementById('popup-telemetry-kpis');
    if (datum && datum.profile_id) {
        kpiEl.innerHTML = `
            <div class="card kpi"><div class="k-label">Profile ID</div><div class="k-value" style="color:var(--purple)">${datum.profile_id}</div><div class="k-note">${datum.phase}</div></div>
            <div class="card kpi"><div class="k-label">Primary Metric</div><div class="k-value" style="color:var(--cyan)">${datum.value} ${datum.unit}</div><div class="k-note">${datum.metric}</div></div>
            <div class="card kpi"><div class="k-label">Rank Provenance</div><div class="k-value" style="color:var(--green)">${datum.rank !== undefined ? datum.rank : 'All-Rank'}</div><div class="k-note">${datum.node}</div></div>
            <div class="card kpi"><div class="k-label">Artifact Class</div><div class="k-value" style="color:var(--amber)">${datum.evidence_class}</div><div class="k-note">Nsight / PyTorch</div></div>
        `;
        document.getElementById('popup-telemetry-config').innerHTML = `
            <table style="width:100%;font-size:9.5px">
                <tr><th>Case / Workload</th><th>Phase</th><th>Node</th><th>Rank</th><th>Aggregation Rule</th></tr>
                <tr>
                    <td><b>${datum.case}</b></td>
                    <td>${datum.phase}</td>
                    <td>${datum.node}</td>
                    <td>${datum.rank}</td>
                    <td>${datum.aggregation_rule}</td>
                </tr>
            </table>
        `;
        document.getElementById('popup-telemetry-network').innerHTML = `<b>Artifact Trace:</b> <code>${datum.artifact_path}</code>`;
    } else if (datum) {"""

    content = content.replace(old_telemetry_block, new_telemetry_block)

    # 6. Update Structured JSON & Footer for Profiler
    old_json_block = """    const datumObj = datum ? {
        "evidence_id": datum.evidence_id || "EV-DERIVED","""

    new_json_block = """    const datumObj = datum ? (datum.profile_id ? datum : {
        "evidence_id": datum.evidence_id || "EV-DERIVED","""

    content = content.replace(old_json_block, new_json_block)

    old_footer_block = """    // 6. Footer info
    document.getElementById('popup-footer-info').innerHTML = datum ? `ID: <b>${datum.evidence_id}</b> | Case: <b>${datum.case}</b> (${datum.bench})` : `Discovery: <b>${discovery.title}</b>`;"""

    new_footer_block = """    // 6. Footer info
    document.getElementById('popup-footer-info').innerHTML = datum ? (datum.profile_id ? `Profile ID: <b>${datum.profile_id}</b> | Case: <b>${datum.case}</b> (${datum.phase})` : `ID: <b>${datum.evidence_id}</b> | Case: <b>${datum.case}</b> (${datum.bench})`) : `Discovery: <b>${discovery.title}</b>`;"""

    content = content.replace(old_footer_block, new_footer_block)

    # 7. Update Chart Click Handlers to bind direct canonical evidence_id / profile_id
    # Chart 1: chart_exec_ttft
    old_exec_ttft_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const topoMap = ['tp4_context_baseline', 'tp8_context_baseline', 'tp4_pp4_dist', 'tp16_pp1_dist'];
                const ctxMap = ['128k', '512k', '1m'];
                return { query: `${topoMap[dsIdx]} ${ctxMap[idx]}` };
            })"""

    new_exec_ttft_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const grid = [
                    ['EV-010', 'EV-011', 'EV-012'], // TP4: 128k, 512k, 1m
                    ['EV-014', 'EV-015', 'EV-016'], // TP8: 128k, 512k, 1m
                    ['EV-082', 'EV-083', 'EV-084'], // TP4/PP4: 128k, 512k, 1m
                    ['EV-085', 'EV-086', 'EV-087']  // TP16/PP1: 128k, 512k, 1m
                ];
                return grid[dsIdx] && grid[dsIdx][idx] ? { evidence_id: grid[dsIdx][idx] } : null;
            })"""
    content = content.replace(old_exec_ttft_click, new_exec_ttft_click)

    # Chart 2: chart_exec_tpot
    old_exec_tpot_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const topoMap = ['tp4_context_baseline', 'tp8_context_baseline', 'tp4_pp4_dist', 'tp16_pp1_dist'];
                const ctxMap = ['8k', '128k', '512k', '1m'];
                return { query: `${topoMap[dsIdx]} ${ctxMap[idx]}` };
            })"""

    new_exec_tpot_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const grid = [
                    ['EV-009', 'EV-010', 'EV-011', 'EV-012'], // TP4: 8k, 128k, 512k, 1m
                    ['EV-013', 'EV-014', 'EV-015', 'EV-016'], // TP8: 8k, 128k, 512k, 1m
                    [null, 'EV-082', 'EV-083', 'EV-084'],     // TP4/PP4
                    [null, 'EV-085', 'EV-086', 'EV-087']      // TP16/PP1
                ];
                return grid[dsIdx] && grid[dsIdx][idx] ? { evidence_id: grid[dsIdx][idx] } : null;
            })"""
    content = content.replace(old_exec_tpot_click, new_exec_tpot_click)

    # Chart 3: chart_exec_capacity
    old_exec_cap_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                if (dsIdx === 0) {
                    const cMap = ['c1', 'c4', 'c8', 'c16', 'c32'];
                    return { query: `tp4_closedloop_8k ${cMap[idx]}` };
                } else {
                    const cMap = ['8k_c1', '', '8k_c8', '', ''];
                    return { query: `tp8_qualification ${cMap[idx]}` };
                }
            })"""

    new_exec_cap_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                if (dsIdx === 0) {
                    const ids = ['EV-036', 'EV-037', 'EV-038', 'EV-039', 'EV-040'];
                    return { evidence_id: ids[idx] };
                } else {
                    const ids = ['EV-005', null, 'EV-006', null, null];
                    return ids[idx] ? { evidence_id: ids[idx] } : null;
                }
            })"""
    content = content.replace(old_exec_cap_click, new_exec_cap_click)

    # Chart 4: chart_scaleup_ttft
    old_scaleup_ttft_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const tp = dsIdx === 0 ? 'tp4_context_baseline' : 'tp8_context_baseline';
                const ctx = ['8k_c1', '128k_c1', '512k_c1', '1m_c1'][idx];
                return { query: `${tp} ${ctx}` };
            })"""

    new_scaleup_ttft_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const grid = [
                    ['EV-009', 'EV-010', 'EV-011', 'EV-012'],
                    ['EV-013', 'EV-014', 'EV-015', 'EV-016']
                ];
                return { evidence_id: grid[dsIdx][idx] };
            })"""
    content = content.replace(old_scaleup_ttft_click, new_scaleup_ttft_click)

    # Chart 5: chart_scaleup_tpot
    old_scaleup_tpot_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const tp = dsIdx === 0 ? 'tp4_context_baseline' : 'tp8_context_baseline';
                const ctx = ['8k_c1', '128k_c1', '512k_c1', '1m_c1'][idx];
                return { query: `${tp} ${ctx}` };
            })"""

    new_scaleup_tpot_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const grid = [
                    ['EV-009', 'EV-010', 'EV-011', 'EV-012'],
                    ['EV-013', 'EV-014', 'EV-015', 'EV-016']
                ];
                return { evidence_id: grid[dsIdx][idx] };
            })"""
    content = content.replace(old_scaleup_tpot_click, new_scaleup_tpot_click)

    # Chart 6: chart_scaleup_tps
    old_scaleup_tps_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const tp = dsIdx === 0 ? 'tp4_context_baseline' : 'tp8_context_baseline';
                const bench = ['8k_c1', '128k_c1', '512k_c1', '1m_c1'][idx];
                return { query: `${tp} ${bench}` };
            })"""

    new_scaleup_tps_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const grid = [
                    ['EV-009', 'EV-010', 'EV-011', 'EV-012'],
                    ['EV-013', 'EV-014', 'EV-015', 'EV-016']
                ];
                return { evidence_id: grid[dsIdx][idx] };
            })"""
    content = content.replace(old_scaleup_tps_click, new_scaleup_tps_click)

    # Chart 7: chart_scaleup_concurrency
    old_scaleup_concurrency_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                if (dsIdx === 0) {
                    const cMap = ['c1', 'c4', 'c8', 'c16', 'c32'];
                    return { query: `tp4_closedloop_8k ${cMap[idx]}` };
                } else {
                    const cMap = ['8k_c1', '', '8k_c8', '', ''];
                    return { query: `tp8_qualification ${cMap[idx]}` };
                }
            })"""

    new_scaleup_concurrency_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                if (dsIdx === 0) {
                    const ids = ['EV-036', 'EV-037', 'EV-038', 'EV-039', 'EV-040'];
                    return { evidence_id: ids[idx] };
                } else {
                    const ids = ['EV-005', null, 'EV-006', null, null];
                    return ids[idx] ? { evidence_id: ids[idx] } : null;
                }
            })"""
    content = content.replace(old_scaleup_concurrency_click, new_scaleup_concurrency_click)

    # Chart 8: chart_scaleup_nccl
    old_scaleup_nccl = """    // Chart 8: Local NCCL All-Reduce Bus Bandwidth
    safeInitChart('chart_scaleup_nccl', {
        type: 'bar',
        data: {
            labels: ['16KB', '128KB', '512KB', '64MB', '128MB', '256MB'],
            datasets: [
                { label: 'TP4 PCIe/NUMA BusBW (GB/s)', data: [1.25, 6.87, 10.06, 25.25, 25.50, 25.95], backgroundColor: 'rgba(66,201,255,0.7)' },
                { label: 'TP8 PCIe/NUMA BusBW (GB/s)', data: [0.77, 4.20, 5.44, 25.08, 25.60, 25.04], backgroundColor: 'rgba(57,217,138,0.7)' }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { title: { display: true, text: 'Bus Bandwidth (GB/s)' } } } }
    });"""

    new_scaleup_nccl = """    // Chart 8: Local NCCL All-Reduce Bus Bandwidth
    safeInitChart('chart_scaleup_nccl', {
        type: 'bar',
        data: {
            labels: ['16KB', '128KB', '512KB', '64MB', '128MB', '256MB'],
            datasets: [
                { label: 'TP4 PCIe/NUMA BusBW (GB/s)', data: [1.25, 6.87, 10.06, 25.25, 25.50, 25.95], backgroundColor: 'rgba(66,201,255,0.7)' },
                { label: 'TP8 PCIe/NUMA BusBW (GB/s)', data: [0.77, 4.20, 5.44, 25.08, 25.60, 25.04], backgroundColor: 'rgba(57,217,138,0.7)' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { title: { display: true, text: 'Bus Bandwidth (GB/s)' } } },
            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                return { profile_id: dsIdx === 0 ? 'PR-002' : 'PR-003' };
            })
        }
    });"""
    content = content.replace(old_scaleup_nccl, new_scaleup_nccl)

    # Chart 9 & 10: Scaleout comparison & context scaling
    old_scaleout_comp_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const topos = ['tp4_pp4_dist', 'tp8_pp2_dist', 'tp4_pp2_dist', 'tp16_pp1_dist'];
                const ctxs = ['128k', '512k', '1m'];
                return { query: `${topos[dsIdx]} ${ctxs[idx]} ${activeScaleoutNet}` };
            })"""

    new_scaleout_comp_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const netMap = {
                    'GCP_NATIVE': [
                        ['EV-082', 'EV-083', 'EV-084'],
                        ['EV-079', 'EV-080', 'EV-081'],
                        ['EV-076', 'EV-077', 'EV-078'],
                        ['EV-085', 'EV-086', 'EV-087']
                    ],
                    'GCP_CAPPED_100G': [
                        ['EV-094', 'EV-095', 'EV-096'],
                        ['EV-091', 'EV-092', 'EV-093'],
                        ['EV-088', 'EV-089', 'EV-090'],
                        ['EV-097', 'EV-098', 'EV-099']
                    ],
                    'GCP_CAPPED_20G': [
                        ['EV-106', 'EV-107', 'EV-108'],
                        ['EV-103', 'EV-104', 'EV-105'],
                        ['EV-100', 'EV-101', 'EV-102'],
                        ['EV-109', 'EV-110', 'EV-111']
                    ]
                };
                const matrix = netMap[activeScaleoutNet] || netMap['GCP_NATIVE'];
                if (activeScaleoutCtx === 'ALL') {
                    return matrix[dsIdx] && matrix[dsIdx][idx] ? { evidence_id: matrix[dsIdx][idx] } : null;
                } else {
                    const ctxIdx = activeScaleoutCtx === '128K' ? 0 : (activeScaleoutCtx === '512K' ? 1 : 2);
                    return matrix[idx] && matrix[idx][ctxIdx] ? { evidence_id: matrix[idx][ctxIdx] } : null;
                }
            })"""
    content = content.replace(old_scaleout_comp_click, new_scaleout_comp_click)

    old_scaleout_ctx_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const topos = ['tp4_pp4_dist', 'tp8_pp2_dist', 'tp4_pp2_dist', 'tp16_pp1_dist'];
                const ctxs = ['128k', '512k', '1m'];
                return { query: `${topos[dsIdx]} ${ctxs[idx]} ${activeScaleoutNet}` };
            })"""
    content = content.replace(old_scaleout_ctx_click, new_scaleout_comp_click)

    # Chart 11: chart_long_concurrency
    old_long_concurrency_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const tp = dsIdx === 0 ? 'tp4_1m_concurrency_extension' : 'tp8_1m_concurrency_extension';
                const c = ['1m_c1', '1m_c2', '1m_c4'][idx];
                return { query: `${tp} ${c}` };
            })"""

    new_long_concurrency_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const grid = [
                    ['EV-065', 'EV-066', 'EV-067'],
                    ['EV-068', 'EV-069', 'EV-070']
                ];
                return { evidence_id: grid[dsIdx][idx] };
            })"""
    content = content.replace(old_long_concurrency_click, new_long_concurrency_click)

    # Chart 12: chart_long_scheduler
    old_long_sched_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const cases = ['tp4_1m_maxseq4', 'tp4_1m_maxseq8', 'tp4_1m_maxseq16'];
                return { query: cases[idx] };
            })"""

    new_long_sched_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const ids = ['EV-071', 'EV-072', 'EV-073'];
                return { evidence_id: ids[idx] };
            })"""
    content = content.replace(old_long_sched_click, new_long_sched_click)

    # Chart 13: chart_long_chunk
    old_long_chunk_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const cases = ['tp4_chunk4k', 'tp4_chunk8k', 'tp4_chunk16k'];
                return { query: `${cases[idx]} 1m_c1` };
            })"""

    new_long_chunk_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const ids = ['EV-027', 'EV-031', 'EV-035'];
                return { evidence_id: ids[idx] };
            })"""
    content = content.replace(old_long_chunk_click, new_long_chunk_click)

    # Chart 15: chart_long_prefix
    old_long_prefix_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const cases = ['tp4_prefix128k', 'tp4_prefix512k', 'tp4_prefix1m'];
                return { query: cases[idx] };
            })"""

    new_long_prefix_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const ids = ['EV-073', 'EV-074', 'EV-075'];
                return { evidence_id: ids[idx] };
            })"""
    content = content.replace(old_long_prefix_click, new_long_prefix_click)

    # Chart 17: chart_sched_kv
    old_sched_kv_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const topos = ['tp4_context_baseline', 'tp8_context_baseline', 'tp4_pp4', 'tp8_pp2', 'tp4_pp2', 'tp16_pp1'];
                const ctxs = ['8k', '128k', '512k', '1m'];
                return { query: `${topos[dsIdx]} ${ctxs[idx]}` };
            })"""

    new_sched_kv_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const grid = [
                    ['EV-009', 'EV-010', 'EV-011', 'EV-012'], // TP4
                    ['EV-013', 'EV-014', 'EV-015', 'EV-016'], // TP8
                    [null, 'EV-082', 'EV-083', 'EV-084'],     // TP4/PP4
                    [null, 'EV-079', 'EV-080', 'EV-081'],     // TP8/PP2
                    [null, 'EV-076', 'EV-077', 'EV-078'],     // TP4/PP2
                    [null, 'EV-085', 'EV-086', 'EV-087']      // TP16/PP1
                ];
                return grid[dsIdx] && grid[dsIdx][idx] ? { evidence_id: grid[dsIdx][idx] } : null;
            })"""
    content = content.replace(old_sched_kv_click, new_sched_kv_click)

    # Chart 19: chart_sched_queue_mean
    old_sched_queue_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const cases = ['tp4_1m_concurrency_extension 1m_c1', 'tp4_1m_concurrency_extension 1m_c2', 'tp4_1m_concurrency_extension 1m_c4', 'tp8_1m_concurrency_extension 1m_c1', 'tp8_1m_concurrency_extension 1m_c2', 'tp8_1m_concurrency_extension 1m_c4', 'tp4_pp4_dist 1m_c1', 'tp16_pp1_dist 1m_c1'];
                return { query: cases[idx] };
            })"""

    new_sched_queue_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const ids = ['EV-065', 'EV-066', 'EV-067', 'EV-068', 'EV-069', 'EV-070', 'EV-084', 'EV-087'];
                return { evidence_id: ids[idx] };
            })"""
    content = content.replace(old_sched_queue_click, new_sched_queue_click)

    # Chart 21: chart_sched_max_seqs
    old_sched_max_seqs_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const cases = ['tp4_1m_maxseq4', 'tp4_1m_maxseq8', 'tp4_1m_maxseq16'];
                return { query: cases[idx] };
            })"""

    new_sched_max_seqs_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const ids = ['EV-071', 'EV-072', 'EV-073'];
                return { evidence_id: ids[idx] };
            })"""
    content = content.replace(old_sched_max_seqs_click, new_sched_max_seqs_click)

    # Chart 23a & 23b: open loop sweeps
    old_open_loop_8k_click = "onClick: makeChartClickHandler((chart, dsIdx, idx) => { const rps = ['0.25x', '0.50x', '0.75x', '0.90x', '1.00x', '1.10x', '1.25x'][idx]; return { query: 'tp4_openloop_8192 ' + rps }; })"
    new_open_loop_8k_click = "onClick: makeChartClickHandler((chart, dsIdx, idx) => { const ids = ['EV-112', 'EV-113', 'EV-114', 'EV-115', 'EV-116', 'EV-117', 'EV-118']; return { evidence_id: ids[idx] }; })"
    content = content.replace(old_open_loop_8k_click, new_open_loop_8k_click)

    old_open_loop_128k_click = "onClick: makeChartClickHandler((chart, dsIdx, idx) => { const rps = ['0.25x', '0.50x', '0.75x', '0.90x', '1.00x', '1.10x', '1.25x'][idx]; return { query: 'tp4_openloop_131072 ' + rps }; })"
    new_open_loop_128k_click = "onClick: makeChartClickHandler((chart, dsIdx, idx) => { const ids = ['EV-119', 'EV-120', 'EV-121', 'EV-122', 'EV-123', 'EV-124', 'EV-125']; return { evidence_id: ids[idx] }; })"
    content = content.replace(old_open_loop_128k_click, new_open_loop_128k_click)

    # Chart 24: chart_prof_kernel_categories
    old_prof_kernel_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const queries = ['tp4_prefill', 'tp4_decode', 'tp8_decode', 'tp16_pp1_dist', 'tp4_pp4_dist'];
                return { query: queries[dsIdx] || 'profiler' };
            })"""

    new_prof_kernel_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const prMap = ['PR-001', 'PR-002', 'PR-003', 'PR-004', 'PR-005'];
                return { profile_id: prMap[dsIdx] };
            })"""
    content = content.replace(old_prof_kernel_click, new_prof_kernel_click)

    # Chart 25: chart_prof_pytorch_operators
    old_prof_torch_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                return { query: dsIdx === 0 ? 'tp4_decode' : 'tp8_decode' };
            })"""

    new_prof_torch_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                return { profile_id: dsIdx === 0 ? 'PR-002' : 'PR-003' };
            })"""
    content = content.replace(old_prof_torch_click, new_prof_torch_click)

    # Chart 26: chart_prof_cuda_api
    old_prof_cuda_api = """    // Chart 26: CUDA Aggregate Host API Time (cuda_api_sum.csv)
    safeInitChart('chart_prof_cuda_api', {
        type: 'bar',
        data: {
            labels: ['cudaEventSynchronize', 'cudaLaunchKernel', 'cuLaunchKernelEx', 'cudaMemcpyAsync', 'cudaStreamWaitEvent', 'cudaLaunchKernelExC', 'cudaEventRecord'],
            datasets: [
                { label: 'Aggregate Host API Time (s)', data: [3.638, 3.466, 1.530, 0.710, 0.361, 0.359, 0.286], backgroundColor: 'rgba(255,200,87,0.85)', yAxisID: 'y' },
                { label: 'Share of Host API Time (%)', data: [32.8, 31.2, 13.8, 6.4, 3.2, 3.2, 2.6], backgroundColor: 'rgba(57,217,138,0.75)', yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { type: 'linear', position: 'left', title: { display: true, text: 'Aggregate Host API Time (seconds)' } },
                y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'Time Share (%)' } }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        afterBody: (context) => {
                            const calls = [
                                '512 calls (7.1 ms avg per sync)',
                                '888,504 calls (3.9 μs avg per launch)',
                                '389,896 calls (3.9 μs avg per launch)',
                                '90,224 calls (7.9 μs avg per copy)',
                                '337,712 calls (1.1 μs avg per wait)',
                                '67,584 calls (5.3 μs avg per launch)',
                                '229,376 calls (1.2 μs avg per record)'
                            ];
                            return [`Call count: ${calls[context[0].dataIndex]}`, 'Canonical Nsight Systems tp4_decode/cuda_api_sum.csv export'];
                        }
                    }
                }
            }
        }
    });"""

    new_prof_cuda_api = """    // Chart 26: CUDA Aggregate Host API Time (cuda_api_sum.csv)
    safeInitChart('chart_prof_cuda_api', {
        type: 'bar',
        data: {
            labels: ['cudaEventSynchronize', 'cudaLaunchKernel', 'cuLaunchKernelEx', 'cudaMemcpyAsync', 'cudaStreamWaitEvent', 'cudaLaunchKernelExC', 'cudaEventRecord'],
            datasets: [
                { label: 'Aggregate Host API Time (s)', data: [3.638, 3.466, 1.530, 0.710, 0.361, 0.359, 0.286], backgroundColor: 'rgba(255,200,87,0.85)', yAxisID: 'y' },
                { label: 'Share of Host API Time (%)', data: [32.8, 31.2, 13.8, 6.4, 3.2, 3.2, 2.6], backgroundColor: 'rgba(57,217,138,0.75)', yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { type: 'linear', position: 'left', title: { display: true, text: 'Aggregate Host API Time (seconds)' } },
                y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'Time Share (%)' } }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        afterBody: (context) => {
                            const calls = [
                                '512 calls (7.1 ms avg per sync)',
                                '888,504 calls (3.9 μs avg per launch)',
                                '389,896 calls (3.9 μs avg per launch)',
                                '90,224 calls (7.9 μs avg per copy)',
                                '337,712 calls (1.1 μs avg per wait)',
                                '67,584 calls (5.3 μs avg per launch)',
                                '229,376 calls (1.2 μs avg per record)'
                            ];
                            return [`Call count: ${calls[context[0].dataIndex]}`, 'Canonical Nsight Systems tp4_decode/cuda_api_sum.csv export'];
                        }
                    }
                }
            },
            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                return { profile_id: 'PR-002' };
            })
        }
    });"""
    content = content.replace(old_prof_cuda_api, new_prof_cuda_api)

    # Chart 27: chart_prof_kernel_latency
    old_prof_latency_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const queries = ['tp4_prefill 128k', 'tp4_decode 8k', 'tp4_prefill 128k', 'tp4_prefill 128k', 'tp4_prefill 128k', 'tp4_decode 8k', 'tp4_decode 8k', 'tp4_pp4_dist 128k'];
                return { query: queries[idx] || 'profiler' };
            })"""

    new_prof_latency_click = """            onClick: makeChartClickHandler((chart, dsIdx, idx) => {
                const prMap = ['PR-001', 'PR-002', 'PR-001', 'PR-001', 'PR-001', 'PR-002', 'PR-002', 'PR-005'];
                return { profile_id: prMap[idx] };
            })"""
    content = content.replace(old_prof_latency_click, new_prof_latency_click)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully applied deep audit fixes to {filepath}")

for p in [
    'v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/dashboards/v4_dashboard/index.html',
    'v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/release_specs/index.html'
]:
    if os.path.exists(p):
        update_dashboard_file(p)
