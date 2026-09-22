# V8-FULL 1M Context Coverage

> 1,000,000 nominal input tokens are distinct from the 1,048,576 max-model-length setting.

| Scope | Network | Case | Bench | TP | PP | C | Status | KV peak | Preemptions | Gate |
|---|---|---|---|---:|---:|---:|---|---:|---:|---|
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_context_baseline | 1m_c1 | 4 | 1 | 1 | **COMPLETED** | 12.3% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp8_context_baseline | 1m_c1 | 8 | 1 | 1 | **COMPLETED** | 12.2% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_prefill_focus | 1m_prefill | 4 | 1 | 1 | **COMPLETED** | 12.3% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_chunk4k | 1m_c1 | 4 | 1 | 1 | **COMPLETED** | 12.2% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_chunk8k | 1m_c1 | 4 | 1 | 1 | **COMPLETED** | 12.3% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_chunk16k | 1m_c1 | 4 | 1 | 1 | **COMPLETED** | 12.5% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_closedloop_1m | c1 | 4 | 1 | 1 | **COMPLETED** | 12.3% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_closedloop_1m | c2 | 4 | 1 | 2 | **COMPLETED** | 15.5% | 0.0 |  |
| SINGLE_V6_BASE | SINGLE_NODE_LOCAL | tp4_native_offload_pressure | 1m_c1 | 4 | 1 | 1 | **NOT_RUN** |  | None |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_1m_concurrency_extension | 1m_c1 | 4 | 1 | 1 | **COMPLETED** | 12.3% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_1m_concurrency_extension | 1m_c2 | 4 | 1 | 2 | **COMPLETED** | 15.5% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_1m_concurrency_extension | 1m_c4 | 4 | 1 | 4 | **COMPLETED** | 15.5% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp8_1m_concurrency_extension | 1m_c1 | 8 | 1 | 1 | **COMPLETED** | 12.2% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp8_1m_concurrency_extension | 1m_c2 | 8 | 1 | 2 | **COMPLETED** | 15.3% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp8_1m_concurrency_extension | 1m_c4 | 8 | 1 | 4 | **COMPLETED** | 15.4% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_1m_maxseq4 | 1m_c4 | 4 | 1 | 4 | **COMPLETED** | 15.5% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_1m_maxseq8 | 1m_c4 | 4 | 1 | 4 | **COMPLETED** | 15.5% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_1m_maxseq16 | 1m_c4 | 4 | 1 | 4 | **COMPLETED** | 15.5% | 0.0 |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_fp8_kv_1m | 1m_c1 | 4 | 1 | 1 | **NOT_RUN** |  | None |  |
| SINGLE_V8_1M_EXT | SINGLE_NODE_LOCAL | tp4_prefix1m | prefix1m | 4 | 1 | 1 | **COMPLETED** | 14.6% | 0.0 |  |
| MULTI_V8 | GCP_NATIVE | tp4_pp2_dist | 1m_c1 | 4 | 2 | 1 | **COMPLETED** | 5.9% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_NATIVE | tp8_pp2_dist | 1m_c1 | 8 | 2 | 1 | **COMPLETED** | 5.9% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_NATIVE | tp4_pp4_dist | 1m_c1 | 4 | 4 | 1 | **COMPLETED** | 2.7% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_NATIVE | tp16_pp1_dist | 1m_c1 | 16 | 1 | 1 | **COMPLETED** | 12.1% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_100G | tp4_pp2_dist | 1m_c1 | 4 | 2 | 1 | **COMPLETED** | 5.9% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_100G | tp8_pp2_dist | 1m_c1 | 8 | 2 | 1 | **COMPLETED** | 5.9% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_100G | tp4_pp4_dist | 1m_c1 | 4 | 4 | 1 | **COMPLETED** | 2.7% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_100G | tp16_pp1_dist | 1m_c1 | 16 | 1 | 1 | **COMPLETED** | 12.1% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_20G | tp4_pp2_dist | 1m_c1 | 4 | 2 | 1 | **COMPLETED** | 5.9% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_20G | tp8_pp2_dist | 1m_c1 | 8 | 2 | 1 | **COMPLETED** | 5.9% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_20G | tp4_pp4_dist | 1m_c1 | 4 | 4 | 1 | **COMPLETED** | 2.7% | 0.0 | GATE_PASSED |
| MULTI_V8 | GCP_CAPPED_20G | tp16_pp1_dist | 1m_c1 | 16 | 1 | 1 | **COMPLETED** | 12.1% | 0.0 | GATE_PASSED |
