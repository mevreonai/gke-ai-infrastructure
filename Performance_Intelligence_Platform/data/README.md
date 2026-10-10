# Performance Intelligence Platform — Telemetry & Data Vault

This directory serves as the canonical landing vault for all benchmark telemetry, server logs, hardware metrics, and verification manifests produced during master benchmark suite runs.

---

## 🗂 Vault Structure

```
Performance_Intelligence_Platform/data/
├── raw_runs/                  # Step-by-step benchmark receipts (.done markers, server logs, command receipts)
│   └── README.md              # Detailed structural documentation for all 15 benchmark steps
├── results/                   # Aggregated JSON results, Prometheus metrics, and hardware traces
└── README.md                  # This file
```

---

## 🚀 Execution & Output Population

When `./scripts/run_master_benchmark.sh` is executed on the cluster, output receipts are automatically structured and populated:
* **`raw_runs/step01_...` to `raw_runs/step15_...`**: Individual execution directories per step.
* **`master_step_status.jsonl`**: Real-time step status log recording step numbers, timestamps, and return codes (`rc: 0`).
* **`combined_vllm_runs.json` & `.csv`**: Consolidated multi-step metrics produced by the post-execution aggregation pipeline.
