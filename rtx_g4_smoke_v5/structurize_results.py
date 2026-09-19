import os
import shutil
import zipfile

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v5"
print(f"Structuring {base_dir} ...")

# 1. Target Directory Paths
v5_baselines_dir = os.path.join(base_dir, "01_v5_baselines")
v6_prod_dir = os.path.join(base_dir, "02_v6_production_suite")
dashboards_dir = os.path.join(base_dir, "03_dashboards")

os.makedirs(os.path.join(v5_baselines_dir, "option_a_pytorch"), exist_ok=True)
os.makedirs(os.path.join(v5_baselines_dir, "option_b_deepspeed"), exist_ok=True)
os.makedirs(os.path.join(v5_baselines_dir, "option_c_nccl_hardware"), exist_ok=True)

single_node_dir = os.path.join(v6_prod_dir, "single_node_matrix")
multi_node_dir = os.path.join(v6_prod_dir, "multi_node_distributed")
scripts_dir = os.path.join(v6_prod_dir, "scripts")

os.makedirs(os.path.join(single_node_dir, "summary"), exist_ok=True)
os.makedirs(os.path.join(single_node_dir, "qualification_logs"), exist_ok=True)
os.makedirs(os.path.join(multi_node_dir, "summary"), exist_ok=True)
os.makedirs(os.path.join(multi_node_dir, "traces_and_logs"), exist_ok=True)
os.makedirs(os.path.join(multi_node_dir, "archive"), exist_ok=True)
os.makedirs(scripts_dir, exist_ok=True)
os.makedirs(dashboards_dir, exist_ok=True)

# 2. Populate 01_v5_baselines
for opt, folder_name in [("option_a", "option_a_pytorch"), ("option_b", "option_b_deepspeed"), ("option_c", "option_c_nccl_hardware")]:
    src = os.path.join(base_dir, opt)
    dst = os.path.join(v5_baselines_dir, folder_name)
    if os.path.exists(src):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if not os.path.exists(d):
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
print("Copied V5 Baselines.")

# 3. Populate 02_v6_production_suite / single_node_matrix
# Copy summary files
v6_results = os.path.join(base_dir, "v6_suite", "results")
for f in ["vllm_runs.csv", "VLLM_SUMMARY.md", "SERVING_ANALYSIS.md"]:
    src = os.path.join(v6_results, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(single_node_dir, "summary", f))

