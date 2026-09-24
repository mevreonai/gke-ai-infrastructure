# Audit package: V6 vLLM Characterization Dashboard

Everything in the 22-page audit PDF, re-packaged so an AI coding agent can read it without losing tables, numbers, or charts.

| File | What it is | Authoritative for |
|---|---|---|
| `00_TASK.md` | The prompt to give the agent (rules, phases, report format) | How to work |
| `01_spec.md` | Full report as Markdown, figures embedded | Requirements |
| `02_evidence_rows.csv` / `.json` | 59 evidence rows from Appendix B + the 6 missing configured cases | **All numbers** |
| `02b_chart_only_values.csv` | Values that exist only inside chart images (Figs 1, 4, 9, 10, 11), pixel-measured | Nothing: approximate; verify against the HTML |
| `03_chart_map.md` | Figure → source rows, plus buildable-vs-blocked table for required charts | Which data feeds which chart |
| `04_acceptance_checklist.md` | Spec §16 as a per-phase pass/fail form + mechanical checks | Sign-off |
| `figures/` | 11 figures extracted from the PDF at original resolution | Visual reference only |
| `original.pdf` | Untouched source | Fallback |

## Known gaps: these are NOT in the report, so they are not in this package

- `run_id`, `source_file`, and sample count N for any row (columns exist in the CSV but are empty on purpose)
- Raw logs / manifests / Prometheus / Nsight / V4 NCCL data
- Numeric values for Scale-Out (Figs 9–10) and the "UI JS" bars (Figs 4, 11): recoverable only from the dashboard HTML itself (approximate pixel reads provided in `02b`)
- The archived case manifests (`10_vllm_surrogate_cases.json`, `10b_vllm_multi_node_cases.json`)
- `MASTER_CHARACTERIZATION_DASHBOARD.html` itself: **it must be in the same workspace as this folder**

## Suggested placement

```
<your-dashboard-repo>/
  MASTER_CHARACTERIZATION_DASHBOARD.html
  docs/audit/   <- this folder's contents
```
