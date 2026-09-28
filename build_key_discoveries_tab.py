import sys
import re

# Complete script to inject Key Discoveries Tab
with open("build_key_discoveries_tab.py", "r", encoding="utf-8") as f:
    builder_code = f.read()

# Let's add details for cards 4 to 10 in KD_DETAILS_STORE in build_key_discoveries_tab.py
more_details = """
    4: {
        title: "Prefix Reuse Changes the Curve",
        eyebrow: "FINDING #4 &middot; WORKLOAD REGIME SHIFT",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Repeated-prefix traffic changes latency scaling from quadratic (O(N&sup2;)) to near-constant (O(1)). At 1M context, repeat-hit requests complete prefill in <b>2.614s</b> compared to <b>94.227s</b> for first/cold requests (&approx;<b>36.0&times; speedup</b>).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>Cold TTFT</th><th>Repeat-Hit Median</th><th>Speedup</th><th>Runtime Prefix Counters</th></tr></thead>
                <tbody>
                    <tr><td>128K Context</td><td>4.8965 s</td><td>0.3307 s</td><td style="color:#4ade80;font-weight:700">~14.8&times;</td><td>87.33% hit ratio</td></tr>
                    <tr><td>512K Context</td><td>32.5762 s</td><td>1.1679 s</td><td style="color:#4ade80;font-weight:700">~27.9&times;</td><td>49.98% hit ratio</td></tr>
                    <tr><td>1M Context</td><td>94.2272 s</td><td>2.6140 s</td><td style="color:#4ade80;font-weight:700">~36.0&times;</td><td>49.97% hit ratio</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Derivation:</b> Prefix caching bypasses attention computation for previously ingested prompt blocks. The repeat prefill latency reflects only the un-cached suffix (here fixed to ~500 tokens) plus KV pointer block table lookup overhead.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Execution Behavior:</b> KV blocks remain in GPU high-bandwidth memory (HBM). Radix tree traversal takes &lt;1ms; prefill computation scales only with the novel token delta.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleup_prefix_matrix/tp4_prefix128k.json (EV-053)<br>
                scaleup_prefix_matrix/tp4_prefix512k.json (EV-054)<br>
                scaleup_prefix_matrix/tp4_prefix1m.json (EV-075)
            </div>
        `
    },
    5: {
        title: "Parallelism Directional Elasticity + Frontier",
        eyebrow: "FINDING #5 &middot; PARETO SCALING FRONTIER",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Parallelism elasticity flips sign with context length. While TP8 is slower than TP4 at short contexts (8K: +18.5% TTFT penalty) due to cross-socket AllReduce overhead, it becomes faster at long contexts (1M: -19.9% TTFT improvement) as compute scaling overtakes communication.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>TP4/PP1 TTFT</th><th>TP8/PP1 TTFT</th><th>TP8 Latency Effect</th><th>Resource Elasticity</th></tr></thead>
                <tbody>
                    <tr><td>8K Context</td><td>0.222 s</td><td>0.263 s</td><td style="color:#f87171">+18.5% (Slower)</td><td>Negative Elasticity</td></tr>
                    <tr><td>128K Context</td><td>4.532 s</td><td>4.810 s</td><td style="color:#f87171">+6.1% (Slower)</td><td>Near-Zero Elasticity</td></tr>
                    <tr><td>512K Context</td><td>31.916 s</td><td>28.089 s</td><td style="color:#4ade80">-12.0% (Faster)</td><td>Positive Elasticity</td></tr>
                    <tr><td>1M Context</td><td>93.248 s</td><td>74.688 s</td><td style="color:#4ade80">-19.9% (Faster)</td><td>High Positive Elasticity</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Pipeline Frontier at 1M (Holding TP=4, Scaling PP):</b><br>
                - TP4/PP1 (4 GPUs): TTFT = 93.248s &rarr; <b>373.0 GPU-s/req</b><br>
                - TP4/PP2 (8 GPUs): TTFT = 52.526s &rarr; <b>420.2 GPU-s/req</b> (+12.7% resource footprint)<br>
                - TP4/PP4 (16 GPUs): TTFT = 28.568s &rarr; <b>457.1 GPU-s/req</b> (+22.5% resource footprint)<br>
                PP provides smooth latency reduction (3.26&times; speedup) with modest +22.5% resource overhead.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Trade-off:</b> TP scales within node; PP scales across nodes. Choosing topology depends on whether the workload optimizes for minimal turn latency (PP4) or maximal cluster occupancy efficiency (PP1).
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp1_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp2_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_native.json
            </div>
        `
    },
    6: {
        title: "Prompt-Token Admission Fingerprint",
        eyebrow: "FINDING #6 &middot; OPEN-LOOP PREFILL CAPACITY",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Request throughput varies dramatically by prompt length (~18.2&times; gap between 8K and 128K), but when normalized by input tokens, achieved throughput collapses to nearly the same processing rate (~27.5K vs ~24.2K input tok/s, a mere ~1.14&times; gap).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>Offered Load Sweep</th><th>Median Achieved Req/s</th><th>Input Token Rate</th><th>Ratio vs 8K</th></tr></thead>
                <tbody>
                    <tr><td>8K Context</td><td>1.00&times;, 1.10&times;, 1.25&times;</td><td style="color:#f87171;font-weight:700">3.3586 req/s</td><td style="color:#4ade80;font-weight:700">27.51K tok/s</td><td>1.00&times;</td></tr>
                    <tr><td>128K Context</td><td>1.00&times;, 1.10&times;, 1.25&times;</td><td style="color:#f87171;font-weight:700">0.1846 req/s</td><td style="color:#4ade80;font-weight:700">24.19K tok/s</td><td>1.14&times;</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Normalization Formula:</b><br>
                <code>Input_Token_Rate = Achieved_Request_Rate &times; Prompt_Tokens</code><br>
                - 8K: <code>3.3586 &times; 8,192 &approx; 27,513 tokens/s</code><br>
                - 128K: <code>0.1846 &times; 131,072 &approx; 24,192 tokens/s</code><br>
                The ~18.2&times; request rate gap is primarily sequence length volume; admission control must track prompt token budgets.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Evaluated under open-loop Poisson arrival traffic. High-load stress demonstrates that engine prefill pipelines saturate on cumulative token volume.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                openloop_matrix/tp4_8k_load_sweep.json<br>
                openloop_matrix/tp4_128k_load_sweep.json
            </div>
        `
    },
    7: {
        title: "Runtime-Knob Derivative Fingerprint",
        eyebrow: "FINDING #7 &middot; CHUNK SIZE VS MAX_NUM_SEQS",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Tuning max_num_seqs between 4, 8, and 16 produces less than 0.05% change in TTFT (&lt;110ms on a 232s turn) because concurrency is constrained by memory and prompt chunking. In contrast, chunk size tuning (4K&rarr;16K) delivers a steep <b>27.1% TTFT reduction</b> (122.0s &rarr; 88.9s).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Runtime Knob</th><th>Evaluated Values</th><th>Observed TTFT Delta</th><th>Leverage / Derivative</th></tr></thead>
                <tbody>
                    <tr><td>Chunk Size (1M c1)</td><td>4K &rarr; 8K &rarr; 16K</td><td>122.049s &rarr; 93.277s &rarr; 88.951s</td><td style="color:#4ade80;font-weight:700">High (-27.1% latency)</td></tr>
                    <tr><td>max_num_seqs (1M c4)</td><td>4 &rarr; 8 &rarr; 16</td><td>232.342s &rarr; 232.364s &rarr; 232.250s</td><td style="color:#94a3b8">Non-binding (0.049% spread)</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Telemetry Confirmation:</b> Server engine telemetry confirms <code>peak_running=2</code> and <code>peak_waiting=3</code> during the 1M c4 benchmark. The ceiling of 16 was never activated; chunk size, by contrast, directly scales GEMM arithmetic intensity on the HBM bus.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Larger chunk size amortizes kernel launch overhead and improves cuBLAS GEMM tensor core utilization during prefill chunk execution.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleup_matrix/vllm_scaleup_chunk_matrix/tp4_1m_chunk4k.json<br>
                scaleup_matrix/vllm_scaleup_chunk_matrix/tp4_1m_chunk8k.json<br>
                scaleup_matrix/vllm_scaleup_chunk_matrix/tp4_1m_chunk16k.json<br>
                scaleup_matrix/vllm_scaleup_scheduler_matrix/tp4_1m_seqs4.json<br>
                scaleup_matrix/vllm_scaleup_scheduler_matrix/tp4_1m_seqs16.json
            </div>
        `
    },
    8: {
        title: "TP Decode Evidence Chain",
        eyebrow: "FINDING #8 &middot; COLLECTIVE CROSS-SOCKET OVERHEAD",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Wider tensor parallelism hurts single-stream decode turns on dual-socket architectures. At 8K decode, TP8 incurs a <b>+41.9% TPOT penalty</b> (6.350ms vs 4.475ms on TP4). The cause is directly traced across four measurement layers to cross-NUMA PCIe bridge AllReduce latency.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Layer</th><th>Tool / Instrument</th><th>TP4 / PP1</th><th>TP8 / PP1</th><th>Observation</th></tr></thead>
                <tbody>
                    <tr><td>1. Microbench</td><td>NCCL test</td><td>~19 &mu;s</td><td>~37 &mu;s</td><td>~1.9&ndash;2.2&times; latency over PCIe bridge</td></tr>
                    <tr><td>2. Profiler</td><td>PyTorch Profiler</td><td>251.529 ms</td><td>583.866 ms</td><td>+332.3ms in nccl:all_reduce (7040 calls)</td></tr>
                    <tr><td>3. Nsight</td><td>CUDA GPU Kernels</td><td>Intra-socket bus</td><td>Cross-socket bridge</td><td>AllReduce is dominant decode category</td></tr>
                    <tr><td>4. E2E Metric</td><td>vLLM Serving</td><td>4.475 ms TPOT</td><td>6.350 ms TPOT</td><td>+41.9% interactive turn latency penalty</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Invocation Analysis:</b> Both TP4 and TP8 execute precisely 7,040 AllReduce calls per 8K decode run. Average latency per collective increases from 35.7&mu;s to 82.9&mu;s on TP8 due to PCIe socket traversal.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                - <b>PR-002:</b> TP4 Decode 8K, Self CUDA Time = 251.5 ms (86.3% of kernel work)<br>
                - <b>PR-003:</b> TP8 Decode 8K, Self CUDA Time = 583.9 ms (89.1% of kernel work)<br>
                Artifacts: <code>results_V8_runs(3)/hardware_processed/nsight_tp4_decode/</code> and <code>nsight_tp8_decode/</code>
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                hardware_processed/nsight_tp4_decode/cuda_gpu_kern_sum.csv (PR-002)<br>
                hardware_processed/nsight_tp8_decode/cuda_gpu_kern_sum.csv (PR-003)<br>
                scaleup_matrix/tp4_8k_decode.json (EV-009)<br>
                scaleup_matrix/tp8_8k_decode.json (EV-013)
            </div>
        `
    },
    9: {
        title: "Busy GPU != Efficient Serving",
        eyebrow: "FINDING #9 &middot; OBSERVABILITY & SM CYCLE DIVERGENCE",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> GPU SM utilization is fundamentally misleading as a sizing metric. At 1M context, cross-node TP16/PP1 reports <b>80.6%</b> GPU utilization while executing prefill in 68.197s. TP4/PP4 reports only <b>62.8%</b> GPU utilization yet finishes prefill in <b>28.568s</b> (&approx;<b>2.39&times; faster</b>).
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Context</th><th>TP4/PP4 SM Util</th><th>TP4/PP4 TTFT</th><th>TP16/PP1 SM Util</th><th>TP16/PP1 TTFT</th><th>Efficiency Winner</th></tr></thead>
                <tbody>
                    <tr><td>128K Context</td><td>35.2%</td><td>1.710 s</td><td>63.2%</td><td>6.420 s</td><td style="color:#4ade80;font-weight:700">TP4/PP4 (3.75&times; faster)</td></tr>
                    <tr><td>512K Context</td><td>55.3%</td><td>10.222 s</td><td>67.8%</td><td>29.624 s</td><td style="color:#4ade80;font-weight:700">TP4/PP4 (2.90&times; faster)</td></tr>
                    <tr><td>1M Context</td><td>62.8%</td><td>28.568 s</td><td>80.6%</td><td>68.197 s</td><td style="color:#4ade80;font-weight:700">TP4/PP4 (2.39&times; faster)</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Mechanism:</b> GPU utilization telemetry measures whether SM warps are scheduled. In distributed TP16, warps spend extensive cycles polling and waiting in NCCL AllReduce synchronization barriers, keeping the SMs registered as 'busy' without advancing token computation.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Nsight profiling proves that &gt;76% of TP16 execution time is collective network communication. Sizing workloads by GPU % alone would erroneously favor the slower configuration.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_native.json<br>
                scaleout_matrix/vllm_scaleout_network_matrix/tp16_pp1_dist_1m_c1_native.json
            </div>
        `
    },
    10: {
        title: "KV Headroom != VRAM Headroom",
        eyebrow: "FINDING #10 &middot; MEMORY DILUTION TELEMETRY",
        findings: `
            <div style="font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:12px">
                <b>Measured Phenomenon:</b> Pipeline parallelism dilutes the engine's reported KV cache utilization percentage, giving the false illusion of vast memory headroom. At 1M context, reported peak KV drops from 12.29% (PP1) to 5.91% (PP2) to <b>2.75% (PP4)</b>, yet peak physical GPU VRAM allocation remains flat and saturated at <b>~88.83 GiB</b> out of ~95.59 GiB usable capacity.
            </div>
            <table class="kd-table" style="font-size:11px">
                <thead><tr><th>Topology (1M Context)</th><th>Reported Peak KV %</th><th>Global Model KV Check</th><th>Peak Physical VRAM</th><th>Apparent vs Real Headroom</th></tr></thead>
                <tbody>
                    <tr><td>TP4 / PP1</td><td>12.29%</td><td>12.29%</td><td>88.39 GiB</td><td>Matches single-device reality</td></tr>
                    <tr><td>TP4 / PP2</td><td>5.91%</td><td>~11.82% (2 &times; 5.91%)</td><td>88.69 GiB</td><td>KV diluted across 2 stages</td></tr>
                    <tr><td>TP4 / PP4</td><td style="color:#38bdf8;font-weight:700">2.75%</td><td>~11.00% (4 &times; 2.75%)</td><td style="color:#fde047;font-weight:700">88.83 GiB</td><td>Appears 97.2% free, but VRAM is 88.8G!</td></tr>
                    <tr><td>TP16 / PP1</td><td>12.13%</td><td>12.13%</td><td>86.71 GiB</td><td>Slightly lower static buffer</td></tr>
                </tbody>
            </table>
        `,
        derivation: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                <b>Mathematical Proof:</b> Pipeline stages shard layers across GPUs (PP4 divides 27 layers &approx; 6.75 layers/stage). Each stage holds only 1/4th of the active KV blocks. However, model weights, CUDA runtime, and activation buffers maintain total per-GPU footprint at ~88.4&ndash;88.8 GiB.<br>
                Raw device capacity reported in preflight: <code>97,887 MiB &approx; 95.59 GiB</code> per GPU.
            </div>
        `,
        profiler: `
            <div style="font-size:11px;color:#cbd5e1;line-height:1.5">
                Independent replication on TP8 confirms the pattern: TP8/PP1 12.18% KV &rarr; TP8/PP2 5.88% KV while memory remains 88.7 GiB.
            </div>
        `,
        artifacts: `
            <div style="font-size:10px;font-family:monospace;color:#38bdf8;line-height:1.6">
                scaleout_matrix/vllm_scaleout_network_matrix/tp4_pp4_dist_1m_c1_native.json (EV-084)<br>
                final_validation/STATIC_VALIDATION.json<br>
                hardware_processed/memory_telemetry.json
            </div>
        `
    }
};
"""

# Now write the updater function
print("Ready to integrate.")
