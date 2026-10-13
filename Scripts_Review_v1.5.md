# Performance Intelligence Platform scripts: v1.4's comments, checked in the new code

*v1.5 · 13 Oct 2026 · for the team that maintains the scripts · v1.5 checks each comment in v1.4 against the folder shared on 13 Oct (8 am), lists what is new, and answers whether a full run can start*

*Scope: the folder as shared (220 files, zip md5 726a1b6e…), read against the folder v1.4 reviewed (214 files): 6 files added, 31 changed, 5 of them docs. Statements about vLLM's own behaviour come from the vLLM 0.29.0 wheel, as in v1.3 and v1.4, and are marked "(vLLM 0.29.0)". Every statement about the code is asserted by `audit/check_scripts_review_v15.py` (177 checks, all pass). It runs none of the team's scripts; its experiments (E1–E12) reproduce each mechanism with snippets of their own. Item numbers follow v1.4's: blockers 1–13 and coverage fixes 1–8 from v1.3, v1.4's findings N1–N14; the new findings are N15–N25. Three independent passes over drafts of this review found errors and gaps; each was checked against the files and corrected.*

## 1. In short

- **Ready to run end to end: yes for the master, once three things are done.** No step stops a default run any more. The stops v1.4 found are fixed (the self-kills in steps 2, 4, 19 and 20, step 4's broken quoting, step 13's unset variable), and step 3 without nccl-tests now marks the run FAILED instead of ending it. Each step's failure is recorded and the run goes on, and it ends with an audit of the case manifests that fails it when a case or step failed. The three things (section 2):
  - fix step 11, whose 15,12 arm now silently runs vLLM's default split (N15);
  - on the VMs, rewrite the old `RUN_CONFIG.env` if it is still there, and check that its `VENV_DIR` names the venv holding the build;
  - decide the build and check it on both nodes, with iperf3 and Nsight Systems installed, which the gate also requires: run step 0 alone first and read its two readiness reports, since the gate still does not stop the run.
- **Expect two things that are not the run's fault.** The smoke test now fails on a healthy node, since its vLLM check reads a help page that lists no flags (N19, vLLM 0.29.0); the cluster set-up helper stops on it. And unless its cause is fixed, step 8's FP8 KV case will most likely fail to start as it did in the second campaign, so the campaign will end FAILED on that case; this time its server log is kept.
- **v1.4's 56 items** (the 42 carried from v1.3, and N1–N14): 23 closed, 24 partly, 9 open. Of the 42, v1.4 had 16 closed, 14 partly and 12 open; now 20, 14 and 8.
- **Fixed since v1.4,** besides the stops: the master exports the node addresses, key and venv and takes them as flags; the runners undo what made the old `RUN_CONFIG.env` stop servers; `VLLM_DISABLE_PYNCCL` is unset everywhere and no longer forwarded; `LD_LIBRARY_PATH` no longer gains an empty entry from the scripts; the batching runner's node 1 gets the clean NCCL path and the TP4/PP2 cases ask 4 GPUs a node; the network labels follow each condition; both helpers remove their caps in a trap; warm-ups have their own seed and are judged by their log; the smoke test fails when a check fails; the runner library is one version everywhere; the 07/ master finds its files.
- **Still open or partly,** in short: what a run records about itself (silenced `tc` errors, no link measurement, no NCCL library or MoE line checked at start-up); the build's pins, which still fall back silently; the smoke test, which still runs no server; docs that still recommend `NCCL_ALGO=Tree`, the "+27.58%" split claim and the restart claim; the copies; and the coverage gaps (Nsight Compute, depth, mid lengths, network conditions on every layout).
- **New:**
  - step 11's split A/B is void (N15);
  - the 20-minute helper stops before its run (N16);
  - the end audit misses several kinds of failure, so a PASSED summary is not proof (N17);
  - the runners keep the file's node addresses over the master's new flags (N18);
  - the smoke test fails on a healthy node, and once fixed never reaches its top verdict (N19);
  - step 12's comparison reads warm-up manifests as points (N20);
  - step 15's aggregation comes out empty, or not at all (N21);
  - a topology selection empties step 12 (N22);
  - new files outside the run: a dashboard page whose hardware and latency claims contradict the run's records, its metrics, and a timing estimate for another model (N23);
  - missed by earlier reviews: the two-server Nsight driver deletes node 1's sampler after its first capture (N24), and step 3's summary reads keys nccl-tests does not write (N25).

## 2. Ready to run end to end?

### 2.1 The answer

Yes. Started with `--new-run` (or with no options, when no earlier run is recorded) and the default profile, the master now goes from step 0 to its end. `run_step` records each step's status in `master_step_status.jsonl`, marks a step done only when it returns 0, lists failed steps and always returns 0; the master's own exits are its help, an unknown flag or profile, and its end. After the last step it reads the case manifests it finds under the run (N17 lists what it misses), writes `CAMPAIGN_SUMMARY.json`, and exits 1 if a case or a step failed.

Before the full run, three things. Without them the run completes, but some of its results are wrong or not comparable with earlier sets:

1. **Step 11 (N15).** Its 15,12 arm passes the split through the environment, and the two-server runner now unsets it, so both arms run vLLM's default. Save the caller's split before the runner's re-read and put it back after the unset, as the runner already does for eight other values. Add the split, or the folder, to the summarizer's rows too: without it, step 11's summary cannot tell its two arms apart even once they differ.
2. **`RUN_CONFIG.env` on the VMs.** If the file the v1.3-era helpers wrote is still there, it now shrinks the run: its TP4/PP4-only selection pins the master and, through the runners' new filter, step 10 runs only TP4/PP4 and step 12 nothing, while steps 4, 11 and 13 are skipped and steps 2 and 14 drop their single-node TP8 captures; its cap label goes on step 10's runs, and its skip list replaces arm B's empty one (N3). Rewrite it with the four keys the helpers write now. Check its `VENV_DIR`: on a VM set up before, the helpers point runs at `~/pip_vllm_env` while `setup_node_env.sh` now installs into `~/vllm_env` (blocker 10).
3. **The build.** The readiness gate expects vLLM 0.29.0, Ray 2.58.0, torch 2.13.0, Triton 3.7.1, FlashInfer 0.6.18 and NCCL 2.29.7 or 2.31.2 (or a library in the clean folder); the TP4/PP4 run in the data folder used vLLM 0.31.0, FlashInfer 0.7.0.post1 and Ray 2.59.0. Decide which, install it the same on both nodes, and check it before the run (2.3). If it is 0.31.0, change the gate's versions and `setup_node_env.sh`'s pins to it, and re-check this review's vLLM 0.29.0 facts on it. The gate also requires iperf3 and Nsight Systems (`nsys`) on each node, and neither `setup_node_env.sh` nor the runbook installs them (01's node-preparation script installs iperf3): without them the gate reads FAIL whatever the build, and without `nsys` on node 0, step 13 fails and step 14's Nsight captures are lost quietly.

