# Performance Intelligence Platform scripts: checked against the feedback

*v1.3 · 12 Oct 2026 · for the team that maintains the scripts · v1.3 adds section 6 (what the scripts would cover across layouts, prompt lengths and loads once the blockers are fixed, with eight fixes), blocker 13 (1M prompts that do not fit the servers' context length) and section 10 (scope for after the first full run), and corrects sections 4 and 5 for vLLM's default Ray executor, under which a worker keeps any variable its own node set; v1.2's sections 6–9 are now 7–9 and 11. v1.2 recorded the settings agreed since v1.1 (MoE backend, layer split, pynccl) and added section 5, the log checks and A/B for the team to decide the autotune skip list; v1.1 reworded v1 for the single flow*

*Scope: the folder as shared (145 files, zip md5 7cd868bf…), read against the vLLM 0.29.0 release wheel and the FlashInfer 0.6.18 wheel it pins. The findings about the scripts, vLLM and FlashInfer are asserted by `audit/check_scripts_review.py` (162 checks, all pass), and section 6's table is printed by `audit/coverage_matrix.py`. The log figures in sections 4–6 come from `audit/check_autotune_skip.py`, which reads the pilot's and stages 1–3's run records and logs in place. The scripts themselves were not run.*

*Step and line numbers refer to the version shared. Where the single flow has already moved code, each blocker still names the file and the mechanism to fix.*

## 1. In short

- **Most of the feedback is now written into the scripts.**
  - two-server runs under load on all four layouts, 1K to 1M, up to 32 in flight, plus one request at a time at 1K and 8K;
  - decode profiles on two servers, and steady arrivals on two servers (batching block 7);
  - two-long-prompt, step-budget, request-cap and mixed-traffic blocks beyond TP4/PP1;
  - a pause and stall screen over the whole run, and a warm-up before the first measured run of every main-suite server but two;
  - the Ray workers' NCCL environment audited on both nodes, and `--moe-backend` on the servers the runners start.
- **As written, almost none of it would run.**
  - A default run stops at step 3 or 4 with no serving measurement, yet steps 1 and 2 are marked done.
  - Getting past step 4 takes four fixes, and the run then stops at step 13.
  - The 15/12 layer split stops every PP1 and PP4 server, so only TP4/PP2 and TP8/PP2 servers would start.
  - The main suite's single-node runs would record no telemetry, because the sampler is missing from their folder.
  - Steps report success when their runs fail, and resume, which is on by default, then skips them. Following the README, the dry run marks every step done, so the real runs after it skip everything.
- **The settings in force are not the ones on the command line.**
  - `RUN_CONFIG.env` is read after the flags and again inside the runners. So `--profile deep-profile` runs no deep-profile step, and network conditions would be recorded as native.
  - Caps and loss land on node 0 only, and after the cluster set-up, node 1 stays capped at 20 Gbit/s.
- **The one-build decision is not in the scripts yet.**
  - The node set-up installs whichever vLLM is newest on the day. `22_readiness.py` would catch a mismatch, but nothing calls it.
  - We have chosen the FlashInfer CUTLASS MoE backend. The runners default to it, but the profiles and step 4 run `auto`, which falls back to Triton wherever FlashInfer is not usable, as in the pilot. Pin the flag on every launch (section 4) and re-measure the reference points.
- **Agreed since v1.1.**
  - Leave the layer split unset, so vLLM's own defaults apply: 14/13 at PP2 and 7/7/7/6 at PP4. The scripts as shared still force 15,12 and, after either helper, 7,7,7,6 (blocker 4).
  - Leave `VLLM_DISABLE_PYNCCL` unset. Set autotune explicitly.
  - The autotune skip list stays as it is until the team has run the checks in section 5 and decided. For that A/B's second arm, node 1's export of the list (two-server runner line 34) has to change too: under vLLM's default Ray executor, a worker keeps any variable its own node set (section 5).
- **The five additions to reach a 9.**
  - Steady arrivals on two servers are written, but cannot run as written.
  - The NCCL check is partly there: a network sweep that the master never calls, and a socket-thread sweep without a library A/B.
  - The expert-parallel check and Nsight Compute are missing.
  - Only the knee case is repeated, and it runs on TP4/PP1, which the split stops.
  - The fifth, the tool-versus-reality table, is document work on our side.
- **Coverage, once the blockers are fixed (section 6).**
  - The four two-node layouts get the same load grid, 1K to 1M from one request at a time up to 32 in flight (8 at 128K, 4 at 512K and 1M), and two to five of the batching blocks each.
  - TP8/PP1, one node with 8 GPUs, gets little: its baseline is defined but no step runs it. That leaves 8K one at a time, the 16K–256K curve one at a time, and one batching block.
  - Profiling is thin. The master selects 1 of the 24 two-server Nsight captures, TP4/PP2 gets no profile of any kind, two-server Nsight always runs eager, and nothing uses Nsight Compute.
  - Long-prompt points rest on few requests: the two-server 512K and 1M points have 2–8 each, and no 8- or 16-GPU point is repeated by design. Batching block 1's 1M prompts do not fit the servers' context length at all (blocker 13).
  - Eight fixes close this for the scope we set. Other models and vLLM builds, more nodes, quantized weights, and data parallelism and accuracy checks come after the first full run (section 10).
- **Most fixes are small.** The run-stopping blockers are a few lines each, and the network fix mostly means calling scripts the suite already has.

## 2. What a default run does today

| Step | As written |
|---|---|
| 0 | Records the environment; vLLM's version on node 0 only |
| 1 | Both chunk-budget servers (TP4/PP1, 4 GPUs) fail at start-up on the 15/12 split (blocker 4). The step is marked done, because its last command, the summarizer, succeeds |
| 2 | Every capture is skipped (blocker 2). Marked done |
| 3 | Stops the run: in the folder as shared, the script is not executable (blocker 1). With the bit set, the step still stops the run if nccl-tests is not built; otherwise it runs the socket-thread sweep |
| 4 | Exits 3 and stops the run. The server log points at `/server.log`, `local` leaves the PID empty (blocker 2), and the TP8 server is PP1, so the split stops it too (blocker 4) |

On the next run, resume skips the steps marked done (blocker 7). Getting past step 4 takes blockers 1, 2, 4 and 5, and nccl-tests built: fixing blocker 2 makes step 2's `pkill` live. The run then stops at step 13 (blocker 3).

## 3. Blockers: fix before any run

1. **The scripts are not executable.**
   - *Where:* every `.sh` file in the folder as shared. The master calls the subfolder scripts directly in steps 2, 3 and 10–14. The setup manual runs `chmod +x *.sh` in `scripts/`, `01/`, `02/` and `07/`, but never in `04/` or `06/`, which hold every script the master calls directly.
   - *What happens:* unless the bits are set on the VM, each direct call fails with Permission denied, and steps 3 and 13 stop the run. Inside the `bash -c` bodies of steps 2, 10, 11 and 14 the failure is hidden, so those steps run nothing and are marked done.
   - *Fix:* call them with `bash`, or commit them executable (`git update-index --chmod=+x`).
2. **The `bash -c` bodies cannot see the master's shell state.**
   - *Where:*
     - `topology_matches` (defined at line 296) is called inside `bash -c` in step 2 (421–458) and step 14 (822, 825, 841).
     - `TP8_DIR` (step 4), `NET_DIR`, `CASES_FILE` and `CAPPED_DIR` (step 12) and `OBS_DIR` (step 20) are plain variables, used escaped (`\$VAR`) inside the bodies.
     - Step 4 starts its server with `& local PID=$!` (line 501).
   - *What happens:* the child shell sees neither the function nor those variables.
     - Step 2 skips all its captures, and step 14 its three topology-guarded ones. Step 14's other three calls still run, and fail on blockers 1, 3 and 4.
     - Step 4's server log points at `/server.log`, and `local` fails outside a function, leaving the PID empty. The readiness loop then exits 3 at once, and the run stops.
     - Step 12 calls `/12_run_vllm_multi_node.sh` under every condition, while still applying and removing caps on node 0.
     - Step 20's comparison would read the current folder.
     - Steps 2, 12 and 14 exit 0 and are marked done.
   - *Fix:* single-quote these variables as the other steps do (`'$TP8_DIR'`), run `export -f topology_matches`, and drop `local`. Once this is fixed, step 2's `pkill` goes live (blocker 5).
3. **Files the scripts need are missing from their folders.**
   - *Where:*
     - `02_single_node_baseline_matrix/` lacks `09_metrics_sampler.py`, which the single-node runner looks for in its own folder.
     - `06_deep_kernel_and_torch_profiling/` lacks `20_nccl_policy.sh`, `20_ray_nccl_env_audit.py`, `09_metrics_sampler.py` and `10b_vllm_multi_node_cases.json`.
   - *What happens:*
     - Every single-node benchmark in the main suite runs without its Prometheus and GPU sampler, whose error goes to /dev/null. The runs record no telemetry and nothing fails or warns; only the summary's Metrics column shows NOT_CAPTURED. The batching runner finds its sampler.
     - The two-server profile driver stops at line 7 (`source "$SCRIPT_DIR/20_nccl_policy.sh"`). Step 13 stops the run, and step 14's two-server Nsight profiles fail behind `|| true`.
   - *Fix:* keep one copy of each shared file and resolve it from one place, and add a start-up check that every file a step references exists.
4. **One layer split for every server.**
   - *Where:* master line 255 (`${VLLM_PP_LAYER_PARTITION:-15,12}`), `RUN_CONFIG.env.example` line 115, 07's example line 30 and `run_smoke_test.sh` line 147. The cluster set-up (line 141) and the 20-minute TP4/PP4 script (`run_20min_tp4pp4_campaign.sh`, line 104) also write 7,7,7,6 into `scripts/RUN_CONFIG.env`.
   - *What happens:* `VLLM_PP_LAYER_PARTITION=15,12` reaches every server, and vLLM's `get_pp_indices` raises "len(partitions)=2 does not match pp_size=1" (or `=4`) as the model builds its layers.
     - Every PP1 and PP4 server fails at start-up. That covers all single-node work, step 4's TP8 server included, every TP16/PP1 (16 GPUs) and TP4/PP4 (16 GPUs) server, and 20 of the 28 batching cases.
     - Only TP4/PP2 (8 GPUs) and TP8/PP2 (16 GPUs) servers start.
     - Step 11's "default" control inherits 15,12 too, so that A/B compares 15/12 with itself.
     - After either helper runs, 7,7,7,6 leaves only the PP4 servers able to start.
   - *Fix (agreed):* leave the variable unset everywhere. Take it out of the master, both RUN_CONFIG examples, the smoke test and the two helpers. vLLM then uses its own default, 14/13 at PP2 and 7/7/7/6 at PP4, and step 11's control becomes a real default. Keep it out of `RUN_CONFIG.env` (blocker 8). To try another split later, export it for that one PP2 case (section 4). Record the split each server used: the variable's value when it is set, otherwise vLLM's default, which it logs as "Hidden layers were unevenly partitioned: [14,13]" at PP2 and "[7,7,7,6]" at PP4 (a set split, and PP1, log nothing). The two-server runner writes `default_14_13` whenever the variable is unset, which is right only at PP2. The smoke test reports "PP_SPLIT=15,12" as passed without testing the variable (line 155); check each server's split instead.
5. **`pkill -9 -f vllm` kills its own caller.**
   - *Where:* master lines 425–462 (step 2), 918 (step 19) and 933 (step 20); the remote clean-ups at lines 447, 455 and 463; `14d_run_vllm_torch_profile_multi_node.sh` line 55, which runs at start-up.
   - *What happens:* `pkill -f` matches every process whose command line contains `vllm`, the caller included: the step's `bash -c` text, the 14d script's own path, the ssh shell on node 1.
     - Steps 19 and 20 die after their first case.
     - 14d dies at start-up.
     - On node 1, the `ray stop` that follows never runs.
     - Under `set -euo pipefail`, a killed step ends the run.
   - *Fix:* kill the server by the PID or process group the script started, and run `ray stop -f` as its own command. Never `pkill -f` a pattern that appears in the caller's own text.
6. **A failed case ends its group.**
   - *Where:* `12_run_vllm_multi_node.sh`, which runs under `set -euo pipefail`; its per-case runner raises on failure.
   - *What happens:* the first failed case ends the group. Later cases are skipped, and so is the `ray stop` after the failed case, which leaves Ray up on both nodes. In step 10, TP4/PP4 fails on the split, so TP16/PP1 never runs.
   - *Fix:* record a failed case and carry on, stop Ray in a trap, and report the failures at the end.
7. **Steps report success when their runs fail; resume and dry runs then skip them.**
   - *Where:* `run_step` (lines 355–384) and the `bash -c` bodies; the resume default (line 35); the dry-run branch (lines 367–374); the README's run order.
   - *What happens:*
     - A `bash -c` body has no `set -e`, so a step reports only its last command's status. Step 1, for example, ends with the summarizer, which exits 0 even when no case ran, and many commands end in `\|\| true`.
     - So a step whose servers all failed is marked done. Resume, on by default with the latest run id, then skips it next time.
     - A dry run also marks every step it reaches as done. The README runs `--dry-run` before the smoke, dashboard and default profiles, so those runs skip every step.
   - *Fix:* fail a step when any of its cases failed (read the case manifests), make dry runs write no markers, and start each full run with `--new-run`.
8. **`RUN_CONFIG.env` overrides the command line.**
   - *Where:*
     - the master sources it after parsing the flags (lines 217–220);
     - the two-server runner (lines 9–10) and the two-server profile driver (line 9) re-read it after taking the step's settings;
     - the cluster set-up and the 20-minute TP4/PP4 script rewrite it.
   - *What happens:*
     - `--profile deep-profile` turns the sweep switches on, then the example config resets them to 0, so steps 18–20 never run.
     - The two-server runner takes the step's network labels, then the example resets them to native, so every condition would be recorded as native.
     - The profile driver's re-read sets `RUN_HEAVY_PROFILE=0`, which filters out step 13's only profile (TP16/PP1 at 512K).
     - The helpers leave behind the 7,7,7,6 split, a 20G label and a TP4/PP4-only topology selection, which every later run inherits.
   - *Fix:* keep only addresses and paths in `RUN_CONFIG.env`, and read it before the flags. Put per-run settings on the command line or in the case files. Stop the helpers writing the file.
9. **The network conditions are not applied as labelled.**
   - *Where:* master lines 657, 689 and 724 (node 1's interface); the 18 `tc` commands in steps 10–12; `setup_cluster_and_run_smoke.sh`.
   - *What happens:*
     - Node 1's interface is looked up with `print $i+1`, which prints `1`. So every `tc` command on node 1 targets a device called `1`: caps and loss land on node 0's side only, and node 1 is never cleaned.
     - All 18 `tc` commands silence their errors, and nothing records the qdisc or measures the link.
     - Step 12 never sets the cap variable that the runner records, and today it runs no case at all (blocker 2).
     - The cluster set-up caps both nodes at 20 Gbit/s by default and never removes the cap. The master clears node 0 only, so later "native" runs have node 1 capped at 20 Gbit/s.
   - *Fix:*
     - Base step 12 on `20_run_vllm_network_matrix.sh`, which looks up node 1 correctly, lets `tc` fail, and validates with iperf3. Add a reverse-direction check and a loss mode to it, and select cases instead of using `--all`.
     - Record `tc -s qdisc show` on both nodes before and after each condition.
     - Have the step write the cap and labels into each manifest.
     - Have the set-up remove its cap.
10. **The build is not pinned.**
    - *Where:* `setup_node_env.sh` lines 58–66; the runbook; the setup manual; `run_demo_setup.sh`; step 0.
    - *What happens:*
      - `pip install "vllm>=0.6.3"` installs the newest vLLM on the day, and that release's pins then decide torch and FlashInfer. The 0.29.0 wheel, for example, pins torch 2.13.0 and flashinfer-python 0.6.18.
      - The other recipes disagree. The runbook adds FlashInfer from a torch-2.5 index. The setup manual pins transformers 4.44.2 and safetensors 0.4.4 against the wheel's ≥5.10.4 and ≥0.6.2, so its recipe cannot install. `run_demo_setup.sh` installs nightly torch and an unpinned vLLM.
      - There are three venv paths, and step 0 records vLLM's version on node 0 only.
      - `22_readiness.py` already gates exact versions and exits 2 on a mismatch, but nothing calls it.
    - *Fix:* install the one chosen wheel by file on both nodes, check its sha256, and keep one venv. Run `22_readiness.py` in step 0 on both nodes and stop on a mismatch, after fixing its NCCL line (section 4).
11. **The batching suite cannot run its two-server cases.**
    - *Where:* `run_continuous_batching.py`; step 17; `CB_BLOCKS="all"` in the RUN_CONFIG example.
    - *What happens:*
      - The runner asks for the Ray backend on two-server cases but never forms the two-node cluster, yet step 17 runs with the example config. A two-server case can fail at start-up, run on a Ray cluster left over from an earlier step, or (TP4/PP2, 8 GPUs) start on node 0 alone under a two-server label.
      - On top of that, blocker 4 stops 20 of the 28 cases.
      - Every block-4 (mixed traffic) case raises KeyError before sending a request, because its streams lack the `concurrency` field the bench builder reads.
    - *Fix:* run the two-server cases through the Ray set-up in `12_run_vllm_multi_node.sh`, or form and stop the cluster per case. Record the node list in each manifest, and give each mixed-traffic stream a concurrency.
12. **The smoke test proves nothing.**
    - *Where:* `run_smoke_test.sh`.
    - *What happens:*
      - The "end-to-end" check writes a fixed result (48.9 ms to first token) without starting a server.
      - The runner check is a dry run, in which no step executes.
      - Several checks record PASSED on fallbacks: no GPUs, the framework not loaded, tools missing, node 1 not reached.
      - So the smoke test cannot catch blockers 1–11.
    - *Fix:* start one real server per pipeline size (TP4/PP1, TP4/PP2, TP4/PP4, TP16/PP1) and send each one request. Check the start-up lines (MoE backend, KV pool, layer split, NCCL library) and the telemetry files, and fail on any fallback.
13. **Some 1M prompts do not fit.**
    - *Where:* batching block 1's `1m_c2` benchmark in `continuous_batching_cases.json`, on five servers (three TP4/PP1, one TP4/PP4, one TP8/PP2); the two-server profile matrix's four `extreme_prefill_1m` captures, none of which the master selects today.
    - *What happens:*
      - They ask for 1,048,576 prompt tokens plus 256 output tokens (block 1) or 8 (the profiles), on servers whose `max_model_len` is 1,048,576.
      - vLLM 0.29.0 refuses a completion whose prompt is longer than `max_model_len` minus its `max_tokens` (`completion/protocol.py` 263–274, `renderers/params.py` 204–210 and 451–474), and `vllm bench serve` sends `max_tokens` equal to the output length.
      - So every request at that length is refused, and those points record no valid data. The main suite's and the two-server suite's 1M is 1,000,000 prompt tokens with 32 output, which fits.
      - Nothing flags it. `vllm bench serve` only warns "All requests failed", writes zeros for the timings and exits 0 (`benchmarks/serve.py` 653–658 and 732–768), so the batching runner and the profile case record those points as COMPLETED (`run_continuous_batching.py` line 196, `18_run_vllm_multi_node_profile_case.py` line 113).
    - *Fix:* use 1,000,000 for 1M everywhere, as the main suite does, so that block 1 and the profiles also match the load grid's 1M. In all four runners, and for their warm-ups, mark a point FAILED when fewer requests completed than were sent; the result file has `completed` and `failed`. Today each runner marks a point COMPLETED on a zero exit alone (single-node runner line 129, two-server runner line 133, and the two above).

## 4. The footing: one build, one set of settings

- **MoE backend: FlashInfer CUTLASS (agreed).**
  - The runners pass `--moe-backend`, taking the value from `MOE_BACKEND` or `VLLM_MOE_BACKEND` (default `flashinfer_cutlass`). They pass it only if the help text lists the flag; otherwise it is skipped silently. The B1 decode profile, the torch profiles (one- and two-server) and step 4's TP8 server pass nothing, so they run `auto`. The two-server Nsight profiles do pass the flag.
  - With `auto`, vLLM 0.29.0 tries FlashInfer TRT-LLM, FlashInfer CUTLASS, Triton, then batched Triton (`unquantized.py` 67–73). It moves both FlashInfer kernels back on Hopper and for the SWIGLUOAI activation, and CUTLASS also when data parallelism is above 1 (75–93); LoRA takes another path (222–236). None applies here: the activation is SiLU, there is no LoRA, and data parallelism is 1. TRT-LLM's kernel is SM100-only, so on these GPUs (SM120) `auto` takes CUTLASS whenever FlashInfer is usable, and Triton otherwise.
  - vLLM counts FlashInfer as usable only with the flashinfer-cubin package (or `VLLM_HAS_FLASHINFER_CUBIN=1`) or `nvcc` on PATH (`flashinfer.py` 56–83). The pilot's run records have no CUDA_HOME and its logs no autotune line of either kind: FlashInfer was not usable, and `auto` ran Triton. Stages 1–3 recorded CUDA_HOME=/usr/local/cuda; stages 2 and 3's logs show CUTLASS, and stage 1 kept none. Every set recorded flashinfer-python 0.6.18 and the nvidia-cuda-nvcc 13.4.92 package; none recorded PATH.
  - FlashInfer builds its CUTLASS MoE module with nvcc on the first MoE call, which comes in vLLM's memory profiling run, before the autotune step, and keeps it in `~/.cache/flashinfer/0.6.18/<arch>/cached_ops`. A prebuilt copy from the matching flashinfer-jit-cache package skips the build (FlashInfer `fused_moe/core.py` 585–598, `jit/core.py` 300–321, `jit/env.py` 58–62 and 113–162). It logs nothing while it builds.
  - So pass `--moe-backend flashinfer_cutlass` on every launch, the profiles and step 4 included. With the flag, a node where FlashInfer is not usable stops at start-up with "Unquantized MoE backend FlashInfer CUTLASS does not support the deployment configuration", instead of running Triton quietly (`unquantized.py` 258–297). Keep nvcc on PATH for the servers and their Ray workers on both nodes. Without nvcc, vLLM needs flashinfer-cubin (or `VLLM_HAS_FLASHINFER_CUBIN=1`), and FlashInfer needs flashinfer-jit-cache for this version. Keep `~/.cache/flashinfer` between runs. Record `shutil.which("nvcc")` inside each Ray worker, in the Ray audit: the workers on node 1 take PATH from the shell that ran `ray start` there, and vLLM's default Ray executor never replaces it (see how the Ray workers get their environment, below). Check the start-up line "Using FlashInfer CUTLASS Unquantized MoE backend".
  - Drop environment pins of the backend. Stage 3 set `VLLM_MOE_BACKEND=triton` in all 11 run records, but vLLM never reads it, none of its 12 saved commands carries `--moe-backend`, and its one logged server ran CUTLASS.
  - Re-measure the reference points on the chosen settings before comparing. What we have so far: at 128K prefill, stage 2's CUTLASS GEMMs, not tuned, took 27–29% longer per MoE layer than the pilot's Triton (TP4/PP2 and TP4/PP4, eager captures; a different build, on other GPUs of the same type). Tuning took 13% off the two GEMMs per MoE layer at 512K (section 5, C7). Tuned CUTLASS has not been captured at 128K: arm B of the A/B in section 5 measures it, and the A/B's optional Triton arm gives the point to compare with.
- **Settings vLLM never reads.**
  - `VLLM_MOE_BACKEND` and `MOE_BACKEND` only feed the runners' flag, and nothing acts on `VLLM_FLASHINFER_AUTOTUNE`.
  - vLLM warns "Unknown vLLM environment variable detected" for `VLLM_*` names it does not know, so `server.log` shows this.
  - Autotune follows the optimization level: off at O0, on at O1–O3, and the default is O2. So it is on today by default, not because of the setting. Pass `--enable-flashinfer-autotune` explicitly and record it. The skip list decides which operations it leaves out: section 5.
- **How the Ray workers get their environment.**
  - vLLM 0.29.0 runs Ray servers on RayExecutorV2 by default (`VLLM_USE_RAY_V2_EXECUTOR_BACKEND` defaults to 1, `envs.py` 914–918; `abstract.py` 61–65), and no script changes that. The pilot's and stages 2 and 3's worker logs name its RayWorkerProc actor.
  - Each worker starts from the environment of the `ray start` on its own node, and takes node 0's server environment only for variables it lacks, so it keeps every variable the scripts set on its own node (`ray_executor_v2.py` 155–174 and 345–348, `ray_env_utils.py` 10–20). Nothing is logged when a worker keeps its own value. The fill-in also comes after the worker process has started and loaded torch (`ray_executor_v2.py` 380–396 and 436–446), so for variables read when libraries load, such as `LD_LIBRARY_PATH`, only the `ray start` environment counts.
  - So a variable has to be right in both nodes' `ray start`. The two-server runner starts node 0's Ray from its own shell (line 74), and node 1's with the NCCL policy's exports followed by line 34's (line 76); the Nsight driver passes the policy's exports too (line 85). The two-server torch script, 14d, does not: it never sources the NCCL policy and starts node 1's Ray with no exports (line 79), so its captures run on whatever NCCL library each node's login environment finds. Give it the policy's exports, as the other two do.
- **`VLLM_DISABLE_PYNCCL`: leave it unset (agreed).**
  - Setting it to 1 turns off vLLM's own NCCL communicator. All-reduce, all-gather and send/receive fall back to PyTorch's NCCL group, and the NCCL version line that the communicator prints disappears.
  - All-gatherv asserts that the communicator is on, so data-parallel expert parallelism would stop on its first forward pass; this model's own sequence parallelism only turns on with it. Reduce-scatter returns without writing, which leaves uninitialised memory and raises no error. Its only user here would be the compile-time sequence-parallel pass, which is off by default.
  - No run in any log set had it set (run records: 0 in every set).
  - Take it out of every place in one change: the master (line 270, `${VLLM_DISABLE_PYNCCL:-1}`), the two-server runner (shell lines 23 and 34, Python line 78), both RUN_CONFIG examples and both helpers. Line 34 exports it for node 1 after the policy exports, and node 1's Ray workers keep that value (see how the Ray workers get their environment, above). So with it unset on node 0 alone, node 1's workers would keep 1.
- **Layer split: vLLM's default (agreed).**
  - With the variable unset, vLLM splits the 27 layers 14/13 at PP2 and 7/7/7/6 at PP4 (`get_pp_indices`, `utils.py` 155–167), and logs "Hidden layers were unevenly partitioned: [14,13]" (or `[7,7,7,6]`); a set split logs nothing. Full-attention layers per stage: 3/4 at 14/13, 3/4 at 15/12, 1/2/2/2 at 7/7/7/6.
  - To try another split later, export it for that one PP2 server only, for example `export VLLM_PP_LAYER_PARTITION=15,12` just before that launch, and unset it after. The two-server runner puts a set split into both nodes' `ray start` (lines 69–76), which is where the workers take it from. Never put it in `RUN_CONFIG.env`, and record it. The split is part of vLLM's compile key, so the first start on a new split is a cold start.
  - Our one same-session A/B (stage 2, 2–4 requests per point, one at a time) measured 15/12 against the default at −5.6% to +3.1% first-token time and within 1.2% token time:

    | Layout | Prompt | First token, default → 15/12 | Token time, default → 15/12 |
    |---|---|---|---|
    | TP4/PP2 | 128K | 2,763 → 2,848 ms (+3.1%) | 6.036 → 5.965 ms (−1.2%) |
    | TP4/PP2 | 512K | 18,437 → 18,089 ms (−1.9%) | 8.426 → 8.393 ms (−0.4%) |
    | TP8/PP2 | 128K | 3,485 → 3,291 ms (−5.6%) | 8.051 → 8.036 ms (−0.2%) |
    | TP8/PP2 | 512K | 18,479 → 17,693 ms (−4.3%) | 10.387 → 10.354 ms (−0.3%) |

  - The docs' "+27.58% TTFT" for 15/12 (6.12 s → 4.43 s; `README_SETUP_AND_OPERATIONS.md` line 1402 and five other files) does not match this A/B. Check which runs it compares before quoting it.
- **The NCCL library.**
  - The master makes `/tmp/clean_nccl_libs` on node 0 only. Node 1 gets it only from the init script, and only when `V5_FORCE_NCCL_SOCKET=1`.
  - The two-server runner and the Nsight driver propagate the library path to node 1 (14d does not, above), so if the folder is missing there, node 1 silently loads another library.
  - The Ray audit records each worker's environment, not the library it mapped.
  - `22_readiness.py` expects nvidia-nccl-cu13 2.29.7, while our existing measurements logged 2.31.2 loaded from the clean folder. So the package version alone does not say which library ran.
  - Create the folder on both nodes at the start of every run. Record each worker's mapped `libnccl` (from `/proc/<pid>/maps`) and `torch.cuda.nccl.version()`.
- **Docs against code.**
  - The README lists `NCCL_ALGO=Tree` and `NCCL_PROTO=Simple` as enforced, but the master unsets both. Keep them unset, since Simple alone slows small messages, and fix the README.
  - `NCCL_CROSS_NIC=1` is still in the RUN_CONFIG example and in both helper-written configs. Each node has one NIC, so drop it.
  - The README promises a server restart between concurrency levels. In fact the runner starts one server per case and runs every benchmark on it, and the drain barrier is never called. Either design works, but the README should say which one is used.
- **Admission caps.**
  - The two-server load cases run up to 32 in flight with `max_num_seqs` 16, so at 32 only 16 run at once and the rest queue.
  - The one-server cases run at 32 in flight cap at 64 in the main case file and at 256 in the batching suite. The 32-capped baselines are used by no step.
  - Raise the two-server cap to 32, or compare at 16 in flight or fewer.

## 5. The autotune skip list: check the logs, then decide

The scripts set `VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS=trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2`. We are not asking for it to be removed now. This section sets out what it does, what the pilot's and stages 1–3's logs say about it, what they cannot say, and a short A/B with a decision rule, so the team can decide on evidence.

**Where it is set.** Seven lines set it unconditionally: the master (line 254), `RUN_CONFIG.env.example` (114), 07's example (29), the smoke test (146), the two-server runner (line 22), and the two helpers, which write it into `RUN_CONFIG.env` (cluster set-up line 140, 20-minute TP4/PP4 script line 103). The two-server runner exports it again for node 1 after the policy exports (line 34), and the single-node runner injects it when it is unset (`11_run_vllm_surrogate.py` line 58). The older copies in `rtx_g4_smoke_v5/` do the same, and both READMEs give it as a set-up step. The comments give the reason as "to prevent Triton MoE hang"; the docs say it avoids "warmup hangs" (`README_SETUP_AND_OPERATIONS.md` line 1401) and a "45-minute JIT freeze" in Triton MoE warm-up (`PIP_MASTER_RESULTS_AND_BENCHMARKS.md` line 36).

**What it does (vLLM 0.29.0, FlashInfer 0.6.18).**
- The two names are the two GEMMs that FlashInfer's CUTLASS fused MoE tunes (`fused_moe/core.py` 891, 960–988). Triton's MoE never calls them, so with Triton the list changes nothing.
- vLLM reads the list at the autotune step, which runs only when autotune is on, FlashInfer is usable and the GPU is SM90 or newer (`kernel_warmup.py` 189–196). It logs "Skipping FlashInfer autotuning for ops (…)" once per node and hands the list to FlashInfer (299–305). Set but empty, the variable skips nothing (`envs.py` 1712–1723).
- A skipped GEMM is not profiled and gets FlashInfer's heuristic fallback tactic (`autotuner.py` 1609–1621): the same tactic as with autotune off, which is what stage 2 ran.
- The skip applies only while tuning (938–944, 988–992). vLLM keeps tuned results in a cache file: rank 0 reads it on node 0 and broadcasts it, every rank loads it before tuning, and rank 0 saves it after (`kernel_warmup.py` 307–341). The file sits under the vLLM cache folder (or `VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR`), keyed by vLLM's compile key, which leaves out both the skip list and that folder (`flashinfer_autotune_cache.py` 19–41, `envs.py` 2257–2302). If the file already holds tuned results for the two GEMMs, from an earlier start without the list on the same settings, they are used in serving, and every rank logs "Config cache hit" (`autotuner.py` 1430–1491). So what the list does to serving depends on what is in that file.
- FlashInfer averages each tactic's time across all ranks, so every rank must tune the same operations against the same starting cache, or the reduction deadlocks (`autotuner.py` 1066–1072, 2187–2201). A list on some ranks and not others is therefore a way to cause a hang at this step, not to prevent one. vLLM gives every rank the same cache. Each Ray worker keeps the list its own node's `ray start` set, and takes node 0's only if that is unset (section 4). The scripts export the same list on both nodes (two-server runner lines 22 and 34).
- The list cannot avoid building the CUTLASS MoE module, which FlashInfer does on the first MoE call, before the autotune step, whatever tactic is picked (section 4).

**What each log set ran with.**

| | Pilot | Stage 1 | Stage 2 | Stage 3 |
|---|---|---|---|---|
| Run records | 15 | 5 | 10 | 11 |
| vLLM version label | 0.29.0 | 0.29.0 | 0.29.0 | 0.29.0 |
| vLLM build (BUILD) | – | not logged | not the pilot's: 15 of the 33 log messages both print come from other source lines | stage 2's: 0 of 31 do |
| CUDA_HOME set | 0 of 15 | 5 of 5 | 10 of 10 | 11 of 11 |
| FlashInfer usable (C1, C2) | no | not logged | yes | yes |
| MoE backend in the logs (C1) | Triton, 17 logs | no log kept | FlashInfer CUTLASS, 9 logs | FlashInfer CUTLASS, 1 log |
| Autotune in the saved commands | no flag (61 commands) | off in 3 of 5 | off in 19 of 19 | no flag (12 commands) |
| Skip list in the run records | 0 of 15 | 0 of 5 | 0 of 10 | 6 of 11 (the capped and lossy network runs) |
| `VLLM_MOE_BACKEND` | unset | unset | unset | `triton` in 11 of 11 (never read) |
| Split variable | unset | unset | 15,12 in 2 of 10 (the split A/B arm) | unset |
| `VLLM_DISABLE_PYNCCL` | unset | unset | unset | unset |
| Ray workers' NCCL path | clean folder (58 records) | no audit | clean folder (34) | no clean folder (18) |
| Serving starts that became ready / kept a server log | 41 / 0 | 5 / 0 | 9 / 0 | 10 / 0 |
| Starts that never became ready | 3 (126–134 s) | 0 | 1 (184 s) | 1 (2,013 s) |
| Captures with worker logs | 17 | 0 | 9 | 1 |

**The checks and what they show.** Each check reads lines that vLLM or FlashInfer log, or the run records. `audit/check_autotune_skip.py` runs all of them on any set of folders or zips. Lines logged once per node come from each node's first rank only.

| Check | Reads | Pilot | Stage 2 | Stage 3 |
|---|---|---|---|---|
| C1 MoE backend | "Using … Unquantized MoE backend" (once per node) | Triton (17) | CUTLASS (9) | CUTLASS (1) |
| C2 autotune and skip list | "Running FlashInfer autotune with N tokens" (every rank), "…because it is disabled" and "Skipping FlashInfer autotuning for ops" (once per node), "Using FlashInfer autotune cache file" (rank 0) | neither autotune line in 17 of 17 (FlashInfer not usable) | disabled (9) | ran (8 worker logs); no skip-list line in any saved log |
| C2b same operations on every rank | per worker that ran the autotune step: tuned the two GEMMs or not | – | – | all 8 tuned both |
| C3 what was tuned | "Tuning <op>:", "Config cache hit for <op>", "No tuned config covers" | nothing | nothing | both GEMMs in 8 logs; no cache hit, so tuning started from an empty cache |
| C4 tuning time | "[Autotuner]: Autotuning process starts" and "ends", per worker | – | – | 4.20–4.21 s, 8 workers |
| C5 stopped starts | an autotune line with nothing after it; a worker log that ends before "Kernel JIT monitor activated" | 0 of 120 | 0 of 64 | 0 of 8 |
| C6 start-up | server start → ready per layout in launch order, and the starts that never became ready (run records) | table below | table below | table below |
| C7 MoE kernel time | Nsight kernel summaries, per call | Triton | CUTLASS, not tuned | CUTLASS, tuned (512K); one decode capture of unknown state |
| C8 worker start-up | worker init → "Kernel JIT monitor activated"; "Loading weights took" | 11–18 s (weights 1.7–3.8 s) | 12–20 s (weights 1.7–3.6 s) | 272–275 s: weights 230.82 s, tuning 4.2 s |

Stage 1 kept no logs, so only C6 applies to it.

C6, first start of a set-up against later ones (seconds, server start → ready):

| Set | Layout | First start | Later starts: median (range), count | Skip list | Autotune |
|---|---|---|---|---|---|
| Pilot | TP16/PP1 | 110 | 50 (48–52), 2 | none | FlashInfer not usable |
| Pilot | TP4/PP2 | 142 | 46 (44–48), 2 | none | FlashInfer not usable |
| Pilot | TP4/PP4 | 44 | 47 (44–50), 2 | none | FlashInfer not usable |
| Pilot | TP8/PP1 | 50 | 44 (44–44), 2 | none | FlashInfer not usable |
| Pilot | TP8/PP2 | 46 | 48 (46–50), 2 | none | FlashInfer not usable |
| Pilot | TP4/PP1 | 192 | 138 (128–150), 25 | none | FlashInfer not usable |
| Stage 1 | TP4/PP1 | 410 | 123 (116–124), 4 | none | on for the first two starts, then off |
| Stage 2 | TP4/PP2 | 386 | 40 (40–40), 2 | none | off |
| Stage 2 | TP8/PP2 | 68 | 42 (42–42), 2 | none | off |
| Stage 3 | TP16/PP1 | 72 | 58 (56–62), 3 | later three only | on (default level) |
| Stage 3 | TP4/PP4 | 90 | 48 (46–50), 3 | later three only | on (default level) |

The skip-list column, like the table above, is what the runner recorded of its own environment. A runner that adds the list to the server's environment only, as the single-node runner as shared does, leaves no trace in the records. The stage 1–2 code we have never sets it.

- First starts are often slow, and they are slow with FlashInfer unusable (pilot) and with autotune off (stage 2), so tuning is not what makes them slow. Not every first start was slow (pilot TP4/PP4, TP8/PP1 and TP8/PP2: 44–50 s), and the records do not say where the slow ones spent their time.
- In stage 3 the skip list was on only for the later starts, which were also the capped and lossy network runs, so its effect cannot be told apart from launch order or the network condition.
- The most the list can save at start-up is the tuning itself: 4.2 s per start with an empty cache (C4), and nothing once the cache holds the results.
- The slowest worker start-up among the captures was stage 3's 512K Nsight capture, its first two-server start: node 1's workers spent 230.82 s of 272–275 s loading weights, and 4.2 s tuning (C8).

C7, what tuning the two GEMMs is worth. The one like-for-like pair: TP16/PP1, one 512K prompt, eager captures, the same build on other GPUs of the same type. Stage 2 ran with autotune off, which gives the tactic the skip list gives on an empty cache; stage 3 tuned both GEMMs:

| Per call | Not tuned (stage 2) | Tuned (stage 3) | Change |
|---|---|---|---|
| `fused_moe::run_global` | 851.6 µs | 720.4 µs | −15.4% |
| `MoeFCGemm` | 490.6 µs | 444.4 µs | −9.4% |
| Both, one MoE layer | 1,342.2 µs | 1,164.8 µs | −13.2% |

Calls: 31,616 of each in stage 2; 31,824 and 31,408 in stage 3. Against this, tuning cost 4.2 s per start with an empty cache, with every worker tuning at once.

**What the logs cannot tell.**
- No serving start in any set kept its server log (0 of 70, the five that never became ready included). For the six stage-3 starts with the skip list, nothing shows the backend, the list applied, or whether a cache served tuned results.
- Their layouts' first starts ran without the list, so by the code they tuned the two GEMMs and rank 0 saved the results. A later start reuses those only with the same compile key (the same server settings) and the same cache folder on node 0, which the records do not show. So whether the skip-list starts served tuned or untuned GEMMs is unknown.
- No capture is known to have run with the skip list, so its cost in kernel time is inferred from stage 2's untuned captures, not measured. Stage 3's graphs-on decode capture kept no log, so its tuning state is unknown.
- Every worker log that was kept reached the end of start-up (C5, 0 of 192), so no kept log shows a hang. But five serving starts never became ready, each ending "server exited rc=1", and none kept a log: three in the pilot (126–134 s), stage 2's FP8 KV rerun (184 s), and stage 3's streaming-jitter run on TP4/PP1 (2,013 s, about 34 minutes). That last one is the only long start in the records, and the one that could match the freeze the docs describe. Nothing records what it was doing. Its run record shows no skip list in the runner's environment, but the single-node runner as shared adds the list to the server's environment when it is unset (line 58), and stage 3's runner was not shared, so whether that server had the list is unknown.
- Whether a cache file held results shows as "Config cache hit" on every rank (C3), and no kept log has one. Rank 0's log, which names the file, was not kept.

**The A/B to decide it.** Twelve server starts on the two nodes (15 with the options), most followed by a few minutes of load.
- *Arms.* A: the skip list as the scripts set it. B: the variable set but empty, which skips nothing (`envs.py` 1712–1723). Set it empty rather than unsetting it: with the form below an unset variable falls back to the list, while an empty one stays empty, and the NCCL policy passes it to node 1 as it is (`20_nccl_policy.sh` lines 75–79).
- *Making B possible.* The master (line 254), the two-server runner (line 22) and `RUN_CONFIG.env` set the list unconditionally, and the master and the two-server runner both source `RUN_CONFIG.env`, so a value given for the run is overwritten. In those three, in both examples, and in any older `RUN_CONFIG.env` the runners can still find (the two-server runner takes the first of four candidates, line 9), use `export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2}"` (note `-`, not `:-`, so that an empty value stays empty). Line 34 has to change too. It exports the full list for node 1 after the policy's exports, and node 1's Ray workers keep a value their own `ray start` set (section 4). With line 34 as it is, arm B's node-1 ranks would skip the two GEMMs while node 0's tune them, the mismatch that can deadlock tuning. Take the variable out of line 34: the policy's export just before it already carries node 0's value, empty included. Do not run the two helpers during the A/B: they rewrite `RUN_CONFIG.env` (blocker 8), and inside their heredocs the form would need `\${…}`. The single-node runner already keeps a value that is set.
- *Fixed for both arms.* `--moe-backend flashinfer_cutlass`, `--enable-flashinfer-autotune`, the split unset, `VLLM_DISABLE_PYNCCL` unset, the clean NCCL folder on both nodes, and the same server settings per layout.
- *Caches.* Give each arm its own autotune cache folder (`VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR`), set the same and writable on both nodes: every rank writes the copy rank 0 broadcasts, and rank 0 reads and saves it on node 0. The skip list is not part of the cache key, so with one folder, B's tuned results would reach A. The compile cache and `~/.cache/flashinfer` can be shared, since neither variable is part of the compile key. Before each start, list the arm's folder and `~/.cache/flashinfer/0.6.18/*/cached_ops`.
- *Layouts.* TP4/PP1 (one node) and TP4/PP2 (two nodes) with load; and one TP16/PP1 start per arm, start-up only, each with an empty folder: tuning synchronised across 16 ranks on two nodes is where a hang would show.
- *Order on TP4/PP1 and TP4/PP2.* One start with a third, throwaway cache folder, to warm the page cache and the compile cache; not measured. Then A with its folder empty, B with its folder empty, B again (its folder now holds the tuned GEMMs), and A again (its folder never gains GEMM results): A B B A.
- *Load per start.* 8K one request at a time, 8K with 32 in flight, and 128K one at a time, each after the suite's warm-up.
- *Keep for every start.* The server log on node 0 and node 1's Ray logs, the Ray audit (two-node starts), the start → ready time, and the listing of the cache folders. Then run `check_autotune_skip.py A=<arm A folder> B=<arm B folder>`. In A, expect the skip-list line once per node and no rank tuning the GEMMs (C2, C2b, C3). In B, expect no skip-list line; on the starts with an empty folder, every rank tuning both GEMMs, and the tuning time (C2b, C3, C4); on the second start, cache hits instead (C3). In both, nothing stopped (C5) and every start became ready (C6).
- *Optional.* One Nsight capture of a 128K prompt per arm (eager), read with C7, for tuned against untuned per-call times at 128K; and a Triton arm (`--moe-backend triton`) on TP4/PP1 at 128K, to set against arm B. No capture yet shows tuned CUTLASS against Triton at long prefill.

**Decide.** Fix the thresholds before the run, so the numbers decide.
- *Keep the list, and find the cause,* if arm B shows the problem it is meant to prevent: any start that stops at the autotune step (C5) or fails during tuning. Look first at C2b, then at the list each node's Ray workers had. The default Ray executor logs nothing when a worker keeps its own value, so read the Ray audit that the two-server runner writes for each case (04's `20_ray_nccl_env_audit.py` records each node's `VLLM_*` variables as a Ray task inherits them, which is what the workers start from; where it shows the variable unset, the workers took node 0's server value), and compare the environment of `ray start` on both nodes.
- *Keep it too* if B's starts are more than 30 s slower than A's matching ones (empty folder against empty folder, second start against second start) and B's serving gain stays within the spread between repeats of the same arm.
- *Otherwise remove it,* from every place listed above in one change, node 1's export included: a list left on one node makes the ranks tune different operations. Point `VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR` at a folder that survives between runs and is writable on both nodes (rank 0's copy, on node 0, is the one read), so each set-up tunes once, and keep `~/.cache/flashinfer` so the CUTLASS module is built once per node.
- *Either way,* record the decision, the thresholds and the A/B folders in the run notes, and keep C1, C2 and C5 in the smoke test.

