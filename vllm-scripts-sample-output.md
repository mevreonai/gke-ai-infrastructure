# How to read the benchmark scripts' output

A guide for anyone new to these scripts: what each one tells you, what its output looks like, and what to do next.

## Start here

1. **Run the benchmark:** `./bench_run.sh`. It runs the tests and saves everything we need.
2. **Check which runs you can trust:** `python3 bench_summary.py bench_results`.
3. **If a number looks wrong:** run `metrics_diff.py` and `server_log.py` on that run to find out why.
4. **Only if it's still unclear:** profile with `./profile_run.sh`.

## Words you'll see

| Word | Plain meaning | Typical value here |
|---|---|---|
| **TTFT** | How long until the first word of the answer arrives | 0.3–0.5 s |
| **TPOT / ITL** | Time between words while the answer streams | ~50 ms |
| **E2EL** | Total time for one full answer | ~50 s for 1,024 tokens |
| **C (concurrency)** | How many requests are running at the same time | 1, 8, 16 |
| **Wave** | The benchmark sends C requests at once, and the next ones start as those finish. The first wave is everyone arriving together, which is the hardest moment for TTFT. | |
| **Queue time** | Time a request waits inside vLLM before any work starts | should be ~0 |
| **Prefix cache** | vLLM reuses work for prompts it has seen before. Great in production, but it makes repeated test runs look faster than reality. | should be ~0% in tests |
| **ISL / OSL** | Input / output length in tokens | 1,024 / 1,024 |

