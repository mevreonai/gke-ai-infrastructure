# V8-FULL readiness

- Overall: **PASS**
- Require exact V6 core stack: **True**
- Free disk: **355.3 GiB**

| Check | Status |
|---|---|
| `bin:vllm` | PASS |
| `bin:ray` | PASS |
| `bin:nsys` | PASS |
| `bin:nvidia-smi` | PASS |
| `bin:iperf3` | PASS |
| `bin:tc` | PASS |
| `bin:python3` | PASS |
| `vllm_serve_flag:--distributed-executor-backend` | PASS |
| `vllm_serve_flag:--ray-workers-use-nsight` | PASS |
| `vllm_serve_flag:--profiler-config` | PASS |
| `vllm_serve_flag:--tensor-parallel-size` | PASS |
| `vllm_serve_flag:--pipeline-parallel-size` | PASS |
| `vllm_serve_flag:--no-enable-prefix-caching` | PASS |
| `vllm_bench_flag:--profile` | PASS |
| `vllm_bench_flag:--request-rate` | PASS |
| `vllm_bench_flag:--max-concurrency` | PASS |
| `vllm_bench_flag:--save-result` | PASS |
| `vllm_bench_flag:--save-detailed` | PASS |
| `v6_stack:vllm` | PASS |
| `v6_stack:ray` | PASS |
| `v6_stack:torch` | PASS |
| `v6_stack:triton` | PASS |
| `v6_stack:flashinfer-python` | PASS |
| `v6_stack:nvidia-nccl-cu13` | PASS |
| `gpu_count` | PASS |
| `gpu_model_rtx_pro_6000_blackwell` | PASS |
| `gpu_memory_96gb_class` | PASS |
| `disk_free` | PASS |
| `no_forbidden_local_nccl_overrides` | PASS |
| `socket_workaround:clean_nccl_dir` | PASS |
| `socket_workaround:libnccl_present` | PASS |
| `socket_workaround:net_plugin_disabled` | PASS |
