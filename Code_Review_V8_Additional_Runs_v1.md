# Code review — V8 additional runs, Stage 1 and Stage 2

*Package reviewed: `v8_additional_runs_stage1_stage2.zip` (66 files). Reviewed 5 Oct 2026 against the run list (items 1–10), the re-run plan v1.4 and the pilot archive. Every claim below was checked in the code or the archive; nothing was run on the cluster.*

## Verdict

The package is built the right way: it reuses the pilot suite unchanged (hash-identical to the suite the pilot ran, except two files), isolates outputs, checkpoints every step, keeps each server's log, and preserves the V6/V8 NCCL policy. But as written it would run for about 5.5 hours and leave most of the questions open:

| Run list item | Status as written |
|---|---|
| 1 · 8K chunk budget | **Works** — small fixes (same prompt counts as the pilot, a same-session control) |
| 2 · Two-node layouts under load | **Works** — set and check the network mode; more waves at 128K |
| 3 · PP2 15/12 split | **Does not test it** — no partition is set, and it runs on one node |
| 4 · TP8 pinned to sockets | **Does not test it** — nothing pins anything |
| 5 · 8-GPU KV pool | **Does not test it** — the script reads a metric that does not exist, and never reads the pool size |
| 6 · Torch capture at c8 / c32 | **Needs a fix** — the profile window is mostly prefill |
| 7 · Prompts under 8K | **Works** — few waves at c32 |
| 8 · TP16 512K re-capture | **Will likely fail again** — the export fix is in the wrong place |
| 9 · NCCL plugin and socket threads | **Does not test it** — it runs iperf3, not NCCL |
| 10 · Closed-loop edges | **Does not work** — the trimming script reads keys that do not exist |
| Stage 2 · FP8 KV | Drops the 1M point, the one the predictions rest on |
| Stage 2 · KV offload | The fix lets the server start but removes the pressure the test exists for |
| Stage 2 · Capped profiles | Same export bug as item 8 |

It also will not start as unpacked: the zip was made on Windows and carries no execute bits (§4).

## 1. Before any run: three free checks

1. **Read the pilot's server logs on node 0.** The shared archive has no `.log` files at all; the runner did write `server.log` for every case (`11_run_vllm_surrogate.py` line 65), so they should still be in the original results directory (`/home/ayu23/v8_full_results/20260921_195656/...`). Three of them settle three things at zero machine cost:
   - `tp4_fp8_kv`, `tp4_fp8_kv_1m` and `tp4_native_offload_pressure`: the archive records only `"server exited rc=1"` after 126–134 s of start-up. The README's causes (a missing `--attention-config` key; a "256-block minimum") are hypotheses until these logs are read.
   - `tp4_context_baseline` and `tp8_context_baseline`: the "GPU KV cache size: N tokens" line answers item 5 outright.
2. **Look for full copies of the failed Nsight reports.** The failed pilot reports were 0-byte files copied out of `/tmp/ray/session_*/logs/nsight` (§2, C4). If those session directories still exist on either node, complete reports (e.g. `worker_process_1086878.nsys-rep` for TP8/PP2 decode) may be there, and they can be re-exported without a re-run.
3. **Fix the packaging** (§4, L1) — otherwise the first command fails with "Permission denied".

## 2. Findings, most severe first

### Critical — the run completes but does not answer its question

**C1 · TP8 pinning is not implemented** (`stage1_cases.json` · `tp8_numa_pinned`; `11_run_vllm_surrogate.py`). The case has no pinning field, and the runner only sets `CUDA_VISIBLE_DEVICES`. The server command it generates is the pilot's TP8 command with `--max-num-seqs 32`; nothing binds a rank to a socket. Note also that `numactl` in front of `vllm serve` cannot do this: all eight workers would inherit one policy.
*Fix:* keep the server up and run the unpinned 8K c1 first as the control. Then pin each worker to its own GPU's CPUs and rerun 8K c1 on the same server:
```bash
nvidia-smi --query-compute-apps=pid,gpu_bus_id --format=csv,noheader | while IFS=', ' read -r pid bus; do
  dev=$(echo "$bus" | sed -E 's/^[0-9A-Fa-f]{4}([0-9A-Fa-f]{4}:)/\1/' | tr 'A-F' 'a-f')   # 00000000:05:00.0 -> 0000:05:00.0
  taskset -a -cp "$(cat /sys/bus/pci/devices/$dev/local_cpulist)" "$pid"
done | tee PINNING.txt
```
The primary metric is the serving token. If the serving-only ~21 µs per AllReduce (58.7 vs 37.6 µs) is host-side, 55 calls per token take the TP8 8K c1 token from 6.35 ms to about 5.2 ms. If it stays at 6.35 ms, pinning is ruled out.

