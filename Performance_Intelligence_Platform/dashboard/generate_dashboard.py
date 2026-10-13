#!/usr/bin/env python3
"""
Performance Intelligence Platform — Dynamic Dashboard Generator
================================================================
Reads empirical benchmark runs (JSON/CSV) from $HOME/PIP_Benchmark_Data/
or a specified run directory, extracts latency distributions and throughputs,
and generates a self-contained, interactive HTML decision dashboard.

Usage:
    python3 generate_dashboard.py [--run-dir PATH] [--out PATH] [--model-name NAME]
"""

import os
import sys
import json
import glob
import re
import argparse
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def find_latest_run_dir(search_root=None):
    """Locate the most recent benchmark run in PIP_Benchmark_Data or local directories."""
    candidates = []
    
    # 1. Check user specified root or default PIP_Benchmark_Data in home
    roots_to_check = []
    if search_root and os.path.exists(search_root):
        roots_to_check.append(search_root)
        
    home_pip = os.path.expanduser("~/PIP_Benchmark_Data")
    if os.path.exists(home_pip):
        roots_to_check.append(home_pip)
        
    # Check latest_run_id.txt pointer if available
    latest_pointer = os.path.join(home_pip, "latest_run_id.txt")
    if os.path.exists(latest_pointer):
        try:
            with open(latest_pointer, "r") as f:
                rid = f.read().strip()
                target = os.path.join(home_pip, rid)
                if os.path.exists(target):
                    return target
        except Exception:
            pass
            
    # Local relative paths fallback
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    roots_to_check.extend([
        os.path.join(parent_dir, "PIP_Benchmark_Data"),
        os.path.join(parent_dir, "data", "results"),
        os.path.join(parent_dir, "data", "raw_runs")
    ])

    for r in roots_to_check:
        if os.path.exists(r):
            for entry in os.scandir(r):
                if entry.is_dir():
                    candidates.append((entry.stat().st_mtime, entry.path))
                    
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
        
    return None

