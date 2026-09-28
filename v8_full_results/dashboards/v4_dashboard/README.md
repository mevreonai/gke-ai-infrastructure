# V8 Characterization Campaign — V4 Master Dashboard (V6 Comment Closure Release)

This directory contains the production-grade, self-contained characterization dashboards and automation toolchain for the **V8-FULL Benchmark Campaign** evaluated on MoonshotAI Kimi-K1.5-Preview (67B hybrid MoE, 32K &rarr; 1M Context) across dual-node 16&times; NVIDIA RTX 6000 Ada Generation Server GPUs.

---

## 1. Directory Structure

```text
v8_full_results/dashboards/v4_dashboard/
├── index.html                                            # Default production entry point (Dual-Tab)
├── MASTER_CHARACTERIZATION_DASHBOARD.html                 # Canonical distribution dashboard (Dual-Tab)
├── MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html   # Version 1: Preserves legacy 'Key Finds' & canonical 'Key Discoveries'
├── MASTER_CHARACTERIZATION_DASHBOARD_NO_KEYFINDS.html     # Version 2: Production-hardened with sole 'Key Discoveries' top-10
├── apply_surgical_v6_fixes.py                            # Deterministic dashboard generator script
├── run_final_parity_validation.py                        # Automated 18-gate parity validation suite
├── KEY_DISCOVERIES_VALIDATION.json                       # Machine-readable validation audit report (18/18 PASS)
├── KEY_DISCOVERIES_VALIDATION.md                         # Markdown sign-off validation matrix (18/18 PASS)
├── DASHBOARD_CANONICAL_DATA.json                         # Underlying canonical telemetry run data
├── EXECUTIVE_DISCOVERIES.json                            # Legacy executive findings ledger
├── EXECUTIVE_DISCOVERIES_V2.json                         # Cross-validated executive findings ledger
├── chart.umd.js                                          # Local offline Chart.js bundle
└── README.md                                             # This architecture and operations guide
```

---

## 2. Dashboard Variants

To accommodate both organizational continuity and strict single-source production criteria, two release versions are maintained:

### Version 1 — Dual-Tab Master Dashboard
* **Files:** [`MASTER_CHARACTERIZATION_DASHBOARD.html`](./MASTER_CHARACTERIZATION_DASHBOARD.html), [`MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html`](./MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html), and [`index.html`](./index.html).
* **Audience:** Engineering leads, cross-functional teams, and stakeholders who cross-reference prior benchmarks.
* **Navigation:** Exposes both the historical `🎯 Key Finds` tab and the updated canonical `✨ Key Discoveries` tab.

### Version 2 — Clean Production Master Dashboard
* **Files:** [`MASTER_CHARACTERIZATION_DASHBOARD_NO_KEYFINDS.html`](./MASTER_CHARACTERIZATION_DASHBOARD_NO_KEYFINDS.html).
* **Audience:** Final executive technical sign-off and public release.
* **Navigation:** Removes `🎯 Key Finds` from top navigation, presenting `✨ Key Discoveries` as the single canonical Top-10 experience to eliminate duplicate representations.

---

## 3. The 10 Key Discoveries Architecture

The `✨ Key Discoveries` tab is structured around an auditable 3-tier information hierarchy:

$$\text{Signal Rail (Executive Cards)} \longrightarrow \text{Engineer Explorer (10 Subpages + 20 Charts)} \longrightarrow \text{Forensic Evidence Modal (Exact Run Telemetry)}$$

### Summary of Canonical Discoveries

