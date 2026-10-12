# Performance Intelligence Platform scripts: v1.3's comments, checked in the new code

*v1.4 · 13 Oct 2026 · for the team that maintains the scripts · v1.4 checks each comment in v1.3 against the folder shared on 12 Oct (9 pm), lists what is new, and reads the TP4/PP4 run in the data folder, which was made with the code as it was before these fixes*

*Scope: the folder as shared (214 files, zip md5 076730f9…), read against the folder v1.3 reviewed (145 files). Statements about vLLM's own behaviour come from the vLLM 0.29.0 and FlashInfer 0.6.18 wheels, as in v1.3, and are marked "(vLLM 0.29.0)"; the TP4/PP4 run used vLLM 0.31.0, whose source this review did not read. The statements about the code are asserted by `audit/check_scripts_review_v14.py` (147 checks, all pass), and the figures about the run by `audit/check_tp4pp4_run.py` (58 checks, all pass). Neither runs the team's scripts; the experiments reproduce each mechanism with snippets of their own. Item numbers follow v1.3's (blockers 1–13, coverage fixes 1–8); the new findings are N1–N14. Independent passes over two drafts of this review found errors and gaps; each was checked against the files and corrected.*

## 1. In short

- **Much of v1.3 is fixed.** Of its 42 items, 16 are closed, 14 partly and 12 open; of its 13 blockers, 3 are closed, 8 partly and 2 open (5 and 10). Fixed: the executable bits, the `bash -c` bodies' functions and variables, failed cases in the two-server runner, dry runs, node 1's interface, the cap label, the 1M length, the success check in all four runners, mixed traffic, the MoE and autotune flags on every launch, `VLLM_DISABLE_PYNCCL`, the layer split in the scripts, the skip list's `-` form, the load grid's admission cap, three coverage fixes, step 20's workload and the pause screen's step-12 rule.
- **A default run now stops at step 2,** as v1.3 expected once blocker 2 was fixed. The new pkill pattern, `vllm.entrypoints|vllm serve|ray::RayWorkerProc`, is still in the step's own `bash -c` text, so the first pkill kills the step (status 137, reproduced) and `run_step` ends the run. Behind it, three more stops:
  - step 3, unchanged, unless nccl-tests is built;
  - step 4, which now kills itself the same way (the new pattern's first branch is in its own clean-up line), and whose new comparison breaks the step's own quoting (N2);
  - step 13, new: the two-server Nsight driver stops on a variable it no longer defaults, under `set -u` (N1). None of step 14's two-server Nsight runs can run either.
- **The old `RUN_CONFIG.env`, if it is still on the VM, stays in force (N3).**
  - The folder as shared holds no such file; the one the v1.3-era helpers wrote stays in place when new code is copied over the old. The helpers now keep an existing file, and the two-server runner, the Nsight driver, 14d and the NCCL sweep read it again after the master's unsets.
  - That file holds `VLLM_DISABLE_PYNCCL=1`, the 7,7,7,6 split, the full skip list, TP4/PP4-only and 20G selections and a cap label of 20. The TP4/PP4 run's Ray audit shows the communicator setting and the split on both nodes.
  - Left on the VM, it stops every TP4/PP2, TP8/PP2 and TP16/PP1 server the two-server runner starts, turns vLLM's own communicator off on both nodes, skips steps 4, 11 and 13 even with `--topologies all`, and labels every two-server run capped at 20.
  - Rewrite it with the four keys the helpers now write, not just delete it: the master takes the node addresses from it, and the runners would fall back to older copies in `$HOME`.
- **The build is still not one build.**
  - The TP4/PP4 run used vLLM 0.31.0, FlashInfer 0.7.0.post1 and Ray 2.59.0 on node 0; node 1's were not recorded. The pilot and stages 2 and 3 all ran one identical package list with vLLM 0.29.0.
  - `setup_node_env.sh` now asks for vLLM 0.29.0 but falls back silently to the newest release.
  - Step 0 now calls the readiness gate on both nodes, without its required `--out`, so it exits 2 and never gates (N4).
- **The TP4/PP4 run works end to end, but it is not a reference.**
  - 16 points, 488 requests, all completed at the requested lengths, GPU telemetry from both nodes, no pause.
  - One at a time, its first-token times are 3–22% above the pilot's under a measured 20 Gbit/s cap (16.5 Gbit/s by iperf3), and at 128K inside the spread of stage 3's four TP4/PP4 starts.
  - At 15 of its 16 points, 30 ms is the lag at which its token arrivals recur most often (68–90% of arrivals one at a time), as at 7 of stage 3's 8 TP4/PP4 points and at none of the pilot's or stage 2's. Under load at 8K and 128K that is about one token per request every 30 ms, and its time per token reaches 2.44× stage 2's at 128K.
  - It ran on another build and other machines, with vLLM's own communicator off, the skip list on and 8 requests admitted at once. The cap the helper tried to apply left no record, the folder holds no server log, and its report's median ITL column is wrong in 14 of 16 rows.
- **The crash that led to `VLLM_DISABLE_PYNCCL=1`.**
  - The team's reading of the error, that NCCL has no Tree algorithm for AllGather, points at `NCCL_ALGO=Tree`, which, by the team's account of the change, that run had set. With vLLM's own communicator off, the all-gather goes through PyTorch's NCCL group, which calls the same library under the same settings (vLLM 0.29.0).
  - So the fix was most likely unsetting `NCCL_ALGO` and `NCCL_PROTO`, made in the same change. Stage 3 ran TP4/PP4 on both nodes with neither variable set and no communicator setting on node 0 (vLLM 0.29.0), without this error.
  - Only the master unsets the two now, and the old `RUN_CONFIG.env` wherever a runner re-reads it. Once that file is rewritten, a shell that follows the five docs that still give `NCCL_ALGO=Tree` (three also give `NCCL_PROTO=Simple`) would most likely bring the crash back on the 20-minute helper's path, which goes straight to the two-server runner; the NCCL policy forwards every `NCCL_*` variable to node 1.
  - One short TP4/PP4 case on the chosen build settles it, with a control that sets Tree with the communicator off.
- **Still open from v1.3, besides the above.**
  - Steps still report success when their runs fail.
  - `tc` errors are still silenced, and nothing measures the link.
  - The smoke test still reports ready once 8 of its checks pass, so a node without GPUs or vLLM can pass, and its end-to-end check still writes its result without a server.
  - The batching runner's two-server cases still lack node 1's NCCL library path, and its TP4/PP2 cases can run on one node.
  - No launch checks the MoE backend line, and nothing records the NCCL library each worker mapped.
  - Nsight Compute, depth, mid lengths and network conditions on the PP2 layouts are still missing.
- **Before the next run:** section 6.

## 2. What a default run does now

*With a `RUN_CONFIG.env` made from an example, or the one the helpers now write (a two-node run needs one for the node addresses). With the old file still on the VM, see N3 as well. "Stops the run" marks each stop; the run stops at the first, and each later one is the next stop once the earlier ones are fixed.*

| Step | As shared |
|---|---|
| 0 | Records the environment on both nodes. Node 1's Python snapshot and readiness check use node 1's system Python, outside the venv; the readiness check exits 2 on both nodes, for want of `--out` and, on node 1, of the file itself unless the suite sits at the same path there (N4, N5). Marked done |
| 1 | The chunk A/B on TP4/PP1; its servers can start now that the split is unset. Marked done on the summarizer's status, whatever the runs did (blocker 7) |
| 2 | Runs the first torch capture (TP4, 8K, 8 in flight); then the first pkill kills the step's own shell (status 137). **Stops the run** (blocker 5) |
| 3 | **Stops the run** unless nccl-tests is built under `$BENCH_ROOT`, which the two examples set differently (unchanged) |
| 4 | The TP8 server now gets the MoE and autotune flags, its log path and its PID. After the pinned benchmark, its clean-up pkill kills the step (blocker 5); once that is fixed, its comparison fails because the step's quoting breaks (N2). **Stops the run** |
| 5–9 | Run. Step 6 now adds the TP4 context curve and both baselines, behind `\|\| true` |
| 10, 11 | Run the two-server grid and the split A/B, after clearing both nodes' caps |
| 12 | Runs each condition on both nodes and prints the qdisc to the log. `tc` errors are silenced and nothing measures the link. With an example-based `RUN_CONFIG.env`, the runner's re-read resets the mode and provenance labels to the file's, so only the cap label changes with the condition (blockers 8 and 9) |
| 13 | **Stops the run** at once (N1) |
| 14 | The single-node captures and the two-server torch captures run; the two-server Nsight calls fail behind `\|\| true` (N1) |
| 15 | Runs two tools that do not read the run (N11) |
| 16 | The pause screen, which now counts step 12's runs |
| 17 | Skipped unless `--cb-blocks` is given, as v1.3 asked; the example no longer sets `CB_BLOCKS` |
| 18, 19 | Run with `--profile deep-profile` only. Step 19 kills itself after its first case (blocker 5). **Stops the run** |
| 20 | With `--profile deep-profile` only; it would kill itself after its first case too (blocker 5) |

## 3. v1.3's items, one by one

*Closed: done as v1.3 asked. Partly: the problem is smaller; what is left is named. Open: the problem still stands, whatever else changed.*

### 3.1 Blockers 1–13

| # | v1.3 | Status | Now, and what is left |
|---|---|---|---|
| 1 | The scripts are not executable | Closed | All 49 `.sh` files carry an executable bit in the zip |
| 2 | The `bash -c` bodies cannot see the master's shell state | Closed | `export -f topology_matches` and `bandwidth_matches`; `TP8_DIR`, `NET_DIR`, `CASES_FILE`, `CAPPED_DIR` and `OBS_DIR` expanded by the master; step 4 takes `PID=$!` without `local`. Left: the node addresses, which steps 0 and 10–12 read inside their bodies, and `SSH_KEY`, which steps 10–12 use there, reach the bodies only through `RUN_CONFIG.env`: the master never sets the addresses, and sets the key without exporting it |
| 3 | Files the scripts need are missing from their folders | Partly | The five are now in 02/ and 06/. Not done: one copy resolved from one place, and a start-up check that every file a step calls exists. The copies grew; outside the old `rtx_g4_*` folders, the sampler is in 5 places, the runner library in 6 (two versions: 03/ and 05/ keep the old one, with `pkill -f "vllm"` and no success check; no step imports them), the Ray audit in 3 (two versions) (N13) |
| 4 | One layer split for every server | Partly | Closed in the scripts: the master unsets it; neither example, the smoke test nor either helper sets it; step 11's 15,12 arm is the only place that does. The two-server runner records the variable when set, otherwise vLLM's default by pipeline size (`default_14_13`, `default_7_7_7_6`). Left: the smoke test reports `PP_SPLIT=vLLM_default` as passed without reading any server's split; `README.md` and `scripts/README.md` still export 15,12, the setup guide lists it, and the setup guide and the runbook say the smoke test checks it; the old `RUN_CONFIG.env` brings 7,7,7,6 back (N3) |
| 5 | `pkill -f` kills its own caller | Open | New pattern, same mechanism: the pattern's text is in the caller's own command line (reproduced, E1–E2). Steps 2, 19 and 20; step 4, newly, since the new pattern's first branch is in its own clean-up line (v1.3's did not match it); and node 1's command in 14d, where the pkill comes before `ray stop`, so `ray stop` never runs there (E1c). 14d no longer kills itself at start-up, since its path no longer matches. The 20-minute helper's remote clean-up ends its own ssh shell too; harmless there, since `ray stop` runs first and the pkill's status is discarded |
| 6 | A failed case ends its group | Closed | The two-server runner runs each case under `set +e`, records a failure and carries on, stops Ray in a trap and exits non-zero at the end. Left: a `ray start`, `ray status` or Ray-audit failure (the audit exits 2 on a violation) still ends the group unrecorded, under `set -e` |
| 7 | Steps report success when their runs fail; resume and dry runs skip them | Partly | Dry runs write no markers. Open: none of the 19 bodies sets `-e`, so each reports its last command's status; eight steps end with the summarizer, whose status becomes theirs; `\|\| true` appears 71 times in the bodies (22 in step 12); no step reads its case manifests; resume is still on by default |
| 8 | `RUN_CONFIG.env` overrides the command line | Partly | The master reads it before the flags; the helpers write only `VENV_DIR`, the node addresses and `SSH_KEY`, and only when the file is missing (v1.3 asked them to stop writing it); the Nsight driver keeps the caller's `RUN_HEAVY_PROFILE`. Open: the two-server runner, the Nsight driver, 14d and the NCCL sweep still read the file after the master has set or unset its variables; both examples still set the network mode and provenance labels, and the scripts/ one `RUN_HEAVY_PROFILE` and the three sweep switches (all `0`); `--topologies all` and `--bandwidth all` cannot undo a selection the file sets (E6); an existing file is kept as it is (N3) |
| 9 | The network conditions are not applied as labelled | Partly | Node 1's interface is found with `print $(i+1)`; caps go on and come off on both nodes; step 12 passes the cap label per condition and prints `tc -s qdisc show` on both nodes after each change. Open: every `tc` command in steps 10–12 still silences its errors, the six that apply a cap or loss among them (the twelve deletes may fail harmlessly when nothing is there); the qdisc goes to the master log only, not into each condition's folder; nothing measures the link, and `20_run_vllm_network_matrix.sh`, with its iperf3 checks, is still not called; with an example-based `RUN_CONFIG.env` only the cap label follows the condition (blocker 8). The cluster set-up removes its cap only on its success path, and the 20-minute helper never removes its cap (N6) |
| 10 | The build is not pinned | Open | `setup_node_env.sh` now asks for vLLM 0.29.0, Ray 2.58.0 and FlashInfer 0.6.18, each with a silent fallback to an unpinned install, and for torch 2.13.0 from the CUDA 12.4 index, with a fallback to torch 2.5.1 (N9); no install by file, no checksum; two venv names (`pip_vllm_env` in the set-up and the helpers, `vllm_env` in the master, the two-server runner and the batching runner's node 1). Step 0 calls the readiness gate on both nodes, but it never gates (N4, N5). The runbook, the setup manual and `run_demo_setup.sh` are unchanged. The TP4/PP4 run shows the result: vLLM 0.31.0 |
| 11 | The batching suite cannot run its two-server cases | Partly | The runner now forms and stops a two-node Ray cluster for each two-server case; every mixed-traffic stream has a concurrency, and a mixed point fails when either stream does. Open: node 1's `ray start` there carries none of the NCCL policy's exports, no `LD_LIBRARY_PATH` and no skip list, and activates a fixed venv path; its `ray stop` activates none; no Ray audit runs; the case manifest does not record the nodes; and the three TP4/PP2 cases can run on one node (N7) |
| 12 | The smoke test proves nothing | Partly | The fallbacks now fail on Linux unless `ALLOW_SURROGATE=1` (GPUs, the framework, the utilities, node 1). Open: the test still reports "100% READY" and exits 0 once 8 checks pass, so a node whose GPU, framework and node-1 checks all fail is reported ready; the end-to-end check still writes its `bench.json` without a server (N8); the runner check is still a dry run, in which no step executes; the wave check passes without running when its test file is absent; nothing checks the start-up lines |
| 13 | Some 1M prompts do not fit | Partly | Every 1M prompt is now 1,000,000 tokens (9 points in the batching suite and the profile matrix), and all four runners mark a point FAILED when its exit code is non-zero or fewer requests completed than were sent. Left: a warm-up is still judged by its exit code alone, and `vllm bench serve` exits 0 when every request fails (vLLM 0.29.0) |

### 3.2 The footing: one build, one set of settings

| Item | Status | Now, and what is left |
|---|---|---|
| MoE backend: `--moe-backend flashinfer_cutlass` on every launch, checked at start-up | Partly | The single-node Nsight script (14), both torch profile scripts (14c, 14d) and step 4 now pass it, with `--enable-flashinfer-autotune`. Left: the runners add both flags only when vLLM's help lists them, silently otherwise; no script checks the start-up line naming the MoE backend; the Ray audit does not record `nvcc` inside the workers |
| Autotune set explicitly | Closed | `--enable-flashinfer-autotune` on every launch (in the runners, when vLLM's help lists it). `VLLM_FLASHINFER_AUTOTUNE=1` is still exported by the master, both examples and the smoke test; vLLM never reads it (vLLM 0.29.0) |
| The Ray workers' environment: 14d | Closed | 14d now sources the NCCL policy and passes its exports to node 1's `ray start`. The batching runner does not (N7) |
| `VLLM_DISABLE_PYNCCL` out everywhere | Closed | Set nowhere in the scripts; the master unsets it. The NCCL policy still forwards it, and the split, to node 1 whenever node 0 has them set, so the old `RUN_CONFIG.env` turns the communicator off on both nodes again (N3) |
| Layer split: vLLM's default | Partly | As blocker 4. The docs' "+27.58% TTFT" for 15/12 is still in six files |
| The NCCL library | Partly | The master now makes `/tmp/clean_nccl_libs` on node 1 too, but only where `/usr/local/gib/lib64` exists and the folder does not, with errors silenced. The readiness gate, strict by default, takes NCCL 2.29.7 or 2.31.2 or a `libnccl.so` in the clean folder (non-strict, the folder alone), but does not run (N4). Open: nothing records the library each worker mapped, or `torch.cuda.nccl.version()`; `LD_LIBRARY_PATH` ends in an empty entry (N12) |
| Docs against code | Open | Five docs still give `NCCL_ALGO=Tree`, three of them with `NCCL_PROTO=Simple`; `README.md` and `scripts/README.md` still export both, and `NCCL_CROSS_NIC="1"`; 04's README says the policy enforces `NCCL_ALGO=Tree`. The master's header still says the server restarts between concurrency levels, and the runner library's drain barrier is still called nowhere. Both examples now drop `NCCL_CROSS_NIC` |
| Admission caps | Closed | The four load-grid cases admit 32. 10b's four cases, which the two-server runner defaults to and the 20-minute helper uses, still admit 8; the network-condition cases admit 16 |

### 3.3 The autotune skip list

| Item | Status | Now |
|---|---|---|
| The `-` form, so arm B's empty value stays empty | Closed | The master, the two-server runner, both examples and the smoke test |
| Node 1's own export of the list in the two-server runner | Closed | Gone; node 1 gets node 0's value, empty included, through the policy's exports. 14d now does the same |
| The single-node runner | Closed (unchanged) | Keeps a value that is set, empty included |
| The helpers rewriting `RUN_CONFIG.env` during the A/B | Closed | They no longer write the list. The old file still holds it (N3) |
| The A/B itself | Open | Not run yet. In the batching runner's two-server cases, arm B's empty value reaches node 1's ranks only if node 1's login sets no list of its own (N7); and the old `RUN_CONFIG.env` puts the full list back whenever a runner re-reads it (N3) |

### 3.4 Coverage fixes 1–8

| Fix | Status | Now |
|---|---|---|
| 1. Run the two baselines and the TP4 curve | Closed | Step 6 runs `--group baseline_matrix` and `tp4_r1_continuous_context_curve`, behind `\|\| true` |
| 2. Select the profiles that are defined | Closed in the scripts | The Nsight driver takes a comma list; step 14 asks for `decode_8k,batched_decode_8k_c8,prefill_128k`, which all four layouts define; TP4/PP2 is in step 14's torch loop; step 2's two-server block is gone. The master now selects 13 of the 24 two-server Nsight captures, in 21 runs (one in step 13, 20 in step 14; 8 of them twice, eager and with graphs on), but none runs while N1 stands |
| 3. Graphs on for two-server Nsight | Closed in the scripts | An `ENFORCE_EAGER` switch, eager by default, and a second call in step 14 with graphs on, into its own folder. Same caveat |
| 4. Nsight Compute on 8 and 16 GPUs | Open | Nothing uses Nsight Compute |
| 5. Depth | Partly | The load grid admits 32. The 512K and 1M points still rest on 2–8 requests (1M with 4 in flight: 4 requests, one wave), and the only repeats are TP4/PP1's knee case, so nothing on 8 or 16 GPUs repeats |
| 6. Mid lengths on two nodes | Open | The load grid is still 1K, 8K, 128K, 512K and 1M |
| 7. Network conditions on every two-node layout | Open | Still TP16/PP1 and TP4/PP4 only, at 128K with 1 and 4 in flight; step 12's report reads only those two (N10) |
| 8. What is not covered | Open | Two TP4/PP1 servers side by side, prefix caching on two servers, the expert-parallel run |

### 3.5 Smaller points

| Point | Status | Now |
|---|---|---|
| Step 15's tools are missing | Partly | Both now exist, but neither reads the run (N11) |
| Step 20 compares different workloads | Closed | The same 8K workload, 8 and 32 in flight, under minimal and full telemetry |
| Two master runners | Partly | Now identical copies (`scripts/` and `07/`), but started from 07/ a run misses files and, once the earlier stops are fixed, stops at step 7 (N13); the older `rtx_g4_*` folders remain |
| The setup manual's ray 2.35.0 and triton 3.0.0 | Open | Unchanged |
| Step 11's rows carry neither the folder nor the split | Open | The summarizer is unchanged; the two-server runner's case manifest does record the split now |
| `step12_capped_profiles` and the pause screen | Closed | The pause screen no longer takes paths with `capped_profiles` or `network_resilience` for profiler captures, so it counts step 12's runs |
| The profile runs send no warm-up | Open | All four profile paths (14, 14c, 14d and the two-server Nsight case script) still send none |
| A warm-up shares its measured run's seed | Open | The first benchmark of each case still does; in the TP4/PP4 run, seed 5000 for both |

In all, v1.3 raised 42 items in these five tables: 16 are closed, 14 partly and 12 open.

### 3.6 The feedback, item by item

*Written: in the scripts. Runs: in a default run, once blocker 5, N1 and N2 are fixed and nccl-tests is built.*

| Item | Written | Runs | Note |
|---|---|---|---|
| One vLLM build, pinned and recorded on both nodes | Partly | No | Pins with silent fallbacks (N9); the readiness gate never gates (N4); the TP4/PP4 run used 0.31.0 |
| MoE backend set by flag on every launch, checked at start-up | Partly | Yes, unchecked | The flag everywhere, when vLLM's help lists it; no start-up check |
| Autotune set explicitly | Yes | Yes | The skip list waits for the A/B |
| The clean-folder NCCL library on every worker, mapped library recorded | Partly | Partly | The folder on both nodes where GIB is installed; the path passed to node 1 except by the batching runner; the mapped library not recorded |
| NCCL check on the servers to be used | Partly | Partly | Unchanged: the master calls only the socket tuning sweep |
| Expert-parallel start-up check | No | No | |
| Steady-arrival runs on two servers | Yes | Partly | Block 7 now forms the cluster, but node 1 starts Ray without the NCCL settings (N7); needs `--cb-blocks` |
| One request at a time below 128K on two servers | Yes | Yes | Step 10, 1K and 8K |
| Two servers under load | Yes | Yes | Step 10, 32 admitted now |
| Decode profiles on two servers | Yes | Yes | Torch: four layouts, graphs on. Nsight: 13 captures in 21 runs, eager and with graphs on |
| Nsight Compute kernel captures | No | No | |
| Repeats with a spread | Partly | Yes | TP4/PP1's knee case only |
| Network conditions applied and recorded | Partly | Partly | Both nodes now, labelled per condition; errors silenced, the qdisc in the log only, no link measurement |
| Both nodes' logs kept | Partly | Partly | Node 1's GPU telemetry comes back; the Nsight driver keeps both nodes' Ray worker and raylet logs, the serving runners none; the TP4/PP4 folder holds no server log |
| Warm-ups | Partly | Yes | The main suite's points, but none at 512K or 1M in the load grid, the split cases or the baselines (36 points), none in batching blocks 4 and 7, and none before the profiles |
| Pause screen | Yes | Yes | Now counts step 12's runs |
| Two long prompts, step budgets, request caps and mixed traffic beyond TP4/PP1 | Yes | Partly | Batching blocks 1–4; their two-server cases as in N7 |
| First-repeat rule at 1M | Partly | No | Unchanged |
| Two TP4 copies on one server; prefix caching beyond TP4/PP1 | No | No | |
| Coverage on 8 and 16 GPUs | Partly | Partly | Baselines and profiles selected; mid lengths and depth missing |

## 4. New findings

N1. **The two-server Nsight driver stops on an unset variable.**
   - *Where:* `18_run_vllm_multi_node_profiles.sh` line 11, under `set -euo pipefail`. The change for blocker 8 removed the line that gave `PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE` a default; line 11 still reads it.
   - *What happens:* neither the NCCL policy, the examples nor steps 13 and 14 set it, so the driver stops on line 11 with "unbound variable" (reproduced, E3). Step 13 calls it through `run_step`, so the run ends there. Step 14's two calls fail behind `|| true`, so none of its 20 two-server Nsight runs, 12 eager and 8 with graphs on, happens.
   - *Fix:* `if [[ -n "${PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE:-}" ]]`, or put the default line back.

N2. **Step 4's new comparison breaks the step's own quoting.**
   - *Where:* the master, step 4 (lines 477–558). The comparison is a Python heredoc inside the step's double-quoted `bash -c` string, and its Python has bare double quotes, from line 544 on. Step 4 is the only step with this break.
   - *What happens:* the first of them closes the string. Bash joins the pieces up to `print(NUMA` into the step's script, with every quote stripped from the Python, and passes `Pinning` and the rest, the heredoc's closing `PY` line included, as `$0` and `$1`. The step's shell then reads the heredoc to the end of its script, Python stops at a syntax error on the fourth line, no `PINNING_COMPARISON.json` is written, and the step exits 1 (the mechanism reproduced with a snippet, E7; the split replayed on the master's text). v1.3's version had no such quotes. Today the clean-up pkill kills the step first (blocker 5); once that is fixed, this stops the run at step 4.
   - *Fix:* put the comparison in its own `.py` file and call it, or escape its quotes as the rest of the body does.

N3. **The old `RUN_CONFIG.env` stays in force, if it is still on the VM.**
   - *Where:* the folder as shared holds no `RUN_CONFIG.env`; the one the v1.3-era helpers wrote stays in place when new code is copied over the old. Both helpers now keep an existing `scripts/RUN_CONFIG.env` ("preserved without clobbering") and write one, with the four keys, only when there is none. The two-server runner, the Nsight driver, 14d and the NCCL sweep read it again after the master has set or unset its variables.
   - *What happens:* the old file holds `VLLM_DISABLE_PYNCCL="1"`, `VLLM_PP_LAYER_PARTITION="7,7,7,6"`, `TOPOLOGY_SELECTION="tp4_pp4"`, a 20G bandwidth selection, `NCCL_CROSS_NIC="1"`, the full skip list, a cap label of 20, and `unset NCCL_ALGO NCCL_PROTO`. The TP4/PP4 run's Ray audit shows the communicator setting, the split and `NCCL_CROSS_NIC` on both nodes, as the file set them. With that file still on the VM:
     - the two-server runner exports 7,7,7,6 into both nodes' `ray start`, and vLLM stops a server whose split does not have one entry per stage (vLLM 0.29.0), so every TP4/PP2, TP8/PP2 and TP16/PP1 server fails at start-up; only TP4/PP4 starts;
     - it exports `VLLM_DISABLE_PYNCCL=1` again, and the NCCL policy forwards it, so vLLM's own communicator is off on both nodes;
     - the master reads the selections before the flags, and `--topologies all` or `--bandwidth all` cannot undo them (E6): steps 4, 11 and 13 and step 2's TP8 captures are skipped, and step 12 runs only its 20G condition;
     - every two-server run is labelled with a 20 Gbit/s cap, step 10's native runs included;
     - arm B of the skip-list A/B gets the full list back at every re-read.
   - *Fix:* rewrite the file with the four keys the helpers now write. Deleting it is not enough: the master takes the node addresses from it, and without it the runners fall back to `$HOME/rtx_g4_smoke/RUN_CONFIG.env` (the two-server runner also to the old suite's folder). Every reader takes a `RUN_CONFIG.env` in the folder a run is started from before either; check there too. The old file is also, today, what unsets `NCCL_ALGO` and `NCCL_PROTO` at the runners' re-read, so move that unset into the runner and the NCCL policy in the same change (section 6). Then make the runners stop reading the file, or re-apply the master's unsets after their read.

N4. **The readiness gate never runs.**
   - *Where:* step 0 calls `22_readiness.py` on node 0 and node 1 (master lines 405 and 410), without `--out`.
   - *What happens:* `--out` is required, so on node 0 the script stops at argument parsing with exit 2 (reproduced, E4), behind `|| true`, and the readiness file holds its usage message. On node 1 it does the same if the suite sits at node 0's path there; otherwise Python cannot open the file, also exit 2 (N5). With `--out`, the gate is strict by default and would fail the TP4/PP4 run's stack: vLLM 0.31.0, Ray 2.59.0 and FlashInfer 0.7.0.post1 against the 0.29.0, 2.58.0 and 0.6.18 it expects.
   - *Fix:* pass `--out` (a folder per node), run it inside the venv on both nodes, and stop the run when it fails.

N5. **Node 1's step-0 checks run outside the venv.**
   - *Where:* master lines 407 and 410.
   - *What happens:* the remote commands run `python3` without activating a venv, so node 1's "Python stack" and readiness come from its system Python, which may lack torch and vLLM or hold other versions. The readiness call also needs the suite at the same path on node 1, and nothing copies it there: the only file any script copies to node 1 is the sampler.
   - *Fix:* activate `$VENV_DIR` in both remote commands, and copy the gate to node 1 as the runners copy the sampler.

N6. **The two set-up helpers.**
   - `setup_cluster_and_run_smoke.sh`:
     - it reads `RUN_CONFIG.env` only when no node-1 address is given (lines 49–53), yet removes node 1's cap with `ssh -i "$SSH_KEY"` under `set -u` (line 177). Called with the address, as its usage line shows, it stops there on "SSH_KEY: unbound variable", after removing node 0's cap and before node 1's;
     - it caps both nodes, then runs the smoke test under `set -e` (line 140), so a failing smoke test stops it with both caps in place;
     - with `--run-benchmark` it runs the master's step 10 with `--topologies tp4_pp4 --bandwidth 20g`. Step 10 clears both caps and runs its group, which the runner selects by group alone, so all four layouts run, uncapped, under a banner that says TP4/PP4.
   - `run_20min_tp4pp4_campaign.sh`:
     - it caps both nodes at 20 Gbit/s with `sudo` (no `-n`) and its errors silenced, records no qdisc, and never removes the cap;
     - on a node without `RUN_CONFIG.env` it writes the file but does not read it, so `SSH_KEY` is unset at its pre-flight (line 117) and it stops there, with both nodes capped;
     - it takes node 0's address from the first entry of `hostname -I`;
     - it runs one case from 10b (8 admitted), not the master's load-grid case (32), so its figures do not line up with a full run's;
     - its header lists six parts and its banner promises "FlashInfer CUTLASS (Autotuned)" and 20 Gbit/s; it runs one case and checks neither.
   - *Fix:* give `SSH_KEY` a default before its first use in both, and remove the caps in a trap. In the 20-minute helper, record `tc -s qdisc show` on both nodes before and after, measure the link, run the master's `tp4_pp4_dist_load` case, and unset `NCCL_ALGO` and `NCCL_PROTO` as its night version did.

N7. **The batching runner's two-node cluster.**
   - *Where:* `run_continuous_batching.py`, node 1's `ray start` (line 148) and `ray stop` (lines 140 and 242).
   - *What happens:* node 1 starts Ray with `source $HOME/vllm_env/bin/activate 2>/dev/null || true; CUDA_VISIBLE_DEVICES=… ray start …`, with none of the NCCL policy's exports, no `LD_LIBRARY_PATH` and no skip list.
     - vLLM's Ray workers fill in the driver's variables only where their own node's environment has none (vLLM 0.29.0), so node 1's ranks take node 0's NCCL and skip-list settings unless node 1's login sets its own.
     - `LD_LIBRARY_PATH` is the one that matters: the loader reads it when the worker starts, from node 1's `ray start` shell, so node 1's ranks load the clean NCCL folder only if node 1's login puts it on the path.
     - On a node set up by `setup_node_env.sh` the venv is `pip_vllm_env`, so the activation fails silently. Node 1's `ray stop` activates no venv at all and its output is captured, so where `ray` is only in the venv the stop fails unseen and node 1's Ray can stay up between cases.
     - No Ray audit runs, the case manifest does not record the nodes, and the default SSH key (`google_compute_engine`) differs from the helpers' (`id_rsa`).
     - No two-server batching case sets `ray_gpus_per_node`, so the runner offers 8 GPUs on each node. The three TP4/PP2 cases need 8, and vLLM places them with PACK (vLLM 0.29.0), so they can run on one node under a two-server label.
   - *Fix:* form and stop the cluster with the two-server runner's code (the policy's exports, `$VENV_DIR`, the audit), or call that script; give the TP4/PP2 cases `ray_gpus_per_node: 4`.

N8. **The smoke test's end-to-end check looks measured.**
   - *Where:* `run_smoke_test.sh`, the micro-benchmark check.
   - *What happens:* it still starts no server. It writes `bench.json` with a first-token time taken from two consecutive clock reads (at least 1 ms) and a fixed 5.0 ms a token, and records "Generated valid bench.json telemetry output" as passed; the "pipeline validated" message it builds goes into a variable nothing uses. So the smoke folder holds a first-token time that no server produced.
   - *Fix:* blocker 12's: one real server per pipeline size, one request each, its start-up lines checked.

N9. **`setup_node_env.sh`'s pins fall back silently.** It asks for torch 2.13.0 from the CUDA 12.4 index (`whl/cu124`) and falls back to torch 2.5.1 there, then for vLLM 0.29.0, Ray 2.58.0 and FlashInfer 0.6.18, each falling back silently to an unpinned install (`vllm>=0.6.3`, any Ray, any FlashInfer) if the pinned one fails; the readiness gate that would catch it does not run (N4). The TP4/PP4 run's venv, however it was built, shows what an unpinned install gives: vLLM 0.31.0 and FlashInfer 0.7.0.post1, and torch 2.13.0 with 13 CUDA 12 packages beside the CUDA 13 ones (`nvidia-nccl-cu12` 2.21.5 beside `nvidia-nccl-cu13` 2.29.7). *Fix:* install the chosen wheels by file with their hashes, from one index, stop on any failure, and record `pip freeze` on both nodes.

N10. **Step 12's comparison sets unlike points side by side.** For each layout and condition, `find_ttft` (master line 761) returns the mean first-token time of the first result file `rglob` finds: 128K with 1 or with 4 in flight, in file-system order. So its "degradation" can set one load against the other. It reads only the native and impaired conditions, not the 100G or 20G runs; only TP16/PP1 and TP4/PP4; and only the first-token time. *Fix:* match benchmarks by name across conditions, report each point under each condition, and add time per token.

N11. **Step 15's tools do not read the run.** `tools/compile_canonical_data.py` reads `data/results/real_data/combined_vllm_runs.csv` under the repository, else the first CSV in `data/results/` (in this folder, the TP4/PP4 report's table), and writes it to the repository's `dashboard/DASHBOARD_CANONICAL_DATA.json`, with 16 GPUs and 1,536 GiB written in as constants; it never sees `$MASTER_ROOT`. `tools/run_v1_4_verification.py` checks strings in a dashboard file at a fixed Windows-style relative path, which does not exist on the VM; `|| true` hides the error. *Fix:* pass the run's folder to the aggregation and write its output into the run; take the dashboard check out of the run.