The samples below are trimmed to their key lines, with `<-` notes added. Samples marked **real** come from our two C16 runs. Samples marked **synthetic** use made-up test data (we don't have those files from the server yet): the layout is real, the numbers are not.

---

## 1. bench_run.sh: run the benchmark and keep the evidence

**Answers:** "How do I run a test we can trust and explain later?"

**What you get, per run:**
```
c8_s12345.json                 the results, including every request's timings
c8_s12345.metrics_before.prom  the server's own counters before the run
c8_s12345.metrics_after.prom   ... and after the run
c8_s12345.server.log           what the server logged during the run
c8_s12345.meta.json            the settings used (concurrency, seed, lengths)
```

**Why it matters:** for the old 1 s C8 TTFT, we suspect other traffic was on the server, but nobody saved the server's log or counters, so we can't prove it. This script saves them on every run.

It also avoids two traps automatically:
- **Cold server:** a short warm-up runs first and is kept out of the results.
- **Cached prompts:** every run uses new random prompts, so the cache can't flatter TTFT.

---

## 2. bench_summary.py: can I trust this run?

**Answers:** "Which runs are valid, and do repeats agree?"

**Sample (real, trimmed):**
```
run                    C   ok/N    OSL  TTFT p50  TPOT p50  ITL p50  out tok/s
..._gateway_c16       16  100/100   29     762     504.6     51.2       7.9   <- OSL 29? TPOT 505 ms? looks wrong
   ! OUTPUT TOKENS UNDERCOUNTED: ~920 chunks/request, only 29 tokens counted   <- the script explains it
   ! ITL std 405 ms >> p99 81 ms: a few multi-second gaps in the stream
..._direct_c16        16  100/100 1024     376      51.4     51.4     285.8   <- healthy: TPOT = ITL ≈ 51 ms
   ! ITL std 389 ms >> p99 54 ms: a few multi-second gaps in the stream
```

**What this tells us:**
- **Gateway run:** it counted only 29 output tokens per request, even though each stream clearly ran ~1,000 tokens. So its tok/s and TPOT are wrong, but its TTFT is still usable.
- **Direct run:** healthy. 51 ms per token, 286 tok/s.
- **Both runs:** the streams pause for a few seconds now and then. That's worth investigating.

**Repeats table (synthetic):**
```
setup                         C  runs  TTFT p50  spread  verdict
completions/direct 1024/1024  8    2      619      0%    stable            <- repeats agree: safe to compare
completions 1024/1024         8    1      301      -     need >=2 repeats  <- one run can't show noise
```

**Common flags and what to do:**

| Flag | Meaning | Do this |
|---|---|---|
| `FAILED` | Some requests didn't finish | Read the error shown; check `server_log.py` |
| `OUTPUT TOKENS UNDERCOUNTED` | Tokens were generated but not counted | Don't use tok/s or TPOT from this run; use ITL and TTFT |
| `ISL/OSL vs target` | Prompts or answers weren't the length asked for | Check the endpoint (chat adds template tokens) |
| `throughput … of expected` | The run was slower than its own latencies predict | Look for a stuck or failed request |
| `first-wave TTFT …x later waves` | The first burst is much slower | Check `ttft_waves.py`; could be warm-up or the burst itself |
| `ITL std >> p99` | Streams pause for seconds now and then | Compare chat vs completions; check where the client ran |
| `summary only` | Run without `--save-detailed` | Rerun with `bench_run.sh` (it adds it) |
| `num_prompts … not a multiple of C` | The last wave ran half-empty | Not a problem; use a multiple of C next time |

---

## 3. bench_table.sh: quick comparison table

**Answers:** "Can I see all runs side by side?" Useful for pasting into messages.

**Sample (real):**
```
file              done  out_tok  TTFTp50  TTFTp99  TPOTp50  ITLp50  out_tok/s
c16_direct.json   100   102400   376      461      51.4     51.4    285.8
c16_gateway.json  100   2888     762      1474     504.6    51.2    7.9
```
It has no checks: use `bench_summary.py` to know which rows to trust.

---

## 4. ttft_waves.py: is the first wave slower?

**Answers:** "Is high TTFT a one-off burst at the start, or every request?"

**Sample (synthetic, C8):**
```
wave   0: mean    996 ms |   1083    906    920   1031   1030   1096    909    989   <- 8 requests arriving together
wave   1: mean    310 ms |    306    327    270    301    313    327    329    310   <- normal after that
```

**What this tells us:** only the first 8 requests are slow, so the cause is the start of the run (a cold server, or 8 prompts arriving at once), not steady-state serving. If every wave were slow, the problem would be ongoing.

---

## 5. metrics_diff.py: where did TTFT go?

**Answers:** "Was the first-token time spent waiting, computing, or outside vLLM?"

**Sample (synthetic, trimmed):**
```
TTFT (server)   mean 900 ms
  queue          mean  50 ms     <- waiting in line inside vLLM: should be ~0
  prefill        mean 700 ms     <- actually processing the prompt
  TTFT split: queue 50 + prefill 700 + outside scheduler 150 ms
prefix cache: 800 hit / 9312 tokens = 8.6%   <- should be ~0% in a test
finished: abort=1, length=8                  <- one request was abandoned

FINDINGS
  - prefix cache hit 9%: prompts are partly cached, TTFT is optimistic
  - 1 requests aborted: client timeout/disconnect
```

**What this tells us:** most of this TTFT is real prompt processing, with very little waiting. But 9% of prompt tokens came from the cache, so TTFT looks slightly better than it really is.

**For the old C8 question:** a queue time clearly above 0 would show that requests were waiting behind other work.

---

## 6. server_log.py: what did the server actually do?

**Answers:** "How many requests was the server really handling, and did anything go wrong?"

**Sample (synthetic, trimmed):**
```
running requests   mean 4.0   max 7.0     <- never reached the 8 the benchmark asked for
waiting requests   mean 0.3   max 1.0     <- some requests queued
PROBLEMS
  aborted request  x3
NCCL
  channels via SHM/direct/direct          <- GPUs talk through host memory (no P2P): expected on this box

FINDINGS
  - server never had 8 requests running (max 7): the client or a gateway is not keeping that many requests open
  - Waiting > 0 in 9 of 27 stats lines: requests queued inside vLLM
```

**What this tells us:**
- **Running below C:** the server never had 8 requests at once, so something between the client and vLLM held some back.
- **Running above C:** would mean someone else's traffic was on the server.

**For the old C8 question:** this is the check. If `running` goes above 8 during a C8 run, other traffic was sharing the GPUs.

---

## 7. profile_run.sh + trace_summary.py: where does GPU time go? (advanced)

**Answers:** "Inside the GPU, which work takes the time, and is one GPU slower than the others?" Only needed if steps 2–6 don't explain the numbers.

**Sample (synthetic, trimmed):**
```
rank  compute_ms  allreduce_ms
   0        84.0          78.0
   1        84.0          78.0
   2        84.0          78.0
   3        95.4          78.0     <- slowest GPU: the others wait for it

step   dur_ms   what it spent time on
 0P     66.0    allreduce 45%  moe 41%  attention 14%   <- P = prompt processing (prefill)
 1       4.8    ...                                     <- normal token steps
```

**What this tells us:**
- **Rank 3 is the slow GPU:** since all GPUs must finish each step together, one slow GPU slows everything. Check its clocks, temperature and PCIe link.
- **Prefill step:** almost half its time is GPUs exchanging data (all-reduce), which is expensive on this box without direct GPU-to-GPU links.

Profiled timings run slower than normal, so compare percentages, not milliseconds.

---

## Cheat sheet

| Symptom | Run | Look for |
|---|---|---|
| TTFT high at one concurrency | `ttft_waves.py`, then `metrics_diff.py` | first wave only? queue time > 0? |
| Suspect other traffic | `server_log.py` | `running` max above C |
| Throughput looks too low | `bench_summary.py` | `UNDERCOUNTED`, `FAILED`, `throughput … of expected` |
| Numbers change between runs | `bench_summary.py` | spread above 10%, prefix cache hits |
| A request failed | `bench_summary.py`, `server_log.py` | error text, aborted requests |
| Still unexplained | `profile_run.sh`, `trace_summary.py` | slow rank, what prefill spends time on |