**C2 · The PP2 15/12 split is not set, and it runs on the wrong topology** (`stage1_cases.json` · `tp4_pp2_split_test`). `VLLM_PP_LAYER_PARTITION` appears nowhere in the package, so the default 14/13 split runs. The case also goes through the single-node runner, so it is TP4/PP2 on 8 GPUs of one node. The pilot's PP2 runs, and the cost model's −3.5% prediction, are for the two-node layouts, and the pilot has no single-node PP2 run to compare against. The case also lacks 512K, where the prediction is largest, and TP8/PP2.
*Fix:*
- Run it through `12_run_vllm_multi_node.sh` with copies of `tp4_pp2_dist` and `tp8_pp2_dist` at 128K and 512K c1, using the pilot's prompt counts and output lengths (128K: 4 prompts, 64 out; 512K: 2 prompts, 32 out).
- Export `VLLM_PP_LAYER_PARTITION=15,12` on both nodes before `ray start`. Today the remote export string (`nccl_remote_v6_aligned_exports`) carries only `NCCL_*` and `LD_LIBRARY_PATH`, so node 1's workers would not see it.
- Add a default-split control in the same session.
- Confirm the stage layer ranges in the server log.

**C3 · The NCCL tuning step measures iperf3, not NCCL** (`23_run_nccl_socket_tuning.sh`).
- It runs iperf3 with 4 streams as "baseline" and 16 streams as "tuned", after exporting `NCCL_SOCKET_NTHREADS`/`NCCL_NSOCKS_PERTHREAD`. iperf3 ignores both variables, so the "speedup" is 16 streams against 4 and says nothing about NCCL.
- It never starts an iperf3 server on node 1. If none is still running there, the errors are swallowed by `|| true`, so the summary is null and the step still passes.
- There is no nccl-tests run and no provider-plugin variant.

*Fix:* reuse the `mpirun … sendrecv_perf / all_reduce_perf` lines of `03_run_network_sweep.sh`. Pass the variables through with `-x` (exports in the launching shell do not reach the remote rank), and run three variants:
- (a) the pilot's configuration (`NCCL_NET=Socket`, `/tmp/clean_nccl_libs`, default threads);
- (b) `NCCL_SOCKET_NTHREADS × NCCL_NSOCKS_PERTHREAD` = 4 × 4, and 8 × 2;
- (c) the provider plugin on.

Use `NCCL_DEBUG=INFO` to prove which transport ran, then compare the 16 KiB AllReduce (227–290 µs today) and the 256 MiB SendRecv (7.1 GB/s today).

**C4 · The Nsight export fix is in the wrong place** (`18_run_vllm_multi_node_profiles.sh`). The pilot's failed reports were 0-byte files: 15 of 16 for TP8/PP2 decode and 9 of 12 for TP16 512K, each exporting as "Cannot read from stream" (`NSYS_ANALYSIS.json`). In other words, they were copied before nsys had written them. The new 15-second sleep runs *after* the copy (copy at "sleep 5 … cp -a", new sleep just before `ray stop`), so it cannot help. `ray stop -f` then kills any nsys still writing. `PROFILE_VALIDATION.json` only checks that a report file exists, so a 0-byte capture counts as complete. Item 8 and the five capped profiles will likely fail the same way.
*Fix:* before copying, on each node, wait until no nsys process is left and every report is non-empty and unchanged; then copy; then stop Ray:
```bash
wait_nsys(){   # $1 = <ray session>/logs/nsight on this host; up to 15 min
  local prev="" cur
  for _ in $(seq 1 90); do
    cur=$(find "$1" -name '*.nsys-rep' -printf '%f:%s\n' 2>/dev/null | sort)
    if ! pgrep -f 'nsys (profile|launch)' >/dev/null && [[ -n "$cur" && "$cur" == "$prev" ]] \
       && [[ -z "$(find "$1" -name '*.nsys-rep' -size 0)" ]]; then return 0; fi
    prev=$cur; sleep 10
  done; return 1
}
```
Make validation require, for every expected rank (TP × PP), a report larger than 0 bytes and a kernel table with rows; otherwise wait and copy again.

