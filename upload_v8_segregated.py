#!/usr/bin/env python3
"""
V8 Characterization Data Vault — Segregated GCS Upload Pipeline (High-Performance Engine)
Uploads and segregates all V8 benchmarking assets to:
  gs://mevreon-v8-benchmarks-segregated/

Structure in GCS:
  ├── archives/                     Master compressed bundles & evidence packages
  ├── execution_logs/               Campaign orchestration & execution logs
  ├── nsys_profiles/                All .nsys-rep files (Nsight Systems profile captures)
  ├── sqlite_traces/                All .sqlite trace databases
  ├── pytorch_traces/               All .pt.trace.json.gz (PyTorch Timeline traces)
  ├── additional_runs/              Unpacked structured V8 additional runs (20261005, 20261009)
  ├── master_results_matrix/        Unpacked V8 characterization results (20260921_195656)
  ├── suites_and_scripts/           V8 suite runner scripts & campaign configs
  ├── V8_DATA_VAULT_INDEX.md        Human-readable comprehensive vault directory index
  └── V8_DATA_MANIFEST.json        Machine-readable catalog with file metadata & sizes
"""

import os
import sys
import glob
import json
import time
import shutil
import subprocess
from pathlib import Path

BUCKET = "gs://mevreon-v8-benchmarks-segregated"
HOME = os.path.expanduser("~")
STAGING_DIR = os.path.join(HOME, "v8_vault_staging")

def run_cmd(cmd, check=True):
    print(f"\n[EXEC] {cmd}", flush=True)
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.stdout:
        print(res.stdout.strip(), flush=True)
    if res.stderr and res.returncode != 0:
        print(f"[STDERR] {res.stderr.strip()}", file=sys.stderr, flush=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed (code {res.returncode}): {cmd}\n{res.stderr}")
    return res

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def stage_files(files, target_category_dir, base_dir=None):
    """Stages files into target_category_dir via hardlinks (instantaneous, 0 disk cost)."""
    os.makedirs(target_category_dir, exist_ok=True)
    total_bytes = 0
    staged_count = 0

    for f in files:
        if not os.path.exists(f):
            continue
        try:
            sz = os.path.getsize(f)
            total_bytes += sz
        except OSError:
            pass

        if base_dir:
            rel = os.path.relpath(f, base_dir)
            dest = os.path.join(target_category_dir, rel)
        else:
            dest = os.path.join(target_category_dir, os.path.basename(f))

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest):
            os.remove(dest)
        try:
            os.link(f, dest)
            staged_count += 1
        except Exception:
            # Fallback to copy if cross-filesystem or link failed
            shutil.copy2(f, dest)
            staged_count += 1

    return staged_count, total_bytes

