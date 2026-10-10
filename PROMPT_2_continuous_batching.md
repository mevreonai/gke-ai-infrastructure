# Task 2: measure continuous batching: its settings, mixed traffic, memory pressure, long answers and steady arrivals

This follows Task 1 (`PROMPT.md`) and uses the same kit. Do Task 1's harness changes first: warm-up at the run's concurrency, the time-stamped `server.log` kept with each run, the clock pair, iteration-detail logging on, and the maximum token gap in the summary. Every run below depends on them. Run the kit's analysis on every run (`pip_waves.py`, `pip_scan.py`, `pip_timeline.py`) and Task 1's `server_log.py`.

## How the scheduler batches, and what our runs showed

vLLM batches continuously. Each engine step first serves the requests already running: one token for each answer, and the next chunk of any prompt being read. It then fills what is left of its token budget with prompts waiting to start. Requests join and leave at every step.

Both campaigns ran vLLM 0.29.0. In its scheduler (`vllm/v1/core/sched/scheduler.py`), a prompt being read takes all the budget left unless `--long-prefill-token-threshold` caps its chunk, and none of our runs set it. So a request that arrives during a long read waits for that read to finish.

Our runs exercised batching whenever more than one request was in flight: 46 of the pilot's 119 runs and 39 of the second campaign's 56. They showed:

- **Answers batch well.** At 8K on TP4/PP1, 32 requests in flight cost 76% less per request than one at a time.
- **Long prompts are read one at a time.** At 1M, the first tokens of four requests sent together land one read apart on all six layouts (0.94–0.98 reads).
- **Short prompts share a step.** A step of 8,192 tokens reads up to 8 prompts of 1K, 4 of 2K, or one of 8K.
- **The cost is stalls.** While a chunk is in the step, every answer waits for it. At 128K with 8 in flight, answers spend 87–100% of their time stalled. On TP4/PP1 at 128K with 4 in flight, the stall followed the budget: 161, 270 and 536 ms at 4K, 8K and 16K. Over the same budgets a lone read took 5.25, 4.54 and 4.38 s.

What we never varied, or measured badly:

- **The settings.** The request cap was swept only at 512K and 1M (4, 8 and 16, with 4 in flight). No run had more requests in flight than its cap, so the cap never bound. The token budget was varied only on TP4/PP1:
  - 4K, 8K and 16K at 128K, with up to 4 in flight;
  - the same three at 512K and 1M, one at a time;
  - at 8K, only 8,192 against 8,448.

  The chunk cap was never set. Older vLLM versions had `--max-num-partial-prefills`; 0.29.0 does not, and the chunk cap does its job.
- **Mixed traffic.** One pilot run on TP4/PP1 read 512K prompts while the bench client's `--probe-request-rate` sent one-token probes, one at a time, each 4.7 s after the last one finished. The probes took 13 ms at the median, 41.9 s at p99 and 58.2 s at most. A lone 512K read takes 32 s. That fits the scheduler: a probe that arrives during a long read waits for it, and for any long prompt queued ahead of it. The client keeps only those three figures, with no per-probe record.
- **Memory pressure under load.** No load run came near full memory: KV use peaked at 27.8% in the pilot and 15.2% in the second campaign. The only preemptions, 2, came from a one-at-a-time 1M run whose cache was cut to 8.5 GiB per GPU. The pilot's try at 4 GiB never started: the server exited with code 1, and we have no log of why.
- **Steady arrivals.** Fixed-rate runs exist only on TP4/PP1, at 8K and 128K, plus the probe run. None ran on two servers, and none at 1M.
  - **Where the rates came from.** The campaign harness's load-case generator (`13_generate_load_cases.py`) took each prompt length's best throughput from any run. At 8K that was a run with 4-token answers, at 4.23 requests a second. With the sweep's own 256-token answers, the server served at most 3.4 a second.
  - **What that did at 8K.** The runs labelled 0.90× to 1.25× all asked for more than the server could serve. The client's cap of 64 in flight held requests back for 71–80% of each run. `vllm bench serve` starts a request's clock only after the request passes that cap, so those waits leave the queue out.
  - **At 128K**, each rate sent only 24 requests. At the rate labelled 1.00×, the second half waited 32.6 s on average, against 21.1 s for the whole run, so the queue was still growing.

## Runs to add

Group runs by server settings: a server start costs minutes, while a run at 8K takes under a minute.