**C5 · The KV audit and the trace trimming do not work** (`24_audit_kv_and_trim_traces.py`).
- It reads `vllm_gpu_cache_usage_factor` from `metrics_gpu.jsonl`. The sampler writes `vllm:kv_cache_usage_perc` inside `{"kind":"prometheus","metrics":[…]}` records, so the peak is always 0.
- It reads `detailed_results` from the benchmark JSON. The file holds `ttfts`, `itls` and `start_times` arrays, so it always returns "too few requests".
- It trims 10% from each end in list order, not the first and last wave.
- It runs only on the TP4 chunk run, and it never reads the pool size, which is the actual question.

*Fix:*
- **Pool size:** take it from `server.log` (`grep -E "GPU KV cache size|Maximum concurrency"`) for TP4 (item 1's server) and TP8 (item 4's server), or from the `vllm:cache_config_info` metric.
- **Trimming:** sort requests by `start_times`. Drop the first `concurrency` requests from the first-token statistics and the last `concurrency` from the token statistics. This is the definition used on the note's E2E · C/D pages.
- **Scope:** apply it to the pilot's closed-loop runs, not only the new one.

**C6 · The offload rerun will not exercise offload** (`stage2_cases_single_node.json` · `tp4_native_offload_fixed`).
- At 8,064 B per token per rank, 8.5 GiB holds 1.13 M tokens, so every test prompt (128K, 512K, 1M, one at a time) fits on the GPU.
- With prefix caching off, nothing is ever looked up and reloaded.
- The runs would therefore report a BF16 baseline under another name.
- The pilot's 4 GiB held 0.53 M tokens, below `--max-model-len 1048576`, which needs 7.9 GiB. That check is the likely start failure, not a "256-block minimum"; the log in §1 will confirm it.

*Fix:* make it a reuse test, with prefix caching on: cold prompt A, then cold prompt B large enough to push A out of GPU memory, then A again. At 1M, use two prompts of about 600K tokens on the 8.5 GiB pool; alternatively, lower `--max-model-len` and keep 4 GiB. Record the offload counters (`offload_bytes`, `offload_time`). The prediction to test is that the revisit's first token takes about 0.3 s at 1M, against 93 s cold.

### High — the run answers a narrower question than planned

**H1 · The FP8 rerun drops 1M** (`tp4_fp8_kv_fixed`). The four failed runs were 128K c1, 128K c4, 512K c1 and 1M c1. The new case swaps 1M c1 for 8K c8, but 1M c1 is the point behind the 10.3 → 7.9 ms prediction, and its start log gives the KV pool size behind D3's pool prediction.
- The `--attention-config` key is unverified.
- `add_if_supported` silently drops the flag if the CLI does not list it, so the server would fail again in the same way.

*Fix:* add `1m_c1` (32 output tokens, 1 prompt, `--max-num-seqs 8` as the pilot had). Make the flag required (`require_flag`) for this case. Read the pilot's `server.log` first (§1).

**H2 · The batched torch capture profiles mostly prefill** (`14c_run_vllm_torch_profile_batched.sh`). `--profile` starts before the first request and stops after the last, so the window holds all the prefills. At c32 that is 32 × 8K prompts, about 6–7 s of prefill against about 2 s of decode, and in mixed steps the kernels cannot be told apart.
*Fix:*
- Drop `--profile` and make the output long enough that decode outlasts the prefills (e.g. 1,024 tokens).
- Call `/start_profile` after the last first token (about 15 s in at c32), and `/stop_profile` about 3 s later.
- Start the profile server with the serving flags (`--gpu-memory-utilization 0.9 --performance-mode balanced --optimization-level 2`).
- Check that the per-step kernel sum closes on the serving own step: 7.7 ms at c8, 15.8 ms at c32.

**H3 · The chunk check is not a clean A/B** (`tp4_8k_chunk_fix`). c32 has 64 prompts (2 waves) against the pilot's 128 (4 waves), and there is no 8,192 control in the same session. *Fix:* use the pilot's counts (c4: 24, c32: 128) and add a same-session run at 8,192. That costs about 3 minutes.

### Medium

