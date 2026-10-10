# Task: add waves, stalls and pauses to our benchmark tools, and keep the server's own record of every run

You are working in `Performance_Intelligence_Platform` in the `gke-ai-infrastructure` repo. Start by mapping it: where `vllm serve` is started and its output written, where the `vllm bench serve` command is built, the warm-up step, the `/metrics` sampler, the packaging step, and the analysis scripts (`bench_summary.py`, `ttft_waves.py`, `metrics_diff.py`, `server_log.py`). The campaign harness we ran used `v5_runner_lib.py` (`build_server_cmd`, `build_bench_cmd`, `run_warmup`), `09_metrics_sampler.py` and `12_run_vllm_multi_node.py`; use their equivalents if names differ. Show me the map and a plan before changing code.

The reference implementation is attached (`pip_waves.py`, `pip_scan.py`, `pip_timeline.py`, tests and expected values). Port it into the repo's tools; keep its definitions and thresholds.

## Why

Every `--save-detailed` result file already holds each request's send time, first-token time and every token gap. Read together, they show who waited for whom, which the run summary cannot. On the two archives this showed:

1. **Long prompts are read one at a time on every layout.** In a burst, the k-th request waits about k reads. At 1M with 4 in flight the first wave averages 2.41–2.47 reads against the 2.5 that one-at-a-time predicts, on all six layouts. At 128K with 8 in flight it is 3.77–4.51 reads against 4.5.
2. **Pipeline stages read short prompts side by side.** At 8K the first-wave prompts start 0.50–0.51 reads apart on 2 stages and 0.26 on 4 stages, against 0.88–0.93 with no stages. At 128K the spacing stays at 0.79–0.99 reads.
3. **Under load at long prompts, answers mostly wait.** While a prompt is being read, every answer in progress gets one token per read step (0.27–0.89 s) instead of one per decode step (9–17 ms). Answers spend 87–100% of their time stalled at 128K and 8–29% at 8K with 8 in flight.
4. **Three runs stopped every token for 1–4 s, and their summaries can't show it.** Each was the first run on a fresh server, after a warm-up of 2 prompts at 2 in flight. Their p99 token gap was 8.7–30.7 ms. One of them turned a 13% A/B effect into an apparent 42%.
5. **Closed-loop averages are mostly the opening burst.** In one run the first wave was 57% of all waiting, and the run mean described 3 of 128 requests.

What we could not answer: why the pauses happened (the archives we received have no `server.log` or metrics time series), and how each request's wait splits into queue and prefill (the engine reports only run means).

## Part 1 · Recover the evidence we already have (no code)

The harness writes `server.log` per case, plus `metrics_node0.jsonl`, `metrics_raw.prom.log` and `metrics_node1.jsonl` per benchmark. Every second-campaign server ran with `--enable-logging-iteration-details`. These files were left out of the archive we received. Please copy them from the run machine or bucket for these three cases, plus the warm-up and bench stdout logs:

- `stage1/01_chunk_budget_ab/control/tp4_8k_chunk_control_8192` (bench `8k_c4`): the pause starts 0.66 s after the first request and lasts 3.98 s.
- `stage2/03_multi_node_load/tp4_pp2_dist_load` (bench `8k_c8`): 1.50 s in, 3.97 s long.
- `stage2/03_multi_node_load/tp8_pp2_dist_load` (bench `8k_c8`): 0.65 s in, 1.02 s long.

For the multi-node cases, also copy the Ray session logs from both nodes.

To find each pause in `server.log`, start from `benchmarks[].start` in `case_manifest.json`. That is the wall-clock time just before the bench started; the first request leaves a few seconds later, once the client has built its prompts. Look for a gap of a second or more between consecutive iteration-detail lines. Then report every line in that window: compile, CUDA graph, autotune, NCCL, warnings. Do the same check in `metrics_node0.jsonl`.

## Part 2 · Change the harness so every run keeps its evidence

1. **Warm up at the measured concurrency.** Today `run_warmup` sends `warmups` prompts (2) at `min(C, warmups)` in flight. Change it to at least `max(warmups, 2·C)` prompts at C in flight, with the run's own prompt and answer lengths, and keep it out of the results. This is a guard, not a proven fix: four other fresh servers with the same 2-prompt warm-up ran clean.
2. **Ship the evidence.** Package `server.log`, every `metrics_*.jsonl`, `metrics_raw.prom.log`, `bench_stdout.log`, `warmup_stdout.log` and the Ray logs from every node, gzipped, next to each run's result JSON.
3. **Timestamp every server line.** Read the server's stdout through a pipe and write `"%.6f %s" % (time.time(), line)` to `server.log`, with `PYTHONUNBUFFERED=1` set. vLLM's own log time is to the second, which cannot place a 1 s pause.
4. **Record a clock pair.** Store `time.time()` and `time.monotonic()` in the benchmark record just before launching `vllm bench serve`. The bench's `start_times` come from `time.perf_counter()`, which on Linux reads the same monotonic clock. So the wall time of a request is `start_time - mono + wall`.
5. **Server logging.** Set `VLLM_LOG_STATS_INTERVAL=1`, keep `--enable-logging-iteration-details` on every load run, and set `TORCH_LOGS=recompiles` so a runtime recompile leaves a line. Check each name against the installed build's `--help` or source first; use the existing `add_if_supported` pattern for flags. Record the observability profile in every manifest; the second campaign's are empty.
6. **Bench.** Use `--metric-percentiles 50,95,99,100`, so the summary's maximum token gap shows a pause that the p99 hides. Keep `--save-detailed`.
7. **Server order.** Record each run's position on its server (1st, 2nd, ...), the server start and ready times, and the time since ready, in the benchmark record.
8. **Per-request engine timings (optional).** If the build supports OpenTelemetry traces (`vllm serve --otlp-traces-endpoint`), send the spans to a local collector that writes JSON. They give each request's own queue and prefill times, which makes the per-request split exact. If the flag is absent, skip this and say so.

