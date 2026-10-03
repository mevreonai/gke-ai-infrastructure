# Master Dashboard review — fixes tab by tab, checked against the V8 run results

*v1.2 (3 Oct 2026): adds §4.17 — an end-to-end wall-time budget (queue · prefill kernels · collectives · pipeline waits · overhead for the first token; collectives · memory floor · kernels · waiting for the decode token) per layout, prompt and load, which no tab shows today and no earlier item asked for as one view; bounds the TP16 decode AllReduce claim in §4.8 (11–16 ms, not 16); notes in §4.3 that the 1M decode token is memory-bound on its KV read. Fix list items 27–28 and two runs added.*

*v1.1 (3 Oct 2026): one correction to §4.7 — the `8,7,6,6` pipeline partition proposed in v1 is withdrawn; the stage-0 idle is structural on this layer map and the partition test moves to PP2 (`15,12`). Items 18 in §5 and the run list are updated accordingly. Nothing else changed.*

**Dashboard reviewed:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_29thSept_1amIST.html` (8 tabs, 36 charts, 58 tables, 7 dropdowns) and the Key Discoveries tab (10 findings, Signal view + 10-page explorer).
**Data used for every check:** `results_V8_runs.zip` → `results/real_data/` (identical to the copy behind the engineering brief) plus `results/logs/` (preflight, readiness). Nothing in this note comes from memory or from the dashboard itself; every number was recomputed from the files named next to it.
**How to read it:** §1 lists the problems that cut across tabs (fix these first, they repeat everywhere). §2 goes tab by tab and dropdown by dropdown. §3 is the list of things we checked that are correct, so nobody wastes time re-verifying them. §4 is the part we think matters most: analyses the data already supports but the dashboard (and in several cases the PDF brief) does not show. §5 is the prioritised fix list.

Severity tags: **P0** = wrong or misleading on screen, fix before anyone else sees it · **P1** = unsupported claim or missing qualifier · **P2** = presentation, wording, consistency.

## 0. Summary

Checked: 36 Scale-Out explorer cells × 7 metrics (252 values), the numeric claims on the Executive / Scale-Up / Long Context / Scheduler tabs (§3 lists them), all 10 Key Discoveries pages (every number in every table), the Profiler tab against the nsys and torch exports, and the Evidence tab filters against `combined_vllm_runs.csv` and `coverage.csv`.

What holds: every TTFT / TPOT / throughput / KV / queue number taken from `combined_vllm_runs.csv` matches the file (0 mismatches in 252 explorer cells; all 20G/100G deltas correct to the decimal; all prefix counters, open-loop knees, max-num-seqs and chunk numbers correct). The campaign bookkeeping (119/126, 95 + 24 + 7, 14/22 profiles) matches `FINAL_VALIDATION.json` and `coverage.csv`.

What does not hold, in order of damage:

| # | Issue | Where it shows | Severity |
|---|---|---|---|
| 1 | Scale-Out **50G and 10G** selections silently render **native** numbers and native evidence IDs under a capped title | Scale-Out tab, network dropdown (2 of 5 options) | P0 |
| 2 | Every Nsight profile (6 single-node + 17 distributed) ran with `--enforce-eager`; every serving run had CUDA graphs on. Decode conclusions built on the profiles (AllReduce 86–89 %, 369/446 µs per call, 888 K launches, "CUDA graphs are a candidate optimisation") describe a mode we never serve in | Profiler tab, Executive bottleneck map, KD #7 layer 3, Scale-Up interpretation | P0 |
| 3 | Distributed **decode** profiles are marked COMPLETE but their per-rank exports failed (0–2 usable ranks of 8–16); the "key empirical finding" cells for those rows cannot have come from them | Profiler coverage matrix, Executive "14/22" tile | P0 |
| 4 | The NUMA / dual-socket cause for the TP8 decode penalty is stated as "cross-validated" on five tabs; the hardware data points the other way (socket crossing adds ≤ 0.4 µs, P2P level changes nothing, a wider ring explains +17 µs of the +40 µs, the rest appears only in serving) | Executive, Scale-Up, Profiler, KD #7, Scheduler | P1 |
| 5 | Network facts that are not in the data: MTU 8896 (archive: `mtu 1460`), interface ens4 (archive: ens3), 0.05 ms RTT (no measurement in the archive), "0 drops" (native iperf logged 4,426 retransmits), "tc/netem" (it is tc HTB), "AMD EPYC 9654" (no CPU inventory in the archive) | Header strip, Scale-Out network tables, Profiler provenance | P1 |
| 6 | "NCCL POLICY INCOMPLETE · Ray audit missing on 12 scale-out runs" is a validator counting bug: all 12 `*_RAY_NCCL_ENV_AUDIT.json` files exist and pass (2 live nodes, 0 violations each) | Executive tile | P1 |
| 7 | Four numbers on screen do not exist in the data: "sub-15 ms TPOT" at c16 (it is 19.2 ms), "chunk=4096" for TP4/PP4 (it is 8192), "TP8 slightly slower at 128K (5.59 s vs 5.37 s)" (it is 4.81 s vs 4.53 s), "AllReduce 5,739 µs on TP16" (exports give 3,911 µs at 128K) | Executive, Profiler | P0 |
| 8 | Hit-ratio story on the Long Context tab ("~50 % reflects the cold-first-then-warm pattern") is wrong: with 1 cold + 3 repeats a clean run gives 75 %; 50 % means **one of three repeats missed** — and the per-request data says which one and why | Long Context, KD #4 | P1 |
| 9 | KD #7's 2.32× AllReduce ratio mixes the single prefill step's 55 big AllReduces (119 → 174 ms) into a 7,040-call sum; decode-only it is 132 → 410 ms (3.1×), 18.9 → 58.7 µs per call | KD #7, Profiler torch panel | P1 |
| 10 | Capacity knee is a "slope inflection" of means; 93 of 119 runs have unreliable p95 (≤ 12 requests). Without an explicit SLO the 128K knee (0.75×) already violates p95 TPOT ≤ 100 ms (145 ms) | Scheduler & KV, KD #5 | P1 |

And the other way round, the biggest missed opportunities (details in §4): the KV pool is **8.1 M tokens whatever the TP width** and scales only with PP; long-prompt prefill is **strictly serialised** across concurrent requests (the per-request timeline proves it and names the scheduler limit that binds); the decode step budget from the torch profiles explains the whole 4.47 ms token without the eager artefacts; AllReduce is 55 × 2.0 ms per 8K prefill chunk, i.e. about half of an 8K first token and 43 % of a 128K one on this PCIe box; energy per token is in the data (power is sampled on every run) and ranks layouts differently from utilisation.

## 1. Cross-cutting issues (fix once, they repeat on several tabs)

### 1.1 P0 — Scale-Out: 50G and 10G show native data

`updateScaleoutDashboard()` does

```js
const netData = scaleoutMetricsData[activeScaleoutNet] || scaleoutMetricsData['GCP_NATIVE'];
...
const matrix = netMap[activeScaleoutNet] || netMap['GCP_NATIVE'];
```

`scaleoutMetricsData` only has keys `GCP_NATIVE`, `GCP_CAPPED_100G`, `GCP_CAPPED_20G`. Selecting "50G Cap (HW Qualified 33.0 Gbps)" or "10G Cap (HW Qualified 9.0 Gbps)" re-titles the charts "(GCP_CAPPED_50G)" / "(GCP_CAPPED_10G)" and renders the native values — TP16/PP1 at 1M shows 68.20 s under a 10G title (the measured 20G value is 256.89 s, and 10G was never run). The evidence drawer then opens native evidence IDs (EV-082…) for a "capped" point. This is exactly the "missing is never zero" rule the dashboard states, broken in the opposite direction (missing rendered as native).

Fix: drop the two options, or keep them and render application cells as `NOT_RUN` (no bars, no verdicts) while the hardware panel shows the iperf/NCCL numbers that do exist for 50G/10G (`hardware_processed/iperf.csv`: 33.0 / 9.0 Gb/s; `nccl_points.csv`: 256M SendRecv 4.09 / 1.11 GB/s). Also the option labels: the 100G/20G ones say "tc/netem"; the shaper is `tc` **HTB** (`network_validation/node0_qdisc.txt`: `qdisc htb 1: root`).

### 1.2 P0 — All Nsight profiles are CUDA-graphs-off captures

Every `server_command.txt` / `SERVER_COMMAND.txt` under `profiles_single_node/*`, `profiles_multi_node_native/*/*/workload/` and `profiles_multi_node_capped/.../workload/` contains `--enforce-eager --enable-layerwise-nvtx-tracing --profiler-config.profiler cuda`. None of the 44 serving server commands (`case_manifest.json → server_command`, covering all 119 runs) contains `--enforce-eager`.

What that does to the numbers:

| Quantity | Eager profile | Serving (graphs on) | Ratio |
|---|---|---|---|
| TP4 8K decode step (`profiles_single_node/tp4_decode/bench.json` vs `tp4_closedloop_8k/c1`) | 30.46 ms | 4.47 ms | 6.8× |
| TP8 8K decode step | 31.31 ms | 6.35 ms | 4.9× |
| TP4 128K prefill TTFT (`tp4_prefill/bench.json` vs `tp4_context_baseline/128k_c1`) | 4,803 ms | 4,532 ms | 1.06× |
| TP8 128K prefill TTFT | 4,658 ms | 4,810 ms | 0.97× |

So the prefill captures are usable (prefill is a few large kernels per layer; graphs barely matter) and the decode captures are not: in eager mode each rank launches ~650 kernels per token from Python, ranks drift, and the AllReduce kernel on the early rank spins waiting for the late one — which is why the decode nsys tables show AllReduce at 86.3 % (TP4) / 89.1 % (TP8) with 369.5 / 446.5 µs per call, while the graphs-on torch profiles give 18.9 / 58.7 µs per decode AllReduce (§1.9). The same applies to "888,504 launches, 3.47 s in cudaLaunchKernel, 3.64 s in cudaEventSynchronize": that is the cost of eager mode, not of serving.

Fix: (a) a banner on the Profiler tab and on every tile that uses a decode nsys number: "captured with `--enforce-eager`; decode step 30.5 ms vs 4.47 ms in serving; use for kernel inventory, not for time shares"; (b) remove "CUDA Graph capture is a candidate follow-up optimisation" (two places) — serving already runs with graphs; (c) replace the decode time-share numbers with the torch-profile decode-only budget (§4.3); (d) keep prefill shares, they are fine; (e) re-capture decode once with graphs on (`nsys` supports it; the torch profiler already did).

### 1.3 P0 — Distributed profile "COMPLETE" ≠ usable

`PROFILE_VALIDATION.json` checks that `.nsys-rep` files exist. The per-worker exports (`worker_process_*_processed/cuda_gpu_kern_sum.csv`) are what the tab reads, and many contain only `Exportation error: Cannot read from stream` / `ERROR: Database file ... could not be found`:

| Profile point | Workers | Usable kernel exports | Dashboard status |
|---|---|---|---|
| tp4_pp4 prefill_128k (native) | 16 | 16 | COMPLETE ✓ |
| tp4_pp4 long_prefill_512k | 16 | 16 | COMPLETE ✓ |
| tp4_pp2 prefill_128k | 8 | 8 | COMPLETE ✓ |
| tp8_pp2 prefill_128k | 16 | 15 | COMPLETE ✓ |
| tp16_pp1 prefill_128k | 16 | 12 | COMPLETE ✓ |
| tp16_pp1 long_prefill_512k | 12 | **1** | COMPLETE ✗ |
| tp4_pp4 decode_8k | 16 | **2** | COMPLETE ✗ |
| tp4_pp2 decode_8k | 8 | **2** | COMPLETE ✗ |
| tp8_pp2 decode_8k | 16 | **0** | COMPLETE ✗ |
| tp16_pp1 decode_8k | 9 | **0** | COMPLETE ✗ |
| tp4_pp2 batched_decode_8k_c8 | 4 | **0** | COMPLETE ✗ |
| tp8_pp2 / tp16 / tp4_pp4 batched_decode_8k_c8 | 1 / 2 / 0 | 0 / 0 / 0 | INCOMPLETE ✓ |
| capped-100G prefill_128k (3 points) | 8 / 16 / 16 | 8 / 16 / 15 | COMPLETE ✓ |

Also the `nccl_op_sum.csv`, `nccl_gpu_proj_sum.csv`, `nccl_gpu_time_sum.csv` exports are error stubs for every worker ("Report 'nccl_op_sum' could not be found" — the nsys 2025.6.3 install lacks those report scripts), although `NSYS_ANALYSIS.json` records `rc: 0, exists: true` for them.

Fix: add a "usable exports" column to the coverage matrix (count of worker CSVs with a header row), set status from it, and delete the "KEY EMPIRICAL FINDING" text of rows whose exports are empty (tp4_pp4_decode_8k "NUMA-local TP4 handles layerwise collectives", tp8_pp2_decode_8k "cross-NUMA 8-GPU ring barrier adds 20.8 %", tp4_pp2_decode_8k_c8 "zero TCP packet retransmissions", tp16_pp1_prefill_512k "…" rest on 0–2 ranks or on nothing). Re-export from the `.nsys-rep` files where they are intact; where the rep itself is truncated (the "Cannot read from stream" ones), re-capture.

### 1.4 P1 — The NUMA / dual-socket cause is asserted, the data does not support it

Text on screen: "4-GPU barrier avoids dual-NUMA PCIe bridge traversal [MEDIUM / CROSS-VALIDATED]" (Executive, twice), "Single-NUMA 4-GPU ring avoids dual-NUMA bridge traversal (cross-validated contributor)" (Scale-Up, twice), "TP8 spans 2 NUMA sockets (PCIe bridges); AllReduce ring call takes 82.9 µs vs 35.7 µs" and "+20.8 % cross-NUMA socket traversal overhead" (Profiler), "Co-locating TP4 within a single NUMA socket is a candidate optimisation" (Profiler, twice).

What the hardware files say:

* `hardware_raw/node0/nvbandwidth_latency.raw.json` (device_to_device_latency_sm): PIX 0.94 µs, NODE 1.19 µs, SYS (across sockets) 1.32 µs. Crossing the socket costs **≤ 0.4 µs per hop**; the TP8 penalty is +40 µs per AllReduce.
* `hardware_raw/node0/nvbandwidth_d2d.raw.json`: GPU→GPU copy bandwidth is 51.7–53.1 GB/s for PIX, NODE and SYS alike — the socket crossing costs no bandwidth either.
* `hardware_processed/nccl_points.csv`, labels `140_ar_tp8_sensitivity_p2p_PHB / _SYS / 141_…_p2p_disabled`: 16 KiB AllReduce at TP8 = 37.2–38.8 µs whatever the P2P level, vs 37.6 µs default. The P2P path (which is what a "bridge traversal" story is about) is not the variable.
* Same file, `120_ar_tp4` vs `121_ar_tp8` at 16 KiB: 19.0 µs vs 37.6 µs with no model running. Ring AllReduce does 2(n−1) steps: 6 at TP4, 14 at TP8; a fit of 2.17 µs per step + 6.6 µs fixed reproduces both numbers. The wider ring explains **+17 µs** of the +40 µs.
* Torch profiles with graphs on (`profiles_torch_single_node`, decode-only, §1.9): 18.9 → 58.7 µs per call, i.e. +40 µs. The remaining **+22 µs appears only in serving**. No `taskset`/`numactl`/pinning appears in any `server_command`; the two 4-GPU halves of a TP8 group run their worker processes on whichever cores the scheduler picks, on two sockets. Host-side skew between ranks is the open suspect, not the PCIe path.

Fix: replace "avoids dual-NUMA bridge traversal (cross-validated)" with "the 8-GPU ring is 2× longer (14 vs 6 steps: +17 µs per call measured by nccl-tests) and a further +22 µs per call appears only under serving; socket crossing itself adds ≤ 0.4 µs (nvbandwidth) — pinning test pending". Downgrade cause confidence to MEDIUM-LOW until the pinning run is done. Keep the decision (TP4 for interactive decode); it does not depend on the mechanism.

### 1.5 P1 — Network facts that the archive contradicts or does not contain

| On screen | In the archive | Fix |
|---|---|---|
| "MTU 8896 (Jumbo)", "MTU 8896 verified", "All multi-node runs used … MTU 8896 jumbo frames" | `vllm_scaleout_network_matrix/*/network_validation/node0_link.txt` and `node1_network_state.txt`: `ens3: … mtu 1460` in all three modes | state MTU 1460 (GCP default) or attach the file that says otherwise |
| "Interface ens4" | `NETWORK_MODE.json`: `"iface": "ens3"` | ens3 |
| "0.05 ms RTT" (header, two tables) | no ping/RTT file anywhere in `real_data/` or `logs/` | remove or measure |
| "0 drops", "0 packet drops over 173G VPC", "zero TCP packet retransmissions" | `GCP_NATIVE/network_validation/iperf_forward.json`: `retransmits: 4426` in the 10 s native run (0 at 100G and 20G); no drop counters captured during serving | remove; if kept, cite the iperf retransmit count |
| "tc/netem" | `node0_qdisc.txt`: `qdisc htb 1: root`; `node0_class.txt`: `class htb 1:10 … rate 100Gbit ceil 100Gbit burst 2400b cburst 2400b` | "tc HTB" |
| "100G cap (measured ~56.84 Gb/s)" | correct (`IPERF_VALIDATION.json`), but worth saying why: the HTB class carries a 2,400-byte `burst`/`cburst`, which at 100 Gbit makes the shaper timer-limited; ~57 Gb/s is consistent with that. The 20G class (`burst 1760b`) reaches 16.5 of 20 | add one line; it answers "why is the 100G point at 57" |
| "Traced on … AMD EPYC 9654" | no `lscpu`/CPU model anywhere in the archive; `nvidia-smi topo -m` shows 2 NUMA nodes, CPU affinity 0–95,192–287 / 96–191,288–383 (2 × 96 cores, SMT) | cite the source or drop the model name |
| "Single-Node NVLink/PCIe Base", "Local PCIe/NVLink" (KD #2, KD #7 network rows) | no NVLink on this box: `nvidia-smi topo -m` shows PIX/NODE/SYS only; d2d copy 52 GB/s = PCIe | "PCIe (no NVLink)" |

### 1.6 P1 — "NCCL POLICY INCOMPLETE" is a validator bug, not a data gap

`FINAL_VALIDATION.json` says `nccl_policy_ok: false`, `ray_nccl_scaleout_audits: 0 / expected 12`. The audit files are there: `vllm_scaleout_network_matrix/{GCP_NATIVE,GCP_CAPPED_100G,GCP_CAPPED_20G}/results/{tp4_pp2,tp8_pp2,tp4_pp4,tp16_pp1}_dist_RAY_NCCL_ENV_AUDIT.json` — 12 files, each `live_nodes: 2`, both workers with `NCCL_NET=Socket`, `NCCL_SOCKET_IFNAME==ens3`, `LD_LIBRARY_PATH=/tmp/clean_nccl_libs`, `violations: []`. `NCCL_POLICY_AUDIT.json` itself lists all 12 under `ray_worker_audits` with `ok: true` and then reports `scaleout_ray_audit_count: 0` (the validation was re-run on a Windows path, `result_root: C:\Users\...`, and the counting glob missed them). Fix the tile to "12/12 Ray NCCL env audits present and clean; FINAL_VALIDATION counter is wrong" and fix the validator.

### 1.7 P1 — Percentiles and the SLO

`combined_vllm_runs.csv` carries `p95_reliable` / `p99_reliable`: 26 of 119 runs have a reliable p95 (≥ 24 completed requests), 7 a reliable p99; 82 runs completed fewer than 10 requests. The Evidence tab states the ≥ 20 / ≥ 100 rule correctly and filters on it (good). But the capacity statements elsewhere are built on means only: the 8K knee "~0.90× offered" and the 128K knee "~0.75×" are slope inflections of mean TPOT and mean queue. At 128K 0.75× the mean TPOT is 50.6 ms and the p95 is **145.3 ms** (reliable, 24 requests); at 0.50× p95 is 95.5 ms. If the SLO is "p95 TPOT ≤ 100 ms", the 128K operating point is 0.50× (13,967 tok/s), not 0.75× (21,572 tok/s) — a 35 % capacity difference hiding in the choice of statistic. Fix: state the SLO once (the brief uses p95 TPOT ≤ 100 ms and ≥ 90 % of offered served) and show p95 next to every mean where it is reliable; grey it out where it is not.

### 1.8 P2 — Method differences between the dashboard and the PDF brief

Not errors, but the team will be asked. Put a "definitions" box on the Executive tab:

| Quantity | Dashboard | Brief | Why |
|---|---|---|---|
| Full-attention growth 128K→512K | 15.7× | 15.5× | kernel-name grouping differs (which `flash_fwd` variants count) |
| 8K vs 128K capacity gap | 18.20× req/s, 1.14× prompt tok/s at one load point | 18× req/s, 1.15× all-tokens peak, **1.8× usable** (p95 TPOT ≤ 100 ms) | one point vs peak vs SLO-conditioned |
| GPU-seconds per 1M request | from first-token time (TP4/PP1 373 GPU-s; TP4/PP4 457, +22.5 %) | from end-to-end time (374; 462, +24 %) | 32 output tokens at 10–11 ms add ~0.3 s |
| TP8 decode AllReduce penalty | 2.32× (7,040-call Self CUDA sum incl. the prefill step) | 3× (decode-only per call, 19.5 → 59.0 µs) | §1.9 |
| Chunk 4K→16K at 1M | −27.1 % in one step | −23.6 % (4K→8K) then −4.6 % (8K→16K) | same data, split |

### 1.9 P1 — KD #7 / Profiler torch panel: the 7,040-call sum is contaminated by the prefill step

`profiles_torch_single_node/tp{4,8}_8k_decode/torch/profiler_out_0.txt`: `ncclDevKernel_AllReduce_Sum_bf16_RING_LL` 7,040 calls = 128 steps × 55; the 128 steps are **1 prefill step (8,192 tokens) + 127 decode steps**. The prefill step's 55 AllReduces move 8,192 × 2,304 × 2 B = 37.7 MB each and are listed separately as the op `vllm::all_reduce` (55 calls, CUDA total 119.2 ms on TP4, 174.0 ms on TP8). Decode-only:

| | TP4 | TP8 | ratio |
|---|---|---|---|
| AllReduce kernel Self CUDA, all 7,040 calls | 251.5 ms | 583.9 ms | 2.32× (dashboard) |
| minus the 55 prefill calls | 132.3 ms | 409.9 ms | **3.10×** |
| per decode call (6,985 calls) | **18.9 µs** | **58.7 µs** | +39.8 µs |
| per decode step (55 calls) | 1.04 ms of 4.47 ms (23 %) | 3.23 ms of 6.35 ms (51 %) | |
| nccl-tests 16 KiB, no model | 19.0 µs | 37.6 µs | 1.98× |

Ranks 1–3 give 19.4–20.0 µs and 58.8–59.2 µs (4-rank means 19.5 and 58.9 µs, the numbers the brief uses). Fix the hero ("2.32× / 251.5 → 583.9 ms") to the decode-only numbers and say in one line where the other 119 / 174 ms went. The same applies to "TP8 AllReduce penalty (+332.4 ms) exceeds GEMV savings" → +277.6 ms decode-only.

## 2. Tab by tab

Format for each item: **where** → what it says now → what the data says (file) → fix.

### 2.1 Executive tab

**Header strip (all tabs)**

* P1 · "Fabric: GCP_NATIVE (measured ~173.58 Gb/s fwd, MTU 8896, 0.05ms RTT)" → 173.58 is right (`GCP_NATIVE/network_validation/IPERF_VALIDATION.json`, 16 TCP streams, 10 s). MTU and RTT: see §1.5. Fix: "173.58 Gb/s fwd / 173.59 rev (iperf3, 16 streams), MTU 1460".
* P2 · "Network Sensitivity: 100G cap (measured ~56.84 Gb/s) & 20G cap (~16.48 Gb/s)" → correct. Add "configured cap ≠ achieved: HTB burst 2400 B" (§1.5) so nobody reads 100G as 100.

**Run-validation tiles**

* P1 · "NCCL POLICY — POLICY INCOMPLETE · nccl_policy_ok=false · Ray audit missing on 12 scale-out runs" → false alarm (§1.6). Fix tile text and colour.
* P0 · "DISTRIBUTED PROFILE COVERAGE 14 / 22 COMPLETE" → 14 `.nsys-rep` sets exist; usable per-rank exports exist for 7 prefill points (6 complete, 1 at 12/16) and for no decode point (§1.3). Fix: "22 planned · 14 captured · 7 with usable exports (all prefill) · decode captures need re-export/re-capture".
* P2 · "NATIVE NETWORK EVIDENCE 173.58 Gbps · 0.05ms RTT, 0 drops, MTU 8896 verified" → keep 173.58; remove the rest (§1.5).

**Deployment Decision Map**

* P1 · Row "Short-context interactive (8K) … Interpretation [MEDIUM / CROSS-VALIDATED]: 4-GPU barrier avoids dual-NUMA PCIe bridge traversal" → §1.4. The measured 4.475 ms vs 6.350 ms is right (`tp4_context_baseline/8k_c1`, `tp8_context_baseline/8k_c1`; the four TP4 8K c1 runs span 4.467–4.487 ms, a useful noise band to quote).
* P0 · Row "Long prompt, c1 (128K) … MEMORY/KV: chunk=4096 · 90,967 MiB" → `vllm_scaleout_network_matrix/GCP_NATIVE/results/tp4_pp4_dist/tp4_pp4_dist/case_manifest.json`: `max_num_batched_tokens: 8192`. Memory 90,967 MiB = 88.83 GiB is right. Fix: chunk=8192.
* P2 · Row "1M c1 extreme prompt … ~35,005 input tok/s derived" → 1,000,000 / 28.568 s = 35,004 ✓. Say "prompt tokens ÷ TTFT".
* P1 · Row "Single-node 1M concurrency … c2 incurs queue cliff (TP4: 44.33 s queue, 181.97 ms TPOT; TP8: 35.31 s, 177.21 ms)" → numbers ✓ (`tp4_1m_concurrency_extension/1m_c2`: queue 44.34 s; `tp8_…/1m_c2`: 35.28 s). The mechanism is in the data and is worth one sentence here: the second request's first token arrives exactly one full prefill after the first (§4.2) — the queue is the single prefill slot.
* P2 · "Multi-node scale-out fabric … only +3.91 % TTFT delta at 20G vs +276.7 % on TP16" ✓ (29,683.7 / 28,568.0; 256,889.5 / 68,196.8).

**Campaign Scope / Gaps** — correct. Add "decode profiles: eager-mode only (§1.2)" to "Not established / Unresolved".

**Configuration Guidance Matrix**

* P0 · Row "Short-context throughput under TPOT SLO — TP4/PP1 (c=8..16) — Reaches 560.9 tok/s (c8) to 675.3 tok/s (c16) with sub-15 ms TPOT" → `tp4_closedloop_8k`: c8 TPOT 10.82 ms (p95 13.28), **c16 TPOT 19.20 ms (p95 22.12)**. Fix: "c8: 560.9 tok/s at 10.8 ms (p95 13.3); c16: 675.3 tok/s at 19.2 ms (p95 22.1); sub-15 ms holds to c8 only".
* P1 · Row "512K serving — TP8/PP1 single: 28.09 s TTFT (~12.0 % faster prefill than TP4)" ✓ (28,088.7 vs 31,916.2 = −12.0 %).
* P2 · Row "1M concurrent serving — c=1 … c2 already incurs 35–44 s queue" ✓.
* P2 · Row "2-node native scale-out … Pipeline latency overhead on short batch-1 decode" → the data has it: TP4/PP4 8K decode was never run in serving; the only PP decode numbers are at 128K–1M (TPOT 5.51–10.64 ms, i.e. +0.3 to +0.5 ms vs TP4/PP1). Say that or drop "short".

**TTFT vs Context / TPOT vs Context cards**

* P1 · TPOT card "INTERPRETATION: Cross-validated: 4-GPU barrier avoids NUMA bridge crossing" → §1.4.
* P2 · TTFT card "NEXT EVIDENCE: Distributed Nsight trace parsing" → the TP4/PP4 prefill traces are parsed and usable (16/16 at 128K and 512K); what is missing is a timeline (critical path), not parsing. Say "per-rank timeline".

**Capacity / SLO Envelope card** — "TP4 closed-loop c32 achieves 784.1 output tok/s" ✓; add the TPOT that comes with it (34.5 ms mean, 38.0 p95), otherwise the number reads as free capacity.

**Hardware Ceiling ↔ Application Achieved** — the chain lists "NVBandwidth / P2P: H2D · D2H · D2D" without numbers. They are in `hardware_raw/node{0,1}/nvbandwidth_*.raw.json`: H2D 56.9 GB/s, D2H 56.6 GB/s per GPU; D2D 52 GB/s (any pair); D2D latency 0.94 / 1.19 / 1.32 µs (PIX / NODE / SYS); BabelStream Copy 1.71 TB/s on GPU 0 and GPU 4 of both nodes (1,710–1,718 GB/s). Put them on the card; they are the ceilings the rest of the dashboard should be compared against (§4.3, §4.9).

**Knobs That Matter / Do Not**

* P2 · "Chunk size … decode-interference / fairness trade-off remains unresolved" → it is measured: `tp4_chunk{4k,8k,16k}/128k_c4` TPOT = 141.3 / 119.3 / 105.1 ms, TTFT 11.34 / 10.66 / 10.88 s. Larger chunks gave lower TPOT at c4 (fewer, not shorter, stalls — §4.5). Replace "unresolved" with the numbers.
* P2 · "Prefix reuse … (49.97 % hit ratio on tp4_prefix1m)" ✓ (1,998,848 / 4,000,000) — but see §2.5 L1: that ratio means one of three repeats missed.
* P2 · "Network cap … Validate on unthrottled VPC; do not deploy TP across low-BW nodes" → the data says more precisely: do not deploy **cross-node TP**; PP boundaries were fine down to 20G (−0.1 % to +3.9 % at 1M).

**Bottleneck Regime Map**

* P1 · Row "8K · c=1 to c=32 · decode dominated · BabelStream Copy ~1.72 TB/s · Memory BW / Sync · HIGH" → the memory-bandwidth classification is not supported. Active weights per token are ~3.07 B params (`model_validation.json` config: 8 of 256 routed + 1 shared expert × 26 MoE layers, dense layer 0, 7 MLA + 20 KDA layers, 163,840 × 2,304 lm_head) = 6.1 GB in bf16, 1.54 GB per GPU at TP4; at 1.71 TB/s that is a 0.90 ms floor against a 4.47 ms token. The torch profile (§4.3) puts the weight-streaming kernels (GEMV + MoE) at ~1.9 ms per step, i.e. ~0.8 TB/s ≈ 46 % of BabelStream, AllReduce at 1.04 ms, attention/state kernels at ~0.8 ms. "Kernel-bound at ~45 % of memory bandwidth, 23 % AllReduce" is what the data supports; HIGH confidence belongs to the measurement, not to "Memory BW".
* P2 · Rows 128K/512K "Prefill dominated" ✓; add the comm share inside prefill (§4.4): AllReduce ≈ 43 % of the 128K TTFT at TP4, 55 % at TP8 (nsys per rank).

**Deployment Recipe Card** — "Low-sensitivity settings: max_num_seqs (flat ~0.05 % across 4/8/16 @ 1M c4)" ✓, but say why (peak_running never exceeded 2 — §4.2); "Candidate mechanism: Decode: intra-node collective synchronisation (cross-validated)" → §1.4.

**What Not To Do** — "Do not render missing / unresolved evidence as zero" → the Scale-Out 50G/10G options render it as native (§1.1). "Do not use profiler-instrumented latency as normal benchmark latency" → the Profiler tab does exactly this for decode (§1.2).

### 2.2 Key Discoveries tab — all 10 findings

Overall: the ten findings are the strongest part of the dashboard; the measured values in every table matched the CSV. The problems are in the causal sentences, the labels, and in what is left out of findings 2, 4, 7, 8 and 10 although the data contains it.

**Signal view header** — "Measured transport: Native 173.58 · 100G 56.84 · 20G 16.48" ✓. "APPLICATION EVIDENCE: 119/126" ✓. "PROFILE EVIDENCE: 14/22 DISTRIBUTED PROFILES COMPLETE" → see §1.3 (7 usable).

**60-second map** — row 3 "Attention ~15.7× vs NCCL ~2.18×" → the 2.18× is not reproducible from the exports (see finding 3); row 7 "Same 7040 AllReduce calls … 4.48 ms vs 6.35 ms" ✓ but the 7,040 includes the prefill step (§1.9).

#### Finding 1 — Fabric Exposure (grade: keep; fix labels and add the mechanism)

Verified: all 12 TTFT deltas in the 20G table and the quick-comparison matrix (+8.01/+2.37/+1.14; +0.81/−0.19/−0.10; +14.67/+8.93/+3.91; +383.66/+333.01/+276.69; 100G: +0.13/−0.13/+1.04/+36.36) against `combined_vllm_runs.csv`. Transport table (173.58 / 56.84 / 16.48; 256M SendRecv 7.11 / 5.54 / 2.04 GB/s) ✓ (`nccl_points.csv`).

Fixes:
* P1 · "CAUSE MED-HIGH … TP16/PP1 is severely exposed because AllReduce collectives are serialised over the cross-node fabric on every layer" — right in kind; the data lets you state it quantitatively, which is what makes it a cause rather than a story: each prefill chunk does 55 AllReduces of 8,192 × 2,304 × 2 B = 37.7 MB; the 256 MiB SendRecv ceiling falls 7.11 → 2.04 GB/s (3.5×) from native to 20G and TTFT rises 68.2 → 256.9 s (3.8×). Cross-node AllReduce **latency** (16 KiB) is 227–320 µs at every cap (`225_crossnode_ar_*`), so small-message decode is cap-insensitive (TPOT 20.08 → 20.57 ms, +2.4 %) while bandwidth-bound prefill is not. One sentence, both numbers.
* P2 · "Small negative TP8/PP2 deltas (−0.10 %) … do not call them noise without replicate variance" → the replicate variance exists: identical single-node configs repeat within 0.03–0.5 % on TTFT at c1 (§4.11). −0.10 % is inside that band; say so.
* P2 · Boundary: add "iperf and the serving runs used 16 TCP streams / NCCL plain sockets (`NCCL_NET=Socket`, provider plugin disabled); a different transport changes the whole table".

#### Finding 2 — Concurrency (grade: keep; add the mechanism, fix the network label)

Verified: 1M c1/c2/c4 output tok/s 0.3415 / 0.3449 / 0.3467, TTFT 93.395 / 139.374 / 231.268 s, TPOT 10.228 / 181.974 / 267.411 ms, queue 44.340 / 134.428 s, KV 12.29 / 15.52 / 15.51 %; 8K +120.82 % / 2.74× / 1.63× / 0.027 s; 128K +10.27 % / 2.28× / 12.96× / 5.110 s; 512K +2.19 % / 2.74× / 57.36× / 53.660 s; closure 96.4 / 97.5 / 95.7 / 97.2 % — all ✓.

Fixes:
* P1 · "CAUSE: HIGH for queue closure / MEDIUM for exclusive TPOT mechanism" — the mechanism is visible in the per-request data and should be the headline: in `tp4_1m_concurrency_extension/1m_c4/1m_c4.json` the four simultaneous requests get their first token at **93.5 / 185.4 / 277.3 / 368.9 s** — one full prefill apart; at 512K (`tp4_closedloop_512k/c4`) 32.0 / 63.9 / 95.6 / 127.2 s. Prefill of long prompts is strictly serialised; `peak_running` is 2 (one prefilling + one decoding) in every 512K/1M run with c ≥ 2, and `mean TTFT(cN) ≈ TTFT(c1) × (N+1)/2` predicts the measured means within 1.3 % at 1M (§4.2). The TPOT mechanism is the same: a decoding request's tokens wait behind the other request's prefill chunks (stall median 358 ms at 1M c2, 496 ms at 512K — §4.5). Upgrade cause to HIGH with those two facts and name the knob that binds (vLLM's one-partial-prefill-at-a-time default, not `max_num_seqs`).
* P1 · network row "Single-Node NVLink/PCIe Base" → "single node, PCIe (no NVLink)".
* P2 · The 8K row's "0.027 s queue" is right but at 8K the dividend comes with its own cost: 25 % (c8) to 57 % (c32) of all decode wait is spent behind other requests' prefill chunks (§4.5). Worth a footnote; it is the same mechanism at small scale.

#### Finding 3 — Long-context Resource-Pressure Shift (grade: keep the attention conclusion; fix NCCL, denominators, and the capture window)

Recomputed from the 16 + 16 usable exports of `profiles_multi_node_native/tp4_pp4_dist/{prefill_128k,long_prefill_512k}`: flash-attention kernels 4.25 → 66.05 s (**15.6×**, dashboard 15.7× ✓), MoE 2.73 → 10.35 s (3.79× ✓), KDA 0.71 → 2.81 s (3.93× ✓), GEMM 1.53 → 7.96 s (5.21× ✓). SendRecv 4.31 → 19.29 s = **4.48×**, AllReduce 12.44 → 33.75 s = 2.71×, other NCCL (startup Broadcast) 10.70 → 15.07 s = 1.41×. We could not reproduce "NCCL Transport (Send/Recv) 2.18× (p≈0.56)" from any grouping; the shares "22.8 % → 44.8 %" come out as 11.0 → 40.4 % of all kernel time, or 15.3 → 44.5 % if the startup Broadcast is excluded, or 16.3 → 50.9 % if AllReduce is also excluded.

Fixes:
* P1 · Publish the grouping: the exact kernel-name regexes, the denominator (all ranks? node 0? rank 0?), and whether startup collectives are excluded. The stage-0 ranks carry 1.22 s of `ncclDevKernel_Broadcast_RING_LL` (weight broadcast at start-up) in a 3.0 s capture at 128K — 40 % of that rank's kernel time is not prefill. Excluding it changes every share on this page.
* P1 · "NCCL 2.18×, sub-linear" → SendRecv kernel time grows 4.5× (it includes waiting at stage boundaries) and AllReduce 2.7×; neither is sub-linear. The headline (attention grows fastest, ~N²) survives; the NCCL comparison does not.
* P2 · "Direct PyTorch/Nsight kernel breakdown" → it is nsys only, eager mode (fine for prefill; say so).
* P2 · Add the per-stage view the same exports give for free (§4.7): at 512K stage 0 holds 1 of the 7 full-attention layers and the other three hold 2 each; stage 0 spends 2.77 s of 10.7 s in SendRecv waiting. The imbalance is real but structural on this layer map — see the §4.7 correction: no contiguous split beats 7/7/7/6, so the per-stage view is for pricing the idle, not for a repartition.

#### Finding 4 — Prefix Reuse (grade: keep; replace the hit-ratio explanation)

Verified: cold 4.8965 / 32.5762 / 94.2272 s, repeat medians 0.3307 / 1.1679 / 2.6140 s, speed-ups 14.8 / 27.9 / 36.0×, counters 917,504/1,050,624 = 87.33 %, 1,048,576/2,098,177 = 49.98 %, 1,998,848/4,000,000 = 49.97 % ✓ (`combined_vllm_runs.csv` prefix columns; per-request `ttfts` in the prefix JSONs).

Fixes:
* P1 · The counter ratios are not "a range of hit rates"; they are **exact miss counts**. 128K: 8 prompts, 7 repeats all hit (7 × 131,072 = 917,504 ✓). 512K: 4 prompts, hits = 2 × 524,288 — one repeat missed. 1M: hits = 2 × 999,424 — one repeat missed. Per request (`start_times` order): 512K TTFTs 32.58 / 1.17 / 1.17 / **32.56** s — the 4th request missed, and it is the only one tokenised to **524,545** tokens (`input_lens`), the other three to 524,544: the random suffix changed a token boundary at the prefix/suffix junction. 1M TTFTs 94.23 / **93.96** / 2.61 / 2.60 s — the **2nd** request missed with identical lengths (1,000,000 ×4): a different cause (cache insertion/commit timing for a 1M-token hybrid-model prefix, or the KDA state boundary), not tokenisation. Put both facts in the table; they turn "49.97 %" from a mystery into two follow-ups (hash the tokenised prefix; log `prefix_cache` events at the engine).
* P2 · "Cold TTFT super-linear p = 1.44 … repeat near-linear p = 1.00" ✓ as a fit; note the repeat median at 1M (2.6 s) is 256 suffix tokens + 32 output tokens plus the block-match walk over 999,424 tokens — the walk is what scales linearly.

#### Finding 5 — Prompt-token Admission (grade: keep; add the SLO-conditioned row)

Verified: median achieved req/s over the 1.00/1.10/1.25× points: 8K 3.3586 (255/75.92, 280/83.66, 318/92.93 → 3.359 / 3.347 / 3.422), 128K 0.1846 (24/129.92, 24/131.39, 24/130.03); × prompt length = 27,514 and 24,196 tok/s; 18.20× and 1.14× ✓.

Fixes:
* P1 · The three "high-load" points are past saturation for both prompt classes and the latency is not comparable: at those points 128K runs at mean TPOT 167–185 ms (p95 284 ms) and TTFT 21 s, 8K at mean TPOT 62–64 ms (p95 70.5). Add a third row "same SLO (p95 TPOT ≤ 100 ms, ≥ 90 % of offered served)": 8K 0.75× = 24,977 tok/s, 128K 0.50× = 13,967 tok/s → **1.8×**. The finding's decision (size in prompt tokens/s) is unchanged; the magnitude is 1.14× at equal saturation and 1.8× at equal latency, and a capacity planner needs the second.
* P2 · Scope: the open-loop runs had `--max-concurrency 64` (8K) / `32` (128K). Above the knee the client caps in-flight requests, so the offered rate was not actually delivered (achieved 3.42 req/s at "1.25× = 5.29 offered") and server-side queue/TTFT are understated. State it as a boundary.

#### Finding 6 — Parallelism Frontier (grade: keep)

Verified: GPU-s per 1M request = TTFT × GPUs: 372.99 / 420.21 / 457.09 / 597.50 / 664.24 / 1,091.15 ✓; TP8 1M −19.9 % (74.688 vs 93.248) ✓; 8K +18.5 % (263.3 vs 222.2 ms) ✓; 128K +6.1 % ✓; 512K −12.0 % ✓.

Fixes:
* P2 · "Measured across … 6 scale-out topologies at 1M" → 4 scale-out + 2 single-node.
* P2 · GPU-seconds here use first-token time; the brief uses end-to-end (374 / 462 GPU-s, +24 %). Label the definition on the chart (§1.8).
* P2 · Add energy as a second cost axis — it is in every run (§4.6): at 1M, TP4/PP4 is also the lowest energy per token (143 J per 1K tokens vs 181 for TP4/PP1 and 247 for TP16/PP1), which strengthens the frontier claim.

#### Finding 7 — TP Decode Communication (grade: keep the decision; fix the hero numbers and the cause)

Verified: TPOT 4.475 / 6.350 (+41.9 %), 5.106 / 7.098 (+39.0 %), 7.565 / 9.455 (+25.0 %), 10.267 / 12.102 (+17.9 %) ✓; 7,040 calls and 251.5 / 583.9 ms are what `profiler_out_0.txt` says ✓ — but see §1.9.

Fixes:
* P1 · Hero "2.32× — 8K AllReduce CUDA time — 251.5 ms → 583.9 ms Self CUDA" → decode-only 132.3 → 409.9 ms (3.10×), 18.9 → 58.7 µs per call; the difference is the single 8,192-token prefill step's 55 AllReduces (119 → 174 ms). With the current number a reader computes 35.7 µs per call for TP4 and gets a 2× discrepancy with nccl-tests (19.0 µs); with the corrected number the two agree.
* P1 · "why it matters: AllReduce serialisation overhead across 8 GPUs outweighs the memory bandwidth advantage" ✓ in substance; add the budget: 55 × 58.7 µs = 3.23 ms of the 6.35 ms TP8 token (51 %) vs 1.04 ms of 4.47 ms at TP4 (23 %). The dense/MoE kernels do shrink (GEMV 171 → 127 ms, MoE 140 → 138 ms rank-local), just not by 2.2 ms.
* P1 · network row "Local PCIe/NVLink" → "PCIe, no NVLink". Any NUMA wording in the explorer page → §1.4.
* P2 · Boundary: "Causal profiler evidence strongest at 8K" — add "graphs-on torch profile, rank-local, 1 request; 128K–1M are E2E only".

#### Finding 8 — Runtime Knobs (grade: keep; name the binding limit)

Verified: chunk 4K/8K/16K TTFT 5.228 / 4.532 / 4.364 s (128K), 40.271 / 31.916 / 30.455 (512K), 122.049 / 93.248 / 88.951 (1M) ✓; max_num_seqs 87.973 / 87.931 / 87.932 (512K c4) and 232.342 / 232.364 / 232.250 (1M c4) ✓.

Fixes:
* P1 · "The configured max_num_seqs ceiling was not reached … the underlying causal constraint requires further telemetry" → the telemetry is in the same CSV: `peak_running = 2` and `peak_waiting = 3` in every 512K/1M c4 run, whatever max_num_seqs is. Two requests run (one prefilling, one decoding) because only one long prefill is admitted at a time (§4.2). The knob to test next is the partial-prefill limit (`--max-num-partial-prefills` / `--max-long-partial-prefills` / `--long-prefill-token-threshold`, default threshold 4 % of max_model_len ≈ 41.9 K tokens), with a larger `--max-num-batched-tokens` to feed it. Say that; "non-binding, cause unknown" undersells what was measured.
* P2 · Chunk size: the c4 rows exist (`tp4_chunk*/128k_c4`: TTFT 11.34 / 10.66 / 10.88 s, TPOT 141.3 / 119.3 / 105.1 ms) and show the trade-off the Executive tab calls unresolved. Add them.
* P2 · "−27.1 % 4K→16K" → say "−23.6 % 4K→8K, −4.6 % 8K→16K" so the diminishing return is visible (the brief's wording).

#### Finding 9 — Busy GPU ≠ Efficient Serving (grade: keep; fix the source label; add power)

Verified: utilisation 35.2 / 55.3 / 62.8 % (TP4/PP4; node means 36.4+34.1, 55.3+55.3, 62.8+62.8) vs 63.2 / 67.8 / 80.6 % (TP16; 64.6+61.8, 68.1+67.6, 80.7+80.5), TTFT ratios 3.75 / 2.90 / 2.39× ✓ (`gpu_node_stats_json`).

Fixes:
* P2 · "Prometheus GPU SM utilisation" → the utilisation comes from the nvidia-smi sampler (`09_metrics_sampler.py --gpu-indices …`, `gpu_util_mean_pct` in `gpu_node_stats_json`), not from vLLM's Prometheus endpoint.
* P1 · The same sampler recorded **power**, which is the signal this finding is looking for: TP16 at 1M draws 224.7 / 224.4 W per GPU (node 0 / node 1) at 80.6 % "utilisation"; TP4/PP4 draws 282 / 337 W at 62.8 %. The busier-looking layout does less work per GPU per second. Energy per token: TP4/PP4 143 J per 1K tokens, TP16 247 (§4.6). Add a power column; it makes the point without needing a profiler.
* P2 · Takeaway 4 "The captured TP16 profile contains a large aggregate GPU-kernel-work share attributed to AllReduce" ✓ (76–79 % on all 12 usable ranks at 128K, 3.9 ms per call); label it eager-mode prefill.

#### Finding 10 — KV Cache vs VRAM (grade: upgrade; the data proves a law this page says is unproven)

Verified: peak KV 12.29 / 5.91 / 2.75 / 12.18 / 5.88 / 12.13 % and peak VRAM 88.39 / 88.69 / 88.83 / 87.27 / 87.51 / 86.71 GiB ✓.

Fixes:
* P1 · Takeaway "Avoid linear arithmetic KV aggregation … those arithmetic reconstructions imply an allocator law not proven by this data" → the law is proven by this data, just not the one the sentence is about. Convert every c1 run to pool size = prompt tokens ÷ peak KV fraction (`requested_input_tokens / peak_kv_usage`): TP4/PP1 **8.14 M tokens**, TP8/PP1 **8.21 M**, TP16/PP1 **8.24 M**, TP4/PP2 **16.9 M**, TP8/PP2 **17.0 M**, TP4/PP4 **36.4 M** — consistent to ±1.5 % across 128K, 512K and 1M prompts within each layout. Doubling or quadrupling TP buys **no** KV capacity in tokens; PP multiplies it by its depth (and a little more, since each stage frees weight memory). The arithmetic the page warns against (2 × 5.91 % = 11.82 %) is exactly what the data does. Mechanism (to be confirmed from the engine's "GPU KV cache size: N tokens" start-up line, which is not in the archive): the MLA latent KV (576 values per token per full-attention layer, 8,064 B per token in bf16) is replicated on every TP rank, so TP width does not shard it; PP does.
* P1 · Decision: "Use KV % for cache pressure…" is fine but incomplete. The decision this enables: for 1M-context pools, capacity in concurrent contexts is ~8 per TP replica regardless of TP width (8.1 M ÷ 1 M); more capacity comes from PP or from more replicas, never from wider TP. Add it.
* P2 · "Headroom 95.59 GiB − peak" → `--gpu-memory-utilization 0.9` already reserves 86.0 GiB; the 6.8–8.9 GiB "headroom" is the 10 % vLLM leaves plus sampler timing, not free memory for KV. Say so.

#### Across the ten pages

* P2 · Each explorer page has "Evidence IDs" that open the drawer; the drawer's "PROFILER / RANK AGGREGATION RULE" field should state eager/graphs mode and the rank set for every profiler-backed value (findings 3, 7, 9).
* P2 · Confidence vocabulary: "CROSS-VALIDATED" is used for the NUMA cause (§1.4), which is contradicted by three hardware files. Reserve it for claims with two independent measurements that agree.

### 2.3 Scale-Up tab (TP4/PP1 ↔ TP8/PP1)

Verified: TTFT 8K 222.2 / 263.3 ms, 128K 4,532 / 4,810, 512K 31,916 / 28,089, 1M 93,248 / 74,688; TPOT 4.475 / 6.350 … 10.27 / 12.10; 8K closed-loop 188.0 / 415.2 / 560.9 / 675.3 / 784.1 tok/s; NCCL bus-bandwidth points ✓.

* P1 · TPOT card and decision row 1: "Single-NUMA 4-GPU ring avoids dual-NUMA bridge traversal (cross-validated contributor)" → §1.4 wording.
* P2 · TTFT card "Crossover ~256K–384K (DERIVED)" → it is a straight-line interpolation of two points (TP8/TP4 ratio 1.061 at 128K, 0.880 at 512K → 1.0 at ≈ 257K). Nothing was measured between 128K and 512K; say "linear interpolation, ≈ 257K; unmeasured".
* P2 · Decision row "High-throughput short context (8K): reaches 560.9 (c8) to 784.1 tok/s (c32) with healthy KV" → add TPOT 10.8 → 34.5 ms (p95 13.3 → 38.0) next to the throughput; "healthy KV" (4 %) is irrelevant to the trade-off at 8K.
* P2 · Decision row "Extreme Long Context (1M c1): TP8/PP1 (c=1 cleanest)" ✓; add that TP8 saves 18.6 s of TTFT at 1M but pays +1.8 ms per output token (12.10 vs 10.27), so the 1M c1 choice flips once outputs exceed ~10 K tokens (18.6 s ÷ 1.83 ms). The data supports the break-even; a planner can use it.
* P2 · "NCCL Bus Bandwidth TP4/PP1 vs TP8/PP1" chart → label the sizes; the decode-relevant point is 16 KiB (latency 19.0 vs 37.6 µs), the prefill-relevant one is 64 MiB (busbw 25.2 vs 24.1–25.1 GB/s). The chart as rendered invites comparing bus bandwidth, which is nearly equal, when the gap that matters is latency.
* P2 · Scope box "TP4/PP2 is not part of the single-node matrix" ✓ (it is dual-node, 4 GPUs per node).

### 2.4 Scale-Out tab — dropdown by dropdown

**Network dropdown (5 options)**

| Option | What it renders now | What it should render |
|---|---|---|
| GCP_NATIVE (173.6 Gbps Uncapped) | native data ✓ (12 cells × 7 metrics verified) | as is; label "iperf 173.58 Gb/s, 16 streams, MTU 1460" |
| 100G Cap (56.8 Gbps tc/netem) | 100G data ✓ (12 × 7 verified) | "tc HTB"; add "achieved 56.8 of 100 (HTB burst 2400 B)" |
| 20G Cap (16.5 Gbps tc/netem) | 20G data ✓ (12 × 7 verified) | "tc HTB" |
| 50G Cap (HW Qualified 33.0 Gbps) | **native data under a GCP_CAPPED_50G title; native evidence IDs** | application cells `NOT_RUN`; hardware panel: iperf 33.0 / 34.2 Gb/s, SendRecv 256M 4.09 GB/s, cross-node 16 KiB AllReduce 223–297 µs |
| 10G Cap (HW Qualified 9.0 Gbps) | **native data under a GCP_CAPPED_10G title** | application cells `NOT_RUN`; hardware: iperf 9.0 / 9.0, SendRecv 1.11 GB/s, AllReduce 232–319 µs |

**Context dropdown (ALL / 128K / 512K / 1M)** — values correct for all three measured networks. Two wording fixes: the "Multi-Node Context Scaling Curves" card says "TTFT scales super-linearly: 128K→512K ~6.0×, 512K→1M ~2.8× across all topologies"; measured ratios are TP4/PP4 5.98× / 2.80×, TP4/PP2 6.78× / 2.93×, TP8/PP2 5.59× / 2.66×, TP16/PP1 **4.61× / 2.30×**. Say "4.6–6.8× and 2.3–2.9×; TP16 grows slowest because its 128K point is already communication-bound". The ALL view's observation card ("selected context / confidence required / workload scoped") is placeholder text — fill it or hide it.

**Metric dropdown (7 options)**

| Metric | Check | Fix |
|---|---|---|
| TTFT (s) | 36 cells ✓ | — |
| TPOT (ms) | 36 cells ✓ | add "c1: no batching, decode = pure per-token cost" |
| Output tok/s | 36 cells ✓ | these are c1 single-stream rates (0.46–31 tok/s); say so, otherwise they read as capacity |
| Request tok/s | 36 cells ✓ | same |
| Peak KV % | 36 cells ✓ | add the derived pool in tokens (8.2 M / 16.9–17.0 M / 36.4 M — §4.1); the % alone hides that TP16 and TP4/PP1 have the same capacity |
| Mean queue (ms) | 36 cells ✓ (0.012–0.038 ms) | these are c1 runs: the queue was never exercised; label "c1 — not a load measurement" |
| Preemptions | all 0 ✓ | label "0 observed at c1; not exercised" |

**Decision Matrix (Topology × Context)** — numbers ✓. The VERDICT column says "VIABLE" for 9 cells and "lowest measured TTFT" for 3; nothing defines viable. Make it SLO-driven (e.g. TTFT ≤ 30 s and TPOT ≤ 100 ms → TP4/PP4 only at 1M) or rename the column "measured" and drop the word.

**Native 1M Scale-Out Matrix** — ✓ (52.53 / 41.51 / 28.57 / 68.20 s). "~35,005 input tok/s derived ingestion rate" → say "prompt tokens ÷ TTFT".

**Native Network Verification table**

* P1 · "Interface / MTU — ens4 / MTU 8896 (Jumbo) — VALIDATED — native validation" → `NETWORK_MODE.json` iface ens3; `node0_link.txt` mtu 1460. Change both and the status.
* P2 · "iperf 173.58 fwd (smoke ~173.60 / ~173.59 rev)" ✓.
* P2 · "NCCL SendRecv 64M 7.24 · 128M 6.98 · 256M 7.11 GB/s" ✓.
* P2 · "Local TP4/TP8 & Cross-Node TP16 — 25.95 GB/s (TP4) / 25.40 GB/s (TP8) PCIe/NUMA BusBW" → TP4 256M busbw is 26.09 / 25.95 / 25.95, TP8 is 25.04 / 24.95 / 24.95 (`nccl_points.csv`); 25.40 is not a measured point. Also the row title promises TP16 and gives none: cross-node TP16 16 KiB AllReduce is 290 µs native (vs 37.6 µs TP8 in-node, 19.0 µs TP4) — that is the number to show.

**Placement panel** — generic boxes. The actual mapping is in the archive: `node0_gpu_inventory.csv` (index → UUID → PCI bus: 05/06/0A/0B on socket 0, 84/85/89/8A on socket 1), `nvidia-smi topo -m` in every `PROFILE_CASE_MANIFEST.json`, and worker hostnames/pids in `*_RAY_NCCL_ENV_AUDIT.json`. For TP4/PP2 the manifests force 4 visible GPUs per node (`ray_gpus_per_node: 4`, `physical_gpu_indices_each_node: [0,1,2,3]`): both stages sit on socket 0 of their node. Render that.

**Topology × Network Sensitivity Heatmap** — all 24 deltas ✓. Two label issues: "HIGH NETWORK RESILIENCE" on TP4/PP4 at 128K is +14.67 % at 20G (and +2.97 % at 100G); the class names should come from a threshold rule printed under the table (e.g. < 5 % / 5–20 % / > 20 %), not from prose. "Key Finding: … incurring minimal latency degradation (< 4 % @ 1M on 20G cap)" → "< 4 % at 1M, up to 15 % at 128K".

**Network Architecture: Configured vs Measured Transport** — "RTT / MTU 0.05ms / 8896" on five rows → §1.5. "tc/netem" → tc HTB. "Transport Layer Audit: All multi-node runs used TCP/IP … MTU 8896 jumbo frames" → MTU 1460. CAPPED_50G/10G rows "HW QUALIFIED / RUNS DEFERRED" ✓ — keep exactly this wording in the application cells when those options are selected (§1.1).

**Scale-Out Decision Output** — row 512K "0 packet drops over 173G VPC" → not measured (§1.5). Row 1M "Suspected mechanism [MEDIUM]: cross-node tensor communication latency on TP16/PP1" → the mechanism is bandwidth, not latency, for prefill: 55 AllReduces of 37.7 MB per 8K chunk against a 7.11 GB/s socket ceiling (§4.4); latency (290 µs per call) is what hurts TP16 decode (55 × 0.29 ms = 16 ms of the 20.1 ms token). Both numbers are in `nccl_points.csv`.

### 2.5 Long Context tab

Verified: the 1M waterfall (93.25 / 139.37 / 231.27 s; 10.23 / 181.97 / 267.41 ms; 0 / 44.34 / 134.43 s; 12.29 / 15.52 / 15.51 %; TP8 74.89 / 111.74 / 184.88; 12.05 / 177.21 / 259.50; 35.28 / 106.91 s; 12.18 / 15.27 / 15.37 %) ✓; prefix table ✓; "0 timeouts · 0 preemptions" ✓ (`failed = 0`, `preemptions_delta = 0` on all 119 rows); distributed 1M cells ✓.

* P1 · L1 · "Hit ratios are ~87 % at 128K and ~50 % at 512K/1M (reflecting the cold-first-then-warm measurement pattern)" → wrong explanation. With 1 cold + 7 repeats the pattern gives 87.5 % (measured 87.33 % — all repeats hit). With 1 cold + 3 repeats it gives 75 %; the measured 49.98 / 49.97 % means **one of the three repeats missed** at 512K and at 1M. Which one and the likely cause are in §2.2 finding 4. Fix the sentence and add the per-request TTFTs.
* P1 · L2 · "GUARDED NOT_RUN — Host CPU Offload Disabled … intentionally disabled as all tested models and KV states operated entirely within onboard GPU memory without requiring host tiering" → `tp4_native_offload_pressure/case_manifest.json` describes a probe that was designed to force offload (`offload_gib_total_across_tp: 32`, purpose "deliberately pressure GPU KV and observe native CPU KV offload"); it has an empty `benchmarks` list and no gate/skip reason. Say "NOT_RUN, no reason recorded"; do not supply one.
* P2 · L3 · "FP8 KV: GUARDED NOT_RUN / backend acceptance not validated" ✓ (`coverage.csv`: 4 rows NOT_RUN, `has_gate False`, no `gate_reason`). Same as above: "no reason recorded".
* P2 · L4 · Waterfall "Critical Architectural Discovery: … latency degradation is overwhelmingly prefill-compute and scheduling-queue bound" → add the mechanism and the per-request ladder (§4.2); also the TP8 c4 run shows the scheduler did not keep FIFO (first tokens at 75.0 / 148.3 / **294.7 / 221.6** s — request 4 ran before request 3).
* P2 · L5 · "IS LATENCY USABLE? 28.57 s TTFT" sits in the single-node section but is the TP4/PP4 distributed number. Label it.
* P2 · L6 · "1M Serving Decision … c1 Cleanest measured point" ✓; the first regime where concurrency stops paying is c2 at ≥ 512K and the reason is serial prefill, so the admission signal is "one long prefill in flight", not a user count. Say that.

### 2.6 Scheduler & KV tab

* P1 · K1 · "Candidate knee: 8K ~0.90× (3.811 RPS offered, 3.302 achieved; queue 0.182 s, TPOT 60.86 ms) · 128K ~0.75× (0.171 RPS; queue 1.94 s, TPOT 50.57 ms)" → numbers ✓, but "heuristic: slope inflection" is not a serving criterion. With p95 TPOT ≤ 100 ms the 128K point is 0.50× (p95 95.5 ms; at 0.75× p95 is 145.3 ms) and the 8K point is 0.75× (p95 62.2 ms; at 0.90× p95 70.2 ms is still fine but only 87 % of offered load was served). State the SLO, add p95, and show both knees (§1.7).
* P1 · K2 · The open-loop runs are capped by the client: `--max-concurrency 64` (8K) and `32` (128K). Above saturation the achieved rate flattens at 3.30–3.42 req/s (8K) and 0.183–0.185 (128K) while the "offered" column keeps rising; requests queue in the client where TTFT is not measured, so the server queue (0.25 s max at 8K) and TTFT at ≥ 1.0× understate reality — which is also why 8K TTFT is non-monotonic (979 → 784 → 826 ms at 1.0 / 1.1 / 1.25×). Say "beyond the knee this is a closed loop at 64 / 32 in flight".
* P1 · K3 · "Scale-Out Scheduler Discovery: Pipeline Parallelism is consistent with distributing active KV allocation across 4 sequential stages (exact allocator sharding is not directly measured)" → the pool in tokens is measurable from the same rows and is the clean statement: 8.1–8.2 M tokens for TP4/PP1, TP8/PP1 and TP16/PP1 alike; 16.9–17.0 M for PP2; 36.4 M for PP4 (§4.1). Replace the hedge with the numbers.
* P1 · K4 · "max_num_seqs Sensitivity … non-binding" → name the binding limit: `peak_running = 2`, `peak_waiting = 3` at 512K/1M c4 (§4.2). The scheduler admitted one long prefill at a time; `max_num_seqs` 4/8/16 could not matter.
* P2 · K5 · Offload box "intentionally disabled …" → same fix as 2.5 L2.
* P2 · K6 · "Queue mean 0.00001 s / 0.00002 s" in the scale-out ledger vs "0.012 ms" in the Scale-Out matrix for the same runs — pick one unit and precision; and mark these as c1 (queue not exercised).
* P2 · K7 · "LEADING MEASURED OPERATING POINT 8K: c≤8 closed-loop (TPOT 10.82 ms, queue 0.19 s)" ✓ (`tp4_closedloop_8k/c8`: queue_mean 0.190 s). Add p95 13.3 ms.
* P2 · K8 · Runtime semantics table — add "partial prefills in flight" as a row; it is the state variable that explained the long-context results.
* P2 · K9 · "Peak KV usage vs context / concurrency" chart — add a secondary axis in tokens (pool × %) so 12.3 % reads as "1 M of 8.1 M".

### 2.7 Profiler tab

Verified against `profiles_single_node/*/cuda_gpu_kern_sum.csv`, `cuda_api_sum.csv`, the 16-rank exports and `profiles_torch_single_node/*/torch/profiler_out_0.txt`: 86.3 % / 41.62 s / 112,640 / 369.5 µs (tp4_decode); 46.0 % / 8.23 s / 5,060 / 1,626.6 µs and flash 21.5 % / 616 / 6,243 µs (tp4_prefill); 89.1 % / 446.5 µs (tp8_decode); flash 4,262 µs (tp8_prefill); cudaEventSynchronize 3.64 s (32.8 %), cudaLaunchKernel 3.47 s / 888,504 / 3.9 µs, cudaMemcpyAsync 710 ms / 90,224; torch 7,040 calls, 251.5 / 583.9 ms, fused_moe 120.0 / 117.7 ms; TP16 128K AllReduce share 76.3–79.5 % (mean 77.6 %) ✓. Kernel dispersion tile (14–18,090 µs AllReduce; flash 1,164–9,151 µs; KDA 218/228/248 µs; norms < 35 µs) ✓.

What to fix:

* P0 · P1 · Tab-wide banner: all nsys captures are `--enforce-eager` (§1.2). Every decode share/latency on this tab is an eager artefact. Remove "CUDA Graph capture is a candidate follow-up optimisation" (host-overhead card and takeaways row 5) — serving already uses graphs; that is why serving TPOT is 4.47 ms and the profiled step 30.46 ms.
* P0 · P2 · Hero "ALLREDUCE BARRIER LATENCY 369.5 µs → 5,739 µs · TP4 PCIe 369.5 | TP8 NUMA 446.5 | TP16 TCP 5.74 ms" → 369.5 / 446.5 are eager decode (graphs-on decode: 18.9 / 58.7 µs, §1.9). 5,739 µs is not in any export: TP16 128K prefill gives 3,833–3,984 µs per call (mean 3,911) across the 12 usable ranks; the single usable 512K rank gives 4,471 µs. Replace the tile with "decode AllReduce per call, graphs on: TP4 18.9 µs · TP8 58.7 µs (torch); prefill AllReduce per 37.7 MB call: TP4 1.6–2.0 ms · TP8 2.0 ms · TP16 cross-node 3.9 ms (nsys)".
* P1 · P3 · Hero "FLASHATTENTION FWD 6.24 → 4.26 ms: 8 GPUs cut attention duration by −31.7 %" → per-kernel duration with half the heads per GPU; total attention kernel time across ranks rose 4.20 → 5.72 s and the 128K TTFT did not improve (4,532 → 4,810 ms in serving). Either drop the tile or caption it "per-kernel; no TTFT gain at 128K".
* P1 · P4 · Hero "DECODE GEMV 156.1 → 89.2 ms (−42.9 %)" → both numbers are the sum of the top three `gemvx` rows only; all `gemvx` rows give 171.2 → 126.5 ms (−26 %). Use the full sum or name the subset.
* P1 · P5 · Hero "CUDA HOST LAUNCH & SYNC 3.9 µs/launch, 888,504 launches, 3.64 s EventSync" → eager-mode numbers; caption accordingly or move to a "capture diagnostics" box.
* P1 · P6 · Kernel-composition card "AllReduce consumes 86.3 % (TP4) to 89.1 % (TP8) of aggregate GPU kernel work" → eager; the graphs-on budget is 23 % / 51 % of the decode step (§4.3). "PREFILL CONTRAST: Attention (23.5 %) + MoE (11.6 %)" ✓ (eager prefill is representative). "TP16/PP1 spends 76.2 % … all-rank mean 77.6 %" ✓ (12 of 16 ranks; say so). "TP4/PP4 P2P SendRecv represents 8.3 % of captured stage work" → that is one stage-0 rank at 128K; the four ranks of the last stage spend 17–22 % in SendRecv (waiting on upstream), and at 512K stage 0 spends 26 % (blocked sends). Show per stage (§4.7).
* P1 · P7 · Torch panel "Grouping Recipe: Attn (paged_attention_v2), MoE (fused_moe), AllReduce (nccl:all_reduce), GEMV (addmm/cublasGemv), KDA (recurrent_state), Norm (rms_norm)" → none of `paged_attention_v2`, `addmm`, `recurrent_state` appears in these profiles; the kernels are `_fwd_grouped_kernel_stage1/2`, `fusedKimiK3MLADecode…`, `gemvx`, `fused_recurrent_kda_packed_decode_kernel`, `_causal_conv1d_update_kernel`. Publish the regexes actually used. "TP8 AllReduce penalty (+332.4 ms)" → +277.6 ms decode-only (§1.9). "NUMA CROSSING: 82.9 µs vs 35.7 µs" → 58.7 vs 18.9 µs decode-only, and the cause is not established (§1.4). "Fused MoE kernel time is identical (120 vs 118 ms)" ✓. "PRESCRIPTION: co-locating TP4 within a single NUMA socket" → the TP4 runs already were on one socket (GPUs 0–3); the open test is CPU pinning of the TP8 ranks, not GPU placement.
* P2 · P8 · Resource-Pressure ledger: row "Host CPU Launch & Event Sync — 6.1 % 1.10 s (prefill) — 3.0 % 3.64 s (decode)" mixes CPU API time into a GPU-share table (3.64 s is 32.8 % of API time, not 3.0 % of GPU work). Move it out. Row "TP AllReduce Sync 46.0 % … TP8 incurs +20.8 % cross-NUMA socket traversal overhead" → eager decode ratio; cause unproven.
* P2 · P9 · Top-15 table: values ✓; add a "mode" column (eager) and for the `ncclDevKernel_SendRecv tp4_pp4_dist 128K (Stage 0)` row say which worker (54 instances, 4.68 ms avg = one of the four stage-0 ranks; the stage-3 ranks show 6.4–7.2 ms avg).
* P0 · P10 · Coverage & Validation Matrix: statuses from `.nsys-rep` presence; add usable-export counts (§1.3 table) and delete the finding text in rows with 0–2 usable ranks (tp4_pp4_decode_8k, tp8_pp2_decode_8k, tp16_pp1_decode_8k, tp4_pp2_decode_8k, tp4_pp2_decode_8k_c8, tp16_pp1_prefill_512k). Specific unsupported cells: "zero TCP drops across native VPC fabric", "zero TCP packet retransmissions", "Cross-NUMA 8-GPU ring barrier adds 20.8 % latency over TP4, but zero cross-node TP traffic" (that number is from the single-node eager capture, not from tp8_pp2), "Peak memory remains flat at 88.84 GiB" (telemetry, not the profile). The summary row "Bandwidth-Capped Profiles — Deferred" contradicts the three COMPLETE capped-100G rows below it.
* P1 · P11 · Takeaways table: row 2 "At 128K, TP8 is slightly slower than TP4 (5.59 s vs 5.37 s)" → no such values; 4.81 s vs 4.53 s (serving) or 4.66 vs 4.80 s (eager profile, where TP8 was faster). Row 1 "AllReduce ring barrier surges from 369.5 µs to 446.5 µs (+20.8 %) which cancels out GEMV acceleration" → eager; graphs-on it is +39.8 µs per call (3.1×), 2.2 ms per token. Row 3 "27 hidden layers (20 KDA, 7 full attention)" ✓ (`model_validation.json`). Row 5 "CUDA Graph capture is a candidate…" → remove.
* P2 · P12 · Provenance header "AMD EPYC 9654, MTU 8896 Jumbo VPC" → §1.5.
* P2 · P13 · Scenario chips (6): the "All Scenarios" view compares eager decode with eager prefill side by side; after the banner that is fine. Add the two torch profiles as a seventh chip ("TP4/TP8 8K decode, graphs on") since they are the only decode captures that reflect serving.

### 2.8 Evidence tab

Verified: 126 rows (95 native + 24 capped + 7 guarded) ✓; filter counts p99 valid 7, p95 valid 26, p95 not valid 93, not run 7 ✓ (`p95_reliable`/`p99_reliable` columns); scope / class / topology options match `coverage.csv` (`scope`, `network_provenance`, `tp`/`pp`).

* P2 · E1 · The status contract lists NOT_CAPTURED but the ledger shows 1 NOT_CAPTURED row while the Profiler matrix shows 5 NOT_CAPTURED + 3 INCOMPLETE profile points. Either the ledger carries profile points (then 22 rows) or it does not (then 0). Reconcile.
* P2 · E2 · "Authoritative Source Hierarchy: FINAL_VALIDATION.json → run integrity / publication gate" → note its two known defects: `ray_nccl_scaleout_audits: 0` (files exist, §1.6) and `result_root` pointing at a Windows copy, so the gate was computed off-box.
* P2 · E3 · Columns worth adding (all in the files already): `warmups` (0 / 1 / 2 on 77 / 26 / 16 runs), `prompts_requested`, `server_ready − server_start` (model load, §4.12), sampler coverage (`metric_samples`), and for profiler rows "usable exports / workers".
* P2 · E4 · Reliability filter is right; add the same gate to every p95 shown on other tabs (§1.7).
* P2 · E5 · The config key definition lists DP/EP/rank placement — none of the 44 server commands in the case manifests carries a data-parallel or expert-parallel flag (TP/PP only); say "DP/EP = 1 in this campaign" rather than leaving the fields "UNKNOWN".

## 3. What we checked and found correct (do not re-verify)

| Area | Checked | Result |
|---|---|---|
| Scale-Out explorer | 3 networks × 4 layouts × 3 contexts × 7 metrics (TTFT, TPOT, out tok/s, req/s, KV %, queue, preemptions) vs `combined_vllm_runs.csv` | 252 / 252 match (≤ 0.5 % rounding) |
| Scale-Out heatmap | 24 deltas (100G and 20G vs native) | all match to the second decimal |
| KD #1 | 12 TTFT deltas + 4 native/100G/20G rows + transport table | all match |
| KD #2 | 1M c1/c2/c4 (TPS, TTFT, TPOT, queue, KV), 8K/128K/512K ratios, closure % | all match |
| KD #3 | growth factors flash 15.6×, MoE 3.79×, KDA 3.93×, GEMM 5.21× recomputed from 32 rank exports | match; NCCL 2.18× and the shares do not reproduce (§2.2) |
| KD #4 | cold/repeat TTFTs, speed-ups, counter ratios | all match |
| KD #5 | median req/s, token rates, 18.20× / 1.14× | all match |
| KD #6 | 6 GPU-s values, −19.9 %, +18.5 %, +6.1 %, −12.0 % | all match |
| KD #7 | 4 TPOT pairs, 7,040 calls, 251.5 / 583.9 ms | match (interpretation issue, §1.9) |
| KD #8 | 9 chunk TTFTs, 6 max_num_seqs TTFTs | all match |
| KD #9 | 6 utilisation values, 3 TTFT ratios | all match |
| KD #10 | 6 KV %, 6 peak-VRAM values | all match |
| Executive | 173.58 / 56.84 / 16.48 Gb/s; 119/126; 95 + 24 + 7; 80/87; 12/12; TPOT 4.475/6.350; TTFT 1,710/4,532; 10.22 / 28.09 / 31.92 s; 28.57 s; 35,005 tok/s; 1.107 tok/s; 44.33 / 35.31 s queue; 181.97 / 177.21 ms; +3.91 / +276.7 %; 88.95 vs 122.05 s; 232.3 s; 94.23 → 2.61 s; 49.97 %; 134.43 / 107.01 s; BabelStream 1.72 / 1.46 TB/s; 0.126 % KV; 86.69 / 88.84 GiB | all match |
| Scale-Up | 8 TTFT, 8 TPOT, 5 throughput points; 12.0 % / 19.9 % / 29.5 %; 35.3 s | all match |
| Long Context | 1M waterfall (18 values), prefix table (12 values), "0 failed / 0 preemptions" | all match |
| Scheduler & KV | both knees (6 values), 8K closed-loop c8 (10.82 ms, 0.190 s), 12 scale-out KV % and queue values, 0.254 s max queue, ~64 ms TPOT plateau, < 8.1 % KV | all match |
| Profiler | 86.3 % / 41.62 s / 112,640 / 369.5 µs; 46.0 % / 8.23 s / 5,060 / 1,626.6 µs; 21.5 % / 616 / 6,243 µs; 89.1 % / 446.5 µs; 4,262 µs; 3.64 s / 32.8 %; 3.47 s / 888,504 / 3.9 µs; 710 ms / 90,224; 7,040 / 251.5 / 583.9 ms; 120 / 118 ms MoE; 77.6 % TP16; dispersion min/avg/max (4 kernels); top-15 table (15 rows) | all match (interpretation issues in §2.7) |
| Evidence | 126 rows; filter counts 7 / 26 / 93 / 7; scope and class counts | all match |
| Hardware | iperf 10 values; NCCL 16K–256M TP4/TP8 (36 points); SendRecv 30 points; cross-node AR 15 points; nvbandwidth H2D/D2H/D2D/latency; BabelStream 40 rows | consistent with `hardware_processed/*` and raw JSON |
| Repeatability | 8 pairs of identical configs | TTFT within 0.03–3.9 %, TPOT within 0.02–2.1 % (§4.11) |

## 4. The gold mine — what the data already proves but nobody shows

Each item: what the files say (numbers recomputed here), how it was computed, the decision it changes, the caveat, and where it belongs. Items 4.1–4.5 answer Anurag's "cause vs effect vs correlation" question directly: they are mechanisms with arithmetic, not comparisons.

### 4.1 KV capacity is 8.1 M tokens per TP replica, whatever the TP width — PP is what multiplies it

**Computation.** For every single-request run, pool size in tokens = `requested_input_tokens / peak_kv_usage` (`combined_vllm_runs.csv`). Within each layout the three prompt lengths agree to ±1.5 %, which is what you expect if the gauge is linear in tokens.

| Layout | GPUs | Pool (M tokens) at 128K / 512K / 1M | Concurrent 1M contexts that fit |
|---|---|---|---|
| TP4/PP1 | 4 | 8.02 / 8.12 / 8.14 | 8 |
| TP8/PP1 | 8 | 8.15 / 8.19 / 8.21 | 8 |
| TP16/PP1 | 16 | 8.22 / 8.24 / 8.24 | 8 |
| TP4/PP2 | 8 | 16.7 / 16.9 / 16.9 | 16 |
| TP8/PP2 | 16 | 16.9 / 17.0 / 17.0 | 17 |
| TP4/PP4 | 16 | 35.9 / 36.4 / 36.4 | 36 |

**Why.** Going from 4 to 16 GPUs with TP alone adds 1.3 % of KV capacity; adding PP stages multiplies it (2.08× for PP2, 4.47× for PP4). The arithmetic is consistent with the MLA latent KV (kv_lora_rank 512 + rope 64 = 576 values × 7 full-attention layers = 8,064 B per token in bf16, `model_validation.json`) being **replicated on every TP rank** (one latent head, nothing to shard), while PP gives each stage only its own layers. At 8,064 B per token per rank, 8.14 M tokens = 61 GiB per GPU — about what is left of the 86 GiB budget (0.9 × 95.6) after 22.9 GiB of weights at TP4.

**Decision.** For 1M-context pools, capacity in concurrent contexts is ~8 per TP replica regardless of TP width; buy capacity with PP (or replicas), latency with the TP4/PP4 frontier. It also explains why KD #10's "2 × 5.91 % = 11.82 %" works: it is not a coincidence.

**Caveat / next check.** The engine prints "GPU KV cache size: N tokens" and "Maximum concurrency for 1,048,576 tokens per request" at start-up; the server stdout is not in the archive. Add it to the ledger; one line per run confirms the law directly. The TP8 pool "should" be ~15 % larger than TP4 by free memory and is not — worth asking the engine why (hybrid allocator page sizing for the KDA state is the suspect).

**Where.** KD #10 (replace the "unproven allocator law" takeaway), Scale-Out KV metric, Scheduler & KV ledger.

### 4.2 Long-prompt prefill is strictly serialised — the per-request timeline is the cause behind findings 2 and 8

**Computation.** Per-request `ttfts` and `start_times` from the benchmark JSONs:

| Run | First-token times of the simultaneous requests (s) | TTFT(c1) |
|---|---|---|
| `tp4_1m_concurrency_extension/1m_c4` (4 × 1M at once) | 93.5 · 185.4 · 277.3 · 368.9 | 93.4 |
| `tp8_1m_concurrency_extension/1m_c4` | 75.0 · 148.3 · **294.7 · 221.6** (request 4 before 3) | 74.9 |
| `tp4_closedloop_512k/c4` (8 prompts, 4 in flight) | 32.0 · 63.9 · 95.6 · 127.2, then 96.2 · 95.4 · 95.4 · 95.3 | 32.0 |
| `tp4_closedloop_512k/c2` | 32.0 · 63.7, then 32.7 · 32.7 | 32.0 |

Each first token arrives exactly one full prefill after the previous one; nothing overlaps. Hence `mean TTFT(cN) = TTFT(c1) × (N+1)/2`: predicted 233.4 / 187.2 / 140.0 / 112.3 s vs measured 231.3 / 184.9 / 139.4 / 111.7 s at 1M (TP4 c4, TP8 c4, TP4 c2, TP8 c2) — within 1.3 %. `peak_running = 2` (one prefilling, one decoding) and `peak_waiting = N − 1` in every 512K/1M run with c ≥ 2, whatever `max_num_seqs` was. At 128K the law holds loosely (c4: 10.3 vs 11.3 s predicted) because 128K prompts are 16 chunks and a second prefill can start between them; at 8K it does not apply (prompt < one chunk budget).

**Why.** The "queue" in KD #2 is the wait for the single prefill slot: vLLM's default scheduler admits one partial prefill at a time (`max_num_partial_prefills = 1`; prompts above `long_prefill_token_threshold` ≈ 4 % of `max_model_len` ≈ 41.9 K tokens are "long" and limited by `max_long_partial_prefills = 1`). That is also why `max_num_seqs` 4/8/16 changed nothing (KD #8): two requests were ever running.

**Decision.** The admission signal for ≥ 128K traffic is "long prefills in flight", not request count; and there is a knob to test before buying hardware: `--max-num-partial-prefills 2 --max-long-partial-prefills 2` with `--max-num-batched-tokens 16384`, rerun 1M c2 and 512K c4. If the serialisation is a policy, c2 TTFT should fall from 139 s toward ~100 s; if it is memory/compute, it will not.

**Caveat.** The scheduler-parameter explanation is inferred from the timeline and from vLLM defaults; the engine's scheduler log would confirm it in one run.

**Where.** KD #2 (cause), KD #8 (binding limit), Long Context waterfall, Scheduler semantics.

### 4.3 Where the 4.47 ms decode token goes (graphs on) — and why "memory-bandwidth bound" is wrong at c1

**Computation.** `profiles_torch_single_node/tp4_8k_decode/torch/profiler_out_0.txt` (rank 0, graphs on, 1 prefill + 127 decode steps). Kernel rows only (Self CPU = 0), prefill-only rows removed (`vllm::all_reduce` 119.2 ms, `flash_fwd` 5.8 ms, `chunk_gated_delta` 8.8 ms, prefill GEMMs ≈ 54 ms, prefill MoE share ≈ 30 ms), divided by 127 steps:

| Component (TP4, 8K, c1) | ms per token | share of 4.47 ms | TP8 (of 6.35 ms) |
|---|---|---|---|
| AllReduce (55 calls × 18.9 µs) | 1.04 | 23 % | 3.23 (51 %) |
| Dense GEMV / GEMM (projections, lm_head) | ≈ 1.07 | 24 % | ≈ 0.78 |
| MoE (routing + 8 + 1 experts, 52 kernels) | ≈ 0.87 | 19 % | ≈ 0.85 |
| Attention: MLA decode (7 layers) + KDA recurrent/conv (20 layers) | ≈ 0.68 + 0.16 | 19 % | ≈ 0.65 + 0.15 |
| Norms, elementwise, sampler | ≈ 0.5 | 11 % | ≈ 0.5 |
| Unaccounted (launch gaps between piecewise graphs) | ≈ 0.15 | 3 % | ≈ 0.2 |

Weights streamed per token: ~3.07 B active parameters (`model_validation.json`: 8 of 256 routed + 1 shared expert × 26 MoE layers, dense layer 0, 7 MLA + 20 KDA layers, 163,840 × 2,304 lm_head) = 6.1 GB bf16 → 1.54 GB per GPU at TP4. The GEMV + MoE kernels take ≈ 1.94 ms for that → **≈ 0.79 TB/s, 46 % of the 1.71 TB/s BabelStream copy rate**. A pure bandwidth floor would be 0.90 ms.

**Why.** The Executive "Bottleneck Regime Map" calls 8K decode "Memory BW / Sync — HIGH". At c1 it is kernel-time bound with the weight-streaming kernels at under half of memory bandwidth, plus a 23 % AllReduce tax (51 % at TP8). Those are three different optimisation targets (kernel efficiency of small-M GEMV/MoE, AllReduce fusion/overlap, and nothing about HBM), and the eager nsys numbers hide all three behind "86 % AllReduce".

**Caveat.** ±10 %: per-step attribution from aggregate tables; the profiler slowed the step 1.41× (6.31 vs 4.47 ms) on the CPU side, kernel durations are unaffected. A torch timeline export (`--profile` with trace) would make it exact.

**Scope (v1.2).** "Not memory-bound" is a statement about the 8K single request. At long context the token *is* memory-bound — on its KV cache, not its weights: a 1M decode token must read the whole replicated latent cache, 1M × 8,064 B = 8.1 GB per rank, 4.7 ms at the BabelStream 1.72 TB/s; the measured growth 8K → 1M is 5.8 ms on TP4, 5.8 on TP8 and 5.8 on TP16 (4.47 → 10.27, 6.35 → 12.10, 14.94 → 20.08 ms), identical across widths because the latent is replicated (§4.1). Wider TP cannot shorten it; fewer bytes per token can — the FP8 KV probe (NOT_RUN) predicts 10.3 → 7.9 ms at 1M on TP4 if the attention backend supports it. See §4.17.

**Where.** Profiler tab (replace the decode composition card), Executive bottleneck map, KD #7.

### 4.4 Prefill communication share by prompt length — the number behind "comm isn't the HW bottleneck"

**Computation.** An 8K prefill chunk does 55 AllReduces of 8,192 × 2,304 × 2 B = 37.7 MB. nccl-tests (`nccl_points.csv`, TP4 native): 19.0 µs at 16 KiB, 17.4 GB/s algorithm bandwidth at 256 MiB → α-β time for 37.7 MB ≈ 2.19 ms. In the eager prefill capture (`tp4_prefill`) each rank made 1,265 AllReduce calls = 16 chunks × 55 + 7 decode steps × 55, averaging 1.63 ms; taking the 385 small decode-step calls out at their eager cost (~0.37 ms) leaves 1.92 s over the 880 prefill-chunk calls = **2.18 ms per call — the α-β estimate to within 1 %**; the 16 TP4/PP4 ranks at 512K show 1.9–2.2 ms per call. Per 8K chunk: 55 × 2.18 ms ≈ **120 ms**. Chunk compute grows with position (attention over the prefix); the AllReduce cost does not.

| Prompt | Chunks | AllReduce per rank | TTFT (serving, TP4) | Comm share |
|---|---|---|---|---|
| 8K | 1 | ≈ 0.12 s | 0.222 s | ≈ 50 % |
| 128K | 16 | 1.92 s measured (nsys: 2.06 s per rank incl. the 7 decode steps' small calls) | 4.53 s | ≈ 42 % |
| 512K | 64 | ≈ 7.7 s (extrapolated at 0.12 s per chunk) | 31.9 s | ≈ 24 % |
| 1M | 122 | ≈ 14.6 s (extrapolated) | 93.3 s | ≈ 16 % |

TP8 at 128K: 2.56 s of AllReduce per rank (1,265 calls at 2.02 ms; ≈ 2.4 s prefill-only) in a 4.66 s capture ≈ 51–55 %; that is why 8 GPUs did not shorten the 128K first token (4.53 → 4.81 s in serving): the per-rank compute halved and the AllReduce grew.

**Why.** This is the quantitative answer to "comm isn't the hardware bottleneck": on a PCIe box (26 GB/s ring bus bandwidth, no NVLink) intra-node TP prefill spends 14–50 % of the first token in AllReduce depending on prompt length, and cross-node TP16 spends 77 % of its prefill kernel time there (12 usable ranks). For PP boundaries the cost is 8–22 % of kernel time as SendRecv waits (4.7). The three numbers together say where a faster fabric would and would not help: TP within a node for short prompts, yes; PP across nodes, no.

**Caveat.** The 512K and 1M rows are the chunk cost extrapolated from the measured 2.0 ms per call; the 8K and 128K rows are measured (nsys per rank). Sequence-parallel / reduce-scatter + all-gather would change the per-call size.

**Where.** KD #1 (mechanism), KD #6/#7, Executive bottleneck map (128K/512K rows), Scale-Up decision row 2.

### 4.5 Decode stalls behind other requests' prefill chunks — how much of the per-token wait is interference

**Computation.** Per-token inter-token latencies (`itls` lists in the benchmark JSONs; first entry per request skipped). A "stall" is an ITL > 100 ms.

| Run | Tokens | Median ITL | p99 | Tokens stalled | Stall median | Share of all decode wait spent in stalls |
|---|---|---|---|---|---|---|
| 8K c8 (`tp4_closedloop_8k/c8`) | 8,128 | 7.7 ms | 205 ms | 1.2 % | 208 ms | **25 %** |
| 8K c32 | 32,511 | 15.8 ms | 211 ms | 9.2 % | 211 ms | **57 %** |
| 8K open loop 1.00× | 64,770 | 23.1 ms | 216 ms | 20.6 % | 212 ms | **71 %** |
| 128K c4 | 1,499 | 9.4 ms | 338 ms | 21.1 % | 276 ms | 88 % |
| 128K open loop 0.50× / 1.00× | 6,084 / 6,096 | 9.1 / 242 ms | 335 / 349 ms | 10.1 / 60.4 % | 278 / 283 ms | 78 / 97 % |
| 512K c2 / c4 | 248 / 496 | 397 / 460 ms | 766 / 774 ms | 75 / 88 % | 491 / 496 ms | 99.5 / 99.8 % |
| 1M c2 / c4 | 60 / 120 | 120 / 313 ms | 487 / 496 ms | 50 / 75 % | 358 / 357 ms | 97 / 99 % |

The stall length equals one prefill chunk of the co-scheduled request: 208–212 ms at 8K (= the 8K TTFT, 222 ms), 276–283 ms at 128K (`prefill_mean_s_from_hist` 4.5 s ÷ 16 chunks), ~495 ms at 512K (32 s ÷ 64). At the 8K knee, 71 % of all decode waiting is another request's prefill.

**Why.** It is the mechanism of the brief's 5b ("55 % of peak usable at 128K") and it quantifies the prefill/decode disaggregation case without a new experiment: at 8K load the decode SLO is set by prefill interference, not by batch compute. It also explains the Executive "unresolved" chunk-size trade-off: 16K chunks at 128K c4 gave lower mean TPOT (105 vs 141 ms) because there were half as many stalls.

**Decision.** Three candidate remedies, each testable with the existing harness: decode-priority / smaller chunk for mixed traffic, a separate prefill pool (P/D), or admission by "prefill chunks in flight". Rank them by stall-time share, which this table gives per operating point.

**Where.** KD #2 and #5, Scheduler & KV (new card "stall budget"), Executive knobs row.

### 4.6 Energy per token — power is sampled on every run and ranks layouts differently from utilisation

**Computation.** `gpu_node_stats_json` has `gpu_power_mean_w` (mean over the sampled GPUs, 0.5 s interval) per node per run; energy = Σ_nodes (mean W × GPUs sampled on that node) × benchmark duration; tokens = completed × (input + output). Idle baseline 47 W per GPU (P0, 180 MHz; `120_ar_tp4_native_16k_gpu_query.csv`, 138 K idle samples).

| Operating point | GPUs | Mean W per GPU | J per 1K tokens | M tokens per kWh |
|---|---|---|---|---|
| 8K open loop 0.90× (the knee) | 4 | 237 | **34.0** | 106 |
| 8K open loop 0.25× | 4 | 182 | 83.9 | 43 |
| 8K closed loop c1 / c32 | 4 | 162 / 225 | 104.2 / 34.8 | 35 / 103 |
| 128K open loop 0.50× / 0.90× | 4 | 207 / 294 | 59.2 / 46.7 | 61 / 77 |
| 128K c1: TP4/PP1 · TP4/PP4 · TP16/PP1 | 4 · 16 · 16 | 236 · 154 · 150 | 37.2 · 38.8 · 134.8 | 97 · 93 · 27 |
| 1M c1: TP4/PP1 · TP8/PP1 · TP4/PP2 · TP8/PP2 · **TP4/PP4** · TP16/PP1 | 4 · 8 · 8 · 16 · 16 · 16 | 483 · 320 · 379 · 268 · 310 · 225 | 180.9 · 192.0 · 160.2 · 179.7 · **143.1** · 247.2 | 20 · 19 · 22 · 20 · **25** · 15 |

**Why.** Three things the dashboard cannot say today: (1) at 1M the TP4/PP4 layout is not only the fastest but the cheapest in energy per token (143 vs 181 J/ktok for TP4/PP1 and 247 for TP16), so the GPU-seconds penalty in KD #6 (+22.5 %) is partly bought back in energy (−21 %); (2) TP16 at 80.6 % "utilisation" draws 225 W per GPU while TP4/PP4 at 62.8 % draws 310 W — power is the work signal utilisation pretends to be (KD #9); (3) in every PP layout node 1 draws 17–21 % more than node 0 at 1M (414 vs 343 W, 337 vs 282, 289 vs 247) at equal utilisation — the later stages hold more full-attention layers (4.7). A 1M prefill pushes a GPU to 483 W mean; an 8K c1 decode holds it at 162 W.

**Caveat.** Board power from the sampler (GPU only, no host/NIC), mean over the run including ramp; the sampler window is slightly longer than the benchmark. Relative numbers are solid; absolute J/token ±5 %.

**Where.** KD #6 (second cost axis), KD #9 (power column), a "cost" metric in the Scale-Out explorer, Executive guidance matrix.

### 4.7 Pipeline-stage imbalance from the 16-rank exports — real, measurable, and structural (corrected in v1.1)

**Computation.** `profiles_multi_node_native/tp4_pp4_dist/long_prefill_512k/node{0,1}_capture/worker_process_*_processed/cuda_gpu_kern_sum.csv`, 16 usable ranks, grouped by the AllReduce instance count (1,143 / 1,067 / 1,067 / 915 = stages 0–3; 27 layers split 7/7/7/6):

| Stage (node) | Flash-attention time | SendRecv (waiting) | Share of the 10.5 s run spent waiting |
|---|---|---|---|
| 0 (node 0, GPUs 0–3) | 2.37 s (1 full-attention layer: #3) | **2.75–2.77 s** | 26 % |
| 1 (node 0, GPUs 4–7) | 4.71 s (layers #7, #11) | 0.40–0.44 s | 4 % |
| 2 (node 1) | 4.71 s (#15, #19) | 0.50–0.53 s | 5 % |
| 3 (node 1) | 4.71 s (#23, #26) + lm_head | 1.10–1.13 s | 11 % |

Stage 0 has half the attention work of the others (the 7 full-attention layers sit at 3, 7, 11, 15, 19, 23, 26 — only one falls in layers 0–6) and spends a quarter of the run blocked on sends; stage 3 waits on upstream for 11 %. Same picture at 128K (SendRecv 8–10 % on stages 0–2, 17–22 % on stage 3).

**Why.** Equal layer counts are not equal work when attention cost grows with context.

**Correction (v1.1).** v1 proposed `VLLM_PP_LAYER_PARTITION=8,7,6,6` as a fix. It is not one, and it would make the first token longer. A two-number cost model fitted on the four stages — 0.61 s per layer plus 2.36 s per full-attention layer per rank at 512K — reproduces the measured busy time of every stage within 5 % (model 6.6 / 9.0 / 9.0 / 8.4 s vs measured 6.3 / 9.1 / 8.9 / 8.5 s) and the PP2 captures' 3:4 attention split (stage 0 / stage 1 flash time 0.77 on TP4/PP2 and 0.77 on TP8/PP2 against 0.75 expected). Under that model, the full-attention layers sit every fourth layer, so any contiguous stage of eight or more layers holds two of them; the light stage cannot take more layers without picking up a second attention layer. Of all 2,600 contiguous splits of 27 layers into 4, none beats today's 7/7/7/6 (4 tie with it), and `8,7,6,6` (attention layers 2/1/2/2) makes stage 0 the heaviest: predicted first token +7 %. The 26 % stage-0 idle (11 of 168 GPU-seconds per 512K request, 7 %) is therefore structural for this model on a 4-stage pipeline and should be priced, not tuned. Where the layer map does allow a gain is PP2: `15,12` instead of the default `14,13` predicts stage-0 idle 10 % → 3 % and a 3.5 % shorter 512K first token on TP4/PP2 — that is the run to do. The general decision stands: partition by cost (attention layers per stage), not by layer count, after reading the layer map.

**Caveat.** Eager-mode capture; prefill only (fine). SendRecv kernel time includes rendezvous waiting on both sides, so "26 %" is an upper bound on recoverable time.

**Where.** KD #3 (per-stage view), Scale-Out decision output, Profiler.

### 4.8 A latency-bandwidth model of the fabric from nccl-tests — and what it predicts for TP16 decode

**Computation.** `hardware_processed/nccl_points.csv`:

| Group | α (16 KiB) | β (256 MiB algbw / busbw) | time for a 4.6 KB decode AllReduce | for a 37.7 MB prefill-chunk AllReduce |
|---|---|---|---|---|
| TP4 in-node | 19.0 µs | 17.4 / 26.1 GB/s | ≈ 19 µs | ≈ 2.2 ms |
| TP8 in-node | 37.6 µs | 14.3 / 25.0 GB/s | ≈ 38 µs | ≈ 2.7 ms |
| TP2 / TP8 / TP16 cross-node, native | 227 / 280 / 290 µs | SendRecv 7.11 GB/s (256 MiB) | ≈ 290 µs | ≥ 5 ms |
| same, 20G cap | 231 / 287 / 298 µs | 2.04 GB/s | ≈ 300 µs | ≥ 18 ms |

**Why.** Two predictions the serving data confirms: TP16 decode is 55 cross-node AllReduces per token at 208–290 µs each = **11–16 ms** of a 14.9–20.1 ms TPOT (v1 said 16 ms flat; the 128K token is only 14.9 ms, so after ~3.5 ms of kernels and memory floor the per-call cost must be nearer 208 µs for the 4.6 KB decode message — the same figure comes out of the 1M token — while 290 µs is nccl-tests' smallest size, 16 KiB; §4.17) (decode is pure latency, cap-insensitive: 20.08 → 20.57 ms at 20G), and TP16 prefill is bandwidth-bound (3.5× slower ceiling → 3.8× TTFT at 20G). The in-node numbers also say the box is PCIe-class: 52 GB/s per GPU pair and 26 GB/s ring bus bandwidth, where an NVLink system would show 10–20× more — relevant for anyone extrapolating these layouts to other hardware.

**Where.** Scale-Out network tables (replace the bare 25.95 / 25.40 GB/s row), KD #1, Profiler hero.

### 4.9 Host ↔ GPU bandwidth and the KV-tiering arithmetic (the LMCache / storage question)

**Computation.** `nvbandwidth_host_gpu.raw.json`: H2D 56.9 GB/s and D2H 56.6 GB/s per GPU (all 8 GPUs on both nodes within 0.1 %). KV per token per rank from the model config: 8,064 B (4.1). A 1M-token context's latent KV is 8.1 GB per rank; the KDA recurrent state is ~20 MiB per sequence (20 layers × 32 heads × 128 × 128 × 2 B) — negligible.

| Operation at 1M context | Time |
|---|---|
| Recompute (prefill, TP4/PP1) | 93.3 s |
| Recompute on TP4/PP4 | 28.6 s |
| Reload latent KV from host DRAM at 56.9 GB/s | **0.14 s** per rank if transfers do not contend (the four TP4 ranks sit on one socket as two PIX pairs; concurrent reloads may share upstream bandwidth — measure) |
| Save to host at 56.6 GB/s | 0.14 s |
| Prefix hit in GPU cache (measured) | 2.6 s (block walk + 256-token suffix + 32 outputs) |

**Why.** The offload probes were not run, but the bounds are measurable: a host-tier KV reload costs about 0.3 % of a recompute, so for repeat-prefix traffic beyond the ~8 contexts the GPU pool holds (4.1), host DRAM is the obvious next tier and the experiment is cheap (`tp4_native_offload_pressure` is already defined). It also sizes the host: 8 GB per 1M context per rank.

**Caveat.** 8,064 B per token is from the config, not from the engine (see 4.1 caveat); vLLM's offload path adds copies and metadata, so real reload time will be a small multiple of 0.14 s, not 0.14 s.

**Where.** Long Context "CPU offload" box (replace "intentionally disabled"), Scheduler knob matrix, Executive hardware-ceiling card.

### 4.10 The two prefix misses are different bugs

Already in 2.2 finding 4; repeated here because it is a data finding, not a wording fix. `tp4_prefix512k/prefix512k.json`: `input_lens = [524544, 524544, 524544, 524545]`, `ttfts = [32.58, 1.17, 1.17, 32.56]` — the one differently-tokenised prompt is the one that missed. `tp4_prefix1m/prefix1m.json`: `input_lens` all 1,000,000, `ttfts = [94.23, 93.96, 2.61, 2.60]` — the request immediately after the cold one missed. Engine counters (`prefix_hits_delta`) agree: 2 × 524,288 and 2 × 999,424 hits. Two follow-ups, both one run each: hash the tokenised prefix client-side (tokenisation boundary), and log prefix-cache insert/commit events for a 1M hybrid-model prefix (insertion timing).

### 4.11 Repeatability is excellent — use it as the dashboard's noise floor

Eight pairs of identical configurations were run in different cases (`tp4_qualification`/`tp4_closedloop_8k`, `tp4_context_baseline`/`tp4_closedloop_512k`, `tp4_closedloop_512k/c4`/`tp4_512k_maxseq8`, `tp4_context_baseline/1m_c1`/`tp4_1m_concurrency_extension/1m_c1`, …): TTFT agrees within **0.03–0.5 %** at c1 and within 1.9–3.9 % under load (8K c8, 128K c4); TPOT within 0.02–2.1 %. This is the answer to KD #1's "do not call −0.10 % noise without replicate variance": −0.10 % is noise; +1.14 % (TP4/PP2 at 20G, 1M) is at the edge; +3.91 % is real. Put the band on every delta table.

### 4.12 Cold start and model load — measured, not discussed

* First request after server-ready, 0 warm-ups (`warmups = 0` on 77 runs): the first TTFT is within **0–3.4 %** of the median of the rest (worst: TP16 native 128K, +3.4 %; TP4/PP4 20G 128K, +2.8 %). The "GPU cache cold-start prologue" inside a session is ≤ 3 %. (CUDA-graph capture and compile happen before "ready".)
* `server_ready − server_start` in every `case_manifest.json`: **128–192 s for TP4/PP1** (26 cases, median 138 s), **44–52 s for TP8/PP1, TP8/PP2, TP4/PP4 and TP16/PP1**, 142 s / 110 s for the first native TP4/PP2 and TP16 sessions (cold page cache on node 1). Loading is slowest on the layout with the most weight per GPU (24.5 GB at TP4 vs 12.2 GB at TP8) — disk → DRAM → VRAM plus graph capture scale per GPU, and 4 GPUs load in parallel, not 8.
* Over the whole campaign 1.25 h of 4.92 h of server-up time was start-up (25 %).

**Where.** A "start-up" row in the Evidence ledger and in the Long Context fit/finish cards; it answers the model-load question with the data we have and defines what L9 should split next (disk read, DRAM→VRAM copy, compile, graph capture).

### 4.13 The open-loop client cap and what it does to the "cliff"

`tp4_openloop_8192` ran with `--max-concurrency 64`, `tp4_openloop_131072` with `32`. Achieved request rate saturates at 3.30–3.42 req/s (8K) and 0.183–0.185 (128K) from 0.90× onward while the offered rate climbs to 5.29 / 0.285; the surplus queues in the client, invisible to TTFT. Consequences: the 8K TTFT is non-monotonic above the knee (979 → 784 → 826 ms), server `queue_mean` stays ≤ 0.25 s, and the true cliff is steeper than shown. Not a flaw in the knee location (0.90× / 0.75× are below the cap) but a required caveat on every open-loop chart, and a reason to repeat the two sweeps once with the cap at 256 / 64.

### 4.14 Chunk size has a TTFT/TPOT Pareto in the data (not "unresolved")

`tp4_chunk{4k,8k,16k}`: at 1M c1 TTFT 122.0 / 93.3 / 89.0 s; at 128K c4 TTFT 11.34 / 10.66 / 10.88 s and TPOT 141.3 / 119.3 / 105.1 ms. Bigger chunks cut the number of stalls (4.5) faster than they lengthen each one, so 16K wins both axes at these points; the trade-off the Executive tab says is unresolved is resolved in favour of 16K for ≥ 128K prompts, with the open question being 8K traffic mixed in (never run with 16K chunks).

### 4.15 Why the "100G" cap delivered 57 Gb/s

`GCP_CAPPED_100G/network_validation/node0_class.txt`: `class htb 1:10 … rate 100Gbit ceil 100Gbit burst 2400b cburst 2400b`. An HTB class with a 2.4 KB burst at 100 Gbit is limited by the shaper's timer rather than by the link; the measurements fit that (16-stream iperf: 56.8 Gb/s, 0 retransmits, 37 % CPU on the sender vs 134 % and 4,426 retransmits for native). The 20G class (`burst 1760b`) reaches 16.5 of 20. Either raise `burst`/`cburst` to rate × 10 ms in the next sweep or relabel the modes by achieved bandwidth (57G / 16.5G), as the brief does.

### 4.16 Anurag's questions against the data — what exists, what the dashboard shows, what is missing

| Question | In the archive today | Shown on the dashboard | Gap |
|---|---|---|---|
| L2 host/NUMA: cores, pinning, host memory | `nvidia-smi topo -m` (2 sockets, CPU affinity lists) in every profile manifest; no pinning in any command; no host-memory or per-core sampling | NUMA named as a cause without the above | sample host memory + per-rank CPU; one pinned TP8 run |
| Storage / model load / LMCache | `server_start → server_ready` per case (4.12); H2D/D2H 56.9/56.6 GB/s (4.9); offload probes NOT_RUN | nothing | start-up row; run the defined offload probe |
| Tool calling | nothing | nothing | needs a trace-replay workload class |
| MoE expert popularity | nothing (no router counters); only aggregate MoE kernel time (4.3) | nothing | router histogram hook (1 line in the model) |
| PagedAttention / KV block events | `kv_cache_usage` gauge, prefix hit/query counters, preemptions (all 0); pool-in-tokens law (4.1) | KV % only | block alloc/evict events; engine start-up line |
| Reproducibility (git hash, metadata) | `SUITE_SOURCE_SHA256SUMS.txt` (50 files), `V8_FULL_RELEASE.json` pinned stack, `logs/readiness_node*/V8_READINESS.json` (vllm 0.29.0, ray 2.58.0, torch 2.13.0, triton 3.7.1, flashinfer 0.6.18, nccl 2.29.7, driver 580.173.02, CUDA 13.0, kernel 6.12.0, GPU UUIDs), model revision `e1df551a…`, `--seed` per benchmark, NCCL env per run, every server/bench command | partly in the Evidence config key | add suite git commit + vLLM wheel hash; show the readiness block on the Evidence tab |
| Cold-start prologue / epilogue | first-request penalty ≤ 3.4 %; load 44–192 s (4.12) | nothing | show it |
| "Comm isn't the HW bottleneck" | 4.4 and 4.8: 14–50 % of TTFT in AllReduce for in-node TP by prompt length; 77 % for cross-node TP16; ≤ 4 % TTFT sensitivity for PP at 20G | the PP conclusion only | the by-phase table |
| Section 5 decisions: cause vs correlation | 4.1 (KV law), 4.2 (serial prefill), 4.3 (decode budget), 4.5 (stall budget), 4.7 (stage imbalance) are mechanisms with predictions that match within 1–10 %; 4.17 puts them on one wall-time axis | correlations plus "timeline attribution pending" | put the five mechanisms on the KD pages; add the §4.17 panel |

### 4.17 Where the wall time goes — an end-to-end budget per operating point (added in v1.2)

**Why it is missing.** Reviewers ask the same question of every number: of the seconds a user waits, how much is compute, how much memory bandwidth, how much communication, how much the engine (queueing, scheduling, tokenising)? Today the dashboard answers it only in fragments: the Long Context tab's 1M "waterfall" (TTFT / TPOT / queue / KV % at c1–c4, no composition), the Profiler tab's kernel-composition card (aggregate kernel shares, eager mode, §1.2) and the torch operator panel (TP4 vs TP8 at 8K, rank-local, §1.9). No tab stitches a request's wall time together, and none of §4.1–4.16 asked for it as one view. The archive supports it for every run without a new experiment.

**Computation (all from files already in the archive).** For the **first token**: `combined_vllm_runs.csv` gives `mean_ttft_ms` (client) and `queue_mean_s_from_hist`, `prefill_mean_s_from_hist` (engine histograms) per run; the remainder TTFT − queue − prefill is the overhead outside the engine (tokenise, transfer, schedule, first-token sampling) — 14 ms at 8K, 0.19 s at 128K, 1.4 s at 1M, i.e. 1–6 % of a single request's first token. The prefill splits into collectives and kernels from the per-rank captures (`profiles_single_node/tp{4,8}_prefill`, `profiles_multi_node_native/{tp4_pp2_dist,tp8_pp2_dist}/prefill_128k`, `tp4_pp4_dist/{prefill_128k,long_prefill_512k}`, `tp16_pp1_dist/prefill_128k`: AllReduce and SendRecv kernel time ÷ kernel time excluding the start-up Broadcast) or, where no capture exists, from the measured per-call cost × the call count (§4.4, §4.8). Under load the prefill above the single-request prefill is the step shared with other requests' decode (0.35 s at 8K full load, 0.52 s at 128K c4). For the **decode token**: the graphs-on torch budget (§4.3) gives collectives, the memory-speed floor (active weights ÷ BabelStream) and the kernels above it at 8K; longer prompts add the KV bytes read per token at memory speed (above); under load the normal-token median (§4.5) is the request's own step and `mean_itl_ms` − median is waiting behind other requests' prefill chunks, with the collective at the batch's message size from the α-β model.

**What it shows (all six layouts at 128K, 512K and 1M; TP4/PP1 and TP8/PP1 at 8K; four loaded points on TP4/PP1; † = split modelled).**

| Operating point | first token | queue | prefill collectives | pipeline waits | prefill kernels | shared step | overhead |
|---|---|---|---|---|---|---|---|
| TP4/PP1 · 8K | 0.22 s | — | 54 % | — | 40 % | — | 6 % |
| TP8/PP1 · 8K † | 0.26 s | — | 57 % | — | 37 % | — | 6 % |
| TP4/PP1 · 128K | 4.53 s | — | 42 % | — | 54 % | — | 4 % |
| TP8/PP1 · 128K | 4.81 s | — | 50 % | — | 46 % | — | 4 % |
| TP4/PP2 · 128K | 2.65 s | — | 41 % | 5 % | 47 % | — | 7 % |
| TP8/PP2 · 128K | 2.79 s | — | 51 % | 5 % | 37 % | — | 7 % |
| TP4/PP4 · 128K | 1.71 s | — | 38 % | 13 % | 37 % | — | 11 % |
| TP16/PP1 · 128K | 6.42 s | — | 75 % | — | 22 % | — | 3 % |
| TP4/PP1 · 512K † | 31.92 s | — | 24 % | — | 74 % | — | 2 % |
| TP8/PP1 · 512K † | 28.09 s | — | 34 % | — | 63 % | — | 3 % |
| TP4/PP2 · 512K † | 17.95 s | — | 21 % | 6 % | 69 % | — | 4 % |
| TP8/PP2 · 512K † | 15.58 s | — | 31 % | 6 % | 59 % | — | 5 % |
| TP4/PP4 · 512K | 10.22 s | — | 21 % | 12 % | 60 % | — | 7 % |
| TP16/PP1 · 512K † | 29.62 s | — | 53 % | — | 44 % | — | 2 % |
| TP4/PP1 · 1M † | 93.25 s | — | 16 % | — | 83 % | — | 1 % |
| TP8/PP1 · 1M † | 74.69 s | — | 25 % | — | 74 % | — | 2 % |
| TP4/PP2 · 1M † | 52.53 s | — | 14 % | 5 % | 78 % | — | 3 % |
| TP8/PP2 · 1M † | 41.51 s | — | 22 % | 5 % | 69 % | — | 3 % |
| TP4/PP4 · 1M † | 28.57 s | — | 21 % | 12 % | 61 % | — | 5 % |
| TP16/PP1 · 1M † | 68.20 s | — | 44 % | — | 54 % | — | 2 % |
| TP4/PP1 · 8K · open loop 1.0× | 0.98 s | 26 % | 12 % | — | 9 % | 36 % | 17 % |
| TP4/PP1 · 8K · c32 | 1.62 s | 48 % | 7 % | — | 5 % | 25 % | 14 % |
| TP4/PP1 · 128K · c4 | 10.31 s | 50 % | 19 % | — | 24 % | 5 % | 3 % |
| TP4/PP1 · 1M · c4 † | 231.27 s | 58 % | 6 % | — | 33 % | 1 % | 2 % |

| Operating point | per token | collectives | pipeline hops | memory-speed floor (weights + KV read) | kernels above the floor | waiting behind other prefills |
|---|---|---|---|---|---|---|
| TP4/PP1 · 8K | 4.5 ms | 24 % | — | 21 % | 55 % | — |
| TP8/PP1 · 8K | 6.4 ms | 52 % | — | 8 % | 41 % | — |
| TP4/PP1 · 128K † | 5.1 ms | 21 % | — | 30 % | 49 % | — |
| TP8/PP1 · 128K † | 7.1 ms | 46 % | — | 15 % | 39 % | — |
| TP4/PP2 · 128K † | 5.5 ms | 19 % | 7 % | 27 % | 46 % | — |
| TP8/PP2 · 128K † | 7.5 ms | 44 % | 6 % | 14 % | 36 % | — |
| TP4/PP4 · 128K † | 5.6 ms | 19 % | 9 % | 27 % | 45 % | — |
| TP16/PP1 · 128K † | 14.9 ms | 77 % | — | 6 % | 18 % | — |
| TP4/PP1 · 512K † | 7.6 ms | 14 % | — | 44 % | 41 % | — |
| TP8/PP1 · 512K † | 9.5 ms | 35 % | — | 31 % | 34 % | — |
| TP4/PP2 · 512K † | 7.9 ms | 14 % | 4 % | 43 % | 40 % | — |
| TP8/PP2 · 512K † | 9.9 ms | 33 % | 4 % | 29 % | 33 % | — |
| TP4/PP4 · 512K † | 8.0 ms | 13 % | 6 % | 42 % | 39 % | — |
| TP16/PP1 · 512K † | 17.4 ms | 66 % | — | 15 % | 19 % | — |
| TP4/PP1 · 1M † | 10.3 ms | 10 % | — | 54 % | 35 % | — |
| TP8/PP1 · 1M † | 12.1 ms | 27 % | — | 43 % | 30 % | — |
| TP4/PP2 · 1M † | 10.5 ms | 10 % | 3 % | 53 % | 34 % | — |
| TP8/PP2 · 1M † | 12.5 ms | 26 % | 3 % | 41 % | 29 % | — |
| TP4/PP4 · 1M † | 10.6 ms | 10 % | 4 % | 53 % | 34 % | — |
| TP16/PP1 · 1M † | 20.1 ms | 57 % | — | 25 % | 18 % | — |
| TP4/PP1 · 8K · c8 † | 10.8 ms | 12 % | — | 9 % | 51 % | 28 % |
| TP4/PP1 · 8K · c32 † | 34.5 ms | 5 % | — | 3 % | 38 % | 54 % |
| TP4/PP1 · 128K · c4 † | 67.0 ms | 2 % | — | 2 % | 10 % | 86 % |
| TP4/PP1 · 1M · c4 † | 267.4 ms | — | — | 2 % | 1 % | 96 % |

**Why.** Four readings that no single existing panel gives. (1) A single request never queues and the engine's own accounting closes to within 6 % — the "vLLM overhead" people suspect is 14 ms at 8K and grows with the prompt (tokenise + transfer), not with the engine. (2) The first token is collective-bound for short prompts (54 % on 4 GPUs, 75 % across nodes at 128K) and kernel-bound for long ones (74–83 % at 512K–1M): that is the whole TP-vs-PP decision in one picture. (3) Under load the user's wall time is dominated by the scheduler, not by compute: queueing is 50 % of the first token at 128K c4 and 58 % at 1M c4; waiting behind other requests' prefill chunks is 86–96 % of a long-prompt decode token and 54 % at 8K c32. (4) The 1M decode token is 54 % memory-speed KV read on every width (§4.3 scope note); the two-stage pipelines pay 5–6 % at their one boundary against 12–13 % at TP4/PP4's three, and 21–31 % of the 512K first token in collectives; TP16's cross-node collective comes out at 208 µs per call from the 128K, 512K and 1M tokens alike, which bounds §4.8.

**Where.** A "Where the time goes" panel on the Scheduler & KV tab (two 100 %-stacked bar charts — first token and decode token — with the operating point on the y-axis, the total at the right, and a † on modelled rows), fed directly from `combined_vllm_runs.csv`; the same two bars as an Executive tile for the headline operating points; on the Profiler tab, replace the eager kernel-composition card with the graphs-on budget rows. Mark measured vs modelled segments explicitly, as above. The brief's companion note (`PIP_Magnifying_Glass_v1.1`, pages E2E·A and E2E·B) carries the reference rendering and the full method.

**Not yet split, and what would split it.** The kernels above the floor at batch > 1 (one graphs-on torch capture at c8 and c32, 10 min); the overhead outside the engine into tokenise / transfer / schedule (client-side timestamps per phase); the shared-step time under load into other requests' decode kernels vs scheduler bookkeeping (a graphs-on capture at load); the attention excess above the KV-read floor at 512K–1M (a per-kernel timeline). Cheapest of all: keep the engine's per-request phase times per request instead of aggregating them into histograms — the same counters, no new run — and this chart exists for every run without a model.

## 5. Prioritised fix list

**P0 — before the dashboard goes to anyone else (≈ 1 day)**

1. Scale-Out network dropdown: 50G/10G must not render native data (§1.1). Remove the two options or render `NOT_RUN` cells; fix the evidence-ID fallback the same way.
2. Profiler + Executive: eager-mode disclosure on every nsys-derived decode number; delete both "CUDA Graph capture is a candidate optimisation" sentences; replace the decode composition with the graphs-on budget (§1.2, §4.3).
3. Profiler coverage matrix: status from usable exports; delete finding text on rows with 0–2 usable ranks; fix the "Deferred" summary row (§1.3).
4. Wrong numbers on screen: "sub-15 ms TPOT" at c16 → 19.2 ms; "chunk=4096" → 8192; "5.59 s vs 5.37 s" → 4.81 vs 4.53 s; "5,739 µs" → 3,911 µs (128K, 12 ranks) / 4,471 µs (512K, 1 rank); GEMV "156.1 → 89.2" → 171.2 → 126.5 ms or name the subset (§2.1, §2.7).
5. KD #7 hero and Profiler torch panel: decode-only AllReduce 132 → 410 ms, 18.9 → 58.7 µs, 3.1× (§1.9).

**P1 — same week**

6. NUMA/socket cause: reword on all five tabs, downgrade confidence, add the three hardware facts and the pending pinning test (§1.4).
7. Network facts: MTU 1460, ens3, remove RTT/"0 drops", tc HTB, 100G-cap burst note, drop "AMD EPYC 9654" or cite it, remove "NVLink" (§1.5).
8. "NCCL POLICY INCOMPLETE" tile → 12/12 audits clean; fix the validator count (§1.6).
9. Prefix hit-ratio text on Long Context and KD #4: "one of three repeats missed" with the per-request evidence (§2.2 F4, §4.10).
10. Offload / FP8 "intentionally disabled … without requiring host tiering" → "NOT_RUN, no reason recorded" (§2.5).
11. SLO and p95: state the SLO once; show p95 where reliable; add the 0.50× / 0.75× SLO knees next to the slope-inflection knees (§1.7, §2.6).
12. Open-loop client cap caveat on every open-loop chart (§4.13).
13. KD #2 / KD #8 / Long Context: add the serial-prefill timeline and name the partial-prefill limit as the binding knob (§4.2).
14. KD #10 / Scheduler: replace the "unproven allocator law" hedge with the pool-in-tokens table (§4.1).
15. KD #3: publish the kernel grouping, exclude start-up Broadcast from denominators, fix the NCCL 2.18× claim (§2.2 F3).
16. KD #5: add the SLO-conditioned 1.8× row (§2.2 F5).

**P2 — next revision**

17. Energy per token as a cost axis (KD #6, KD #9, Scale-Out metric) (§4.6).
18. Per-stage PP view, with the stage-0 idle priced as structural; the partition test moves to PP2 (§4.7, corrected).
19. Fabric α-β table replacing the bare bus-bandwidth row; TP16 decode prediction (§4.8).
20. Host↔GPU bandwidth and KV-tiering arithmetic in the offload box (§4.9).
21. Repeatability band on every delta table (§4.11).
22. Start-up time and first-request penalty rows (§4.12).
23. Stall-budget card on Scheduler & KV; chunk-size Pareto replaces "unresolved" (§4.5, §4.14).
24. Evidence tab: reconcile NOT_CAPTURED counts; add warm-ups, prompts, load time, usable-export columns; note FINAL_VALIDATION defects; readiness block (§2.8, §4.16).
25. Placement panel from the real inventory; label c1-only metrics (queue, preemptions, output tok/s) as not-exercised (§2.4).
26. Definitions box for dashboard-vs-brief method differences (§1.8).
27. **P1** · "Where the time goes" panel on Scheduler & KV (first-token and decode-token budgets per operating point, measured vs modelled marked), Executive tile for the headline points, graphs-on budget rows replacing the eager composition on the Profiler tab (§4.17).
28. §4.8 TP16 decode AllReduce: 11–16 ms per token (210–290 µs per call), not 16 ms flat; §4.3: scope the "not memory-bound" reading to short prompts and add the KV-read floor at long context (§4.17).

**Runs worth doing before the next dashboard version (each ≤ 30 min of GPU time)**

* 1M c2 and 512K c4 with `--max-num-partial-prefills 2 --max-long-partial-prefills 2 --max-num-batched-tokens 16384` (tests §4.2).
* TP8 8K c1 with ranks pinned to their socket's cores (`numactl --cpunodebind`/`taskset`) (tests §1.4).
* TP4/PP2 512K with `VLLM_PP_LAYER_PARTITION=15,12` — predicted stage-0 idle 10 % → 3 %, first token −3.5 % (tests §4.7, corrected; the v1 suggestion `8,7,6,6` on PP4 is withdrawn: it would lengthen the first token by ~7 %).
* Graphs-on nsys capture of TP4 and TP8 8K decode (replaces the eager tables).
* Re-export (or re-capture) the four distributed decode profiles (§1.3).
* The already-defined `tp4_native_offload_pressure` probe (§4.9).
* Repeat the two open-loop sweeps with `--max-concurrency 256 / 64` (§4.13).
* Graphs-on torch capture of TP4 8K decode at c8 and c32 — splits the batched step's kernels from its collective and its waiting (§4.17).
* The planned FP8 KV-cache probe at 1M c1 on TP4 — predicted decode token 10.3 → 7.9 ms if the latent bytes halve (§4.3 scope note, §4.17).

## 6. Method and files

**Verification method.** Every dashboard value was recomputed from the archive with short Python/pandas scripts: `final_validation/combined_vllm_runs.csv` (119 rows × 81 columns) for all serving metrics; `coverage.csv` for status; the per-benchmark `*.json` files (`ttfts`, `itls`, `start_times`, `input_lens`) for per-request analysis; `case_manifest.json` for commands, server start/ready timestamps and GPU placement; `hardware_processed/{nccl_points,iperf,babelstream,nvbandwidth_metrics}.csv` and `hardware_raw/node{0,1}/*.raw.json` for the fabric; `profiles_single_node/*/{cuda_gpu_kern_sum,cuda_api_sum,nvtx_pushpop_sum}.csv`, `profiles_multi_node_*/**/worker_process_*_processed/cuda_gpu_kern_sum.csv` and `profiles_torch_single_node/*/torch/profiler_out_{0..3}.txt` for the profiler; `vllm_scaleout_network_matrix/*/network_validation/*` for the network state; `results/logs/{preflight,readiness}_node*/` for the stack. The dashboard's own data objects (`scaleoutMetricsData`, `KD_PAGES_DATA`, `CANONICAL_DASHBOARD_DATA`, `PROFILER_REGISTRY`) were extracted from the HTML and compared field by field; the Scale-Out dropdown states were driven in a headless browser to read what actually renders.

**Model facts used** (from `model_validation.json`, revision `e1df551a…`): 27 layers; full attention (MLA, kv_lora_rank 512, rope 64) at layers 4, 8, 12, 16, 20, 24, 27 (1-indexed); KDA linear attention on the other 20; 256 routed experts, 8 per token, 1 shared, MoE intermediate 1,024, dense layer 0 with intermediate 9,216; hidden 2,304; vocab 163,840; max_model_len 1,048,576. Parameter counts derived from these: ≈ 49.1 B total, ≈ 3.07 B active per token.

**Hardware facts used:** 2 nodes × 8 RTX PRO 6000 Blackwell Server Edition (97,887 MiB each), PCIe only (PIX/NODE/SYS; GPU↔GPU 52 GB/s, latency 0.94 / 1.19 / 1.32 µs), two sockets per node (GPUs 0–3 on NUMA 0, 4–7 on NUMA 1), host↔GPU 56.9 / 56.6 GB/s, BabelStream copy 1.71 TB/s, iperf native 173.6 Gb/s (16 streams, MTU 1460), NCCL over plain TCP sockets (`NCCL_NET=Socket`, provider plugin disabled), vLLM 0.29.0 / torch 2.13.0 / NCCL 2.29.7 / driver 580.173.02 / CUDA 13.0.

**Known limits of this review.** Dashboard charts were checked through their data objects and rendered tables, not pixel by pixel; the Key Discoveries explorer charts' axis labels were not individually verified. Per-step decode attribution (§4.3) is derived from aggregate torch tables and carries ±10 %. The scheduler-policy explanation in §4.2 and the MLA-replication explanation in §4.1 are inferred from the data plus vLLM defaults; each has a one-run confirmation listed above.
