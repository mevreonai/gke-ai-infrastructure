import json
import re

with open('v8_full_results/dashboards/v4_dashboard/DASHBOARD_CANONICAL_DATA.json', 'r', encoding='utf-8') as f:
    canon = json.load(f)

reg = canon['evidence_registry']

appendix_a = [
    ('tp4_context_baseline 8k', 'EV-009', 'tp4_context_baseline', '8k_c1', 'SINGLE_NODE_LOCAL'),
    ('tp4_context_baseline 128k', 'EV-010', 'tp4_context_baseline', '128k_c1', 'SINGLE_NODE_LOCAL'),
    ('tp4_context_baseline 512k', 'EV-011', 'tp4_context_baseline', '512k_c1', 'SINGLE_NODE_LOCAL'),
    ('tp4_context_baseline 1m', 'EV-012', 'tp4_context_baseline', '1m_c1', 'SINGLE_NODE_LOCAL'),
    ('tp8_context_baseline 8k', 'EV-013', 'tp8_context_baseline', '8k_c1', 'SINGLE_NODE_LOCAL'),
    ('tp8_context_baseline 128k', 'EV-014', 'tp8_context_baseline', '128k_c1', 'SINGLE_NODE_LOCAL'),
    ('tp8_context_baseline 512k', 'EV-015', 'tp8_context_baseline', '512k_c1', 'SINGLE_NODE_LOCAL'),
    ('tp8_context_baseline 1m', 'EV-016', 'tp8_context_baseline', '1m_c1', 'SINGLE_NODE_LOCAL'),
    ('tp4_pp4_dist 128k', 'EV-082', 'tp4_pp4_dist', '128k_c1', 'GCP_NATIVE'),
    ('tp4_pp4_dist 512k', 'EV-083', 'tp4_pp4_dist', '512k_c1', 'GCP_NATIVE'),
    ('tp4_pp4_dist 1m', 'EV-084', 'tp4_pp4_dist', '1m_c1', 'GCP_NATIVE'),
    ('tp16_pp1_dist 128k', 'EV-085', 'tp16_pp1_dist', '128k_c1', 'GCP_NATIVE'),
    ('tp16_pp1_dist 512k', 'EV-086', 'tp16_pp1_dist', '512k_c1', 'GCP_NATIVE'),
    ('tp16_pp1_dist 1m', 'EV-087', 'tp16_pp1_dist', '1m_c1', 'GCP_NATIVE'),
    ('tp4_pp2_dist 128k', 'EV-076', 'tp4_pp2_dist', '128k_c1', 'GCP_NATIVE'),
    ('tp4_pp2_dist 512k', 'EV-077', 'tp4_pp2_dist', '512k_c1', 'GCP_NATIVE'),
    ('tp4_pp2_dist 1m', 'EV-078', 'tp4_pp2_dist', '1m_c1', 'GCP_NATIVE'),
    ('tp8_pp2_dist 128k', 'EV-079', 'tp8_pp2_dist', '128k_c1', 'GCP_NATIVE'),
    ('tp8_pp2_dist 512k', 'EV-080', 'tp8_pp2_dist', '512k_c1', 'GCP_NATIVE'),
    ('tp8_pp2_dist 1m', 'EV-081', 'tp8_pp2_dist', '1m_c1', 'GCP_NATIVE'),
    ('tp4_1m_concurrency_extension 1m_c1', 'EV-065', 'tp4_1m_concurrency_extension', '1m_c1', 'SINGLE_NODE_LOCAL'),
    ('tp4_1m_concurrency_extension 1m_c2', 'EV-066', 'tp4_1m_concurrency_extension', '1m_c2', 'SINGLE_NODE_LOCAL'),
    ('tp4_1m_concurrency_extension 1m_c4', 'EV-067', 'tp4_1m_concurrency_extension', '1m_c4', 'SINGLE_NODE_LOCAL'),
    ('tp8_1m_concurrency_extension 1m_c1', 'EV-068', 'tp8_1m_concurrency_extension', '1m_c1', 'SINGLE_NODE_LOCAL'),
    ('tp8_1m_concurrency_extension 1m_c2', 'EV-069', 'tp8_1m_concurrency_extension', '1m_c2', 'SINGLE_NODE_LOCAL'),
    ('tp8_1m_concurrency_extension 1m_c4', 'EV-070', 'tp8_1m_concurrency_extension', '1m_c4', 'SINGLE_NODE_LOCAL'),
]

for html_file in ['v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html', 'v8_full_results/dashboards/v4_dashboard/index.html']:
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    match = re.search(r'const exactMap = \{([^}]+)\};', html)
    if not match:
        print(f'exactMap not found in {html_file}')
        continue
    
    exact_map_str = match.group(1)
    entries = re.findall(r'[\'"]([^\'"]+)[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]', exact_map_str)
    exact_map = dict(entries)
    print(f'Checking {html_file}: parsed {len(exact_map)} entries.')
    
    passed = 0
    for alias, exp_ev, exp_case, exp_bench, exp_net in appendix_a:
        actual_ev = exact_map.get(alias)
        if actual_ev != exp_ev:
            print(f'  [FAIL] {alias}: got {actual_ev}, expected {exp_ev}')
        else:
            rec = reg.get(actual_ev)
            if not rec or rec['case'] != exp_case or rec['bench'] != exp_bench:
                print(f'  [FAIL REGISTRY] {alias} -> {actual_ev}: {rec}')
            else:
                passed += 1
    print(f'  Appendix A score: {passed}/{len(appendix_a)} MATCHES.')