## 6. Coverage across layouts, prompt lengths and loads

*What the scripts would run, by layout, once the blockers in section 3 are fixed. `audit/coverage_matrix.py` prints it from the case files, the profile scripts and the master runner; re-run it after changing any of them. Batching blocks count only when the run selects them, with `--cb-blocks` or an exported `CB_BLOCKS`; today only the RUN_CONFIG example sets `CB_BLOCKS`, and blocker 8's fix takes it out. cN means N requests in flight.*

**What each layout gets.**

| Layout | Serving runs | Profiles the master selects |
|---|---|---|
| TP4/PP1 · 4 GPUs, one node | 1K at c1–c64, 2K at c1–c32, 8K at c4–c64 and 128K at c1–c8 (steps 1, 5 and 6; batching blocks 1–6; the knee repeats, 3× 8K c16 and 3× 128K c4). 512K and 1M only at c1, in the FP8 KV and offload cases (steps 8 and 9), and 1M at c2 in block 1 (blocker 13). Steps 18–20 add 1K–8K points with `--profile deep-profile` | Nsight, graphs on: 8K decode c1 and 128K prefill c1 (step 14). Torch, graphs on: 8K c8 (steps 2 and 14) and c32 (step 2) |
| TP8/PP1 · 8 GPUs, one node | 8K c1 (step 4, unpinned then pinned); 16K, 32K, 64K and 256K at c1 (step 6); block 2 | Nsight, graphs on: 128K prefill c1 (step 14). Torch, graphs on: 8K c8 and c32 (step 2) |
| TP4/PP2 · 8 GPUs, two nodes | the load grid (step 10); 1K–1M at c1 in the split A/B (step 11); blocks 2, 4 and 7 | none |
| TP8/PP2 · 16 GPUs | the load grid; the split A/B; blocks 1, 2, 3, 4 and 7 | Torch, graphs on: 8K c8 (steps 2 and 14) |
| TP4/PP4 · 16 GPUs | the load grid; network conditions at 128K c1 and c4 (step 12); blocks 1, 3, 4 and 7 | Torch, graphs on: 8K c8 (steps 2 and 14) |
| TP16/PP1 · 16 GPUs | the load grid; network conditions at 128K c1 and c4; blocks 4 and 7 | Nsight, eager: 512K prefill (step 13). Torch, graphs on: 8K c8 (steps 2 and 14) |

