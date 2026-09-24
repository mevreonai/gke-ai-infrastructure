import os
import zipfile
import shutil

def create_v6_package():
    output_zip = 'V6_BENCHMARK_RESULTS_AND_LOGS.zip'
    print(f"Creating {output_zip}...")

    # Define the README text for the zip
    readme_content = """# V6 vLLM Benchmark Results & Logs — Canonical Guide

## Executive Summary
This package contains the complete, authoritative collection of benchmark results, telemetry, raw logs, and characterization dashboards for the **V6 vLLM Inference Characterization Suite** conducted on **NVIDIA RTX PRO 6000 Blackwell Server Edition (96GB GDDR7, PCIe Gen5)** nodes.

### Clarification on Repository Structure (Why Two Folders Existed)
- **`rtx_g4_smoke_v5/v6_suite/`**: The original **execution & development workspace** where test scripts were staged and execution output files were initially dumped.
- **`rtx_g4_smoke_v5/02_v6_production_suite/`**: The **curated, canonical production repository** organized into structured subdirectories alongside `01_v5_baselines` and `03_dashboards`.
- This package unifies both into a single, clean, unambiguous hierarchy.

---

## Directory Structure

```
V6_BENCHMARK_RESULTS/
├── README_V6_RESULTS_GUIDE.md              <-- This guide
├── 01_SUMMARY_REPORTS/                     <-- Core CSV and Markdown reports
│   ├── vllm_runs.csv                       <-- 59-row master single-node test matrix
│   ├── VLLM_SUMMARY.md                     <-- Single-node qualification & sweeps summary
│   ├── MULTI_NODE_SUMMARY.md               <-- Multi-node distributed scaling summary
│   └── SERVING_ANALYSIS.md                 <-- Serving capacity & latency envelope analysis
├── 02_INTERACTIVE_DASHBOARD/               <-- Master interactive audit dashboard
│   ├── MASTER_CHARACTERIZATION_DASHBOARD.html
│   ├── data/
│   │   ├── evidence.json                   <-- 59 verified typed rows with full provenance
│   │   └── scaleout.json                   <-- Multi-node distributed benchmark data
├── 03_SINGLE_NODE_RAW_LOGS/                <-- Unprocessed single-node runtime logs & telemetry
│   ├── tp4_qualification/                  <-- TP4 8K baseline, GPU telemetry, Prometheus logs
│   ├── tp8_qualification/                  <-- TP8 8K baseline, GPU telemetry, Prometheus logs
│   ├── analysis/                           <-- Automated per-run metric extraction
│   ├── summary_v6/                         <-- Qualification run logs & summaries
│   └── vllm_surrogate_manifest.json        <-- Environment & engine configuration manifest
├── 04_MULTI_NODE_DISTRIBUTED_RAW_LOGS/     <-- Multi-node distributed traces and Ray server logs
│   ├── tp4_pp4_dist/                       <-- 4 stages of TP4 within NUMA
│   ├── tp4_pp2_dist/                       <-- Forced TP4/PP2 (cross-node remote PP boundary)
│   ├── tp8_pp2_dist/                       <-- TP8 per node with remote PP boundary
│   ├── tp16_pp1_dist/                      <-- TP16 spanning Node 0 and Node 1
│   └── archive/vllm_multi_node.tar.gz      <-- Compressed multi-node raw logs archive
└── 05_BENCHMARK_SCRIPTS_AND_CONFIGS/       <-- Executable benchmark harness & test configurations
    ├── 10_vllm_surrogate_cases.json        <-- Single-node test case matrix definition
    ├── 10b_vllm_multi_node_cases.json      <-- Multi-node test case matrix definition
    ├── run_v6_e2e.sh                       <-- End-to-end suite runner script
    ├── 11_run_vllm_surrogate.py            <-- Single-node test executor
    ├── 12_run_vllm_multi_node.py           <-- Multi-node test executor
    └── 15_summarize_vllm.py                <-- Metric extraction & aggregation script
```

---

## Benchmark Highlights & Key Numbers

### 1. Single-Node Performance Matrix (`vllm_runs.csv`)
- **Total Measured Runs**: 59 test configurations.
- **Context Lengths Evaluated**: 8K, 128K, 512K, 1,000,000 (1M) tokens.
- **Concurrency Range**: c = 1 to c = 32 requests.
- **Preemptions**: `preemptions_delta = 0` in all 59 measured runs.
- **Key Findings**:
  - **8K Baseline**: TP4 achieves lower TPOT (5.09 ms vs 7.03 ms) while TP8 delivers lower TTFT (135.7 ms vs 188.4 ms).
  - **128K Closed-Loop**: Throughput scales from 13.7 tok/s (c1) to 58.7 tok/s (c16).
  - **1M Feasibility**: Measured at 93.4s TTFT at c1; TPOT scales from 10.2 ms (c1) to 267.7 ms (c4) while throughput remains flat at ~0.3 tok/s.

### 2. Multi-Node Distributed Matrix (`MULTI_NODE_SUMMARY.md`)
Evaluated across 2 nodes (16 GPUs total):
- **Forced TP4 / PP2**: **1,723.7 ms TTFT**, 30.9 tok/s (Fastest distributed TTFT).
- **TP8 / PP2**: **2,646.6 ms TTFT**, 21.4 tok/s.
- **TP4 / PP4**: **2,817.6 ms TTFT**, 19.5 tok/s.
- **TP16 / PP1**: **6,024.9 ms TTFT**, 9.5 tok/s (Inter-node TP communication latency overhead).

---

## How to View the Interactive Dashboard
Open `02_INTERACTIVE_DASHBOARD/MASTER_CHARACTERIZATION_DASHBOARD.html` directly in any standard browser (Chrome, Edge, Firefox, Safari). No web server or Python daemon is required; all 59 evidence rows and scale-out datasets are embedded and registered with strict provenance verification.
"""

    # Create temporary zip archive
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Write README
        zipf.writestr('V6_BENCHMARK_RESULTS/README_V6_RESULTS_GUIDE.md', readme_content)

        # 1. Summary Reports
        summary_files = [
            ('rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/vllm_runs.csv', 'V6_BENCHMARK_RESULTS/01_SUMMARY_REPORTS/vllm_runs.csv'),
            ('rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/VLLM_SUMMARY.md', 'V6_BENCHMARK_RESULTS/01_SUMMARY_REPORTS/VLLM_SUMMARY.md'),
            ('rtx_g4_smoke_v5/02_v6_production_suite/single_node_matrix/summary/SERVING_ANALYSIS.md', 'V6_BENCHMARK_RESULTS/01_SUMMARY_REPORTS/SERVING_ANALYSIS.md'),
            ('rtx_g4_smoke_v5/02_v6_production_suite/multi_node_distributed/summary/MULTI_NODE_SUMMARY.md', 'V6_BENCHMARK_RESULTS/01_SUMMARY_REPORTS/MULTI_NODE_SUMMARY.md'),
        ]
        for src, dest in summary_files:
            if os.path.exists(src):
                zipf.write(src, dest)
                print(f"Added summary: {dest}")

        # 2. Interactive Dashboard
        dashboard_files = [
            ('MASTER_CHARACTERIZATION_DASHBOARD.html', 'V6_BENCHMARK_RESULTS/02_INTERACTIVE_DASHBOARD/MASTER_CHARACTERIZATION_DASHBOARD.html'),
            ('data/evidence.json', 'V6_BENCHMARK_RESULTS/02_INTERACTIVE_DASHBOARD/data/evidence.json'),
            ('data/scaleout.json', 'V6_BENCHMARK_RESULTS/02_INTERACTIVE_DASHBOARD/data/scaleout.json'),
        ]
        for src, dest in dashboard_files:
            if os.path.exists(src):
                zipf.write(src, dest)
                print(f"Added dashboard file: {dest}")

        # 3. Single-Node Raw Logs
        single_node_base = 'rtx_g4_smoke_v5/v6_suite/qualification_results/v5_single_node_results'
        if os.path.exists(single_node_base):
            for root, _, files in os.walk(single_node_base):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, single_node_base)
                    dest = f"V6_BENCHMARK_RESULTS/03_SINGLE_NODE_RAW_LOGS/{rel_path}".replace('\\', '/')
                    zipf.write(full_path, dest)
            print(f"Added single-node raw logs from {single_node_base}")

        # 4. Multi-Node Distributed Raw Logs
        multi_node_base = 'rtx_g4_smoke_v5/02_v6_production_suite/multi_node_distributed'
        if os.path.exists(multi_node_base):
            for root, _, files in os.walk(multi_node_base):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, multi_node_base)
                    # skip duplicate summary if already added
                    if 'summary' in rel_path:
                        continue
                    dest = f"V6_BENCHMARK_RESULTS/04_MULTI_NODE_DISTRIBUTED_RAW_LOGS/{rel_path}".replace('\\', '/')
                    zipf.write(full_path, dest)
            print(f"Added multi-node distributed raw logs from {multi_node_base}")

        # 5. Benchmark Scripts and Configs
        scripts_base = 'rtx_g4_smoke_v5/02_v6_production_suite/scripts'
        if os.path.exists(scripts_base):
            for root, _, files in os.walk(scripts_base):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, scripts_base)
                    dest = f"V6_BENCHMARK_RESULTS/05_BENCHMARK_SCRIPTS_AND_CONFIGS/{rel_path}".replace('\\', '/')
                    zipf.write(full_path, dest)
            print(f"Added benchmark scripts from {scripts_base}")

    zip_size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"\nSUCCESS: Created {output_zip} ({zip_size_mb:.2f} MB)")

if __name__ == '__main__':
    create_v6_package()