| # | Finding Name | Category | Scope / Hardware | Canonical Metric / Finding | Core Decision Changed |
|---|---|---|---|---|---|
| **1** | **Fabric Exposure** | Topology Dependent | 128K&rarr;1M &middot; 4 Topologies &middot; Native / 100G / 20G | 1M 20G TTFT: TP16/PP1 degrades **+276.69%** (68.20s &rarr; 256.89s) vs TP4/PP4 degrading only **+3.91%** (28.57s &rarr; 29.68s). | Topology dictates exposed transport risk; size networks to application TTFT exposure, not raw NIC line-rate. |
| **2** | **Concurrency Paradox** | Admission / SLO Risk | TP4/PP1 8K&rarr;1M c1&rarr;c4 &middot; TP8/PP1 R@1M | At 1M, scaling c1 &rarr; c4 yields only **+1.52% output TPS** while TTFT spikes **2.48&times;** (231.27s), TPOT jumps **26.15&times;** (267.41ms), and requests queue for **134.43s**. | Set admission control from latency & queue SLOs; low memory occupancy does not guarantee concurrent capacity. |
| **3** | **Long-Context Shift** | Scaling Regime | TP4/PP4 profiler matched pair (128K &rarr; 512K) | Full-attention grouped work expands **~15.70&times;** (empirical $p \approx 1.99$). MoE (~3.80&times;) and KDA (~3.95&times;) grow approximately linearly. | Re-profile tuning targets at each context tier; attention dominates at extreme context while GEMM/communication share dilutes. |
| **4** | **Prefix Cache Reuse** | Algorithmic Leverage | TP4/PP1 single-node &middot; 8K / 128K / 512K / 1M | Repeat-hit median latency drops from 94.23s down to **2.61s (36.0&times; speedup @ 1M)**, moving from super-linear cold prefill to near-linear warm hit. | Partition repeat-prefix traffic as a dedicated workload class; evaluate routing and residency strategies empirically. |
| **5** | **Prompt Admission** | Capacity Planning | TP4/PP1 open-loop (8K vs 128K) | Request rate drops 18.2&times; (3.359 to 0.185 req/s), but normalized prompt token ingestion drops only **~1.14&times;** (27.51K vs 24.19K tok/s). | Normalize prefill capacity into prompt tokens/s; raw requests/sec distorts mixed-prompt cluster planning. |
| **6** | **Parallelism Frontier** | Architecture Design | TP4/PP1&rarr;PP4 &middot; TP8/PP1&rarr;PP2 &middot; TP16/PP1 | At 8K/128K, TP synchronization offsets compute gains. At 512K/1M, compute benefits outweigh TP overhead. At 1M, TP4/PP4 achieves 28.57s TTFT at 457.09 GPU-s. TP8/PP2 achieves 41.52s at 664.24 GPU-s. | Sizing must balance turn latency (TTFT) against GPU-seconds occupancy per request along the empirical Pareto frontier. |
| **7** | **TP Decode Comm** | Interconnect Bottleneck | 8K profiler + E2E 128K&rarr;1M &middot; TP4/PP1 vs TP8/PP1 | TP8 suffers a **+41.9% TPOT penalty** at 8K (6.35ms vs 4.48ms) and persists to 1M (+17.9%). 8K PyTorch profiler traces 583.87ms Self CUDA time in AllReduce (52.7% of decode). | Validate collective synchronization latency before widening tensor parallelism for interactive generation. |
| **8** | **Runtime Knobs** | Serving Optimization | TP4/PP1 &middot; chunk 4K&rarr;16K &middot; maxseq 4/8/16 | Chunk prefill delivers **-27.1% TTFT reduction** at 1M (38.87s vs 53.30s). `max_num_seqs` across 4, 8, 16 is flat (232.342s, 232.364s, 232.250s) and non-binding. | Optimize only knobs with matched A/B derivatives in the current cluster state. |
| **9** | **Busy GPU &ne; Efficiency** | Operational Metrics | TP4/PP4 vs TP16/PP1 across 128K&rarr;1M (16 GPUs) | TP16/PP1 reports 80.6% GPU SM utilization vs TP4/PP4 at 62.8%, yet TP16/PP1 takes **2.39&times; longer to complete prefill** (68.20s vs 28.57s). | High SM activity reflects communication wait states and collective kernels; never size topologies by utilization alone. |
| **10** | **KV Cache vs VRAM** | Memory Architecture | TP4/PP1&rarr;PP4 sweep &middot; TP8/PP1&rarr;PP2 &middot; TP16/PP1 | KV cache pressure dilutes with pipeline stages (12.29% &rarr; 5.91% &rarr; 2.75%), but physical device memory remains high (~87.27 to 88.83 GiB peak telemetry on 95.59 GiB devices). | Use KV% for cache pressure and physical device telemetry for OOM headroom; never substitute one for the other. |

---

## 4. HTML Generator Script (`apply_surgical_v6_fixes.py`)

The generator script deterministically updates the HTML dashboard files while preserving all 10 subpages, 41 table rows, and 20 dynamic Chart.js charts.

### Key Operations Performed
1. **Canonical 20G TTFT Chart Synchronization:**
   Replaces stale literals (`2.926`, `18.860`, `2.510`, `15.650`) in line chart `chart-p1-primary` with verified run values:
   - TP4/PP2: `[2.859, 18.372, 53.127]`
   - TP8/PP2: `[2.810, 15.546, 41.472]`
   - TP4/PP4: `[1.961, 11.134, 29.684]`
   - TP16/PP1: `[31.053, 128.275, 256.889]`
2. **Neutral GPU Activity Metrics:**
   Replaces subjective chart labels (`Util (%) - Erroneous High`, `TTFT (s) - Fast & Efficient`, `Up to 3.75× Slower!`) with objective telemetry labels (`TP16 / PP1 GPU activity (%)`, `TP4 / PP4 TTFT (s)`).
3. **Memory & Headroom Semantics:**
   Updates memory labels to `Peak GPU Memory Telemetry (GiB)`. Replaces false saturation claims and linear cross-stage KV multiplication ($PP \times KV\%$) with rigorous headroom semantics.
4. **Empirical Exponent Framing:**
   Updates profiler observation from unqualified quadratic expansion to `corresponding to empirical p≈1.99 over the matched 128K→512K profile interval`.
5. **Signed Differences over (noise):**
   Replaces all legacy `(noise)` labels with exact signed percentages (`-0.10%`, `-0.13%`).