- **Server defaults.** Start every server with `--max-num-seqs 256` unless a block sets it.
- **Reuse servers.** Reuse a server wherever its settings match. Block 1 starts three servers on TP4/PP1:
  - **A**: the baseline: budget 8,192, no chunk cap;
  - **B**: budget 16,384 with the chunk cap at 8,192;
  - **C**: budget 16,384 alone.

  The later blocks reuse them.
- **Load.** The times below are benchmark time, estimated from our runs; server starts and warm-ups come on top. In all, the blocks need about 6 hours of runs and about 17 server starts.
- **Order.** Run blocks 1–4 first: they decide whether the settings change what we already measured. Run block 7 with the baseline settings.
- **Evidence.** For every run, keep Task 1's evidence, and record the most requests in flight, taken from the per-request file.

1. **Let two long prompts be read at once.** On A, B and C: 1M with 2 in flight, and 128K with 8.
   - On B, each step reads 8,192 tokens of each of two prompts. C shows what the bigger step alone buys. The pilot read a lone 1M prompt in 89.0 s at a 16,384 budget, against 93.3 s at 8,192.
   - Today a lone 1M read takes R = 93.5 s, and the two first tokens land at 93.5 s and 185.4 s.
   - Read f = 2 × (the first wave's last first token) / (C × R), with R the lone read on A. f is the time to read two prompts, counted in lone reads. Reading them one after the other gives 2; our 128K first wave gives 1.95 today.
     - **f near 1** (both 1M first tokens near 94 s): the second read came free. The GPUs had room, and reading one prompt at a time set the limit.
     - **f near 2** (both near 187 s): the GPUs were already full. Reading side by side only delays the first answer, and only more replicas help.
   - Load: about 15 minutes, 3 server starts.
2. **The step budget.** `--max-num-batched-tokens` at 4,096, 8,192, 16,384 and 32,768.
   - Layouts: TP4/PP1 and TP4/PP2.
   - Runs: 8K with 8 and 32 in flight; 128K with 4 and 8.
   - Read the stall length and share, prompts per step at 8K, the first-token wait and tokens per second. At 16,384, a step should read about two 8K prompts.
   - This extends the 128K result above to 8K, to 32 in flight, to a 32K budget and to pipeline stages. If stalls follow the chunk, the budget sets the price of a stall. If they do not, the stall is not the chunk.
   - Load: about 30 minutes. TP4/PP1 uses A at 8,192 and C at 16,384; with those, 6 new server starts.
3. **The request cap where it binds.** On TP4/PP1, `--max-num-seqs` at 16, 32 and 64.
   - Runs: 1K and 8K prompts, 64 in flight, 256-token answers.
   - Read running (it should plateau at the cap), waiting, the first-token wait, the token gap and tokens per second. Together they show what a cap buys each answer and what it costs in waiting.
   - Load: about 5 minutes, 3 server starts.
4. **Mixed traffic.** On A and on B, run two `vllm bench serve` clients at once, each with `--save-detailed` and its own clock pair.
   - **Short stream:** 1K prompts with 128-token answers, at half the short-only capacity measured on the same server first.
   - **Long stream:** 20 prompts of 128K, then 10 of 512K, at one third of a lone read's rate, so a long read is in progress about a third of the time.
   - **Baseline:** short requests only, at the same rate.
   - On B, the long read keeps today's 8,192 tokens a step and leaves 8,192 for short prompts.
   - **Optional third server:** the chunk cap at 2,048 with the 8,192 budget, for shorter stalls and a slower long read.
   - **Expect:** today, a short request that arrives during a long read waits for the rest of it, and for any long prompt queued ahead of it. On B, while one long prompt is being read, it should start within a step or two, then stall once per step while the long read goes on. Two long prompts read side by side fill B's step again.
   - **Read, for short requests:**
     - the first-token wait and token gaps, while a long prompt is being read and while none is;
     - the share of short requests that arrived during a long read;
     - the stall share, against the baseline.
   - **Read, for long requests:** how much the cap slows the read.
   - **Optional: priority.** Start a server with `--scheduling-policy priority`, and give the long client `--extra-body '{"priority": 1}'` (lower runs first). Priority orders only the waiting queue. A short request still waits for a long read in progress, but no longer for a long prompt queued ahead of it.
   - Load: about 1 hour for A and B, with no new server start; each option needs 1 more.
5. **Memory pressure under load.** Set `--kv-cache-memory-bytes` (per GPU) so that the startup line reporting the KV cache size in tokens shows about half of C × (prompt + answer). `--num-gpu-blocks-override` is the other way to set it.
   - Runs: 8K with 32 in flight and 1,024-token answers; 128K with 8.
   - **Expect:** the scheduler admits a request only when its whole prompt fits in free KV blocks, and the first one that does not fit holds back every request behind it. So expect queueing, not preemption, at 128K. Preemption needs answers that grow after admission, as at 8K with 1,024-token answers.
   - Read the preemption counter, KV use over time (each iteration line carries it), and tokens per second against the same run with room. A preempted request shows as a long gap mid-answer while its prompt is recomputed.
   - If a size will not start, keep its `server.log`.
   - Load: about 10 minutes, 2 server starts.
6. **Long answers.** On A: 8K prompts with 1,024- and 2,048-token answers, at 16, 32 and 64 in flight.
   - Read the decode step against the number of answers in the batch, and how fast the KV cache fills.
   - Our longest answers so far were 512 tokens, at 8K with up to 16 in flight.
   - Load: about 10 minutes, no new server start.
7. **Steady arrivals on two servers.**
   - **Fix the load-case generator first.** Take each rate's basis from a closed-loop run on the same layout, with the same prompt length, answer length and budget, at the most in flight: 32 and 64 at 8K, 8 and 16 at 128K.
   - **Rates:** run `--request-rate R --burstiness 1` at 0.5, 0.75, 0.9 and 1.0 times that capacity.
   - **Client cap:** set `--max-concurrency` far above what the run reaches. Check that the most in flight in the per-request file stays below it.
   - **Requests:** enough for a p95: 200 at 8K, 60 at 128K. Answers of 256 tokens at 8K and 128K, as in the pilot's sweep, and 64 at 512K and 1M.
   - **Layouts:**
     - 8K and 128K on TP4/PP2, TP8/PP2, TP4/PP4 and TP16/PP1;
     - 512K and 1M on TP4/PP1 (on A) and TP4/PP4, at 0.5 times only, with 12 requests.
   - **Read** the first-token wait and token gaps once the opening is past, and the rate at which waits start to grow. At 1.0 the queue never settles, so report the wait against each request's place in the run.
   - The waits in our cost tables are closed-loop means with the opening burst in them; these runs give the steady figures.
   - Load: about 2½ hours at 8K and 128K, with the capacity runs, plus about 1 hour at 512K and 1M. TP4/PP2 reuses block 2's server at 8,192; with that, 3 new server starts.

## Analysis to add

1. **Merged timeline.** Merge the bench files from one server on their clock pairs into one timeline. Tag each request's class (short or long), and draw each class in its own group of rows. Draw the engine strips over both.
2. **Step cost.** In vLLM 0.29.0, each iteration line reads, after an `Engine 000: ` prefix, `Iteration(N): X context requests, Y context tokens, Z generation requests, W generation tokens, iteration elapsed time: T ms, GPU KV cache usage: K%`.
   - **Fit** step time ≈ a + b × answers + c × prompt tokens, per layout and prompt length. Report a, b, c and the fit's error.
   - **At 128K and above,** add what each step reads back: the answers' total context, and, for a chunk, how far into its prompt it is. Count that from the run of context steps since its prompt started.
   - **Timing.** The logged time is the engine's wait for that step's result. Async scheduling is on by default in 0.29.0, so steps overlap even on one stage, and more so with pipeline stages; the logged time is only part of a step. Check it against the spacing of the time-stamped lines, and calibrate once on one stage with `--no-async-scheduling`.
   - This is continuous batching's cost model: it predicts the stall and the decode step.
3. **Gauges on the timeline.** Draw running against the cap, waiting, KV use and preemptions on the engine strips.
4. **Steady arrivals.** Plot the first-token wait and token gap percentiles against the arrival rate, per layout. Mark where waits start to grow.
5. **Mixed traffic.** Report short requests' first-token wait and stall share, split by whether a long prompt was being read at the time.

## Rules

Task 1's rules hold. Also:
- Check every flag against this build's `vllm serve --help` and `vllm bench serve --help` before a run, with the existing `add_if_supported` pattern.
- Compare runs only within one server session or one build.
- Record the vLLM version and the build's md5, never the file name.
- Record every server flag and each run's position on its server.

## Done when

- Every run above is in the archive, with Task 1's evidence and the analysis outputs.
- Each block's question has a one-line answer with its numbers, read against the outcomes above.
- The step-cost fit is reported per layout, with its error.
- The load-case generator takes its rates from matching runs, and a test shows it.