## Part 3 · Add the analysis

Definitions, thresholds and formulas are in the `pip_waves.py` docstring; keep them. In short:

- **Order and waves.** Requests are ordered by send time (warn if that differs from file order). The first C requests are the first wave and are exact; later waves are approximate.
- **Reads.** The lone read R is the first wave's shortest wait. "Reads" means a wait divided by R. The one-at-a-time rule predicts a first-wave mean of (C+1)/2 reads.
- **Stall.** A token gap over 100 ms. Report how many gaps fall between 60 and 150 ms, to show the split is clean.
- **Decode silence.** The longest stretch with someone mid-answer and no token to anyone.
- **Normal step.** The larger of R × B / I and the p99 token gap, where B is `--max-num-batched-tokens` and I is the prompt length.
- **Pause.** A decode silence of 3 normal steps or more. Profiler captures never count.

Build these:

1. **`ttft_waves.py`:** keep today's lines. Add the first wave in reads, the mean against the rule, the spacing ("a prompt every X reads"), the later mean, the burst's share of all waiting, and first-wave prompts per step.
2. **`bench_summary.py`:** add flags:
   - `PAUSE x s at t s (n normal steps; run k on its server)`
   - `BURST p% of waiting; steady wait w s`
   - `STALLED q% of answering`
   - the maximum token gap
3. **A scan command** (`pip_scan.py`) over any results folder: one CSV row per run, the pause list, and the run's position on its server.
4. **A timeline PNG per run** (`pip_timeline.py`).
   - **Request rows:** grey `#C9C2B6` in line; red `#9b1c1c` prompt being read (prefill); blue `#1c4f95` answer being written (decode); grey with a thin blue line for an answer stalled while another prompt is read.
   - **Pause:** a pink `#F4E9E9` band; inside it every request is waiting.
   - **The engine, above the rows:** how many prompts are being read, and how many answers are getting tokens or stalled.
   - Text never overlaps; the script checks this and fails rather than overlap.
5. **`server_log.py`:**
   - Parse the time-stamped lines: stats lines into a time series of running, waiting and KV use; iteration-detail lines (write the pattern from real lines, and print samples when nothing matches); compile, CUDA graph, autotune, NCCL and warning lines.
   - Align them with requests through the clock pair.
   - For every pause, print the lines from 2 s before it to 1 s after it, and the longest gap between iteration lines.
6. **Metrics:**
   - From `metrics_node0.jsonl`, take per-scrape deltas of the tokens-per-iteration histogram, where present (steps per interval, tokens per step). A pause shows as an interval with no steps.
   - Check the drawn timeline against the gauges: reads plus answers in progress against running, and in line against waiting.
   - Check the drawn mean read against the engine's prefill histogram mean. At 128K and 1M the engine's figure is 1.01–1.15× the drawn read. At 8K it is 1.6–2.5×, because the engine counts from a prompt's first chunk, and under load an 8K prompt's chunks spread over two or more steps and through every stage.

## Rules

- Never edit the result archives; write outputs next to each run or to a new folder.
- Keep today's command lines and output lines working; add, don't replace.
- Every printed number comes from the files; thresholds are flags with the defaults above.
- Use Python 3.10+, the standard library for analysis, and matplotlib only for figures. Add tests with each change.

## Done when

- `python3 test_pip_waves.py` passes its 8 synthetic tests; the ninth, the archive test, skips until the two folders below are set.
- With `PIP_PILOT_ROOT` set to the pilot's `real_data` folder and `PIP_SECOND_ROOT` set to the second campaign's `raw_runs` folder, the same tests reproduce `expected_values.json`: 24 run fixtures within 0.5%, and the scan's 3 pauses. Run your ported code against the same values.
- On a new run with the Part 2 changes, the archive holds the time-stamped `server.log`, the metrics time series and the clock pair. `bench_summary.py` prints the pause, burst and stall lines. `server_log.py` prints the log window around any pause.
- Part 1's files are shared, along with what the log shows at each of the three pauses.

## Files in the kit

- `pip_waves.py`: one run's waves, stalls, pause and drawn phases. `python3 pip_waves.py <run.json> [--budget 8192] [--json out.json]`
- `pip_scan.py`: the pause scan over folders. `python3 pip_scan.py <folder> [<folder> ...] [--csv scan.csv]`
- `pip_timeline.py`: the timeline figure. `python3 pip_timeline.py <run.json> --out run.png [--title "..."]`
- `test_pip_waves.py`: the tests above.
- `build_expected_values.py`: rebuilds `expected_values.json` from the two archives.
- `expected_values.json`: the reference values; each fixture names its input file's md5.
- `example_timeline.png`: what `pip_timeline.py` draws for the TP4/PP2 8K run with its 4 s pause.
