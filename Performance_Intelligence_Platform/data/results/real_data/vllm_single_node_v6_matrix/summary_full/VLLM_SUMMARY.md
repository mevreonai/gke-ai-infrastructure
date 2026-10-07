# V5 serving summary

> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.
> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.

| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tp4_qualification | 8k_c1 | 8192 | 1 | 0.73 | 223.53 | 4.49 | 187.14 | 0.001 | 0 | 0 | CAPTURED |
| tp4_qualification | 8k_c8 | 8192 | 8 | 2.15 | 931.27 | 10.89 | 551.51 | 0.010 | 6 | 0 | CAPTURED |
| tp4_qualification | 128k_c1 | 131072 | 1 | 0.19 | 4530.44 | 5.10 | 24.72 | 0.016 | 0 | 0 | CAPTURED |
| tp4_qualification | 512k_c1 | 524288 | 1 | 0.03 | 31931.64 | 7.59 | 1.97 | 0.065 | 0 | 0 | CAPTURED |
| tp8_qualification | 8k_c1 | 8192 | 1 | 0.53 | 263.25 | 6.37 | 135.57 | 0.001 | 0 | 0 | CAPTURED |
| tp8_qualification | 8k_c8 | 8192 | 8 | 1.74 | 1031.23 | 13.94 | 445.94 | 0.009 | 6 | 0 | CAPTURED |
| tp8_qualification | 128k_c1 | 131072 | 1 | 0.18 | 4782.84 | 7.05 | 22.54 | 0.016 | 0 | 0 | CAPTURED |
| tp8_qualification | 512k_c1 | 524288 | 1 | 0.03 | 28079.82 | 9.48 | 2.23 | 0.064 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 8k_c1 | 8192 | 1 | 1.26 | 222.23 | 4.47 | 161.89 | 0.001 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 128k_c1 | 131072 | 1 | 0.19 | 4532.09 | 5.11 | 24.71 | 0.016 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 512k_c1 | 524288 | 1 | 0.03 | 31916.19 | 7.57 | 1.98 | 0.065 | 0 | 0 | CAPTURED |
| tp4_context_baseline | 1m_c1 | 1000000 | 1 | 0.01 | 93247.86 | 10.27 | 0.34 | 0.123 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 8k_c1 | 8192 | 1 | 0.93 | 263.31 | 6.35 | 119.63 | 0.001 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 128k_c1 | 131072 | 1 | 0.18 | 4809.57 | 7.10 | 22.41 | 0.016 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 512k_c1 | 524288 | 1 | 0.03 | 28088.72 | 9.46 | 2.23 | 0.064 | 0 | 0 | CAPTURED |
| tp8_context_baseline | 1m_c1 | 1000000 | 1 | 0.01 | 74687.51 | 12.10 | 0.43 | 0.122 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 8k_prefill | 8192 | 1 | 4.23 | 222.66 | 4.45 | 16.94 | 0.000 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 128k_prefill | 131072 | 1 | 0.22 | 4536.91 | 5.12 | 0.88 | 0.016 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 512k_prefill | 524288 | 1 | 0.03 | 31955.16 | 7.82 | 0.13 | 0.064 | 0 | 0 | CAPTURED |
| tp4_prefill_focus | 1m_prefill | 1000000 | 1 | 0.01 | 93274.24 | 10.49 | 0.04 | 0.123 | 0 | 0 | CAPTURED |
| tp4_decode_focus | 8k_decode_c1 | 8192 | 1 | 0.40 | 223.06 | 4.49 | 203.47 | 0.001 | 0 | 0 | CAPTURED |
| tp4_decode_focus | 8k_decode_c8 | 8192 | 8 | 1.41 | 922.65 | 9.28 | 722.38 | 0.010 | 6 | 0 | CAPTURED |
| tp4_decode_focus | 8k_decode_c16 | 8192 | 16 | 1.76 | 1229.90 | 15.30 | 903.55 | 0.020 | 12 | 0 | CAPTURED |
| tp4_chunk4k | 128k_c1 | 131072 | 1 | 0.18 | 5227.57 | 5.12 | 11.53 | 0.016 | 0 | 0 | CAPTURED |
| tp4_chunk4k | 128k_c4 | 131072 | 4 | 0.19 | 11344.86 | 141.28 | 12.33 | 0.049 | 3 | 0 | CAPTURED |
| tp4_chunk4k | 512k_c1 | 524288 | 1 | 0.02 | 40271.31 | 7.58 | 0.79 | 0.064 | 0 | 0 | CAPTURED |
| tp4_chunk4k | 1m_c1 | 1000000 | 1 | 0.01 | 122048.67 | 10.31 | 0.13 | 0.122 | 0 | 0 | CAPTURED |
| tp4_chunk8k | 128k_c1 | 131072 | 1 | 0.21 | 4534.46 | 5.12 | 13.18 | 0.016 | 0 | 0 | CAPTURED |
| tp4_chunk8k | 128k_c4 | 131072 | 4 | 0.22 | 10657.23 | 119.26 | 14.05 | 0.065 | 3 | 0 | CAPTURED |
| tp4_chunk8k | 512k_c1 | 524288 | 1 | 0.03 | 31936.02 | 7.65 | 0.99 | 0.065 | 0 | 0 | CAPTURED |
| tp4_chunk8k | 1m_c1 | 1000000 | 1 | 0.01 | 93276.60 | 10.35 | 0.17 | 0.123 | 0 | 0 | CAPTURED |
| tp4_chunk16k | 128k_c1 | 131072 | 1 | 0.21 | 4364.18 | 5.09 | 13.66 | 0.017 | 0 | 0 | CAPTURED |
| tp4_chunk16k | 128k_c4 | 131072 | 4 | 0.23 | 10884.49 | 105.13 | 14.60 | 0.066 | 3 | 0 | CAPTURED |
| tp4_chunk16k | 512k_c1 | 524288 | 1 | 0.03 | 30455.13 | 7.53 | 1.04 | 0.066 | 0 | 0 | CAPTURED |
| tp4_chunk16k | 1m_c1 | 1000000 | 1 | 0.01 | 88951.34 | 10.26 | 0.18 | 0.125 | 0 | 0 | CAPTURED |
| tp4_closedloop_8k | c1 | 8192 | 1 | 0.73 | 222.25 | 4.47 | 188.05 | 0.001 | 0 | 0 | CAPTURED |
| tp4_closedloop_8k | c4 | 8192 | 4 | 1.62 | 609.59 | 7.27 | 415.24 | 0.005 | 2 | 0 | CAPTURED |
| tp4_closedloop_8k | c8 | 8192 | 8 | 2.19 | 887.06 | 10.82 | 560.93 | 0.010 | 4 | 0 | CAPTURED |
| tp4_closedloop_8k | c16 | 8192 | 16 | 2.64 | 1156.00 | 19.20 | 675.28 | 0.020 | 12 | 0 | CAPTURED |
| tp4_closedloop_8k | c32 | 8192 | 32 | 3.06 | 1618.66 | 34.47 | 784.06 | 0.040 | 28 | 0 | CAPTURED |
| tp4_closedloop_128k | c1 | 131072 | 1 | 0.19 | 4531.72 | 5.13 | 24.70 | 0.016 | 0 | 0 | CAPTURED |
| tp4_closedloop_128k | c4 | 131072 | 4 | 0.21 | 10314.35 | 66.41 | 27.23 | 0.065 | 3 | 0 | CAPTURED |
| tp4_closedloop_128k | c8 | 131072 | 8 | 0.22 | 12629.64 | 187.53 | 27.97 | 0.131 | 7 | 0 | CAPTURED |
| tp4_closedloop_128k | c16 | 131072 | 16 | 0.22 | 37249.93 | 242.69 | 28.25 | 0.147 | 15 | 0 | CAPTURED |
| tp4_closedloop_512k | c1 | 524288 | 1 | 0.03 | 31997.71 | 7.56 | 1.97 | 0.065 | 0 | 0 | CAPTURED |
| tp4_closedloop_512k | c2 | 524288 | 2 | 0.03 | 40270.52 | 367.17 | 2.01 | 0.128 | 1 | 0 | CAPTURED |
| tp4_closedloop_512k | c4 | 524288 | 4 | 0.03 | 87628.75 | 433.72 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_closedloop_1m | c1 | 1000000 | 1 | 0.01 | 93356.47 | 10.22 | 0.34 | 0.123 | 0 | 0 | CAPTURED |
| tp4_closedloop_1m | c2 | 1000000 | 2 | 0.01 | 150539.28 | 239.07 | 0.35 | 0.155 | 1 | 0 | CAPTURED |
| tp4_512k_maxseq4 | 512k_c4 | 524288 | 4 | 0.03 | 87973.05 | 433.64 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_512k_maxseq8 | 512k_c4 | 524288 | 4 | 0.03 | 87931.31 | 433.55 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_512k_maxseq16 | 512k_c4 | 524288 | 4 | 0.03 | 87931.67 | 433.55 | 2.01 | 0.129 | 3 | 0 | CAPTURED |
| tp4_prefix128k | prefix128k | 131328 | 1 | 0.63 | 902.45 | 5.32 | 81.08 | 0.019 | 0 | 0 | CAPTURED |
| tp4_prefix512k | prefix512k | 524544.25 | 1 | 0.06 | 16866.47 | 7.64 | 3.69 | 0.077 | 0 | 0 | CAPTURED |
| tp4_observer_minimal | 8k_c8 | 8192 | 8 | 2.15 | 924.66 | 10.93 | 550.94 | 0.010 | 5 | 0 | CAPTURED |
| tp4_observer_minimal | 128k_c4 | 131072 | 4 | 0.21 | 10243.49 | 67.05 | 27.22 | 0.065 | 3 | 0 | CAPTURED |
| tp4_observer_full | 8k_c8 | 8192 | 8 | 2.16 | 895.93 | 11.00 | 552.60 | 0.010 | 6 | 0 | CAPTURED |
| tp4_observer_full | 128k_c4 | 131072 | 4 | 0.21 | 10512.20 | 65.04 | 27.20 | 0.065 | 3 | 0 | CAPTURED |