- *The load grid* (step 10, the same on all four two-node layouts): 1K and 8K at c1, c8 and c32; 128K at c1, c2, c4 and c8; 512K and 1M at c1, c2 and c4. These servers admit 16 at once (section 4).
- *The batching blocks:* 1, two long prompts side by side (128K c8, 1M c2); 2, step budgets (8K c8 and c32, 128K c4 and c8); 3, request caps (1K and 8K at c64); 4, mixed traffic (1K and 128K streams at set rates); 5, memory pressure (8K c32, 128K c8); 6, long answers (8K c16 and c32); 7, steady arrivals (8K and 128K at set rates, capped at 128 and 64 in flight).
- *Defined, but no step runs them:* `tp8_pp1_baseline` (1K and 8K at c1, c8 and c32; 128K at c1, c4 and c8; 512K at c1, c2 and c4; 1M at c1 and c2), `tp4_pp1_baseline` (the same, up to 512K c2 and 1M c1) and `tp4_r1_continuous_context_curve` (16K–256K at c1 on TP4/PP1).

**Still missing once the blockers are fixed.**
- *TP8/PP1 under load.* With its baseline unused, the one-node 8-GPU layout has nothing at 1K, 512K or 1M, nor 128K at c1, and its only load points are block 2's. So 8 GPUs on one node (TP8/PP1) and on two (TP4/PP2) compare like for like only at block 2's four points. TP4/PP1's baseline is unused too. At the suite's default settings (an 8,192-token step budget, no FP8 KV, offload or prefix caching), TP4/PP1 has no 8K or 128K point at c1: step 6 runs 128K c1 with a 16,384-token budget, steps 8 and 9 with FP8 KV and with offload. It has no 512K point either, and its one 1M point at those settings, in block 1, is refused (blocker 13).
- *Profiles.*
  - The two-server Nsight matrix defines 24 captures: four layouts, each with 1K prefill, 8K decode, 8K decode at c8, and 128K, 512K and 1M prefill. The master selects one, TP16/PP1 at 512K (step 13).
  - Step 14 asks for the mode `decode`, but the two-server Nsight driver's filter takes one exact name (`18_run_vllm_multi_node_profiles.sh` line 54) and the modes are `decode_8k` and `batched_decode_8k_c8`, so it selects none.
  - The case script the driver runs always adds `--enforce-eager` (`18_run_vllm_multi_node_profile_case.py` line 75), so no two-server Nsight capture shows serving with CUDA graphs, and eager decode carries launch gaps that graphs remove.
  - TP4/PP2 is in neither step 2's nor step 14's two-server torch captures, so it gets no profile of any kind. Nothing uses Nsight Compute.