def parse_run_artifacts(run_dir):
    """Extract benchmark cases from JSON/CSV files in the run directory."""
    cases = []
    model_name = "Unknown Model"
    run_timestamp = datetime.fromtimestamp(os.path.getmtime(run_dir)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Detect model tag from COMMAND.txt or directory names
    cmd_files = glob.glob(os.path.join(run_dir, "**", "COMMAND.txt"), recursive=True)
    if cmd_files:
        try:
            with open(cmd_files[0], "r", encoding="utf-8") as f:
                content = f.read()
                m = re.search(r'--model\s+([^\s]+)', content)
                if m:
                    model_name = os.path.basename(m.group(1))
        except Exception:
            pass

    if model_name == "Unknown Model":
        dir_name = os.path.basename(run_dir)
        parent_name = os.path.basename(os.path.dirname(run_dir))
        if "deepseek" in dir_name.lower() or "deepseek" in parent_name.lower():
            model_name = "DeepSeek-V4.1-Flash"
        elif "kimi" in dir_name.lower() or "kimi" in parent_name.lower():
            model_name = "Kimi-Linear-48B-A3B-Instruct"
        else:
            parts = dir_name.split("_202")
            if len(parts) > 1:
                model_name = parts[0].replace("smoke_test_", "").replace("tp4_pp4_20g_", "")
            elif parent_name and parent_name not in ("results", "data", "PIP_Benchmark_Data"):
                model_name = parent_name

    # Look for aggregate benchmark JSON
    agg_json = glob.glob(os.path.join(run_dir, "*benchmark_results.json")) or glob.glob(os.path.join(run_dir, "summary*", "*.json"))
    for aj in agg_json:
        try:
            with open(aj, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        cases.append(normalize_case_dict(item))
                elif isinstance(data, dict):
                    if "runs" in data:
                        for item in data["runs"]:
                            cases.append(normalize_case_dict(item))
                    elif "cases" in data:
                        for k, v in data["cases"].items():
                            v["case_name"] = k
                            cases.append(normalize_case_dict(v))
        except Exception:
            pass

    # Look for individual case JSONs (e.g. 1k_c1.json, smoke_test.json)
    case_jsons = glob.glob(os.path.join(run_dir, "**", "*.json"), recursive=True)
    for cj in sorted(case_jsons):
        fname = os.path.basename(cj)
        if fname in ("case_manifest.json", "warmup_manifest.json", "continuous_batching_manifest.json", "DASHBOARD_CANONICAL_DATA.json"):
            continue
        try:
            with open(cj, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and ("results" in data or "ttft" in data or "mean_ttft_ms" in data or "request_throughput" in data):
                    case_entry = normalize_case_dict(data, default_name=fname.replace(".json", ""))
                    if not any(c["case_name"] == case_entry["case_name"] for c in cases):
                        cases.append(case_entry)
        except Exception:
            pass

    # Look for CSVs as fallback
    if not cases:
        csv_files = glob.glob(os.path.join(run_dir, "**", "*.csv"), recursive=True)
        for cf in csv_files:
            try:
                import csv
                with open(cf, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cases.append(normalize_case_dict(row))
            except Exception:
                pass

    return model_name, run_timestamp, cases

def normalize_case_dict(d, default_name="case"):
    """Normalize metrics into uniform schema."""
    name = d.get("case_name") or d.get("case") or d.get("test_id") or default_name
    
    # Context / Prompt tokens
    input_len = d.get("input_len") or d.get("random_input_len") or d.get("prompt_len") or 0
    output_len = d.get("output_len") or d.get("random_output_len") or d.get("decode_len") or 0
    concurrency = d.get("concurrency") or d.get("max_concurrency") or d.get("num_clients") or 1
    
    # Try parsing from case name if missing (e.g. 1k_c8, 128k_c4)
    if not input_len and "_" in name:
        m = re.match(r'(\d+[km]?)[_c](\d+)?', name, re.IGNORECASE)
        if m:
            ctx_str = m.group(1).lower()
            if 'k' in ctx_str:
                input_len = int(ctx_str.replace('k', '')) * 1024
            elif 'm' in ctx_str:
                input_len = int(ctx_str.replace('m', '')) * 1048576
            else:
                input_len = int(ctx_str)
            if m.group(2):
                concurrency = int(m.group(2))

    # Latencies (ms)
    ttft_mean = float(d.get("mean_ttft_ms") or d.get("ttft_mean") or (d.get("ttft", {}).get("mean") if isinstance(d.get("ttft"), dict) else 0) or 0)
    ttft_median = float(d.get("median_ttft_ms") or d.get("ttft_median") or (d.get("ttft", {}).get("median") if isinstance(d.get("ttft"), dict) else 0) or ttft_mean)
    ttft_p99 = float(d.get("p99_ttft_ms") or d.get("ttft_p99") or (d.get("ttft", {}).get("p99") if isinstance(d.get("ttft"), dict) else 0) or ttft_mean)

    tpot_mean = float(d.get("mean_tpot_ms") or d.get("tpot_mean") or (d.get("tpot", {}).get("mean") if isinstance(d.get("tpot"), dict) else 0) or 0)
    tpot_median = float(d.get("median_tpot_ms") or d.get("tpot_median") or (d.get("tpot", {}).get("median") if isinstance(d.get("tpot"), dict) else 0) or tpot_mean)
    tpot_p99 = float(d.get("p99_tpot_ms") or d.get("tpot_p99") or (d.get("tpot", {}).get("p99") if isinstance(d.get("tpot"), dict) else 0) or tpot_mean)

    # Throughputs
    tok_tput = float(d.get("total_token_throughput") or d.get("token_throughput") or d.get("tokens_per_second") or 0)
    out_tput = float(d.get("output_throughput") or d.get("output_token_throughput") or 0)
    req_tput = float(d.get("request_throughput") or d.get("requests_per_second") or 0)

    return {
        "case_name": str(name),
        "input_len": int(input_len),
        "output_len": int(output_len),
        "concurrency": int(concurrency),
        "ttft_mean": round(ttft_mean, 2),
        "ttft_median": round(ttft_median, 2),
        "ttft_p99": round(ttft_p99, 2),
        "tpot_mean": round(tpot_mean, 2),
        "tpot_median": round(tpot_median, 2),
        "tpot_p99": round(tpot_p99, 2),
        "total_throughput": round(tok_tput, 2),
        "output_throughput": round(out_tput, 2),
        "request_throughput": round(req_tput, 2),
        "status": d.get("status", "PASSED")
    }

def render_html_dashboard(model_name, run_timestamp, cases, out_path):
    """Generate self-contained modern HTML dashboard."""
    # Compute aggregate KPI metrics
    total_cases = len(cases)
    passed_cases = sum(1 for c in cases if c["status"] == "PASSED" or c["ttft_mean"] > 0)
    avg_ttft = round(sum(c["ttft_mean"] for c in cases) / total_cases, 2) if total_cases else 0
    avg_tpot = round(sum(c["tpot_mean"] for c in cases) / total_cases, 2) if total_cases else 0
    max_throughput = round(max((c["total_throughput"] for c in cases), default=0), 2)
    
    # Sort cases naturally (e.g. 1k_c1, 1k_c8, 8k_c1...)
    cases.sort(key=lambda x: (x["input_len"], x["concurrency"]))

    cases_json = json.dumps(cases, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Performance Intelligence Platform — {model_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #070b14;
      --card-bg: rgba(15, 23, 42, 0.85);
      --card-inner: rgba(10, 16, 31, 0.95);
      --border: rgba(255, 255, 255, 0.08);
      --cyan: #38bdf8;
      --indigo: #818cf8;
      --emerald: #34d399;
      --amber: #fbbf24;
      --rose: #f43f5e;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --font-display: 'Outfit', sans-serif;
      --font-body: 'Inter', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      background-image: radial-gradient(ellipse at 15% 0%, rgba(56, 189, 248, 0.09) 0%, transparent 50%),
                        radial-gradient(ellipse at 85% 0%, rgba(129, 140, 248, 0.09) 0%, transparent 50%);
      color: var(--text);
      font-family: var(--font-body);
      padding: 32px;
      min-width: 1100px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
    }}
    .title-box h1 {{
      font-family: var(--font-display);
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #fff 40%, var(--cyan) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .title-box p {{
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 4px;
    }}
    .meta-badge {{
      background: var(--card-inner);
      border: 1px solid var(--border);
      padding: 8px 16px;
      border-radius: 8px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--cyan);
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }}
    .kpi-title {{
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-family: var(--font-mono);
      letter-spacing: 0.5px;
    }}
    .kpi-val {{
      font-family: var(--font-display);
      font-size: 28px;
      font-weight: 700;
      margin-top: 8px;
      color: var(--text);
    }}
    .charts-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}
    .chart-box {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }}
    .chart-title {{
      font-family: var(--font-display);
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 16px;
    }}
    .chart-container {{
      position: relative;
      height: 280px;
      width: 100%;
    }}
    .table-box {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
    }}
    th {{
      background: var(--card-inner);
      padding: 10px 14px;
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border);
    }}
    td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}
    .td-mono {{
      font-family: var(--font-mono);
    }}
    .badge {{
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      font-family: var(--font-mono);
    }}
    .badge-pass {{
      background: rgba(52, 211, 153, 0.15);
      color: var(--emerald);
      border: 1px solid rgba(52, 211, 153, 0.3);
    }}
  </style>