Then, cheap and worth doing before the run:

- Build nccl-tests under `$BENCH_ROOT` (`$HOME/platform_bench_suite` with the example, `$HOME/rtx_g4_smoke` without it), or step 3 fails and the campaign ends FAILED on that step. 01's node-preparation script, which the master does not call, builds them there and installs iperf3: run it on both nodes with the `BENCH_ROOT` step 3 will use and `PEER_IP` set to the other node's address. It stops at the first step that fails, and it builds nvbandwidth first, so check afterwards that `nccl-tests/build/` holds `all_reduce_perf` and `sendrecv_perf`, the two step 3 runs. And fix step 3's summary keys (N25), or read its raw logs.
- Move the Nsight driver's sampler copy into its loop (N24), or 18 of the 21 two-server Nsight runs come back without node 1's GPU telemetry.
- Until N17 is fixed, read the step folders, not just `CAMPAIGN_SUMMARY.json`: a PASSED summary can hide failed warm-ups, profiles and runners that stopped early. And expect a FAILED one from step 8's FP8 case unless its start is fixed: read its server log in `step08_fp8_kv_rerun/tp4_fp8_kv_fixed/server.log`.
- Make step 12's network conditions checkable: let the commands that apply a cap or loss fail, write `tc -s qdisc show` from both nodes into each condition's folder, and measure the link with iperf3 under each condition (blocker 9). As shared, a cap that did not take effect looks the same as one that did.
- Do not gate on the smoke test until its vLLM check reads `--help=all` (N19); like the gate, it now also requires iperf3.
- Do not use the 20-minute helper until N16 is fixed: it stops before its run.

### 2.2 What a default run does now