6. **Direct Forensic Evidence Routing:**
   Removes the redirect loop where `openEvidencePopup` forwarded back to `openFindingModal`. Configures `openEvidenceForFinding(pageId)` to open the real in-place evidence popup modal (`evidence-popup-modal`) with exact run IDs (`EV-030`, `EV-034`, `PR-007`, `EV-038`, `EV-040`, `EV-044`, `PR-003`, `EV-048`, `EV-050`, `EV-054`).
7. **Tri-State Trust Strip:**
   Surfaces explicit profiler completeness:
   - `APPLICATION EVIDENCE: 119/126 COMPLETED E2E ROWS VALIDATED`
   - `PROFILE EVIDENCE: 14/22 DISTRIBUTED PROFILES COMPLETE`
   - `STRICT SUITE SIGN-OFF INCOMPLETE`
   - Physical transport rates: `Native 173.58 Gb/s`, `100G 56.84 Gb/s`, `20G 16.48 Gb/s`.

---

## 5. Automated Parity & Validation Suite (`run_final_parity_validation.py`)

The automated validation suite enforces 18 strict quality gates before any dashboard can be marked production-ready.

```bash
python run_final_parity_validation.py
```

### Verification Checklist (18/18 PASS)
- [x] **P0_Stable_IDs_1_to_10**: 10 full-depth discovery pages in exact sequence 1..10.
- [x] **P0_Trust_Strip_Wording**: Contains Application 119/126, Profile 14/22, and Strict Sign-Off Incomplete.
- [x] **P0_Measured_Transports**: Contains Native 173.58 Gb/s, 100G 56.84 Gb/s, 20G 16.48 Gb/s.
- [x] **P0_Map_Scope_Column**: Finding map table contains dedicated Scope column.
- [x] **P0_Coverage_Rails_On_Cards**: Coverage rails verified across all Signal cards.
- [x] **P0_Finding1_Fabric_Data**: Canonical 20G TTFT values verified; stale literals 2.926, 18.860, 2.510, 15.650 completely eliminated.
- [x] **P0_Finding2_Concurrency_Data**: Validated 0.3415&rarr;0.3467 tok/s, 231.268s TTFT, 267.411ms TPOT, 134.428s queue.
- [x] **P0_Finding3_Complexity_Wording**: Uses `empirical p≈1.99`; quadratic prefill expansion claims removed.
- [x] **P0_Finding4_Prefix_Reuse**: Validated cold vs repeat-hit speedup (36.0&times; @ 1M).
- [x] **P0_Finding5_Admission_Data**: Validated 3.3586 vs 0.1846 req/s admission throughput.
- [x] **P0_Finding6_Parallelism_Frontier**: Contains TP8/PP2 @ 664.24 GPU-s / 41.515s measured point; TP8/PP4 never rendered.
- [x] **P0_Finding7_TP_Decode_TPOT**: Validated TP4/TP8 PyTorch AllReduce breakdown 251.53ms vs 583.87ms.
- [x] **P0_Finding8_Runtime_Knobs**: Fixed 233.364s typo to 232.364s; chunk prefill -27.1% verified; maxseq flat.
- [x] **P0_Finding9_Busy_GPU**: Neutral activity labels applied; Erroneous High / Fast & Efficient removed.
- [x] **P0_Finding10_KV_vs_VRAM**: Peak GPU Memory Telemetry used; Global KV check and 93% saturated removed.
- [x] **P0_UX_Action_Labels**: Signal uses `View Detailed Finding ↓`; Engineer uses `Inspect Evidence →`; Forensic Modal View removed.
- [x] **P0_With_KeyFinds_Nav_Integrity**: Version 1 preserves `Key Finds` tab active alongside `Key Discoveries`.
- [x] **P0_No_KeyFinds_Nav_Isolation**: Version 2 removes/hides legacy `Key Finds` tab; `Key Discoveries` is single Top-10.

---

## 6. How to Reproduce & Build

### Step 1: Execute Generator
From the workspace root or dashboard folder:
```bash
python apply_surgical_v6_fixes.py
```

### Step 2: Run Parity Validation
Verify that all 18 tests pass with zero errors:
```bash
python run_final_parity_validation.py
```

### Step 3: View Dashboards Locally
Open any of the generated HTML files directly in a web browser:
```powershell
# Windows PowerShell
Start-Process "MASTER_CHARACTERIZATION_DASHBOARD.html"

# Or serve via Python HTTP server
python -m http.server 8080
# Navigate to: http://localhost:8080/MASTER_CHARACTERIZATION_DASHBOARD.html
```

---

## 7. Audit Compliance & Quality Guarantee

* **Zero Mock Telemetry:** Every displayed number traces directly to raw logs in `results_V8_runs(4).zip` / `vllm_runs.csv` / `PROFILE_VALIDATION.json`.
* **Zero Forbidden Phrases:** Grep count is **0** across all production files for stale literals, unproven causal claims, and subjective labels.
* **Deterministic Build:** The HTML generator and parity validation suites are fully automated and version-controlled.
