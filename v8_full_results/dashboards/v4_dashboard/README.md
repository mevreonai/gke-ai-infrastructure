# V4 Interactive Characterization Dashboard — User & Verification Guide

This directory houses the standalone, production-grade **V4 Performance Characterization Dashboard** for `Kimi-Linear-48B` served across NVIDIA RTX PRO 6000 Ada/Blackwell GPUs.

---

## 🖥 How to Open the Dashboard

Simply double-click [`MASTER_CHARACTERIZATION_DASHBOARD.html`](file:///v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html) or open it in any modern web browser (Chrome, Edge, Firefox, Safari).

* **Zero Internet Required:** All styles, scripts, and time-budget visualizers are completely inlined into the single HTML file.
* **Production Mirror:** [`index.html`](file:///v8_full_results/dashboards/v4_dashboard/index.html) is an identical mirror of the master file for web server hosting.

---

## 🧭 Dashboard Tabs & What They Show

```
[Executive] [Throughput] [Latency] [Long Context] [Scale-Out] [Scheduler] [Profiler] [Evidence]
```

1. **Executive Overview (`#tab-executive`)**:
   - High-level KPIs: Verified 14.2 ms TTFT floor, 4.47 ms TPOT decode step floor, and 2.4× multi-node advantage under 1M context.
   - Recommended deployment decision tree across short, medium, and long contexts.

2. **Throughput Scaling (`#tab-throughput`)**:
   - Interactive tokens/sec vs. concurrency curves across TP2, TP4, and TP8 topologies.
   - Batch size saturation knee points.

3. **Latency Distributions (`#tab-latency`)**:
   - Time-to-First-Token (TTFT) and Time-per-Output-Token (TPOT) percentiles ($P_{50}, P_{90}, P_{99}$).

4. **Long Context Dynamics (`#tab-long-context`)**:
   - **FP8 KV Cache Card (`#fp8-kv-cache-card`)**: Documents why FP8 KV caching requires Blackwell SM100 architecture and defaults to BF16 on Ada Lovelace.
   - **Host Memory Tiering Card (`#offload-card`)**: Details the 41.39s TTFT penalty on 600K context revisits when swapping to DDR5 host memory.

5. **Scale-Out Architecture (`#tab-scale-out`)**:
   - **Card 4.7 (PP2 Layer Rebalance)**: Shows the +1.18% speedup (5.965 ms vs 6.036 ms) achieved with the asymmetric 15/12 split across pipeline stages.
   - **Multi-Node Concurrency Profiles**: Compares dual-node TP4/PP4 against single-node TP8 under sustained 1M load.

6. **Scheduler & Serving Queue (`#tab-scheduler`)**:
   - Queue wait times, chunked prefill scheduling, and concurrency expansion dynamics.

7. **Profiler & Kernels (`#tab-profiler`)**:
   - **Protocol Disclosure Banner**: Explains why Nsight traces run with `--enforce-eager` (~30.5 ms decode step) while serving uses CUDA Graphs ON (4.47 ms).
   - **Four High-Resolution Time-Budget Charts**: Inline Base64 breakdowns of first-token and decode-token wall times.

8. **Audited Evidence Ledger (`#tab-evidence`)**:
   - Complete 16-column ledger tracking all 126 benchmark runs with exact cluster hardware and driver metadata.

---

## 🧪 How to Run Automated Verification

To verify that the dashboard has zero broken images, zero broken links, and 100% compliance with audit specifications, run:

```bash
python tools/run_v1_4_verification.py
```
Expected output: **`Final Result: ALL 72 VERIFICATIONS PASSED (100%)!`**