N12. **`LD_LIBRARY_PATH` ends in an empty entry.** The master and both examples build it as `/tmp/clean_nccl_libs:${LD_LIBRARY_PATH:-}`. With it empty, the path ends in `:`, an empty entry the loader reads as the current folder; with the master and an example both applied, the folder goes in twice. The TP4/PP4 run's workers on both nodes had `/tmp/clean_nccl_libs:/tmp/clean_nccl_libs:/usr/local/cuda/lib64:/usr/local/cuda/lib64:`. *Fix:* `/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}`, set in one place.

N13. **The copies drift, and the 07/ master misses files.**
   - The runner library's copies in 03/ and 05/ (and in the old `rtx_g4_smoke_v5/`) still have `pkill -9 -f vllm` and no success check, and the Ray audit has two versions. Nothing uses the old copies today; the next step that imports from 03/ or 05/ gets the old behaviour (blocker 3).
   - The two master copies are identical, but steps 7 and 15–17 reach files through `$SUITE_ROOT` with no fallback, and 07/ has no `05_long_context_1m_extensions/` or `pip_scan.py`. Started from the 07/ copy, step 7's audit command fails, with no `|| true`, and stops the run there once the earlier stops are fixed.
   - *Fix:* keep one copy of each file, resolved from one place, and one master.