- *Depth.* The load-grid servers admit 16 at once, so c32 measures 16 running and 16 queued (section 4). Each 512K point runs two waves (2, 4 and 8 requests at c1, c2 and c4), and 1M at c2 and c4 a single wave of 2 and 4 requests, so a long-prompt figure rests on one or two batches. No 8- or 16-GPU point is repeated by design; the only repeats by design are TP4/PP1's knee case. Steps 11 and 12 measure some points a second time on new servers (1K–1M at c1 on the PP2 layouts in step 11's default arm, 128K at c1 and c4 on TP16/PP1 and TP4/PP4 in step 12's native arm), but none at 8K c32, 128K c8 or 1M c4.
- *Mid lengths.* 16K, 32K, 64K and 256K run only on TP8/PP1, one at a time; TP4/PP1's curve is unused. On two nodes the grid goes from 8K to 128K to 512K.
- *Network conditions.* Step 12 runs TP16/PP1 and TP4/PP4 only, at 128K c1 and c4 with 64-token answers, so both points are prefill-heavy. Neither PP2 layout runs under caps or loss.
- *Not covered at all.*
  - Two TP4/PP1 copies on one node: every TP4/PP1 case uses GPUs 0–3.
  - Prefix caching beyond TP4/PP1: it is on only in the offload and prefix-decay cases.
  - Expert parallelism: no script enables it, and the start-up check is missing (section 7).
  - FP8 KV beyond TP4/PP1. FP8 KV has also never started: all three FP8 starts in the records (two in the pilot, stage 2's rerun) exited rc=1 before becoming ready, and none kept a server log (`check_autotune_skip.py`, C6).

**Fixes.** The first three are a few lines each.
1. **Run the two baselines and the TP4 curve.** Add a step line with `--group baseline_matrix`: the two baselines are the only cases in that group, and the single-node runner selects cases by group. Add `--case tp4_r1_continuous_context_curve` to step 6, beside the TP8 curve. TP8/PP1 then gets the two-node grid's lengths and most of its loads (all but 128K c2 and 1M c4), so 8 GPUs on one node and on two compare like for like, and TP4/PP1 gets 8K and 128K at c1, 512K and 1M at the suite's default settings. The baselines' servers admit 32 at once and the load grid's 16, so compare at 16 in flight or below, or raise the load grid's cap (fix 5).
2. **Select the profiles that are defined.** Let the driver's mode filter take a comma-separated list of exact names (line 54), and have step 14 ask for `decode_8k,batched_decode_8k_c8,prefill_128k`: twelve captures, three per two-node layout, eager as today. Add `tp4_pp2_dist` to step 14's torch loop; `14d_run_vllm_torch_profile_multi_node.sh` already supports it (lines 27–28). Step 2's two-server torch block takes the same three captures as step 14, so drop that block from step 2. Keep step 2's TP4 c32 and TP8 c8 and c32 captures; step 14 takes only TP4 c8.
3. **Graphs on for two-server Nsight.** Give the case script an `ENFORCE_EAGER` switch, as the single-node script has (`14_run_vllm_nsys_profile.sh` lines 28 and 34–36), but defaulting to eager, so that step 13's 512K capture and fix 2's captures stay comparable with the earlier eager ones and keep their per-layer NVTX ranges. Then add a second driver call to step 14, `ENFORCE_EAGER=0 PROFILE_MODE_FILTER=decode_8k,batched_decode_8k_c8`, with its own `OUT_ROOT`: one call applies one setting to every capture it selects, and the driver writes each capture to `$OUT_ROOT/<layout>/<mode>` (line 68). vLLM's Ray Nsight integration traces CUDA graphs node by node (`ray_executor_v2.py` 265–270), so each kernel still shows. The layer-wise NVTX ranges the case script turns on (line 76) do not work with CUDA graphs (`config/observability.py` 72–75), so the graphs-on captures will lack them, as the single-node graphs-on captures already do.
4. **Nsight Compute on 8 and 16 GPUs.** Besides the TP4 decode step and one 128K prefill (section 9), capture the same two on TP8/PP1, one node, limited by kernel name and launch count so that the NCCL kernels are left out. TP16/PP1 needs a way to start one Ray worker under Nsight Compute, which neither vLLM nor the scripts have (vLLM's Ray integration starts workers under Nsight Systems only), so add it once such a wrapper has been tried. Check first that the VMs give access to the GPU performance counters (Nsight Compute reports ERR_NVGPUCTRPERM when they do not); if they do not, record that and leave it out.
5. **Depth.** Raise the load grid's `max_num_seqs` to 32 (section 4). Give the long-prompt points at least three waves, for example 12 requests at 1M c4 instead of 4. Run the two repeats in section 9 on the two-node layouts too.
6. **Mid lengths on two nodes.** Add 32K and 256K at c1 and c4 to the load grid, so each two-node layout has more points between 8K and 512K than 128K alone: four more points per layout.
7. **Network conditions on every two-node layout.** Add TP4/PP2 and TP8/PP2 cases to the network-conditions group (`r3_network_resilience`) at 128K c1 and c4, and on all four a point where decode clearly dominates, for example 8K c8 with 1,024-token answers. Extend step 12's report, which reads only the TP16/PP1 and TP4/PP4 results (master lines 777–781). TP4/PP2 is the only 8-GPU layout that crosses the network.
8. **What is not covered.**
   - Two TP4/PP1 servers side by side on one node, on GPUs 0–3 and 4–7 and two ports, each at the same load, against one TP8/PP1 server at the combined load.
   - A two-server copy of the prefix-decay case (`tp4_r2_agentic_prefix_cache_decay`) for TP4/PP2, in a group the two-server runner runs, for prefix caching across nodes. The single-node runner always builds a single-node server (`11_run_vllm_surrogate.py` line 59).
   - Once the expert-parallel start-up check passes, one serving run with `--enable-expert-parallel` on TP8/PP1 at 8K c8 and c32 and 128K c4, against the same points from the TP8 baseline (fix 1).
   - FP8 KV: keep the server log of the next attempt. If the start fails in vLLM itself for this model, mark FP8 KV out of scope rather than retrying it.

**When it counts.** These fixes give coverage in the scripts. It becomes coverage in data once a full run gets through on the chosen settings: the real smoke test passes (blocker 12), the reference point agrees (section 9, item 7), the pause and stall screen is clean, and the headline points have their repeats.

## 7. The feedback, item by item

*Runs once executable: whether that part would work with the scripts as they are, once the `.sh` files are executable and a run reaches it.*

| Item | Written | Runs once executable | Note |
|---|---|---|---|
| One vLLM build, pinned and recorded on both nodes | No | No | Blocker 10; a readiness gate exists but is not called |
| MoE backend set by flag on every launch, checked at start-up | Partly | Partly | Agreed: FlashInfer CUTLASS. Runners yes, if the help text lists the flag; B1, the torch profiles and step 4 no; no start-up check |
| Autotune set explicitly | No | – | On by default at O2. The skip list leaves out the two CUTLASS GEMMs; the team decides it with section 5 |
| The clean-folder NCCL library on every worker, mapped library recorded | Partly | Partly | Path propagated, environment audited; folder not ensured on node 1; mapped file not recorded; vLLM's own communicator now off |
| NCCL check on the servers to be used (library arms, iperf3, nccl-tests at 16 KiB, 32 MiB and 256 MiB, TP16 at 128K) | Partly | Partly | `03_run_network_sweep.sh` covers iperf3 both ways and nccl-tests from 16 KiB to 256 MiB, but the master does not call it. Step 3 runs a socket-thread sweep only, with no library arm |
| Expert-parallel start-up check (TP8/PP1, 8 GPUs, at 8,192, with and without `--enable-expert-parallel`) | No | No | The flag exists in 0.29.0 |
| Steady-arrival runs on two servers | Yes | No | Block 7: all four layouts at 8K and 128K; blockers 4 and 11 |
| One request at a time below 128K on two servers | Yes | PP2 only | 1K and 8K on all four layouts; blocker 4 |
| Two servers under load | Yes | PP2 only | 1K–1M, up to 32 in flight, but 16 at once (section 4) |
| Decode profiles on two servers | Yes | No | Nsight: four layouts, eager. Torch: three layouts (no TP4/PP2), graphs on. The Nsight driver stops at a missing file (blocker 3), and step 14's mode filter matches none of its profiles. The torch ones sit behind blockers 2 and 5. Section 6, fixes 2 and 3 |
| Nsight Compute kernel captures | No | No | Section 6, fix 4: TP4/PP1 and TP8/PP1 once counter access is checked, TP16/PP1 once a wrapper exists |
| Repeats with a spread | Partly | No | Knee case only: 3× at 8K with 16 in flight and 128K with 4, on TP4/PP1 (blocker 4); none on 8 or 16 GPUs (section 6, fix 5) |
| Network conditions applied and recorded | Partly | No | Step 12 runs no case (blocker 2); caps on node 0 only (blocker 9); labels reset to native (blocker 8) |
| Both nodes' logs kept | Partly | Partly | Serving runs bring back node 1's GPU telemetry only, and no serving start in the pilot or stages 1–3 kept its server log (section 5). The Nsight driver would keep Ray worker logs but stops before that (blocker 3), and 14d keeps none. The main suite's single-node runs have no sampler at all (blocker 3) |
| Warm-ups | Partly | Yes | Main suite: before every server's first measured run, except the offload case (128K first) and R2 (cold by design). Batching blocks 4 and 7 (10 of 28 servers) and all the profiles have none |
| Pause screen | Yes | Partly | Step 16 reads the per-request files, so it works over whatever was captured. But it treats any path containing "profile" as a profiler capture and never counts its pauses, so step 12's runs (in `step12_capped_profiles`) would be skipped |
| Two long prompts, step budgets, request caps and mixed traffic beyond TP4/PP1 | Yes | No | Batching blocks 1–4; blockers 4, 11 and 13 |
| First-repeat rule at 1M (a whole-block prefix with 256- and 576-token suffixes; the retention interval) | Partly | No | One unused case: a 999,744-token prefix with a 256-token suffix, 576 tokens past the last whole block, which repeats the miss already measured. No whole-block or retention arm |
| Two TP4 copies on one server; prefix caching beyond TP4/PP1 | No | No | Section 6, fix 8 |
| Coverage on 8 and 16 GPUs: lengths, loads, profiles, depth | Partly | PP2 only | Section 6: the TP8 baseline is unused, 1 of the 24 two-server Nsight captures is selected, mid lengths run on TP8/PP1 only, and long-prompt points have 2–8 requests |

## 8. Smaller points

- Step 15 runs `tools/compile_canonical_data.py` and `tools/run_v1_4_verification.py`. The folder holds neither, and `|| true` hides the failure.
- Step 20 compares the minimal-telemetry case (8K) with the short-prompt case (1K/2K). These are different workloads, so the difference is not telemetry's cost. Run one case twice, once per observability profile.
- There are two master runners with different case files (`scripts/` and `07_master_campaign_orchestration/`), plus older copies (`rtx_g4_*`). Keep one; the single flow may already have done this.
- The setup manual's ray 2.35.0 and triton 3.0.0 also disagree with the readiness gate (ray 2.58.0, triton 3.7.1).
- Step 11's two arms run the same cases into two folders, and one summary is built over both. Its rows carry neither the folder nor the split, so the A/B comes out as identically labelled pairs. Add both to each row.
- Rename `step12_capped_profiles`, or mark profiler captures explicitly, so the pause screen counts step 12's runs.
- The profile runs send no warm-up, so every trace starts with the server's first requests. Send a short warm-up before the trace starts.
- The first benchmark of each case warms up with the same seed as its measured run. This is harmless today, because no case with prefix caching on warms up its first benchmark. Give warm-ups their own seed before one does.

## 9. Before the first full run

1. Fix blockers 1–7, 11 and 13. Each one stops a run or empties part of it, and most are a few lines.
2. Keep only addresses and paths in `RUN_CONFIG.env` (blocker 8). Leave the layer split unset; set the network labels and the selections per case or per run, and select the batching blocks with `--cb-blocks`.
3. Install the chosen wheel by file on both nodes, check its hash, and run `22_readiness.py` in step 0 on both nodes.
4. Pass `--moe-backend flashinfer_cutlass` and `--enable-flashinfer-autotune` on every launch, keep nvcc on PATH on both nodes, and take `VLLM_DISABLE_PYNCCL` out everywhere (section 4). Run the A/B in section 5 and decide the skip list.
5. Fix the network steps (blocker 9), and remove any cap the set-up left.
6. Smoke test for real (blocker 12), including the telemetry files and the start-up lines.
7. On the servers you will use, run the reference set-up once at 128K, one request at a time, on the chosen settings, and compare it with the A/B's TP4/PP1 128K point for the arm you kept (section 5). If they agree within the spread between the A/B's repeats, start the full run with `--new-run`.
8. Add the missing runs:
   - the NCCL library A/B, with the network sweep on both nodes;
   - the expert-parallel start-up check;
   - Nsight Compute on the B1 decode step and on one 128K prefill;
   - the 1M first-repeat arms: a 999,424-token whole-block prefix with 256- and 576-token suffixes, and the retention interval;
   - two repeats of each headline point (1M with 4 in flight, 128K with 4 and 8, 8K with 32), with a server restart between them;
   - the coverage fixes in section 6.

## 10. After the first full run (later)

Left out of this review's scope on purpose, and not needed for the first full run. Once one full run has passed with the fixes above, decide whether to add:
- other models, and other vLLM builds;
- more than two nodes;
- quantized weights;
- data parallelism across nodes, and accuracy checks (stage 3's plan left both out).

## 11. How this was checked

`audit/check_scripts_review.py` reads the scripts, the zip as shared (for the file modes), the vLLM 0.29.0 release wheel and the FlashInfer 0.6.18 wheel, and asserts the findings above about the scripts and the two wheels: 162 of 162. It does not install or import either wheel. The one piece of vLLM it runs is `get_pp_indices`, taken from the wheel's source.

It also confirms these behaviours directly in a scratch folder:
- `get_pp_indices` with the scripts' splits;
- node 1's interface lookup, replayed with awk on a typical `ip route get` line;
- `pkill -f` killing the shell that calls it;
- `run_step` ending the whole run on one failed step;
- an unexported function, an unexported variable, and `local`, inside `bash -c`;
- a `bash -c` body reporting only its last command's status;
- `source` of a missing file ending a script under `set -e`.

`audit/check_autotune_skip.py` reads each log set in place (a folder or a zip, with nested archives read in memory) and prints the run records' settings and checks C1–C8 per set, the cross-set comparisons in section 5 (kernel times, start-up order, which build), and the layer-split A/B where a set holds one; for section 6, it also counts the KV cache type of every serving start, and how many became ready; and it names the Ray actor the worker logs show (section 4). It writes nothing, masks home folders and prints no archive names. Its output on the pilot and stages 1–3 is `audit/check_autotune_skip_out.txt`.

`audit/coverage_matrix.py` reads the main and batching case files, the two-server profile matrix, the profile scripts' defaults and the master runner, and prints section 6's table: the serving points per layout by step or batching block, the points vLLM would refuse, the cases no step runs, and the profiles the master selects. It runs nothing and imports nothing from the scripts. Its output on the folder as shared is `audit/coverage_matrix_out.txt`.

Independent passes over this review found several of the blockers above and, for v1.2 and v1.3, corrections to sections 4–6. Each was verified, and the facts behind it were added to the checkers.

```
python3 -I check_scripts_review.py <Performance_Intelligence_Platform dir> <vllm-0.29.0 wheel> <scratch dir> <the zip as shared> <flashinfer_python-0.6.18 wheel>
python3 -I check_autotune_skip.py pilot=<pilot results folder or zip> stage1=<stage 1-2 raw_runs zip>::raw_runs/stage1/ stage2=<stage 1-2 raw_runs zip>::raw_runs/stage2/ stage3=<stage 3 raw_runs zip>
python3 -I check_autotune_skip.py A=<arm A folder> B=<arm B folder>
python3 -I coverage_matrix.py <Performance_Intelligence_Platform dir>
```
