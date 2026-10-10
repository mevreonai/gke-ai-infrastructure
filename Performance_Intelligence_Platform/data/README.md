# Performance Intelligence Platform — Telemetry & Data Vault

This directory serves as the canonical landing vault for all benchmark telemetry, server logs, hardware metrics, continuous batching data, and verification manifests produced during benchmark runs.

---

## 🗂 Vault Structure

```text
Performance_Intelligence_Platform/data/
├── raw_runs/                  # Step-by-step benchmark receipts (.done markers, server logs, command receipts)
│   └── README.md              # Detailed structural documentation for all 17 benchmark steps
├── results/                   # Aggregated JSON results, Prometheus metrics, and hardware traces
│   ├── continuous_batching/   # Continuous batching manifest, step-cost fits, pause scans
│   └── summaries/             # Consolidated CSV tables and master Markdown summaries
└── README.md                  # This file
```

---

## 🚀 Execution & Output Population

When `./scripts/run_master_benchmark.sh` or `./scripts/run_continuous_batching.sh` is executed on the cluster, output receipts are automatically structured and populated:
* **`raw_runs/step01_...` to `raw_runs/step17_...`**: Individual execution directories per step.
* **`master_step_status.jsonl`**: Real-time step status log recording step numbers, timestamps, dry-run flags, and return codes (`rc: 0`).
* **`pause_scan.csv`**: Automated scan of all per-request JSONs for stalls and engine decode pauses.
* **`step17_continuous_batching/`**:
  - `continuous_batching_manifest.json`: Full machine-readable manifest of all executed blocks.
  - `RESULT_SUMMARY.md`: Human-readable Markdown summary with throughput, latency percentiles, and timing.
  - `BLOCK_<N>_SUMMARY.md`: Detailed per-block execution telemetry.
* **Reference Results Compendium**:
  - [`PIP_MASTER_RESULTS_AND_BENCHMARKS.md`](file:///c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/PIP_MASTER_RESULTS_AND_BENCHMARKS.md): Master empirical results table, model curves, and telemetry compendium.