def main():
    start_time = time.time()
    print("================================================================================")
    print("  PERFORMANCE INTELLIGENCE PLATFORM — V8 DATA VAULT GCS SEGREGATION")
    print(f"  Target Bucket : {BUCKET}")
    print(f"  Source Root   : {HOME}")
    print(f"  Staging Dir   : {STAGING_DIR}")
    print("================================================================================", flush=True)

    if os.path.exists(STAGING_DIR):
        print(f"Cleaning previous staging directory {STAGING_DIR}...")
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
    os.makedirs(STAGING_DIR, exist_ok=True)

    catalog = {
        "bucket": BUCKET,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "categories": {}
    }

    # 1. Archives & Master Evidence Tarballs
    print("\n[PHASE 1/8] Staging V8 Archives & Master Tarballs...", flush=True)
    archive_patterns = [
        f"{HOME}/v8_full_results/*.tar.gz*",
        f"{HOME}/v8_additional_runs_*.tar.gz*",
        f"{HOME}/v8_additional_runs_*.zip",
        f"{HOME}/V8_FULL_*.zip",
    ]
    archive_files = []
    for pat in archive_patterns:
        archive_files.extend(glob.glob(pat))
    archive_files = sorted(list(set(archive_files)))
    
    cnt, sz = stage_files(archive_files, os.path.join(STAGING_DIR, "archives"))
    catalog["categories"]["archives"] = {"count": cnt, "total_bytes": sz, "size_formatted": format_size(sz)}
    print(f"  -> Staged {cnt} archive bundles ({format_size(sz)}).", flush=True)

    # 2. Execution & Campaign Logs
    print("\n[PHASE 2/8] Staging V8 Execution & Campaign Logs...", flush=True)
    log_patterns = [
        f"{HOME}/v8_*.log",
        f"{HOME}/v8_*.out",
        f"{HOME}/V8_*.log",
        f"{HOME}/launch_v8.sh",
        f"{HOME}/v8_nohup.log"
    ]
    log_files = []
    for pat in log_patterns:
        log_files.extend(glob.glob(pat))
    log_files = sorted(list(set(log_files)))

    cnt, sz = stage_files(log_files, os.path.join(STAGING_DIR, "execution_logs"))
    catalog["categories"]["execution_logs"] = {"count": cnt, "total_bytes": sz, "size_formatted": format_size(sz)}
    print(f"  -> Staged {cnt} log files ({format_size(sz)}).", flush=True)

    # 3. Nsight Systems Profiles (*.nsys-rep)
    print("\n[PHASE 3/8] Scanning & Staging Nsight Systems Profiles (*.nsys-rep)...", flush=True)
    nsys_files = []
    for root, _, files in os.walk(f"{HOME}/v8_full_results"):
        for f in files:
            if f.endswith(".nsys-rep"):
                nsys_files.append(os.path.join(root, f))
    for root, _, files in os.walk(f"{HOME}/v8_additional_runs"):
        for f in files:
            if f.endswith(".nsys-rep"):
                nsys_files.append(os.path.join(root, f))
    if os.path.exists(f"{HOME}/v5_profiling"):
        for root, _, files in os.walk(f"{HOME}/v5_profiling"):
            for f in files:
                if f.endswith(".nsys-rep"):
                    nsys_files.append(os.path.join(root, f))

    nsys_files = sorted(list(set(nsys_files)))
    cnt, sz = stage_files(nsys_files, os.path.join(STAGING_DIR, "nsys_profiles"), base_dir=HOME)
    catalog["categories"]["nsys_profiles"] = {"count": cnt, "total_bytes": sz, "size_formatted": format_size(sz)}
    print(f"  -> Staged {cnt} Nsight Systems profile captures ({format_size(sz)}).", flush=True)

    # 4. SQLite Trace Databases (*.sqlite)
    print("\n[PHASE 4/8] Scanning & Staging SQLite Trace Databases (*.sqlite)...", flush=True)
    sqlite_files = []
    for root, _, files in os.walk(f"{HOME}/v8_full_results"):
        for f in files:
            if f.endswith(".sqlite"):
                sqlite_files.append(os.path.join(root, f))
    for root, _, files in os.walk(f"{HOME}/v8_additional_runs"):
        for f in files:
            if f.endswith(".sqlite"):
                sqlite_files.append(os.path.join(root, f))
    if os.path.exists(f"{HOME}/v5_profiling"):
        for root, _, files in os.walk(f"{HOME}/v5_profiling"):
            for f in files:
                if f.endswith(".sqlite"):
                    sqlite_files.append(os.path.join(root, f))

    sqlite_files = sorted(list(set(sqlite_files)))
    cnt, sz = stage_files(sqlite_files, os.path.join(STAGING_DIR, "sqlite_traces"), base_dir=HOME)
    catalog["categories"]["sqlite_traces"] = {"count": cnt, "total_bytes": sz, "size_formatted": format_size(sz)}
    print(f"  -> Staged {cnt} SQLite databases ({format_size(sz)}).", flush=True)

    # 5. PyTorch Timeline Traces (*.pt.trace.json.gz)
    print("\n[PHASE 5/8] Scanning & Staging PyTorch Profiler Timeline Traces...", flush=True)
    pt_files = []
    for root, _, files in os.walk(f"{HOME}/v8_full_results"):
        for f in files:
            if f.endswith(".pt.trace.json.gz"):
                pt_files.append(os.path.join(root, f))
    for root, _, files in os.walk(f"{HOME}/v8_additional_runs"):
        for f in files:
            if f.endswith(".pt.trace.json.gz"):
                pt_files.append(os.path.join(root, f))

    pt_files = sorted(list(set(pt_files)))
    cnt, sz = stage_files(pt_files, os.path.join(STAGING_DIR, "pytorch_traces"), base_dir=HOME)
    catalog["categories"]["pytorch_traces"] = {"count": cnt, "total_bytes": sz, "size_formatted": format_size(sz)}
    print(f"  -> Staged {cnt} PyTorch timeline traces ({format_size(sz)}).", flush=True)

    # Upload Staged Folders (Parallel & High-Throughput)
    print("\n[PHASE 6/8] Uploading Segregated Staged Assets to GCS...", flush=True)
    t_up_start = time.time()
    for cat in ["archives", "execution_logs", "nsys_profiles", "sqlite_traces", "pytorch_traces"]:
        src_cat = os.path.join(STAGING_DIR, cat)
        if os.path.exists(src_cat):
            print(f"--> Uploading category: {cat} to {BUCKET}/{cat}/ ...", flush=True)
            run_cmd(f"gcloud storage cp --recursive '{src_cat}' '{BUCKET}/'")
    print(f"--> Segregated asset upload completed in {time.time() - t_up_start:.1f}s.", flush=True)

    # 6. Structured Directories Sync (v8_additional_runs & v8_full_results)
    print("\n[PHASE 7/8] Syncing Complete Structured Results Matrices...", flush=True)
    if os.path.exists(f"{HOME}/v8_additional_runs"):
        print("--> Syncing additional_runs structured directory...", flush=True)
        run_cmd(f"gcloud storage rsync --recursive '{HOME}/v8_additional_runs' '{BUCKET}/additional_runs'")
    
    if os.path.exists(f"{HOME}/v8_full_results/20260921_195656"):
        print("--> Syncing master_results_matrix (20260921_195656)...", flush=True)
        run_cmd(f"gcloud storage rsync --recursive '{HOME}/v8_full_results/20260921_195656' '{BUCKET}/master_results_matrix/20260921_195656'")

    if os.path.exists(f"{HOME}/v8_full_suite"):
        print("--> Syncing v8_full_suite...", flush=True)
        run_cmd(f"gcloud storage rsync --recursive '{HOME}/v8_full_suite' '{BUCKET}/suites_and_scripts/v8_full_suite'")

    if os.path.exists(f"{HOME}/v8_additional_runs_suite"):
        print("--> Syncing v8_additional_runs_suite...", flush=True)
        run_cmd(f"gcloud storage rsync --recursive '{HOME}/v8_additional_runs_suite' '{BUCKET}/suites_and_scripts/v8_additional_runs_suite'")

    # 7. Generate Manifest & Index
    print("\n[PHASE 8/8] Generating Vault Index and Catalog Manifest...", flush=True)
    elapsed_sec = time.time() - start_time
    catalog["elapsed_seconds"] = round(elapsed_sec, 2)
    catalog["status"] = "COMPLETE"

    manifest_path = "/tmp/V8_DATA_MANIFEST.json"
    with open(manifest_path, "w") as fp:
        json.dump(catalog, fp, indent=2)

    readme_content = f"""# V8 Benchmark Data Vault — Structured & Segregated Repository

**Target GCS Bucket:** `{BUCKET}`  
**Generated:** `{catalog['created_at']}`  
**Transfer Elapsed Time:** `{elapsed_sec:.1f} seconds`  

---

## Directory Architecture & Segregation Schema

| Segregated Category | GCS Path | Total Files | Formatted Size | Content Description |
|:---|:---|:---:|:---:|:---|
| **Archives & Bundles** | `gs://mevreon-v8-benchmarks-segregated/archives/` | {catalog['categories'].get('archives', {}).get('count', 0)} | {catalog['categories'].get('archives', {}).get('size_formatted', 'N/A')} | Master `.tar.gz` and `.zip` archives of V8 characterization and additional runs. |
| **Execution Logs** | `gs://mevreon-v8-benchmarks-segregated/execution_logs/` | {catalog['categories'].get('execution_logs', {}).get('count', 0)} | {catalog['categories'].get('execution_logs', {}).get('size_formatted', 'N/A')} | Detailed campaign logs, launch scripts, stage 1/2/3 logs, and nohup outputs. |
| **Nsight Systems Profiles** | `gs://mevreon-v8-benchmarks-segregated/nsys_profiles/` | {catalog['categories'].get('nsys_profiles', {}).get('count', 0)} | {catalog['categories'].get('nsys_profiles', {}).get('size_formatted', 'N/A')} | All `.nsys-rep` profiling captures with preserved case and node hierarchies. |
| **SQLite Trace Databases** | `gs://mevreon-v8-benchmarks-segregated/sqlite_traces/` | {catalog['categories'].get('sqlite_traces', {}).get('count', 0)} | {catalog['categories'].get('sqlite_traces', {}).get('size_formatted', 'N/A')} | All exported `.sqlite` profiling trace databases for deep SQL query analysis. |
| **PyTorch Timeline Traces** | `gs://mevreon-v8-benchmarks-segregated/pytorch_traces/` | {catalog['categories'].get('pytorch_traces', {}).get('count', 0)} | {catalog['categories'].get('pytorch_traces', {}).get('size_formatted', 'N/A')} | PyTorch Profiler timeline traces (`.pt.trace.json.gz`) for kernel timelines. |
| **Additional Runs (Structured)** | `gs://mevreon-v8-benchmarks-segregated/additional_runs/` | Dynamic | Complete Tree | Unpacked runs (`20261005_210750`, `20261009_104123`) with JSON manifests & outputs. |
| **Master Results Matrix** | `gs://mevreon-v8-benchmarks-segregated/master_results_matrix/` | Dynamic | Complete Tree | Master characterization runs (`20260921_195656`) with all case directories. |
| **Suites & Scripts** | `gs://mevreon-v8-benchmarks-segregated/suites_and_scripts/` | Dynamic | Complete Tree | V8 benchmark test suites, configurations, and automation scripts. |

---

## Quick Access Instructions

### 1. Download Entire Specific Category (e.g. SQLite Traces)
```bash
gcloud storage cp --recursive gs://mevreon-v8-benchmarks-segregated/sqlite_traces/ ./my_sqlite_traces/
```

### 2. Download Nsight Systems Profiles
```bash
gcloud storage cp --recursive gs://mevreon-v8-benchmarks-segregated/nsys_profiles/ ./my_nsys_profiles/
```

### 3. Download Full Evidence Archive
```bash
gcloud storage cp gs://mevreon-v8-benchmarks-segregated/archives/20260921_195656_FULL_EVIDENCE.tar.gz ./
```

### 4. Query Bucket Structure
```bash
gcloud storage ls --recursive gs://mevreon-v8-benchmarks-segregated/
```
"""
    readme_path = "/tmp/V8_DATA_VAULT_INDEX.md"
    with open(readme_path, "w") as fp:
        fp.write(readme_content)

    run_cmd(f"gcloud storage cp '{manifest_path}' '{BUCKET}/V8_DATA_MANIFEST.json'")
    run_cmd(f"gcloud storage cp '{readme_path}' '{BUCKET}/V8_DATA_VAULT_INDEX.md'")
    run_cmd(f"gcloud storage cp '{readme_path}' '{BUCKET}/README.md'")

    # Cleanup staging directory
    print(f"\nCleaning local staging directory {STAGING_DIR}...")
    shutil.rmtree(STAGING_DIR, ignore_errors=True)

    print("\n================================================================================")
    print("  ✅ V8 DATA VAULT UPLOAD & SEGREGATION COMPLETED SUCCESSFULLY!")
    print(f"  Target Bucket : {BUCKET}")
    print(f"  Total Elapsed : {elapsed_sec:.1f}s")
    print("================================================================================", flush=True)

if __name__ == "__main__":
    main()