N14. **Smaller.**
   - The scripts/ example's batching help lost its examples: the lines that showed `"all"`, `"1,2,3"` and `"4"` all read `# export CB_BLOCKS="all"` now. (Its `export CB_BLOCKS="all"` is commented out too, as v1.3 asked, so step 17 runs only with `--cb-blocks`; keep it that way.)
   - The zip carries 252 macOS metadata entries (`__MACOSX/`) and 3 `.DS_Store` files; leave them out when zipping.

## 5. The TP4/PP4 run in the data folder

*The run in `data/results/tp4_pp4_20g_<timestamp>/` was made with the code v1.3 reviewed, which already held the six changes the team made that night to finish it (5.7). So it shows how that code collects data; it tests none of this version's fixes. `audit/check_tp4pp4_run.py` prints every figure below.*

### 5.1 Did it work?

Yes, as a pipeline.
- All 16 points of the two-node load grid completed every request: 1K and 8K with 1, 8 and 32 in flight, 128K with 1, 2, 4 and 8, 512K and 1M with 1, 2 and 4. That is 488 requests, none failed, every prompt and answer at the requested length; the runner marked all 16 COMPLETED with exit code 0.
- One server start served all 16 points in a fixed order: 96 s to ready, then 1,511 s of serving (1,130 s of measured runs, 313 s of warm-ups, 68 s between them). The 1K to 128K points were warmed up at their own load first; the six 512K and 1M points were not.
- Node 0's server metrics (KV use, the queue, preemptions) were captured at every point, and the summary holds GPU telemetry from both nodes. No request was preempted; KV use peaked at 5.6% (1M with 4 in flight).
- The pause screen finds no pause; the longest silence is 1.75 normal steps (1K, one at a time).
- The mean first-token time and time per token recompute from the per-request arrays, and the team's table matches the files for those two and for requests/s and output tokens/s.