- **M1 · Multi-node load** (`02_run_stage2…`, `stage2_cases_multi_node_load.json`).
  - **Network not set or checked.** `12_run_vllm_multi_node.sh` is called directly, so unless `RUN_CONFIG.env` sets the provenance, rows are labelled `GCP_UNSPECIFIED`; and a tc class left over from a capped run would cap them silently. Run it through `20_run_vllm_network_matrix.sh` in native mode, or check `tc qdisc` and iperf3 on both nodes and set `V8_GCP_NETWORK_PROVENANCE_OVERRIDE=GCP_NATIVE`.
  - **Few waves at 128K.** The 128K points have 3 waves; use at least 5 and trim the first.
  - **Missing points.** TP4/PP2 lacks 1M c4, and the plan's 8K c8 is missing.
- **M2 · Short prompts.** c32 runs only 2–2.5 waves, and the plan's open-loop sweep is missing.
- **M3 · Resume and provenance.**
  - **Resume:** it works only if you pass the same `--run-id`; by default every start makes a new root.
  - **No hash manifest:** the package has none, though the pilot kept `SUITE_SOURCE_SHA256SUMS.txt`.
  - **Node 1 not snapshotted:** the environment snapshot covers node 0 only.
- **M4 · `--help=all` in `v5_runner_lib.py`.** Harmless for the flags the pilot used: a simulated server command for the chunk case matches the pilot's apart from 8,448 and the port. Still, diff each new `SERVER_COMMAND.txt` against the pilot's for the same case before analysis.

### Low — packaging and README

- **L1 · Windows zip.**
  - **Paths:** backslash separators.
  - **Permissions:** no Unix mode bits at all. The scripts call each other directly (`"$SUITE_ROOT/01_run_stage1_quick_wins.sh"`, `"$VLLM_DIR/20_run_single_node_v6_aligned.sh"`), so the run stops at "Permission denied".
  - **Bytecode:** `__pycache__` (CPython 3.14) is included.

  Re-zip on Linux or macOS, or `chmod +x` every `.sh` after unpacking. The line endings are fine, and every script passes `bash -n` and `py_compile`.
- **L2 · README corrections.**
  - **GPU model:** the GPUs are RTX PRO 6000 Blackwell Server Edition, not "Ada".
  - **PP2 rationale:** the 15/12 split balances full-attention layers (stage 0 holds 3 of 7), not embedding or head compute.
  - **Failure causes:** they are stated as facts but are unverified (§1).
  - **FP8 list:** "8K, 128K, 512K" is not the four failed runs.
  - **"Pinning policies":** V8 had none.
  - **"Zero-risk":** the suite changes tc qdiscs with sudo; it does restore them on exit.
  - **Capped profiles:** they run 8 captures (including the 3 that exist), not 5.

## 3. What is good and should stay

- Isolated output root, so historical results are never touched; per-step `.done` markers; a JSONL step log.
- The pilot suite is reused as-is: 37 of the 39 pilot suite files in the package are hash-identical to the suite the pilot ran (2 changed, 3 new).
- The single-node runner writes `server.log`, `SERVER_COMMAND.txt`, per-benchmark commands, detailed results and metrics for every case.
- The NCCL policy is preserved: local P2P and SHM forcing are cleared, and the Ray environment is audited on both nodes.
- The `awk` quoting fix for the remote interface lookup in `18_run_vllm_multi_node_profiles.sh` is correct: the old line lost the quotes around `dev` inside the ssh string.
- The FP8 `attention_config` is stored as a JSON string, so it reaches the CLI as valid JSON.

## 4. Not in the package

From the brief's pending list, two items are still missing. They are worth adding if the run goes ahead (about 30 min together):
- the 128K stall-vs-chunk test (plan A9);
- the 3× repeats of the two usable-throughput knee points.

## 5. Suggested order once fixed

1. Do the free checks in §1.
2. On one node, TP4: item 1 with its control (keep the log for item 5); item 6 with the decode-only window; FP8 including 1M; item 7.
3. On one node, TP8: item 4, control then pinned on the same server (keep the log for item 5).
4. On two nodes: item 9 with nccl-tests; item 3 through the multi-node runner with its control; item 2 in native mode.
5. Item 8 and the capped profiles, only after the wait-for-nsys fix.
6. Offload, as a reuse test.
7. Items 5 and 10 as analysis (the fixed script).
