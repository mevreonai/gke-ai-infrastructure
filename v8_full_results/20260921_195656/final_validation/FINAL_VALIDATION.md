# V8-FULL Final Validation

- Coverage rows: **126**
- Completed: **119**
- Safety-skipped: **0**
- Not run: **7**
- Failed: **0**
- Readiness both nodes: **True**
- Hardware validation: **True**
- NCCL local-policy audit: **False**
- vLLM network evidence (Native/100G/20G): **True**
- Scale-out both-node telemetry: **True**
- Distributed profiles complete: **14/22**
- All 12 scale-out 1M topology×network points completed: **True**
- Strict full coverage: **False**

## Guardrails
- V6 single-node native runs must have no NCCL_* overrides.
- Multi-node runs may retain the V6 NCCL Socket network workaround, but never disable local P2P/SHM.
- GCP_CAPPED_20G is a bandwidth-sensitivity proxy, not LOCAL_REAL_2x10G.
- Aggregate Nsight kernel time is not request critical-path wall time.
- 48B absolute latency/tok/s does not transfer directly to Kimi K3.