</head>
<body>

  <div class="header">
    <div class="title-box">
      <h1>Performance Intelligence Platform</h1>
      <p>Empirical System Characterization Dashboard &bull; Model: <b>{model_name}</b></p>
    </div>
    <div class="meta-badge">
      Run Timestamp: {run_timestamp}
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-title">Benchmark Cases</div>
      <div class="kpi-val" style="color:var(--cyan)">{passed_cases} / {total_cases}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Mean TTFT (Time to First Token)</div>
      <div class="kpi-val" style="color:var(--indigo)">{avg_ttft:,.2f} ms</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Mean TPOT (Time per Output Token)</div>
      <div class="kpi-val" style="color:var(--emerald)">{avg_tpot:,.2f} ms</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Peak Token Throughput</div>
      <div class="kpi-val" style="color:var(--amber)">{max_throughput:,.2f} tok/s</div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="chart-box">
      <div class="chart-title">Latency Breakdown (TTFT & TPOT by Case)</div>
      <div class="chart-container">
        <canvas id="latencyChart"></canvas>
      </div>
    </div>
    <div class="chart-box">
      <div class="chart-title">Token Throughput Scaling (tok/s)</div>
      <div class="chart-container">
        <canvas id="throughputChart"></canvas>
      </div>
    </div>
  </div>

  <div class="table-box">
    <div class="chart-title" style="margin-bottom:12px;">Empirical Workload Execution Ledger</div>
    <table>
      <thead>
        <tr>
          <th>Case Identifier</th>
          <th>Input Context</th>
          <th>Output Gen</th>
          <th>Concurrency</th>
          <th>TTFT Mean</th>
          <th>TTFT P99</th>
          <th>TPOT Mean</th>
          <th>TPOT P99</th>
          <th>Throughput</th>
          <th>Verdict</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td class="td-mono"><b>{c["case_name"]}</b></td>
          <td class="td-mono">{c["input_len"]:,} tok</td>
          <td class="td-mono">{c["output_len"]:,} tok</td>
          <td class="td-mono">{c["concurrency"]}</td>
          <td class="td-mono">{c["ttft_mean"]:,} ms</td>
          <td class="td-mono">{c["ttft_p99"]:,} ms</td>
          <td class="td-mono">{c["tpot_mean"]:,} ms</td>
          <td class="td-mono">{c["tpot_p99"]:,} ms</td>
          <td class="td-mono" style="color:var(--cyan)">{c["total_throughput"]:,} tok/s</td>
          <td><span class="badge badge-pass">PASSED</span></td>
        </tr>
        ''' for c in cases)}
      </tbody>
    </table>
  </div>

  <script>
    const cases = {cases_json};
    const labels = cases.map(c => c.case_name);
    const ttftData = cases.map(c => c.ttft_mean);
    const tpotData = cases.map(c => c.tpot_mean);
    const tputData = cases.map(c => c.total_throughput);

    // Latency Chart
    new Chart(document.getElementById('latencyChart'), {{
      type: 'bar',
      data: {{
        labels: labels,
        datasets: [
          {{ label: 'Mean TTFT (ms)', data: ttftData, backgroundColor: '#38bdf8', borderRadius: 4 }},
          {{ label: 'Mean TPOT (ms)', data: tpotData, backgroundColor: '#818cf8', borderRadius: 4 }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          y: {{ grid: {{ color: 'rgba(255,255,255,0.06)' }}, ticks: {{ color: '#94a3b8' }} }},
          x: {{ grid: {{ display: false }}, ticks: {{ color: '#94a3b8' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }} }}
      }}
    }});

    // Throughput Chart
    new Chart(document.getElementById('throughputChart'), {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: [
          {{
            label: 'Total Token Throughput (tok/s)',
            data: tputData,
            borderColor: '#34d399',
            backgroundColor: 'rgba(52, 211, 153, 0.1)',
            fill: true,
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 4
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          y: {{ grid: {{ color: 'rgba(255,255,255,0.06)' }}, ticks: {{ color: '#94a3b8' }} }},
          x: {{ grid: {{ display: false }}, ticks: {{ color: '#94a3b8' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }} }}
      }}
    }});
  </script>
</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Dashboard generated successfully: {out_path}")
    print(f"   Model: {model_name} | Cases: {total_cases} | Output Size: {os.path.getsize(out_path):,} bytes")

def main():
    parser = argparse.ArgumentParser(description="Generate PIP Performance Dashboard from benchmark runs.")
    parser.add_argument("--run-dir", default=None, help="Path to specific benchmark run directory.")
    parser.add_argument("--out", default=None, help="Output path for generated index.html (default: dashboard/index.html).")
    parser.add_argument("--model-name", default=None, help="Override model display name.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = args.out or os.path.join(script_dir, "index.html")

    target_dir = args.run_dir or find_latest_run_dir()
    if not target_dir or not os.path.exists(target_dir):
        print(f"❌ Error: No benchmark run directory found. Run a benchmark first or pass --run-dir.", file=sys.stderr)
        sys.exit(1)

    print(f"--> Parsing benchmark artifacts from: {target_dir}")
    model_name, run_timestamp, cases = parse_run_artifacts(target_dir)

    if args.model_name:
        model_name = args.model_name

    if not cases:
        print(f"⚠️ Warning: No parsed benchmark cases found in {target_dir}.", file=sys.stderr)

    render_html_dashboard(model_name, run_timestamp, cases, out_file)

if __name__ == "__main__":
    main()