*On a new run id, with a `RUN_CONFIG.env` holding the node addresses (the helpers' four keys, or one made from the example), and nccl-tests built.*

| Step | As shared |
|---|---|
| 0 | Records both nodes' environments, node 1's inside the venv, and runs the readiness gate on both nodes with `--out`. A failed gate does not stop the run; node 1's full report stays in its `/tmp`, only its summary line comes back (N4) |
| 1 | The chunk A/B on TP4/PP1; marked done on the summarizer's status (blocker 7) |
| 2 | The four torch captures (TP4 and TP8, 8K, 8 and 32 in flight), 3 s apart; no pkill any more |
| 3 | With a node 1 address, the NCCL socket sweep. Without the nccl-tests binaries it exits 1: the step is recorded as failed and the campaign ends FAILED, but the run goes on. With them, its summary's two figures are null for every variant (N25) |
| 4 | The TP8 pinning A/B: the server in its own process group, stopped by that group (E1), the comparison in `tools/`; runs to its end now. Reports 3 if its server dies at start |
| 5–9 | Run. Step 8's FP8 KV case failed to start in the second campaign; if it does again, the end audit counts it failed (its summary is behind `\|\| true`) |
| 10 | The load grid on the four two-server layouts, 32 admitted, after clearing both nodes' caps |
| 11 | Both arms run vLLM's default split (N15) |
| 12 | The four conditions on TP16/PP1 and TP4/PP4, now labelled per condition; `tc` errors silenced, the qdisc in the master log only, no link measurement (blocker 9); its comparison as in N20 |
| 13 | The two-server Nsight capture of TP16/PP1's 512K prefill now runs (N1 fixed). The driver exits 2 without nsys, Ray or vLLM on node 0; on node 1 only the vLLM lookup counts, and a failed capture still ends it 0 |
| 14 | The single-node Nsight and torch captures; 20 two-server Nsight runs, 12 eager and 8 with graphs on (with step 13's, 13 captures in 21 runs), all but the first of each call without node 1's GPU telemetry (N24); the two-server torch traces on four layouts |
| 15 | The aggregation reads the run now, but its figures come out 0, or it writes nothing (N21) |
| 16 | The pause screen and the bench summary |
| 17 | Skipped unless `--cb-blocks` is given (or `CB_BLOCKS` set) |
| 18–20 | Only with `--profile deep-profile` (or `--step 18` to `20`) |
| End | Reads the case manifests, writes `CAMPAIGN_SUMMARY.json`, exits 1 on a failed case or step; misses the failures listed in N17; on a failure the closing banner is skipped (E5) |

### 2.3 How to start it

Run step 0 alone, read the two readiness reports, then let the same run go on from step 1:

```
bash scripts/run_master_benchmark.sh --new-run --step 0
#   read <run>/env/node0_readiness/PLATFORM_READINESS.md, <run>/env/node1_readiness.txt
#   and <run>/env/node0_python_stack.txt, node1_python_stack.txt (versions on each node)
nohup bash scripts/run_master_benchmark.sh > master_stdout.log 2>&1 &   # resumes that run id; step 0 is skipped as done
```

Start the second so that it outlives the SSH session, with `nohup` as above (as the setup guide does) or in tmux: on its own, the master ends when the session drops. It also writes everything to `<run>/logs/MASTER_BENCHMARK_RUN.log`. The second command picks up the run id from `latest_run_id.txt`, which the first wrote; `--run-id <id>` names it outright, should anything else write that file in between (the 20-minute helper does, once it runs). Step 0 is marked done even when a gate fails, so to check again after a fix, run the first command again (a new id). Node 1's full report is in its `/tmp/node1_readiness/`; its clean-folder checks run only if node 1's own login sets `NCCL_NET=Socket` or puts the folder on `LD_LIBRARY_PATH`. Use `--new-run` for any fresh run: `--no-resume` keeps the latest run's folder and re-runs every step into it, so the end audit counts the old manifests with the new ones.

## 3. v1.4's items, one by one

*Closed: done as v1.4 asked. Partly: the problem is smaller; what is left is named. Open: the problem still stands.*

### 3.1 Blockers 1–13

| # | v1.4 | Status | Now, and what is left |
|---|---|---|---|
| 1 | The scripts are not executable | Closed | All 49 `.sh` files carry the bit in the zip. The master runs 6 of them directly, not through `bash`, from 20 places: if a copy drops file modes, steps 3 and 13 are recorded as failed (exit 126), and steps 2, 10–12 and 14 lose those calls quietly |
| 2 | The `bash -c` bodies cannot see the master's state | Closed | The master now exports the node addresses, the SSH key, the venv, the run root and id, and the dry-run and resume switches; it takes `--node0-ip`, `--node1-ip`, `--ssh-key` and `--venv-dir`, and defaults node 0's address to the first entry of `hostname -I`. The runners do not keep these flags against a `RUN_CONFIG.env` that sets them (N18) |
| 3 | Files the scripts need are missing; one copy from one place | Partly | The runner library is now one version in all 7 places, each with the success check and without the old `pkill -9 -f "vllm"`. Left: the copies (outside the old `rtx_g4_*` folders the sampler is in 5 places, the runner library in 6, the Ray audit in 3 with 2 versions; the runners' copies agree, the one in 01/ differs and nothing calls it), and no start-up check that the files a step calls exist |
| 4 | One layer split for every server | Partly | vLLM's default everywhere: the master unsets it, no example or helper sets it, and the two-server runner, the Nsight driver and 14d unset it after their re-read, so an old `RUN_CONFIG.env` can no longer bring 7,7,7,6 back. The READMEs now unset it, the setup guide's settings list says it is left unset, and the runbook's smoke-test line matches what the test checks. Left: the setup guide's own smoke-test list still says the test validates `VLLM_PP_LAYER_PARTITION=15,12`, and `README.md` still describes TP8/PP2 as a 15/12 split; and step 11's 15,12 arm, the one place meant to set a split, now cannot (N15) |
| 5 | `pkill -f` kills its own caller | Closed | No step body calls pkill; steps 2, 19 and 20 wait 3 s between captures; step 4 starts its server with `setsid` and stops its process group (E1); 14d and the 20-minute helper have none. Left: 14c's own pkill, `vllm.*port.*$PORT`, which targets its server; neither step that calls 14c has "port" in lower case in its text, so it cannot match their shells unless a folder path supplies the word. The runner library's drain barrier and the master's new `kill_orphan_workers` hold pkills too, but nothing calls them |
| 6 | A failed case ends its group | Closed | The two-server runner records a failed case and carries on, as v1.4 found. Left: a failed `ray start`, `ray status`, Ray audit or sampler copy still ends the group under `set -e`, now with no case manifest for the end audit to count (N17) |
| 7 | Steps report success when their runs fail; resume | Partly | `run_step` records each step's status, marks it done only on 0, lists failed steps and never stops the run; the end audit fails the run on a failed case or step. Left: a step's status is still its last command's: 9 of the 19 bodies end with `\|\| true`, an echo or an `if` block and report 0 (step 4 reports 3 if its server dies at start), and 8 report the summarizer's; `\|\| true` appears 70 times in the bodies (23 in step 12). So, apart from steps 3 and 13, which report their own scripts' status, failures count mostly through the manifests, and the audit misses several kinds (N17). Resume is on by default, and `--no-resume` re-runs into the latest run's folder |
| 8 | `RUN_CONFIG.env` overrides the command line | Partly | The master reads it before the flags; both examples, now one file in two places, default their five selections to `all` and their network labels with `${VAR:-...}`, so a caller's value survives a re-read; the two-server runner, the Nsight driver and 14d save the caller's values (8, 4 and 9 of them) before their re-read and put back those that are not empty. Left: `--topologies all` and `--bandwidth all` still export nothing, so a selection a file sets stays (E6); the runners keep neither the master's addresses, key and venv (N18) nor an empty skip list (3.3); the NCCL sweep saves nothing; and the example still sets `RUN_HEAVY_PROFILE`, the three sweep switches, the MoE variables and the NCCL interface outright, so an environment variable cannot change them: the sweeps and `RUN_HEAVY_PROFILE` have a flag (`--profile deep-profile`), while the MoE variables and the NCCL interface have none, so only an edit to the file changes them |
| 9 | The network conditions are not applied as labelled | Partly | The mode, cap and provenance labels step 12 passes now survive the runner's re-read, so each condition's cases are labelled as intended; both helpers remove their caps in a trap. Left: the 6 `tc` commands that apply a cap or loss still silence their errors, as do the 12 deletes, so nothing confirms a cap took effect; the qdisc goes to the master log only, not into each condition's folder; nothing measures the link (no iperf3, and the network matrix script with its iperf3 checks is still not called); each condition's top-level manifest reads its mode from a variable nothing on the master's path sets, so it says native under every condition |
| 10 | The build is not pinned | Partly | `setup_node_env.sh` now defaults to the master's venv, `~/vllm_env`, links `~/pip_vllm_env` to it when that name is free, and writes `pip freeze` into the venv; step 0 runs the gate on both nodes (N4). Left: every pin still falls back silently (vLLM 0.29.0 with Ray 2.58.0 to `vllm>=0.6.3` with any Ray, FlashInfer 0.6.18 to any, torch 2.13.0 from the CUDA 12.4 index to torch 2.5.1); vLLM 0.29.0 pins torch 2.13.0 and FlashInfer 0.6.18 itself, so when its pin installs, the torch line does not decide torch. No install by file or hash. The gate does not stop the run. Both helpers still prefer `~/pip_vllm_env` when it exists, so on a VM set up before, `setup_node_env.sh` run with its defaults installs into `~/vllm_env` while the `RUN_CONFIG.env` the helpers write points the run at `~/pip_vllm_env`. The setup manual still lists Ray 2.35.0 and Triton 3.0.0, the runbook torch 2.5.1. Which build, 0.29.0 or 0.31.0, is still undecided |
| 11 | The batching suite cannot run its two-server cases | Partly | Node 1 now activates `$VENV_DIR`, puts the clean NCCL folder first on `LD_LIBRARY_PATH` and unsets `NCCL_ALGO`, `NCCL_PROTO` and `VLLM_DISABLE_PYNCCL` before `ray start`; its `ray stop` uses the venv; the three TP4/PP2 cases ask 4 GPUs a node (the runner falls back to 4 for TP4/PP2); the case manifest records both nodes. Left: no Ray audit, and node 1's ray start carries none of the NCCL policy's exports. A Ray worker fills in the driver's variables where its own node's environment has none (vLLM 0.29.0), so node 1's ranks take node 0's NCCL settings and skip list unless node 1's own login sets them |
| 12 | The smoke test proves nothing | Partly | It now exits 1 and reports "DEPLOYMENT BLOCKED" when any check fails. Left: on a healthy node its vLLM check now fails (N19), so it blocks; its end-to-end check still writes `bench.json` without a server (N8); its new `--live-server` flag ("Launch real micro-server test") sets a variable nothing reads; of its 21 checks, four test values written into the test itself, its context check always warns, and its batching check passes whenever the file parses (N19); it fails arm B of the skip-list A/B (3.3); the runner check is still a dry run, and the wave check still passes without running when its test file is absent |
| 13 | Some 1M prompts do not fit; failed points | Closed | Every 1M prompt fits, and a point fails on a non-zero exit or too few completions. A warm-up now also fails when its log holds "All requests failed", which vLLM 0.29.0 prints when every request fails while exiting 0 (its ready check is off by default). Its other two tests ("Zero completed requests", and "failed_requests" with "successful_requests: 0") never match vLLM 0.29.0's output, so a warm-up where only some requests fail passes; vLLM prints "Failed requests during benchmark run detected" then, which the check could look for |

### 3.2 The footing: one build, one set of settings

| Item | Status | Now, and what is left |
|---|---|---|
| MoE backend: `--moe-backend flashinfer_cutlass` on every launch, checked at start-up | Partly | Unchanged: the runners add the flag and `--enable-flashinfer-autotune` only when vLLM's help lists them; the only server-log line any runner reads is the KV cache size, so nothing checks the line naming the MoE backend |
| Autotune set explicitly | Closed | The flag on every launch. `VLLM_FLASHINFER_AUTOTUNE=1` and `VLLM_MOE_BACKEND` are still exported by the master, the examples and the smoke test; vLLM 0.29.0 reads neither |
| The Ray workers' environment: 14d | Closed | Unchanged; the batching runner as blocker 11 |
| `VLLM_DISABLE_PYNCCL` out everywhere | Closed | Set nowhere; unset by the master, the NCCL policy, the two-server runner, the Nsight driver, 14d, the 20-minute helper, the examples and the batching runner's node 1; no longer in the list the policy forwards to node 1. The split is still in that list, but every runner unsets it first |
| Layer split: vLLM's default | Partly | Done in the scripts (blocker 4). The "+27.58%" claim for 15/12 is still in 5 docs (7 places): `README.md`, `scripts/README.md`, 04's README, `data/raw_runs/README.md` and `PIP_MASTER_RESULTS_AND_BENCHMARKS.md`; the setup guide dropped it |
| The NCCL library | Partly | The scripts no longer add an empty `LD_LIBRARY_PATH` entry (N12). Left: nothing records the library each worker mapped, or `torch.cuda.nccl.version()`; the clean folder is still made on node 1 only where GIB is installed, with errors silenced |
| Docs against code | Partly | `README.md` and `scripts/README.md` no longer export `NCCL_ALGO=Tree`, `NCCL_PROTO=Simple` or `NCCL_CROSS_NIC`, and 04's README says the two are left unset. Left: `README_SETUP_AND_OPERATIONS.md` (4 places, one asking for it in `RUN_CONFIG.env`) and `README_FILES_AND_ARCHITECTURE.md` (3, one claiming 28.4% less cross-node AllReduce latency) still recommend `NCCL_ALGO=Tree`. Every script that starts servers and reads `RUN_CONFIG.env` now unsets it after the read, and the others do not read the file, so a run's servers are safe from it; a server started by hand from those docs is not. The claim that the server restarts between concurrency levels is still in the master's header (both copies), `README.md`, `scripts/README.md`, 02's and 04's READMEs and `RUN_COVERAGE.md`, two of them with `pkill -9 -f vllm`; the runners keep one server for all of a case's points, the drain barrier is called nowhere, and no script writes the `cache_state` tag those READMEs describe |
| Admission caps | Closed | The load grid admits 32 at once, the network-condition cases 16; the 20-minute helper now runs the load grid's TP4/PP4 case |

### 3.3 The autotune skip list

| Item | Status | Now |
|---|---|---|
| The `-` form, so arm B's empty value stays empty | Closed | The master, the two-server runner, both examples and the smoke test |
| Node 1's own export in the two-server runner | Closed | Unchanged |
| The single-node runner | Closed | Keeps a value that is set, empty included |
| The helpers rewriting `RUN_CONFIG.env` | Closed | They write only the four keys, and only when the file is missing |
| The A/B itself | Open | Not run. Three things now stand in its way: the smoke test's MoE check fails an empty list; the two-server runner puts the caller's list back after its re-read only when it is not empty, so a file that sets the list replaces arm B's empty value; and in the batching runner's two-server cases, node 1's ranks get the empty list only if node 1's own login sets none (blocker 11) |

### 3.4 Coverage fixes 1–8

*The master's cases file and the profile matrix are unchanged since v1.4, and v1.3's coverage matrix prints the same output on both folders.*

| Fix | Status | Now |
|---|---|---|
| 1. Run the two baselines and the TP4 curve | Closed | Step 6 |
| 2. Select the profiles that are defined | Closed | And now they run: N1 is fixed |
| 3. Graphs on for two-server Nsight | Closed | Step 14's second call, which now runs |
| 4. Nsight Compute on 8 and 16 GPUs | Open | Nothing uses Nsight Compute |
| 5. Depth | Partly | Unchanged: the load grid admits 32; 512K and 1M still rest on 2–8 requests; repeats only on TP4/PP1's knee case |
| 6. Mid lengths on two nodes | Open | The load grid is still 1K, 8K, 128K, 512K and 1M |
| 7. Network conditions on every two-node layout | Open | Still TP16/PP1 and TP4/PP4 only, at 128K with 1 and 4 in flight |
| 8. What is not covered | Open | Two TP4/PP1 servers side by side, prefix caching on two servers, the expert-parallel run |

### 3.5 Smaller points

| Point | Status | Now |
|---|---|---|
| Step 15's tools | Partly | The aggregation reads the run and writes into it; the dashboard string check is out of the run. Its figures come out 0, or it writes nothing (N21) |
| Step 20 compares different workloads | Closed | Unchanged: the same 8K workload, minimal and full telemetry |
| Two master runners | Closed | Identical copies; the 07/ copy now takes its suite root from `scripts/`, so it finds 05/, `pip_scan.py` and the cases file |
| The setup manual's Ray 2.35.0 and Triton 3.0.0 | Open | Unchanged |
| Step 11's rows carry neither the folder nor the split | Open | The summarizer is unchanged; the case manifest records the split, which is now always the default (N15) |
| `step12_capped_profiles` and the pause screen | Closed | Unchanged |
| The profile runs send no warm-up | Open | All four profile paths (14, 14c, 14d and the two-server Nsight case) still send none |
| A warm-up shares its measured run's seed | Closed | A warm-up's seed is now (seed + 9999) mod 100000 |

In all, of the 42 items in these five tables: 20 closed, 14 partly, 8 open.

### 3.6 v1.4's new findings, N1–N14

| N | v1.4 | Status | Now, and what is left |
|---|---|---|---|
| N1 | The two-server Nsight driver stops on an unset variable | Closed | The default line is back before the variable is read; steps 13 and 14's two-server Nsight runs can run |
| N2 | Step 4's comparison breaks the step's quoting | Closed | The comparison is now `tools/compare_numa_pinning.py`; bash receives step 4's body as one word, and no step's string closes before its body ends |
| N3 | The old `RUN_CONFIG.env` stays in force | Partly | What made it stop servers and turn the communicator off is undone after every runner's re-read: the two-server runner saves the caller's values, reads the file, then unsets the split, `VLLM_DISABLE_PYNCCL`, `NCCL_ALGO` and `NCCL_PROTO`; the Nsight driver and 14d do the same. Left, if the old file is still on the VM: its TP4/PP4-only selection pins the master (E6) and now filters the runners too, so steps 4, 11 and 13 are skipped, step 2 skips its two TP8 torch captures, step 10 runs only TP4/PP4, step 12 runs its 20G condition with neither of its cases (E10), step 14 skips its single-node TP8 Nsight capture and keeps only TP4/PP4's two-server torch trace, while its two-server Nsight runs ignore the selection; step 10 passes no cap label, so the file's 20 stays on step 10's native runs; the policy forwards every `NCCL_*` variable but the local-transport ones and the two above, so its `NCCL_CROSS_NIC=1` reaches node 1; its skip list replaces an empty one (3.3); its `MODEL` and `REVISION` replace `--model` and `--revision` in the two-server runner and the Nsight driver; and its old `LD_LIBRARY_PATH` line adds the folder again at each re-read. The helpers still keep an existing file as it is: rewrite it |
| N4 | The readiness gate never runs | Partly | Step 0 runs it with `--out` on both nodes, node 1's inside the venv; node 0's report lands in `env/node0_readiness/`, node 1's summary line in `env/node1_readiness.txt` (its full report stays in node 1's `/tmp`). Left: both calls are behind `\|\| true`, so a failed gate (exit 2) does not stop the run, and step 0 is still marked done; node 1's clean-folder checks run only when node 1's own login sets `NCCL_NET=Socket` or the folder on its path |
| N5 | Node 1's step-0 checks run outside the venv | Closed | Both remote `python3` commands activate `$VENV_DIR` first, and step 0 copies the gate to node 1 |
| N6 | The two set-up helpers | Partly | The cluster set-up gives `SSH_KEY` a default, reads `RUN_CONFIG.env` whenever it exists (the command-line address wins), removes both caps in its EXIT trap, a failing smoke test included, and clears the trap before it hands over to the master; with `--run-benchmark`, the runner now keeps only the TP4/PP4 case. The 20-minute helper uses `sudo -n`, removes its caps in a trap, runs the load grid's TP4/PP4 case and unsets `NCCL_ALGO`, `NCCL_PROTO` and `VLLM_DISABLE_PYNCCL`. Left: the cluster set-up now stops at its smoke test on a healthy node (N19), so `--run-benchmark` is not reached; once it is, that run is uncapped and labelled native, since step 10 clears the caps, under a banner that says 20 Gbit/s (`--bandwidth` reaches only step 12), and it resumes the latest run, so a step 10 already done there is skipped; the 20-minute helper stops before its run (N16), still takes node 0's address from `hostname -I`, and keeps its six-part header and its "FlashInfer CUTLASS (Autotuned)" banner while it runs one case; neither measures the link; both helpers' fallback to `id_rsa` never changes the key (E8), harmless since ssh then tries its default keys |
| N7 | The batching runner's two-node cluster | Partly | As blocker 11 |
| N8 | The smoke test's end-to-end check looks measured | Open | Still no server: its `bench.json` now holds a first-token time of two clock reads plus 0.045 s, a fixed 5.0 ms a token and status COMPLETED, and the check passes when the file exists |
| N9 | `setup_node_env.sh`'s pins fall back silently | Partly | `pip freeze` is now written into the venv; the fallbacks are unchanged (blocker 10) |
| N10 | Step 12's comparison sets unlike points side by side | Partly | Now `tools/compare_resilience_matrix.py`: it matches points by benchmark name across all four conditions and adds time per token. Left: it reads each warm-up manifest and each Ray audit file as a point (N20), and computes the change only for 0.05% loss against native |
| N11 | Step 15's tools do not read the run | Partly | As step 15's tools in 3.5 (N21) |
| N12 | `LD_LIBRARY_PATH` ends in an empty entry | Partly | The scripts now build it with `${LD_LIBRARY_PATH:+:...}` (the master, both examples, both READMEs, the batching runner's node 1), so they add no empty entry, and the master skips the folder when it is already there. But v1.4 put the TP4/PP4 run's trailing ":" down to the old form, and that was wrong: it comes after the CUDA entries, which no script adds, so it was in the nodes' own path, and the new form keeps it. The examples' line has no guard, so with an example-based file the master plus one re-read give the run's recorded string again, duplicate folder included (E11). Left: drop empty entries and duplicates, in one place |
| N13 | The copies drift, and the 07/ master misses files | Partly | The 07/ master now finds every file; the runner library is one version. Left: the copies themselves (blocker 3) |
| N14 | Smaller | Partly | The example's batching help shows its three examples again, and `export CB_BLOCKS` stays commented out. The zip still carries 256 macOS metadata entries (`__MACOSX/`); the `.DS_Store` files are gone |

Of N1–N14: 3 closed (N1, N2, N5), 10 partly, 1 open (N8). With the 42 above: 23 closed, 24 partly, 9 open.

### 3.7 The agreed feedback, item by item

*Written: in the scripts. Runs: in a default run as shared, with nccl-tests built.*

| Item | Written | Runs | Note |
|---|---|---|---|
| One vLLM build, pinned and recorded on both nodes | Partly | Partly | The gate runs on both nodes but does not stop the run; pins fall back silently; build undecided |
| MoE backend by flag on every launch, checked at start-up | Partly | Yes, unchecked | No start-up check |
| Autotune set explicitly | Yes | Yes | The skip list waits for the A/B |
| The clean-folder NCCL library on every worker, mapped library recorded | Partly | Partly | Now on the batching runner's node 1 too; the mapped library not recorded |
| NCCL check on the servers to be used | Partly | Partly | Step 3's socket sweep only, which needs nccl-tests and whose summary's figures are null (N25) |
| Expert-parallel start-up check | No | No | |
| Steady-arrival runs on two servers | Yes | With `--cb-blocks` | Batching block 7; node 1 now has the NCCL path |
| One request at a time below 128K on two servers | Yes | Yes | Step 10, 1K and 8K |
| Two servers under load | Yes | Yes | Step 10, 32 admitted |
| Decode profiles on two servers | Yes | Yes | Torch on four layouts; Nsight: 13 captures in 21 runs, eager and with graphs on, now that N1 is fixed |
| Nsight Compute kernel captures | No | No | |
| Repeats with a spread | Partly | Yes | TP4/PP1's knee case only |
| Network conditions applied and recorded | Partly | Partly | Labelled per condition now; errors silenced, the qdisc in the log only, no link measurement |
| Both nodes' logs kept | Partly | Partly | Node 1's GPU telemetry comes back from the serving runners, but from only 3 of the 21 two-server Nsight runs (N24); the Nsight driver keeps both nodes' Ray logs, the serving runners none |
| Warm-ups | Partly | Yes | Own seeds and judged by their log now; otherwise as v1.4 found, and none before the profiles |
| Pause screen | Yes | Yes | |
| Two long prompts, step budgets, request caps and mixed traffic beyond TP4/PP1 | Yes | With `--cb-blocks` | Batching blocks 1–4; the TP4/PP2 cases now on two nodes |
| First-repeat rule at 1M | Partly | No | Unchanged |
| Two TP4 copies on one server; prefix caching beyond TP4/PP1 | No | No | |
| Coverage on 8 and 16 GPUs | Partly | Partly | Baselines and profiles selected; mid lengths and depth missing |
| The split A/B (15,12 against the default) | Yes | No | Both arms run the default (N15) |

## 4. New findings

N15. **Step 11's 15,12 arm runs vLLM's default split.** *Effect: step 11's A/B is void.*
   - *Where:* step 11 passes `VLLM_PP_LAYER_PARTITION='15,12'` to the two-server runner only through the environment. The runner's new prologue saves eight caller values, not this one, re-reads `RUN_CONFIG.env`, and then unsets the split (line 30), before it builds the split it exports to both nodes (line 105).
   - *What happens:* both arms run TP4/PP2 and TP8/PP2 at vLLM's default split (14/13 at PP2, vLLM 0.29.0), and the 15,12 arm's case manifest records `default_14_13` (E2). The summarizer's rows carry neither the folder nor the split, so step 11's summary shows the same configuration twice, and the docs' "+27.58%" stays untested.
   - *Fix:* save the caller's split before the re-read (`CALLER_PP_SPLIT="${VLLM_PP_LAYER_PARTITION:-}"`) and put it back after the unset, as the runner does for its other caller values; a stale file's split is then still cleared, and step 11's is kept. Add the split (the case manifests hold it) or the folder to the summarizer's rows, so the summary can tell the arms apart.

N16. **The 20-minute helper stops before its run.** *Effect: the helper cannot run.*
   - *Where:* `run_20min_tp4pp4_campaign.sh` writes the qdisc to `"$OUT_DIR/node0_tc_qdisc_active.txt"` (line 90) and copies node 1's into `"$OUT_DIR/..."` (line 102), but sets `OUT_DIR` only at line 124; it runs under `set -euo pipefail`.
   - *What happens:* where ens3 exists, line 90 stops it with "OUT_DIR: unbound variable", right after node 0's cap is applied; where it does not, line 102 does. `2>/dev/null || true` does not catch an unset variable (E3). The EXIT trap then removes the caps, and the case never runs. The smoke test recommends this helper as its second next step.
   - *Once it runs,* its 20 Gbit/s run will be labelled cap 0 and mode native: it passes no labels, and the file the helpers write sets none. And it writes its own id into `latest_run_id.txt`, so a master resumed after it starts again from step 0, in a new, empty run folder under that id, instead of resuming its own run.
   - *Fix:* set `RUN_TIMESTAMP` and `OUT_DIR`, and create the folder, before step [2/4]; pass the cap and mode labels to the runner; leave `latest_run_id.txt` to the master.

N17. **The end audit can report PASSED when work failed.** *Effect: a PASSED summary is not proof.* It misses:
   - *Failed warm-ups* in the single-node runner (steps 1, 5, 6, 8, 9 and 18–20) and the batching runner (step 17): their case manifests carry no status, and the audit counts a case as failed only when it has an error or a point whose status is FAILED. A case whose failures were all at warm-ups counts as completed (E4): for example a server that dies during a warm-up, when every later point of the case warms up too. The two-server runner marks such a case FAILED, which the audit sees.
   - *The two-server Nsight cases* (steps 13 and 14): their manifest is `PROFILE_CASE_MANIFEST.json`, which the case-sensitive `*manifest*.json` does not match (E4), and the driver ends 0 whatever they did.
   - *Steps with no manifest:* steps 2 and 4, and step 14's single-node Nsight, torch and 14d captures, write none. Step 4 also sets an ERR trap in a shell without `-e`: if its control benchmark fails, the trap stops the server, the pinned run measures nothing, and the step still reports 0.
   - *Runners that stop early:* a two-server runner that stops before its first case manifest (the Ray start-up, the audit, the sampler copy: blocker 6) leaves nothing to count, and its exit status is lost, since steps 10 and 11 end with the summarizer and step 12 with an `if` block.
   - *Step 3 with nccl-tests built,* which ends 0 even if every `mpirun` failed (N25); and *the readiness gate* (N4).
   - Also: resume and `--no-resume` reuse the latest run's folder, so an earlier attempt's manifests are counted with the new ones; and the audit's exit 1 ends the master under `set -e` before `AUDIT_RC` is read, so the closing banner is skipped (E5).
   - *Fix:* count WARMUP_FAILED (and INCOMPLETE) as failed; match manifest names in any case; have step 4 and the shell profilers write a small manifest or return their failures; let a runner that stops before Ray forms record it, or have steps 10–12 return the runner's status; count the gate. Until then, read the step folders.

N18. **The runners keep the file's node addresses over the master's flags.** *Effect: two different node pairs in one run, when the two disagree.*
   - The two-server runner, the Nsight driver and 14d save the caller's selections, labels and paths before re-reading `RUN_CONFIG.env`, but not the node addresses, the SSH key or the venv; the NCCL sweep saves nothing. The file the helpers write sets all four. So when `--node0-ip`, `--node1-ip`, `--ssh-key` or `--venv-dir` differ from the file, the runners in steps 3 and 10–14 use the file's values, while the master's own commands (step 0, and the caps in steps 10–12) use the flags'.
   - They also look in other places. The master reads `RUN_CONFIG.env` from the folder it is started in, from `scripts/` or from the repository root; the runners from the folder they are started in, from `scripts/`, then from older copies in `$HOME`. With no file in the start folder or `scripts/`, the master and the runners can read different files.
   - *Fix:* save and restore those four too; or keep one `RUN_CONFIG.env`, in `scripts/`, that leaves out the addresses, key and venv, and pass them as flags.

N19. **The smoke test fails on a healthy node.** *Effect: it blocks, including the cluster set-up helper; once fixed, its verdict still misleads.*
   - Its vLLM check runs plain `vllm serve --help` and needs `--tensor-parallel-size`, `--pipeline-parallel-size` and `--distributed-executor-backend` in the output. In vLLM 0.29.0 plain `--help` prints only its usage line, description, the list of config groups and the epilog, with none of the three; the flags appear only with `--help=all` (vLLM 0.29.0). So on Linux the check fails, and the smoke test exits 1 with "DEPLOYMENT BLOCKED". The runners, the gate and the Nsight driver read `--help=all` first, so they are not affected. The cluster set-up runs the smoke test under `set -e`, so it stops at its step [4/5] and never reaches `--run-benchmark`.
   - It now also requires iperf3 on Linux (as the gate does), and neither `setup_node_env.sh` nor the runbook installs it (01's node-preparation script does, and the master does not call that script).
   - Once that check passes: its context check reads `input_tokens` and `output_tokens`, while the 160 points in the cases file use `input` (155 of them) and `output`, so it never sees a prompt length; and it warns whenever a case's step budget exceeds 8,192, which 4 cases do by design (the chunk-budget A/B's 8,448 and three 16K-step cases), so it always warns (E9). Any warning makes the verdict "SURROGATE QUALIFIED ... CLEARED FOR CLUSTER DEPLOYMENT", with the note that warnings reflect a local surrogate host; "100% PRODUCTION READY" needs none, so a healthy cluster node never gets it, and `--strict`, which turns warnings into failures, always fails.
   - Its batching check reads only the file's block names, never a stream, and the flag it computes is unused, so it passes whenever the file parses. Its MoE check exports the flags itself and then requires `gemm1` in the skip list, so it fails arm B (3.3). `--live-server` does nothing (blocker 12). Its Python search list holds a developer's Windows home path, and its report hard-codes two node addresses and the model.
   - *Fix:* read `vllm serve --help=all`; install iperf3 in `setup_node_env.sh` and the runbook; read `input` and `output`; drop the budget warning or exempt the cases that test the budget; check the streams' concurrencies; accept an empty skip list; give the end-to-end check a real server (blocker 12).

N20. **Step 12's comparison reads warm-up manifests and audit files as points.** *Effect: a point can come out empty.*
   - It keys each JSON file by `d.get("case_name")` or its folder's name. vLLM's result files have no `case_name` (none of the TP4/PP4 run's 16 has), so a result is keyed by its benchmark folder.
   - The runner writes `warmup_manifest.json` into that same folder, and the comparison does not skip it: the two share a key, and the one the folder lists last is kept, so a point can lose its first-token time (E7). The runner's `<case>_RAY_NCCL_ENV_AUDIT.json` at the top of each condition becomes a point named after the condition. The two layouts' benchmark names differ, so they do not collide with each other.
   - *Fix:* read only `<benchmark>/<benchmark>.json`, or skip `warmup_manifest.json` and `*_AUDIT.json`; key by case and benchmark.

N21. **Step 15's aggregation comes out empty, or not at all.** *Effect: its dashboard data is zeros, or missing.*
   - It now takes `--run-dir` and writes a copy into the run, but takes the first CSV a recursive glob finds there, in file-system order: any step's summary, step 13's GPU inventory or one of step 14's Nsight stats tables. It reads columns (`step_id`, `duration_seconds`, `num_total_requests`, `token_throughput_tps`, `ttft_median_ms`, `itl_p99_ms` and others) that no script in the suite writes; the summarizer's table in the TP4/PP4 run has 78 columns, none of them these.
   - So its totals and per-step tables are 0 or empty, and its raw records are one file's rows. If that first CSV is empty, which the summarizer writes for a step with no rows (as the second campaign's FP8 step shows), pandas fails and nothing is written, behind `|| true`. 16 GPUs and 1,536 GiB are still constants, and it still overwrites the repository's `dashboard/DASHBOARD_CANONICAL_DATA.json`.
   - *Fix:* join every step's `summary/vllm_runs.csv`, skipping empty ones; read the summarizer's column names (`mean_ttft_ms`, `mean_tpot_ms`, `output_throughput` and so on); take the GPUs from step 0's records; write into the run only.

N22. **A topology selection empties step 12.** *Effect: smaller; only with `--topologies`.*
   - The two-server runner now keeps a case only when a selected name is a substring of the case's name. Step 12's two cases are named `stage3_r3_network_jitter_tp16` and `stage3_r3_network_jitter_pp4`, so a selection written as the help shows it (`tp16_pp1`, `tp4_pp4`) keeps neither: the runner exits 2 ("No multi-node cases selected") under every condition, and step 12 runs nothing while still changing the caps (E10). Step 12 has no topology guard of its own to notice. Likewise `--topologies multi_node` passes step 10's guard but matches no case name, so step 10 would run nothing.
   - *Fix:* give each case a topology field (or derive it from its tp and pp) and filter on that; matching both ways, as the master's guards do, would not help here, since neither name is part of the other.

N23. **New files outside the run.**
   - `dashboard/index.html` and `data/results/tp4_pp4_20g_<timestamp>/tp4_pp4_20g_dashboard.html` are the same file (1,766,912 bytes, one md5): a dashboard page of the TP4/PP4 run. It shows `data/results/extracted_dashboard_metrics.json` (16 points), whose median ITL values match the run's result files; the TP4/PP4 report beside them is unchanged, its median ITL column still wrong in 14 of 16 rows. No step reads these files.
   - The page's text contradicts the run's records. It says the run used 16 RTX PRO 6000 Ada GPUs with about 768 GB of memory in all, decoding in under 10 ms throughout; the run recorded RTX PRO 6000 Blackwell Server Edition GPUs at 97,887 MiB each on node 0, and a mean time per token under 10 ms at 2 of its 16 points (7.43–752.03 ms). It calls its data "100% genuine". Correct these before the page is shown to anyone.
   - A new timing calculator for another model reads its input from a developer's Windows path, so it cannot run on the VM; it scales this run's durations by assumed factors (2.4–2.8×), and nothing calls it. Its figures are estimates, not measurements.
   - Unchanged but worth a line: the example sets four switches no script reads (cold/warm isolation, profile topologies, profile contexts, and metric percentiles, which vLLM 0.29.0 does not read either), beside the two that vLLM does not read (3.2).

N24. **The two-server Nsight driver deletes node 1's sampler after its first capture.** *Effect: 18 of 21 two-server Nsight runs lack node 1's GPU telemetry.* Missed by v1.3 and v1.4: the same lines are in both earlier folders.
   - *Where:* `18_run_vllm_multi_node_profiles.sh` copies the sampler to node 1 once (line 58), before its loop over captures (line 81), and deletes it inside the loop (line 188).
   - *What happens:* only the first capture of each call gets node 1's GPU telemetry: 3 of the 21 runs (step 13's one and the first of each of step 14's two calls). The remote start records no error (`nohup ... & echo $!` returns a PID either way), and each later run's `PROFILE_VALIDATION.json` reads `complete: false`.
   - *Fix:* copy the sampler inside the loop, or stop deleting it there.

N25. **Step 3's summary reads keys nccl-tests does not write.** *Effect: the NCCL sweep's summary has no figures, and a sweep whose runs all failed still ends 0.* Missed by v1.3 and v1.4.
   - Its summary reads `d["data"][...]["time_us"]` and `["busbw"]`; nccl-tests' JSON output holds `results[...]["out_of_place"]["time"]` and `["bus_bw"]`, as an earlier run's file shows. So both figures for every variant in `NCCL_TUNING_SUMMARY.json` are null (only the transport line, read from the log, is filled); the numbers are only in the raw logs and JSON files.
   - Each `mpirun` is behind `|| true` and the script ends with an echo, so with the binaries in place but `mpirun` failing, the step still reports 0.
   - *Fix:* read `results[*].out_of_place.time` and `bus_bw`, and drop the latency's fallback to `algbw`, a bandwidth; fail the step when a variant's JSON is missing.

## 5. Before the full run

*Must:* without these, the run completes but some results are wrong or not comparable.
1. **Step 11's split** (N15): save the caller's split in the two-server runner and put it back after the unset; add the split or folder to the summarizer's rows.
2. **`RUN_CONFIG.env` on the VMs** (N3, blocker 10): rewrite an old file with the four keys; check that its `VENV_DIR` is the venv holding the build, on both nodes.
3. **The build** (blocker 10, N4): decide vLLM 0.29.0 or 0.31.0; install it the same on both nodes; set the gate and the pins to it; install iperf3 and Nsight Systems on both nodes, which the gate requires; run step 0 alone and read both readiness reports (2.3). Better still, let a failed gate stop the run.

*Should:* cheap, and without them failures can hide or the evidence is thin.
4. **The end audit** (N17): count failed warm-ups, match manifests in any case, and give step 4, the shell profilers and early runner exits a record.
5. **Step 3** (N25): build nccl-tests under `$BENCH_ROOT` (01's node-preparation script does, and installs iperf3) and fix the summary's keys, or step 3 marks the campaign FAILED or reports no figures.
6. **The Nsight sampler** (N24): copy it to node 1 inside the driver's loop.
7. **Network evidence** (blocker 9): let the commands that apply a cap or loss fail, keeping the deletes tolerant; write `tc -s qdisc show` from both nodes into each condition's folder; measure the link with iperf3 under each condition.
8. **The smoke test's vLLM check** (N19), if the smoke test gates the run; and **step 8's FP8 case**: read its server log after the run, or take it out of the default run until its start is fixed, since a failed start marks the campaign FAILED.
9. **The 20-minute helper** (N16): move its `OUT_DIR` lines up before anyone uses it.

*Can follow the run:*
10. The runners keeping the master's flags (N18), which matters when the flags and the file disagree, or when the master and the runners find different files.
11. The rest of the smoke test (blocker 12, N8, N19); step 12's comparison (N20); step 15's aggregation (N21); topology names (N22); the dashboard page's text (N23); the library path's own empty entry (N12).
12. Docs: `NCCL_ALGO=Tree` in the two docs that still recommend it, the "+27.58%" claim, the 15,12 lines left in the setup guide and `README.md`, the restart claim in its seven places, the setup manual's and runbook's versions.
13. Then the rest of v1.3: the skip-list A/B (once the smoke test accepts an empty list and the two-server runner keeps one, 3.3); the start-up checks (the MoE backend line, the NCCL library each worker mapped); Nsight Compute; depth, mid lengths and network conditions on every two-node layout; profile warm-ups; one copy of each shared file.

## 6. How this was checked

`audit/check_scripts_review_v15.py` reads the folder as shared and the zip (for the file modes). Given the folder v1.4 reviewed, it compares the two folders; given the folder v1.3 reviewed, it reads what the v1.3-era helpers wrote into `RUN_CONFIG.env`; given an earlier nccl-tests output and the second campaign's FP8 folder, it reads the format step 3 should parse and how step 8's case ended there; given the vLLM 0.29.0 wheel, it reads the vLLM facts it uses (`vllm serve`'s plain help, the all-failed and partial-failure messages and the ready check's default in `vllm bench serve`, the wheel's own torch and FlashInfer pins, step 4's server flags, how a Ray worker takes its environment, the variables vLLM does not read, its default layer split). It asserts every statement this review makes about the code: 177 of 177. Its check IDs carry one prefix per table of this review; its last section lists them by item. It runs none of the team's scripts. Its experiments, in a scratch folder, reproduce each mechanism with snippets of their own, re-typed from the team's lines, which the static checks tie to the team's text:
- E1: a server-like process started with `setsid ... & PID=$!` from a non-interactive shell leads its own process group; `kill -- -PID` ends it and its children, and the calling shell carries on;
- E2: the two-server runner's prologue, given the split in its environment, exports none and records `default_14_13`;
- E3: under `set -euo pipefail`, an unset `$OUT_DIR` in a redirect stops the script despite `2>/dev/null || true`; the EXIT trap runs;
- E4: the end audit's rules on three manifests (a failed warm-up counted as completed; a FAILED two-server case counted; the upper-case profile manifest not found);
- E5: under `set -e`, a heredoc Python that exits 1 ends the script before the next line;
- E6: the master's selection lines keeping a selection a config sets;
- E7: step 12's comparison key on one condition's folder;
- E8: the helpers' fallback line for `SSH_KEY`;
- E9: the smoke test's context check on the master's cases file;
- E10: the two-server runner's case filter on step 12's case names;
- E11: the example's and the master's `LD_LIBRARY_PATH` lines on a node path ending in ":", giving the TP4/PP4 run's recorded string;
- E12: pandas reading an empty CSV file (it raises an error).

As a control, run on the folder v1.4 reviewed (`audit/check_scripts_review_v15_control_out.txt`), every check behind an item this review calls fixed since v1.4 fails there or cannot be evaluated; the checks that pass there test what is still open or unchanged, and the experiments. v1.3's `audit/coverage_matrix.py` prints the same output on both folders (`audit/coverage_matrix_v15_out.txt`). v1.4's checkers stay in `v1.4/audit/`. The TP4/PP4 data folder is unchanged except for the files in N23, so v1.4's reading of that run stands, except for the library path's empty entry (N12).

```
python3 -I check_scripts_review_v15.py <Performance_Intelligence_Platform dir> <the zip as shared> <scratch dir> [--old <the folder v1.4 reviewed>] [--v13 <the folder v1.3 reviewed>] [--nccl-json <an nccl-tests -J output>] [--stage2-fp8 <the second campaign's FP8 KV rerun folder>] [--vllm-wheel <vllm-0.29.0 wheel>]
python3 -I coverage_matrix.py <Performance_Intelligence_Platform dir>
```