# Unpack qualification logs if zip exists
zip_path = r"c:\Users\ayu23\OneDrive\Desktop\tpu\v6_qualification_results_with_logs.zip"
if os.path.exists(zip_path):
    print(f"Extracting {zip_path} to {single_node_dir}/qualification_logs ...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(os.path.join(single_node_dir, "qualification_logs"))
    print("Extracted qualification logs.")

# Also check qualification_results folder
qual_src = os.path.join(base_dir, "v6_suite", "qualification_results")
if os.path.exists(qual_src):
    for item in os.listdir(qual_src):
        s = os.path.join(qual_src, item)
        d = os.path.join(single_node_dir, "qualification_logs", item)
        if not os.path.exists(d):
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

# 4. Populate 02_v6_production_suite / multi_node_distributed
# Summary
mn_summary_src = os.path.join(v6_results, "MULTI_NODE_SUMMARY.md")
if os.path.exists(mn_summary_src):
    shutil.copy2(mn_summary_src, os.path.join(multi_node_dir, "summary", "MULTI_NODE_SUMMARY.md"))

# Archive
mn_tar_src = os.path.join(v6_results, "vllm_multi_node.tar.gz")
if os.path.exists(mn_tar_src):
    shutil.copy2(mn_tar_src, os.path.join(multi_node_dir, "archive", "vllm_multi_node.tar.gz"))

# Traces and logs (all 4 topologies)
mn_traces_src = os.path.join(v6_results, "multi_node")
if os.path.exists(mn_traces_src):
    for topo in os.listdir(mn_traces_src):
        s = os.path.join(mn_traces_src, topo)
        d = os.path.join(multi_node_dir, "traces_and_logs", topo)
        if not os.path.exists(d):
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
print("Copied Multi-Node Distributed Suite.")

# 5. Populate scripts
v6_scripts_src = os.path.join(base_dir, "v6_suite")
for item in os.listdir(v6_scripts_src):
    s = os.path.join(v6_scripts_src, item)
    if os.path.isfile(s):
        shutil.copy2(s, os.path.join(scripts_dir, item))
print("Copied V6 runner scripts.")

# 6. Populate 03_dashboards
dash_src = os.path.join(base_dir, "v6_suite", "results", "v6_characterization_dashboard.html")
if os.path.exists(dash_src):
    shutil.copy2(dash_src, os.path.join(dashboards_dir, "v6_characterization_dashboard.html"))
master_dash = r"c:\Users\ayu23\OneDrive\Desktop\tpu\MASTER_CHARACTERIZATION_DASHBOARD.html"
if os.path.exists(master_dash):
    shutil.copy2(master_dash, os.path.join(dashboards_dir, "MASTER_CHARACTERIZATION_DASHBOARD.html"))

# 7. Write Directory Map
dir_map = f"""# RTX PRO 6000 Benchmark & Characterization Directory Structure

This directory organizes all empirical benchmarks, hardware characterization runs, distributed profiles, logs, and interactive dashboards.

```
rtx_g4_smoke_v5/
├── MASTER_BENCHMARK_SUMMARY.md                  <- Cross-suite executive summary
├── MASTER_CHARACTERIZATION_DASHBOARD.html      <- 1-to-1 Interactive characterization dashboard
│
├── 01_v5_baselines/                            <- Previous V5 Baselines
│   ├── option_a_pytorch/                       <- PyTorch / HuggingFace baseline runs
│   │   ├── results/                            <- VLLM_SUMMARY.md, vllm_runs.csv
│   │   └── scripts/                            <- Execution scripts
│   ├── option_b_deepspeed/                     <- DeepSpeed ZeRO-3 baselines
│   │   ├── results/                            <- OPTION_B_SUMMARY.md, traces
│   │   └── scripts/                            <- Execution scripts
│   └── option_c_nccl_hardware/                 <- NCCL interconnect & hardware network sweep
│       ├── results/                            <- AllReduce, AllGather, ReduceScatter across sockets
│       └── scripts/                            <- Runner scripts
│
├── 02_v6_production_suite/                     <- Complete V6 Benchmark Suite
│   ├── single_node_matrix/                     <- 22 Cases / 59 Empirical Benchmarks
│   │   ├── summary/
│   │   │   ├── vllm_runs.csv                   <- Full metrics across all 59 benchmark runs
│   │   │   ├── VLLM_SUMMARY.md                 <- Single-node analytical report
│   │   │   └── SERVING_ANALYSIS.md             <- Capacity, gating, and prefill/decode findings
│   │   └── qualification_logs/                 <- Detailed server.log, bench_stdout.log, metrics_gpu.jsonl
│   ├── multi_node_distributed/                 <- 16x GPU Multi-Node Cluster Runs
│   │   ├── summary/
│   │   │   └── MULTI_NODE_SUMMARY.md           <- Topology comparison (TP4_PP4 vs TP16)
│   │   ├── traces_and_logs/                    <- Per-topology raw server & client logs
│   │   │   ├── tp4_pp4_dist/                   <- Optimal multi-node topology logs & metrics
│   │   │   ├── tp4_pp2_dist/                   <- Remote-PP validation case
│   │   │   ├── tp8_pp2_dist/                   <- Intra-node TP8, cross-node PP2
│   │   │   └── tp16_pp1_dist/                  <- Cross-node TP16 AllReduce bound
│   │   └── archive/
│   │       └── vllm_multi_node.tar.gz          <- Compressed archive of all multi-node traces (3.8MB)
│   └── scripts/                                <- Autonomous harness & test manifests
│       ├── 07_preflight_v5.py
│       ├── 10_vllm_surrogate_cases.json
│       ├── 10b_vllm_multi_node_cases.json
│       ├── 11_run_vllm_surrogate.py
│       └── 12_run_vllm_multi_node.sh
│
└── 03_dashboards/                              <- Production Dashboards
    ├── MASTER_CHARACTERIZATION_DASHBOARD.html  <- Standalone 1-to-1 replica dashboard
    ├── v6_characterization_dashboard.html      <- Result dashboard
    └── build_characterization_dashboard.py     <- Dashboard generator script
```
"""

with open(os.path.join(base_dir, "DIRECTORY_STRUCTURE.md"), "w", encoding="utf-8") as f:
    f.write(dir_map)

print("Directory structure successfully created and mapped in DIRECTORY_STRUCTURE.md!")