### 5.2 What it ran on

| Setting | This run | Agreed | This version of the code |
|---|---|---|---|
| vLLM, FlashInfer, Ray | 0.31.0, 0.7.0.post1 and 2.59.0 on node 0, with torch 2.13.0; node 1 not recorded | one build, pinned and recorded on both nodes; the pilot and stages 2 and 3 ran one identical package list with vLLM 0.29.0 | asks for 0.29.0 with silent fallbacks; the readiness gate never runs (N4, N9) |
| vLLM's own NCCL communicator | off on both nodes (`VLLM_DISABLE_PYNCCL=1`) | on | on, unless the old `RUN_CONFIG.env` stays (N3) |
| `NCCL_ALGO`, `NCCL_PROTO` | unset | unset | unset by the master, and by the old file at a runner's re-read (5.7) |
| Layer split | 7,7,7,6, set | unset; vLLM's default at PP4 is the same 7/7/7/6 (vLLM 0.29.0), so no difference here | unset |
| MoE backend | FlashInfer CUTLASS, by flag | the same | the same |
| Autotune | no flag, at `--optimization-level 2`, where vLLM 0.29.0 turns it on (0.31.0 not read) | the flag | the flag |
| Skip list | set on both nodes; in vLLM 0.29.0 it keeps the start from tuning FlashInfer CUTLASS's two MoE GEMMs. With no server log, what 0.31.0 tuned is unknown | kept until the A/B decides | unchanged |
| `NCCL_CROSS_NIC` | 1 on both nodes | dropped | dropped from the examples |
| Admitted at once | 8 (10b's case) | 32 for the load grid | 32 in the master; 8 in 10b and the 20-minute helper (N6) |
| Network | a 20 Gbit/s cap the helper tried to apply, with nothing recorded; the labels say cap "20", mode "native", provenance "GCP_UNSPECIFIED" | the cap recorded on both nodes and the link measured | the qdisc printed in step 12's log; the link not measured (blocker 9) |

### 5.3 What the folder holds, and what it lacks

- *It holds,* for each point, the per-request result file, the bench command and the warm-up record; the server command; the case and run manifests, with node 0's package list and GPUs; both nodes' NCCL settings as the runner set them before Ray started (the Ray audit shows what the workers got); the Ray audit of both nodes' workers; and the summary, with node 0's server metrics and both nodes' GPU telemetry.
- *It lacks* the server log (the helper prints its path), the 16 evidence archives the case manifest names, the raw sampler files (`metrics_node0.jsonl`, `metrics_node1.jsonl`), the bench and warm-up stdout logs, the `ray status` log, the 12 Ray snapshots the runner takes (status, nodes, actors and placement groups, before the server, at ready and after), any Ray worker log (the serving runners keep none), node 1's packages and vLLM version, and anything about the network: no qdisc and no link test.
- *Ask:* ship the server log, the evidence archives, the sampler files and the Ray snapshots with every run folder. Without the server log, nothing shows the MoE backend line, the autotune lines or the NCCL version that ran.

### 5.4 How its figures compare

The earlier TP4/PP4 runs across the two nodes. Their MoE backends and autotune come from each set's own profiling captures; the TP4/PP4 runs kept no server log, so theirs are inferred (the same packages, with no flag naming a backend):
- **The pilot:** vLLM 0.29.0's release build, Triton MoE (17 of 17 capture logs, none with an autotune line), 8 admitted. Its 20G run kept its network evidence: node 0's qdisc, and iperf3 at 16.5 Gbit/s under the cap against 173.6 native.
- **Stage 2:** the same package list, FlashInfer CUTLASS MoE (9 of 9 capture logs) with autotune off (its server flag, and every log says autotune was skipped), 16 admitted, labelled native.
- **Stage 3:** the same package list, FlashInfer CUTLASS with autotune run at start-up (its one capture log, from a TP16/PP1 run), 16 admitted. Four server starts, in folders named native, 100G, 20G and 0.05% loss; every manifest is labelled native with cap 0, and the folder holds no qdisc or link test, so which caps were in force is not recorded.
- Every set ran on other GPUs (node 0's first GPU differs in each), and this run on vLLM 0.31.0.

First-token time and time per token, in ms; ratios are this run over the earlier one.

| Point | This run | Earlier | Ratio |
|---|---|---|---|
| *The pilot, 20G, one request at a time* | | | |
| 128K (4 requests each) | 2,060 · 13.25 | 1,961 · 5.65 | 1.05 · 2.35 |
| 512K (2 each, no warm-up) | 13,537 · 22.95 | 11,134 · 8.10 | 1.22 · 2.83 |
| 1M (2; the pilot 1; no warm-up) | 30,669 · 14.48 | 29,684 · 10.71 | 1.03 · 1.35 |
| *Stage 3, the folder named 20G* | | | |
| 128K, 1 in flight (4 requests each) | 2,060 · 13.25 | 2,153 · 15.62 | 0.96 · 0.85 |
| 128K, 4 in flight (20 requests; stage 3 8) | 5,435 · 71.28 | 5,005 · 64.18 | 1.09 · 1.11 |
| *Stage 2, under load (the same request counts)* | | | |
| 8K, 8 in flight | 721 · 31.39 | 761 · 23.51 | 0.95 · 1.33 |
| 128K, 2 in flight | 3,742 · 52.25 | 2,567 · 21.40 | 1.46 · 2.44 |
| 128K, 4 in flight | 5,435 · 71.28 | 4,015 · 46.28 | 1.35 · 1.54 |
| 128K, 8 in flight | 7,471 · 206.64 | 6,984 · 93.73 | 1.07 · 2.20 |
| 1M, 2 in flight | 45,048 · 489.07 | 43,347 · 453.33 | 1.04 · 1.08 |
| 1M, 4 in flight | 78,026 · 752.03 | 71,194 · 677.17 | 1.10 · 1.11 |

- Stage 3's four starts spread widely at 128K: one at a time, 1,976–2,967 ms to the first token and 9.32–21.75 ms a token; with 4 in flight, 4,613–6,792 ms and 58.01–88.46 ms. One at a time, the start in the folder named native is the slowest to the first token. This run sits inside both ranges.
- One at a time, this run's first-token times are 3–22% above the pilot's under its measured cap, the 22% at 512K on two requests each. Reading the prompt works about as before; with a spread like stage 3's, one start cannot show a smaller change.
- Its time per token is 2.35× the pilot's at 128K and 2.83× at 512K one at a time, and up to 2.44× stage 2's at 128K under load. Stage 3 was already slower than the pilot (9.32–21.75 ms a token at 128K, against 5.65). The build, the machines and the communicator setting differ from all three sets, the MoE backend from the pilot's, autotune from stage 2's, and the NCCL settings from both the pilot's and stage 2's, so these runs cannot say which change cost what.

### 5.5 Decode: a 30 ms cycle

- Time per token varies between requests at some one-at-a-time points: 7.2–17.0 ms at 1K (20 requests) and 8.2–24.4 ms at 128K (4); at 512K the two requests took 18.8 and 27.1 ms. At 8K and 1M it holds within 7.3–7.5 and 14.0–14.9 ms.
- The tokens recur at 30 ms. One at a time, 68–90% of token arrivals (those at least 31 ms before their request's last token) have another 30 ms later (±1 ms), against 0–41% at 25 or 35 ms. Under load at 8K and 128K the gap between tokens is itself 30 ms (median 29.9–31.6 ms), about one token per request per cycle.
- Taking 30 ms as the lag at which arrivals recur most often from 12 to 40 ms, at least 1.3 times as often as at any other, it holds at 15 of the 16 points, with 13–82% of arrivals under load, where long prompts being read interrupt it; 1K with 8 in flight peaks at 24 ms instead.
- Stage 3 shows the same at 7 of its 8 TP4/PP4 points, in all four starts. The pilot shows it at none of its six one-at-a-time points, under either label: its tokens came at a steady 5.6–10.7 ms. Nor does stage 2: at 8K and 128K under load its median gap was 10.0–21.7 ms, where this run's is 29.9–31.6.
- So a cap alone does not cause it (the pilot's measured 20G run, Triton MoE with the pilot's NCCL settings, has none), nor the package list (stage 2's is the pilot's and stage 3's), nor FlashInfer CUTLASS with autotune off (stage 2), nor the communicator setting on node 0 (stage 3's had none), nor the skip list on node 0 (stage 3's first start had none there and shows it; node 1's is not recorded).
- What stage 3 and this run share, and the pilot and stage 2 lack, as recorded: FlashInfer CUTLASS with start-up autotune (stage 3's log shows it ran; this run had no flag at the optimization level where vLLM 0.29.0 runs it; stage 2 turned it off, and the pilot's Triton runs log none); `NCCL_BUFFSIZE=4194304` (NCCL's default) and `NCCL_CROSS_NIC=1` on both nodes' workers; the interface given as `ens3` rather than `=ens3`; `CUDA_DEVICE_ORDER=PCI_BUS_ID` on node 0; and other machines each time. The cause is not in these files.
- At 8K one at a time, the stream carried about two tokens per chunk (127–133 gaps for 255 tokens), so that point's ITL figures are per chunk: mean ITL 14.60 ms against 7.43 ms a token. A tool that reads ITL as the time between tokens is off by 2× there.
- *To find it:* on the chosen build, TP4/PP4 at 8K, one request at a time, for a minute, keeping the server log and a short torch trace; then the same with `--no-enable-flashinfer-autotune`, and with the pilot's NCCL settings, one change at a time.

### 5.6 The report against its files

| The report says | The files say |
|---|---|
| "ALL 16 TEST CASES PASSED WITH 0 ERRORS"; no preemptions, no failures | Holds: 488 of 488 requests, no preemptions |
| The table's first-token time, time per token, requests/s and output tokens/s | Match the files |
| Median ITL 5.39–5.40 ms in 15 of 16 rows | Wrong in 14 rows. The files give 5.40 ms only at 1K one at a time; one at a time, 5.63 ms at 8K, 11.02 at 128K, 28.11 at 512K and 11.09 at 1M; under load, 15.71–31.61 ms from 1K to 128K, 30.49 at 512K with 2 in flight, 575.37 at 512K with 4 and 239.83 at 1M with 2. The 1M row with 4 in flight (812.06 ms) is the only other one that matches |
| One at a time, median ITL "consistently clocked at 5.40 ms" from 1K to 1M | Only at 1K, as above |
| First-token time "scaled strictly linearly with sequence length" | It did not. Per prompt token, one at a time: 73.2 µs at 1K, 36.3 at 8K, 15.7 at 128K, 25.8 at 512K, 30.7 at 1M |
| Chunked prefill "bounded memory spikes, keeping KV cache usage under 5.6%" | A prompt's KV is held whatever the chunk size; 5.6% is the share of the pool those prompts took, which reflects the pool's size |
| "20 Gbps (Linux Traffic Control `tc HTB` rate-paced on `ens3`)"; "FlashInfer CUTLASS (Autotuned)" | CUTLASS by flag, yes. Nothing recorded the cap (no qdisc, no link test), and with no server log nothing shows the tuning; the skip list was set |
| "Pipeline Partition: `7, 7, 7, 6`" | Yes, set; it is also vLLM's default at PP4 (vLLM 0.29.0) |
| "Pre-flight Ray NCCL environment audit completed with 0 violations" | Yes. The audit checks the P2P and SHM overrides, that each node's `NCCL_*` variables and `LD_LIBRARY_PATH` match node 0's, and that the nodes' splits agree; it does not check the communicator setting, whether a split is set, or the build |
| The rows with 32 in flight (first token 7.6 s at 1K, 23.1 s at 8K) | With 8 admitted, up to 24 requests waited for a seat: by the server's queue-time histogram, waiting is 95% and 97% of those first-token times. At 128K with 4 and 8, 512K with 4 and 1M with 4 in flight, waiting is 44–54% of the first-token time too, there behind other prompts being read (no more than 8 ran at once). The report should say so |
| The CSV's `peak_kv_cache_pct` | Holds fractions: 0.056 for 5.6% |

### 5.7 The night's changes, and the crash

| Change made before the run | In this version |
|---|---|
| The 20-minute helper: `VLLM_DISABLE_PYNCCL=1`, and `NCCL_ALGO` and `NCCL_PROTO` unset instead of Tree and Simple, in the `RUN_CONFIG.env` it wrote; the case run directly through the two-server runner; `ray stop -f` and a pkill on both nodes first | The helper now writes only the four keys, so it neither sets the communicator nor unsets `NCCL_ALGO` and `NCCL_PROTO`. It still runs one case from 10b through the two-server runner (N6). Its pre-flight is kept; the remote pkill ends its own ssh shell, harmless there. The file it wrote that night stays on the VM unless removed (N3) |
| Two-server runner, shell: `VLLM_DISABLE_PYNCCL=1` locally and in node 1's exports | Removed |
| Two-server runner, Python: `VLLM_DISABLE_PYNCCL=1` in the server's environment | Removed |
| NCCL policy: `VLLM_DISABLE_PYNCCL` in the list it exports to node 1 | Still in the list, forwarded whenever node 0 has it set: harmless once nothing sets it, but the old file sets it (N3) |
| `09_metrics_sampler.py` copied into 04/ | Present in 04/, and now in 02/ and 06/ too. Node 1's GPU telemetry reached the run's summary |
| Cluster set-up, master and both examples: `VLLM_DISABLE_PYNCCL=1`, and `NCCL_ALGO` and `NCCL_PROTO` unset | The communicator setting is gone everywhere; only the master still unsets the two NCCL variables |
| The master stopped on PP1 servers under the 7,7,7,6 split, so the case was run through the two-server runner | Blocker 4, fixed in the master; the old `RUN_CONFIG.env` brings the split back through the runners (N3) |

**The crash.**
- The team's account: vLLM's own NCCL communicator (pynccl) crashed in the last stage's logits all-gather (Worker_PP3_TP0), with NCCL reporting no Tree protocol for an AllGather of int8.
- By the team's account of the change, that run had `NCCL_ALGO=Tree` and `NCCL_PROTO=Simple` set: the night's change replaced them with an unset. The run folder holds nothing from the crashed run itself. NCCL implements its Tree algorithm for AllReduce only, so with `NCCL_ALGO=Tree` forced it has no algorithm for an AllGather, whichever communicator calls it. With vLLM's communicator off, the all-gather goes through PyTorch's NCCL group (vLLM 0.29.0), which loads the same library under the same settings.
- So the fix was most likely the unset of `NCCL_ALGO` and `NCCL_PROTO`, made in the same change; `VLLM_DISABLE_PYNCCL=1` should not have been needed. Stage 3 ran TP4/PP4 on both nodes with neither variable set and no communicator setting recorded on node 0 (vLLM 0.29.0), without this error.
- Only the master unsets the two now, and the old file wherever a runner re-reads it. Once that file is rewritten, the 20-minute helper's path, which goes straight to the two-server runner, unsets neither, and the NCCL policy forwards every `NCCL_*` variable to node 1; a shell that follows the five docs that give `NCCL_ALGO=Tree` would most likely bring the error back there.
- *To settle it on the chosen build:* one TP4/PP4 case, 8K one at a time for a few minutes, with `VLLM_DISABLE_PYNCCL`, `NCCL_ALGO` and `NCCL_PROTO` all unset, keeping the server log (vLLM prints the communicator's NCCL version on its rank 0); and, as a control, the same with `NCCL_ALGO=Tree` and the communicator off, which on this reading fails the same way.

### 5.8 Before the next TP4/PP4 run counts as a reference

- The chosen build installed by file on both nodes and recorded on both, with the readiness gate passing.
- The old `RUN_CONFIG.env` rewritten; vLLM's own communicator on; `NCCL_ALGO` and `NCCL_PROTO` unset on both nodes.
- The master's `tp4_pp4_dist_load` case (32 admitted), so the run lines up with a full run.
- The cap applied, recorded and measured as the pilot's network runs did: `tc -s qdisc show` on both nodes before and after, the link measured both ways with iperf3, the cap removed at the end.
- The server log, the evidence archives, the sampler files and the Ray snapshots kept in the folder.
- Three or more server starts: stage 3's four spread 1.5× to the first token and 2.3× a token at 128K, one at a time.
- More than two requests at 512K and 1M, warmed up.
- The report built from the files, with the queueing at 32 in flight stated.
- The decode check in 5.5, once.

## 6. Before the next full run

1. **Fix the stops at steps 2, 4 and 13** (blocker 5, N2, N1).
   - Steps 2, 19 and 20: drop the pkills. 14c and the runner stop their own servers; the runner starts each in its own session and kills that group.
   - Step 4: start the server under `setsid`, so it has a process group of its own, and stop it by that group; a background job started inside the step otherwise shares the master's group. Move the comparison into its own file.
   - Run `ray stop -f` as its own command, and give the Nsight driver's variable a default.
   - Build nccl-tests where `$BENCH_ROOT` points, or step 3 stops the run.
2. **Rewrite `scripts/RUN_CONFIG.env` on the VM, and move the NCCL unset, in one change** (N3, 5.7).
   - Write the four keys the helpers now write, and check the folder runs are started from for another `RUN_CONFIG.env`, which every reader takes first.
   - In the same change, unset `NCCL_ALGO` and `NCCL_PROTO` in the two-server runner and the NCCL policy, not only in the master: today the old file is what unsets them there, and the 20-minute helper goes straight to the runner.
   - Then make the runners stop reading the file after the master, or re-apply the master's unsets after their read.
3. **Decide the build:** vLLM 0.29.0, as every earlier set ran, or 0.31.0, as the TP4/PP4 run did.
   - Install it by file with its hash on both nodes, in one venv path, and set the readiness gate's expected versions and `setup_node_env.sh`'s pins to it; run the gate with `--out`, inside the venv, on both nodes, and stop the run on a failure (N4, N5, N9).
   - If it is 0.31.0, re-check this review's vLLM 0.29.0 facts on it (how Ray workers take their environment, the default splits and the split check, the two flags, autotune's default, what turning the communicator off does) and re-measure the reference points before comparing with earlier sets.
4. **Count failed cases** (blocker 7): read each step's case manifests, record the failures and fail the run at its end. Do not just make a step fail: `run_step` under `set -e` ends the run at the first failed step, which would be step 8, whose FP8 KV case has never started.
5. **Network** (blocker 9, N6): let the commands that apply a cap or loss fail, keeping the deletes tolerant; record `tc -s qdisc show` on both nodes into each condition's folder; measure the link both ways with iperf3; and remove caps in a trap in both helpers.
6. **Docs:** take `NCCL_ALGO=Tree`, `NCCL_PROTO=Simple`, `NCCL_CROSS_NIC=1` and the 15,12 split out of the READMEs, and correct the "+27.58% TTFT" claim, the smoke-test claim and the restart claim.
7. **The smoke test for real** (blocker 12, N8): one real server per pipeline size, and a verdict that fails when any check fails.
8. **The batching runner's node 1** (N7): start and stop Ray with the NCCL policy's exports, `$VENV_DIR` and the audit; give the TP4/PP2 cases `ray_gpus_per_node: 4`.
9. **Then the rest of v1.3:** the skip-list A/B; the start-up checks (the MoE backend line, the NCCL library each worker mapped); Nsight Compute; depth, mid lengths and network conditions on every two-node layout; warm-up seeds and profile warm-ups; step 12's comparison (N10) and step 15's tools (N11).

## 7. How this was checked

`audit/check_scripts_review_v14.py` reads the folder as shared and the zip (for the file modes). Given the folder v1.3 reviewed and the vLLM 0.29.0 wheel, it also reads what the v1.3-era helpers wrote, the old lines this review compares with, and the vLLM facts it uses. It asserts every statement this review makes about the code: 147 of 147. Its check IDs follow this review: B1–B13 for v1.3's blockers, F, K, C and S for 3.2–3.5, N1–N14 for the new findings; its last section lists them by item. Each section runs on its own, so a pattern that a later version removes shows as a failed check, not a crash. It runs none of the team's scripts. Its experiments, in a scratch folder, reproduce the mechanisms with snippets of their own, with the master's pkill pattern renamed so that nothing real is killed where it runs:
- E1, E1b, E1c: a `bash -c` body, step 4's clean-up and node 1's remote command in 14d, each killed by a pkill whose pattern is in its own text (status 137), with a server-like process killed too;
- E2: `run_step` under `set -euo pipefail` ending the run at that step;
- E3: `set -u` stopping a script on `[[ -n "$VAR" ]]` with `VAR` unset;
- E4: a required `--out` left out (exit 2 at argument parsing);
- E5: a `bash -c` body reporting only its last command's status;
- E6: the master's selection lines keeping a selection the config sets, and the steps it then skips;
- E7: a double-quoted `bash -c` body broken by a bare double quote in its heredoc.

As a control, run on the folder v1.3 reviewed (`audit/check_scripts_review_v14_control_out.txt`), every check behind an item this review calls fixed since v1.3 fails there or cannot be evaluated; the 47 that pass check what is still open or unchanged, and the experiments. v1.3's `check_scripts_review.py` no longer runs on this folder, since it reads fixed line numbers.

`audit/check_tp4pp4_run.py` reads the run's folder and, when given them, the pilot's, stage 2's and stage 3's TP4/PP4 folders, and prints every figure in section 5: 58 of 58. It reads the earlier sets' capture log archives in memory, without extracting them. With `--waves` it runs the pause screen from the folder given; this review used its own copy. Its `pip_waves.py` is the team's file byte for byte; the team's `pip_scan.py` adds the step-12 rule and Windows path handling, neither of which touches this run's paths. v1.3's `audit/coverage_matrix.py` runs on this folder unchanged; its output is `audit/coverage_matrix_v14_out.txt`.

```
python3 -I check_scripts_review_v14.py <Performance_Intelligence_Platform dir> <the zip as shared> <scratch dir> [--old <the folder v1.3 reviewed>] [--vllm-wheel <vllm-0.29.0 wheel>]
python3 -I check_tp4pp4_run.py <data/results dir> [--pilot <pilot vllm_scaleout_network_matrix dir>] [--stage2 <stage 2 03_multi_node_load dir>] [--stage3 <stage 3 07_r3_network_resilience dir>] [--waves <pause screen dir>]
python3 -I coverage_matrix.py <Performance_Intelligence_Platform dir>
```
