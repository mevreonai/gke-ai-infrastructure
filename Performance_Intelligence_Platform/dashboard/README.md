# Performance Intelligence Platform — Dashboard Generator

This directory contains the dynamic dashboard generator for the Performance Intelligence Platform.

No static pre-baked dashboard or empirical results are committed here. After running your benchmark suites on the GPU cluster, use `generate_dashboard.py` to compile the run artifacts into an interactive HTML dashboard on demand.

---

## 🚀 How to Generate the Dashboard

### 1. Auto-Detect Latest Benchmark Run:
```bash
python3 dashboard/generate_dashboard.py
```
This automatically inspects `$HOME/PIP_Benchmark_Data/` (or local fallback directories), finds the most recent run, parses latency distributions (TTFT, TPOT, P99) and token throughputs, and outputs `dashboard/index.html`.

### 2. Target a Specific Benchmark Run:
```bash
python3 dashboard/generate_dashboard.py --run-dir ~/PIP_Benchmark_Data/DeepSeek-V4.1-Flash_20261014_023000
```

### 3. Target a Specific Smoke Test Run:
```bash
python3 dashboard/generate_dashboard.py --run-dir ~/PIP_Benchmark_Data/smoke_test_DeepSeek-V4.1-Flash_20261014_023600
```

---

## 🌐 How to Inspect the Generated Dashboard

### Option A: Local Browser
Open `dashboard/index.html` directly in Chrome, Firefox, Safari, or Edge.

### Option B: Quick HTTP Server (from Remote VM)
```bash
python3 -m http.server 8080 --directory dashboard
```
Then navigate to `http://<VM_IP>:8080` in your browser.
