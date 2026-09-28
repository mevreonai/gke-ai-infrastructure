files = [
    'v8_full_results/dashboards/v4_dashboard/index.html',
    'v8_full_results/release_specs/MASTER_CHARACTERIZATION_DASHBOARD.html',
    'v8_full_results/release_specs/index.html'
]

wrong_str = """        "evidence_class": datum.evidence_class,
        "artifact_path": datum.artifact_path
    } : {
        "discovery_id": discovery.id,
        "top_id": discovery.top_id,
        "title": discovery.title,
        "primary_evidence": discovery.drilldown
    };"""

correct_str = """        "evidence_class": datum.evidence_class,
        "artifact_path": datum.artifact_path
    }) : (discovery ? {
        "discovery_id": discovery.id,
        "top_id": discovery.top_id,
        "title": discovery.title,
        "primary_evidence": discovery.drilldown
    } : null);"""

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    if wrong_str in content:
        content = content.replace(wrong_str, correct_str)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed datumObj syntax in {fpath}")
    else:
        print(f"wrong_str not found in {fpath}")
