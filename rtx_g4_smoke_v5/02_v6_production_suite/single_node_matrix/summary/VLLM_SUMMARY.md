# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_qualification | 8k_c1 | 8192 | 1 | 0.74 | 224.35 | 4.45 | 188.37 | 0.001 | 0 | 0 | CAPTURED |
| tp4_qualification | 8k_c8 | 8192 | 8 | 2.17 | 956.45 | 10.70 | 555.03 | 0.010 | 5 | 0 | CAPTURED |
| tp4_qualification | 128k_c1 | 131072 | 1 | 0.19 | 4534.12 | 5.08 | 24.71 | 0.016 | 0 | 0 | CAPTURED |
| tp4_qualification | 512k_c1 | 524288 | 1 | 0.03 | 31955.50 | 7.58 | 1.97 | 0.065 | 0 | 0 | CAPTURED |
| tp8_qualification | 8k_c1 | 8192 | 1 | 0.53 | 267.73 | 6.35 | 135.69 | 0.001 | 0 | 0 | CAPTURED |
| tp8_qualification | 8k_c8 | 8192 | 8 | 1.74 | 1036.03 | 13.92 | 445.75 | 0.009 | 6 | 0 | CAPTURED |
| tp8_qualification | 128k_c1 | 131072 | 1 | 0.18 | 4819.56 | 7.03 | 22.40 | 0.016 | 0 | 0 | CAPTURED |
| tp8_qualification | 512k_c1 | 524288 | 1 | 0.03 | 28216.82 | 9.47 | 2.22 | 0.064 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 8k_c1 | 8192 | 1 | 1.27 | 222.28 | 4.45 | 162.41 | 0.001 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 128k_c1 | 131072 | 1 | 0.19 | 4540.83 | 5.10 | 24.67 | 0.016 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 512k_c1 | 524288 | 1 | 0.03 | 31978.46 | 7.56 | 1.97 | 0.065 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 1m_c1 | 1000000 | 1 | 0.01 | 93384.54 | 10.24 | 0.34 | 0.123 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 8k_c1 | 8192 | 1 | 0.93 | 267.59 | 6.33 | 119.50 | 0.001 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 128k_c1 | 131072 | 1 | 0.17 | 4824.27 | 7.05 | 22.38 | 0.016 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 512k_c1 | 524288 | 1 | 0.03 | 28166.55 | 9.44 | 2.23 | 0.064 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 1m_c1 | 1000000 | 1 | 0.01 | 74850.25 | 12.07 | 0.43 | 0.122 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 8k_prefill | 8192 | 1 | 4.23 | 222.96 | 4.38 | 16.93 | 0.000 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 128k_prefill | 131072 | 1 | 0.22 | 4542.10 | 5.09 | 0.88 | 0.016 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 512k_prefill | 524288 | 1 | 0.03 | 31960.15 | 7.84 | 0.13 | 0.064 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 1m_prefill | 1000000 | 1 | 0.01 | 93354.21 | 10.64 | 0.04 | 0.123 | 0 | 0 | CAPTURED |
| tp4_decode_focus | 8k_decode_c1 | 8192 | 1 | 0.40 | 225.59 | 4.47 | 203.97 | 0.001 | 0 | 0 | CAPTURED |
| tp4_decode_focus | 8k_decode_c8 | 8192 | 8 | 1.41 | 957.21 | 9.23 | 721.04 | 0.010 | 4 | 0 | CAPTURED |
| tp4_decode_focus | 8k_decode_c16 | 8192 | 16 | 1.73 | 1242.58 | 15.64 | 885.13 | 0.020 | 13 | 0 | CAPTURED |
| tp4_chunk4k | 128k_c1 | 131072 | 1 | 0.18 | 5235.52 | 5.13 | 11.51 | 0.016 | 0 | 0 | CAPTURED |
| tp4_chunk4k | 128k_c4 | 131072 | 4 | 0.19 | 11475.91 | 142.05 | 12.22 | 0.048 | 3 | 0 | CAPTURED |
| tp4_chunk4k | 512k_c1 | 524288 | 1 | 0.02 | 40307.15 | 7.57 | 0.79 | 0.064 | 0 | 0 | CAPTURED |
| tp4_chunk4k | 1m_c1 | 1000000 | 1 | 0.01 | 122103.78 | 10.28 | 0.13 | 0.122 | 0 | 0 | CAPTURED |
| tp4_chunk8k | 128k_c1 | 131072 | 1 | 0.21 | 4544.49 | 5.11 | 13.15 | 0.016 | 0 | 0 | CAPTURED |
| tp4_chunk8k | 128k_c4 | 131072 | 4 | 0.22 | 10928.09 | 117.39 | 13.93 | 0.065 | 3 | 0 | CAPTURED |
| tp4_chunk8k | 512k_c1 | 524288 | 1 | 0.03 | 31966.57 | 7.58 | 0.99 | 0.065 | 0 | 0 | CAPTURED |
| tp4_chunk8k | 1m_c1 | 1000000 | 1 | 0.01 | 93375.89 | 10.37 | 0.17 | 0.123 | 0 | 0 | CAPTURED |
| tp4_chunk16k | 128k_c1 | 131072 | 1 | 0.21 | 4366.47 | 5.09 | 13.65 | 0.017 | 0 | 0 | CAPTURED |
| tp4_chunk16k | 128k_c4 | 131072 | 4 | 0.23 | 10922.05 | 106.51 | 14.50 | 0.066 | 3 | 0 | CAPTURED |
| tp4_chunk16k | 512k_c1 | 524288 | 1 | 0.03 | 30498.89 | 7.54 | 1.04 | 0.066 | 0 | 0 | CAPTURED |
| tp4_chunk16k | 1m_c1 | 1000000 | 1 | 0.01 | 89164.13 | 10.26 | 0.18 | 0.125 | 0 | 0 | CAPTURED |
| tp4_closedloop_8k | c1 | 8192 | 1 | 0.73 | 224.91 | 4.47 | 187.60 | 0.001 | 0 | 0 | CAPTURED |
| tp4_closedloop_8k | c4 | 8192 | 4 | 1.62 | 610.83 | 7.27 | 415.28 | 0.005 | 2 | 0 | CAPTURED |
| tp4_closedloop_8k | c8 | 8192 | 8 | 2.19 | 916.48 | 10.73 | 559.73 | 0.010 | 5 | 0 | CAPTURED |
| tp4_closedloop_8k | c16 | 8192 | 16 | 2.63 | 1155.82 | 19.27 | 673.24 | 0.020 | 13 | 0 | CAPTURED |
| tp4_closedloop_8k | c32 | 8192 | 32 | 3.03 | 1623.75 | 34.96 | 774.40 | 0.040 | 27 | 0 | CAPTURED |
| tp4_closedloop_128k | c1 | 131072 | 1 | 0.19 | 4538.78 | 5.11 | 24.67 | 0.016 | 0 | 0 | CAPTURED |
| tp4_closedloop_128k | c4 | 131072 | 4 | 0.21 | 10596.03 | 64.37 | 27.20 | 0.065 | 3 | 0 | CAPTURED |
| tp4_closedloop_128k | c8 | 131072 | 8 | 0.22 | 12722.52 | 186.98 | 27.96 | 0.131 | 7 | 0 | CAPTURED |
| tp4_closedloop_128k | c16 | 131072 | 16 | 0.22 | 37256.56 | 242.85 | 28.24 | 0.146 | 15 | 0 | CAPTURED |
| tp4_closedloop_512k | c1 | 524288 | 1 | 0.03 | 32028.53 | 7.56 | 1.97 | 0.065 | 0 | 0 | CAPTURED |
| tp4_closedloop_512k | c2 | 524288 | 2 | 0.03 | 40299.16 | 367.40 | 2.01 | 0.128 | 1 | 0 | CAPTURED |
| tp4_closedloop_512k | c4 | 524288 | 4 | 0.03 | 87703.85 | 433.95 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_closedloop_1m | c1 | 1000000 | 1 | 0.01 | 93460.38 | 10.20 | 0.34 | 0.123 | 0 | 0 | CAPTURED |
| tp4_closedloop_1m | c2 | 1000000 | 2 | 0.01 | 150654.33 | 239.25 | 0.35 | 0.155 | 1 | 0 | CAPTURED |
| tp4_closedloop_1m | c4 | 1000000 | 4 | 0.01 | 231503.50 | 267.69 | 0.35 | 0.155 | 3 | 0 | CAPTURED |
| tp4_512k_maxseq4 | 512k_c4 | 524288 | 4 | 0.03 | 88007.07 | 433.81 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_512k_maxseq8 | 512k_c4 | 524288 | 4 | 0.03 | 87994.35 | 433.76 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_512k_maxseq16 | 512k_c4 | 524288 | 4 | 0.03 | 87974.85 | 433.77 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_prefix128k | prefix128k | 131328 | 1 | 0.63 | 910.75 | 5.31 | 80.72 | 0.019 | 0 | 0 | CAPTURED |
| tp4_prefix512k | prefix512k | 524544.25 | 1 | 0.06 | 16894.43 | 7.65 | 3.68 | 0.077 | 0 | 0 | CAPTURED |
| tp4_observer_minimal | 8k_c8 | 8192 | 8 | 2.15 | 955.92 | 10.80 | 551.16 | 0.010 | 6 | 0 | CAPTURED |
| tp4_observer_minimal | 128k_c4 | 131072 | 4 | 0.21 | 10289.90 | 66.77 | 27.20 | 0.065 | 3 | 0 | CAPTURED |
| tp4_observer_full | 8k_c8 | 8192 | 8 | 2.17 | 953.95 | 10.70 | 555.41 | 0.010 | 6 | 0 | CAPTURED |
| tp4_observer_full | 128k_c4 | 131072 | 4 | 0.21 | 10854.95 | 62.56 | 27.16 | 0.065 | 3 | 0 | CAPTURED |
