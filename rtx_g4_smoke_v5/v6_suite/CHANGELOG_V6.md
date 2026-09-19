# V6 architectural changes

P0 fixes implemented: per-case KV dtype; exact revision; TP4 GPU filtering; warmup-window isolation; explicit `max_num_seqs`; current Ray executor flag; `RUN_CONFIG.env` sourcing in multi-node wrapper; forced 4-GPU/node TP4/PP2 placement; two-node GPU telemetry; actual token-length validation; low-N percentile reliability flags; deterministic prefix-repetition; KV-memory-vs-GPU-util semantics; total-across-TP offload accounting; separate profiler runs; NCCL Nsight trace; conservative kernel attribution; no generic scheduler substring summing.

P1 coverage added: prefill/decode phase separation; closed-loop concurrency by context; evidence-generated open-loop RPS; burstiness-ready schema; probe requests; 512K/1M safety gating; observer-overhead A/B; scheduler-limit sweep; Ray placement snapshots; UI/analysis-ready summary fields.
