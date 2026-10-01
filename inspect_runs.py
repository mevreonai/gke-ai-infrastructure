import json
from pathlib import Path

def main():
    p = Path("c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html")
    content = p.read_text(encoding="utf-8")
    idx = content.find("CANONICAL_DASHBOARD_DATA = ")
    # Find the end of this statement
    start_json = idx + len("CANONICAL_DASHBOARD_DATA = ")
    # Parse json object
    import json
    # Use raw decoder
    import re
    charts = re.findall(r'new\s+Chart\s*\(\s*([a-zA-Z0-9_]+)', content)
    print(f"Total new Chart() calls: {len(charts)}")
    
    canvases = ['chart_exec_ttft', 'chart_exec_tpot', 'chart_exec_capacity', 
                'chart_scaleup_ttft', 'chart_scaleup_tpot', 'chart_scaleup_tps',
                'chart_scaleout_comparison', 'chart_scaleout_context_scaling',
                'chart_long_concurrency', 'chart_long_scheduler', 'chart_long_chunk']
    dash_path = Path("c:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/DASHBOARD_CANONICAL_DATA.json")
    dash = json.loads(dash_path.read_text(encoding="utf-8"))
    ev = dash["evidence_registry"]
    print("Total evidence items:", len(ev))
    sample = ev["EV-001"]
    print("Sample EV-001:")
    for k, v in sample.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
